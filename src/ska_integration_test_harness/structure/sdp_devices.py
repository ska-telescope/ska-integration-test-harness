"""A test wrapper for the SDP."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    SDPConfiguration,
)


class SDPDevices(abc.ABC):
    """A test wrapper for the SDP."""

    def __init__(self, sdp_configuration: SDPConfiguration):
        """Initialize the SDP wrapper."""
        self.sdp_master = tango.DeviceProxy(sdp_configuration.sdp_master_name)
        self.sdp_subarray = tango.DeviceProxy(
            sdp_configuration.sdp_subarray1_name
        )

    def set_subarray_id(self, subarray_id: str) -> None:
        """Set the subarray ID on the SDP subarray."""
        subarray_id = str(subarray_id).zfill(2)
        self.sdp_subarray = tango.DeviceProxy(
            f"mid-sdp/subarray/{subarray_id}"
        )

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Tear down the SDP (if needed)."""

    @abc.abstractmethod
    def clear_command_call(self) -> None:
        """Clear the command call on the SDP (if needed)."""
