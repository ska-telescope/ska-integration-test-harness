"""Two actions to move the central node to ON state.

The first action is a command action that sends the TelescopeOn command to the
central node and waits for termination (synchronising also on LRC termination).

The second action is a wrapper around the first action, which sends the command
only if the central node is not already in ON state. The result of the second
action is None if the central node is already in ON state, otherwise it is the
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


class MoveToOnCommand(TelescopeCommandAction):
    """Send TelescopeOn to the central node and wait for termination."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        # Is a LRC, but right now it raises err. code 3. TODO: fix this
        # PERSONAL NOTE: it looks like it depends from the starting state,
        # because if it's not exactly the expected one, it completes the
        # operation but the final result is an error
        self.is_long_running_command = False

    def _action(self):
        self._log("Moving the central node to ON state")
        res = self.telescope.tmc.central_node.TelescopeOn()
        return res

    def termination_condition(self):
        """Master and subarray devices are in ON state (+ LRC terminates).

        Master and subarray devices should be in ON state, while
        all dishes should be in STANDBY_FP mode and LRC must terminate.
        """
        # LRC must terminate
        # + devices are in ON state, dishes are in STANDBY_FP mode
        return super().termination_condition() + self.expected_side_effects()

    def expected_side_effects(self):
        """Devices are in ON state, dishes are in STANDBY_FP mode."""
        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in ON state.
        expected_events = master_and_subarray_devices_have_state(
            self.telescope,
            DevState.ON,
        )

        # All dishes should be in STANDBY_FP mode
        expected_events += dishes_have_dish_mode(
            self.telescope, DishMode.STANDBY_FP
        )

        return expected_events


class MoveToOn(TelescopeAction[None | tuple[Any, list[str]]]):
    """Ensure the central node is in ON state.

    This action is a wrapper around the MoveToOnCommand action, which
    sends the TelescopeOn command to the central node only if the central
    node is not already in ON state. This action is useful when you want
    to ensure that the central node is in ON state, but you don't want to
    send the command if the central node is already in ON state.

    The result of this action is None if the central node is already in ON
    state, otherwise it is the result of the MoveToOnCommand action.

    The termination conditions always include the expected side effects
    of the MoveToOnCommand action. The LRC instead is verified only if
    the MoveToOnCommand action is executed.

    Policies about the termination condition are propagated to the
    MoveToOnCommand action.
    """

    def __init__(self) -> None:
        super().__init__()
        self.move_to_on = MoveToOnCommand()

    def _action(self):
        # Check if the central node is already in ON state
        if self.telescope.tmc.central_node.telescopeState == DevState.ON:
            self._log("Central node is already in ON state")
            return None

        # propagate all the settings to the MoveToOnCommand action
        self.move_to_on.set_termination_condition_policy(self.wait_termination)
        self.move_to_on.set_termination_condition_timeout(
            self.termination_condition_timeout
        )
        self.move_to_on.set_logging_policy(self.do_logging)

        return self.move_to_on.execute()

    def termination_condition(self):
        """Master and subarray devices are in ON state.

        Master and subarray devices should be in ON state, while
        all dishes should be in STANDBY_FP mode.
        """
        return self.move_to_on.expected_side_effects()
