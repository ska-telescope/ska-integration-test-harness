"""A wrapper for a production SDP."""

from ska_integration_test_harness.structure.sdp_wrapper import SDPDevices


class ProductionSDPDevices(SDPDevices):
    """A wrapper for a production SDP."""

    def tear_down(self) -> None:
        """Tear down the CSP (not needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the SDP (not needed)."""
