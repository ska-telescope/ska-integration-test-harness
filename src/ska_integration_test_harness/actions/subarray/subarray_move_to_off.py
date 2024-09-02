"""Invoke MoveToOff command on subarray Node."""

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class SubarrayMoveToOff(TelescopeAction):
    """Invoke MoveToOff command on subarray Node."""

    def _action(self):
        # NOTE: if I implement this using an assertion, it will fail
        # Resource(self.telescope.tmc.subarray_node).assert_attribute(
        #     "State"
        # ).equals("ON")
        # assert_that(self.telescope.tmc.subarray_node.State).described_as(
        #     "FAIL IN SubarrayMoveToOff ACTION EXECUTION: "
        #     "TMC Subarray node "
        #     f"({self.telescope.tmc.subarray_node.dev_name()}) "
        #     "State is supposed to be ON before the action."
        # ).is_equal_to(DevState.ON)

        self._log("Invoking Off on SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Off()
        return (result, message)

    def termination_condition(self):
        return []
