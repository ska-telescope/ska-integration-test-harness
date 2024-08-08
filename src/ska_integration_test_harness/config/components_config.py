"""A collection of configurations for the various test wrappers.

Test harness requires some (more or less constant) configurations, such as the
expected names for the various devices. This module provides
classes to encapsulate these configurations.
"""

import abc
from dataclasses import dataclass


@dataclass
class SubsystemConfiguration(abc.ABC):
    """Configuration for a telescope subsystem.

    A subsystem is a collection of devices that are logically grouped together,
    such as CSP, SDP, TMC and the Dishes. This class provides a way to
    encapsulate the names of the devices that make up the subsystem.

    To use this class:

    - extend it,
    - add as attributes your own configuration parameters,
    - implement the method ``all_attributes`` that returns a list of all
      attribute names,
    - optionally, override the methods ``attributes_with_device_names`` and
      ``mandatory_attributes`` to specify which attributes contain device names
      and which are mandatory (useful for further validation).

    A subsystem in the context of SKA can be emulated or a production one.
    This class contains a boolean flag that will specify that. By default,
    all configurations point to emulated devices. You don't need to list the
    ``is_emulated`` attribute in the ``all_attributes``
    """

    is_emulated: bool = True

    @abc.abstractmethod
    def all_attributes(self) -> list[str]:
        """Return the names of all attributes.

        :return: List of attribute names.
        """

    @abc.abstractmethod
    def attributes_with_device_names(self) -> list[str]:
        """Return the names of the attributes that contain device names.

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
    It is initialized with default values.
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

    def all_attributes(self) -> list[str]:
        return [
            "centralnode_name",
            "tmc_subarraynode1_name",
            "tmc_csp_master_leaf_node_name",
            "tmc_csp_subarray_leaf_node_name",
            "tmc_sdp_master_leaf_node_name",
            "tmc_sdp_subarray_leaf_node_name",
            "tmc_dish_leaf_node1_name",
            "tmc_dish_leaf_node2_name",
            "tmc_dish_leaf_node3_name",
            "tmc_dish_leaf_node4_name",
        ]

    def attributes_with_device_names(self) -> list[str]:
        return self.all_attributes()

    def mandatory_attributes(self) -> list[str]:
        return self.all_attributes()


@dataclass
class CSPConfiguration(SubsystemConfiguration):
    """Configuration for a CSP device.

    It contains the names of the various devices that make up the CSP.
    It is initialized with default values.
    """

    csp_master_name: str = None  # = "mid-csp/control/0"
    csp_subarray1_name: str = None  # = "mid-csp/subarray/01"

    def attributes_with_device_names(self) -> list[str]:
        return ["csp_master_name", "csp_subarray1_name"]

    def mandatory_attributes(self) -> list[str]:
        return self.attributes_with_device_names()

    def all_attributes(self) -> list[str]:
        return self.attributes_with_device_names()


@dataclass
class SDPConfiguration(SubsystemConfiguration):
    """Configuration for a SDP device.

    It contains the names of the various devices that make up the SDP.
    It is initialized with default values.
    """

    sdp_master_name: str = None  # = "mid-sdp/control/0"
    sdp_subarray1_name: str = None  # = "mid-sdp/subarray/01"

    def attributes_with_device_names(self) -> list[str]:
        return ["sdp_master_name", "sdp_subarray1_name"]

    def mandatory_attributes(self) -> list[str]:
        return self.attributes_with_device_names()

    def all_attributes(self) -> list[str]:
        return self.attributes_with_device_names()


@dataclass
class DishesConfiguration(SubsystemConfiguration):
    """Configuration for the dishes.

    It contains the names of the various dishes.
    It is initialized with default values (which are the ones you will
    have when the dishes are emulated).
    """

    dish_master1_name: str = None  # = "ska001/elt/master"
    dish_master2_name: str = None  # = "ska036/elt/master"
    dish_master3_name: str = None  # = "ska063/elt/master"
    dish_master4_name: str = None  # = "ska100/elt/master"

    def all_attributes(self) -> list[str]:
        return [
            "dish_master1_name",
            "dish_master2_name",
            "dish_master3_name",
            "dish_master4_name",
        ]

    def attributes_with_device_names(self) -> list[str]:
        return self.all_attributes()

    def mandatory_attributes(self) -> list[str]:
        return self.all_attributes()
