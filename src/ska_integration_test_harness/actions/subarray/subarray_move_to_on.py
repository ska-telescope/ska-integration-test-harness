"""Invoke MoveToOn command on subarray Node."""

from assertpy import assert_that
from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)


class SubarrayMoveToOn(TelescopeCommandAction):
    """Invoke MoveToOn command on subarray Node."""

    def __init__(self) -> None:
        super().__init__(
            target_device=self.telescope.tmc.subarray_node,
            is_long_running_command=True,
        )

    def _action(self):
        if self.telescope.tmc.subarray_node.State != DevState.ON:
            assert_that(self.telescope.tmc.subarray_node.State).described_as(
                "FAILED ASSUMPTION: Subarray state is not either ON or OFF"
            ).is_equal_to(DevState.OFF)

            self._log("Invoking On on SubarrayNode")
            result, message = self.telescope.tmc.subarray_node.On()
            return (result, message)
        # TODO: This if-then-else block is weird, why we have this?
        return None

    def termination_condition(self):
        """No termination condition is provided for this action."""
        return []
