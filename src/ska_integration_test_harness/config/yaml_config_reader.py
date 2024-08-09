"""A configuration reader that reads from a YAML file."""

import yaml

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.config_reader import (
    ConfigurationReader,
)
from ska_integration_test_harness.config.emulation_config import (
    EmulationConfiguration,
)


class YAMLConfigurationReader(ConfigurationReader):
    """A configuration reader that reads from a YAML file.

    A configuration reader that creates the needed test harness configurations
    reading everything from a YAML file.

    The YAML file must have the following structure:

    .. code-block:: yaml

        tmc:
            is_emulated: false # Not supported otherwise, default is false

            # Expected device names (Required)
            centralnode_name: "ska_mid/tm_central/central_node"
            tmc_subarraynode1_name: "ska_mid/tm_subarray_node/1"
            tmc_csp_master_leaf_node_name: "ska_mid/tm_leaf_node/csp_master"
            tmc_csp_subarray_leaf_node_name: "ska_mid/tm_leaf_node/csp_subarray01"
            tmc_sdp_master_leaf_node_name: "ska_mid/tm_leaf_node/sdp_master"
            tmc_sdp_subarray_leaf_node_name: "ska_mid/tm_leaf_node/sdp_subarray01"
            tmc_dish_leaf_node1_name: "ska_mid/tm_leaf_node/d0001"
            tmc_dish_leaf_node2_name: "ska_mid/tm_leaf_node/d0036"
            tmc_dish_leaf_node3_name: "ska_mid/tm_leaf_node/d0063"
            tmc_dish_leaf_node4_name: "ska_mid/tm_leaf_node/d0100"

        csp:
            is_emulated: false # Supported true too, default is true

            # Expected device names
            csp_master_name: "mid-csp/control/0"
            csp_subarray1_name: "mid-csp/subarray/01"

        sdp:
            is_emulated: true # Supported false too, default is true

            # Expected device names (Required)
            sdp_master_name: "mid-sdp/elt/master"
            sdp_subarray1_name: "mid-sdp/elt/subarray01"

        dishes:
            is_emulated: true # Supported false too, default is true

            # Expected device names (Required)
            dish_master1_name: "ska001/elt/master"
            dish_master2_name: "ska036/elt/master"
            dish_master3_name: "ska063/elt/master"
            dish_master4_name: "ska100/elt/master"

    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(self, filename: str) -> None:
        """Create a new YAMLConfigurationReader.

        :param filename: The path to the YAML file you want to read

        :raises FileNotFoundError: If the file doesn't exist.
        :raises yaml.YAMLError: If the file is not a valid YAML file.
        """

        super().__init__()
        self.filename = filename
        self.config_as_dict = self._read_file()

    def _read_file(self) -> dict:
        """Read the YAML file and return the content as a dictionary.

        :return: The content of the YAML file as a dictionary.
        :raises FileNotFoundError: If the file doesn't exist.
        :raises yaml.YAMLError: If the file is not a valid YAML file.
        """
        with open(self.filename, "r", encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def _get_subsystem_dict(self, subsystem: str) -> dict:
        """Get the configuration for a subsystem.

        :param subsystem: The name of the subsystem.
        :return: The configuration for the subsystem.
        :raises ValueError: If the configuration is missing or invalid.
        """
        subsystem_dict = self.config_as_dict.get(subsystem)
        if not isinstance(subsystem_dict, dict):
            raise ValueError(
                f"In the given YAML file '{self.filename}', "
                f"the '{subsystem}' section is missing or "
                "it isn't a dictionary."
            )
        return subsystem_dict

    def get_tmc_configuration(self) -> TMCConfiguration:
        """Get the configuration for the TMC.

        :return: The TMC configuration
        :raises ValueError: If the configuration is missing or invalid.
        """
        tmc = self._get_subsystem_dict("tmc")

        return TMCConfiguration(
            is_emulated=tmc.get("is_emulated", False),
            centralnode_name=tmc.get("centralnode_name"),
            tmc_subarraynode1_name=tmc.get("tmc_subarraynode1_name"),
            tmc_csp_master_leaf_node_name=tmc.get(
                "tmc_csp_master_leaf_node_name"
            ),
            tmc_csp_subarray_leaf_node_name=tmc.get(
                "tmc_csp_subarray_leaf_node_name"
            ),
            tmc_sdp_master_leaf_node_name=tmc.get(
                "tmc_sdp_master_leaf_node_name"
            ),
            tmc_sdp_subarray_leaf_node_name=tmc.get(
                "tmc_sdp_subarray_leaf_node_name"
            ),
            tmc_dish_leaf_node1_name=tmc.get("tmc_dish_leaf_node1_name"),
            tmc_dish_leaf_node2_name=tmc.get("tmc_dish_leaf_node2_name"),
            tmc_dish_leaf_node3_name=tmc.get("tmc_dish_leaf_node3_name"),
            tmc_dish_leaf_node4_name=tmc.get("tmc_dish_leaf_node4_name"),
        )

    def get_csp_configuration(self):
        """Get the configuration for the CSP.

        :return: The CSP configuration
        :raises ValueError: If the configuration is missing or invalid.
        """
        csp = self._get_subsystem_dict("csp")

        return CSPConfiguration(
            is_emulated=csp.get("is_emulated", True),
            csp_master_name=csp.get("csp_master_name"),
            csp_subarray1_name=csp.get("csp_subarray1_name"),
        )

    def get_sdp_configuration(self):
        """Get the configuration for the SDP.

        :return: The SDP configuration
        :raises ValueError: If the configuration is missing or invalid.
        """
        sdp = self._get_subsystem_dict("sdp")

        return SDPConfiguration(
            is_emulated=sdp.get("is_emulated", True),
            sdp_master_name=sdp.get("sdp_master_name"),
            sdp_subarray1_name=sdp.get("sdp_subarray1_name"),
        )

    def get_dish_configuration(self):
        """Get the configuration for the Dish.

        :return: The Dish configuration
        :raises ValueError: If the configuration is missing or invalid.
        """
        dish = self._get_subsystem_dict("dishes")

        return DishesConfiguration(
            is_emulated=dish.get("is_emulated", True),
            dish_master1_name=dish.get("dish_master1_name"),
            dish_master2_name=dish.get("dish_master2_name"),
            dish_master3_name=dish.get("dish_master3_name"),
            dish_master4_name=dish.get("dish_master4_name"),
        )

    def get_emulation_configuration(self):
        """Get the emulation configuration.

        :return: The emulation configuration
        :raises ValueError: If the configuration of TMC, CSP, SDP or Dish
            is missing or invalid.
        """
        return EmulationConfiguration(
            tmc=self.get_tmc_configuration().is_emulated,
            csp=self.get_csp_configuration().is_emulated,
            sdp=self.get_sdp_configuration().is_emulated,
            dish=self.get_dish_configuration().is_emulated,
        )
