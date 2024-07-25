"""Invoke End command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

LOGGER = logging.getLogger(__name__)


class SubarrayEndObservation(TelescopeAction):
    """Invoke End command on subarray Node."""

    def _action(self):
        result, message = self.telescope.tmc.subarray_node.End()
        LOGGER.info("Invoked End on SubarrayNode")
        return result, message

    def termination_condition(self):
        return [
            ExpectedStateChange(
                self.telescope.tmc.csp_subarray_leaf_node,
                "cspSubarrayObsState",
                ObsState.IDLE,
            ),
            ExpectedStateChange(
                self.telescope.tmc.sdp_subarray_leaf_node,
                "sdpSubarrayObsState",
                ObsState.IDLE,
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_subarray, "obsState", ObsState.IDLE
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray, "obsState", ObsState.IDLE
            ),
            ExpectedStateChange(
                self.telescope.tmc.subarray_node, "obsState", ObsState.IDLE
            ),
        ]
