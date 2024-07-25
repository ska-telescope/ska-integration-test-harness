"""Execute provided command on subarray Node."""

import enum
import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

LOGGER = logging.getLogger(__name__)


class TelescopeCommand(enum.Enum):
    """A list of commands that can be executed on the telescope."""

    ASSIGN_RESOURCES = "AssignResources"
    CONFIGURE = "Configure"
    SCAN = "Scan"
    ABORT = "Abort"


class SubarrayExecuteTransition(TelescopeAction):
    """Execute provided command on subarray Node."""

    COMMAND_OUTCOME_MAP = {
        TelescopeCommand.ASSIGN_RESOURCES: ObsState.RESOURCING,
        TelescopeCommand.CONFIGURE: ObsState.CONFIGURING,
        TelescopeCommand.SCAN: ObsState.SCANNING,
        TelescopeCommand.ABORT: ObsState.ABORTING,
    }

    def __init__(self, command_name: str, argin=None):
        super().__init__()
        self.command_name = command_name
        self.argin = argin

    def _action(self):
        if self.command_name is not None:
            result, message = self.telescope.tmc.subarray_node.command_inout(
                self.command_name, self.argin
            )
            LOGGER.info(f"Invoked {self.command_name} on SubarrayNode")
            return (
                result,
                message,
            )
        # pylint says inconsistent-return-statements,
        # what should be returned here?
        return None

    def termination_condition(self):
        if (
            self.command_name
            not in self.COMMAND_OUTCOME_MAP.keys()  # pylint: disable=consider-iterating-dictionary disable=line-too-long # noqa: E501
        ):
            return []

        expected_command_output = self.COMMAND_OUTCOME_MAP[self.command_name]
        return [
            ExpectedStateChange(
                self.telescope.tmc.csp_subarray_leaf_node,
                "cspSubarrayObsState",
                expected_command_output,
            ),
            ExpectedStateChange(
                self.telescope.tmc.sdp_subarray_leaf_node,
                "sdpSubarrayObsState",
                expected_command_output,
            ),
            ExpectedStateChange(
                self.telescope.csp.csp_subarray,
                "obsState",
                expected_command_output,
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray,
                "obsState",
                expected_command_output,
            ),
            ExpectedStateChange(
                self.telescope.tmc.subarray_node,
                "obsState",
                expected_command_output,
            ),
        ]
