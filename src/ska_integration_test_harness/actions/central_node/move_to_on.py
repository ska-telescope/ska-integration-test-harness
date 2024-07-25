"""An action to move the central node to ON State."""

import logging

from tango import DevState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode

LOGGER = logging.getLogger(__name__)


class MoveToOn(TelescopeAction):
    """An action to move the central node to ON State."""

    def _action(self):
        LOGGER.info("Moving the central node to ON state")

        self.telescope.tmc.central_node.TelescopeOn()
        self.telescope.csp.move_to_on()

    def termination_condition(self):
        """No expected outcome for this action."""
        res = [
            ExpectedStateChange(
                self.telescope.tmc.central_node,
                "telescopeState",
                DevState.ON,
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray, "State", DevState.ON
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_master, "State", DevState.ON
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_subarray, "State", DevState.ON
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_master, "State", DevState.ON
            ),
        ]

        res += [
            ExpectedStateChange(dish, "dishMode", DishMode.STANDBY_FP)
            for dish in self.telescope.dishes.dish_master_list
        ]

        return res
