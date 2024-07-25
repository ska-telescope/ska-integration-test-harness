"""Invoke ReleaseResources on the CentralNode."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedEvent,
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.inputs.json_input import JSONInput

LOGGER = logging.getLogger(__name__)


class CentralNodeReleaseResources(TelescopeAction):
    """A class for releasing resources on the CentralNode."""

    def __init__(self, release_input: JSONInput):
        super().__init__()
        self.release_input = release_input

    def _action(self):
        result, message = self.telescope.tmc.central_node.ReleaseResources(
            self.release_input.get_json_string()
        )
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
            # TODO: this is a not so good solution
            # on long term, engineer something better.
            # verify that assignedResources attribute has changed value
            ExpectedEvent(
                device=self.telescope.tmc.subarray_node,
                attribute="assignedResources",
                predicate=lambda event: event.attribute_value
                != pre_action_attr_value,
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_subarray,
                "obsState",
                ObsState.EMPTY,
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray,
                "obsState",
                ObsState.EMPTY,
            ),
            ExpectedStateChange(
                self.telescope.tmc.subarray_node,
                "obsState",
                ObsState.EMPTY,
            ),
        ]
