"""A test wrapper for the MCCS."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    MCCSConfiguration,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)


class MCCSWrapper(SubsystemWrapper, abc.ABC):
    """A test wrapper for the MCCS."""

    def __init__(self, mccs_configuration: MCCSConfiguration):
        """Initialise the MCCS wrapper.

        :param mccs_configuration: The MCCS configuration.
        """
        super().__init__()
        self.mccs_controller = tango.DeviceProxy(
            mccs_configuration.mccs_controller_name
        )
        self.mccs_subarray = tango.DeviceProxy(
            mccs_configuration.mccs_subarray1_name
        )

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "MCCS"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the subsystem devices as a dictionary."""
        return {
            "mccs_controller": self.mccs_controller,
            "mccs_subarray": self.mccs_subarray,
        }

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def set_subarray_id(self, subarray_id: int) -> None:
        """Set the subarray ID."""
        subarray_id = str(subarray_id).zfill(2)
        self.mccs_subarray = tango.DeviceProxy(
            f"low-mccs/subarray/{subarray_id}"
        )

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Tear down the dishes (if needed)."""

    @abc.abstractmethod
    def clear_command_call(self) -> None:
        """Clear the command call on the Dishes (if needed)."""
