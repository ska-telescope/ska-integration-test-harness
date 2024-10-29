"""A wrapper for an emulated SDP."""

from ska_integration_test_harness.emulated.utils.teardown_helper import (
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper


class EmulatedSDPWrapper(SDPWrapper):
    """A wrapper for an emulated SDP.

    Differently from the production SDP wrapper, the tear down implements
    the usual procedure for emulated devices.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._configure_transitions()

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific SDP methods and properties

    def _configure_transitions(self) -> None:
        """Configure the needed for SDP emulated subarray."""
        # SDP should do the ABORTING transition
        # self.sdp_subarray.AddTransition('[["ABORTING", 0.5 ]]')

    def tear_down(self) -> None:
        """Tear down the SDP.

        The procedure is the following:
        - Reset the health state for the SDP master and the SDP subarray.
        - Clear the command call on the SDP subarray.
        - Reset the transitions data for the SDP subarray.
        - Reset the delay for the SDP subarray.
        """
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
