"""Extensions to manage subarray lifecycle and ObsState transitions.

This module contains a framework for managing SKA subarray and the
Observation State Machine (:py:class:`~ska_control_model.ObsState`).
The framework embeds domain knowledge about:

- Which subarray commands exist
- Which :py:class:`~ska_control_model.ObsState` are triggered by each command
- Which :py:class:`~ska_control_model.ObsState` are transient and which
  are quiescent (i.e., stable, that don't change automatically after a while)
- How to reset a subarray-based system to any
  :py:class:`~ska_control_model.ObsState`

Instead, this framework still lacks knowledge about which devices are
involved in the subarray lifecycle (which devices changes
:py:class:`~ska_control_model.ObsState` and which devices should be
the targets of which commands).

**Main Classes**

The main classes in this module are the following three:

1. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSystem`
   , which is an interface to a system based on the Subarray Observation
   State Machine. It required to be implemented by the user and is essentially
   needed to inform the framework about which Tango devices are involved in the
   subarray lifecycle (who receives the commands and who emits events on the
   ``obsState`` attribute).
2. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsFactory`
   , which is a factory class that build actions to run subarray commands
   and synchronise after on the transient and quiescent states. You can use
   it if you want to run subarray commands in your tests and you want them
   already synchronised with the system state.
3. :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetter`
   , which is an orchestrator class that has the responsibility to move
   the system to a desired :py:class:`~ska_control_model.ObsState`, starting
   by almost any initial state.

**Other Classes**

Further important classes and functions are:

- :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`,
  which represents a single step in the process of moving the system to a
  desired :py:class:`~ska_control_model.ObsState` (see
  :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetter`
  ). Each state the system can be in has a corresponding step class,
  which contains the code to move (indeed) `one step` in the direction
  of the desired target state.

  Submodule :py:mod:`ska_integration_test_harness.extensions.subarray.steps`
  contains the step classes implementations used by default in the framework.
  If you need, you can extend or replace them
  with your own implementations and then
  inject them in the framework (see
  :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetter`
  ).

- :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsInput`
  is a dataclass that represents the input for subarray Tango commands used by
  :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetter`
  and
  :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsSetterStep`
  to set the system in a desired :py:class:`~ska_control_model.ObsState`.

- :py:func:`~ska_integration_test_harness.extensions.subarray.read_obs_state`,
  :py:func:`~ska_integration_test_harness.extensions.subarray.read_sys_obs_state`,
  :py:func:`~ska_integration_test_harness.extensions.subarray.read_devices_obs_state`
  are utility functions to read the current :py:class:`~ska_control_model.ObsState`
  from the system or any device.

- In module
  :py:mod:`ska_integration_test_harness.extensions.subarray.exceptions`
  you can find the exceptions used in the framework.

**Global Constants**

A ``DEFAULT_SUBARRAY_ID`` global constant is used to define the subarray ID
that is used by default in the framework if you don't specify one in classes
creations, method calls, etc. It is set to 1, but you can change it.

"""  # pylint: disable=line-too-long # noqa: E501

from .commands_factory import COMMANDS_STATES_MAP, ObsStateCommandsFactory
from .inputs import ObsStateCommandsInput
from .setter import ObsStateSetter
from .setter_step import ObsStateSetterStep
from .system import (
    DEFAULT_SUBARRAY_ID,
    ObsStateSystem,
    read_devices_obs_state,
    read_obs_state,
    read_sys_obs_state,
)

__all__ = [
    "ObsStateSystem",
    "DEFAULT_SUBARRAY_ID",
    "ObsStateCommandsFactory",
    "COMMANDS_STATES_MAP",
    "ObsStateSetter",
    "ObsStateCommandsInput",
    "read_devices_obs_state",
    "read_obs_state",
    "read_sys_obs_state",
    "ObsStateSetterStep",
]
