"""An action to move the central node to ON State."""

from tango import DevState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
    master_and_subarray_devices_have_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class MoveToOn(TelescopeAction[None]):
    """An action to move the central node to ON State."""

    def _action(self):
        self._log("Moving the central node to ON state")
        self.telescope.tmc.central_node.TelescopeOn()
        self.telescope.csp.move_to_on()

    def termination_condition(self):
        """No expected outcome for this action."""

        # The central node, SDP subarray, SDP master, CSP subarray, CSP master
        # and all dishes should be in ON state.
        res = master_and_subarray_devices_have_state(
            self.telescope,
            DevState.ON,
        )

        # All dishes should be in STANDBY_FP mode
        res.extend(dishes_have_dish_mode(self.telescope, DishMode.STANDBY_FP))

        return res
