"""Invoke Release Resource command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
    resources_are_released,
)

LOGGER = logging.getLogger(__name__)


class SubarrayReleaseAllResources(TelescopeAction):
    """Invoke Release Resource command on subarray Node."""

    def _action(self):
        (
            result,
            message,
        ) = self.telescope.tmc.subarray_node.ReleaseAllResources()
        LOGGER.info("Invoked Release Resources on SubarrayNode")
        return result, message

    def termination_condition(self):
        # subarray devices are expected to be in EMPTY state
        res = all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)

        # resources should be released
        res += resources_are_released(self.telescope)

        return res
