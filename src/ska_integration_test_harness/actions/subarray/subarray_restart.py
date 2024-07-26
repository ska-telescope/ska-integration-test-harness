"""Invoke Abort command on subarray Node."""

import logging

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    release_and_restart_termination_condition,
)

LOGGER = logging.getLogger(__name__)


class SubarrayRestart(TelescopeAction):
    """Invoke Restart command on subarray Node."""

    def _action(self):
        result, message = self.telescope.tmc.subarray_node.Restart()
        LOGGER.info("Invoked Restart on SubarrayNode")
        return result, message

    def termination_condition(self):
        return release_and_restart_termination_condition(self.telescope)
