"""Unit tests for the TracerAssertion class."""

import pytest
from assertpy import assert_that
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.assertions import (
    ChainedAssertionsTimeout,
    _get_tracer,
    get_context_early_stop,
    get_context_timeout,
)

from ska_integration_test_harness.core.assertions.tracer_assertion import (
    TracerAssertion,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event


class MockTracerAssertion(TracerAssertion):
    """Mock subclass of TracerAssertion for testing purposes."""

    def __init__(self, *args, **kwargs):
        """Do nothing, just store the arguments."""
        super().__init__(*args, **kwargs)

    def verify(self):
        """Do nothing."""

    def describe_assumption(self):
        """Return a dummy assumption description."""
        return "A dummy assumption that accomplishes nothing."


@pytest.mark.platform
@pytest.mark.core
class TestTracerAssertion:
    """Unit tests for the TracerAssertion class.

    Unit tests on this assertion class focus on the management of the
    tracer, the timeout and the early stop condition.
    """

    @staticmethod
    def test_assertion_init_with_default_tracer_timeout_and_no_early_stop():
        """The assertion initialises with expected default parameters.

        In particular, we expect:

        - a tracer instance to be accessible;
        - a timeout of 0;
        - no early stop condition.
        """
        assertion = MockTracerAssertion()

        assert_that(assertion.tracer).is_instance_of(TangoEventTracer)

        assert_that(assertion.timeout).is_instance_of(ChainedAssertionsTimeout)
        assert_that(assertion.timeout.initial_timeout).described_as(
            "We expect the action timeout to be 0"
        ).is_equal_to(0)
        assert_that(assertion.timeout.get_remaining_timeout()).described_as(
            "We expect the remaining timeout to be 0"
        ).is_equal_to(0)
        assert_that(assertion.timeout.is_started()).described_as(
            "We expect the timeout to not be started"
        ).is_false()

        assert_that(assertion.early_stop).is_none()
        assert_that(assertion.is_tracer_managed()).described_as(
            "By default, the tracer is managed by the assertion"
        ).is_true()
        assert_that(assertion.is_timeout_managed()).described_as(
            "By default, the timeout is managed by the assertion"
        ).is_true()

    @staticmethod
    def test_assertion_context_includes_given_timeout_tracer_and_early_stop():
        """The assertion assertpy context contains the given parameters.

        We expect the assertion to decorate the assertpy context with a
        given tracer, timeout and early stop condition.
        """
        tracer = TangoEventTracer()
        timeout = ChainedAssertionsTimeout(10)

        def custom_early_stop(_):
            """A dummy early stop condition."""
            return False

        assertion = MockTracerAssertion(tracer, timeout, custom_early_stop)

        assertpy_context = assertion.get_assertpy_context()
        assert_that(_get_tracer(assertpy_context)).is_same_as(tracer)
        assert_that(get_context_timeout(assertpy_context)).is_same_as(timeout)
        assert_that(get_context_early_stop(assertpy_context)).is_same_as(
            custom_early_stop
        )
        assert_that(assertion.is_tracer_managed()).described_as(
            "If a tracer is given, it is not managed by the assertion"
        ).is_false()
        assert_that(assertion.is_timeout_managed()).described_as(
            "If a timeout is given, it is not managed by the assertion"
        ).is_false()

    # --------------------------------------------------------------------
    # Tracer management

    @staticmethod
    def test_assertion_tracer_is_overridable():
        """The assertion tracer can be overridden with a custom one.

        We expect the assertion to allow the user to pass a custom tracer
        instance to be used instead of the default one.
        """
        assertion = MockTracerAssertion()

        other_tracer = TangoEventTracer()
        assertion.tracer = other_tracer

        assert_that(assertion.tracer).is_same_as(other_tracer)
        assert_that(assertion.is_tracer_managed()).described_as(
            "If a tracer is set, it is not managed by the assertion"
        ).is_false()

    @staticmethod
    def test_assertion_tracer_is_resetted_during_setup_when_managed():
        """A managed tracer is resetted during setup.

        When the tracer is managed (i.e. created by the assertion and not
        injected), the assertion should reset the tracer events and
        subscriptions during the setup phase.
        """
        assertion = MockTracerAssertion()
        assertion.tracer.subscribe_event(
            create_device_proxy_mock("test/device/1"), "test_attr"
        )
        add_event(assertion.tracer, "test/device/1", "test_attr", 42)
        add_event(assertion.tracer, "test/device/2", "test_attr", 42)

        assertion.setup()

        # pylint: disable-next=protected-access
        assert_that(
            assertion.tracer._subscriber._subscription_ids
        ).described_as(
            "We expect the tracer subscriptions to be cleared"
        ).is_empty()
        assert_that(assertion.tracer.events).described_as(
            "We expect the tracer events to be cleared"
        ).is_empty()

    @staticmethod
    def test_assertion_tracer_is_not_resetted_during_setup_when_not_managed():
        """An unmanaged tracer is not touched during setup.

        When the tracer is set to a given instance, the assertion should
        not reset the tracer events and subscriptions during the setup phase
        (because we assume is used in other parts of the code).
        """
        tracer = TangoEventTracer()
        assertion = MockTracerAssertion(tracer=tracer)
        assertion.tracer.subscribe_event(
            create_device_proxy_mock("test/device/1"), "test_attr"
        )
        event1 = add_event(assertion.tracer, "test/device/1", "test_attr", 42)
        event2 = add_event(assertion.tracer, "test/device/2", "test_attr", 42)

        assertion.setup()

        # pylint: disable-next=protected-access
        assert_that(
            assertion.tracer._subscriber._subscription_ids
        ).described_as(
            "We expect the tracer subscriptions to be kept"
        ).is_not_empty()
        assert_that(assertion.tracer.events).described_as(
            "We expect the tracer events to be kept"
        ).is_not_empty().contains(event1, event2)

    # --------------------------------------------------------------------
    # Timeout management

    @staticmethod
    def test_assertion_timeout_is_overridable_with_objects():
        """The assertion timeout can be overridden with a custom object.

        We expect the assertion to allow the user to pass a custom timeout
        instance to be used instead of the default one. If a custom timeout
        is given, the assertion should not manage it.
        """
        assertion = MockTracerAssertion()

        custom_timeout = ChainedAssertionsTimeout(10)
        assertion.timeout = custom_timeout

        assert_that(assertion.timeout).is_same_as(custom_timeout)
        assert_that(assertion.is_timeout_managed()).described_as(
            "If a timeout is set as object, it is not managed by the assertion"
        ).is_false()

    @staticmethod
    def test_assertion_timeout_is_overridable_with_number():
        """The assertion timeout can be overridden with a number.

        We expect the assertion to allow the user to pass a number to be
        converted into a custom timeout instance. If a custom timeout is
        given, the assertion should not manage it.
        """
        assertion = MockTracerAssertion()

        assertion.timeout = 10

        assert_that(assertion.timeout).is_instance_of(ChainedAssertionsTimeout)
        assert_that(assertion.timeout.initial_timeout).is_equal_to(10)
        assert_that(assertion.is_timeout_managed()).described_as(
            "If a timeout is set as number, it is managed by the assertion"
        ).is_true()

    @staticmethod
    def test_assertion_timeout_is_resetted_during_setup_when_managed():
        """The timeout is resetted during setup when managed by the assertion.

        The assertion should reset the timeout during the setup phase.
        """
        assertion = MockTracerAssertion(timeout=10)
        initial_timeout = assertion.timeout
        assertion.timeout.start()
        assert_that(assertion.timeout.is_started()).is_true()

        assertion.setup()

        assert_that(assertion.timeout).is_not_same_as(initial_timeout)
        assert_that(assertion.timeout.is_started()).is_false()

    @staticmethod
    def test_assertion_timeout_is_not_resetted_during_setup_when_not_managed():
        """The timeout is not touched during setup when not managed.

        When the timeout is set to a given instance, the assertion should
        not reset the timeout during the setup phase.
        """
        timeout = ChainedAssertionsTimeout(10)
        assertion = MockTracerAssertion(timeout=timeout)
        initial_timeout = assertion.timeout
        timeout.start()
        assert_that(timeout.is_started()).is_true()

        assertion.setup()

        assert_that(assertion.timeout).is_same_as(initial_timeout)
        assert_that(timeout.is_started()).is_true()
