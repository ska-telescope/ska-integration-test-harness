"""A facade to expose the CSP devices to the tests."""

from tango import DeviceProxy

from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class CSPFacade:
    """A facade to expose the CSP devices to the tests."""

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    @property
    def csp_master(self) -> DeviceProxy:
        """A Tango proxy to the CSP master device."""
        return self._telescope.csp.csp_master

    @property
    def csp_subarray(self) -> DeviceProxy:
        """A Tango proxy to the CSP subarray device."""
        return self._telescope.csp.csp_subarray
