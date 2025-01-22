"""Unit tests for the TracerAction class."""

import time
from unittest.mock import MagicMock

from assertpy import assert_that
import pytest
from ska_tango_testing.integration.tracer import TangoEventTracer

from ska_integration_test_harness.core.actions.tracer_action import (
    TracerAction,
)
from ska_integration_test_harness.core.assertions.attribute import AssertDevicesAreInState
from ska_integration_test_harness.core.assertions.state_changes import (
    AssertDevicesStateChanges,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event


class MockTracerAction(TracerAction):
    """A mock subclass of TracerAction for testing purposes."""

    def execute_procedure(self):
        """Do nothing."""

    def describe_procedure(self) -> str:
        """Return a dummy procedure description.

        :return: dummy description
        """
        return "A dummy procedure that accomplishes nothing."


def create_state_change_assertion(dev_name, expected_state="ON") -> AssertDevicesStateChanges:
    """Create a state change assertion for the given device.

    :param dev_name: the name of the device
    :param expected_state: the expected state (default: "ON")
    :return: the state change assertion
    """
    return AssertDevicesStateChanges(
        [create_device_proxy_mock(dev_name)], "state", expected_state
    )

def create_simple_assertion(dev_name, expected_state="ON") -> AssertDevicesAreInState:
    """Create a simple assertion for the given device.

    :param dev_name: the name of the device
    :param expected_state: the expected state (default: "ON")
    :return: the state change assertion
    """
    return AssertDevicesAreInState(
        [create_device_proxy_mock(dev_name)], "state", expected_state
    )

def create_mock_assertion(duration: float = 0, fail: bool = False) -> MagicMock:
    """Create a mock assertion."""
    def mock_verify():
        time.sleep(duration)
        if fail:
            raise AssertionError("Mock assertion failed")
        
    mock = MagicMock()
    mock.verify = MagicMock(side_effect=mock_verify)

    return mock

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
    """

    @staticmethod
    def test_action_initialises_with_default_parameters():
        """The action initialises with expected default parameters.

        In particular, we expect:

        - a tracer instance to be accessible;
        - a timeout of 0;
        - no early stop condition.
        - pre-conditions and post-conditions to be empty
        """
        action = MockTracerAction()

        assert_that(action.tracer).is_instance_of(TangoEventTracer)
        assert_that(action.timeout).is_equal_to(0)
        assert_that(action.early_stop).is_none()
        assert_that(action.preconditions).is_instance_of(list).is_length(0)
        assert_that(action.postconditions).is_instance_of(list).is_length(0)

    # -----------------------------------------------------------------------
    # Attributes propagation tests
    # (When I set an attribute or an early stop condition on an action,
    # it propagates to postconditions as expected)

    @staticmethod
    def test_action_timeout_when_set_propagates_to_postconditions():
        """An action timeout when set propagate to existing postconditions."""
        action = MockTracerAction()
        post_cond1 = create_state_change_assertion("test/device/1")
        post_cond2 = create_state_change_assertion("test/device/2")
        action.add_postconditions(post_cond1, post_cond2)

        action.set_timeout(10)

        assert_that(action.timeout).described_as(
            "The action can set a timeout"
        ).is_equal_to(10)
        assert_that(post_cond1.timeout).described_as(
            "The same timeout is propagated to both existing postconditions"
        ).is_same_as(post_cond2.timeout)
        assert_that(float(post_cond1.timeout)).described_as(
            "The timeout value is the expected one"
        ).is_equal_to(10.0).is_equal_to(float(post_cond2.timeout))

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
    def test_action_a_postcondition_can_be_added():
        """An action can add a postcondition.
        
        - the tracer is shared with the action
        - the timeout is shared with the action
        - the early stop condition is shared with the action
        """
        action_mock_early_stop = MagicMock()
        action = MockTracerAction().set_timeout(10).add_early_stop(action_mock_early_stop)
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)

        assert_that(action.postconditions).is_length(1)
        assert_that(action.postconditions[0]).is_same_as(post_cond)
        assert_that(post_cond.tracer).described_as(
            "The tracer is shared with the action"
        ).is_same_as(action.tracer)
        assert_that(post_cond.timeout).described_as(
            "The timeout is shared with the action"
        ).is_same_as(action._timeout)
        assert_that(float(post_cond.timeout)).described_as(
            "The timeout value is the expected one"
        ).is_equal_to(10.0)
        assert_that(post_cond.early_stop).described_as(
            "The early stop condition is shared with the action"
        ).is_same_as(action_mock_early_stop)

    @staticmethod
    def test_action_a_postcondition_early_stop_is_combined_with_the_action_early_stop(): # pylint: disable=line-too-long # noqa
        """
        A postcondition early stop is combined with the action early stop.
        """
        action_mock_early_stop = MagicMock(return_value=False)
        action = MockTracerAction().set_timeout(10).add_early_stop(action_mock_early_stop)
        post_cond = create_state_change_assertion("test/device/1")
        post_cond_mock_early_stop = MagicMock(return_value=False)
        post_cond.early_stop = post_cond_mock_early_stop
        action.add_postconditions(post_cond)

        assert_that(post_cond.early_stop).described_as(
            "The postcondition early stop is combined with the action early stop"
        ).is_not_same_as(action_mock_early_stop)

        # Test that both the early stop conditions are called
        mock_event = MagicMock()
        assert_that(post_cond.early_stop(mock_event)).described_as(
            "The postcondition early stop is combined with the action early stop"
            "(Action: False, Postcondition: False --> False)"
        ).is_false()
        action_mock_early_stop.assert_called_once_with(mock_event)
        post_cond_mock_early_stop.assert_called_once_with(mock_event)\
        
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

    @staticmethod
    def test_action_setup_resets_timeout():
        """An action setup resets the timeout."""
        action = MockTracerAction().set_timeout(1)
        post_cond1 = create_state_change_assertion("test/device/1")
        post_cond2 = create_state_change_assertion("test/device/2")
        action.add_postconditions(post_cond1, post_cond2)
        post_cond1.timeout.start()
        time.sleep(1)
        assert_that(post_cond2.timeout.get_remaining_timeout()).described_as(
            "We expect the timeout to be elapsed"
        ).is_equal_to(0)

        action.setup()

        assert_that(post_cond2.timeout.get_remaining_timeout()).described_as(
            "We expect the timeout to be resetted"
        ).is_equal_to(1)
        assert_that(post_cond2.timeout.is_started()).described_as(
            "We expect the timeout to not be started"
        ).is_false()

        





