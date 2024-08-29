"""Sets the receive addresses attribute on SDP Subarray so an event can
be simulated for Subarray Node to process.
"""

import msgpack
import msgpack_numpy
from tango import DeviceProxy

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.config.config_reader import (  # pylint: disable=line-too-long # noqa: E501
    TMCMIDConfigurationReader,
)
from ska_integration_test_harness.inputs.hardcoded_values import (
    HardcodedValues,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarraySimulateReceiveAddresses(TelescopeAction[None]):
    """Sets the receive addresses attribute on SDP Subarray so an event can
    be simulated for Subarray Node to process.
    """

    def __init__(
        self,
        sdp_sim,
        receive_addresses_input: JSONInput,
    ):
        super().__init__()
        self.sdp_sim = sdp_sim
        self.receive_addresses_input = receive_addresses_input

    def _action(self):
        # TODO: change with a ref to some SDP device
        self.sdp_sim.SetDirectreceiveAddresses(
            self.receive_addresses_input.as_str()
        )

        # Setting pointing offsets after encoding the data.
        sdp_qc = DeviceProxy(
            TMCMIDConfigurationReader()
            .get_other_configurations()
            .sdp_queue_connector
        )
        encoded_data = msgpack.packb(
            HardcodedValues().pointing_offsets, default=msgpack_numpy.encode
        )
        sdp_qc.SetDirectPointingOffsets(("msgpack_numpy", encoded_data))

    def termination_condition(self):
        return []
