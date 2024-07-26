"""Invoke ReleaseResources on the CentralNode."""

import logging

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    release_and_restart_termination_condition,
)
from ska_integration_test_harness.inputs.json_input import JSONInput

LOGGER = logging.getLogger(__name__)


class CentralNodeReleaseResources(TelescopeAction):
    """A class for releasing resources on the CentralNode."""

    def __init__(self, release_input: JSONInput):
        super().__init__()
        self.release_input = release_input

    def _action(self):
        result, message = self.telescope.tmc.central_node.ReleaseResources(
            self.release_input.get_json_string()
        )
        return result, message

    def termination_condition(self):
        return release_and_restart_termination_condition(self.telescope)
