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

    def _action(self):
        self._log("Invoking ReleaseAllResources on TMC SubarrayNode")
        (
            result,
            message,
        ) = self.telescope.tmc.subarray_node.ReleaseAllResources()
        return result, message

    def termination_condition(self):
        """All subarrays are in EMPTY state and resources are released."""

        # subarray devices are expected to be in EMPTY state
        res = all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)

        # resources should be released
        res += resources_are_released(self.telescope)

        return res
