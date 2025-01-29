"""Unit tests for the AssertDevicesStateChange class."""

import pytest
from assertpy import assert_that

from ska_integration_test_harness.core.assertions.dev_state_changes import (
    AssertDevicesStateChanges,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event, delayed_add_event


@pytest.mark.core
class TestAssertDevicesStateChanges:
    """Unit tests for the AssertDevicesStateChange class.

    AssertDevicesStateChange wraps the TangoEventTracer, so those tests
    are inevitably event-based. The following tests are probably partially
    redundant with the tests of the TangoEventTracer in ska-tango-testing, so
    we try to keep them minimal.

    We cover the following cases:

    - basic event assertion (in the past)
    - capability of using previous value and custom matchers (in the past)
    - capability of waiting for a timeout
    - capability of handling early stop events
    """

    # -----------------------------------------------------------------
    # Basic event assertion

    @staticmethod
    def test_assertion_passes_if_events_occurred():
        """The assertion passes if the events occurred."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
            create_device_proxy_mock("test/dev/4"),
        ]
        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", timeout=1
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        add_event(assertion.tracer, "test/dev/4", "state", "ON")
        assertion.verify()

    @staticmethod
    def test_assertion_fails_if_events_did_not_occurred():
        """The assertion fails if the events did not occur."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
            create_device_proxy_mock("test/dev/4"),
        ]
        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", timeout=1
        )
        assertion.setup()

        event1 = add_event(assertion.tracer, "test/dev/3", "state", "OFF")
        event2 = add_event(assertion.tracer, "test/dev/4", "state", "OFF")
        event3 = add_event(assertion.tracer, "test/dev/4", "state", "ON")
        event1.__str__ = lambda _: "ReceivedEvent(test/dev/3.state=OFF)"
        event2.__str__ = lambda _: "ReceivedEvent(test/dev/4.state=OFF)"
        event3.__str__ = lambda _: "ReceivedEvent(test/dev/4.state=ON)"

        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure message includes a reference to the asserted devices."
        ).contains("test/dev/3", "test/dev/4").described_as(
            "The failure message includes a reference to the attribute name."
        ).contains(
            "attribute state"
        ).described_as(
            "The failure message includes a reference to the expected value."
        ).contains(
            "to ON"
        ).described_as(
            "The failure message includes a reference to the device "
            "for which the events have not been received."
        ).contains(
            "Events not found for test/dev/3.state"
        ).described_as(
            "The failure message includes a reference to the received events."
        ).contains(
            "ReceivedEvent(test/dev/3.state=OFF)",
            "ReceivedEvent(test/dev/4.state=OFF)",
            "ReceivedEvent(test/dev/4.state=ON)",
        )

    # -----------------------------------------------------------------
    # Previous value and custom matchers

    @staticmethod
    def test_assertion_fails_if_previous_value_does_not_match():
        """The assertion fails if the previous value does not match."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]
        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", previous_value="OFF"
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "OFF")
        add_event(assertion.tracer, "test/dev/3", "state", "UNKNOWN")
        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure message includes a reference to the asserted devices."
        ).contains("test/dev/3").described_as(
            "The failure message includes a reference to the attribute name."
        ).contains(
            "attribute state"
        ).described_as(
            "The failure message includes a reference to the expected value."
        ).contains(
            "to ON"
        ).described_as(
            "The failure message includes a reference to the previous value."
        ).contains(
            "from OFF"
        )

    @staticmethod
    def test_assertion_fails_if_custom_matcher_does_not_match():
        """The assertion fails if the custom matcher does not match."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]

        def my_custom_matcher(event):
            return event.attribute_value == "OFF"

        assertion = AssertDevicesStateChanges(
            devices, "state", custom_matcher=my_custom_matcher
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "UNKNOWN")
        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure message includes a reference to the asserted devices."
        ).contains("test/dev/3").described_as(
            "The failure message includes a reference to the attribute name."
        ).contains(
            "attribute state"
        ).described_as(
            "The failure message includes a reference to the custom matcher."
        ).contains(
            "matching my_custom_matcher"
        )

    @staticmethod
    def test_assertion_passes_if_previous_value_and_custom_matcher_match():
        """The assertion passes if the prev. value and custom matcher match."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]

        def my_custom_matcher(event):
            return event.attribute_value == "ON"

        assertion = AssertDevicesStateChanges(
            devices,
            "state",
            previous_value="UNKNOWN",
            custom_matcher=my_custom_matcher,
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "UNKNOWN")
        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        assertion.verify()

    # -----------------------------------------------------------------
    # Timeout

    @staticmethod
    def test_assertion_fails_if_timeout_reached():
        """The assertion fails if the timeout is reached."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]
        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", timeout=1
        )
        assertion.setup()

        delayed_add_event(
            assertion.tracer, "test/dev/3", "state", "ON", delay=1.1
        )
        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure message includes a reference to the asserted devices."
        ).contains("test/dev/3").described_as(
            "The failure message includes a reference to the attribute name."
        ).contains(
            "attribute state"
        ).described_as(
            "The failure message includes a reference to the expected value."
        ).contains(
            "to ON"
        ).described_as(
            "The failure message includes a reference to the timeout."
        ).contains(
            "within 1.0 seconds"
        )

    @staticmethod
    def test_assertion_passes_if_timeout_not_reached():
        """The assertion passes if the timeout is not reached."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]
        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", timeout=1
        )
        assertion.setup()

        delayed_add_event(
            assertion.tracer, "test/dev/3", "state", "ON", delay=0.5
        )
        assertion.verify()

    # -----------------------------------------------------------------
    # Early stop events

    @staticmethod
    def test_assertion_fails_if_early_stop_event_occurred():
        """The assertion fails if an early stop event occurred."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]

        def my_early_stop_sentinel(event):
            return event.attribute_value == "UNKNOWN"

        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", early_stop=my_early_stop_sentinel
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "OFF")
        add_event(assertion.tracer, "test/dev/3", "state", "UNKNOWN")
        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure message includes a reference to the asserted devices."
        ).contains("test/dev/3").described_as(
            "The failure message includes a reference to the attribute name."
        ).contains(
            "attribute state"
        ).described_as(
            "The failure message includes a reference to the expected value."
        ).contains(
            "to ON"
        ).described_as(
            "The failure message includes a reference to the early stop event."
        ).contains(
            "using early stop sentinel my_early_stop_sentinel"
        )

    @staticmethod
    def test_assertion_passes_if_no_early_stop_event_occurred():
        """The assertion passes if no early stop event occurred."""
        devices = [
            create_device_proxy_mock("test/dev/3"),
        ]

        def my_early_stop_sentinel(event):
            return event.attribute_value == "UNKNOWN"

        assertion = AssertDevicesStateChanges(
            devices, "state", "ON", early_stop=my_early_stop_sentinel
        )
        assertion.setup()

        add_event(assertion.tracer, "test/dev/3", "state", "OFF")
        add_event(assertion.tracer, "test/dev/3", "state", "ON")
        assertion.verify()
