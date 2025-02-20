"""A facade to expose the CSP devices to the tests."""

import tango

from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class CSPFacade:
    """A facade to expose the CSP devices to the tests."""

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    @property
    def csp_master(self) -> tango.DeviceProxy:
        """A Tango proxy to the CSP master device."""
        return self._telescope.csp.csp_master

    @property
    def csp_subarray(self) -> tango.DeviceProxy:
        """A Tango proxy to the CSP subarray device."""
        return self._telescope.csp.csp_subarray

    @property
    def pst(self) -> "tango.DeviceProxy | None":
        """A Tango proxy to the PST device.

        It is available only when the target is 'low'.
        """
        if not self._telescope.tmc.supports_low():
            raise ValueError("PST is available only in 'low' mode")

        if hasattr(self._telescope.csp, "pst"):
            return self._telescope.csp.pst

        return None
