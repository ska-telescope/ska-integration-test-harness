"""Invoke ReleaseResources on the CentralNode."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
    resources_are_released,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodeReleaseResources(TelescopeAction):
    """A class for releasing resources on the CentralNode."""

    def __init__(self, release_input: JSONInput):
        super().__init__()
        self.release_input = release_input

    def _action(self):
        self._log("Invoking ReleaseResources on CentralNode")
        result, message = self.telescope.tmc.central_node.ReleaseResources(
            self.release_input.get_json_string()
        )
        return result, message

    def termination_condition(self):
        # subarray devices are expected to be in EMPTY state
        res = all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)

        # resources should be released
        res += resources_are_released(self.telescope)

        return res
