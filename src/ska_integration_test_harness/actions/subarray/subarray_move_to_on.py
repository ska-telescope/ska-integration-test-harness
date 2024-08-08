"""Invoke MoveToOn command on subarray Node."""

import logging

from assertpy import assert_that
from tango import DevState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

# TODO: logging should not belong here
LOGGER = logging.getLogger(__name__)


class SubarrayMoveToOn(TelescopeAction):
    """Invoke MoveToOn command on subarray Node."""

    def _action(self):
        # TODO: why are we using strings instead of state enums?
        # which is the point where it's done a mapping between the two?
        # if self.telescope.tmc.subarray_state != "ON":
        if self.telescope.tmc.subarray_node.State != DevState.ON:
            assert_that(self.telescope.tmc.subarray_node.State).described_as(
                "FAILED ASSUMPTION: Subarray state is not either ON or OFF"
            ).is_equal_to(DevState.OFF)

            LOGGER.info("Invoking On on SubarrayNode")
            result, message = self.telescope.tmc.subarray_node.On()
            LOGGER.info("Invoked ON on SubarrayNode")
            return (result, message)
        # pylint says inconsistent-return-statements,
        # what should be returned here?
        return None

    def termination_condition(self):
        return []
