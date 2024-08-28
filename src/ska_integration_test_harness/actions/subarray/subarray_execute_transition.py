"""Execute provided command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayExecuteTransition(TelescopeCommandAction):
    """Execute provided command on subarray Node.

    TODO: this class is a generic command executor, while refactoring
    I put here some synchronization conditions for waiting transient
    states, but I think they should be moved in their specific classes.

    E.g., SubarrayAssignResources, SubarrayConfigure, SubarrayScan and
    SubarrayAbort have an additional parameter that permits to specify
    if you want to synchronize on the transient state or in the final
    quiescent state. This parameter could also be moved in a special
    super-class, for example called SubarrayCommandToTransientState.
    """

    COMMAND_OUTCOME_MAP = {
        "AssignResources": ObsState.RESOURCING,
        "Configure": ObsState.CONFIGURING,
        "Scan": ObsState.SCANNING,
        "Abort": ObsState.ABORTING,
    }

    def __init__(self, command_name: str, argin=None):
        super().__init__()
        self.command_name = command_name
        self.argin = argin

    def _action(self):
        self._log(f"Invoking {self.command_name} on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.command_inout(
            self.command_name, self.argin
        )
        return result, message

    def termination_condition(self):
        # get the expected outcome of the command
        if self.command_name not in self.COMMAND_OUTCOME_MAP:
            return []

        expected_command_output = self.COMMAND_OUTCOME_MAP[self.command_name]
        return all_subarrays_have_obs_state(
            self.telescope, expected_command_output
        )
