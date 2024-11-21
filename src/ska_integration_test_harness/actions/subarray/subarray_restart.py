"""Invoke Abort command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayRestart(TransientQuiescentCommandAction):
    """Invoke Restart command on subarray Node.

    This action is expected to be called when the subarray is in ABORTED state.
    This action will move the subarray to the RESTARTING state (transient)
    and then to the EMPTY state (quiescent and stable).
    """

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Invoking Restart on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Restart()
        return result, message

    def termination_condition_for_quiescent_state(self) -> list[ExpectedEvent]:
        """All subarrays must be in EMPTY state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)

    def termination_condition_for_transient_state(self) -> list[ExpectedEvent]:
        """All subarrays must be in RESTARTING state."""
        return all_subarrays_have_obs_state(
            self.telescope, ObsState.RESTARTING
        )
