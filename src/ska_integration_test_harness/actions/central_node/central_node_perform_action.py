"""Execute provided command on CentralNode."""

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodePerformAction(TelescopeCommandAction):
    """Invoke a generic command on CentralNode."""

    def __init__(
        self, command_name: str, command_input: JSONInput | None = None
    ):
        super().__init__()
        self.command_name = command_name
        self.command_input = command_input

    def _action(self):
        self._log(f"Invoking {self.command_name} on CentralNode")
        input_value = self.command_input.as_str() if self.command_input else ""
        result, message = self.telescope.tmc.central_node.command_inout(
            self.command_name, input_value
        )
        return result, message

    def termination_condition(self):
        """No termination condition is provided for this action."""
        return []
