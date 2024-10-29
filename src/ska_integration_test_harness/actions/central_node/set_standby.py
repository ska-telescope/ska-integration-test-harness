"""An action to set the central node to STANDBY State."""

from tango import DevState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class SetStandby(TelescopeAction[None]):
    """An action to set the central node to STANDBY State."""

    def _action(self):
        self._log("Setting the central node to STANDBY state")
        self.telescope.tmc.central_node.TelescopeStandby()
        self.telescope.csp.move_to_off()

    def termination_condition(self):
        """Central node should be in STANDBY state and so also SDP
        all dishes should be in STANDBY_LP mode."""

        # subarrays must be in OFF state,
        # master devices must be in STANDBY state
        res = [
            ExpectedStateChange(
                self.telescope.tmc.central_node,
                "telescopeState",
                DevState.STANDBY,
            ),
        ]

        # All dishes should be in STANDBY_LP mode
        res.extend(dishes_have_dish_mode(self.telescope, DishMode.STANDBY_LP))

        return res
