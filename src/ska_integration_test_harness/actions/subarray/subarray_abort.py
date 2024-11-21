"""Invoke Abort command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayAbort(TransientQuiescentCommandAction):
    """Invoke Abort command on subarray Node.

    This action is expected to move the subarray to the ABORTING state
    (transient) and then to the ABORTED state (quiescent and stable).
    """

    def __init__(self):
        super().__init__(
            target_device=self.telescope.tmc.subarray_node,
            is_long_running_command=False,
        )

    def _action(self):
        self._log("Invoking Abort on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Abort()
        return result, message

    def termination_condition_for_quiescent_state(self) -> list[ExpectedEvent]:
        """All subarrays must be in ABORTED state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.ABORTED)

    def termination_condition_for_transient_state(self) -> list[ExpectedEvent]:
        """All subarrays must be in ABORTING state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.ABORTING)
