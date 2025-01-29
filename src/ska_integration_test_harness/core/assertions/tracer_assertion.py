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

    This class is a
    :py:class:`~ska_integration_test_harness.core.assertions.SUTAssertion`
    that is based on the events
    emitted by the TangoEventTracer. The assertion is event-based,
    so it needs to be configured with:

    - a valid tracer instance
    - a timeout for the assertion to be verified
    - an optional early stop condition

    The tracer instance and the timeout can be managed by the assertion
    itself, or injected from the outside. A managed tracer will be
    automatically cleared of events and subscriptions during the setup
    phase, while an injected tracer will be left untouched.
    A managed timeout will be re-generated as a new fresh timeout object
    during the setup phase, while an injected timeout will be left
    untouched.

    To make the tracer unmanaged, you can pass a custom tracer instance
    to the constructor. To make the timeout unmanaged, you can pass a
    custom timeout object to the constructor (if you pass a numeric value,
    the timeout object will be created for you and will be managed). Both
    the tracer and the timeout can be shared among multiple assertions
    (to share a timeout, check
    :py:class:`ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`
    ).

    NOTE: you still have to extend this class and implement the
    :py:meth:`verify` and the :py:meth:`describe_assumption`
    methods to make it work. In :py:meth:`verify` implementation you can use
    the  :py:meth:`get_assertpy_context` to get the assertpy context you need
    to verify the assertion.

    **Usage Example**:

    .. code-block:: python

        from ska_integration_test_harness.core.assertions import (
            TracerAssertion
        )

        class MyAssertion(TracerAssertion):

            def verify(self):
                # your verification code here
                # - use get_assertpy_context to get the assertpy context
                #   (already configured with the tracer, the timeout and
                #   the early stop condition)
                # - use the assertpy context to verify the assertion
                #   (you can store it in a variable if you need to chain
                #   dynamically multiple assertions - e.g., in a for loop)
                context = get_assertpy_context()

                context.has_change_event_occurred(
                    "my/device/1", "my_attr", 42
                ).has_change_event_occurred(
                    "my/device/2", "my_attr", 43, previous_value=42
                ).has_change_event_occurred(
                    "my/device/3", "my_attr", 44, previous_value=43
                )

        assertion = MyAssertion()

        # ---------------------------------------------------------------
        # simple verification within a timeout
        assertion.timeout = 5
        assertion.setup()
        assertion.verify()

        # ---------------------------------------------------------------
        # simple verification on the current events on a given
        # tracer instance (setup will NOT clear up the given instance!)
        assertion.tracer = my_tracer
        assertion.setup()
        assertion.verify()

        # ---------------------------------------------------------------
        # verification with an early stop condition
        assertion.tracer = None # This way the tracer will be managed
        assertion.early_stop = lambda event:
            "ERROR" in str(event.attribute_value)

        # ---------------------------------------------------------------
        # verification of this assertion and many others within a same
        # common timeout (setup will NOT clear up the timeout!)

        from ska_tango_testing.integration.assertions import (
            ChainedAssertionsTimeout
        )
        timeout = ChainedAssertionsTimeout(5)

        assertions = [assertion, MyOtherAssertion(), ...]

        for assertion in assertions:
            assertion.timeout = timeout
            # (potentially they could share also the same tracer instance)
            assertion.setup()
            assertion.verify()

    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(
        self,
        tracer: "TangoEventTracer | None" = None,
        timeout: SupportsFloat = 0,
        early_stop: Callable[[ReceivedEvent], bool] | None = None,
    ):
        """Create a new TracerAssertion instance.

        :param tracer: the TangoEventTracer instance to use for the assertion.
            If omitted, a default one will be used. **IMPORTANT**: if you
            don't pass a tracer instance, the event and subscription
            cleanup will be managed automatically during the setup phase,
            but if you pass a tracer the cleanup will be left to you!
        :param timeout: the timeout for the assertion to be verified.
            If omitted, a zero timeout is assumed. **IMPORTANT**: if you
            don't pass a timeout or you pass a numeric value, a timeout
            object will be created for you and managed automatically
            during the setup phase, but if you pass a timeout object the
            cleanup will be left to you!
        :param early_stop: whether to stop the assertion early
            in case of errors. If omitted, the assertion (if not passing)
            will wait for the timeout to expire before failing.
            (see :py:func:`ska_tango_testing.integration.assertions.with_early_stop`
            for more details)
        """  # pylint: disable=line-too-long # noqa: E501
        self.tracer = tracer
        self.timeout = timeout

        self.early_stop = early_stop
        """The early stop condition for the assertion.

        (see
        :py:func:`ska_tango_testing.integration.assertions.with_early_stop`
        for more details)
        """

    # --------------------------------------------------------------------
    # Tracer management

    @property
    def tracer(self) -> TangoEventTracer:
        """Get the tracer instance to use for the assertion.

        :return: the tracer instance to use for the assertion
        """
        return self._injected_tracer or self._managed_tracer

    @tracer.setter
    def tracer(self, value: "TangoEventTracer | None") -> None:
        """Set the tracer instance to use for the assertion.

        :param value: the tracer instance to use for the assertion. If you
            pass None, an on-the-fly managed tracer will be created.
        """
        if isinstance(value, TangoEventTracer):
            self._injected_tracer = value
            self._managed_tracer = None
        else:
            self._injected_tracer = None
            self._managed_tracer = TangoEventTracer()

    def is_tracer_managed(self) -> bool:
        """Check if the used tracer is managed by the assertion.

        :return: True if the tracer is managed by the assertion, False
            otherwise.
        """
        return self._injected_tracer is None

    # --------------------------------------------------------------------
    # Timeout management

    @property
    def timeout(self) -> ChainedAssertionsTimeout:
        """Get the timeout for the assertion to be verified.

        :return: the timeout for the assertion to be verified
        """
        return self._injected_timeout or self._managed_timeout

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
        if isinstance(value, ChainedAssertionsTimeout):
            # If the timeout is already a chained timeout, we just use it
            # and we don't manage it.
            self._injected_timeout = value
            self._managed_timeout = None
        else:
            # Otherwise, we create a new chained timeout object and we
            # manage it.
            self._injected_timeout = None
            self._managed_timeout = ChainedAssertionsTimeout(float(value))

    def is_timeout_managed(self) -> bool:
        """Check if the used timeout is managed by the assertion.

        :return: True if the timeout is managed by the assertion, False
            otherwise.
        """
        return self._injected_timeout is None

    # --------------------------------------------------------------------
    # Assertion lifecycle

    def setup(self) -> None:
        """Reset managed resources before the assertion is verified.

        The resources that can be managed are:

        - the tracer, which if managed will be cleared of events and
          subscriptions;
        - the timeout, which if managed will be re-generated as a new
          fresh object (which still needs to be started).

        Please, override this and subscribe to the events you need to
        verify the assertion.
        """
        if self.is_tracer_managed():
            self.tracer.unsubscribe_all()
            self.tracer.clear_events()

        if self.is_timeout_managed():
            # reset the timeout to its initial value
            self.timeout = self.timeout.initial_timeout

    def get_assertpy_context(self) -> Any:
        """Get the assertpy context to use for the assertion.

        Use this method to access a valid assertpy context that already
        includes: the tracer instance, the timeout and the early stop
        condition. Multiple calls of this method will share the same
        timeout object.

        You can use the returned context to verify the assertion. Example:

        .. code-block:: python

            # what you will probably call in your ``verify`` method
            # implementation
            self.get_assertpy_context().has_change_event_occurred(
                "my/device/1", "my_attr", 42
            )

            # or in a more sophisticated way...
            context = self.get_assertpy_context()
            for device, attr, value in [
                ("my/device/1", "my_attr", 42),
                ("my/device/2", "my_attr", 43),
                ("my/device/3", "my_attr", 44),
            ]:
                context.has_change_event_occurred(device, attr, value)



        :return: the assertpy context to use for the assertion
        """
        return (
            assert_that(self.tracer)
            .described_as(self.describe_assumption())
            .within_timeout(self.timeout)
            .with_early_stop(self.early_stop)
        )
