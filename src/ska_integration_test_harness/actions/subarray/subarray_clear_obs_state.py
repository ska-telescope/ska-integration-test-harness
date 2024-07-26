"""Clear TMC subarray obs state, putting it into the "EMPTY" state."""

from ska_control_model import ObsState

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
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
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
        """Ensure subarrays' final obs state is empty."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.EMPTY)
