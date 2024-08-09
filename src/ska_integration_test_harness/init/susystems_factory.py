"""Factory to build the test harness subsystem wrappers."""

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.emulated.csp_devices import (
    EmulatedCSPDevices,
)
from ska_integration_test_harness.emulated.dishes_devices import (
    EmulatedDishesDevices,
)
from ska_integration_test_harness.emulated.sdp_devices import (
    EmulatedSDPDevices,
)
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.obs_state_commands_input import (
    ObsStateCommandsInput,
)
from ska_integration_test_harness.production.csp_devices import (
    ProductionCSPDevices,
)
from ska_integration_test_harness.production.dishes_devices import (
    ProductionDishesDevices,
)
from ska_integration_test_harness.production.sdp_devices import (
    ProductionSDPDevices,
)
from ska_integration_test_harness.production.tmc_devices import (
    ProductionTMCDevices,
)
from ska_integration_test_harness.structure.csp_devices import CSPDevices
from ska_integration_test_harness.structure.dishes_devices import DishesDevices
from ska_integration_test_harness.structure.sdp_devices import SDPDevices
from ska_integration_test_harness.structure.tmc_devices import TMCDevices


class SubsystemsFactory:
    """Factory to build the test harness subsystem wrappers.

    Given the necessary inputs and configurations, build the various
    test harness subsystems.
    """

    @staticmethod
    def create_tmc_wrapper(
        tmc_config: TMCConfiguration,
        default_commands_input: ObsStateCommandsInput,
        default_vcc_config_input: JSONInput,
    ) -> TMCDevices:
        """Create a TMC wrapper with the given configuration.

        :param tmc_config: The TMC configuration.
        :param default_commands_input: The default commands input.
        :param default_vcc_config_input: The default VCC configuration input.

        :return: The TMC wrapper.
        """
        return ProductionTMCDevices(
            tmc_configuration=tmc_config,
            default_commands_input=default_commands_input,
            default_vcc_config_input=default_vcc_config_input,
        )

    @staticmethod
    def create_csp_wrapper(
        csp_config: CSPConfiguration, all_production: bool = False
    ) -> CSPDevices:
        """Create a CSP wrapper with the given configuration.

        :param csp_config: The CSP configuration.
        :param all_production: flag to indicate if all subsystems are
            production ones.

        :return: The CSP wrapper.
        """
        if csp_config.is_emulated:
            return EmulatedCSPDevices(csp_config)

        return ProductionCSPDevices(
            csp_configuration=csp_config,
            all_production=all_production,
        )

    @staticmethod
    def create_sdp_wrapper(sdp_config: SDPConfiguration) -> SDPDevices:
        """Create a SDP wrapper with the given configuration.

        :param sdp_config: The SDP configuration.

        :return: The SDP wrapper.
        """
        if sdp_config.is_emulated:
            return EmulatedSDPDevices(sdp_config)
        return ProductionSDPDevices(sdp_config)

    @staticmethod
    def create_dishes_wrapper(
        dish_config: DishesConfiguration,
    ) -> DishesDevices:
        """Create a dishes wrapper with the given configuration.

        :param dish_config: The dishes configuration.

        :return: The dishes wrapper.
        """
        if dish_config.is_emulated:
            return EmulatedDishesDevices(dish_config)

        return ProductionDishesDevices(dish_config)
