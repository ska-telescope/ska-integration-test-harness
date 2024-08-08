"""A factory to generate configurations for the test harness' components."""

import abc
import os

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.emulation_config import (
    EmulationConfiguration,
)
from ska_integration_test_harness.config.other_config import (
    OtherDevicesConfigurations,
)


class ConfigurationReader(abc.ABC):
    """A factory that reads from somewhere the test harness configuration.

    This abstract class defines the interface of a configuration reader
    that is able to generate configurations for the various test harness
    components, such as:

    - TMC
    - CSP
    - SDP
    - the dishes
    - the emulation configuration

    The concrete implementations of this class may read the configuration
    from different sources, such as environment variables and configuration
    files.
    """

    @abc.abstractmethod
    def get_tmc_configuration(self) -> TMCConfiguration:
        """Get the configuration for the TMC.

        return: The TMC configuration.
        """

    @abc.abstractmethod
    def get_csp_configuration(self) -> CSPConfiguration:
        """Get the configuration for the CSP.

        return: The CSP configuration.
        """

    @abc.abstractmethod
    def get_sdp_configuration(self) -> SDPConfiguration:
        """Get the configuration for the SDP.

        return: The SDP configuration.
        """

    @abc.abstractmethod
    def get_dish_configuration(self) -> DishesConfiguration:
        """Get the configuration for the dishes.

        return: The dishes configuration.
        """

    @abc.abstractmethod
    def get_other_configurations(self) -> OtherDevicesConfigurations:
        """Get the other configurations for the telescope.

        return: The other configurations.
        """

    @abc.abstractmethod
    def get_emulation_configuration(self) -> EmulationConfiguration:
        """Get the emulation configuration of the test harness.

        return: The emulation configuration.
        """


class TMCMIDConfigurationReader(ConfigurationReader):
    """The default TMC-MID configuration reader.

    It reads something from the environment variables, something else
    instead is hardcoded.
    """

    # -------------------------------
    # ENV Variables Names

    SDP_SIMULATION_ENABLED_VARNAME = "SDP_SIMULATION_ENABLED"
    CSP_SIMULATION_ENABLED_VARNAME = "CSP_SIMULATION_ENABLED"
    DISH_SIMULATION_ENABLED_VARNAME = "DISH_SIMULATION_ENABLED"

    DISH_NAME_1_VARNAME = "DISH_NAME_1"
    DISH_NAME_36_VARNAME = "DISH_NAME_36"
    DISH_NAME_63_VARNAME = "DISH_NAME_63"
    DISH_NAME_100_VARNAME = "DISH_NAME_100"

    # -------------------------------
    # Emulation Configuration
    # (& initialization)

    def __init__(self):
        """Initialize the configuration factory."""
        self._emulation_configuration: EmulationConfiguration = (
            self._read_emulation_configuration_from_env()
        )

    def get_emulation_configuration(self) -> EmulationConfiguration:
        """The emulation configuration of the test harness (from the ENV).

        return: The emulation configuration.
        """
        return self._emulation_configuration

    def _read_emulation_configuration_from_env(self) -> EmulationConfiguration:
        """Read the emulation configuration from environment variables.

        return: The emulation configuration.
        """
        return EmulationConfiguration(
            csp=self._read_bool_env_var(self.CSP_SIMULATION_ENABLED_VARNAME),
            sdp=self._read_bool_env_var(self.SDP_SIMULATION_ENABLED_VARNAME),
            dish=self._read_bool_env_var(self.DISH_SIMULATION_ENABLED_VARNAME),
        )

    @staticmethod
    def _read_bool_env_var(varname: str) -> bool:
        """Read a boolean value from an environment variable.

        param varname: The name of the environment variable.
        return: The boolean value.
        """
        value = os.getenv(varname, "false")
        return value.lower() == "true"

    # -------------------------------
    # System components Configuration

    def get_tmc_configuration(self):
        """Get the configuration for the TMC."""
        return TMCConfiguration(
            is_emulated=self.get_emulation_configuration().tmc,
            centralnode_name="ska_mid/tm_central/central_node",
            tmc_subarraynode1_name="ska_mid/tm_subarray_node/1",
            tmc_csp_master_leaf_node_name="ska_mid/tm_leaf_node/csp_master",
            tmc_csp_subarray_leaf_node_name="ska_mid/tm_leaf_node/csp_subarray01",  # pylint: disable=line-too-long # noqa: E501
            tmc_sdp_master_leaf_node_name="ska_mid/tm_leaf_node/sdp_master",
            tmc_sdp_subarray_leaf_node_name="ska_mid/tm_leaf_node/sdp_subarray01",  # pylint: disable=line-too-long # noqa: E501
            tmc_dish_leaf_node1_name="ska_mid/tm_leaf_node/d0001",
            tmc_dish_leaf_node2_name="ska_mid/tm_leaf_node/d0036",
            tmc_dish_leaf_node3_name="ska_mid/tm_leaf_node/d0063",
            tmc_dish_leaf_node4_name="ska_mid/tm_leaf_node/d0100",
        )

    def get_csp_configuration(self):
        """Get the configuration for the CSP."""
        return CSPConfiguration(
            is_emulated=self.get_emulation_configuration().csp,
            csp_master_name="mid-csp/control/0",
            csp_subarray1_name="mid-csp/subarray/01",
        )

    def get_sdp_configuration(self):
        """Get the configuration for the SDP."""
        return SDPConfiguration(
            is_emulated=self.get_emulation_configuration().sdp,
            sdp_master_name="mid-sdp/control/0",
            sdp_subarray1_name="mid-sdp/subarray/01",
        )

    def get_dish_configuration(self):
        """Get the configuration for the dishes.

        Since the dish master devices name may change depending on the
        environment (production or emulation), when the dishes are production
        devices, their names are read from the environment, otherwise
        (when emulated) they are set to default values.
        """
        if self.get_emulation_configuration().dish:
            # Default dish names
            return DishesConfiguration(
                dish_master1_name="ska001/elt/master",
                dish_master2_name="ska036/elt/master",
                dish_master3_name="ska063/elt/master",
                dish_master4_name="ska100/elt/master",
            )

        return self._read_dish_names_from_env()

    def _read_dish_names_from_env(self):
        """Read the names of the dishes from the environment variables."""
        return DishesConfiguration(
            dish_master1_name=os.getenv(self.DISH_NAME_1_VARNAME),
            dish_master2_name=os.getenv(self.DISH_NAME_36_VARNAME),
            dish_master3_name=os.getenv(self.DISH_NAME_63_VARNAME),
            dish_master4_name=os.getenv(self.DISH_NAME_100_VARNAME),
        )

    # -------------------------------
    # Other Configurations

    def get_other_configurations(self):
        """Get the other configurations for the telescope.

        These are the configurations that don't fit in the other specific
        configuration classes.
        """
        return OtherDevicesConfigurations()
