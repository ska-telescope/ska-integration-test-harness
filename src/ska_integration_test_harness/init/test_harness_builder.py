"""A builder class for configuring and building a test harness."""

import logging
from typing import Any, List

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    SubsystemConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.config_validator import (
    DeviceNamesValidator,
    EmulationConsistencyValidator,
    RequiredFieldsValidator,
    SubsystemConfigurationValidator,
)
from ska_integration_test_harness.config.yaml_config_reader import (
    YAMLConfigurationReader,
)
from ska_integration_test_harness.init.susystems_factory import (
    SubsystemsFactory,
)
from ska_integration_test_harness.inputs.default_inputs import DefaultInputs
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.obs_state_commands_input import (
    ObsStateCommandsInput,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TestHarnessBuilder:
    """A builder class for configuring and building a test harness.

    This class allows you to configure various subsystems such as
    TMC, CSP, SDP, and Dishes, validate the configurations,
    and build the test harness. You can/should also specify some default
    JSON inputs for various commands/purposes.

    Attributes:
        tmc_config (TMCConfiguration): Configuration for the TMC subsystem.
        csp_config (CSPConfiguration): Configuration for the CSP subsystem.
        sdp_config (SDPConfiguration): Configuration for the SDP subsystem.
        dishes_config (DishesConfiguration): Configuration for the Dishes
            subsystem.
        default_inputs (DefaultInputs): Default inputs for various purposes.

    This class exposes two validation methods that should be called before
        building the test harness:

    - validate_configurations: Validates the subsystem configurations.
    - validate_default_inputs: Validates the default inputs.

    Even if they are not compulsory, it is strongly suggested to call them
    before building the test harness.

    The class uses also a set of tools to read and validate the configurations
    and the inputs. Potentially, you can inject your own tools to customize
    the behavior of the builder. Potentially, you can also subclass this
    builder to customize its behavior.

    TODO: refactor and uniform the style
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """Initialize the TestHarnessBuilder with default configurations."""
        # --------------------------------------------------------------
        # inputs and configurations
        self.tmc_config: TMCConfiguration = TMCConfiguration()
        self.csp_config: CSPConfiguration = CSPConfiguration()
        self.sdp_config: SDPConfiguration = SDPConfiguration()
        self.dishes_config: DishesConfiguration = DishesConfiguration()

        self.default_inputs: DefaultInputs = DefaultInputs()

        # --------------------------------------------------------------
        # internal tools
        # TODO:
        self._logger: logging.Logger = logging.getLogger(__name__)
        self.validators = [
            RequiredFieldsValidator(self._logger),
            DeviceNamesValidator(self._logger),
            EmulationConsistencyValidator(self._logger),
        ]
        self.subsystems_factory = SubsystemsFactory()

        # TODO: find a way to toggle them to False every time something change
        self._configs_validated = False
        self._default_inputs_validated = False

    def _log_info(self, message):
        """Log an informational message."""
        self._logger.info("TestHarnessBuilder: %s", message)

    def _log_warning(self, message):
        """Log a warning message."""
        self._logger.warning("TestHarnessBuilder: %s", message)

    def _log_error(self, message):
        """Log an error message."""
        self._logger.error("TestHarnessBuilder: %s", message)

    def read_from_file(self, filepath: str) -> "TestHarnessBuilder":
        """
        Read the configuration from a YAML file and set the configurations
            accordingly.

        :param filepath: The path to the YAML file containing the
            configurations.
        :returns: The current instance of TestHarnessBuilder with
            configurations set.
        :raises FileNotFoundError: If the YAML file does not exist.
        :raises yaml.YAMLError: If the YAML file contains errors.
        """
        self._configs_validated = False

        self._log_info(f"Reading configurations from file: {filepath}")

        config_reader = YAMLConfigurationReader(filepath)
        self.tmc_config = config_reader.get_tmc_configuration()
        self.csp_config = config_reader.get_csp_configuration()
        self.sdp_config = config_reader.get_sdp_configuration()
        self.dishes_config = config_reader.get_dish_configuration()

        self._log_info("Configurations read successfully.")
        return self

    def _configurations(self) -> List[SubsystemConfiguration]:
        """Return a list of all subsystem configurations."""
        return [
            self.tmc_config,
            self.csp_config,
            self.sdp_config,
            self.dishes_config,
        ]

    def _apply_validator(
        self, validator: SubsystemConfigurationValidator
    ) -> None:
        """Apply a validator to all subsystem configurations.

        :param validator: The validator to apply.
        """
        self._log_info(
            f"Applying {validator.__class__.__name__} on "
            "all subsystems configurations."
        )

        validator.reset()
        for config in self._configurations():
            validator.validate(config)

        if not validator.is_valid():
            raise ValueError(
                "Configuration validation "
                f"using {validator.__class__.__name__} "
                "failed with the following critical errors:\n"
                + "\n".join(
                    [str(error) for error in validator.get_critical_errors()]
                )
            )

    def validate_configurations(self) -> "TestHarnessBuilder":
        """Validate all subsystem configurations.

        Logs errors and warnings as necessary.

        If any configuration is invalid, a ValueError is raised, containing
        a detailed list of all validation errors and warnings.

        :returns: The current instance of TestHarnessBuilder if all
            configurations are valid.
        :raises ValueError: If any configuration is invalid,
            with the details of the errors.
        """
        for validator in self.validators:
            self._apply_validator(validator)

        self._log_info("All configurations are valid.")
        self._configs_validated = True

        return self

    def add_default_input(
        self, name: str, input_data: Any
    ) -> "TestHarnessBuilder":
        """Add a default input.

        :param purpose: The purpose for which the input is intended.
        :param input_data: The input data to be used as default.
        :returns: The current instance of TestHarnessBuilder with
            the default input set.
        """
        self._default_inputs_validated = False

        self._log_info(f'Adding default input "{name}".')
        self.default_inputs[name] = input_data
        return self

    def validate_default_inputs(self) -> "TestHarnessBuilder":
        """Check if all default inputs are valid.

        Right now this method checks:

        - all the required default inputs are passed
        - all the required default inputs have the right type

        :raises ValueError: if some input is missing.
        """
        self._log_info("Validating default inputs.")

        # TODO: refactor this
        for attr in self.default_inputs.mandatory_attributes():
            attr_value = getattr(self.default_inputs, attr)
            if not attr_value:
                raise ValueError(f"The default input '{attr}' is missing.")

            # get attribute expected type
            # pylint: disable=no-member
            expected_type = self.default_inputs.__annotations__[attr]
            if not isinstance(attr_value, expected_type):
                raise ValueError(
                    f"The default input '{attr}' is not of the "
                    f"expected type '{expected_type}'. "
                    f"Instead, it is of type '{type(attr_value)}'."
                )
            # for JSON types, ensure they are valid JSON and that they can
            # return a string
            if expected_type is JSONInput:
                attr_value: JSONInput = attr_value
                try:
                    attr_value.get_json_dict()
                except Exception as e:
                    raise ValueError(
                        f"The default input '{attr}' is not a "
                        "valid JSON input because it looks impossible to "
                        "extract an object from it. "
                    ) from e

        self._log_info("All default inputs are valid.")
        self._default_inputs_validated = True

        return self

    def build(self) -> TelescopeWrapper:
        """Build the test harness.

        :returns: a wrapper for the telescope and its subsystems.
        """
        if not self._configs_validated:
            self._log_warning(
                "You are building a test harness without "
                "validating the configurations. We strongly suggest to call "
                "validate_configurations() before building the test harness."
            )
        if not self._default_inputs_validated:
            self._log_warning(
                "You are building a test harness without "
                "validating the default inputs. We strongly suggest to call "
                "validate_default_inputs() before building the test harness."
            )

        self._log_info("Building the telescope wrapper.")
        telescope = TelescopeWrapper()

        self._log_info(
            "Setting up the telescope wrapper with the various subsystems."
        )

        tmc = self.subsystems_factory.create_tmc_wrapper(
            tmc_config=self.tmc_config,
            default_commands_input=ObsStateCommandsInput(
                assign_input=self.default_inputs.assign_input,
                configure_input=self.default_inputs.configure_input,
                scan_input=self.default_inputs.scan_input,
                release_input=self.default_inputs.release_input,
            ),
            default_vcc_config_input=self.default_inputs.default_vcc_config_input,  # pylint: disable=line-too-long # noqa: E501
        )
        csp = self.subsystems_factory.create_csp_wrapper(
            csp_config=self.csp_config,
            all_production=self._all_subsystems_are_in_production(),
        )
        sdp = self.subsystems_factory.create_sdp_wrapper(
            sdp_config=self.sdp_config,
        )
        dishes = self.subsystems_factory.create_dishes_wrapper(
            dish_config=self.dishes_config,
        )

        telescope.set_up(tmc=tmc, csp=csp, sdp=sdp, dishes=dishes)

        self._log_info("Telescope wrapper and subsystems set up successfully.")
        return telescope

    def _all_subsystems_are_in_production(self) -> bool:
        """Check if all subsystems are in production mode."""
        return all(
            [
                not self.tmc_config.is_emulated,
                not self.csp_config.is_emulated,
                not self.sdp_config.is_emulated,
                not self.dishes_config.is_emulated,
            ]
        )


# Example usage:
# builder = TestHarnessBuilder()
# try:
#     builder.read_from_file("path/to/config.yaml").validate_configurations().build()
# except ValueError as e:
#     print(f"Validation failed: {e}")
