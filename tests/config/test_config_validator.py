"""Unit tests for the configuration validators."""

from unittest.mock import MagicMock, Mock, patch

import tango
from assertpy import assert_that

from ska_integration_test_harness.config.config_issue import (
    ConfigurationError,
    ConfigurationWarning,
)
from ska_integration_test_harness.config.config_validator import (
    DeviceNamesValidator,
    EmulationConsistencyValidator,
    RequiredFieldsValidator,
    SubsystemConfigurationValidator,
)
from tests.config.utils.dummy_config import DummySubsystemConfiguration


class DummyValidator(SubsystemConfigurationValidator):
    """A dummy validator for testing purposes."""

    def validate(self, _):
        """Dummy validation method."""


# 1. Tests for SubsystemConfigurationValidator
class TestSubsystemConfigurationValidator:
    """Validator initializes correctly and handles errors and warnings."""

    def test_initialization_with_default_logger(self):
        """Validator initializes with no logger."""
        validator = DummyValidator()
        assert_that(validator.logger).is_none()

    def test_initialization_with_custom_logger(self):
        """Validator initializes with a provided logger."""
        mock_logger = Mock()
        validator = DummyValidator(logger=mock_logger)
        assert_that(validator.logger).is_equal_to(mock_logger)

    def test_reset_clears_errors_and_warnings(self):
        """Resetting the validator clears errors and warnings."""
        validator = DummyValidator()
        validator.add_error("Test error")

        validator.reset()

        assert_that(validator.errors_and_warnings).is_empty()

    def test_is_valid_returns_true_if_no_errors(self):
        """Validator returns True for valid configuration without errors."""
        validator = DummyValidator()
        assert_that(validator.is_valid()).is_true()

    def test_is_valid_returns_false_if_critical_issues(self):
        """Validator returns False if critical issues exist."""
        validator = DummyValidator()
        validator.add_error("Critical error")
        assert_that(validator.is_valid()).is_false()

    def test_add_error_creates_critical_issue(self):
        """Adding an error creates a critical issue."""
        validator = DummyValidator()
        validator.add_error("Critical error")
        assert_that(validator.errors_and_warnings[0]).is_instance_of(
            ConfigurationError
        )

    def test_add_warning_creates_non_critical_issue(self):
        """Adding a warning creates a non-critical issue."""
        validator = DummyValidator()
        validator.add_warning("Non-critical warning")
        assert_that(validator.errors_and_warnings[0]).is_instance_of(
            ConfigurationWarning
        )

    def test_add_error_logs_issue_if_logger_available(self):
        """Add error method logs the issue if a logger is available."""
        validator = DummyValidator()
        validator.logger = Mock()

        with patch.object(ConfigurationError, "log") as mock_log:
            validator.add_error("Test error")

        mock_log.assert_called_once_with(validator.logger)

    def test_get_critical_errors_returns_only_critical_issues(self):
        """Get critical errors returns only critical issues."""
        validator = DummyValidator()
        validator.add_error("Critical error")
        validator.add_warning("Non-critical warning")

        critical_errors = validator.get_critical_errors()

        assert_that(critical_errors).is_length(1)
        assert_that(critical_errors[0].is_critical()).is_true()


# 2. Tests for RequiredFieldsValidator
class TestRequiredFieldsValidator:
    """Required fields validator detects missing or incorrect attributes."""

    def test_validate_all_required_fields_present(self):
        """Validation passes when all required fields are present."""
        config = DummySubsystemConfiguration(
            device_name="valid/device", required_attribute="value"
        )
        validator = RequiredFieldsValidator()

        validator.validate(config)

        assert_that(validator.errors_and_warnings).is_empty()

    def test_validate_missing_required_field(self):
        """Validation adds an error if required field is missing."""
        config = DummySubsystemConfiguration(
            device_name="valid/device", required_attribute=None
        )
        validator = RequiredFieldsValidator()

        validator.validate(config)

        assert_that(validator.errors_and_warnings).is_not_empty()
        assert_that(validator.errors_and_warnings[0].message).contains(
            "The attribute 'required_attribute' is missing."
        )

    def test_validate_incorrect_type_for_field(self):
        """Validation adds an error if field has incorrect type."""
        config = DummySubsystemConfiguration(
            device_name=12345, required_attribute="value"
        )
        validator = RequiredFieldsValidator()

        validator.validate(config)

        assert_that(validator.errors_and_warnings).is_not_empty()
        assert_that(validator.errors_and_warnings[0].message).contains(
            "The attribute 'device_name' is not of the expected type"
        )


# 3. Tests for DeviceNamesValidator
class TestDeviceNamesValidator:
    """Device names validator correctly identifies invalid devices."""

    def test_validate_device_names_valid(self):
        """Validation passes when all device names are valid and reachable."""
        with patch("tango.DeviceProxy", Mock()) as mock_device_proxy:
            config = DummySubsystemConfiguration(
                device_name="valid/device", required_attribute="value"
            )

            validator = DeviceNamesValidator()
            validator.validate(config)

            assert_that(validator.errors_and_warnings).is_empty()
            mock_device_proxy.assert_called_once_with("valid/device")

    def test_validate_device_name_invalid(self):
        """Validation adds an error if a device name is invalid.

        (or unreachable)."""
        with patch(
            "tango.DeviceProxy", Mock(side_effect=tango.DevFailed("error"))
        ):
            config = DummySubsystemConfiguration(
                device_name="invalid/device", required_attribute="value"
            )

            validator = DeviceNamesValidator()
            validator.validate(config)

            assert_that(validator.errors_and_warnings).is_not_empty()
            assert_that(validator.errors_and_warnings[0].message).contains(
                "Device 'invalid/device' is unreachable"
            )


# 4. Tests for EmulationConsistencyValidator
class TestEmulationConsistencyValidator:
    """Emulation consistency validator checks device emulation correctly."""

    def _create_mock_device(self, is_emulated: bool):
        """Create a mock device with the specified emulation status."""
        device = MagicMock()

        attributes = ["attrName"]
        if is_emulated:
            attributes.append("commandCallInfo")

        device.get_attribute_list.return_value = attributes

        return device

    def test_validate_emulator_consistency_correct(self):
        """Validation passes when device is correctly marked as emulator."""
        with patch(
            "tango.DeviceProxy",
            return_value=self._create_mock_device(is_emulated=True),
        ):
            config = DummySubsystemConfiguration(
                device_name="emulated/device",
                required_attribute="value",
                is_emulated=True,
            )

            validator = EmulationConsistencyValidator()
            validator.validate(config)

            assert_that(validator.errors_and_warnings).is_empty()

    def test_validate_emulation_consistency_incorrect(self):
        """When device is not an emulator and configuration specifies it is,
        validation adds a warning."""
        with patch(
            "tango.DeviceProxy",
            return_value=self._create_mock_device(is_emulated=False),
        ):
            config = DummySubsystemConfiguration(
                device_name="production/device",
                required_attribute="value",
                is_emulated=True,
            )

            validator = EmulationConsistencyValidator()
            validator.validate(config)

            assert_that(validator.errors_and_warnings).is_not_empty()
            assert_that(validator.errors_and_warnings[0].message).contains(
                "specifies that the devices are emulated, but the device "
                "'production/device' looks like it is not an emulator"
            )
