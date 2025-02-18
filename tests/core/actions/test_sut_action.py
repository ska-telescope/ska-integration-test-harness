"""Unit tests for the SUTAction class."""

import time
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout

from .utils import MockSUTAction, assert_action_logged_execution


@pytest.mark.platform
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
        """Verify that the postconditions method receives a timeout.

        NOTE: the timeout value is close to 10 and not exactly 10 because the
        timeout internally is an object and it's started just before calling
        the first postcondition verification, so some milliseconds are lost.
        """
        action = MockSUTAction()
        action.execute(postconditions_timeout=10)

        assert_that(action.last_timeout_value).is_close_to(10, 0.1)

    @staticmethod
    def test_verify_postcond_timeout_is_a_object():
        """The timeout received by verify_postconditions is a object.

        The object:

        - is supposed to be a ska_tango_testing.integration.assertions.
          ChainedAssertionsTimeout instance
        - the timeout is supposed to be already started
        - the timeout is supposed to be started but after the execute_procedure
        """
        action = MockSUTAction()
        # inject a slow execute procedure to measure the fact that the timeout
        # is started after the execute_procedure
        execute_procedure = action.execute_procedure

        def slow_execute():
            time.sleep(0.5)
            execute_procedure()

        action.execute_procedure = slow_execute

        # execute the action passing a timeout object
        action.execute(postconditions_timeout=10)

        assert_that(action.last_timeout_object).described_as(
            "The timeout object is supposed to be a "
            "ChainedAssertionsTimeout instance"
        ).is_instance_of(ChainedAssertionsTimeout)
        timeout_object: ChainedAssertionsTimeout = action.last_timeout_object
        assert_that(timeout_object.is_started()).described_as(
            "The timeout object is supposed to be started"
        ).is_true()
        assert_that(timeout_object.get_remaining_timeout()).described_as(
            "The timeout object is supposed to be started but only after the "
            "execute_procedure terminates"
        ).is_close_to(10, 0.1)

    @staticmethod
    def test_timeout_can_be_passed_as_an_object():
        """The timeout can be passed as an object.

        When timeout is passed as an object, the object is supposed to be
        kept as it is and passed to the verify_postconditions method.
        """
        action = MockSUTAction()
        timeout = ChainedAssertionsTimeout(10)
        action.execute(postconditions_timeout=timeout)

        assert_that(action.last_timeout_object).described_as(
            "The exact timeout instance is supposed to be passed to the "
            "verify_postconditions method"
        ).is_equal_to(timeout)
