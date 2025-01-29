"""A framework for defining and executing actions in test cases.

This module provides base classes and implementations for defining and
executing operations in test cases against a (Tango-based)
system under test (SUT).

**What is an action?** In abstract terms, an action is any kind of
self-contained operation that can be executed on the SUT. We chose to define
an action class structure because we want to give a common interface to
anything that holds test logic and/or domain knowledge about how you
interact with the SUT. Concretely, an action can be something as simple as
sending a command to a device or setting an attribute, or it can be
something more complex like orchestrating a sequence of commands, operations,
or other actions.

In our framework, we expect an action to have the following structure:

- Expects some kind of preconditions to be met to be executed
- Performs some operations on the SUT (e.g., invoking a command, writing one
  or more attributes on devices, orchestrating a sequence of other actions)
- Verifies the effects of the operations on the SUT through a set of
  postconditions (and eventually synchronises with the SUT state)

**How are actions implemented in the ITH?** In the ITH framework, we choose to
define actions as a class hierarchy. The base class for all actions
is :py:class:`~ska_integration_test_harness.core.actions.SUTAction`.

This base class is essentially not much more than an empty shell that defines
a common interface for the action lifecycle and so it needs to be
extended to implement concretely the preconditions, the operations, and
the postconditions. You can directly extend it and implement the
steps from scratch or you can start from one of the provided subclasses.
Two important subclasses are:

- :py:class:`~ska_integration_test_harness.core.actions.TracerAction`: a
  subclass that essentially gives more structure to the way the preconditions
  and postconditions are defined. This class makes you define and set
  the preconditions and postconditions as a list of assertion
  objects (see :py:mod:`~ska_integration_test_harness.core.assertions`) and it
  uses a :py:class:`ska_tango_testing.integration.TangoEventTracer` to
  perform the verifications. This is a good choice if you want to have
  a declarative way to define many simple and repetitive pre and post
  conditions.

- :py:class:`~ska_integration_test_harness.core.actions.TangoCommandAction`:
  a subclass that provides a ready-to-use implementation for actions whose
  procedure is a simple Tango command invocation. It is a subclass of
  :py:class:`~ska_integration_test_harness.core.actions.TracerAction` so it
  inherits the structure for defining preconditions and postconditions. It
  is useful as a simple and quick way to send commands and verify their
  effects on the SUT.

Further, more complex action implementations are provided in
:py:mod:`~ska_integration_test_harness.extensions.actions`. We suggest you
look at that module before implementing your own actions and assertions
from scratch.
"""

from .command_action import TangoCommandAction
from .sut_action import SUTAction
from .tracer_action import TracerAction

__all__ = ["SUTAction", "TracerAction", "TangoCommandAction"]
