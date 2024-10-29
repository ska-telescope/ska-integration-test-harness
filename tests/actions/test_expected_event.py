"""Tests for the `ExpectedEvent` class and its subclasses."""

from assertpy import assert_that

from ska_integration_test_harness.actions.expected_event import (
    ExpectedEvent,
    ExpectedStateChange,
)
from tests.actions.utils.mock_device_proxy import patch_device_proxy
from tests.actions.utils.mock_received_event import create_received_event_mock


class TestExpectedEvent:
    """Tests for the ``ExpectedEvent`` class."""

    @staticmethod
    def create_sample_event() -> ExpectedEvent:
        """Create a sample event for testing purposes.

        :return: A sample event.
        """

        return ExpectedEvent(
            device="sample_device",
            attribute="sample_attribute",
            predicate=lambda e: e.attribute_value >= 100,
        )

    def test_str(self) -> None:
        """The string representation of an event contains all the info.

        Expected information:

        - an introductory message,
        - the device name,
        - the attribute name,
        - a reference that the expected event is recognised by
            a custom predicate.
        """

        sample_event = self.create_sample_event()
        event_str = str(sample_event)

        assert_that(event_str).contains("Expected an event")
        assert_that(event_str).contains("sample_device")
        assert_that(event_str).contains("sample_attribute")
        assert_that(event_str).contains("custom predicate")

    def test_event_matches_when_conditions_are_met(self) -> None:
        """An event matches the expected event when conditions are met."""

        sample_event = self.create_sample_event()

        assert_that(
            sample_event.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute", 150
                )
            )
        ).is_true()

        assert_that(
            sample_event.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute", 100
                )
            )
        ).is_true()

    def test_event_doesnt_match_when_a_condition_is_not_met(self) -> None:
        """An event doesn't match the exp. evt. when a condition is not met."""

        sample_event = self.create_sample_event()

        assert_that(
            sample_event.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute", 50
                )
            )
        ).described_as(
            "An event that doesn't satisfy the predicate "
            "is expected to not match the expected event."
        ).is_false()

        assert_that(
            sample_event.event_matches(
                create_received_event_mock(
                    "sample_device_2", "sample_attribute", 100
                )
            )
        ).described_as(
            "An event from a different device "
            "is expected to not match the expected event."
        ).is_false()

        assert_that(
            sample_event.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute_2", 100
                )
            )
        ).described_as(
            "An event with a different attribute "
            "is expected to not match the expected event."
        ).is_false()


class TestExpectedStateChange:
    """Tests for the ``ExpectedStateChange`` class."""

    @staticmethod
    def create_sample_state_change() -> ExpectedStateChange:
        """Create a sample state change for testing purposes.

        :return: A sample state change.
        """

        return ExpectedStateChange(
            device="sample_device",
            attribute="sample_attribute",
            expected_value=100,
        )

    def test_str(self) -> None:
        """The string representation of an event contains all the info.

        Expected information:

        - an introductory message,
        - the device name,
        - the attribute name,
        - a value that the attribute is expected to have.
        """

        # with patch_device_proxy("sample_device", "sample_attribute", 100):

        with patch_device_proxy("sample_device", "sample_attribute", 100):
            sample_state_change = self.create_sample_state_change()
            state_change_str = str(sample_state_change)

        assert_that(state_change_str).contains("Expected an event")
        assert_that(state_change_str).contains("sample_device")
        assert_that(state_change_str).contains("sample_attribute")
        assert_that(state_change_str).contains("100")

    def test_event_matches_when_conditions_are_met(self) -> None:
        """An event matches the expected state change when cond. are met."""
        with patch_device_proxy("sample_device", "sample_attribute", 100):
            sample_state_change = self.create_sample_state_change()

        assert_that(
            sample_state_change.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute", 100
                )
            )
        ).is_true()

    def test_event_doesnt_match_when_attr_value_is_different(self) -> None:
        """An event doesn't match the exp. state change when the value diff."""
        with patch_device_proxy("sample_device", "sample_attribute", 100):
            sample_state_change = self.create_sample_state_change()

        assert_that(
            sample_state_change.event_matches(
                create_received_event_mock(
                    "sample_device", "sample_attribute", 50
                )
            )
        ).is_false()
