"""Unit tests for the SUTAction class."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.core.actions.sut_action import SUTAction


class MockSUTAction(SUTAction):
    """Mock subclass of SUTAction for testing purposes."""

    def __init__(
        self,
        fail_preconditions=False,
        fail_procedure=False,
        fail_postconditions=False,
    ):
        """Initialise the mock action.

        :param fail_preconditions: Flag to indicate if preconditions
            should fail
        :param fail_procedure: Flag to indicate if the procedure should fail
        :param fail_postconditions: Flag to indicate if postconditions
            should fail
        """
        super().__init__()
        self.fail_preconditions = fail_preconditions
        self.fail_procedure = fail_procedure
        self.fail_postconditions = fail_postconditions
        self.setup_called = False
        self.preconditions_verified = False
        self.procedure_executed = False
        self.postconditions_verified = False

    def setup(self) -> None:
        self.setup_called = True

    def verify_preconditions(self) -> None:
        if self.fail_preconditions:
            raise AssertionError("Preconditions failed")
        self.preconditions_verified = True

    def execute_procedure(self) -> None:
        if self.fail_procedure:
            raise AssertionError("Procedure failed")
        self.procedure_executed = True

    def verify_postconditions(self) -> None:
        if self.fail_postconditions:
            raise AssertionError("Postconditions failed")
        self.postconditions_verified = True

    def name(self) -> str:
        return "MockSUTAction"

    def description(self) -> str:
        return "Mock a SUT action and track calls"


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
        mock_logger.info.assert_any_call(
            "Executing action %s: %s "
            "(verify_preconditions=%s, verify_postconditions=%s)",
            "MockSUTAction",
            "Mock a SUT action and track calls",
            True,
            True,
        )
        mock_logger.info.assert_any_call(
            "Action %s: procedure executed successfully. "
            "Verifying postconditions...",
            "MockSUTAction",
        )
        mock_logger.info.assert_any_call(
            "Action %s: execution completed successfully",
            "MockSUTAction",
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
