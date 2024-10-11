"""A wrapper for a production SDP."""

from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper


class ProductionSDPWrapper(SDPWrapper):
    """A wrapper for a production SDP."""

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific SDP methods and properties

    def tear_down(self) -> None:
        """Tear down the CSP (not needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the SDP (not needed)."""
