"""A wrapper for an emulated SDP."""

from ska_integration_test_harness.emulated.utils.teardown_helper import (
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.inputs.json_input import DictJSONInput
from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper


class EmulatedSDPWrapper(SDPWrapper):
    """A wrapper for an emulated SDP.

    Differently from the production SDP wrapper, the tear down implements
    the usual procedure for emulated devices.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.config.supports_low():
            # configure the receive address
            self.configure_receive_address()

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific SDP methods and properties

    def configure_receive_address(self):
        """Configure the receive address for the SDP subarray."""
        receive_address = DictJSONInput(
            {
                "science_A": {
                    "host": [[0, "192.168.0.1"], [2000, "192.168.0.1"]],
                    "port": [[0, 9000, 1], [2000, 9000, 1]],
                },
                "target:a": {
                    "vis0": {
                        "function": "visibilities",
                        "visibility_beam_id": 1,
                        "host": [
                            [0, "192.168.0.1"],
                        ],
                        "port": [
                            [0, 9000, 1],
                        ],
                        "mac": [
                            [0, "06-00-00-00-00-00"],
                        ],
                    }
                },
                "calibration:b": {
                    "vis0": {
                        "function": "visibilities",
                        "host": [
                            [0, "192.168.0.1"],
                            [400, "192.168.0.2"],
                            [744, "192.168.0.3"],
                            [1144, "192.168.0.4"],
                        ],
                        "port": [
                            [0, 9000, 1],
                            [400, 9000, 1],
                            [744, 9000, 1],
                            [1144, 9000, 1],
                        ],
                        "mac": [
                            [0, "06-00-00-00-00-00"],
                            [744, "06-00-00-00-00-01"],
                        ],
                    }
                },
            }
        )
        self.sdp_subarray.SetDirectreceiveAddresses(receive_address.as_str())

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
