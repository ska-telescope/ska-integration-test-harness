"""Clear TMC subarray obs state, putting it into the "EMPTY" state."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.subarray.subarray_abort import (
    SubarrayAbort,
)
from ska_integration_test_harness.actions.subarray.subarray_force_abort import (  # pylint: disable=line-too-long # noqa E501
    SubarrayForceAbort,
)
from ska_integration_test_harness.actions.subarray.subarray_restart import (
    SubarrayRestart,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class SubarrayClearObsState(TelescopeAction):
    """Clear TMC subarray obs state, putting it into the "EMPTY" state."""

    def __init__(self) -> None:
        super().__init__()
        # set a longer timeout for this action
        # (since some actions may take longer to complete)
        self.set_termination_condition_timeout(60)

    def _action(self):
        if self.telescope.tmc.subarray_node.obsState in [
            ObsState.IDLE,
            ObsState.RESOURCING,
            ObsState.READY,
            ObsState.CONFIGURING,
            ObsState.SCANNING,
        ]:
            SubarrayAbort().execute()

        # if there is an ongoing broken abort, ensure it ends before proceeding
        if self.telescope.tmc.subarray_node.obsState == ObsState.ABORTING:
            SubarrayForceAbort().execute()

        if self.telescope.tmc.subarray_node.obsState in [
            ObsState.ABORTED,
        ]:
            SubarrayRestart().execute()

    def termination_condition(self):
        # ensure final state is empty
        res = [
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

        # csp subarray leaf node may not be yet initialized
        if self.telescope.tmc.is_subarray_initialized():
            res.extend(
                [
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
                ]
            )

        return res
