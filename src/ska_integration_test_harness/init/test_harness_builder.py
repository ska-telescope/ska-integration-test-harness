"""A builder class for configuring and building a test harness."""

import logging

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
)
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

    The class uses also a set of tools to read and validate the configurations
    and the inputs. Potentially, you can inject your own tools to customise
    the behaviour of the builder. Potentially, you can also subclass this
    builder to customise its behaviour.

    Usage example:

    .. code-block:: python

        builder = TestHarnessBuilder()
        builder.read_config_file("configurations.yaml")
        builder.validate_configurations()

        default_inputs = TestHarnessInputs(
            assign_input=FileJSONInput("path/to/assign.json"),
            # ...
        )
        builder.set_default_inputs(default_inputs)
        builder.validate_default_inputs()

        telescope = builder.build()


    """

    # pylint: disable=too-many-instance-attributes

    # (this is not a pytest test class)
    __test__ = False

    def __init__(self):
        """Initialise the TestHarnessBuilder with default configurations."""
        # --------------------------------------------------------------
        # inputs and configurations

        self.config: TestHarnessConfiguration = TestHarnessConfiguration()
        """The configuration used to build the test harness."""

        self.default_inputs: TestHarnessInputs = TestHarnessInputs()
        """The default inputs used to build the test harness."""

        # TODO: move it to the configuration, but make it overridable (?)
        # This concept of "configurable but overridable" is a bit tricky,
        # but it may be useful in a good bunch of cases.
        self.kube_namespace: str | None = None
        """The Kubernetes namespace where the SUT is deployed.

        It is optional, but if you set it, it will be used to connect to
        get more information about the various subsystem devices.
        """

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
        self.input_validator.validate_inputs_presence(
            self.default_inputs,
            # if the configuration is not yet available we suppose to be in Mid
            self.config.tmc_config is None
            or self.config.tmc_config.supports_mid(),
        )
        self.input_validator.validate_inputs_correctness(self.default_inputs)

        self._default_inputs_validated = True
        return self

    def set_kubernetes_namespace(
        self, kube_namespace: str
    ) -> "TestHarnessBuilder":
        """Set the Kubernetes namespace where the SUT is deployed.

        It will help to connect to the ska-k8s-config-exporter service.

        :param namespace: The Kubernetes namespace.
        :returns: The current instance of TestHarnessBuilder with
            the Kubernetes namespace set.
        """
        self._log_info(
            f"Setting the Kubernetes namespace to: {kube_namespace}"
        )
        self.kube_namespace = kube_namespace
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

        if self.kube_namespace:
            device_info_provider = DevicesInfoProvider(self.kube_namespace)
            telescope.devices_info_provider = device_info_provider
        else:
            self._log_warning(
                "You are building a test harness without setting the "
                "Kubernetes namespace. You may miss some details about "
                "the devices in the subsystems."
            )

        self._log_info(
            "Telescope wrapper and subsystems set up successfully. "
            "Now, a brief recap of the subsystems and their devices: \n"
            f"{telescope.get_subsystems_recap()}"
        )

        return telescope
