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
        self.dish_leaf_node_list = [
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node1_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node2_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node3_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node4_name),
        ]
        self.csp_subarray_leaf_node = None
        self.sdp_subarray_leaf_node = None

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "TMC"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the sub-system devices as a dictionary."""
        res = {
            "central_node": self.central_node,
            "subarray_node": self.subarray_node,
            "csp_master_leaf_node": self.csp_master_leaf_node,
            "sdp_master_leaf_node": self.sdp_master_leaf_node,
            "dish_leaf_nodes": self.dish_leaf_node_list,
        }

        if self.csp_subarray_leaf_node is not None:
            res["csp_subarray_leaf_node"] = self.csp_subarray_leaf_node

        if self.sdp_subarray_leaf_node is not None:
            res["sdp_subarray_leaf_node"] = self.sdp_subarray_leaf_node

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

    # --------------------------------------------------------------
    # Specific TMC methods and properties

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Reset the TMC devices to their initial state."""
