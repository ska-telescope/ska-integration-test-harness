"""Unit tests for the JSONInput hierarchy."""

import json
from unittest.mock import mock_open, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.inputs.json_input import (
    DictJSONInput,
    FileJSONInput,
    StrJSONInput,
)


class TestDictJSONInput:
    """Tests for the DictJSONInput class."""

    def test_as_str_returns_correct_json_string(self) -> None:
        """as_str returns the correct JSON string representation."""
        json_input = DictJSONInput({"key": "value"})

        assert_that(json_input.as_str()).is_equal_to('{"key": "value"}')

    def test_as_dict_returns_correct_dict(self) -> None:
        """as_dict returns the correct dictionary representation."""
        json_input = DictJSONInput({"key": "value"})

        assert_that(json_input.as_dict()).is_equal_to({"key": "value"})

    def test_with_attribute_adds_new_attribute(self) -> None:
        """with_attribute adds a new attribute and returns a new instance."""
        json_input = DictJSONInput({"key": "value"})
        new_json_input = json_input.with_attribute("new_key", "new_value")

        assert_that(new_json_input.as_dict()).is_equal_to(
            {"key": "value", "new_key": "new_value"}
        )
        assert_that(new_json_input).is_not_equal_to(json_input)

    def test_is_equal_to_json_with_str(self) -> None:
        """is_equal_to_json correctly compares against a JSON string."""
        json_input = DictJSONInput({"key": "value"})

        assert_that(json_input.is_equal_to_json('{"key": "value"}')).is_true()
        assert_that(
            json_input.is_equal_to_json(
                '{"key": "value", "new_key": "new_value"}'
            )
        ).is_false()
        assert_that(
            json_input.is_equal_to_json('{"key": "value2"}')
        ).is_false()

    def test_is_equal_to_json_with_dict(self) -> None:
        """is_equal_to_json correctly compares against a JSON dictionary."""
        json_input = DictJSONInput({"key": "value"})

        assert_that(json_input.is_equal_to_json('{"key": "value"}')).is_true()
        assert_that(json_input.is_equal_to_json({"key": "value"})).is_true()
        assert_that(
            json_input.is_equal_to_json(
                {"key": "value", "new_key": "new_value"}
            )
        ).is_false()


class TestStrJSONInput:
    """Tests for the StrJSONInput class."""

    def test_as_str_returns_input_string(self) -> None:
        """as_str returns the original JSON string."""
        json_input = StrJSONInput('{"key": "value"}')

        assert_that(json_input.as_str()).is_equal_to('{"key": "value"}')

    def test_as_dict_returns_correct_dict(self) -> None:
        """as_dict returns the correct dictionary representation."""
        json_input = StrJSONInput('{"key": "value"}')

        assert_that(json_input.as_dict()).is_equal_to({"key": "value"})

    def test_as_dict_raises_json_decode_error_for_invalid_json(self) -> None:
        """as_dict raises JSONDecodeError for invalid JSON strings."""
        json_input = StrJSONInput("invalid json")

        with pytest.raises(json.JSONDecodeError):
            json_input.as_dict()

    def test_with_attribute_adds_new_attribute(self) -> None:
        """with_attribute adds a new attribute and returns a new instance."""
        json_input = StrJSONInput('{"key": "value"}')
        new_json_input = json_input.with_attribute("new_key", "new_value")

        assert_that(isinstance(new_json_input, DictJSONInput)).is_true()
        assert_that(new_json_input.as_dict()).is_equal_to(
            {"key": "value", "new_key": "new_value"}
        )

    def test_with_attribute_raises_json_decode_error_for_invalid_json(
        self,
    ) -> None:
        """with_attribute raises JSONDecodeError for invalid JSON strings."""
        json_input = StrJSONInput("invalid json")

        with pytest.raises(json.JSONDecodeError):
            json_input.with_attribute("new_key", "new_value")

    def test_compare_with_dict_json_input(self) -> None:
        """__eq__ correctly compares against a DictJSONInput instance."""
        str_json_input = StrJSONInput('{"key": "value"}')
        dict_json_input = DictJSONInput({"key": "value"})

        assert_that(str_json_input).is_equal_to(dict_json_input)


class TestFileJSONInput:
    """Tests for the FileJSONInput class."""

    def test_constructor_reads_file_content_correctly(self) -> None:
        """Constructor reads the file content into the JSON string."""
        mock_json_content = '{"key": "value"}'
        with patch("builtins.open", mock_open(read_data=mock_json_content)):
            json_input = FileJSONInput("dummy_path.json")
            assert_that(json_input.as_str()).is_equal_to(mock_json_content)

    def test_constructor_reads_unvalid_json_file_without_error(self) -> None:
        """Constructor reads unvalid JSON file without raising an error."""
        mock_json_content = '{"key": "value"'
        with patch("builtins.open", mock_open(read_data=mock_json_content)):
            json_input = FileJSONInput("dummy_path.json")
            assert_that(json_input.as_str()).is_equal_to(mock_json_content)

    def test_constructor_raises_filenotfounderror(self) -> None:
        """Constructor raises FileNotFoundError if file does not exist."""
        with pytest.raises(FileNotFoundError):
            FileJSONInput("non_existent_file.json")

    def test_constructor_raises_permissionerror(self) -> None:
        """Constructor raises PermissionError if file is not readable."""
        with patch("builtins.open", side_effect=PermissionError):
            with pytest.raises(PermissionError):
                FileJSONInput("unreadable_file.json")
