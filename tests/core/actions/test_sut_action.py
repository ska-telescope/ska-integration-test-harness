"""Unit tests for the SUTAction class."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from .utils import MockSUTAction, assert_action_logged_execution


@pytest.mark.core
class TestSUTAction:
    """Unit tests for the SUTAction class.

    The tests:

    - Verify that the action initialises correctly
    - Verify the action steps are executed correctly according to the
      parameters passed to the execute method
    - Verify that the action logs messages during execution (or does not)
    """

    @staticmethod
    def test_action_initialise_correctly():
        """Verify that the action initialises correctly."""
        action = MockSUTAction()

        assert_that(action.setup_called).is_false()
        assert_that(action.preconditions_verified).is_false()
        assert_that(action.procedure_executed).is_false()
        assert_that(action.postconditions_verified).is_false()

    @staticmethod
    def test_execute_with_pre_and_post_conditions():
        """Execute action verifying preconditions and postconditions."""
        action = MockSUTAction()
        action.execute()

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_true()
        assert_that(action.procedure_executed).is_true()
        assert_that(action.postconditions_verified).is_true()

    @staticmethod
    def test_execute_without_preconditions():
        """Execute action without preconditions verification."""
        action = MockSUTAction()
        action.execute(verify_preconditions=False)

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_false()
        assert_that(action.procedure_executed).is_true()
        assert_that(action.postconditions_verified).is_true()

    @staticmethod
    def test_execute_without_postconditions():
        """Execute action without postconditions verification."""
        action = MockSUTAction()
        action.execute(verify_postconditions=False)

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_true()
        assert_that(action.procedure_executed).is_true()
        assert_that(action.postconditions_verified).is_false()

    @staticmethod
    def test_execute_with_failing_preconditions():
        """Execute action with failing preconditions."""
        action = MockSUTAction(fail_preconditions=True)
        with pytest.raises(AssertionError, match="Preconditions failed"):
            action.execute()

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_false()
        assert_that(action.procedure_executed).is_false()
        assert_that(action.postconditions_verified).is_false()

    @staticmethod
    def test_execute_with_failing_procedure():
        """Execute action with failing procedure."""
        action = MockSUTAction(fail_procedure=True)
        with pytest.raises(AssertionError, match="Procedure failed"):
            action.execute()

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_true()
        assert_that(action.procedure_executed).is_false()
        assert_that(action.postconditions_verified).is_false()

    @staticmethod
    def test_execute_with_failing_postconditions():
        """Execute action with failing postconditions."""
        action = MockSUTAction(fail_postconditions=True)
        with pytest.raises(AssertionError, match="Postconditions failed"):
            action.execute()

        assert_that(action.setup_called).is_true()
        assert_that(action.preconditions_verified).is_true()
        assert_that(action.procedure_executed).is_true()
        assert_that(action.postconditions_verified).is_false()

    @staticmethod
    @patch(
        "ska_integration_test_harness.core"
        ".actions.sut_action.logging.getLogger"
    )
    def test_logging_during_execution(mock_get_logger):
        """Verify logging messages during action execution."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        action = MockSUTAction()
        action.execute()

        assert_that(mock_logger.info.call_count).is_equal_to(3)
        assert_action_logged_execution(
            mock_logger,
            "MockSUTAction",
            "Mock a SUT action and track calls",
        )

    @staticmethod
    def test_logging_can_be_disabled():
        """The logger can be disabled for the action."""
        action = MockSUTAction()
        assert_that(action.logger.disabled).is_false()

        action.set_logging(enable_logging=False)

        assert_that(action.logger.disabled).is_true()
        action.execute()
        assert_that(action.logger.disabled).is_true()

    @staticmethod
    def test_verify_postcond_receives_timeout_when_action_is_executed():
        """Verify that the postconditions method receives a timeout."""
        action = MockSUTAction()
        action.execute(postconditions_timeout=10)

        assert_that(action.last_timeout).is_equal_to(10)
