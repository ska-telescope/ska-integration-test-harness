"""Template for a generic JSON input."""

import abc
import json
from typing import Any


class JSONInput(abc.ABC):
    """Template for a generic JSON input.

    This class is an abstract class that defines a template for a JSON input
    for a command on the telescope. It is meant to be used as a base class
    to implement your own way to provide that JSON value.

    IMPORTANT NOTE: This class instances are meant to be immutable. If you need
    to change the value of the JSON input, you should create a new instance
    with the new value (see the `with_attribute` method).
    """

    @abc.abstractmethod
    def as_str(self) -> str:
        """Return the JSON string representation of the input.

        This representation is not guaranteed to be valid JSON, but it should
        always be guaranteed to be returned as a string without raising any
        exceptions.

        :return: The JSON string representation of the input.
        """

    @abc.abstractmethod
    def as_dict(self) -> dict:
        """Return the JSON dictionary representation of the input.

        This representation is guaranteed to be a valid JSON dictionary, but
        it may raise an exception if this instance represents an invalid JSON
        string.

        :return: The JSON dictionary representation of the input.
        :raises json.JSONDecodeError: if the JSON string is invalid.
        """

    @abc.abstractmethod
    def with_attribute(self, attr_name: str, attr_value: Any) -> "JSONInput":
        """Decorate the input with an additional attribute.

        This method should return a new instance of the JSON input with the
        specified attribute set to the specified value.

        This representation is guaranteed to be a valid JSON dictionary, but
        it may raise an exception if this instance represents an invalid JSON
        string.

        :param attr_name: the name of the attribute to set
        :param attr_value: the value to set for the attribute
        :raises json.JSONDecodeError: if the JSON string is invalid.
        """

    def __str__(self) -> str:
        """Return the JSON string representation of the input."""
        return self.as_str()

    def __repr__(self) -> str:
        """Return the JSON string representation of the input."""
        return self.as_str()

    def __eq__(self, other: object) -> bool:
        """Check if two JSON inputs are equal."""
        # by default, two JSON inputs are equal
        # if their JSON dictionaries are equal
        if isinstance(other, JSONInput):
            return self.as_dict() == other.as_dict()

        if isinstance(other, (dict, str)):
            return self.is_equal_to_json(other)

        return False

    def is_equal_to_json(self, json_data: dict | str) -> bool:
        """Check if this input is equal to the provided JSON data."""
        if isinstance(json_data, str):
            return self.as_dict() == json.loads(json_data)

        return self.as_dict() == json_data


class DictJSONInput(JSONInput):
    """A JSON input that is represented as a dictionary.

    This class is a concrete implementation of the JSONInput abstract class
    which uses a dictionary to represent the JSON input. This class is useful
    when the JSON input you want to provide is already a dictionary.

    Since a dictionary can be always converted to a valid JSON string, this
    class is guaranteed to always return a valid JSON string representation.
    Since the representation is valid, ``as_dict`` and ``with_attribute`` will
    never raise an exception.
    """

    def __init__(self, json_dict: dict):
        """Create a new JSON input from a JSON dictionary."""
        self._json_dict = json_dict

    def as_str(self) -> str:
        """Return the JSON string representation of the input."""
        return json.dumps(self._json_dict)

    def as_dict(self) -> dict:
        """Return the JSON dictionary representation of the input."""
        return self._json_dict.copy()

    def with_attribute(self, attr_name: str, attr_value: Any) -> "JSONInput":
        """Decorate the input with an additional attribute."""
        new_dict = self.as_dict()
        new_dict[attr_name] = attr_value
        return DictJSONInput(new_dict)


class StrJSONInput(JSONInput):
    """A JSON input that is represented as a string.

    This class is a concrete implementation of the JSONInput abstract class
    which uses a string to represent the JSON input. This class is useful when
    the JSON input is already a string and you don't want to necessarily parse
    it to a dictionary.

    IMPORTANT NOTE: The string representation of the JSON input is not
    guaranteed to be a valid JSON string. This means that the ``as_dict`` and
    ``with_attribute`` methods may raise an exception if the JSON string is
    invalid. However, the ``as_str`` method should always return a string.
    """

    def __init__(self, json_str: str):
        """Create a new JSON input from a JSON string."""
        self._json_str = json_str

    def as_str(self) -> str:
        """Return the JSON string representation of the input."""
        return self._json_str

    def as_dict(self) -> dict:
        """Return the JSON dictionary representation of the input."""
        return json.loads(self._json_str)

    def with_attribute(self, attr_name: str, attr_value: Any) -> "JSONInput":
        """Decorate the input with an additional attribute."""
        return DictJSONInput(self.as_dict()).with_attribute(
            attr_name, attr_value
        )


class FileJSONInput(StrJSONInput):
    """A JSON input that is represented as a file path.

    This class is a concrete implementation of the JSONInput abstract class
    which uses a file path to represent the JSON input. This class is useful
    when the JSON input is already a file path and you don't want
    to necessarily parse it to a dictionary.

    IMPORTANT NOTE: The string representation of the JSON input is not
    guaranteed to be a valid JSON string. This means that the ``as_dict`` and
    ``with_attribute`` methods may raise an exception if the JSON string is
    invalid. However, the ``as_str`` method should always return a string.

    OTHER IMPORTANT NOTE: Since the file path is used to represent the
    JSON input, this class constructor may raise the exceptions you would
    expect when working with files (e.g., FileNotFoundError, PermissionError).
    """

    def __init__(self, json_file: str, encoding: str = "utf-8"):
        """Create a new JSON input from a JSON file.

        :param json_file: the path to the JSON file.
        :param encoding: the expected encoding to use to read the file.
            It defaults to "utf-8".

        :raises FileNotFoundError: if the file does not exist.
        :raises PermissionError: if the file is not readable.
        """
        with open(json_file, "r", encoding=encoding) as file:
            json_str = file.read()
        super().__init__(json_str)
