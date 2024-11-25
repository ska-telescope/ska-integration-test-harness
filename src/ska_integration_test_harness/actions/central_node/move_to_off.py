"""An action to move the central node to OFF State."""

from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
    master_and_subarray_devices_have_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class MoveToOff(TelescopeCommandAction):
    """An action to move the central node to off."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Moving the central node to OFF state")
        res = self.telescope.tmc.central_node.TelescopeOff()
        self.telescope.csp.move_to_off()
        # pylint: disable=duplicate-code
        return res

    def termination_condition(self):
        """Master and subarray devices should be in OFF state.

        Master and subarray devices should be in OFF state, while all dishes
        should be in STANDBY_LP mode and LRC must terminate.
        """
        # LRC must terminate
        expected_events = super().termination_condition()

        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in OFF state.
        expected_events += master_and_subarray_devices_have_state(
            self.telescope,
            DevState.OFF,
        )

        # All dishes should be in STANDBY_LP mode
        expected_events += dishes_have_dish_mode(
            self.telescope, DishMode.STANDBY_LP
        )

        return expected_events
