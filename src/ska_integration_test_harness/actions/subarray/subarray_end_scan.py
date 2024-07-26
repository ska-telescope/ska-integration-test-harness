"""Invoke EndScan command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)

LOGGER = logging.getLogger(__name__)


class SubarrayEndScan(TelescopeAction):
    """Invoke EndScan command on subarray Node."""

    def _action(self):
        result, message = self.telescope.tmc.subarray_node.EndScan()
        LOGGER.info("Invoked EndScan on SubarrayNode")
        return result, message

    def termination_condition(self):
        """All subarrays must be in READY state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.READY)
