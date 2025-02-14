"""Extensions to manage subarray lifecycle and ObsState transitions.

This module contains a framework for managing SKA subarray and the
Observation State Machine (:py:class:`~ska_control_model.ObsState`).
The framework embeds domain knowledge about:

- Which subarray commands exist
- Which :py:class:`~ska_control_model.ObsState` are triggered by each command
- Which :py:class:`~ska_control_model.ObsState` are transient and which
  are quiescent (i.e., stable, that don't change automatically after a
  while)
- How to reset a subarray-based system to any
  :py:class:`~ska_control_model.ObsState`

Instead, this framework still lacks knowledge about which devices are
involved in the subarray lifecycle (which devices changes
:py:class:`~ska_control_model.ObsState` and which devices should be
the targets of which commands).

The main classes in this module are the following three:

1. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSystem`
   , which is an interface to a system based on the Subarray Observation
   State Machine. It required to be implemented by the user and is essentially
   needed to inform the framework about which Tango devices are involved in the
   subarray lifecycle (who receives the commands and who emits events on the
   ``obsState`` attribute).
2. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsFactory`
   , which is a factory class that build actions to run subarray commands
   and synchronise after on the transient and quiescent states.
3. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetter`
   , which is an orchestrator class that has the responsibility to move
   the system to a desired :py:class:`~ska_control_model.ObsState`, starting
   by almost any initial state. This class (and its subclasses) embeds the
   knowledge about how to "pilot" the system in the Observation State Machine
   and uses the factory to generate the command actions.

Further classes are used to define input, exceptions, etc.

Some global constants like
:py:data:`~ska_integration_test_harness.extensions.subarray.DEFAULT_SUBARRAY_ID`,
:py:data:`~ska_integration_test_harness.extensions.subarray.COMMANDS_STATES_MAP`
and :py:data:`~ska_integration_test_harness.extensions.subarray.STATE_CLASS_MAP`
are also defined in this module and can be used to customise the behaviour
of the framework.

TODO: link ObsStateSetter subclasses in a separate section
of the documentation.

"""  # pylint: disable=line-too-long # noqa: E501

from .commands_factory import (
    COMMANDS_STATES_MAP,
    ObsStateCommandDoesNotExist,
    ObsStateCommandHasNoTransition,
    ObsStateCommandsFactory,
)
from .setter import STATE_CLASS_MAP, ObsStateCommandsInput, ObsStateSetter
from .system import (
    DEFAULT_SUBARRAY_ID,
    ObsStateSubarrayDoesNotExist,
    ObsStateSystem,
)

__all__ = [
    "ObsStateSystem",
    "ObsStateSubarrayDoesNotExist",
    "DEFAULT_SUBARRAY_ID",
    "ObsStateCommandsFactory",
    "ObsStateCommandDoesNotExist",
    "ObsStateCommandHasNoTransition",
    "COMMANDS_STATES_MAP",
    "ObsStateSetter",
    "ObsStateCommandsInput",
    "STATE_CLASS_MAP",
]
