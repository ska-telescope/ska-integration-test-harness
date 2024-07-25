"""A wrapper for an emulated SDP."""

from ska_integration_test_harness.emulated.utils.teardown_helper import (
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.structure.sdp_devices import SDPDevices


class EmulatedSDPDevices(SDPDevices):
    """A wrapper for an emulated SDP."""

    def tear_down(self) -> None:
        """Tear down the SDP."""
        EmulatedTeardownHelper.reset_health_state(
            [self.sdp_master, self.sdp_subarray]
        )
        EmulatedTeardownHelper.clear_command_call([self.sdp_subarray])
        EmulatedTeardownHelper.reset_transitions_data([self.sdp_subarray])
        EmulatedTeardownHelper.reset_delay([self.sdp_subarray])
        EmulatedTeardownHelper.unset_defective_status([self.sdp_subarray])

    def clear_command_call(self) -> None:
        """Clear the command call on the SDP."""
        EmulatedTeardownHelper.clear_command_call([self.sdp_subarray])
