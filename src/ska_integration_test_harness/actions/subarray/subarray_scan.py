"""Invoke Scan command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarrayScan(TelescopeAction):
    """Invoke Scan command on subarray Node."""

    def __init__(self, scan_input: JSONInput):
        super().__init__()
        self.scan_input = scan_input

    def _action(self):
        self._log("Invoking Scan on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Scan(
            self.scan_input.get_json_string()
        )
        return result, message

    def termination_condition(self):
        """All subarrays must be in SCANNING state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.SCANNING)
