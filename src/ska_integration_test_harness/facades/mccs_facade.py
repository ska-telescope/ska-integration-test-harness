"""A facade to expose MCCS devices to the tests."""

import tango

from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class MCCSFacade:
    """A facade to expose MCCS devices to the tests."""

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    @property
    def mccs_controller(self) -> tango.DeviceProxy:
        """The MCCS controller Tango device proxy."""
        return self._telescope.mccs.mccs_controller

    @property
    def mccs_subarray(self) -> tango.DeviceProxy:
        """The MCCS subarray Tango device proxy."""
        return self._telescope.mccs.mccs_subarray
