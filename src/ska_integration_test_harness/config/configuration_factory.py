"""A factory to generate configurations for the test harness' components."""

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


class TestHarnessConfigurationFactory:
    """A factory to generate configurations for the test harness' components.

    This class is a tool to generate configurations for the various
    test harness components, such as:

    - TMC
    - CSP
    - SDP
    - the dishes

    It is also used to read the configuration that specifies which components
    are emulated and which are production ones.

    Since some configurations are static, some are read from the environment
    and some depend on the emulation configuration, to keep things
    consistent (without having global variables) every time an instance of
    this class is created, the emulation configuration is read from the
    environment and then the other configurations are generated accordingly.
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
        self._emulation_configuration = (
            self._read_emulation_configuration_from_env()
        )

    @property
    def emulation_configuration(self) -> EmulationConfiguration:
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
        return TMCConfiguration()

    def get_csp_configuration(self):
        """Get the configuration for the CSP."""
        return CSPConfiguration()

    def get_sdp_configuration(self):
        """Get the configuration for the SDP."""
        return SDPConfiguration()

    def get_dish_configuration(self):
        """Get the configuration for the dishes.

        Since the dish master devices name may change depending on the
        environment (production or emulation), when the dishes are production
        devices, their names are read from the environment, otherwise
        (when emulated) they are set to default values.
        """
        if self.emulation_configuration.dish:
            return DishesConfiguration()

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
