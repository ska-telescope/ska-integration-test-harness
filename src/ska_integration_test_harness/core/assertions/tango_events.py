"""Assertions over Tango events."""

from dataclasses import dataclass
from typing import Any, Callable, SupportsFloat

import tango
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.event import ReceivedEvent
from ska_tango_testing.integration.query import (
    NStateChangesQuery,
    QueryWithFailCondition,
)

from .sut_assertion import SUTAssertionWTimeout


@dataclass
class ExpectedStateChange:
    """An expected state change event from a Tango device.

    This class represents an expected state change event from a Tango device.
    It can be used to define the state changes when you assert Tango events.

    It wraps over the :py:mod:`ska_tango_testing.integration` and, in fact,
    to be evaluated it needs a
    :py:class:`ska_tango_testing.integration.TangoEventTracer` instance
    and uses the queries mechanism.
    """

    device: tango.DeviceProxy | None
    """The device that is expected to change state."""

    attribute_name: str | None
    """The name of the attribute that is expected to change state."""

    attribute_value: Any | None
    """The attribute value you expect the attribute to change to."""

    previous_value: Any | None
    """The expected previous value of the attribute."""

    custom_matcher: Callable[[ReceivedEvent], bool] | None
    """An optional matcher to define further constraints on the event."""

    def describe(self) -> str:
        """Describe the expected state change.

        Describe the expected state change in a one-line human-readable format,
        including all the parameters the user choose to set.

        :return: A human-readable description of the expected state change.
        """
        desc = "ExpectedStateChange("

        if self.device:
            desc += f"device_name='{self._get_device_name()}, "

        if self.attribute_name:
            desc += f"attribute_name='{self.attribute_name}', "

        if self.attribute_value is not None:
            desc += (
                "attribute_value="
                f"{self._val_pretty_print(self.attribute_value)}, "
            )

        if self.previous_value is not None:
            desc += (
                "previous_value="
                f"{self._val_pretty_print(self.previous_value)}, "
            )

        if self.custom_matcher:
            desc += f"custom_matcher={self.custom_matcher.__name__}, "

        return desc + ")"

    def _get_device_name(self) -> str:
        """Get the device name from the expected state change.

        :return: The device name as a string.
        """
        return self.device.dev_name()

    @staticmethod
    def _val_pretty_print(value: Any) -> str:
        """Format the value for printing.

        :param value: The value to format.
        :return: The formatted value (if it is a string,
            it is wrapped in quotes).
        """
        if isinstance(value, str):
            return f"'{value}'"

        return value

    def to_query(self, timeout: SupportsFloat) -> NStateChangesQuery:
        """Convert the expected state change to a query.

        Convert the expected state change to a query that can be used to
        check if the event actually occurred.

        :return: A query that can be used to check if the event occurred.
        """
        return NStateChangesQuery(
            device_name=self.device,
            attribute_name=self.attribute_name,
            attribute_value=self.attribute_value,
            previous_value=self.previous_value,
            custom_matcher=self.custom_matcher,
            timeout=timeout,
        )

    def to_predicate(
        self, tracer: TangoEventTracer
    ) -> Callable[[ReceivedEvent], bool]:
        """Convert the expected state change to a predicate.

        Convert the expected state change to a predicate that can be used to
        check if the event actually occurred.

        :param tracer: The tracer to use for eventual previous
            values researches.
        :return: A predicate that can be used to check if the event occurred.
        """

        def predicate(event: ReceivedEvent) -> bool:
            """Checks if the event matches the defined parameters.

            This predicate uses the current tracer events for eventual
            previous values researches.

            :param event: The event to check.
            """
            return self.to_query(0.0).as_predicate(event, tracer.events)

        return predicate


@dataclass
class TracerSubscription:
    """A subscription that has to be done on the tracer."""

    device: tango.DeviceProxy
    """The device to subscribe to."""

    attribute_name: str
    """The attribute to subscribe to."""

    def subscribe(self, tracer: TangoEventTracer):
        """Subscribe to the attribute on the tracer.

        :param tracer: The tracer to subscribe to.
        """
        tracer.subscribe(self.device, self.attribute_name)

    def __eq__(self, value):
        """Check if the subscription is equal to another value."""
        return (
            isinstance(value, TracerSubscription)
            and self.device == value.device
            and self.attribute_name == value.attribute_name
        )


class AssertTangoEvents(SUTAssertionWTimeout):
    """An assertion that verifies the occurrence of Tango events.

    This assertion verifies that a set of expected state changes
    occurred on a Tango device, within a given timeout and without
    any unexpected events.

    TODO: describe better
    """

    def __init__(
        self,
        expected_state_changes: list[ExpectedStateChange],
        early_stop_events: list[ExpectedStateChange] | None = None,
        further_subscriptions: list[TracerSubscription] | None = None,
        assert_description: str = "",
        timeout: SupportsFloat = 0.0,
    ):
        """Create a new AssertTangoEvents instance.

        :param expected_state_changes: A list of expected state changes.
        :param early_stop_events: A list of events that, if they occur,
            stop the event tracing.
        :param further_subscriptions: A list of further subscriptions to do
            on the tracer (automatically foreach passed
            :py:class:`ExpectedStateChange` a subscription is done). Use
            this parameter to define further subscriptions that are needed.
        :param assert_description: The description of the assertion. It is
            optional and can be used to provide more context to the assertion.
            If you want to specify it, try to explain what this group of
            events represents to you.

        :param timeout: The timeout for the assertion.
        """
        super().__init__(timeout)
        self._expected_state_changes = expected_state_changes
        self._early_stop_events = early_stop_events or []
        self._further_subscriptions = further_subscriptions or []
        self._assert_description = assert_description

        # TODO: how can I solve the Event Enum issue? In many points of
        # the code I need to create event tracers/display events values, but
        # I would like to define this just once...
        self.tracer = TangoEventTracer()

    @property
    def expected_state_changes(self) -> list[ExpectedStateChange]:
        """Get the expected state changes.

        :return: The list of expected state changes.
        """
        return self._expected_state_changes.copy()

    @property
    def early_stop_events(self) -> list[ExpectedStateChange]:
        """Get the early stop events.

        :return: The list of early stop events.
        """
        return self._early_stop_events.copy()

    @property
    def tracer_subscriptions(self) -> list[TracerSubscription]:
        """The tracer subscriptions that need to be done."""

        # get the subscriptions from the expected state changes
        expected_events_subscriptions = self._get_subscriptions_from_events(
            self.expected_state_changes
        )

        # get the subscriptions from the early stop events
        early_stop_subscriptions = self._get_subscriptions_from_events(
            self.early_stop_events
        )

        # merge the two lists + the further subscriptions (removing duplicates)
        return self._remove_duplicates(
            expected_events_subscriptions
            + early_stop_subscriptions
            + self._further_subscriptions
        )

    @staticmethod
    def _get_subscriptions_from_events(
        events: list[ExpectedStateChange],
    ) -> list[TracerSubscription]:
        """Get the subscriptions from a list of events, excluding duplicates.

        :param events: The events to get the subscriptions from.
        :return: The subscriptions to do.
        """
        res = []
        for event in events:
            if event.device and event.attribute_name:
                sub = TracerSubscription(event.device, event.attribute_name)
                if sub not in res:
                    res.append(sub)
        return res

    @staticmethod
    def _remove_duplicates(ls: list) -> list:
        """Remove duplicates from a list.

        :param ls: The list to remove duplicates from.
        :return: The list without duplicates.
        """
        return list(set(ls))

    def setup(self):
        """Clean up the event tracer and subscribe to the events."""
        super().setup()

        # clean up the tracer subscriptions
        self.tracer.unsubscribe_all()
        self.tracer.clear_events()

        # subscribe to new events
        for subscription in self.tracer_subscriptions:
            subscription.subscribe(self.tracer)

    def _build_queries(self) -> dict[ExpectedStateChange, NStateChangesQuery]:
        """Build the queries to check if the events occurred.

        :return: The queries to check if the events occurred.
        """
        # get all the queries from the expected state changes
        all_queries = {
            event: event.to_query(self.timeout)
            for event in self.expected_state_changes
        }

        # decorate them with the early stop events
        for event in all_queries.keys():
            query = all_queries[event]

            # create a query with the fail condition foreach early stop event
            # and decorate it with the previous query
            for event in self.early_stop_events:
                query = QueryWithFailCondition(
                    query, event.to_predicate(self.tracer)
                )

            # update the query
            all_queries[event] = query

        return all_queries

    def verify(self):
        """Verify each of the expected events occurs within the timeout.

        If some events do not occur, raise an AssertionError. Ensure that
        the error message contains a description of all the expected events,
        marking foreach of them if they occurred or not. Display also
        the early stop events and the collected events.
        """
        super().verify()

        one_failed = False
        error_msg_lines = "Expected events:\n"

        for event, query in self._build_queries().items():
            # if a failure occurred, no more timeout for this query
            if one_failed:
                query.set_timeout(0)

            # evaluate the query
            self.tracer.evaluate_query(query)
            if query.succeeded():
                error_msg_lines += "- " + event.describe() + " - OK\n"
                continue

            # if the query failed, set the flag
            one_failed = True
            error_msg_lines += "- " + event.describe() + " - FAILED\n"

        if not one_failed:
            return

        # if at least one query failed, check also the early stop events
        error_msg_lines += "\nEarly stop events:\n"
        for early_stop_event in self.early_stop_events:
            early_stop_query = early_stop_event.to_query(0)
            self.tracer.evaluate_query(early_stop_query)
            if early_stop_query.succeeded():
                error_msg_lines += (
                    "- " + early_stop_event.describe() + " - OBSERVED (BAD)\n"
                )
            else:
                error_msg_lines += (
                    "- "
                    + early_stop_event.describe()
                    + " - NOT OBSERVED (OK)\n"
                )

        error_msg_lines += "\nCollected events:\n"
        for event in self.tracer.events:
            error_msg_lines += f"- {str(event)}\n"

        # raise the error
        self.fail(error_msg_lines)

    def describe_assumption(self) -> str:
        """I am assuming that a certain set of events occurs."""
        if self._assert_description:
            desc = self._assert_description
        else:
            desc = "A set of Tango events was expected to occur"

        if self.timeout > 0:
            desc += f" within {self._initial_timeout_value():.2f} seconds"
