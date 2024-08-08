"""Invoke End command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayEndObservation(TelescopeCommandAction):
    """Invoke End command on subarray Node."""

    def _action(self):
        self._log("Invoking End on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.End()
        return result, message

    def termination_condition(self):
        """All subarrays must be in IDLE state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.IDLE)
