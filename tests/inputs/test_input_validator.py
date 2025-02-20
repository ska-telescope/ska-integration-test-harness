"""Unit tests for BasicInputValidator class"""

import pytest
from assertpy import assert_that

from ska_integration_test_harness.inputs.json_input import (
    DictJSONInput,
    StrJSONInput,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.inputs.validation.input_validator import (
    BasicInputValidator,
)


class TestBasicInputValidator:
    """Unit tests  for BasicInputValidator class"""

    @pytest.fixture
    def validator(self) -> BasicInputValidator:
        """Fixture for BasicInputValidator instance"""
        return BasicInputValidator()

    @pytest.fixture
    def valid_inputs(self) -> TestHarnessInputs:
        """Fixture for valid TestHarnessInputs instance"""
        return TestHarnessInputs(
            default_vcc_config_input=DictJSONInput({"key": "value"}),
            assign_input=DictJSONInput({"key": "value"}),
            configure_input=DictJSONInput({"key": "value"}),
            scan_input=DictJSONInput({"key": "value"}),
            release_input=DictJSONInput({"key": "value"}),
        )

    @pytest.fixture
    def invalid_inputs(self) -> TestHarnessInputs:
        """Fixture for TestHarnessInputs instance with invalid JSON"""
        return TestHarnessInputs(
            default_vcc_config_input=StrJSONInput('{"key": "value"'),
            assign_input=DictJSONInput({"key": "value"}),
            configure_input=DictJSONInput({"key": "value"}),
            scan_input=DictJSONInput({"key": "value"}),
            release_input=DictJSONInput({"key": "value"}),
        )

    @pytest.fixture
    def incomplete_inputs(self) -> TestHarnessInputs:
        """Fixture for TestHarnessInputs instance with missing inputs"""
        return TestHarnessInputs(
            default_vcc_config_input=DictJSONInput({"key": "value"}),
            assign_input=None,  # Missing this input
            configure_input=DictJSONInput({"key": "value"}),
            scan_input=DictJSONInput({"key": "value"}),
            release_input=None,  # Missing this input
        )

    def test_validate_inputs_presence_logs_all_present(
        self, validator: BasicInputValidator, valid_inputs: TestHarnessInputs
    ) -> None:
        """Does not raise any error if all required inputs are present"""
        validator.validate_inputs_presence(valid_inputs)
        assert_that(True).is_true()  # If no exception, test passes

    def test_validate_inputs_correctness_raises_valueerror_if_json_invalid(
        self, validator: BasicInputValidator, invalid_inputs: TestHarnessInputs
    ) -> None:
        """Raises ValueError if input JSON is invalid"""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_inputs_correctness(invalid_inputs)
        assert_that(str(exc_info.value)).contains("is not valid JSON")

    def test_validate_inputs_correctness_logs_all_jsons_valid(
        self, validator: BasicInputValidator, valid_inputs: TestHarnessInputs
    ) -> None:
        """Does not raise any error if all inputs are valid JSONs"""
        validator.validate_inputs_correctness(valid_inputs)
        assert_that(True).is_true()  # If no exception, test passes

    def test_validate_inputs_presence_raises_valueerror_if_some_inputs_missing(
        self,
        validator: BasicInputValidator,
        incomplete_inputs: TestHarnessInputs,
    ) -> None:
        """Raises ValueError if not all required inputs are set"""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_inputs_presence(incomplete_inputs)
        assert_that(str(exc_info.value)).contains_ignoring_case(
            str(incomplete_inputs.InputName.ASSIGN), "is missing"
        )

    # --------------------------------------------------------------
    # Additional unit test for low

    def test_validate_inputs_presence_raises_valueerror_if_mid_input_miss(
        self,
        validator: BasicInputValidator,
    ) -> None:
        """Raises ValueError if not all required inputs are set"""
        incomplete_inputs = TestHarnessInputs(
            default_vcc_config_input=None,  # Missing this input
            assign_input=DictJSONInput({"key": "value"}),
            configure_input=DictJSONInput({"key": "value"}),
            scan_input=DictJSONInput({"key": "value"}),
            release_input=DictJSONInput({"key": "value"}),
        )
        with pytest.raises(ValueError) as exc_info:
            validator.validate_inputs_presence(incomplete_inputs)
        assert_that(str(exc_info.value)).contains_ignoring_case(
            str(incomplete_inputs.InputName.DEFAULT_VCC_CONFIG), "is missing"
        )

    def test_validate_inputs_presence_pass_in_low_without_mid_input(
        self,
        validator: BasicInputValidator,
    ) -> None:
        """Does not raise any error if all required inputs are present"""
        valid_inputs = TestHarnessInputs(
            default_vcc_config_input=None,  # Missing this input
            assign_input=DictJSONInput({"key": "value"}),
            configure_input=DictJSONInput({"key": "value"}),
            scan_input=DictJSONInput({"key": "value"}),
            release_input=DictJSONInput({"key": "value"}),
        )
        validator.validate_inputs_presence(valid_inputs, is_mid=False)
        assert_that(True).is_true()
