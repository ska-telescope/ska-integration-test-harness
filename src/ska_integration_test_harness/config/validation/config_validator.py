"""A validator for the whole test harness configuration."""

import abc
import logging

from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)
from ska_integration_test_harness.config.validation.subsys_config_validator import (  # pylint: disable=line-too-long # noqa: E501
    DeviceNamesValidator,
    EmulationConsistencyValidator,
    RequiredFieldsValidator,
    SubsystemConfigurationValidator,
)

# REFACTOR NOTE: this configuration validator mechanism maybe it's a bit
# of a overkill (or maybe also boilerplate). In the big refactoring
# we could consider simplifying it (maybe just letting the configurations
# validate themselves)


class ConfigurationValidator(abc.ABC):
    """A generic validator for the whole test harness configuration.

    It provides interfaces for two main validation steps:

    - a step to validate the presence of a coherent set of subsystems
      (e.g., for TMC-Mid tests, we need TMC, CSP, SDP, and Dishes)
    - a step to validate the individual subsystems configurations
      (e.g., check the required fields, check the device are reachable, etc.)

    It provides also a minimal log.info utility to log the validation steps.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        super().__init__()

        self.logger = logger
        """An optional logger used to log the errors and warnings, while
        they are found during the validation."""

        self.logger_prefix = "CONFIG VALIDATION: "
        """The prefix used to log the validation messages."""

    @abc.abstractmethod
    def validate_subsystems_presence(
        self, config: TestHarnessConfiguration
    ) -> None:
        """Validate the presence of the required subsystems.

        A given configuration must contain a valid subset of subsystems
        (i,e., there must be all the needed dependencies to run the tests).

        If the logger is set, all the errors and warnings are logged.

        :raises ValueError: If any critical error is found.
        """

    @abc.abstractmethod
    def validate_subsystems_configurations(
        self, config: TestHarnessConfiguration
    ) -> None:
        """Validate the individual subsystem configurations.

        Validate all subsystem configurations using the configured
        validators. If any critical error is found, a ValueError is raised.

        If the logger is set, all the errors and warnings are logged.

        :raises ValueError: If any critical error is found.
        """

    def _log_info(self, message: str) -> None:
        """Log an info message if a logger is available.

        :param message: The message to log.
        """
        if self.logger:
            self.logger.info(self.logger_prefix + message)


class BasicConfigurationValidator(ConfigurationValidator):
    """A basic configuration validator for the test harness.

    This validator:

    - checks the presence of TMC, CSP, SDP and Dishes or MCCS configurations
      (depending on the target being Mid or Low)
    - ensure the required fields are set for each subsystem
    - ensure the device names are valid and that they point to reachable
      devices
    - ensure the consistency of the emulation settings
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        super().__init__(logger)

        self.subsystem_validators: SubsystemConfigurationValidator = [
            RequiredFieldsValidator(logger),
            DeviceNamesValidator(logger),
            EmulationConsistencyValidator(logger),
        ]
        """The validators used to validate the subsystem configurations."""

    def _check_subsystems_presence(
        self, config: TestHarnessConfiguration, subsystem_name: str
    ) -> None:
        """Check the presence of a subsystem in the configuration.

        Everything is logged using the logger if available.

        :param config: The configuration to check.
        :param subsystem_name: The name of the subsystem to check.
        :raises ValueError: If the subsystem is missing.
        """
        if not config.get_subsystem_config(subsystem_name):
            raise ValueError(
                f"The configuration for the subsystem '{subsystem_name}' "
                "is missing which instead is required."
            )

        self._log_info(f"Required configuration for '{subsystem_name}': OK.")

    def validate_subsystems_presence(
        self, config: TestHarnessConfiguration
    ) -> None:
        """Validate the presence of TMC, CSP, SDP, and Dishes configs."""
        self._log_info("Checking the presence of the required subsystems.")

        # TMC, CSP and SDP are always required
        for subsystem in [
            TestHarnessConfiguration.SubsystemName.TMC,
            TestHarnessConfiguration.SubsystemName.CSP,
            TestHarnessConfiguration.SubsystemName.SDP,
        ]:
            self._check_subsystems_presence(config, subsystem)

        # Dishes is required only for the mid target
        if config.tmc_config.supports_mid():
            self._check_subsystems_presence(
                config, TestHarnessConfiguration.SubsystemName.DISHES
            )

        # TODO Low: either DISHES or MCCS should be required

        self._log_info("All the required subsystems are present.")

    def validate_subsystems_configurations(
        self, config: TestHarnessConfiguration
    ) -> None:
        """Validate each individual subsystem configuration."""
        self._log_info(
            "Validating the individual subsystem configurations contents."
        )

        for validator in self.subsystem_validators:
            self._apply_subsystem_validator(validator, config)

        self._log_info(
            "All the individual subsystem configurations are valid."
        )

    def _apply_subsystem_validator(
        self,
        validator: SubsystemConfigurationValidator,
        config: TestHarnessConfiguration,
    ) -> None:
        """Apply a validator to all (included) subsystem configurations.

        :param validator: The validator to apply.
        """
        self._log_info(
            "Validating all subsystems configurations "
            f"using {validator.__class__.__name__}."
        )

        validator.reset()
        for subsystem_config in config.get_included_subsystems():
            validator.validate(subsystem_config)

        if not validator.is_valid():
            raise ValueError(
                "Configuration validation "
                f"using {validator.__class__.__name__} "
                "failed with the following critical errors:\n"
                + "\n".join(
                    [str(error) for error in validator.get_critical_errors()]
                )
            )

        self._log_info(
            f"Configuration validation using {validator.__class__.__name__} "
            "succeeded on all subsystems."
        )
