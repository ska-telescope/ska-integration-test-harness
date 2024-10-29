"""An action which is a command sent to TMC subarray."""

import abc

from ska_control_model import ResultCode

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class TelescopeCommandAction(TelescopeAction[tuple[ResultCode, str]]):
    """An action that send a command to some telescope subsystem.

    It is expected to return the tuple of result code and message.
    """


class TransientQuiescentCommandAction(TelescopeCommandAction):
    """An action which can be synchronised on quiescent or transient state.

    Some telescope commands can be synchronised both on a quiescent state
    (the final expected state) or on a transient state (the intermediate
    state). This class provides a way to specify two different termination
    conditions for the action and to choose which one to use at runtime
    by setting the ``synchronise_on_transient_state`` attribute.
    """

    def __init__(self):
        super().__init__()

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
        synchronise on the next transient state.

        :return: A list of ExpectedEvent objects to wait for.
        """
        if self.synchronise_on_transient_state:
            return self.termination_condition_for_transient_state()
        return self.termination_condition_for_quiescent_state()

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
