"""A wrapper for the TMC component."""

import abc

from tango import DeviceProxy

from ska_integration_test_harness.config.components_config import (
    TMCConfiguration,
)


class TMCDevices(abc.ABC):
    """A wrapper for the TMC component."""

    def __init__(self, tmc_configuration: TMCConfiguration):
        """Initialise the TMC wrapper.

        Args:
            tmc_configuration: The TMC configuration.
        """
        self.central_node = DeviceProxy(tmc_configuration.centralnode_name)
        self.central_node.set_timeout_millis(5000)

        self.subarray_node = DeviceProxy(
            tmc_configuration.tmc_subarraynode1_name
        )
        self.subarray_node.set_timeout_millis(5000)

        self.csp_master_leaf_node = DeviceProxy(
            tmc_configuration.tmc_csp_master_leaf_node_name
        )
        self.sdp_master_leaf_node = DeviceProxy(
            tmc_configuration.tmc_sdp_master_leaf_node_name
        )

        # NOTE: not so much used EXTERNALLY, internally just on this
        # constructor. So what is the sense of this list?
        self.dish_leaf_node_list = [  # Those instead are inside TMC
            DeviceProxy(tmc_configuration.tmc_dish_leaf_node1_name),
            DeviceProxy(tmc_configuration.tmc_dish_leaf_node2_name),
            DeviceProxy(tmc_configuration.tmc_dish_leaf_node3_name),
            DeviceProxy(tmc_configuration.tmc_dish_leaf_node4_name),
        ]

        for dish_leaf_node in self.dish_leaf_node_list:
            dish_leaf_node.set_timeout_millis(5000)

        # Create Dish1 leaf node admin device proxy
        self.dish1_leaf_admin_dev_name = self.dish_leaf_node_list[0].adm_name()
        self.dish1_leaf_admin_dev_proxy = DeviceProxy(
            self.dish1_leaf_admin_dev_name
        )

        # Create (but not initialize) the subarray leaf nodes
        self.csp_subarray_leaf_node: DeviceProxy | None = None
        self.sdp_subarray_leaf_node: DeviceProxy | None = None

    # -----------------------------------------------------------
    # CentralNode properties

    @property
    def IsDishVccConfigSet(self):
        """Return DishVccConfigSet flag"""
        return self.central_node.isDishVccConfigSet

    @property
    def DishVccValidationStatus(self):
        """Current dish vcc validation status of central node"""
        return self.central_node.DishVccValidationStatus

    # -----------------------------------------------------------
    # Subarray init methods

    def is_subarray_initialized(self) -> bool:
        """Check if the subarray is initialized"""
        return self.csp_subarray_leaf_node and self.sdp_subarray_leaf_node

    def set_subarray_id(self, subarray_id: int):
        """Set subarray ID"""

        self.subarray_node = DeviceProxy(
            f"ska_mid/tm_subarray_node/{subarray_id}"
        )

        # NOTE: why zfill(2) after the first DeviceProxy creation?
        subarray_id = str(subarray_id).zfill(2)

        self.csp_subarray_leaf_node = DeviceProxy(
            f"ska_mid/tm_leaf_node/csp_subarray{subarray_id}"
        )
        self.sdp_subarray_leaf_node = DeviceProxy(
            f"ska_mid/tm_leaf_node/sdp_subarray{subarray_id}"
        )

    # -----------------------------------------------------------
    # Teardown actions

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Reset the TMC devices to their initial state."""
