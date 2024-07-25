"""Invoke Release Resource command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedEvent,
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

LOGGER = logging.getLogger(__name__)


class SubarrayReleaseAllResources(TelescopeAction):
    """Invoke Release Resource command on subarray Node."""

    def _action(self):
        (
            result,
            message,
        ) = self.telescope.tmc.subarray_node.ReleaseAllResources()
        LOGGER.info("Invoked Release Resources on SubarrayNode")
        return result, message

    def termination_condition(self):
        pre_action_attr_value = (
            self.telescope.tmc.subarray_node.assignedResources
        )

        return [
            ExpectedStateChange(
                self.telescope.tmc.csp_subarray_leaf_node,
                "cspSubarrayObsState",
                ObsState.EMPTY,
            ),
            ExpectedStateChange(
                self.telescope.tmc.sdp_subarray_leaf_node,
                "sdpSubarrayObsState",
                ObsState.EMPTY,
            ),
            ExpectedEvent(
                device=self.telescope.tmc.subarray_node,
                attribute="assignedResources",
                predicate=lambda event: event.attribute_value
                != pre_action_attr_value,
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_subarray, "obsState", ObsState.EMPTY
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray, "obsState", ObsState.EMPTY
            ),
            ExpectedStateChange(
                self.telescope.tmc.subarray_node, "obsState", ObsState.EMPTY
            ),
        ]
