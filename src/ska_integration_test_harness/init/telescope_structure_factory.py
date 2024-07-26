"""Create a telescope test structure according to the current configuration."""

from ska_integration_test_harness.config.configuration_factory import (
    TestHarnessConfigurationFactory,
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
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)
from ska_integration_test_harness.structure.tmc_devices import TMCDevices


class TelescopeStructureFactory:
    """Create a telescope test structure according to the current config.

    This factory is responsible for creating the correct instances of the
    telescope test structure components, according to the current
    configuration. It is able to create both production and emulated
    components, depending on the configuration.

    The factory is also responsible for initializing the components with the
    correct configuration parameters.

    This class initialize for the first time the telescope wrapper with the
    correct sub-components, so everywhere else in the code, when needed
    an unique instance of the telescope wrapper, it can be retrieved
    using the constructor (see Singleton design pattern).
    """

    def __init__(
        self,
        default_commands_input: ObsStateCommandsInput,
        default_vcc_config_input: JSONInput,
    ):
        """Initialize the factory.

        :param default_commands_input: The default commands input. They
            will be used to reset the TMC devices. Fill it with all the
            inputs with suitable default values.
            If you don't some steps of the tear down procedure may fail.
        :param default_vcc_config_input: The default VCC config input. It
            will be used to reset the VCC config.
        """
        self.config_factory = TestHarnessConfigurationFactory()
        self.default_commands_input = default_commands_input
        self.default_vcc_config_input = default_vcc_config_input

    @property
    def _emulation_config(self):
        return self.config_factory.emulation_configuration

    def init_telescope_test_structure(self) -> TelescopeWrapper:
        """Initialize the telescope test structure.

        Initialize the telescope test structure, creating the necessary
        TelescopeWrapper instance and initializing it with the correct
        sub-components (according to the current configuration).

        return: A central node wrapper instance.
        """
        # TODO: add exhaustive logging to describe what am I creating. This may
        # include:
        # - which sub-components are intended to be used
        #   (production or emulated configuration)
        # - how are they configured (device names, etc.)
        # - what's the actual state of the system (some version information
        #   asked directly to the devices, etc.)
        telescope = TelescopeWrapper()
        telescope.set_up(
            tmc=self.create_tmc_wrapper(),
            sdp=self.create_sdp_wrapper(),
            csp=self.create_csp_wrapper(),
            dishes=self.create_dishes_wrapper(),
        )
        return telescope

    def create_tmc_wrapper(self) -> TMCDevices:
        """Create a TMC wrapper.

        return: A TMC wrapper instance.
        """
        return ProductionTMCDevices(
            self.config_factory.get_tmc_configuration(),
            self.default_commands_input,
            self.default_vcc_config_input,
        )

    def create_sdp_wrapper(self) -> SDPDevices:
        """Create a SDP wrapper.

        return: A SDP wrapper instance.
        """
        if self._emulation_config.sdp:
            return EmulatedSDPDevices(
                self.config_factory.get_sdp_configuration()
            )

        return ProductionSDPDevices(
            self.config_factory.get_sdp_configuration()
        )

    def create_csp_wrapper(self) -> CSPDevices:
        """Create a CSP wrapper.

        return: A CSP wrapper instance.
        """
        if self._emulation_config.csp:
            return EmulatedCSPDevices(
                self.config_factory.get_csp_configuration()
            )

        return ProductionCSPDevices(
            csp_configuration=self.config_factory.get_csp_configuration(),
            all_production=self._emulation_config.all_production,
        )

    def create_dishes_wrapper(self) -> DishesDevices:
        """Create a dishes wrapper.

        return: A dishes wrapper instance.
        """
        if self._emulation_config.dish:
            return EmulatedDishesDevices(
                self.config_factory.get_dish_configuration()
            )

        return ProductionDishesDevices(
            self.config_factory.get_dish_configuration()
        )
