"""A collection of configurations for the various test wrappers.

Test harness requires some (more or less constant) configurations, such as the
expected names for the various devices. This module provides
classes to encapsulate these configurations.
"""

from dataclasses import dataclass


@dataclass
class TMCConfiguration:
    """Configuration for a TMC device.

    It contains the names of the various devices that make up the TMC.
    It is initialized with default values.
    """

    # pylint: disable=too-many-instance-attributes

    centralnode_name: str = "ska_mid/tm_central/central_node"
    tmc_subarraynode1_name: str = "ska_mid/tm_subarray_node/1"

    # CSP-related nodes
    tmc_csp_master_leaf_node_name: str = "ska_mid/tm_leaf_node/csp_master"
    tmc_csp_subarray_leaf_node_name: str = (
        "ska_mid/tm_leaf_node/csp_subarray01"
    )

    # SDP-related nodes
    tmc_sdp_master_leaf_node_name: str = "ska_mid/tm_leaf_node/sdp_master"
    tmc_sdp_subarray_leaf_node_name: str = (
        "ska_mid/tm_leaf_node/sdp_subarray01"
    )

    # Dish leaf nodes
    tmc_dish_leaf_node1_name: str = "ska_mid/tm_leaf_node/d0001"
    tmc_dish_leaf_node2_name: str = "ska_mid/tm_leaf_node/d0036"
    tmc_dish_leaf_node3_name: str = "ska_mid/tm_leaf_node/d0063"
    tmc_dish_leaf_node4_name: str = "ska_mid/tm_leaf_node/d0100"

    # NOTE: in TMC hierarchy, is it more sensed to group by master/subarray
    # or by device type?


@dataclass
class CSPConfiguration:
    """Configuration for a CSP device.

    It contains the names of the various devices that make up the CSP.
    It is initialized with default values.
    """

    csp_master_name: str = "mid-csp/control/0"
    csp_subarray1_name: str = "mid-csp/subarray/01"


@dataclass
class SDPConfiguration:
    """Configuration for a SDP device.

    It contains the names of the various devices that make up the SDP.
    It is initialized with default values.
    """

    sdp_master_name: str = "mid-sdp/control/0"
    sdp_subarray1_name: str = "mid-sdp/subarray/01"


@dataclass
class DishesConfiguration:
    """Configuration for the dishes.

    It contains the names of the various dishes.
    It is initialized with default values (which are the ones you will
    have when the dishes are emulated).
    """

    dish_master1_name: str = "ska001/elt/master"
    dish_master2_name: str = "ska036/elt/master"
    dish_master3_name: str = "ska063/elt/master"
    dish_master4_name: str = "ska100/elt/master"
