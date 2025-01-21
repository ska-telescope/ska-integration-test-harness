"""An event-based assertion based on TangoEventTracer."""

import abc
from typing import Any, Callable, SupportsFloat

from assertpy import assert_that
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout
from ska_tango_testing.integration.event import ReceivedEvent

from .sut_assertion import SUTAssertion


class TracerAssertion(SUTAssertion, abc.ABC):
    """An event-based assertion based on TangoEventTracer.

    This class represents an assertion that is based on the events
    emitted by the TangoEventTracer. The assertion is event-based,
    so it needs to be configured with:

    - a valid tracer instance (if omitted, a default one will be used);
    - a timeout for the assertion to be verified (optional, if missing a
      zero timeout is assumed).
    - an early stop condition (optional, if missing the assertion will
      just wait for the timeout to expire, but it will not stop early
      in case of errors).

    NOTE: you still have to extend this class and implement the
    :py:meth:`verify` method to make it work. You can use
    :py:meth:`get_assertpy_context` to get the assertpy context you need
    to verify the assertion.

    """

    def __init__(
        self,
        tracer: TangoEventTracer | None = None,
        timeout: SupportsFloat = 0,
        early_stop: Callable[[ReceivedEvent, bool]] | None = None,
    ):
        """Create a new TracerAssertion instance.

        :param tracer: the TangoEventTracer instance to use for the assertion.
            If omitted, a default one will be used. **IMPORTANT**: if you
            don't pass a tracer instance, the event and subscription
            cleanup will be managed automatically during the setup phase,
            but if you pass a tracer the cleanup will be left to you!
        :param timeout: the timeout for the assertion to be verified.
            If omitted, a zero timeout is assumed. You can pass a numeric
            value to let this class create a timeout object for you, or
            you can pass your own timeout object (maybe shared with other
            assertions).
        :param early_stop: whether to stop the assertion early
            in case of errors. If omitted, the assertion (if not passing)
            will wait for the timeout to expire before failing.
        """
        self.tracer = tracer
        self.timeout: ChainedAssertionsTimeout = timeout
        self.early_stop = early_stop

    @property
    def tracer(self) -> TangoEventTracer:
        """Get the tracer instance to use for the assertion.

        :return: the tracer instance to use for the assertion
        """
        return self._injected_tracer or self._on_the_fly_tracer

    @tracer.setter
    def tracer(self, value: TangoEventTracer | None) -> None:
        """Set the tracer instance to use for the assertion.

        :param value: the tracer instance to use for the assertion. If you
            pass None, an on-the-fly managed tracer will be created.
        """
        self._injected_tracer = value
        self._on_the_fly_tracer = (
            None if value is not None else TangoEventTracer()
        )

    def is_tracer_managed(self) -> bool:
        """Check if the used tracer is managed by the assertion.

        :return: True if the tracer is managed by the assertion, False
            otherwise.
        """
        return self._injected_tracer is None

    @property
    def timeout(self) -> SupportsFloat:
        """Get the timeout for the assertion to be verified.

        :return: the timeout for the assertion to be verified
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: SupportsFloat) -> None:
        """Set the timeout for the assertion to be verified.

        This setter ensures the timeout is a chained timeout object
        (so eventual multiple calls of :py:meth:`get_assertpy_context` will
        share the same timeout). If you pass a numeric value, a timeout
        object will be created for you, otherwise you can pass your own
        timeout object and maybe also share it with other assertions.

        :param value: the timeout for the assertion to be verified
        """
        self._timeout = ChainedAssertionsTimeout.get_timeout_object(value)

    def setup(self) -> None:
        """Clean up an eventual managed tracer instance.

        If the tracer is managed by the assertion, the cleanup will be
        handled automatically during the setup phase.

        Please, override this and subscribe to the events you need to
        verify the assertion.
        """
        if self.is_tracer_managed():
            self._on_the_fly_tracer.unsubscribe_all()
            self._on_the_fly_tracer.clear_events()

    def get_assertpy_context(self) -> Any:
        """Get the assertpy context to use for the assertion.

        Use this method to access a valid assertpy context that already
        includes: the tracer instance, the timeout and the early stop
        condition. Multiple calls of this method will share the same
        timeout object.

        :return: the assertpy context to use for the assertion
        """
        return (
            assert_that(self.tracer)
            .described_as(self.describe_assumption())
            .within_timeout(self.timeout)
            .with_early_stop(self.early_stop)
        )
