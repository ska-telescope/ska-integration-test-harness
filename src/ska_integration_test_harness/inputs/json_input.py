"""Template for a generic JSON input."""

import abc
import json
from typing import Any


class JSONInput(abc.ABC):
    """Template for a generic JSON input.

    This class is an abstract class that defines a template for a JSON input
    for a command over the telescope. It can be used to create a JSON input
    for various ``TelescopeAction``s.

    The idea is essentially you find your own way to get the JSON string
    and you implement the ``get_json_string`` method to return it. Starting
    from this, you can also:

    - get the JSON dictionary representation of the input with the
        ``get_json_dict`` method;
    - check if the JSON input is equal to another JSON string or dict with the
        ``is_equal_to_json`` method;
    - get the JSON string representation of the input with the ``__str__`` and
        ``__repr__`` methods;
    - check if two JSON inputs are equal with the ``__eq__`` method.

    You have also to implement the ``set_attribute_value`` method to permit
    the creation of a new JSON input with an attribute value set.
    """

    @abc.abstractmethod
    def get_json_string(self) -> str:
        """Return the JSON string representation of the input."""

    @abc.abstractmethod
    def set_attribute_value(
        self, attr_name: str, attr_value: Any
    ) -> "JSONInput":
        """Create a new JSON input with an attribute value set.

        :param attr_name: the name of the attribute to set
        :param attr_value: the value to set for the attribute
        """

    def get_json_dict(self) -> dict:
        """Return the JSON dictionary representation of the input."""
        return json.loads(self.get_json_string())

    def is_equal_to_json(self, other_json: str | dict) -> bool:
        """Check if the JSON input is equal to another JSON string or dict."""
        if isinstance(other_json, str):
            try:
                other_json = json.loads(other_json)
            except json.JSONDecodeError:
                return False
        return self.get_json_dict() == other_json

    def __str__(self) -> str:
        """Return the JSON string representation of the input."""
        return self.get_json_string()

    def __repr__(self) -> str:
        """Return the JSON string representation of the input."""
        return self.get_json_string()

    def __eq__(self, other: object) -> bool:
        """Check if two JSON inputs are equal."""
        # by default, two JSON inputs are equal
        # if their JSON dictionaries are equal
        if isinstance(other, JSONInput):
            return self.get_json_dict() == other.get_json_dict()

        # if the passed object is a (maybe JSON) string or dict,
        # we can still try a comparison with the appropriate method
        if isinstance(other, (dict, str)):
            return self.is_equal_to_json(other)

        return False
