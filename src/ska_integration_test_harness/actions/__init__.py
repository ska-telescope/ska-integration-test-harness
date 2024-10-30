"""A structure for performing actions on the telescope system.

This module contains the structure for implementing actions on the telescope.
An action is essentially an abstraction of a procedure that can be executed
on the telescope system and - essentially - it is made by a business logic
and a termination condition to synchronise the execution. Actions then can be
represented through a hierarchy of classes, which have as a root the
:class:`~ska_integration_test_harness.actions.telescope_action.TelescopeAction`.

The main mechanism is the one provided by the
:class:`ska_tango_testing.integration.tracer.TangoEventTracer` that allows
the implementation of a
:class:`~ska_integration_test_harness.actions.state_change_waiter.StateChangeWaiter`
to wait for a specific state change in the system and so to synchronise
after an action is executed.

Further details in the classes documentation.
"""  # pylint: disable=line-too-long # noqa: E501

from .command_action import (
    TelescopeCommandAction,
    TransientQuiescentCommandAction,
)
from .state_change_waiter import StateChangeWaiter
from .telescope_action import TelescopeAction
from .telescope_action_sequence import TelescopeActionSequence

__all__ = [
    "TelescopeAction",
    "TelescopeActionSequence",
    "TelescopeCommandAction",
    "TransientQuiescentCommandAction",
    "StateChangeWaiter",
]
