"""Execute provided command on CentralNode."""

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodeRunCommand(TelescopeCommandAction):
    """Invoke a generic command on CentralNode.

    This action is used to execute any command on CentralNode. The command
    will be called on the Tango device which is pointed to be the
    TMC CentralNode.

    The command can optionally have a JSON input. If it does, the input
    will be sent to the command as a string.

    The command can be a long running command or not. If it is a long
    running command, the action will wait for the command to terminate.
    """

    def __init__(
        self,
        command_name: str,
        command_input: JSONInput | None = None,
        is_long_running_command: bool = False,
    ):
        """Construct the command you want to send on CentralNode.

        :param command_name: Name of command to execute.
        :param command_input: Json send as input to execute command.
        :param is_long_running_command: Whether the command is a long
            running command or not.
        """
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = is_long_running_command

        self.command_name = command_name
        """The name of the command to be executed (e.g., "AssignResources")."""

        self.command_input = command_input
        """The JSON input for the command (if any)."""

    def _action(self):
        self._log(
            f"Invoking {self.command_name} on CentralNode" + " (as LRC)"
            if self.is_long_running_command
            else " (as non-LRC)"
        )
        input_value = self.command_input.as_str() if self.command_input else ""
        result, message = self.telescope.tmc.central_node.command_inout(
            self.command_name, input_value
        )
        return result, message
