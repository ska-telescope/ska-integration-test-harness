"""A collection of configurations for the various test wrappers.

Test harness requires some (more or less constant) configurations, such as the
expected names for the various devices. This module provides
classes to encapsulate these configurations.
"""

import abc
from dataclasses import dataclass


@dataclass
class SubsystemConfiguration(abc.ABC):
    """A generic configuration for a telescope subsystem.

    A subsystem is a collection of devices that are logically grouped together,
    such as CSP, SDP, TMC and the Dishes. This class provides a way to
    encapsulate the names of the devices that make up the subsystem.

    To use this class:

    - extend it,
    - add as attributes your own configuration parameters,
    - implement a few methods to expose attributes containing device names
      and the mandatory attributes.

    A subsystem in the context of SKA can be emulated or a production one.
    This class contains a boolean flag that will specify that. By default,
    all configurations point to emulated devices. You don't need to list the
    ``is_emulated`` attribute in the ``all_attributes``
    """

    is_emulated: bool = True

    @abc.abstractmethod
    def get_device_names(self) -> dict[str, str]:
        """Return all the device names.

        (associated with they "keyword" name in the configuration)

        :return: List of attribute names.
        """

    @abc.abstractmethod
    def mandatory_attributes(self) -> list[str]:
        """Return the names of the mandatory attributes.

        :return: List of attribute names.
        """


@dataclass
class TMCConfiguration(SubsystemConfiguration):
    """Configuration for a TMC device.

    It contains the names of the various devices that make up the TMC.
    It is initialised with default values.
    """

    # pylint: disable=too-many-instance-attributes

    centralnode_name: str = None  # = "ska_mid/tm_central/central_node"
    tmc_subarraynode1_name: str = None  # = "ska_mid/tm_subarray_node/1"

    # CSP-related nodes
    tmc_csp_master_leaf_node_name: str = (
        None  # = "ska_mid/tm_leaf_node/csp_master"
    )
    tmc_csp_subarray_leaf_node_name: str = None  # = (
    #     "ska_mid/tm_leaf_node/csp_subarray01"
    # )

    # SDP-related nodes
    tmc_sdp_master_leaf_node_name: str = (
        None  # = "ska_mid/tm_leaf_node/sdp_master"
    )
    tmc_sdp_subarray_leaf_node_name: str = None  # = (
    #     "ska_mid/tm_leaf_node/sdp_subarray01"
    # )

    # Dish leaf nodes
    tmc_dish_leaf_node1_name: str = None  # = "ska_mid/tm_leaf_node/d0001"
    tmc_dish_leaf_node2_name: str = None  # = "ska_mid/tm_leaf_node/d0036"
    tmc_dish_leaf_node3_name: str = None  # = "ska_mid/tm_leaf_node/d0063"
    tmc_dish_leaf_node4_name: str = None  # = "ska_mid/tm_leaf_node/d0100"

    # NOTE: in TMC hierarchy, is it more sensed to group by master/subarray
    # or by device type?

    def get_device_names(self) -> dict[str, str]:
        return {
            "centralnode_name": self.centralnode_name,
            "tmc_subarraynode1_name": self.tmc_subarraynode1_name,
            "tmc_csp_master_leaf_node_name": (
                self.tmc_csp_master_leaf_node_name
            ),
            "tmc_csp_subarray_leaf_node_name": (
                self.tmc_csp_subarray_leaf_node_name
            ),
            "tmc_sdp_master_leaf_node_name": (
                self.tmc_sdp_master_leaf_node_name
            ),
            "tmc_sdp_subarray_leaf_node_name": (
                self.tmc_sdp_subarray_leaf_node_name
            ),
            "tmc_dish_leaf_node1_name": self.tmc_dish_leaf_node1_name,
            "tmc_dish_leaf_node2_name": self.tmc_dish_leaf_node2_name,
            "tmc_dish_leaf_node3_name": self.tmc_dish_leaf_node3_name,
            "tmc_dish_leaf_node4_name": self.tmc_dish_leaf_node4_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()


@dataclass
class CSPConfiguration(SubsystemConfiguration):
    """Configuration for a CSP device.

    It contains the names of the various devices that make up the CSP.
    It is initialised with default values.
    """

    csp_master_name: str = None  # = "mid-csp/control/0"
    csp_subarray1_name: str = None  # = "mid-csp/subarray/01"

    def get_device_names(self) -> dict[str, str]:
        return {
            "csp_master_name": self.csp_master_name,
            "csp_subarray1_name": self.csp_subarray1_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()


@dataclass
class SDPConfiguration(SubsystemConfiguration):
    """Configuration for a SDP device.

    It contains the names of the various devices that make up the SDP.
    It is initialised with default values.
    """

    sdp_master_name: str = None  # = "mid-sdp/control/0"
    sdp_subarray1_name: str = None  # = "mid-sdp/subarray/01"

    def get_device_names(self) -> dict[str, str]:
        return {
            "sdp_master_name": self.sdp_master_name,
            "sdp_subarray1_name": self.sdp_subarray1_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()


@dataclass
class DishesConfiguration(SubsystemConfiguration):
    """Configuration for the dishes.

    It contains the names of the various dishes.
    It is initialised with default values (which are the ones you will
    have when the dishes are emulated).
    """

    dish_master1_name: str = None  # = "ska001/elt/master"
    dish_master2_name: str = None  # = "ska036/elt/master"
    dish_master3_name: str = None  # = "ska063/elt/master"
    dish_master4_name: str = None  # = "ska100/elt/master"

    def get_device_names(self) -> dict[str, str]:
        return {
            "dish_master1_name": self.dish_master1_name,
            "dish_master2_name": self.dish_master2_name,
            "dish_master3_name": self.dish_master3_name,
            "dish_master4_name": self.dish_master4_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()
