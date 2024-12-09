"""Unit tests for TelescopeCommandAction class and its subclasses."""

from unittest.mock import MagicMock

from assertpy import assert_that
from ska_control_model import ResultCode
from ska_tango_testing.integration.event import ReceivedEvent

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)


class DummyTelescopeCommandAction(TelescopeCommandAction):
    """A dummy subclass to test TelescopeCommandAction behaviour."""

    def _action(self):
        """A dummy action that does nothing."""


class TestTelescopeCommandAction:
    """Unit tests for the TelescopeCommandAction class."""

    @staticmethod
    def test_termination_condition_returns_empty_for_non_lrc():
        """Termination condition should return empty for non-LRC."""
        action = DummyTelescopeCommandAction()
        action.is_long_running_command = False
        action.target_device = None

        termination_conditions = action.termination_condition()

        assert_that(termination_conditions).described_as(
            "Termination conditions for non-LRC commands should be empty."
        ).is_empty()

    @staticmethod
    def test_termination_condition_for_lrc_with_valid_target_device():
        """Termination condition should include expected events for LRC."""
        # Create a mock Tango device
        mock_device = MagicMock()
        mock_device.name = "MockDevice"

        # Create the action
        action = DummyTelescopeCommandAction(target_device=mock_device)
        action.is_long_running_command = True

        # Simulate last execution result
        action.get_last_execution_result = MagicMock(
            return_value=("CommandResult", ["ExpectedCommandResultName"])
        )
        termination_conditions = action.termination_condition()

        # Validate the termination condition event
        assert_that(termination_conditions).is_not_empty()
        assert_that(termination_conditions[0].device).is_equal_to(mock_device)
        assert_that(termination_conditions[0].attribute).is_equal_to(
            "longRunningCommandResult"
        )

        # Simulate a ReceivedEvent and validate the predicate
        received_event = ReceivedEvent(
            event_data=MagicMock(
                device=mock_device,  # Same device as the target device
                attr_name="longRunningCommandResult",
                attr_value=MagicMock(
                    value=(
                        "ExpectedCommandResultName",
                        f'[{ResultCode.OK.value}, "Command Completed"]',
                    )
                ),
            )
        )

        assert_that(
            termination_conditions[0].predicate(received_event)
        ).described_as(
            "Predicate should match the ReceivedEvent correctly."
        ).is_true()

    @staticmethod
    def test_termination_condition_without_target_device_returns_empty():
        """Termination condition should return empty if target is not set."""
        action = DummyTelescopeCommandAction()
        action.is_long_running_command = True
        action.target_device = None

        termination_conditions = action.termination_condition()

        assert_that(termination_conditions).described_as(
            "Termination conditions should be empty "
            "if no target device is set."
        ).is_empty()

    @staticmethod
    def test_termination_condition_handles_mismatched_event():
        """Termination condition should reject mismatched ReceivedEvent.

        We try tricking it by simulating a competition from another event.
        """
        # Create a mock Tango device
        mock_device = MagicMock()
        mock_device.name = "MockDevice"

        # Create the action
        action = DummyTelescopeCommandAction(target_device=mock_device)
        action.is_long_running_command = True

        # Simulate last execution result
        action.get_last_execution_result = MagicMock(
            return_value=("CommandResult", ["ExpectedCommandResultName"])
        )

        termination_conditions = action.termination_condition()

        # Simulate a mismatched ReceivedEvent
        received_event = ReceivedEvent(
            event_data=MagicMock(
                device=mock_device,  # Same device as the target device
                attr_name="longRunningCommandResult",
                # different command reference than the expected one
                attr_value=MagicMock(
                    value=(
                        "MismatchedResult",
                        f'[{ResultCode.OK.value}, "Command Completed"]',
                    )
                ),
            )
        )

        assert_that(
            termination_conditions[0].predicate(received_event)
        ).described_as(
            "Predicate should not match a mismatched ReceivedEvent."
        ).is_false()

    @staticmethod
    def test_termination_condition_handles_different_result_code():
        """Termination condition should reject mismatched ResultCode.

        We check what happens when the ResultCode is not the expected one.
        """
        # Create a mock Tango device
        mock_device = MagicMock()
        mock_device.name = "MockDevice"

        # Create the action
        action = DummyTelescopeCommandAction(target_device=mock_device)
        action.is_long_running_command = True

        # Simulate last execution result
        action.get_last_execution_result = MagicMock(
            return_value=("CommandResult", ["ExpectedCommandResultName"])
        )

        termination_conditions = action.termination_condition()

        # Simulate a mismatched ReceivedEvent
        received_event = ReceivedEvent(
            event_data=MagicMock(
                device=mock_device,  # Same device as the target device
                attr_name="longRunningCommandResult",
                # different result code than the expected one
                attr_value=MagicMock(
                    value=(
                        "ExpectedCommandResultName",
                        f'[{ResultCode.REJECTED.value}, "Command Rejected"]',
                    )
                ),
            )
        )

        assert_that(
            termination_conditions[0].predicate(received_event)
        ).described_as(
            "Predicate should not match an event with a different ResultCode."
        ).is_false()


class DummyTransientQuiescentCommand(TransientQuiescentCommandAction):
    """A dummy TransientQuiescentCommandAction subclass for testing purposes.

    It simply returns two different termination conditions
    for the transient and quiescent states.
    """

    def _action(self):
        """A dummy action that does nothing."""

    def termination_condition_for_transient_state(self):
        """Return a dummy termination condition for the transient state."""
        return [
            ExpectedStateChange(
                device="dummy_device",
                attribute="dummy_attribute",
                expected_value="TRANSIENT_STATE",
            )
        ]

    def termination_condition_for_quiescent_state(self):
        """Return a dummy termination condition for the quiescent state."""
        return [
            ExpectedStateChange(
                device="dummy_device",
                attribute="dummy_attribute",
                expected_value="QUIESCENT_STATE",
            )
        ]


class TestTransientQuiescentCommandAction:
    """Unit tests for TransientQuiescentCommandAction class."""

    @staticmethod
    def test_termination_condition_by_default_returns_quiescent_state():
        """The termination condition returns the quiescent state by default."""
        action = DummyTransientQuiescentCommand()

        assert_that(action.synchronise_on_transient_state).described_as(
            "By default, synchronise_on_transient_state should be False"
        ).is_false()

        assert_that(action.termination_condition()).is_length(1)
        assert_that(action.termination_condition()[0].expected_value).contains(
            "QUIESCENT_STATE"
        )

    @staticmethod
    def test_termination_condition_when_set_returns_transient_state():
        """The termination condition returns the transient state when set."""
        action = DummyTransientQuiescentCommand()
        action.set_synchronise_on_transient_state(True)

        assert_that(action.synchronise_on_transient_state).described_as(
            "synchronise_on_transient_state should be set to True"
        ).is_true()

        assert_that(action.termination_condition()).is_length(1)
        assert_that(action.termination_condition()[0].expected_value).contains(
            "TRANSIENT_STATE"
        )
