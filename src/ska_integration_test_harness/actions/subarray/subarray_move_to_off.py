"""Invoke MoveToOff command on subarray Node."""

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)


class SubarrayMoveToOff(TelescopeCommandAction):
    """Invoke MoveToOff command on subarray Node."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Invoking Off on SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Off()
        return (result, message)
