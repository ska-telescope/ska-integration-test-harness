"""Unit test TelescopeAction coordination logic works as expected."""

from unittest.mock import MagicMock, call, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
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


class MockStateChangeWaiter:
    """A mock state change waiter for testing purposes."""

    def __init__(self):
        """Initialize the state change waiter."""
        self.expected_state_changes = []

    def reset(self):
        """Reset the state change waiter."""
        self.expected_state_changes = []

    def add_expected_state_changes(self, state_changes):
        """Add expected state changes to the waiter."""
        self.expected_state_changes.extend(state_changes)

    def wait_all(self, timeout):
        """Wait for all expected state changes to occur."""
        # In a real scenario, this would wait for state changes


class SimpleAction(TelescopeAction[bool]):
    """A simple action that does nothing but log."""

    def _action(self) -> bool:
        self._log("Executing simple action")
        return True

    def termination_condition(self) -> list[ExpectedEvent]:
        return []


class TestTelescopeAction:
    """Unit tests for TelescopeAction class."""

    def __init__(self) -> None:
        super().__init__()
        self.action = None

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up a simple action for testing."""
        self.action = SimpleAction()
        self.action.telescope = MockTelescopeWrapper()
        self.action._state_change_waiter = (  # pylint: disable=protected-access disable=line-too-long # noqa E501
            MockStateChangeWaiter()
        )

    def test_execute_logs_itself_and_executes_action(self):
        """Execute should log the action and execute it.

        Given an action that does nothing but log, when the action is executed,

        - the action infrastructure should log the start of the action,
        - the action should log its own execution, and
        - the action infrastructure should log the end of the action.
        """

        with patch.object(self.action, "_logger") as mock_logger:
            self.action.execute()
            assert_that(mock_logger.info.call_count).is_equal_to(
                3
            )  # Start, action, and end logs

            expected_calls = [
                call("%s: %s", "SimpleAction", "Starting action execution"),
                call("%s: %s", "SimpleAction", "Executing simple action"),
                call("%s: %s", "SimpleAction", "Action execution completed"),
            ]
            assert_that(mock_logger.info.call_args_list).is_equal_to(
                expected_calls
            )

            mock_logger.reset_mock()
            self.action.set_logging_policy(False)
            self.action.execute()
            assert_that(mock_logger.info.call_count).is_equal_to(0)

    def test_action_can_be_configured_timeout_term_condition_and_logging(self):
        """Action can be configured with timeout, term. cond., and log. policy.

        Given an action with default termination condition policy, timeout,
        and logging policy, an action can be configured with a different
        set of these policies.
        """
        self.action.set_termination_condition_timeout(60)
        assert_that(self.action.termination_condition_timeout).is_equal_to(60)

        assert_that(self.action.wait_termination).described_as(
            "Default wait termination condition policy is True"
        ).is_true()
        self.action.set_termination_condition_policy(False)
        assert_that(self.action.wait_termination).is_false()

        assert_that(self.action.do_logging).described_as(
            "Default logging policy is True"
        ).is_true()
        self.action.set_logging_policy(False)
        assert_that(self.action.do_logging).is_false()

    def test_execute_raises_timeout_error_if_wait_all_fail(self):
        """Execute should raise TimeoutError if wait_all fails.

        When an action is executed and the state change waiter fails to wait
        for all expected termination conditions, a TimeoutError should
        be raised.
        """

        def mock_wait_all(timeout):
            raise TimeoutError("Simulated timeout")

        self.action._state_change_waiter.wait_all = mock_wait_all  # pylint: disable=protected-access disable=line-too-long # noqa E501
        with pytest.raises(TimeoutError):
            self.action.execute()

    def test_error_logging(self):
        """Error logs are generated when an exception is raised."""

        def mock_wait_all(timeout):
            """Simulate a timeout when waiting for state changes."""
            raise TimeoutError("Simulated timeout")

        self.action._state_change_waiter.wait_all = mock_wait_all  # pylint: disable=protected-access disable=line-too-long # noqa E501
        with patch.object(self.action, "_logger") as mock_logger:
            with pytest.raises(TimeoutError):
                self.action.execute()

            assert_that(mock_logger.error.call_count).is_equal_to(1)

    def test_multiple_executions(self):
        """A action can be executed multiple times."""
        for _ in range(3):
            result = self.action.execute()
            assert_that(result).is_true()

    def test_termination_condition(self):
        """The term. condition is passed correctly to the events waiter."""

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
