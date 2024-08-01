"""Invoke Abort command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)

LOGGER = logging.getLogger(__name__)


class SubarrayRestart(TelescopeAction):
    """Invoke Restart command on subarray Node."""

    def _action(self):
        result, message = self.telescope.tmc.subarray_node.Restart()
        LOGGER.info("Invoked Restart on SubarrayNode")
        return result, message

    def termination_condition(self):
        return all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)
