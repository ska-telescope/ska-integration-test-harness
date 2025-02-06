"""A wrapper for a production SDP."""

from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper


class ProductionSDPWrapper(SDPWrapper):
    """A wrapper for a production SDP."""

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False
