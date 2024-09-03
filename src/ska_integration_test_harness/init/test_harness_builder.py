"""A builder class for configuring and building a test harness."""

import logging

from ska_integration_test_harness.config.reader.yaml_config_reader import (
    YAMLConfigurationReader,
)
from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)
from ska_integration_test_harness.config.validation.config_validator import (
    BasicConfigurationValidator,
    ConfigurationValidator,
)
from ska_integration_test_harness.init.test_harness_factory import (
    TestHarnessFactory,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.inputs.validation.input_validator import (
    BasicInputValidator,
    InputValidator,
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
    """

    # (this is not a pytest test class)
    __test__ = False

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """Initialize the TestHarnessBuilder with default configurations."""
        # --------------------------------------------------------------
        # inputs and configurations

        self.config: TestHarnessConfiguration = TestHarnessConfiguration()
        """The configuration used to build the test harness."""

        self.default_inputs: TestHarnessInputs = TestHarnessInputs()
        """The default inputs used to build the test harness."""

        # --------------------------------------------------------------
        # internal tools

        self.logger: logging.Logger = logging.getLogger(__name__)

        self.config_reader: YAMLConfigurationReader = YAMLConfigurationReader()
        """The tool used to read the configurations."""

        self.config_validator: ConfigurationValidator = (
            BasicConfigurationValidator(self.logger)
        )
        """The tool used to validate the configurations."""

        self.input_validator: InputValidator = BasicInputValidator(self.logger)
        """The tool used to validate the inputs."""

        self.test_harness_factory: TestHarnessFactory = TestHarnessFactory(
            self.config, self.default_inputs
        )
        """The factory used to create the subsystems and the
        overall telescope wrapper.
        """

        # --------------------------------------------------------------
        # flags to track the validation status

        self._configs_validated = False
        self._default_inputs_validated = False

    def _log_info(self, message):
        """Log an informational message."""
        self.logger.info("TestHarnessBuilder: %s", message)

    def _log_warning(self, message):
        """Log a warning message."""
        self.logger.warning("TestHarnessBuilder: %s", message)

    def _log_error(self, message):
        """Log an error message."""
        self.logger.error("TestHarnessBuilder: %s", message)

    def read_config_file(self, filepath: str) -> "TestHarnessBuilder":
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

        self.config_reader.read_configuration_file(filepath)
        self.config = self.config_reader.get_test_harness_configuration()

        self._log_info("Configurations read successfully.")
        return self

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
        self._configs_validated = False
        self.config_validator.validate_subsystems_presence(self.config)
        self.config_validator.validate_subsystems_configurations(self.config)

        self._configs_validated = True
        return self

    def set_default_inputs(
        self, inputs: TestHarnessInputs
    ) -> "TestHarnessBuilder":
        """Set the default inputs for the test harness.

        NOTE: all the defaults input specified by the ``TestHarnessInputs``
        class are required, since they are used in test harness tear down
        procedures.

        :param inputs: The default inputs to be used.
        :returns: The current instance of TestHarnessBuilder with
            the default inputs set.
        """
        self._default_inputs_validated = False

        self._log_info("Setting default inputs.")
        self.default_inputs = inputs
        return self

    def validate_default_inputs(self) -> "TestHarnessBuilder":
        """Check if all default inputs are valid.

        Right now this method checks:

        - all the required default inputs are passed
        - all the required default inputs have the right type

        :raises ValueError: if some input is missing.
        """
        self._default_inputs_validated = False
        self.input_validator.validate_inputs_presence(self.default_inputs)
        self.input_validator.validate_inputs_correctness(self.default_inputs)

        self._default_inputs_validated = True
        return self

    def is_config_validated(self) -> bool:
        """Check if the configurations have been validated."""
        return self._configs_validated

    def are_default_inputs_validated(self) -> bool:
        """Check if the default inputs have been validated."""
        return self._default_inputs_validated

    def build(self) -> TelescopeWrapper:
        """Build the test harness.

        :returns: a wrapper for the telescope and its subsystems.
        """
        if not self.is_config_validated():
            self._log_warning(
                "You are building a test harness without "
                "validating the configurations. We strongly suggest to call "
                "validate_configurations() before building the test harness."
            )
        if not self.are_default_inputs_validated():
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
        self.test_harness_factory.set_config(self.config)
        self.test_harness_factory.set_default_inputs(self.default_inputs)
        telescope = self.test_harness_factory.create_telescope_wrapper()

        self._log_info("Telescope wrapper and subsystems set up successfully.")
        return telescope


# Example usage:
# builder = TestHarnessBuilder()
# try:
#     builder.read_config_file("path/to/config.yaml").
# validate_configurations().build()
# except ValueError as e:
#     print(f"Validation failed: {e}")
