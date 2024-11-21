"""An action which is a command sent to TMC subarray."""

import abc

import tango
from ska_control_model import ResultCode

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class TelescopeCommandAction(TelescopeAction[tuple]):
    """An action that send a command to some telescope subsystem.

    Such an action:

    - has a target, which is a Tango device
    - can be a LRC (long running command) or not
    - returns as a tuple the command result

    If the command is a LRC, when you wait for this action to complete,
    by default the action will wait for the LRC to terminate. If you want
    to not do that, you can say that this action is not a LRC or just
    override the ``termination_condition`` method without calling the
    superclass method. You can extend the termination condition to wait
    more things by overriding the ``termination_condition`` method and
    including the result of the superclass method in your own returned list.

    NOTE: what is exactly the type of the return value of a command?
    From what I see, it may not be a tuple of ResultCode and str...
    """

    def __init__(
        self,
        target_device: tango.DeviceProxy,
        is_long_running_command: bool,
    ) -> None:
        super().__init__()
        self.target_device = target_device
        """The Tango device to which the command will be sent."""

        self.is_long_running_command = is_long_running_command
        """Whether the command is a long running command or not."""

    def termination_condition(self) -> list[ExpectedEvent]:
        """Wait for the LRC to terminate.

        If the command is a LRC, when you wait for this action to complete,
        by default the action will wait for the LRC to terminate. If you want
        to not do that, you can say that this action is not a LRC or just
        override the ``termination_condition`` method without calling the
        superclass method. You can extend the termination condition to wait
        more things by overriding the ``termination_condition`` method and
        including the result of the superclass method in your own
        returned list.

        :return: A list of ExpectedEvent objects to wait for.
        """
        if self.is_long_running_command:
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
    """An action which can be synchronised on quiescent or transient state.

    Some telescope commands can be synchronised both on a quiescent state
    (the final expected state) or on a transient state (the intermediate
    state). This class provides a way to specify two different termination
    conditions for the action and to choose which one to use at runtime
    by setting the ``synchronise_on_transient_state`` attribute.
    """

    def __init__(
        self,
        target_device: tango.DeviceProxy,
        is_long_running_command: bool,
    ) -> None:
        super().__init__(target_device, is_long_running_command)

        self.synchronise_on_transient_state = False
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
