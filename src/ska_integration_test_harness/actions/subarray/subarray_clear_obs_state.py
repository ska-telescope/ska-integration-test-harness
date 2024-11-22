"""Clear TMC subarray obs state, putting it into the "EMPTY" state."""

from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
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


class SubarrayClearObsState(TelescopeAction[None]):
    """Clear TMC subarray obs state, putting it into the "EMPTY" state.

    NOTE: the timeout you set on this action is propagated to the
    called sub-actions.
    """

    def _action(self):
        if self.telescope.tmc.subarray_node.obsState in [
            ObsState.IDLE,
            ObsState.RESOURCING,
            ObsState.READY,
            ObsState.CONFIGURING,
            ObsState.SCANNING,
        ]:
            abort = SubarrayAbort()
            abort.set_termination_condition_timeout(
                self.termination_condition_timeout
            )
            abort.execute()

        # if there is an ongoing broken abort, ensure it ends before proceeding
        if self.telescope.tmc.subarray_node.obsState == ObsState.ABORTING:
            force_abort = SubarrayForceAbort()
            force_abort.set_termination_condition_timeout(
                self.termination_condition_timeout
            )
            force_abort.execute()

        if self.telescope.tmc.subarray_node.obsState in [
            ObsState.ABORTED,
            ObsState.RESTARTING,
        ]:
            restart = SubarrayRestart()
            restart.set_termination_condition_timeout(
                self.termination_condition_timeout
            )
            # if a restarting process is ongoing, I don't want it to be
            # treated as a long running command
            if (
                self.telescope.tmc.subarray_node.obsState
                == ObsState.RESTARTING
            ):
                restart.is_long_running_command = False

            restart.execute()

        # using separate checks, since this isn't a real "waiting" action
        # but the state changes should have already happened
        assert_that(self.telescope.tmc.subarray_node.obsState).described_as(
            "UNEXPECTED ERROR: The TMC subarray should have reached "
            "the EMPTY state by now. If this error occurs, "
            "something may have gone wrong with "
            "SubarrayClearObsState procedure."
        ).is_equal_to(ObsState.EMPTY)
        assert_that(self.telescope.csp.csp_subarray.obsState).described_as(
            "UNEXPECTED ERROR: The CSP subarray should have reached "
            "the EMPTY state by now. If this error occurs, "
            "something may have gone wrong with "
            "SubarrayClearObsState procedure."
        ).is_equal_to(ObsState.EMPTY)
        assert_that(self.telescope.sdp.sdp_subarray.obsState).described_as(
            "UNEXPECTED ERROR: The SDP subarray should have reached "
            "the EMPTY state by now. If this error occurs, "
            "something may have gone wrong with "
            "SubarrayClearObsState procedure."
        ).is_equal_to(ObsState.EMPTY)

    def termination_condition(self) -> list[ExpectedEvent]:
        """No termination condition is needed for this action."""
        return []
