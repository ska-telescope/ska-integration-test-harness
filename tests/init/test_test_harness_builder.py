"""Unit tests for TestHarnessBuilder."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.init.test_harness_builder import (
    TestHarnessBuilder,
)
from ska_integration_test_harness.inputs.json_input import (
    JSONInput,
    StrJSONInput,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TestTestHarnessBuilder:
    """Unit tests for TestHarnessBuilder.

    Since this is a particularly critical component, we test it minimizing
    the use of mocks and patches. We use them only when strictly necessary
    (e.g., Tango API). The used configurations are realistic ones, taken
    from TMC-CSP MID integration tests. The passed input instead are JSON,
    but not semantically meaningful (it doesn't matter for the tests,
    since they will be needed only in teardown procedures or similar).
    """

    CONFIG_DATA_DIR = "tests/config_examples"

    @pytest.fixture
    def config_file(self) -> str:
        """Create a path to a valid configuration file."""
        return f"{self.CONFIG_DATA_DIR}/valid_test_harness_config.yaml"

    @pytest.fixture
    def missing_section_config_file(self) -> str:
        """Create a path to a configuration file with a missing section."""
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_section.yaml"

    @pytest.fixture
    def missing_key_config_file(self) -> str:
        """Create a path to a configuration file with a missing key."""
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_centralnode_name.yaml"

    @pytest.fixture
    def valid_json_input(self) -> JSONInput:
        """Create an example of valid JSON input."""
        return StrJSONInput('{"key": "value"}')

    @pytest.fixture
    def invalid_json_input(self) -> JSONInput:
        """Create an example of invalid JSON input."""
        return StrJSONInput('{"key": "value"')

    # -------------------------------------------------------------------------
    # Test configuration collection procedures

    def test_validate_config_with_valid_file_terminates_successfully(
        self, config_file: str
    ):
        """When a valid configuration file is passed, the validation succeeds.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder()

        builder.read_config_file(config_file)

        with patch("tango.DeviceProxy", MagicMock()):
            builder.validate_configurations()

        assert_that(builder.is_config_validated()).is_true()

    def test_validate_config_with_missing_section_raises_value_error(
        self, missing_section_config_file: str
    ):
        """When a config file misses a subsystem section,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.read_config_file(missing_section_config_file)

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    def test_validate_config_with_missing_key_raises_value_error(
        self, missing_key_config_file: str
    ):
        """When a config file misses a key in a subsystem section,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.read_config_file(missing_key_config_file)

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    def test_validate_config_with_no_config_raises_value_error(self):
        """When no configuration is set, the validation raises a ValueError."""
        builder = TestHarnessBuilder()
        assert_that(builder.is_config_validated()).is_false()

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    # -------------------------------------------------------------------------
    # Test input collection procedures

    def test_validate_input_with_valid_input_terminates_successfully(
        self, valid_json_input: JSONInput
    ):
        """When all default inputs are passed and they are valid,
        the validation succeeds.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )

        builder.validate_default_inputs()

        assert_that(builder.are_default_inputs_validated()).is_true()

    def test_validate_input_with_missing_value_raises_value_error(
        self, valid_json_input: JSONInput
    ):
        """When a default input is missing,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                # scan_input=valid_json_input
            )
        )

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated())

    def test_validate_input_with_invalid_input_raises_value_error(
        self, invalid_json_input: str
    ):
        """When a default input is invalid,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=invalid_json_input,
                assign_input=invalid_json_input,
                configure_input=invalid_json_input,
                release_input=invalid_json_input,
                scan_input=invalid_json_input,
            )
        )

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated()).is_false()

    def test_validate_input_with_no_input_raises_value_error(self):
        """When no default input is set, the validation raises a ValueError."""
        builder = TestHarnessBuilder()
        assert_that(builder.are_default_inputs_validated()).is_false()

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated()).is_false()

    # -------------------------------------------------------------------------
    # Test build method

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_valid_config_and_inputs_terminates_successfully(
        self, config_file: str, valid_json_input: JSONInput
    ):
        """HAPPY PATH: when the correct configs and inputs are passed,
        the build method completes successfully."""

        builder = TestHarnessBuilder()

        builder.read_config_file(config_file)
        builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        builder.validate_default_inputs()

        telescope_wrapper = builder.build()

        assert_that(telescope_wrapper).is_instance_of(TelescopeWrapper)
        telescope_wrapper.fail_if_not_set_up()

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_not_validated_but_config_and_input_logs_warning(
        self, config_file: str, valid_json_input: JSONInput
    ):
        """HAPPY PATH (but with warnings): when the correct configs and inputs
        are passed, the build method completes successfully. Since no explicit
        validation is done (and a logger is available), a warning is logged."""

        # patch method logging.getLogger to return MagicMock
        builder = TestHarnessBuilder()
        mock_logger = MagicMock()
        builder.logger = mock_logger

        builder.read_config_file(config_file)
        # builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        # builder.validate_default_inputs()
        telescope_wrapper = builder.build()

        assert_that(telescope_wrapper).is_instance_of(TelescopeWrapper)
        telescope_wrapper.fail_if_not_set_up()

        # check that the warnings were logged
        mock_logger.warning.assert_called()
        logger_warning_calls = mock_logger.warning.call_args_list
        assert_that(logger_warning_calls).is_length(2)
        # (args[1] because of log.warning("PREFIX: %s", *args) signature)
        assert_that(logger_warning_calls[0].args[1]).contains_ignoring_case(
            "build", "test harness", "without validating", "configurations"
        )
        assert_that(logger_warning_calls[1].args[1]).contains_ignoring_case(
            "build", "test harness", "without validating", "default inputs"
        )

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_invalid_config_raises_some_error(
        self, missing_section_config_file: str
    ):
        """When an invalid configuration is passed, the build method is
        expected to fail. In this case, the failure is an attribute error
        (since the initialisation procedure will not be able to find
        a required attribute).
        """

        builder = TestHarnessBuilder()

        builder.read_config_file(missing_section_config_file)
        with pytest.raises(AttributeError):
            builder.build()
