"""Unit test TelescopeAction coordination logic works as expected."""

from unittest.mock import MagicMock, call, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from tests.actions.test_telescope_action_sequence import MockStateChangeWaiter
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock

# Mock classes to avoid using actual Tango Controls API


class MockTelescopeWrapper:
    """A mock telescope wrapper for testing purposes."""

    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.tmc = MagicMock()
        self.tmc.central_node = create_device_proxy_mock(
            device_name="central_node",
            attribute_name="State",
            attribute_value="OFF",
        )
        self.actions_default_timeout = 100


class SimpleAction(TelescopeAction[bool]):
    """A simple action that does nothing but log."""

    def _action(self) -> bool:
        self._log("Executing simple action")
        return True

    def termination_condition(self) -> list[ExpectedEvent]:
        return []


class TestTelescopeAction:
    """Unit tests for TelescopeAction class.

    IMPORTANT: it requires a fixture that ensures the telescope wrapper is
    not yet defined. This is to avoid the singleton pattern to interfere
    with the tests. The fixture is defined in the conftest.py file.
    """

    @staticmethod
    def create_simple_action() -> SimpleAction:
        """Create a simple action for testing."""
        with patch(
            "ska_integration_test_harness.actions.telescope_action"
            ".TelescopeWrapper",
            return_value=MockTelescopeWrapper(),
        ):
            action = SimpleAction()

        # pylint: disable=protected-access
        action._state_change_waiter = MockStateChangeWaiter()
        return action

    def test_execute_logs_itself_and_executes_action(self):
        """Execute should log the action and execute it.

        Given an action that does nothing but log, when the action is executed,

        - the action infrastructure should log the start of the action,
        - the action should log its own execution, and
        - the action infrastructure should log the end of the action.
        """
        action = self.create_simple_action()

        with patch.object(action, "_logger") as mock_logger:
            action.execute()

        assert_that(mock_logger.info.call_count).described_as(
            "We expect 3 log messages: "
            "action start, action execution, action end"
        ).is_equal_to(3)
        expected_calls = [
            call(
                "%s: %s",
                "SimpleAction",
                "Starting action execution "
                "(wait_termination=True, timeout=100)",
            ),
            call("%s: %s", "SimpleAction", "Executing simple action"),
            call("%s: %s", "SimpleAction", "Action execution completed"),
        ]
        assert_that(mock_logger.info.call_args_list).described_as(
            "The log messages should be in the expected order"
        ).is_equal_to(expected_calls)

    def test_execute_with_no_logging(self):
        """Execute should not log if logging is disabled.

        Given an action that does nothing but log, when the action is executed
        with logging disabled, the action infrastructure should not log the
        start of the action, the action should not log its own execution, and
        the action infrastructure should not log the end of the action.
        """
        action = self.create_simple_action()
        action.set_logging_policy(False)

        with patch.object(action, "_logger") as mock_logger:
            action.execute()

        assert_that(mock_logger.info.call_count).is_equal_to(0)

    def test_execute_logs_no_wait_termination(self):
        """Execute should log no wait termination when policy is False.

        Given an action that does nothing but log, when the action is executed
        with wait_termination set to False, the action infrastructure should
        log that wait termination is disabled.
        """
        action = self.create_simple_action()
        action.set_termination_condition_policy(False)

        with patch.object(action, "_logger") as mock_logger:
            action.execute()

        assert_that(mock_logger.info.call_args_list).contains(
            call(
                "%s: %s",
                "SimpleAction",
                "Starting action execution (wait_termination=False)",
            ),
        )

    def test_action_can_be_configured_timeout_term_condition_and_logging(self):
        """Action can be configured with timeout, term. cond., and log. policy.

        Given an action with default termination condition policy, timeout,
        and logging policy, an action can be configured with a different
        set of these policies.
        """
        action = self.create_simple_action()

        action.set_termination_condition_timeout(60)
        assert_that(action.termination_condition_timeout).is_equal_to(60)

        assert_that(action.wait_termination).described_as(
            "Default wait termination condition policy is True"
        ).is_true()
        action.set_termination_condition_policy(False)
        assert_that(action.wait_termination).is_false()

        assert_that(action.do_logging).described_as(
            "Default logging policy is True"
        ).is_true()
        action.set_logging_policy(False)
        assert_that(action.do_logging).is_false()

    def test_execute_raises_timeout_error_if_wait_all_fail(self):
        """Execute should raise TimeoutError if wait_all fails.

        When an action is executed and the state change waiter fails to wait
        for all expected termination conditions, a TimeoutError should
        be raised.
        """
        action = self.create_simple_action()

        def mock_wait_all(timeout):
            raise TimeoutError("Simulated timeout")

        action._state_change_waiter.wait_all = mock_wait_all  # pylint: disable=protected-access disable=line-too-long # noqa E501
        with pytest.raises(TimeoutError):
            action.execute()

    def test_error_logging(self):
        """Error logs are generated when an exception is raised."""
        action = self.create_simple_action()

        def mock_wait_all(timeout):
            """Simulate a timeout when waiting for state changes."""
            raise TimeoutError("Simulated timeout")

        action._state_change_waiter.wait_all = mock_wait_all  # pylint: disable=protected-access disable=line-too-long # noqa E501
        with patch.object(action, "_logger") as mock_logger:
            with pytest.raises(TimeoutError):
                action.execute()

            assert_that(mock_logger.error.call_count).is_equal_to(1)

    def test_multiple_executions(self):
        """A action can be executed multiple times."""
        action = self.create_simple_action()
        for _ in range(3):
            result = action.execute()
            assert_that(result).is_true()

    def test_termination_condition(self):
        """The term. condition is passed correctly to the events waiter."""
        action = self.create_simple_action()

        class ActionWithTermination(TelescopeAction[None]):
            """An action with a termination condition."""

            def _action(self) -> None:
                """Do nothing."""

            def termination_condition(self) -> list[ExpectedEvent]:
                """Expect an event."""
                return [
                    ExpectedEvent(
                        self.telescope.tmc.central_node,
                        "State",
                        lambda x: True,
                    )
                ]

        action = ActionWithTermination()
        action.telescope = MockTelescopeWrapper()
        # pylint: disable=protected-access
        action._state_change_waiter = MockStateChangeWaiter()

        with patch.object(
            action._state_change_waiter,  # pylint: disable=protected-access disable=line-too-long # noqa E501
            "add_expected_state_changes",
        ) as mock_add:
            action.execute()
            mock_add.assert_called_once()

            # there have been passed exactly one ExpectedEvent
            # and it's the one we expected
            args, _ = mock_add.call_args
            assert_that(args[0]).is_length(1)
            assert_that(args[0][0].device).is_equal_to(
                action.telescope.tmc.central_node
            )
            assert_that(args[0][0].attribute).is_equal_to("State")
            assert_that(args[0][0].predicate).is_instance_of(type(lambda x: x))
