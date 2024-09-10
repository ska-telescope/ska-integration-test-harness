"""Invoke Abort command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayRestart(TelescopeAction):
    """Invoke Restart command on subarray Node."""

    def _action(self):
        self._log("Invoking Restart on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Restart()
        return result, message

    def termination_condition(self):
        """All subarrays are in EMPTY state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)
