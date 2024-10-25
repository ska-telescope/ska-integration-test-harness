"""A test wrapper for the SDP."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    SDPConfiguration,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)


class SDPWrapper(SubsystemWrapper, abc.ABC):
    """A test wrapper for the SDP."""

    def __init__(self, sdp_configuration: SDPConfiguration):
        """Initialise the SDP wrapper.

        :param sdp_configuration: The SDP configuration.
        """
        super().__init__()
        self.sdp_master = tango.DeviceProxy(sdp_configuration.sdp_master_name)
        self.sdp_subarray = tango.DeviceProxy(
            sdp_configuration.sdp_subarray1_name
        )

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "SDP"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the subsystem devices as a dictionary."""
        return {
            "sdp_master": self.sdp_master,
            "sdp_subarray": self.sdp_subarray,
        }

    # --------------------------------------------------------------
    # Specific SDP methods and properties

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
