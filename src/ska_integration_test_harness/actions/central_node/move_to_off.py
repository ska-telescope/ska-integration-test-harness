"""
Two actions to move the central node to OFF state.

The first action is a command action that sends the TelescopeOff command to the
central node and waits for termination (synchronising also on LRC termination).

The second action is a wrapper around the first action, which sends the command
only if the central node is not already in OFF state. The result of the second
action is None if the central node is already in OFF state, otherwise it is the
result of the first action.

The termination conditions always include the expected side effects
of the first action. The LRC termination is verified only if the
first action is executed.
"""

from typing import Any

from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
    master_and_subarray_devices_have_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class MoveToOffCommand(TelescopeCommandAction):
    """Send TelescopeOff to the central node and wait for termination."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Moving the central node to OFF state")
        res = self.telescope.tmc.central_node.TelescopeOff()
        self.telescope.csp.move_to_off()
        return res

    def termination_condition(self):
        """Master and subarray devices are in OFF state (+ LRC terminates).

        Master and subarray devices should be in OFF state, while
        all dishes should be in STANDBY_LP mode and LRC must terminate.
        """
        # LRC must terminate
        # + devices are in OFF state, dishes are in STANDBY_LP mode
        return super().termination_condition() + self.expected_side_effects()

    def expected_side_effects(self):
        """Devices are in OFF state, dishes are in STANDBY_LP mode."""
        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in OFF state.
        expected_events = master_and_subarray_devices_have_state(
            self.telescope,
            DevState.OFF,
        )

        # All dishes should be in STANDBY_LP mode
        expected_events += dishes_have_dish_mode(
            self.telescope, DishMode.STANDBY_LP
        )

        return expected_events


class MoveToOff(TelescopeAction[None | tuple[Any, list[str]]]):
    """Ensure the central node is in OFF state.

    This action is a wrapper around the MoveToOffCommand action, which
    sends the TelescopeOff command to the central node only if the central
    node is not already in OFF state. This action is useful when you want
    to ensure that the central node is in OFF state, but you don't want to
    send the command if the central node is already in OFF state.

    The result of this action is None if the central node is already in OFF
    state, otherwise it is the result of the MoveToOffCommand action.

    The termination conditions always include the expected side effects
    of the MoveToOffCommand action. The LRC instead is verified only if
    the MoveToOffCommand action is executed.

    Policies about the termination condition are propagated to the
    MoveToOffCommand action.
    """

    def __init__(self) -> None:
        super().__init__()
        self.move_to_off = MoveToOffCommand()

    def _action(self):
        # Check if the central node is already in OFF state
        if self.telescope.tmc.central_node.state() == DevState.OFF:
            self._log("Central node is already in OFF state")
            return None

        # propagate all the settings to the MoveToOffCommand action
        self.move_to_off.set_termination_condition_policy(
            self.wait_termination
        )
        self.move_to_off.set_termination_condition_timeout(
            self.termination_condition_timeout
        )

        return self.move_to_off.execute()

    def termination_condition(self):
        """Master and subarray devices are in OFF state.

        Master and subarray devices should be in OFF state, while
        all dishes should be in STANDBY_LP mode.
        """
        return self.move_to_off.expected_side_effects()
