"""An action to move the central node to OFF State."""

from tango import DevState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
    master_and_subarray_devices_have_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class MoveToOff(TelescopeAction[None]):
    """An action to move the central node to off."""

    def _action(self):
        self._log("Moving the central node to OFF state")
        self.telescope.tmc.central_node.TelescopeOff()
        self.telescope.csp.move_to_off()

    def termination_condition(self):
        """Master and subarray devices should be in OFF state, while
        all dishes should be in STANDBY_LP mode."""

        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in OFF state.
        res = master_and_subarray_devices_have_state(
            self.telescope,
            DevState.OFF,
        )

        # All dishes should be in STANDBY_LP mode
        res.extend(dishes_have_dish_mode(self.telescope, DishMode.STANDBY_LP))

        return res
