"""Invoke Abort command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayAbort(TelescopeCommandAction):
    """Invoke Abort command on subarray Node."""

    def _action(self):
        self._log("Invoking Abort on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Abort()
        return result, message

    def termination_condition(self):
        """All subarrays must be in ABORTED state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.ABORTED)
