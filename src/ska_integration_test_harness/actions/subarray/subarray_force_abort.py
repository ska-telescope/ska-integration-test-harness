"""Subclass of Abort action that forces the abort if it failed."""

import tango
from ska_control_model import ObsState

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)


class SubarrayForceAbort(TelescopeAction[None]):
    """Foreach of the individual subarray devices, force an abort if an
    abort process is not ongoing."""

    def _devices_that_should_abort(self) -> list[tango.DeviceProxy]:
        """Return the list of devices that should be aborted."""
        devices_that_should_abort = [
            self.telescope.csp.csp_subarray,
            self.telescope.sdp.sdp_subarray,
            self.telescope.tmc.subarray_node,
        ]
        # if self.telescope.tmc.is_subarray_initialised():
        #     devices_that_should_abort.extend(
        #         [
        #             self.telescope.tmc.csp_subarray_leaf_node,
        #             self.telescope.tmc.sdp_subarray_leaf_node,
        #         ]
        #     )
        return devices_that_should_abort

    def _ok_states(self) -> list[ObsState]:
        """Return the list of states that are considered OK."""
        return [ObsState.ABORTED, ObsState.ABORTING]

    def _action(self):
        for device in self._devices_that_should_abort():
            if device.obsState not in self._ok_states():
                self._log(f"Forcing Abort on {device.dev_name()}")
                device.Abort()

    def termination_condition(self):
        """All subarrays must be in ABORTED state."""
        return all_subarrays_have_obs_state(self.telescope, ObsState.ABORTED)
