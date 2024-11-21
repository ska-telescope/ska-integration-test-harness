"""Invoke Assign Resource command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.utils.generate_eb_pb_ids import (
    generate_eb_pb_ids,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarrayAssignResources(TransientQuiescentCommandAction):
    """Invoke Assign Resource command on subarray Node.

    This action is expected to move the subarray to the RESOURCING state
    (transient) and then to the IDLE state (quiescent and stable).

    This action is not supposed to be used to release resources, unless
    you subclass it and override the termination conditions.
    """

    def __init__(self, assign_input: JSONInput):
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True
        self.assign_input = assign_input

    def _action(self):
        cmd_input = generate_eb_pb_ids(self.assign_input)
        self._log("Invoking AssignResources on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.AssignResources(
            cmd_input.as_str()
        )
        return result, message

    def termination_condition_for_transient_state(self):
        """All subarrays must reach the RESOURCING state."""
        return all_subarrays_have_obs_state(
            self.telescope, ObsState.RESOURCING
        )

    def termination_condition_for_quiescent_state(self):
        """All subarrays must reach the IDLE state and LRC must terminate."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.IDLE)
