"""Invoke Scan command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarrayScan(TelescopeCommandAction):
    """Invoke Scan command on subarray Node."""

    def __init__(self, scan_input: JSONInput):
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True
        self.scan_input = scan_input

    def _action(self):
        self._log("Invoking Scan on TMC SubarrayNode")
        return self.telescope.tmc.subarray_node.Scan(self.scan_input.as_str())

    def termination_condition(self):
        """All subarrays must be in SCANNING state (and LRC must terminate)."""
        # LRC must terminate
        expected_events = super().termination_condition()

        # All subarrays must be in SCANNING state
        expected_events += all_subarrays_have_obs_state(
            self.telescope, ObsState.SCANNING
        )

        return expected_events
