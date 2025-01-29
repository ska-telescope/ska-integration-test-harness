"""Unit tests for the TracerAction class."""

import time
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from ska_tango_testing.integration.tracer import TangoEventTracer

from ska_integration_test_harness.core.actions.tracer_action import (
    TracerAction,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event, delayed_add_event

from .utils import (
    create_mock_assertion,
    create_simple_assertion,
    create_state_change_assertion,
)


class MockTracerAction(TracerAction):
    """A mock subclass of TracerAction for testing purposes."""

    def execute_procedure(self):
        """Do nothing."""

    def describe_procedure(self) -> str:
        """Return a dummy procedure description.

        :return: dummy description
        """
        return "A dummy procedure that accomplishes nothing."


@pytest.mark.core
class TestTracerAction:
    """Unit tests for the TracerAction class.

    The unit tests focus on:

    - the initialisation procedure
    - the capability of setting a timeout
      (and having it propagated to existing postconditions)
    - the capability of adding an early stop condition
      (and having it propagated to existing postconditions)
    - the capability of adding preconditions and postconditions
      (and having them share the same tracer, timeout and early stop condition
      present at the time of their addition)
    - the capability of executing the action and verifying the
      preconditions and postconditions
    - the capability of logging or not logging preconditions and postconditions
      according to the initialisation parameters
    """

    @staticmethod
    def test_action_initialises_with_default_parameters():
        """The action initialises with expected default parameters.

        In particular, we expect:

        - a tracer instance to be accessible;
        - no early stop condition is set;
        - pre-conditions and post-conditions to be empty
        """
        action = MockTracerAction()

        assert_that(action.tracer).is_instance_of(TangoEventTracer)
        assert_that(action.early_stop).is_none()
        assert_that(action.preconditions).is_instance_of(list).is_length(0)
        assert_that(action.postconditions).is_instance_of(list).is_length(0)

    # -----------------------------------------------------------------------
    # Attributes propagation tests
    # (When I set an attribute or an early stop condition on an action,
    # it propagates to postconditions as expected)

    @staticmethod
    def test_action_early_stop_when_set_propagates_to_postconditions():
        """Actions early stop when set propagate to existing postconditions."""
        action = MockTracerAction()
        post_cond1 = create_state_change_assertion("test/device/1")
        post_cond2 = create_state_change_assertion("test/device/2")
        mock_initial_early_stop = MagicMock(return_value=False)
        post_cond2.early_stop = mock_initial_early_stop
        action.add_postconditions(post_cond1, post_cond2)

        mock_new_early_stop = MagicMock(return_value=True)
        action.add_early_stop(mock_new_early_stop)

        assert_that(action.early_stop).described_as(
            "The action can set an early stop condition"
        ).is_same_as(mock_new_early_stop)
        assert_that(post_cond1.early_stop).described_as(
            "The new early stop condition is used for an action without "
            "an early stop condition"
        ).is_same_as(mock_new_early_stop)
        assert_that(post_cond2.early_stop).described_as(
            "The new early stop condition is combined in OR "
            "with an existing early stop condition in a postcondition"
        ).is_not_same_as(mock_initial_early_stop)

        # Test that the new early stop condition is used
        # for a postcondition without an early stop condition
        mock_event = MagicMock()
        assert_that(post_cond1.early_stop(mock_event)).described_as(
            "The new early stop condition is used for an action without "
            "an early stop condition"
            "(Old: Not set, New: True --> True)"
        ).is_true()
        mock_new_early_stop.assert_called_with(mock_event)
        mock_new_early_stop.reset_mock()

        # Test that the new early stop condition is combined in OR
        # with an existing early stop condition in a postcondition
        mock_event2 = MagicMock()
        assert_that(post_cond2.early_stop(mock_event2)).described_as(
            "The new early stop condition is combined in OR "
            "with an existing early stop condition in a postcondition"
            "(Old: False, New: True --> True)"
        ).is_true()
        mock_new_early_stop.assert_called_once_with(mock_event2)
        mock_initial_early_stop.assert_called_once_with(mock_event2)

    # -----------------------------------------------------------------------
    # Precondition and postcondition management tests

    @staticmethod
    def test_action_a_precondition_can_be_added():
        """An action can add a precondition."""
        action = MockTracerAction()
        pre_cond = create_simple_assertion("test/device/1")

        action.add_preconditions(pre_cond)

        assert_that(action.preconditions).is_length(1)
        assert_that(action.preconditions[0]).is_same_as(pre_cond)

    @staticmethod
    def test_action_a_precondition_can_be_added_and_tracer_is_propagated():
        """It the precondition needs a tracer, it is shared with the action."""
        action = MockTracerAction()
        pre_cond = create_state_change_assertion("test/device/1")

        action.add_preconditions(pre_cond)

        assert_that(pre_cond.tracer).is_same_as(action.tracer)

    @staticmethod
    def test_action_multiple_preconditions_can_be_added():
        """Multiple preconditions can be added to an action."""
        action = MockTracerAction()
        pre_cond1 = create_simple_assertion("test/device/1")
        pre_cond2 = create_simple_assertion("test/device/2")

        action.add_preconditions(pre_cond1, pre_cond2)

        assert_that(action.preconditions).is_length(2)
        assert_that(action.preconditions[0]).is_same_as(pre_cond1)
        assert_that(action.preconditions[1]).is_same_as(pre_cond2)

    @staticmethod
    def test_action_a_postcondition_can_be_added():
        """An action can add a postcondition.

        - the tracer is shared with the action
        - the timeout is shared with the action
        - the early stop condition is shared with the action
        """
        action_mock_early_stop = MagicMock()
        action = MockTracerAction().add_early_stop(action_mock_early_stop)
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)

        assert_that(action.postconditions).is_length(1)
        assert_that(action.postconditions[0]).is_same_as(post_cond)
        assert_that(post_cond.tracer).described_as(
            "The tracer is shared with the action"
        ).is_same_as(action.tracer)
        assert_that(post_cond.early_stop).described_as(
            "The early stop condition is shared with the action"
        ).is_same_as(action_mock_early_stop)

    @staticmethod
    def test_multiple_postconditions_can_be_added():
        """Multiple postconditions can be added to an action."""
        action = MockTracerAction()
        post_cond1 = create_state_change_assertion("test/device/1")
        post_cond2 = create_state_change_assertion("test/device/2")

        action.add_postconditions(post_cond1, post_cond2)

        assert_that(action.postconditions).is_length(2)
        assert_that(action.postconditions[0]).is_same_as(post_cond1)
        assert_that(action.postconditions[1]).is_same_as(post_cond2)

    @staticmethod
    def test_action_a_postcondition_early_stop_is_combined_with_the_action_early_stop():  # pylint: disable=line-too-long # noqa
        """
        A postcondition early stop is combined with the action early stop.
        """
        action_mock_early_stop = MagicMock(return_value=False)
        action = MockTracerAction().add_early_stop(action_mock_early_stop)
        post_cond = create_state_change_assertion("test/device/1")
        post_cond_mock_early_stop = MagicMock(return_value=False)
        post_cond.early_stop = post_cond_mock_early_stop
        action.add_postconditions(post_cond)

        assert_that(post_cond.early_stop).described_as(
            "The postcondition early stop is combined "
            "with the action early stop"
        ).is_not_same_as(action_mock_early_stop)

        # Test that both the early stop conditions are called
        mock_event = MagicMock()
        assert_that(post_cond.early_stop(mock_event)).described_as(
            "The postcondition early stop is combined "
            "with the action early stop"
            "(Action: False, Postcondition: False --> False)"
        ).is_false()
        action_mock_early_stop.assert_called_once_with(mock_event)
        post_cond_mock_early_stop.assert_called_once_with(mock_event)

    # -----------------------------------------------------------------------
    # Action execution (relation with pre and post conditions)

    @staticmethod
    def test_action_execution_setups_pre_and_post_conditions():
        """An action execution setups pre and post conditions."""
        action = MockTracerAction()
        pre_cond = create_mock_assertion()
        post_cond = create_mock_assertion()
        action.add_preconditions(pre_cond).add_postconditions(post_cond)

        action.setup()

        pre_cond.setup.assert_called_once()
        post_cond.setup.assert_called_once()

    @staticmethod
    def test_action_execution_verify_preconditions():
        """An action execution verifies preconditions."""
        action = MockTracerAction()
        pre_cond = create_mock_assertion()
        action.add_preconditions(pre_cond)

        action.verify_preconditions()

        pre_cond.verify.assert_called_once()

    @staticmethod
    def test_action_execution_verify_postconditions():
        """An action execution verifies postconditions."""
        action = MockTracerAction()
        post_cond = create_mock_assertion()
        action.add_postconditions(post_cond)

        action.verify_postconditions()

        post_cond.verify.assert_called_once()

    @staticmethod
    def test_action_postcondition_passes_if_events_happened():
        """An action postcondition passes if the events happened."""
        action = MockTracerAction()
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)
        add_event(action.tracer, "test/device/1", "state", "ON")

        action.verify_postconditions()

    @staticmethod
    def test_action_postcondition_fails_if_events_did_not_happen():
        """An action postcondition fails if the events did not happen."""
        action = MockTracerAction()
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)
        add_event(action.tracer, "test/device/1", "state", "OFF")

        with pytest.raises(AssertionError):
            action.verify_postconditions()

    # -----------------------------------------------------------------------
    # Action execution (setup resets tracer and timeout)

    @staticmethod
    def test_action_setup_resets_tracer_events_and_subscriptions():
        """An action setup resets the tracer events and subscriptions."""
        action = MockTracerAction()
        action.tracer.subscribe_event(
            create_device_proxy_mock("test/device/1"), "test_attr"
        )
        add_event(action.tracer, "test/device/1", "test_attr", 42)

        action.setup()

        # pylint: disable=protected-access
        assert_that(action.tracer._subscriber._subscription_ids).described_as(
            "We expect the tracer subscriptions to be cleared"
        ).is_empty()
        assert_that(action.tracer.events).described_as(
            "We expect the tracer events to be cleared"
        ).is_empty()

    # -----------------------------------------------------------------------
    # Logging tests

    @staticmethod
    def test_action_executions_does_not_log_preconditions_by_default():
        """An action execution does not log preconditions by default."""
        action = MockTracerAction()
        action.logger = MagicMock()
        pre_cond = create_state_change_assertion("test/device/1")
        pre_cond.verify = MagicMock()
        action.add_preconditions(pre_cond)

        action.verify_preconditions()

        action.logger.info.assert_not_called()

    @staticmethod
    def test_action_executions_logs_postconditions_by_default():
        """An action execution logs postconditions by default."""
        action = MockTracerAction()
        action.logger = MagicMock()
        post_cond = create_state_change_assertion("test/device/1")
        post_cond.verify = MagicMock()
        action.add_postconditions(post_cond)

        action.verify_postconditions()

        action.logger.info.assert_called_once()
        action.logger.info.assert_called_with(
            "Verifying postcondition: %s", str(post_cond)
        )

    @staticmethod
    def test_action_executions_can_enable_precondition_logging():
        """An action execution can enable logging."""
        action = MockTracerAction(log_preconditions=True)
        action.logger = MagicMock()
        pre_cond = create_state_change_assertion("test/device/1")
        pre_cond.verify = MagicMock()
        action.add_preconditions(pre_cond)

        action.verify_preconditions()

        action.logger.info.assert_called_once()
        action.logger.info.assert_called_with(
            "Verifying precondition: %s", str(pre_cond)
        )

    @staticmethod
    def test_action_executions_can_disable_postcondition_logging():
        """An action execution can disable logging."""
        action = MockTracerAction(log_postconditions=False)
        action.logger = MagicMock()
        post_cond = create_state_change_assertion("test/device/1")
        post_cond.verify = MagicMock()
        action.add_postconditions(post_cond)

        action.verify_postconditions()

        action.logger.info.assert_not_called()

    # -----------------------------------------------------------------------
    # The postconditions are verified within the timeout

    @staticmethod
    def test_action_postconditions_are_verified_within_the_timeout_and_pass():
        """The postconditions are verified within the timeout and pass."""
        action = MockTracerAction()
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)
        delayed_add_event(action.tracer, "test/device/1", "state", "ON", 0.5)

        start_time = datetime.now()
        action.execute(postconditions_timeout=1)

        assert_that((datetime.now() - start_time).total_seconds()).described_as(
            "The action succeeds only when the postconditions are verified"
        ).is_close_to(0.5, 0.1)

    @staticmethod
    def test_action_postconditions_are_verified_within_the_timeout_and_fail():
        """The postconditions are verified within the timeout and fail."""
        action = MockTracerAction()
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)
        delayed_add_event(action.tracer, "test/device/1", "state", "OFF", 0.5)

        start_time = datetime.now()
        with pytest.raises(AssertionError):
            action.execute(postconditions_timeout=1)

        assert_that((datetime.now() - start_time).total_seconds()).described_as(
            "We expect the whole timout to be elapsed"
        ).is_close_to(1, 0.1)
