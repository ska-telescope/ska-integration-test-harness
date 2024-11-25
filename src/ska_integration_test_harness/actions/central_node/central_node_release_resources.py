"""Invoke ReleaseResources on the CentralNode."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
    resources_are_released,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodeReleaseResources(TelescopeCommandAction):
    """Invoke ReleaseResources on the CentralNode."""

    def __init__(self, release_input: JSONInput):
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = True
        self.release_input = release_input

    def _action(self):
        self._log("Invoking ReleaseResources on CentralNode")
        result, message = self.telescope.tmc.central_node.ReleaseResources(
            self.release_input.as_str()
        )
        return result, message

    def termination_condition(self):
        """All subarrays are in EMPTY state and resources are released.

        (and LRC must terminate).
        """
        # LRC must terminate
        expected_events = super().termination_condition()

        # All subarrays must reach the EMPTY state
        expected_events += all_subarrays_have_obs_state(
            self.telescope, ObsState.EMPTY
        )

        # Resources should be released
        expected_events += resources_are_released(self.telescope)

        return expected_events
