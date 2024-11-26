"""An action which is a command sent to TMC subarray."""

import abc
from typing import Any

import tango
from ska_control_model import ResultCode

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class TelescopeCommandAction(TelescopeAction[tuple[Any, list[str]]]):
    """An action that send a command to some telescope subsystem.

    Such an action:

    - may have a target encoded in the action, which can be a Tango device
    - may be a LRC (long running command) or not
    - returns as a tuple the command result

    If the command is a LRC (and a target device is provided),
    by default the action will wait for the LRC to terminate. If you want
    to extend the termination condition to wait for more things or
    not to wait for the LRC to terminate, you can override the
    ``termination_condition`` method (and include or not the result of the
    superclass method in your own returned list). Actually, just changing
    the ``is_long_running_command`` attribute to ``False`` you can avoid
    waiting for the LRC to terminate.

    The result of the command is a tuple with two elements:

    - the first element is the result of the command (e.g., ResultCode.OK)
    - the second element is one or more messages about the command execution.

    If the command is a LRC, the second element can be used as a reference
    to check the command status through the longRunningCommandResult
    attribute. In fact, the waiting condition for the LRC termination
    is based on this attribute.

    **IMPORTANT NOTE**: at the moment, the command itself is not part of this
    action. This is because I don't yet want to interfere with the way
    you call it (e.g., with the command name, the command input, etc.).
    This may be subject to change in the future, but for now, you have to
    implement the command execution in the ``_action`` method
    as you would do in a normal action.
    """

    # TODO: I know that more generalisation is possible here (e.g.,
    # adding a command name, a command input and a default _action method
    # that calls the command on the target device), but this will be
    # object of a future MR. For now, I don't want too impactful changes.

    def __init__(
        self,
        target_device: "tango.DeviceProxy | None" = None,
        is_long_running_command: bool = False,
    ) -> None:
        """Set a few (optional) attributes of the action.

        Attributes are optional so you can set them later if you want.

        :param target_device: The Tango device to which the command
            will be sent.
        :param is_long_running_command: Whether the command is a long
            running command or not.

        See the class documentation for more details.
        """
        super().__init__()
        self.target_device = target_device
        """The Tango device to which the command will be sent."""

        self.is_long_running_command = is_long_running_command
        """Whether the command is a long running command or not."""

    def termination_condition(self) -> list[ExpectedEvent]:
        """Wait for the LRC to terminate.

        If the command is a LRC (and a target device is provided),
        by default the action will wait for the LRC to terminate. If you want
        to extend the termination condition to wait for more things or
        not to wait for the LRC to terminate, you can override the
        ``termination_condition`` method (and include or not the result of the
        superclass method in your own returned list).

        :return: A list of ExpectedEvent objects to wait for (which is empty
            by default, or includes the termination condition for the LRC if
            the command is marked as a LRC).
        """
        if self.is_long_running_command and self.target_device:
            return self.termination_condition_for_lrc()

        return []

    def termination_condition_for_lrc(self) -> list[ExpectedEvent]:
        """Wait for the LRC to terminate.

        Implement this method to specify the termination condition for
        when the command is a long running command.

        :return: A list of ExpectedEvent objects to wait for, when
            the command is a long running command.
        """

        return [
            ExpectedEvent(
                device=self.target_device,
                attribute="longRunningCommandResult",
                predicate=lambda e: e.attribute_value
                == (
                    self.get_last_execution_result()[1][0],
                    f'[{ResultCode.OK.value}, "Command Completed"]',
                ),
            )
        ]


class TransientQuiescentCommandAction(TelescopeCommandAction):
    """A command which can synchronise on a quiescent or on a transient state.

    This class represents a command that when called can be synchronised
    on a quiescent state (the final expected state) or
    on a transient state (an intermediate state in the command execution).
    Concretely, this means that the action has two instead of one
    termination conditions: one for the quiescent state and one for the
    transient state. By default, the action will synchronise on the
    quiescent state. If you want to synchronise on the transient state,
    you can set the ``synchronise_on_transient_state`` attribute to True.

    This is a subclass of ``TelescopeCommandAction``, so it still inherits
    the fact of having a target device and being a LRC or not. If this action
    is set as a LRC, when you synchronise on the quiescent state, the action
    termination condition by default will include the LRC termination
    condition.
    """

    def __init__(
        self,
        target_device: "tango.DeviceProxy | None" = None,
        is_long_running_command: bool = False,
        synchronise_on_transient_state: bool = False,
    ) -> None:
        """Init the action with a few (optional) attributes.

        The attributes are optional so you can set them later if you want.

        :param target_device: The Tango device to which the command
            will be sent.
        :param is_long_running_command: Whether the command is a long
            running command or not.
        :param synchronise_on_transient_state: If True, the action will
            synchronise on the next transient state instead of the next
            quiescent state. By default, it is False, so the action will
            synchronise on the next quiescent state.

        See the class documentation for more details.
        """
        super().__init__(target_device, is_long_running_command)

        self.synchronise_on_transient_state = synchronise_on_transient_state
        """If True, the action will synchronise on the next transient state
        instead of the next quiescent state. By default, it is False, so
        the action will synchronise on the next quiescent state.
        """

    def set_synchronise_on_transient_state(self, value: bool):
        """Set the synchronise_on_transient_state attribute.

        :param value: If True, the action will synchronise on the next
            transient state instead of the next quiescent state.
            By default, it is False, so the action will synchronise
            on the next quiescent state.
        """
        self.synchronise_on_transient_state = value

    def termination_condition(self) -> list[ExpectedEvent]:
        """Wait for the quiescent or transient state of the subarray.

        By default, the action will synchronise on the next quiescent state,
        but if the synchronise_on_transient_state attribute is True, it will
        synchronise on the next transient state. Eventual inherited termination
        conditions are also include when synchronising on the quiescent state.

        :return: A list of ExpectedEvent objects to wait for.
        """
        if self.synchronise_on_transient_state:
            return self.termination_condition_for_transient_state()

        return (
            super().termination_condition()
            + self.termination_condition_for_quiescent_state()
        )

    @abc.abstractmethod
    def termination_condition_for_transient_state(self) -> list[ExpectedEvent]:
        """Wait for the transient state of the subarray.

        Implement this method to specify the termination condition for
        when you want to synchronise on the transient state.

        :return: A list of ExpectedEvent objects to wait for, when
            you want to synchronise on the transient state.
        """

    @abc.abstractmethod
    def termination_condition_for_quiescent_state(self) -> list[ExpectedEvent]:
        """Wait for the quiescent state of the subarray.

        Implement this method to specify the termination condition for
        when you want to synchronise on the quiescent state.

        :return: A list of ExpectedEvent objects to wait for, when
            you want to synchronise on the quiescent state.
        """
