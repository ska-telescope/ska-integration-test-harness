"""Invoke Release Resource command on subarray Node."""

import logging

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    release_and_restart_termination_condition,
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
        return release_and_restart_termination_condition(self.telescope)
