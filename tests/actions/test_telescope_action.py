"""Unit test TelescopeAction coordination logic works as expected."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class SimpleTestAction(TelescopeAction[bool]):
    """A test action that returns a boolean value."""

    def __init__(
        self,
        should_succeed: bool,
        mock_target: MagicMock = None,
        termination_condition: list[ExpectedEvent] = None,
    ) -> None:
        super().__init__()
        self.should_succeed = should_succeed
        self.mock_target = mock_target
        self.term_condition = termination_condition or []

    def _action(self) -> bool:
        if self.mock_target:
            self.mock_target()
        return self.should_succeed

    def termination_condition(self) -> list[ExpectedEvent]:
        return self.term_condition


class TestTelescopeAction:
    """Unit test TelescopeAction coordination logic works as expected.

    This set of unit tests checks that ``TelescopeAction`` works correctly
    in isolation, so essentially it checks that it coordinates correctly
    the execution of the action, the logging and the waiting for state
    changes (assuming that the state change waiter is correctly implemented).

    If one of those tests fail, it is likely that the action internal
    coordination logic is broken.

    **IMPORTANT NOTE**: This set of tests does not check the real interaction
    with the Tango devices, or with the real state change waiter.
    """

    @pytest.fixture
    def mock_logger(self):
        """A mock for the logger used by the action."""
        return MagicMock()

    @pytest.fixture
    def mock_state_change_waiter(self):
        """A mock for the state change waiter used by the action."""
        return MagicMock()

    @pytest.fixture
    def mock_action_target(self):
        """A mock for the target of the action."""
        return MagicMock()

    @staticmethod
    def create_action(
        should_succeed: bool = True,
        mock_target: MagicMock = None,
        mock_logger: MagicMock = None,
        mock_state_change_waiter: MagicMock = None,
    ) -> SimpleTestAction:
        """Create a test action with the given configuration.

        :param should_succeed: The return value of the action.
        :param mock_target: The mock target of the action.
        :param mock_logger: The mock logger of the action.
        :param mock_state_change_waiter: The mock state change waiter
            of the action.
        :return: A test action with the given configuration.
        """

        action = SimpleTestAction(should_succeed, mock_target=mock_target)
        action._logger = mock_logger  # pylint: disable=protected-access
        action._state_change_waiter = mock_state_change_waiter  # pylint: disable=protected-access disable=line-too-long # noqa: E501
        return action

    # --------------------------------------------------------------
    # Tests: configuration setters

    @staticmethod
    def test_set_termination_condition_timeout_changes_timeout():
        """The termination condition timeout can be set."""
        action = SimpleTestAction(True)
        action.set_termination_condition_timeout(45)
        assert_that(action.termination_condition_timeout).is_equal_to(45)

    @staticmethod
    def test_set_termination_condition_policy_changes_flag():
        """The termination condition policy can be set."""
        action = SimpleTestAction(True)

        action.set_termination_condition_policy(False)
        assert_that(action.wait_termination).is_false()

        action.set_termination_condition_policy(True)
        assert_that(action.wait_termination).is_true()

    @staticmethod
    def test_set_logging_policy():
        """The logging policy can be set."""
        action = SimpleTestAction(True)

        action.set_logging_policy(False)
        assert_that(action.do_logging).is_false()

        action.set_logging_policy(True)
        assert_that(action.do_logging).is_true()

    # --------------------------------------------------------------
    # Tests: execute method (default configuration)

    def test_execute_makes_the_action_run_and_return_result(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method makes the action run and return the result."""
        action = self.create_action(
            should_succeed=True,
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        result = action.execute()

        # the action target should have been called once
        mock_action_target.assert_called_once()

        # the result should be the return value of the action
        assert_that(result).described_as(
            "The result should be the return value of the action."
        ).is_true()

    def test_execute_logs_its_start_and_end(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method logs its start and end."""
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.execute()

        # get the calls to the logger
        calls = mock_logger.info.call_args_list

        assert_that(calls).described_as(
            "The logger should have been called twice."
        ).is_length(2)

        assert_that("|".join(calls[0].args)).described_as(
            "The call arguments should contain the class name "
            "and the string 'Starting action'."
        ).contains("SimpleTestAction", "Starting action")

        assert_that("|".join(calls[1].args)).described_as(
            "The call arguments should contain the class name "
            "and the string 'Action execution completed'."
        ).contains("SimpleTestAction", "Action execution completed")

    def test_execute_waits_correctly_for_termination_condition(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method waits correctly for the termination condition.

        The ``execute`` method does all the necessary coordination to
        make the action run and wait for the termination condition, including
        the subscription to the termination condition events and the
        waiting for them.
        """
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.set_termination_condition_timeout(2)

        action.execute()

        # the state change waiter should have been called once
        add_expected_state_changes_calls = (
            mock_state_change_waiter.add_expected_state_changes.call_args_list
        )

        assert_that(add_expected_state_changes_calls).described_as(
            "The state change waiter should have been called once."
        ).is_length(1)
        assert_that(add_expected_state_changes_calls[0].args[0]).described_as(
            "The state change waiter should have been called with the "
            "termination condition."
        ).is_equal_to(action.termination_condition())

        # the state change waiter should have been called once
        wait_all_calls = mock_state_change_waiter.wait_all.call_args_list

        assert_that(wait_all_calls).described_as(
            "The state change waiter should have been called once."
        ).is_length(1)
        assert_that(wait_all_calls[0].args[0]).described_as(
            "The state change waiter should have been called with the "
            "given termination condition timeout."
        ).is_equal_to(2)

    def test_execute_raises_timeout_error_when_wait_term_cond_fails(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method raises a TimeoutError when the term. cond. fails.

        The state change waiter raises a TimeoutError if the termination
        condition events do not occur within the timeout. The execute method
        should keep this exception and raise it.
        """
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.set_termination_condition_timeout(2)
        mock_state_change_waiter.wait_all.side_effect = TimeoutError

        with pytest.raises(TimeoutError):
            action.execute()

    # --------------------------------------------------------------
    # Tests: execute method (custom configuration)

    def test_execute_does_not_wait_for_termination_condition(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method does not wait for the termination condition.

        If the action is configured to not wait for the termination condition,
        the execute method should not wait for it.
        """
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.set_termination_condition_policy(False)

        action.execute()

        # the state change waiter should not have been called
        mock_state_change_waiter.add_expected_state_changes.assert_not_called()
        mock_state_change_waiter.wait_all.assert_not_called()

    def test_execute_does_not_log_if_logging_disabled(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method does not log if logging is disabled."""
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.set_logging_policy(False)

        action.execute()

        # the logger should not have been called
        mock_logger.info.assert_not_called()

    def test_execute_does_not_log_if_logging_disabled_when_term_cond_fails(
        self, mock_action_target, mock_logger, mock_state_change_waiter
    ):
        """The execute method does not log if logging is disabled."""
        action = self.create_action(
            mock_target=mock_action_target,
            mock_logger=mock_logger,
            mock_state_change_waiter=mock_state_change_waiter,
        )

        action.set_logging_policy(False)
        action.set_termination_condition_timeout(2)
        mock_state_change_waiter.wait_all.side_effect = TimeoutError

        with pytest.raises(TimeoutError):
            action.execute()

        # the logger should not have been called
        mock_logger.error.assert_not_called()
