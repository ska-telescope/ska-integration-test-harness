"""Subclass of Abort action that forces the abort if it failed."""

import logging

import tango
from ska_control_model import ObsState

from ska_integration_test_harness.actions.subarray.subarray_abort import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAbort,
)

LOGGER = logging.getLogger(__name__)


class SubarrayForceAbort(SubarrayAbort):
    """Invoke Abort command on subarray Node and force it if it failed."""

    def _devices_that_should_abort(self) -> list[tango.DeviceProxy]:
        """Return the list of devices that should be aborted."""
        devices_that_should_abort = [
            self.telescope.csp.csp_subarray,
            self.telescope.sdp.sdp_subarray,
            self.telescope.tmc.subarray_node,
        ]
        # if self.telescope.tmc.is_subarray_initialized():
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
        LOGGER.info("Forcing Abort on each subarray device.")
        for device in self._devices_that_should_abort():
            if device.obsState not in self._ok_states():
                device.Abort()

    # (termination codition is the same as the parent class - i.e.,
    # wait for all devices to reach ABORTED state)
