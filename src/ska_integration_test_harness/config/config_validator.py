"""A validator for a subsystem configuration."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    SubsystemConfiguration,
)


class SubsystemConfigurationValidator(abc.ABC):
    """A validator for a subsystem configuration.

    NOTE: maybe in future this could be refactored with the
    https://refactoring.guru/design-patterns/visitor
    design pattern.
    """

    # pylint: disable=too-few-public-methods

    @abc.abstractmethod
    def validate(
        self, config: SubsystemConfiguration
    ) -> tuple[bool, list[str]]:
        """Validate a generic subsystem configuration.

        Validate a generic subsystem configuration, implementing your own
        checks to ensure that the configuration is correct. This method should
        return a tuple with two elements:

        - a boolean that is True if the config. is valid, False otherwise,
        - a list of error/warning messages if the configuration is not valid.

        :param config: The configuration to validate.
        :return: True if the configuration is valid, False otherwise.
        """


class BasicConfigurationValidator(SubsystemConfigurationValidator):
    """A basic validator. Replace it if you need something more sophisticated.

    This is a basic validator that given any subsystem configuration, it will:

    - check that all the required attributes are specified,
    - check that all the attributes that point to device names point to valid
      Tango device names and that they are reachable,
    - check that if a subsystem is emulated, that the devices are effectively
      emulators, or otherwise that they are production devices (this is not
      a strict check, in fact if it fails it will issue a warning).
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_validation_errors = []
        self._last_validation_valid = False

    def validate(
        self, config: SubsystemConfiguration
    ) -> tuple[bool, list[str]]:
        """Validate a generic subsystem configuration.

        Validate a generic subsystem configuration, implementing your own
        checks to ensure that the configuration is correct. This method should
        return a tuple with two elements:

        - a boolean that is True if the config. is valid, False otherwise,
        - a list of error/warning messages if the configuration is not valid.

        This is a basic validator that given any subsystem configuration
        and it consecutively checks:

        - that all the required attributes are specified,
        - that all the attributes that point to device names
          point to valid Tango device names and that they are reachable,
        - that if a subsystem is emulated, that the devices
          are effectively emulators, or otherwise that they are
          production devices (this is not a strict check, in fact if it
          fails it will issue a warning).

        :param config: The configuration to validate.
        :return: True if the configuration is valid, False otherwise.
        """
        # reset cached values
        self._last_validation_errors = []
        self._last_validation_valid = True

        # Check required fields are set and return if not
        self.check_required_fields_are_set(config)
        if not self._last_validation_valid:
            return False, self._last_validation_errors

        # Check that the devices are valid and reachable and return if not
        self.check_device_are_valid(config)
        if not self._last_validation_valid:
            return False, self._last_validation_errors

        # Check the emulation is consistent and return
        self.check_emulation(config)
        return self._last_validation_valid, self._last_validation_errors

    # ----------------------------------------------
    # Utils methods to populate the errors list

    def _add_error(self, error: str) -> None:
        """Add an error to the validation errors list.

        :param error: The error message to add.
        """
        self._last_validation_errors.append("ERROR: " + error)
        self._last_validation_valid = False

    def _add_warning(self, warning: str) -> None:
        """Add a warning to the validation errors list.

        Different from errors, warnings don't make the validation invalid.

        :param warning: The warning message to add.
        """
        self._last_validation_errors.append("WARNING: " + warning)

    # ----------------------------------------------
    # Validation steps

    def check_required_fields_are_set(
        self, config: SubsystemConfiguration
    ) -> None:
        """Check that all the required fields are set.

        Check that all the required fields are set in the configuration
        and that they are of the expected type. This method will
        write its findings in the ``_last_validation_errors`` list
        and will set the ``_last_validation_valid`` flag accordingly.

        :param config: The configuration to check.
        """
        for attr in config.mandatory_attributes():
            attr_value = getattr(config, attr)
            if not attr_value:
                self._add_error(f"The attribute '{attr}' is missing.")
            # get attribute expected type
            expected_type = config.__annotations__[attr]
            if not isinstance(attr_value, expected_type):
                self._add_error(
                    f"The attribute '{attr}' is not of "
                    f"the expected type '{expected_type}'."
                )

    def check_device_are_valid(self, config: SubsystemConfiguration) -> None:
        """Check that all the device names are valid.

        Check that all the device names are valid Tango device names
        and that they are reachable. This method will write its findings
        in the ``_last_validation_errors`` list and will set the
        ``_last_validation_valid`` flag accordingly.

        :param config: The configuration to check.
        """
        for attr in config.attributes_with_device_names():

            dev_name = getattr(config, attr)
            if not dev_name:
                self._add_warning(f"The attribute '{attr}' is empty.")
                continue

            try:
                dev_proxy = tango.DeviceProxy(dev_name)
                dev_proxy.ping()
            except tango.DevFailed as df:
                self._add_error(f"Device '{dev_name}' is unreachable: {df}")
            except tango.ConnectionFailed as cf:
                self._add_error(f"Device '{dev_name}' connection failed: {cf}")
            except tango.DevError as de:
                self._add_error(f"Device '{dev_name}' returned an error: {de}")
            # except Exception as e:
            #     self._add_error(
            #         f"Device '{dev_name}' raised an exception: {e}"
            #     )

    def check_emulation(self, config: SubsystemConfiguration) -> None:
        """Check that the devices are emulators or production devices.

        Check that the devices are emulators or production devices depending
        on the configuration. This is not a strict check, in fact if it fails
        it will issue a warning.
        This method will write its findings in the ``_last_validation_errors``
        list and will set the ``_last_validation_valid`` flag accordingly.

        Assumptions:

        - The given devices are all reachable.

        :param config: The configuration to check.
        """
        for attr in config.attributes_with_device_names():
            dev_name = getattr(config, attr)
            if not dev_name:
                continue

            dev_proxy = tango.DeviceProxy(dev_name)
            responds_as_emulator = self._device_responds_as_emulator(dev_proxy)

            if config.is_emulated and not responds_as_emulator:
                self._add_warning(
                    f"The configuration {config.__class__.__name__} "
                    "specifies that the devices are emulated, but "
                    f"the device '{dev_name}' looks like it is not "
                    "an emulator."
                )
            elif not config.is_emulated and responds_as_emulator:
                self._add_warning(
                    f"The configuration {config.__class__.__name__} "
                    "specifies that the devices are production devices, "
                    f"but the device '{dev_name}' looks like it is an "
                    "emulator."
                )

    def _device_responds_as_emulator(
        self, dev_proxy: tango.DeviceProxy
    ) -> bool:
        """Check if a device responds as an emulator.

        Check if a device responds as an emulator. This is a heuristic
        check, that tries to execute some operations on the device that
        - in theory - only emulators should support. The operations are:

        - resetDelay()
        - commandCallInfo()

        :param dev_proxy: The device proxy to check.
        :return: True if the device responds as an emulator, False otherwise.
        """
        try:
            dev_proxy.resetDelay()
            _ = dev_proxy.commandCallInfo
            return True
        except AttributeError:
            # if the device is not an emulator, it will raise an exception
            return False
