"""A JSON input for the subarray, built around a dictionary."""

import json
from typing import Any

from ska_integration_test_harness.inputs.json_input import JSONInput


class DictJSONInput(JSONInput):
    """A JSON input for the subarray, built around a dictionary."""

    def __init__(self, json_dict: dict):
        """Initialise the JSON input with a dictionary."""
        super().__init__()
        self._json_dict = json_dict

    def get_json_string(self) -> str:
        """Return the JSON string representation of the input."""
        return json.dumps(self._json_dict)

    def set_attribute_value(
        self, attr_name: str, attr_value: Any
    ) -> "DictJSONInput":
        new_json_dict = self._json_dict.copy()
        new_json_dict[attr_name] = attr_value
        return DictJSONInput(new_json_dict)
