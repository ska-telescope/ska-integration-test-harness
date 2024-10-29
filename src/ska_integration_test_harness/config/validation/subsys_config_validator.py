"""A validator for a subsystem configuration."""

import abc
import logging

import tango

from ska_integration_test_harness.config.components_config import (
    SubsystemConfiguration,
)
from ska_integration_test_harness.config.validation.config_issue import (
    ConfigurationIssue,
    create_configuration_issue,
)


class SubsystemConfigurationValidator(abc.ABC):
    """A generic validator for a subsystem configuration.

    This is an abstraction of a class that can be used to validate one or more
    subsystem configurations. The idea is that you can implement your own
    validation logic by subclassing this class and implementing the
    ``validate`` method. The validation logic should scan a given configuration
    and populate the ``errors_and_warnings`` list with the errors and warnings
    found during the validation (using the ``add_error`` and
    ``add_warning`` helper methods).

    With a validator instance, you can run multiple validations on different
    configurations, and collect all the errors and warnings in the
    ``errors_and_warnings`` list, or you can reset the validator and start
    a new validation. After one or more runs, you can check if the validation
    was successful by calling the ``is_valid`` method.

    When you initialise an instance of this class, you can pass an optional
    logger that will be used to log the errors and warnings found during the
    validation.

    NOTE: maybe in future this could be refactored with the
    https://refactoring.guru/design-patterns/visitor
    design pattern (and so implement custom checks for each different
    kind of subsystem configuration).
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        super().__init__()

        self.errors_and_warnings: list[ConfigurationIssue] = []
        """The errors and warnings found during one or more validations."""

        self.logger = logger
        """An optional logger used to log the errors and warnings, while
        they are found during the validation."""

    @abc.abstractmethod
    def validate(self, config: SubsystemConfiguration):
        """Validate a generic subsystem configuration.

        Validate a generic subsystem configuration, implementing your own
        checks to ensure that the configuration is correct. As a side effect,
        this method should populate the ``errors_and_warnings`` list with
        the errors and warnings found during the validation.

        NOTE: this method is not expected to return anything, nor to raise
        exceptions.

        :param config: The configuration to validate.
        """

    def reset(self) -> None:
        """Reset the validator, clearing the errors and warnings list."""
        self.errors_and_warnings = []

    def is_valid(self) -> bool:
        """Return True if there are no critical issues (i.e., errors)."""
        return not any(
            issue.is_critical() for issue in self.errors_and_warnings
        )

    # ----------------------------------------------
    # Utils methods to populate the errors list

    def add_error(self, message: str) -> None:
        """Add an error to the errors and warnings list.

        :param message: The error message to add.
        """
        error = create_configuration_issue(message, is_critical=True)
        self.errors_and_warnings.append(error)
        self._maybe_log(error)

    def add_warning(self, message: str) -> None:
        """Add a warning to the errors and warnings list.

        :param message: The warning message to add.
        """
        warning = create_configuration_issue(message, is_critical=False)
        self.errors_and_warnings.append(warning)
        self._maybe_log(warning)

    def _maybe_log(self, issue: ConfigurationIssue) -> None:
        """Log a message if a logger is available.

        :param issue: The issue to log.
        """
        if self.logger:
            issue.log(self.logger)

    def get_critical_errors(self) -> list[ConfigurationIssue]:
        """Return the critical errors found during the validation.

        :return: A list of critical errors.
        """
        return [
            issue for issue in self.errors_and_warnings if issue.is_critical()
        ]


class RequiredFieldsValidator(SubsystemConfigurationValidator):
    """Validator to check that all required fields are set.

    This validator checks that all required fields in the subsystem
    configuration. It logs errors if any required attribute is missing.

    :param config: The configuration to validate.
    """

    def validate(self, config: SubsystemConfiguration) -> None:
        """Validate the required fields of a subsystem configuration.

        Check that all the required fields are set in the configuration.

        :param config: The configuration to validate.
        """
        for attr in config.mandatory_attributes():
            attr_value = getattr(config, attr, None)
            if not attr_value:
                self.add_error(f"The attribute '{attr}' is missing.")


class DeviceNamesValidator(SubsystemConfigurationValidator):
    """Validator to check the validity of device names in the configuration.

    This validator checks that all device names specified in the subsystem
    configuration are valid Tango device names and that they are reachable.
    Errors are logged for any unreachable or invalid device names.

    :param config: The configuration to validate.
    """

    def validate(self, config: SubsystemConfiguration) -> None:
        """Validate the device names in a subsystem configuration.

        Check that all the device names are valid Tango device names
        and that they are reachable. Errors are logged for any invalid
        or unreachable device names.

        :param config: The configuration to validate.
        """
        for dev_key, dev_name in config.get_device_names().items():
            if not dev_name:
                self.add_warning(f"The attribute '{dev_key}' is empty.")
                continue

            try:
                dev_proxy = tango.DeviceProxy(dev_name)
                dev_proxy.ping()
            except tango.DevFailed as df:
                self.add_error(f"Device '{dev_name}' is unreachable: {df}\n")
            except tango.ConnectionFailed as cf:
                self.add_error(
                    f"Device '{dev_name}' connection failed: {cf}\n"
                )
            except tango.DevError as de:
                self.add_error(
                    f"Device '{dev_name}' returned an error: {de}\n"
                )


class EmulationConsistencyValidator(SubsystemConfigurationValidator):
    """Validator to check the consistency of emulation in the configuration.

    This validator checks that the devices in the subsystem configuration are
    consistent with their emulation status. Warnings are logged if the devices
    do not match the expected emulation or production status.

    :param config: The configuration to validate.
    """

    def validate(self, config: SubsystemConfiguration) -> None:
        """Validate the emulation consistency in a subsystem configuration.

        Check that the devices are emulators or production devices depending
        on the configuration. Warnings are logged if the emulation status is
        inconsistent with the configuration.

        :param config: The configuration to validate.
        """
        for dev_key, dev_name in config.get_device_names().items():

            dev_proxy = tango.DeviceProxy(dev_name)
            responds_as_emulator = self._device_responds_as_emulator(dev_proxy)

            if config.is_emulated and not responds_as_emulator:
                self.add_warning(
                    f"The configuration {config.__class__.__name__} "
                    "specifies that the devices are emulated, but "
                    f"the device {dev_key}='{dev_name}' looks like it is not "
                    "an emulator."
                )
            elif not config.is_emulated and responds_as_emulator:
                self.add_warning(
                    f"The configuration {config.__class__.__name__} "
                    "specifies that the devices are production devices, "
                    f"but the device {dev_key}='{dev_name}' looks like "
                    "it is an emulator."
                )

    def _device_responds_as_emulator(
        self, dev_proxy: tango.DeviceProxy
    ) -> bool:
        """Check if a device responds as an emulator.

        Check if a device responds as an emulator. This is a heuristic
        check, that verifies if the device has some commands and attributes
        that are typical of an emulator (i.e., the
        ``commandCallInfo`` attribute).

        :param dev_proxy: The device proxy to check.
        :return: True if the device responds as an emulator, False otherwise.
        """
        attributes = [
            str(attr).lower() for attr in dev_proxy.get_attribute_list()
        ]
        return "commandCallInfo".lower() in attributes
