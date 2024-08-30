from unittest.mock import create_autospec

import pytest
from assertpy import assert_that

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)
from ska_integration_test_harness.config.validation.config_validator import (
    BasicConfigurationValidator,
    ConfigurationValidator,
)
from ska_integration_test_harness.config.validation.subsys_config_validator import (  # pylint: disable=line-too-long # noqa: E501
    SubsystemConfigurationValidator,
)


class TestBasicConfigurationValidator:
    """Tests for BasicConfigurationValidator class."""

    @pytest.fixture
    def validator(self) -> ConfigurationValidator:
        """Fixture to create an instance of BasicConfigurationValidator."""
        return BasicConfigurationValidator()

    @pytest.fixture
    def valid_config(self) -> TestHarnessConfiguration:
        """Fixture to create a valid TestHarnessConfiguration."""
        return TestHarnessConfiguration(
            tmc_config=TMCConfiguration(),
            csp_config=CSPConfiguration(),
            sdp_config=SDPConfiguration(),
            dishes_config=DishesConfiguration(),
        )

    def test_validate_subsystems_presence_with_all_required_subsystems(
        self,
        validator: ConfigurationValidator,
        valid_config: TestHarnessConfiguration,
    ):
        """No error is raised if all required subsystems are present."""
        try:
            validator.validate_subsystems_presence(valid_config)
        except ValueError as e:
            pytest.fail(f"Unexpected ValueError: {e}")

    def test_validate_subsystems_presence_missing_subsystem_raises_error(
        self, validator: ConfigurationValidator
    ):
        """A ValueError is raised if a required subsystem is missing."""
        incomplete_config = TestHarnessConfiguration(
            tmc_config=None,
            csp_config=CSPConfiguration(),
            sdp_config=SDPConfiguration(),
            dishes_config=DishesConfiguration(),
        )
        with pytest.raises(ValueError) as exc_info:
            validator.validate_subsystems_presence(incomplete_config)

        assert_that(str(exc_info.value)).contains_ignoring_case(
            "Configuration", "TMC", "is missing"
        )

    def test_validate_subsystems_configurations_applies_all_validators(
        self,
        validator: ConfigurationValidator,
        valid_config: TestHarnessConfiguration,
    ):
        """All subsystem validators are applied to the configuration."""
        mock_validator_1 = create_autospec(SubsystemConfigurationValidator)
        mock_validator_2 = create_autospec(SubsystemConfigurationValidator)
        mock_validator_3 = create_autospec(SubsystemConfigurationValidator)

        validator.subsystem_validators = [
            mock_validator_1,
            mock_validator_2,
            mock_validator_3,
        ]
        validator.validate_subsystems_configurations(valid_config)

        mock_validator_1.validate.assert_called()
        mock_validator_2.validate.assert_called()
        mock_validator_3.validate.assert_called()

    def test_validate_subsystems_configurations_raises_error_on_failure(
        self, validator: ConfigurationValidator, valid_config
    ):
        """A ValueError is raised if any subsystem validator fails."""
        mock_validator = create_autospec(SubsystemConfigurationValidator)
        mock_validator.is_valid.return_value = False
        mock_validator.get_critical_errors.return_value = [
            "Critical error 1",
            "Critical error 2",
        ]

        validator.subsystem_validators = [mock_validator]

        with pytest.raises(ValueError) as exc_info:
            validator.validate_subsystems_configurations(valid_config)

        assert_that(str(exc_info.value)).contains(
            "Critical error 1", "Critical error 2"
        )
