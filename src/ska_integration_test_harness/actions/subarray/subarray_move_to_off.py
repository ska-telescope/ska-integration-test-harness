"""Invoke MoveToOff command on subarray Node."""

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class SubarrayMoveToOff(TelescopeAction):
    """Invoke MoveToOff command on subarray Node."""

    def _action(self):
        self._log("Invoking Off on SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Off()
        return (result, message)

    def termination_condition(self):
        return []
