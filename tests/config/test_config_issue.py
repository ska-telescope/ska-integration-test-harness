"""Unit tests for the ConfigurationIssue hierarchy."""

import logging

from assertpy import assert_that

from ska_integration_test_harness.config.validation.config_issue import (
    ConfigurationError,
    ConfigurationWarning,
    create_configuration_issue,
)


class TestConfigurationIssue:
    """Unit tests for the ConfigurationIssue hierarchy."""

    @staticmethod
    def test_configuration_error_is_critical_returns_true() -> None:
        """ConfigurationError should return True for is_critical."""
        error = ConfigurationError("Critical error")
        assert_that(error.is_critical()).is_true()

    @staticmethod
    def test_configuration_warning_is_critical_returns_false() -> None:
        """ConfigurationWarning should return False for is_critical."""
        warning = ConfigurationWarning("Non-critical warning")
        assert_that(warning.is_critical()).is_false()

    @staticmethod
    def test_configuration_error_logs_error(caplog) -> None:
        """ConfigurationError should log an error message."""
        error = ConfigurationError("Critical error")
        with caplog.at_level(logging.ERROR):
            error.log(logging.getLogger())
        assert_that(caplog.text).contains(
            "CONFIGURATION ERROR: Critical error"
        )

    @staticmethod
    def test_configuration_warning_logs_warning(caplog) -> None:
        """ConfigurationWarning should log a warning message."""
        warning = ConfigurationWarning("Non-critical warning")
        with caplog.at_level(logging.WARNING):
            warning.log(logging.getLogger())
        assert_that(caplog.text).contains(
            "CONFIGURATION WARNING: Non-critical warning"
        )

    @staticmethod
    def test_create_config_issue_with_critical_returns_error() -> None:
        """create_configuration_issue with is_critical=True returns an error.

        (i.e., an instance of ConfigurationError)
        """
        issue = create_configuration_issue("Critical error", is_critical=True)
        assert_that(issue).is_instance_of(ConfigurationError)

    @staticmethod
    def test_create_config_issue_with_non_critical_returns_warning() -> None:
        """create_configuration_issue with is_critical=False returns a warning.

        (i.e., an instance of ConfigurationWarning)
        """
        issue = create_configuration_issue(
            "Non-critical warning", is_critical=False
        )
        assert_that(issue).is_instance_of(ConfigurationWarning)
