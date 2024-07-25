"""Invoke Assign Resource command on CentralNode."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.generate_eb_pb_ids import (
    generate_eb_pb_ids,
)
from ska_integration_test_harness.inputs.json_input import JSONInput

LOGGER = logging.getLogger(__name__)


class CentralNodeAssignResources(TelescopeAction):
    """Invoke Assign Resource command on CentralNode."""

    # NOTE: this is very similar to SubarrayAssignResources

    def __init__(self, assign_input: JSONInput):
        super().__init__()
        self.assign_input = assign_input

    def _action(self):
        # NOTE: should I do this?
        # device = DeviceUtils(
        #     obs_state_device_names=[
        #         device_dict.get("csp_subarray"),
        #         device_dict.get("sdp_subarray"),
        #         device_dict.get("tmc_subarraynode"),
        #     ]
        # )
        # device.check_devices_obsState("EMPTY")
        # set_wait_for_obsstate = kwargs.get("set_wait_for_obsstate", True)

        cmd_input = generate_eb_pb_ids(self.assign_input)
        result, message = self.telescope.tmc.central_node.AssignResources(
            cmd_input.get_json_string()
        )
        LOGGER.info("Invoked AssignResources on CentralNode")
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
