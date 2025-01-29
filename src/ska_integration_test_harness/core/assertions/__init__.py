"""A collection of assertion objects and functions for use in test cases.

This module provides a collection of assertion (abstract and concrete) classes,
for defining and executing verifications and synchronizations against a
(Tango based) system under test (SUT).

**What is an assertion?** In abstract terms, an assertion is supposed to be a
generic verification of a system state or property. In an event based system
like Tango, an assertion is often a verification that some events are emitted,
in the past or in a certain time frame.

Representing assertions as classes have not been an easy choice,
since the risk of producing or encouraging the production of
over-engineered boilerplate code is high. **Before going further, we want to
remind you that in testing there are many tools to assert things**:

- using the built-in Python
  `assert <https://docs.pytest.org/en/stable/assert.html>`_ statement
- using various assertion methods provided by libraries such as
  `assertpy <https://assertpy.github.io/docs.html>`_,
- using :py:mod:`ska_tango_testing` and :py:mod:`ska_tango_testing.integration`
  utilities for specifically asserting over Tango devices.

However, we decided to define a set of classes for defining assertion classes
in the context of the ITH for the following reasons:

- The SUT is a complex system made of many components, so sometimes
  you may want to group multiple lower-level checks in few re-usable
  high-level assertion. Having a class structure helps in organizing
  the assertion code in standard modular pieces.
- The ITH has the purpose of engineering some aspects of the testing process,
  and for implementing some mechanisms you may want to separate the definition
  of an assertion from its execution.
  For example, you may want to compose a more complex object
  (e.g., an action - see :py:mod:`ska_integration_test_harness.core.actions.TracerAction`)
  injecting assertions as parameters. Representing assertions as classes
  makes it easier to define objects, pass them around and operate on them
  using a standard interface.
- The SUT is a distributed system, so often the assertion are event based.
  An assertion in an event based context often needs first to subscribe to
  some event, and then wait for the event to happen. Having a class structure
  helps in defining a standard interface for the various steps required
  to perform the assertion (e.g, setup and verification).

Just to be clear: **those classes are meant primarily to engineer
internal mechanisms inside the core and inside your own extensions of the ITH**.
If you are writing a test case, especially if you are in a THEN step,
you should prefer to directly use directly the assertion methods provided by
`assertpy <https://assertpy.github.io/docs.html>`_ and the
`ska-tango-testing <https://developer.skao.int/projects/ska-tango-testing/en/latest/guide/integration/getting_started.html>`_
utilities (this to facilitate tests readability and debugging).

So, given those premises, **how are actions implemented in the ITH?**
In this module we provide essentially two base classes for assertions:

- :py:class:`~ska_integration_test_harness.core.assertions.SUTAssertion`: a
  base class that defines the common interface for all the
  assertions in the ITH. It serves as an empty shell that defines the
  common shape of all assertion objects.
- :py:class:`~ska_integration_test_harness.core.assertions.TracerAssertion`: a
  subclass that represents event-based assertions that use the
  :py:class:`ska_tango_testing.integration.TangoEventTracer` to perform the
  verifications. This class explicitly introduces the concept of
  a timeout and of an early stop condition, and provides you utilities
  to operate with the tracer (potentially injecting it and the timeout
  from the outside to share them among different assertions).

Some concrete and ready-to-use assertions are:

- :py:class:`~ska_integration_test_harness.core.assertions.AssertDevicesAreInState`:
  a simple assertion that checks if a set of devices attributes have a
  specific value. Useful for defining simple non-event based checks.
- :py:class:`~ska_integration_test_harness.core.assertions.AssertDevicesStateChanges`:
  an assertion that checks if a set of devices attributes change their value
  in a specific way. Useful for defining simple event-based checks.

For further more complex assertions implementation, we suggest you to look at
:py:mod:`~ska_integration_test_harness.extensions.assertions`.
"""  # pylint: disable=line-too-long # noqa: E501

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
