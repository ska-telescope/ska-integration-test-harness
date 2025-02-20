"""Execute provided command on subarray Node."""

from ska_control_model import ObsState  # pylint: disable=unused-import

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarrayRunCommand(TelescopeCommandAction):
    """Invoke a generic command on the TMC SubarrayNode.

    This action is used to execute any command on the TMC SubarrayNode.
    The command will be called on the Tango device which is pointed to be the
    TMC SubarrayNode.

    The command can optionally have a JSON input. If it does, the input
    will be sent to the command as a string.

    The command can be a long running command or not. If it is a long
    running command, the action will wait for the command to terminate.

    Optionally, you can specify the expected obsState after the command is
    called. If you do, the action will wait for all subarrays to have the
    expected obsState before it terminates.
    """

    def __init__(
        self,
        command_name: str,
        expected_obs_state: "ObsState | None" = None,
        command_input: JSONInput | None = None,
        is_long_running_command: bool = False,
    ):
        """Construct the command you want to send on SubarrayNode.

        :param command_name: Name of command to execute.
        :param expected_obs_state: Expected obsState after the command is
            executed.
        :param command_input: Json send as input to execute command.
        :param is_long_running_command: Whether the command is a long
            running command or not.
        """
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = is_long_running_command

        self.command_name = command_name
        """The name of the command to be executed (e.g., "Configure")."""

        self.expected_obs_state = expected_obs_state
        """The expected obsState after the command is executed.

        (e.g., ObsState.READY). If not provided, the action will have an empty
        termination condition. If provided, the termination condition will be
        that all subarrays must have the expected obsState.
        """

        self.command_input = command_input
        """The JSON input for the command (if any)."""

    def _action(self):
        self._log(
            f"Invoking {self.command_name} on SubarrayNode" + " (as LRC)"
            if self.is_long_running_command
            else " (as non-LRC)"
        )
        input_value = self.command_input.as_str() if self.command_input else ""
        result, message = self.telescope.tmc.subarray_node.command_inout(
            self.command_name, input_value
        )
        return result, message

    def termination_condition(self):
        """Eventual LRC termination check + eventual expected obsState check.

        This action may have those two termination conditions:

        - The LRC must terminate (if the command is a LRC).
        - All subarrays must have the expected obsState (if provided).
        """
        # LRC must terminate (if the command is a LRC, superclass deal with it)
        expected_events = super().termination_condition()

        if self.expected_obs_state:
            # All subarrays must have the expected obsState
            expected_events += all_subarrays_have_obs_state(
                self.telescope, self.expected_obs_state
            )

        return expected_events
