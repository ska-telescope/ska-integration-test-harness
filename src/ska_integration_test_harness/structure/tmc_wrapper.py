"""A wrapper for the TMC component."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    TMCConfiguration,
)


class TMCWrapper(abc.ABC):
    """A wrapper for the TMC component."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, tmc_configuration: TMCConfiguration):
        """Initialise the TMC wrapper.

        Args:
            tmc_configuration: The TMC configuration.
        """
        self.central_node = tango.DeviceProxy(
            tmc_configuration.centralnode_name
        )
        self.central_node.set_timeout_millis(5000)

        self.subarray_node = tango.DeviceProxy(
            tmc_configuration.tmc_subarraynode1_name
        )
        self.subarray_node.set_timeout_millis(5000)

        self.csp_master_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_csp_master_leaf_node_name
        )
        self.sdp_master_leaf_node = tango.DeviceProxy(
            tmc_configuration.tmc_sdp_master_leaf_node_name
        )

        self.dish_leaf_node_list = [  # Those instead are inside TMC
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node1_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node2_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node3_name),
            tango.DeviceProxy(tmc_configuration.tmc_dish_leaf_node4_name),
        ]

        for dish_leaf_node in self.dish_leaf_node_list:
            dish_leaf_node.set_timeout_millis(5000)

        # Create Dish1 leaf node admin device proxy
        self.dish1_leaf_admin_dev_name = self.dish_leaf_node_list[0].adm_name()
        self.dish1_leaf_admin_dev_proxy = tango.DeviceProxy(
            self.dish1_leaf_admin_dev_name
        )

        # Create (but not initialise) the subarray leaf nodes
        self.csp_subarray_leaf_node: tango.DeviceProxy | None = None
        self.sdp_subarray_leaf_node: tango.DeviceProxy | None = None

    # -----------------------------------------------------------
    # CentralNode properties

    @property
    def is_dish_vcc_config_set(self):
        """Return DishVccConfigSet flag"""
        return self.central_node.isDishVccConfigSet

    @property
    def dish_vcc_validation_status(self):
        """Current dish vcc validation status of central node"""
        return self.central_node.DishVccValidationStatus

    # -----------------------------------------------------------
    # Subarray init methods

    def is_subarray_initialised(self) -> bool:
        """Check if the subarray is initialised"""
        return self.csp_subarray_leaf_node and self.sdp_subarray_leaf_node

    def set_subarray_id(self, subarray_id: int):
        """Set subarray ID"""

        self.subarray_node = tango.DeviceProxy(
            f"ska_mid/tm_subarray_node/{subarray_id}"
        )

        # NOTE: why zfill(2) after the first DeviceProxy creation?
        subarray_id = str(subarray_id).zfill(2)

        self.csp_subarray_leaf_node = tango.DeviceProxy(
            f"ska_mid/tm_leaf_node/csp_subarray{subarray_id}"
        )
        self.sdp_subarray_leaf_node = tango.DeviceProxy(
            f"ska_mid/tm_leaf_node/sdp_subarray{subarray_id}"
        )

    # -----------------------------------------------------------
    # Teardown actions

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Reset the TMC devices to their initial state."""
