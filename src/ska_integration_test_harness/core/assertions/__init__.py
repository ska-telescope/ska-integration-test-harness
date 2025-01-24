"""A collection of assertion objects and functions for use in test cases.

This module provides a collection of assertion (abstract and concrete) classes,
for defining and executing verifications and synchronizations against a
(Tango based) system under test (SUT).

**What is an assertion?** In abstract terms, an assertion is supposed to be a
generic verification or synchronization operation. Actually it can be anything
that verifies some kind of property.

Representing assertions as classes have not been an easy choice,
since the risk of producing or encouraging the production of
over-engineered boilerplate code is high. **Before going further, we want to
to remind that inn testing contexts there are many ways to assert things**:

- using the built-in Python
  `assert <https://docs.pytest.org/en/stable/assert.html>`_ statement
- using various assertion methods provided by libraries such as
  `assertpy <https://assertpy.github.io/docs.html>`_,
- using :py:mod:`ska_tango_testing` and :py:mod:`ska_tango_testing.integration`
  utilities for specifically asserting over Tango devices.

However, we decided to define a set of classes for defining assertion classes
in the context of the ITH because:

- When building a test harness that has to systematically
  verify a large number of properties on a large number of devices, sometimes
  you want to re-use the same assertion logic in many situations
"""

from .attribute import AssertDevicesAreInState
from .state_changes import AssertDevicesStateChanges
from .sut_assertion import SUTAssertion
from .tracer_assertion import TracerAssertion

__all__ = [
    "SUTAssertion",
    "TracerAssertion",
    "AssertDevicesStateChanges",
    "AssertDevicesAreInState",
]
