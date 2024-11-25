"""Invoke Release Resource command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
    resources_are_released,
)


class SubarrayReleaseAllResources(TelescopeCommandAction):
    """Invoke Release Resource command on subarray Node."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Invoking ReleaseAllResources on TMC SubarrayNode")
        return self.telescope.tmc.subarray_node.ReleaseAllResources()

    # pylint: disable=duplicate-code
    def termination_condition(self):
        """Subarrays are in EMPTY, resources are released, LRC terminates."""
        # LRC must terminate
        expected_events = super().termination_condition()

        # subarray devices are expected to be in EMPTY state
        expected_events += all_subarrays_have_obs_state(
            self.telescope, ObsState.EMPTY
        )

        # resources should be released
        expected_events += resources_are_released(self.telescope)

        return expected_events
