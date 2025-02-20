"""A test wrapper for the CSP."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)


class CSPWrapper(SubsystemWrapper, abc.ABC):
    """A test wrapper for the CSP."""

    def __init__(self, csp_configuration: CSPConfiguration):
        """Initialise the CSP wrapper.

        :param csp_configuration: The CSP configuration.
        """
        super().__init__()
        self.csp_master = tango.DeviceProxy(csp_configuration.csp_master_name)
        self.csp_subarray = tango.DeviceProxy(
            csp_configuration.csp_subarray1_name
        )
        self.config = csp_configuration

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "CSP"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the subsystem devices as a dictionary."""
        return {
            "csp_master": self.csp_master,
            "csp_subarray": self.csp_subarray,
        }

    # --------------------------------------------------------------
    # Specific CSP methods and properties

    def tear_down(self) -> None:
        """Tear down the CSP (if needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (if needed)."""

    def set_subarray_id(self, subarray_id: str) -> None:
        """Set the subarray ID on the CSP subarray."""
        subarray_id = str(subarray_id).zfill(2)
        target = "low" if self.config.supports_low() else "mid"

        self.csp_subarray = tango.DeviceProxy(
            f"{target}-csp/subarray/{subarray_id}"
        )
