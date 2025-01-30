"""Unit tests for the SUTActionSequence class."""

import time
from typing import SupportsFloat
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.core.actions.sequence import (
    SUTActionSequence,
)
from tests.core.actions.utils import (
    MockSUTAction,
    assert_action_logged_execution,
)


@pytest.mark.core
class TestSUTActionSequence:
    """Unit tests for the SUTActionSequence class.

    The tests:

    - Verify that the sequence initialises correctly
    - Verify the sequence steps are executed correctly according to the
      parameters passed to the execute method
    - Verify that the sequence logs messages during execution (or does not)
    """

    @staticmethod
    def test_sequence_initialise_correctly():
        """Verify that the sequence initialises correctly."""
        sequence = SUTActionSequence()

        assert_that(sequence.actions).is_empty()

    @staticmethod
    def test_execute_sequence_with_pre_and_post_conditions():
        """Execute sequence verifying preconditions and postconditions."""
        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute()

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_true()
        assert_that(action1.procedure_executed).is_true()
        assert_that(action1.postconditions_verified).is_true()

        assert_that(action2.setup_called).is_true()
        assert_that(action2.preconditions_verified).is_true()
        assert_that(action2.procedure_executed).is_true()
        assert_that(action2.postconditions_verified).is_true()

    @staticmethod
    def test_execute_sequence_without_preconditions():
        """Execute sequence without preconditions verification."""
        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute(verify_preconditions=False)

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_false()
        assert_that(action1.procedure_executed).is_true()
        assert_that(action1.postconditions_verified).is_true()

        assert_that(action2.setup_called).is_true()
        assert_that(action2.preconditions_verified).is_false()
        assert_that(action2.procedure_executed).is_true()
        assert_that(action2.postconditions_verified).is_true()

    @staticmethod
    def test_execute_sequence_without_postconditions():
        """Execute sequence without postconditions verification."""
        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute(verify_postconditions=False)

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_true()
        assert_that(action1.procedure_executed).is_true()
        assert_that(action1.postconditions_verified).is_false()

        assert_that(action2.setup_called).is_true()
        assert_that(action2.preconditions_verified).is_true()
        assert_that(action2.procedure_executed).is_true()
        assert_that(action2.postconditions_verified).is_false()

    @staticmethod
    def test_execute_sequence_with_failing_preconditions():
        """Execute sequence with failing preconditions."""
        action1 = MockSUTAction(fail_preconditions=True)
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)

        with pytest.raises(AssertionError, match="Preconditions failed"):
            sequence.execute()

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_false()
        assert_that(action1.procedure_executed).is_false()
        assert_that(action1.postconditions_verified).is_false()

        assert_that(action2.setup_called).is_false()
        assert_that(action2.preconditions_verified).is_false()
        assert_that(action2.procedure_executed).is_false()
        assert_that(action2.postconditions_verified).is_false()

    @staticmethod
    def test_execute_sequence_with_failing_procedure():
        """Execute sequence with failing procedure."""
        action1 = MockSUTAction(fail_procedure=True)
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)

        with pytest.raises(AssertionError, match="Procedure failed"):
            sequence.execute()

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_true()
        assert_that(action1.procedure_executed).is_false()
        assert_that(action1.postconditions_verified).is_false()

        assert_that(action2.setup_called).is_false()
        assert_that(action2.preconditions_verified).is_false()
        assert_that(action2.procedure_executed).is_false()
        assert_that(action2.postconditions_verified).is_false()

    @staticmethod
    def test_execute_sequence_with_failing_postconditions():
        """Execute sequence with failing postconditions."""
        action1 = MockSUTAction(fail_postconditions=True)
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)

        with pytest.raises(AssertionError, match="Postconditions failed"):
            sequence.execute()

        assert_that(action1.setup_called).is_true()
        assert_that(action1.preconditions_verified).is_true()
        assert_that(action1.procedure_executed).is_true()
        assert_that(action1.postconditions_verified).is_false()

        assert_that(action2.setup_called).is_false()
        assert_that(action2.preconditions_verified).is_false()
        assert_that(action2.procedure_executed).is_false()
        assert_that(action2.postconditions_verified).is_false()

    @staticmethod
    @patch(
        "ska_integration_test_harness.core"
        ".actions.sut_action.logging.getLogger"
    )
    def test_logging_during_sequence_execution(mock_get_logger):
        """Verify logging messages during sequence execution."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute()

        assert_that(mock_logger.info.call_count).described_as(
            "Nine log messages are expected: "
            "3 for the sequence object, 3 for the first action, "
            "and 3 for the second action"
        ).is_equal_to(9)
        assert_action_logged_execution(
            mock_logger,
            "MockSUTAction",
            "Mock a SUT action and track calls",
        )
        assert_action_logged_execution(
            mock_logger,
            "SUTActionSequence",
            "Sequence of actions: MockSUTAction, MockSUTAction",
        )

    @staticmethod
    def test_logging_can_be_disabled_for_sequence():
        """The logger can be disabled for the sequence."""
        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        assert_that(sequence.logger.disabled).is_false()

        sequence.set_logging(enable_logging=False)

        assert_that(sequence.logger.disabled).is_true()
        assert_that(action1.logger.disabled).is_true()
        assert_that(action2.logger.disabled).is_true()
        sequence.execute()
        assert_that(sequence.logger.disabled).is_true()
        assert_that(action1.logger.disabled).is_true()
        assert_that(action2.logger.disabled).is_true()

    @staticmethod
    def test_verify_postcond_receives_timeout_when_sequence_is_executed():
        """Verify that the postconditions method receives a timeout."""
        action1 = MockSUTAction()
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute(postconditions_timeout=10)

        assert_that(action1.last_timeout).is_close_to(10, 0.1)
        assert_that(action2.last_timeout).is_close_to(10, 0.1)

    @staticmethod
    def test_sequence_timeout_is_shared_between_actions():
        """Verify that the sequence timeout is shared between actions."""

        action1 = MockSUTAction()
        verify_postcond = action1.verify_postconditions

        def slow_verify_postconditions(timeout: SupportsFloat = 0):
            verify_postcond(timeout=timeout)
            time.sleep(0.5)

        action1.verify_postconditions = MagicMock(
            side_effect=slow_verify_postconditions
        )
        action2 = MockSUTAction()
        sequence = SUTActionSequence()
        sequence.add_actions(action1, action2)
        sequence.execute(postconditions_timeout=3)

        assert_that(action1.last_timeout).is_close_to(3, 0.1)
        assert_that(action2.last_timeout).is_close_to(2.5, 0.1)
