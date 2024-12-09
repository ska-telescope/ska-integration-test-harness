"""Invoke MoveToOn command on subarray Node."""

from assertpy import assert_that
from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)


class SubarrayMoveToOn(TelescopeCommandAction):
    """Invoke MoveToOn command on subarray Node."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.subarray_node
        self.is_long_running_command = True

    def _action(self):
        assert_that(self.telescope.tmc.subarray_node.State).described_as(
            "FAILED ASSUMPTION: Subarray state is not OFF"
        ).is_equal_to(DevState.OFF)

        self._log("Invoking On on SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.On()
        return (result, message)
