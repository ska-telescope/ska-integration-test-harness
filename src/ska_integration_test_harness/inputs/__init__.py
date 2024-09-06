"""A collection of (mostly abstract) classes to represent the required inputs.

This module contains classes that represent the required inputs
for the telescope actions. Mainly, those inputs come in the form of
JSON strings, for which we provide an abstraction to represent them.

Currently, it contains also some classes
(left outside from the documentation on purpose) to represent various data
types that - in theory - they should belong to external repositories but
that for some reason they are here.
"""

from .json_input import DictJSONInput, FileJSONInput, JSONInput, StrJSONInput
from .test_harness_inputs import TestHarnessInputs

__all__ = [
    "TestHarnessInputs",
    "JSONInput",
    "StrJSONInput",
    "DictJSONInput",
    "FileJSONInput",
]
