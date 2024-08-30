"""Unit tests for the TestHarnessInputs data class."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)


class TestTestHarnessInputs:
    """Unit tests for the TestHarnessInputs data class."""

    def test_get_input_returns_correct_json_input(self) -> None:
        """get_input returns the correct JSONInput for valid InputName."""
        mock_input = MagicMock(spec=JSONInput)
        harness_inputs = TestHarnessInputs(
            default_vcc_config_input=mock_input,
            assign_input=None,
            configure_input=None,
            scan_input=None,
            release_input=None,
        )

        result = harness_inputs.get_input(
            TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG
        )

        assert_that(result).is_equal_to(mock_input)

        # setting fail_if_missing to True should not raise an exception
        result = harness_inputs.get_input(
            TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG,
            fail_if_missing=True,
        )

        assert_that(result).is_equal_to(mock_input)

    def test_get_input_returns_none_for_missing_input(self) -> None:
        """get_input returns None for missing input."""
        harness_inputs = TestHarnessInputs()
        result = harness_inputs.get_input(
            TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG
        )
        assert_that(result).is_none()

    def test_get_input_raises_exception_for_missing_input(self) -> None:
        """get_input raises ValueError for missing input.
        (if fail_if_missing is True)."""
        harness_inputs = TestHarnessInputs()
        with pytest.raises(ValueError):
            harness_inputs.get_input(
                TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG,
                fail_if_missing=True,
            )

    def test_get_non_none_json_inputs_returns_correct_dict(self) -> None:
        """get_non_none_json_inputs returns correct dict of non-None inputs."""
        mock_default_vcc = MagicMock(spec=JSONInput)
        mock_assign = MagicMock(spec=JSONInput)
        harness_inputs = TestHarnessInputs(
            default_vcc_config_input=mock_default_vcc,
            assign_input=mock_assign,
            configure_input=None,
            scan_input=None,
            release_input=None,
        )

        result = harness_inputs.get_non_none_json_inputs()

        assert_that(result).is_type_of(dict).contains_entry(
            {TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG: mock_default_vcc}
        ).contains_entry({TestHarnessInputs.InputName.ASSIGN: mock_assign})

    def test_get_non_none_json_inputs_returns_empty_dict(self) -> None:
        """get_non_none_json_inputs returns empty dict if no input is set."""
        harness_inputs = TestHarnessInputs()
        result = harness_inputs.get_non_none_json_inputs()
        assert_that(result).is_empty()
