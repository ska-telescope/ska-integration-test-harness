"""A collection of configurations for the various test wrappers.

Test harness requires some (more or less constant) configurations, such as the
expected names for the various devices. This module provides
classes to encapsulate these configurations.
"""

import abc
from dataclasses import dataclass, field


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

    target: str = "mid"
    """
    The target environment for the subsystem.

    It can be "mid" (default) or "low".
    """

    def supports_mid(self) -> bool:
        """Check if the configuration supports the mid target environment."""
        return self.target == "mid"

    def supports_low(self) -> bool:
        """Check if the configuration supports the low target environment."""
        return self.target == "low"

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

    # Central node name
    centralnode_name: str = None

    # Controllers leaf nodes names
    tmc_csp_master_leaf_node_name: str = None
    tmc_sdp_master_leaf_node_name: str = None
    tmc_mccs_master_leaf_node_name: str | None = None

    # Subarray nodes names
    subarrays_names: dict[int, str] = field(default_factory=dict)
    tmc_csp_subarrays_leaf_nodes_names: dict[int, str] = field(
        default_factory=dict
    )
    tmc_sdp_subarrays_leaf_nodes_names: dict[int, str] = field(
        default_factory=dict
    )
    tmc_mccs_subarrays_leaf_nodes_names: dict[int, str] = field(
        default_factory=dict
    )

    @property
    def tmc_subarraynode1_name(self) -> str:
        """Get the name of the first subarray node."""
        return self.subarrays_names.get(1)

    @property
    def tmc_sdp_subarray_leaf_node_name(self) -> str:
        """Get the name of the first subarray node."""
        return self.tmc_sdp_subarrays_leaf_nodes_names.get(1)

    @property
    def tmc_csp_subarray_leaf_node_name(self) -> str:
        """Get the name of the first subarray node."""
        return self.tmc_csp_subarrays_leaf_nodes_names.get(1)

    @property
    def tmc_mccs_subarray_leaf_node_name(self) -> str:
        """Get the name of the first subarray node."""
        return self.tmc_mccs_subarrays_leaf_nodes_names.get(1)

    # Dish leaf nodes
    tmc_dish_leaf_node1_name: str = None
    tmc_dish_leaf_node2_name: str = None
    tmc_dish_leaf_node3_name: str = None
    tmc_dish_leaf_node4_name: str = None

    target: str = "mid"
    """
    The target environment for the TMC. It can be "mid" (default) or "low".
    """

    def supports_mid(self) -> bool:
        """Check if the configuration supports the mid target environment."""
        return self.target == "mid"

    def supports_low(self) -> bool:
        """Check if the configuration supports the low target environment."""
        return self.target == "low"

    def get_device_names(self) -> dict[str, str]:
        all_devices = {
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
        }

        if self.supports_mid():
            all_devices.update(
                {
                    "tmc_dish_leaf_node1_name": self.tmc_dish_leaf_node1_name,
                    "tmc_dish_leaf_node2_name": self.tmc_dish_leaf_node2_name,
                    "tmc_dish_leaf_node3_name": self.tmc_dish_leaf_node3_name,
                    "tmc_dish_leaf_node4_name": self.tmc_dish_leaf_node4_name,
                }
            )

        if self.supports_low():
            all_devices.update(
                {
                    "tmc_mccs_master_leaf_node_name": (
                        self.tmc_mccs_master_leaf_node_name
                    ),
                    "tmc_mccs_subarray_leaf_node_name": (
                        self.tmc_mccs_subarray_leaf_node_name
                    ),
                }
            )

        return all_devices

    def mandatory_attributes(self) -> list[str]:
        mandatory_device_names = [
            "centralnode_name",
            "tmc_subarraynode1_name",
            "tmc_csp_master_leaf_node_name",
            "tmc_csp_subarray_leaf_node_name",
            "tmc_sdp_master_leaf_node_name",
            "tmc_sdp_subarray_leaf_node_name",
        ]

        if self.supports_mid():
            mandatory_device_names.extend(
                [
                    "tmc_dish_leaf_node1_name",
                    "tmc_dish_leaf_node2_name",
                    "tmc_dish_leaf_node3_name",
                    "tmc_dish_leaf_node4_name",
                ]
            )

        if self.supports_low():
            mandatory_device_names.extend(
                [
                    "tmc_mccs_master_leaf_node_name",
                    "tmc_mccs_subarray_leaf_node_name",
                ]
            )

        return mandatory_device_names


@dataclass
class CSPConfiguration(SubsystemConfiguration):
    """Configuration for a CSP device.

    It contains the names of the various devices that make up the CSP.
    It is initialised with default values.
    """

    csp_master_name: str = None
    csp_subarrays_names: dict[int, str] = field(default_factory=dict)

    # At the moment the following are required just for low
    pst_name: str | None = None

    @property
    def csp_subarray1_name(self) -> str:
        """Get the name of the first subarray."""
        return self.csp_subarrays_names.get(1)

    def get_device_names(self) -> dict[str, str]:
        dev_names = {
            "csp_master_name": self.csp_master_name,
            "csp_subarray1_name": self.csp_subarray1_name,
        }

        # NOTE: maybe PST is available only after the Online mode thing
        # removed that check for now, since it fails.

        return dev_names

    def mandatory_attributes(self) -> list[str]:
        attrs = [
            "csp_master_name",
            "csp_subarray1_name",
        ]

        # TODO: check if it's really necessary and if it isn't, remove it
        if not self.is_emulated and self.supports_low():
            attrs.append("pst_name")

        return attrs


@dataclass
class SDPConfiguration(SubsystemConfiguration):
    """Configuration for a SDP device.

    It contains the names of the various devices that make up the SDP.
    It is initialised with default values.
    """

    sdp_master_name: str = None
    sdp_subarrays_names: dict[int, str] = field(default_factory=dict)

    @property
    def sdp_subarray1_name(self) -> str:
        """Get the name of the first subarray."""
        return self.sdp_subarrays_names.get(1)

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

    dish_master1_name: str = None
    dish_master2_name: str = None
    dish_master3_name: str = None
    dish_master4_name: str = None

    def get_device_names(self) -> dict[str, str]:
        return {
            "dish_master1_name": self.dish_master1_name,
            "dish_master2_name": self.dish_master2_name,
            "dish_master3_name": self.dish_master3_name,
            "dish_master4_name": self.dish_master4_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()


@dataclass
class MCCSConfiguration(SubsystemConfiguration):
    """Configuration for the MCCS.

    It contains the names of the various devices that make up the MCCS.
    It is initialised with default values.
    """

    mccs_controller_name: str = None
    mccs_subarrays_names: dict[int, str] = field(default_factory=dict)

    @property
    def mccs_subarray1_name(self) -> str:
        """Get the name of the first subarray."""
        return self.mccs_subarrays_names.get(1)

    def get_device_names(self) -> dict[str, str]:
        return {
            "mccs_controller_name": self.mccs_controller_name,
            "mccs_subarray1_name": self.mccs_subarray1_name,
        }

    def mandatory_attributes(self) -> list[str]:
        return self.get_device_names().keys()
