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

TODO: classes overview

"""

from .obs_state_commands_factory import (
    COMMANDS_STATES_MAP,
    ObsStateCommandDoesNotExist,
    ObsStateCommandHasNoTransition,
    ObsStateCommandsFactory,
)
from .obs_state_setter import ObsStateCommandsInput, ObsStateSetter
from .obs_state_system import (
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
]
