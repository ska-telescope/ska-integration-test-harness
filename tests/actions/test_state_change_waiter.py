"""Unit tests for the StateChangeWaiter class."""

from typing import Callable
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.event import ReceivedEvent

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.state_change_waiter import (
    StateChangeWaiter,
)
from tests.actions.utils.mock_event_tracer import (
    add_event,
    create_mock_event_tracer,
    delayed_add_event,
)


class TestStateChangeWaiter:
    """Unit tests for the StateChangeWaiter class."""

    @pytest.fixture
    @staticmethod
    def mocked_event_tracer() -> MagicMock:
        """Create a mock TangoEventTracer instance."""
        return create_mock_event_tracer()

    @pytest.fixture
    @staticmethod
    def real_event_tracer():
        """Create a real TangoEventTracer instance."""
        return TangoEventTracer()

    @staticmethod
    def create_state_change_waiter(
        event_tracer: MagicMock | TangoEventTracer,
    ) -> StateChangeWaiter:
        """
        Create a StateChangeWaiter instance with a mock event tracer.

        :param mock_event_tracer: A MagicMock instance of TangoEventTracer,
            or a real TangoEventTracer instance.
        :return: An instance of StateChangeWaiter with the mock event tracer.
        """
        waiter = StateChangeWaiter()
        waiter.event_tracer = event_tracer
        return waiter

    @staticmethod
    def create_expected_event(
        device: str = "device1",
        attribute: str = "obsState",
        predicate: Callable[[ReceivedEvent], bool] = lambda _: True,
    ) -> ExpectedEvent:
        """
        Create an ExpectedEvent with predefined values.

        :return: An instance of ExpectedEvent.
        """
        return ExpectedEvent(
            device=device, attribute=attribute, predicate=predicate
        )

    def test_add_expected_state_changes_should_add_and_subscribe(
        self, mocked_event_tracer
    ) -> None:
        """When expected state changes is called, the event is subscribed.

        (and added to the pending state changes)
        """
        state_change_waiter = self.create_state_change_waiter(
            mocked_event_tracer
        )
        expected_event = self.create_expected_event()

        state_change_waiter.add_expected_state_changes([expected_event])

        assert_that(state_change_waiter.pending_state_changes).described_as(
            "The expected events should be added to the pending state changes."
        ).contains(expected_event)
        state_change_waiter.event_tracer.subscribe_event.assert_called_once_with(  # pylint: disable=line-too-long # noqa: E501
            expected_event.device, expected_event.attribute
        )

        # NOTE: when there is a subscription, we mock the event tracer
        # instead of the DeviceProxy, since the event tracer for technical
        # reasons (https://gitlab.com/tango-controls/pytango/-/issues/459)

    def test_wait_all_succeeds_if_all_state_changes_occurred(
        self, real_event_tracer
    ) -> None:
        """All state changes occurred should return True if all occurred.

        NOTE: An event occurred if and only if in the EventTracer events list
        there is an event that matches the expected event.
        """
        state_change_waiter = self.create_state_change_waiter(
            real_event_tracer
        )
        # the state change waiter expects two events
        state_change_waiter.pending_state_changes = [
            self.create_expected_event(
                "device1", "attribute1", lambda e: e.attribute_value == 100
            ),
            self.create_expected_event(
                "device2", "attribute2", lambda e: e.attribute_value == 200
            ),
        ]

        # the tracer contains or will contain all needed events
        add_event(real_event_tracer, "device1", "attribute1", 100)
        delayed_add_event(
            real_event_tracer, "device2", "attribute2", 200, delay=1
        )

        # wait all succeeds without errors
        state_change_waiter.wait_all(2)

    def test_wait_all_succeeds_if_some_event_didnt_occur(
        self, real_event_tracer
    ) -> None:
        """All state changes occurred should return False if some didn't occur.

        NOTE: An event occurred if and only if in the EventTracer events list
        there is an event that matches the expected event.
        """
        state_change_waiter = self.create_state_change_waiter(
            real_event_tracer
        )
        # the state change waiter expects two events
        occurred_event = self.create_expected_event(
            "device1", "attribute1", lambda e: e.attribute_value == 100
        )
        not_occurred_event = self.create_expected_event(
            "device2", "attribute2", lambda e: e.attribute_value == 200
        )
        state_change_waiter.pending_state_changes = [
            occurred_event,
            not_occurred_event,
        ]
        # the tracer contains only the first of the expected events
        # (+ additional non-interesting events)
        add_event(real_event_tracer, "device1", "attribute1", 100)
        add_event(real_event_tracer, "device2", "attribute2", 400)

        # wait all fails with a TimeoutError
        with pytest.raises(TimeoutError) as excinfo:
            state_change_waiter.wait_all(1)

        # the exception message should indicate that
        # not all expected events occurred, report which events
        # did not occur and which did occur
        error_message = str(excinfo.value)

        assert_that(error_message).described_as(
            "The exception message should indicate that not "
            "all expected events occurred."
        ).contains("Not all the expected events occurred")

        assert_that(error_message.replace("\n", "")).described_as(
            "The exception message should indicate which events did not occur."
        ).contains(
            "The following events did not occur:" + str(not_occurred_event)
        )

        assert_that(error_message.replace("\n", "")).described_as(
            "The exception message should indicate which events did occur."
        ).contains("The following events occurred:" + str(occurred_event))

    def test_reset_should_clear_pending_state_changes(
        self, mocked_event_tracer
    ) -> None:
        """Reset the state change waiter and clear pending state changes."""
        state_change_waiter = self.create_state_change_waiter(
            mocked_event_tracer
        )
        expected_event = self.create_expected_event()
        state_change_waiter.add_expected_state_changes([expected_event])

        state_change_waiter.reset()

        assert_that(state_change_waiter.pending_state_changes).described_as(
            "the pending state changes should be cleared"
        ).is_empty()

        # the tracer should be cleared
        mocked_event_tracer.unsubscribe_all.assert_called_once()
        mocked_event_tracer.clear_events.assert_called_once()
