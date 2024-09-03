"""Test TelescopeActionSequence class."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.actions.telescope_action_sequence import (
    TelescopeActionSequence,
)
from tests.actions.utils.mock_state_change_waiter import MockStateChangeWaiter


class SimpleAction(TelescopeAction[bool]):
    """A simple action for testing that does nothing."""

    def __init__(self, result: bool = False) -> None:
        super().__init__()
        self._result = result

    def _action(self):
        return self._result

    def termination_condition(self):
        return []


class TestTelescopeActionSequence:
    """Unit tests for the TelescopeActionSequence class."""

    action1 = None
    action2 = None

    @pytest.fixture(autouse=True)
    def init_sequence_steps_actions(self):
        """Create the two actions that will make the sequence."""
        self.action1 = SimpleAction()
        self.action1.telescope = MagicMock()
        # pylint: disable=protected-access
        self.action1._state_change_waiter = MockStateChangeWaiter()

        self.action2 = SimpleAction(True)
        self.action2.telescope = MagicMock()
        # pylint: disable=protected-access
        self.action2._state_change_waiter = MockStateChangeWaiter()

    def create_action_sequence(self) -> TelescopeActionSequence[bool]:
        """Create a sequence action with two steps.

        :return: The sequence action with two steps.
        """
        return TelescopeActionSequence[bool]([self.action1, self.action2])

    def test_initialization(self):
        """Initialization of sequence action with correct steps."""
        sequence_action = self.create_action_sequence()
        assert_that(sequence_action.steps).is_equal_to(
            [self.action1, self.action2]
        )

    def test_execute_sequence_in_right_order(self):
        """Execution of steps in correct order."""
        sequence_action = self.create_action_sequence()
        with patch.object(
            self.action1, "execute"
        ) as mock_action1, patch.object(
            self.action2, "execute"
        ) as mock_action2:
            sequence_action.execute()
            assert_that(mock_action1.call_count).is_equal_to(1)
            assert_that(mock_action2.call_count).is_equal_to(1)

        assert_that(sequence_action.execute()).described_as(
            "The actions should be executed in the right order "
            "(the second action result should be returned)."
        ).is_true()

    def test_execute_returns_the_last_step_result(self):
        """Execution of sequence returns the result of the last step."""
        sequence_action = self.create_action_sequence()
        result = sequence_action.execute()
        assert_that(result).described_as(
            "The result of the last step should be returned."
        ).is_true()

    def test_termination_condition_is_empty(self):
        """A termination condition of a sequence should be empty."""
        sequence_action = self.create_action_sequence()
        assert_that(sequence_action.termination_condition()).is_equal_to([])

    def test_set_termination_condition_timeout_propagate_to_steps(self):
        """Setting termination condition timeout propagates to each step."""
        sequence_action = self.create_action_sequence()

        timeout = 60
        sequence_action.set_termination_condition_timeout(timeout)
        assert_that(self.action1.termination_condition_timeout).is_equal_to(
            timeout
        )
        assert_that(self.action2.termination_condition_timeout).is_equal_to(
            timeout
        )

    def test_set_termination_condition_policy_propagate_to_steps(self):
        """Applying termination condition policy correctly to each step."""
        sequence_action = self.create_action_sequence()

        sequence_action.set_termination_condition_policy(True)
        assert_that(self.action1.wait_termination).is_true()
        assert_that(self.action2.wait_termination).is_true()

        sequence_action.set_termination_condition_policy(False)
        assert_that(self.action1.wait_termination).described_as(
            "The first action should always wait for termination."
        ).is_true()
        assert_that(self.action2.wait_termination).described_as(
            "The second action should not wait for termination"
            "after the policy is set to False."
        ).is_false()

    def test_set_logging_policy_propagate_to_steps(self):
        """Applying logging policy correctly to each step."""
        sequence_action = self.create_action_sequence()

        sequence_action.set_logging_policy(True)
        assert_that(self.action1.do_logging).is_true()
        assert_that(self.action2.do_logging).is_true()

        sequence_action.set_logging_policy(False)
        assert_that(self.action1.do_logging).is_false()
        assert_that(self.action2.do_logging).is_false()
