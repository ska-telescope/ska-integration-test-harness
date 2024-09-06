"""Invoke MoveToOn command on subarray Node."""

from assertpy import assert_that
from tango import DevState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class SubarrayMoveToOn(TelescopeAction):
    """Invoke MoveToOn command on subarray Node."""

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
        return []
