"""An action to move the central node to ON State."""

from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
    master_and_subarray_devices_have_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class MoveToOn(TelescopeCommandAction):
    """An action to move the central node to ON State."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Moving the central node to ON state")
        res = self.telescope.tmc.central_node.TelescopeOn()
        self.telescope.csp.move_to_on()
        return res

    def termination_condition(self):
        """Master and subarray devices are in ON state (+ LRC terminates).

        Master and subarray devices should be in ON state, while
        all dishes should be in STANDBY_FP mode and LRC must terminate.
        """
        # LRC must terminate
        expected_events = super().termination_condition()

        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in ON state.
        expected_events += master_and_subarray_devices_have_state(
            self.telescope,
            DevState.ON,
        )

        # All dishes should be in STANDBY_FP mode
        expected_events += dishes_have_dish_mode(
            self.telescope, DishMode.STANDBY_FP
        )

        return expected_events
