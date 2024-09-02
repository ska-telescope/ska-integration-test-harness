"""Factory to build the test harness subsystem wrappers."""

from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)
from ska_integration_test_harness.emulated.csp_wrapper import (
    EmulatedCSPWrapper,
)
from ska_integration_test_harness.emulated.dishes_wrapper import (
    EmulatedDishesWrapper,
)
from ska_integration_test_harness.emulated.sdp_wrapper import (
    EmulatedSDPWrapper,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.production.csp_wrapper import (
    ProductionCSPWrapper,
)
from ska_integration_test_harness.production.dishes_wrapper import (
    ProductionDishesWrapper,
)
from ska_integration_test_harness.production.sdp_wrapper import (
    ProductionSDPWrapper,
)
from ska_integration_test_harness.production.tmc_wrapper import (
    ProductionTMCWrapper,
)
from ska_integration_test_harness.structure.csp_wrapper import CSPWrapper
from ska_integration_test_harness.structure.dishes_wapper import DishesWrapper
from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)
from ska_integration_test_harness.structure.tmc_wrapper import TMCWrapper


class TestHarnessFactory:
    """Factory to build the test harness wrappers.

    Given the necessary inputs and configurations, build the various
    test harness subsystems (dealing with emulation directives, variants
    coming from configuration settings, etc.).

    Main methods:

    - create_tmc_wrapper: Create a wrapper for the TMC subsystem.
    - create_csp_wrapper: Create a wrapper for the CSP subsystem.
    - create_sdp_wrapper: Create a wrapper for the SDP subsystem.
    - create_dishes_wrapper: Create a wrapper for the Dishes subsystem.
    """

    def __init__(
        self,
        config: TestHarnessConfiguration,
        default_inputs: TestHarnessInputs,
    ):
        """Initialize the factory with the given configuration and inputs.

        :param config: The test harness configuration.
        :param default_inputs: The default inputs for the test harness.
        """
        self.config = config
        self.default_inputs = default_inputs

    def set_config(self, config: TestHarnessConfiguration):
        """Set the configuration for the factory.

        :param config: The new configuration.
        """
        self.config = config

    def set_default_inputs(self, default_inputs: TestHarnessInputs):
        """Set the default inputs for the factory.

        :param default_inputs: The new default inputs.
        """
        self.default_inputs = default_inputs

    # --------------------------------------------------------------
    # Subsystems wrappers creation

    def create_telescope_wrapper(self) -> TelescopeWrapper:
        """Create a telescope wrapper with the given configuration.

        :return: The telescope wrapper.
        """
        telescope = TelescopeWrapper()
        telescope.set_up(
            tmc=self.create_tmc_wrapper(),
            csp=self.create_csp_wrapper(),
            sdp=self.create_sdp_wrapper(),
            dishes=self.create_dishes_wrapper(),
        )
        return telescope

    # --------------------------------------------------------------
    # Subsystems wrappers creation

    def create_tmc_wrapper(self) -> TMCWrapper:
        """Create a TMC wrapper with the given configuration.

        :return: The TMC wrapper.
        """
        return ProductionTMCWrapper(
            tmc_configuration=self.config.tmc_config,
            default_commands_input=self.default_inputs,
            default_vcc_config_input=self.default_inputs.default_vcc_config_input,  # pylint: disable=line-too-long # noqa: E501
        )
        # TODO: do not pass the third parameter, if it is already included
        # in the second one.

    def create_csp_wrapper(self) -> CSPWrapper:
        """Create a CSP wrapper with the given configuration.

        :return: The CSP wrapper.
        """
        csp_config = self.config.csp_config
        if csp_config.is_emulated:
            return EmulatedCSPWrapper(csp_config)

        return ProductionCSPWrapper(
            csp_configuration=csp_config,
            all_production=self.config.all_production(),
        )

    def create_sdp_wrapper(self) -> SDPWrapper:
        """Create a SDP wrapper with the given configuration.

        :return: The SDP wrapper.
        """
        sdp_config = self.config.sdp_config
        if sdp_config.is_emulated:
            return EmulatedSDPWrapper(sdp_config)
        return ProductionSDPWrapper(sdp_config)

    def create_dishes_wrapper(self) -> DishesWrapper:
        """Create a dishes wrapper with the given configuration.

        :return: The dishes wrapper.
        """
        dish_config = self.config.dishes_config
        if dish_config.is_emulated:
            return EmulatedDishesWrapper(dish_config)

        return ProductionDishesWrapper(dish_config)
