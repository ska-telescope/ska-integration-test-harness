"""A wrapper for the TMC component."""

import abc

import tango

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
)
from ska_integration_test_harness.config.components_config import (
    TMCConfiguration,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)


class TMCWrapper(SubsystemWrapper, abc.ABC):
    """A wrapper for the TMC component."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, tmc_configuration: TMCConfiguration):
        """Initialise the TMC wrapper.

        :param tmc_configuration: The TMC configuration.
        """
        super().__init__()
        self.central_node = tango.DeviceProxy(
            tmc_configuration.centralnode_name
        )
        self.subarray_node = tango.DeviceProxy(
            tmc_configuration.tmc_subarraynode1_name
        )
        self.csp_master_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_csp_master_leaf_node_name
        )
        self.sdp_master_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_sdp_master_leaf_node_name
        )
        self.csp_subarray_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_csp_subarray_leaf_node_name
        )
        self.sdp_subarray_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_sdp_subarray_leaf_node_name
        )

        if tmc_configuration.supports_mid():
            self.dish_leaf_node_list = [
                tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node1_name),
                tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node2_name),
                tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node3_name),
                tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node4_name),
            ]

        if tmc_configuration.supports_low():
            self.mccs_master_leaf_node = tango.DeviceProxy(
                tmc_configuration.tmc_mccs_master_leaf_node_name
            )
            self.mccs_subarray_leaf_node = tango.DeviceProxy(
                tmc_configuration.tmc_mccs_subarray_leaf_node_name
            )

        # TODO: Use a tango dev factory instead of DeviceProxy

        self.config = tmc_configuration

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "TMC"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the subsystem devices as a dictionary."""
        res = {
            "central_node": self.central_node,
            "subarray_node": self.subarray_node,
            "csp_master_leaf_node": self.csp_master_leaf_node,
            "sdp_master_leaf_node": self.sdp_master_leaf_node,
        }

        if self.csp_subarray_leaf_node is not None:
            res["csp_subarray_leaf_node"] = self.csp_subarray_leaf_node

        if self.sdp_subarray_leaf_node is not None:
            res["sdp_subarray_leaf_node"] = self.sdp_subarray_leaf_node

        if self.supports_mid():
            res["dish_leaf_node_001"] = self.dish_leaf_node_list[0]
            res["dish_leaf_node_036"] = self.dish_leaf_node_list[1]
            res["dish_leaf_node_063"] = self.dish_leaf_node_list[2]
            res["dish_leaf_node_100"] = self.dish_leaf_node_list[3]

        if self.supports_low():
            res["mccs_master_leaf_node"] = self.mccs_master_leaf_node
            res["mccs_subarray_leaf_node"] = self.mccs_subarray_leaf_node

        return res

    def get_recap(
        self, devices_info_provider: DevicesInfoProvider | None = None
    ) -> str:
        recap = super().get_recap(devices_info_provider)

        # if the devices are not yet set, we add a note in the recap
        if self.csp_subarray_leaf_node is None:
            recap += "- csp_subarray_leaf_node: not yet set\n"

        if self.sdp_subarray_leaf_node is None:
            recap += "- sdp_subarray_leaf_node: not yet set\n"

        return recap

    # --------------------------------------------------------------
    # Specific TMC methods and properties

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Reset the TMC devices to their initial state."""

    def is_subarray_initialised(self) -> bool:
        """Check if the subarray is initialised"""
        return self.csp_subarray_leaf_node and self.sdp_subarray_leaf_node

    def set_subarray_id(self, subarray_id: int):
        """Set subarray ID"""
        target = "low" if self.config.supports_low() else "mid"
        self.subarray_node = tango.DeviceProxy(
            f"ska_{target}/tm_subarray_node/{subarray_id}"
        )

        # adapt subarray ID name to the format used in the leaf nodes
        subarray_id = str(subarray_id).zfill(2)
        self.csp_subarray_leaf_node = tango.DeviceProxy(
            f"ska_{target}/tm_leaf_node/csp_subarray{subarray_id}"
        )
        self.sdp_subarray_leaf_node = tango.DeviceProxy(
            f"ska_{target}/tm_leaf_node/sdp_subarray{subarray_id}"
        )

    def supports_low(self) -> bool:
        """Check if the configuration supports the low target environment."""
        return self.config.supports_low()

    def supports_mid(self) -> bool:
        """Check if the configuration supports the mid target environment."""
        return self.config.supports_mid()
