"""A tool to wait a set of state changes from multiple Tango devices."""

from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration.tracer import TangoEventTracer

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.inputs.dish_mode import DishMode
from ska_integration_test_harness.inputs.pointing_state import PointingState

# from ska_tango_testing.integration.tracer import TangoEventTracer


class StateChangeWaiter:
    """A tool to wait for a set of state changes from multiple Tango devices.

    This class is used to wait for a set of state changes to occur
    on multiple Tango devices. You use this class by creating an
    instance of it, progressively adding state changes to wait for,
    and then calling the `wait_all` method to wait for all the state
    changes to occur (or for a timeout to occur). If all the state
    changes occur before the timeout, the execution continues, else
    it will be raised an exception.

    An instance of this class can be shared among multiple classes, so
    you can separate the responsibility of knowing what conditions
    to wait foreach group of devices (e.g., a TMC class may know what
    to wait for the TMC devices, and a CSP class may know what to wait
    for the CSP devices, etc.) and also move the `wait_all` call in a
    common orchestrator class (that doesn't need to know the details
    of what to wait for).

    Calling the method `reset` you will clear the list of expected
    state changes, so you can reuse the same instance for multiple
    actions.
    """

    def __init__(self) -> None:
        self.event_tracer = TangoEventTracer(
            {
                "obsState": ObsState,
                "cspSubarrayObsState": ObsState,
                "sdpSubarrayObsState": ObsState,
                "dishMode": DishMode,
                "pointingState": PointingState,
            }
        )
        self.pending_state_changes: list[ExpectedEvent] = []

    def add_expected_state_changes(
        self,
        state_changes: list[ExpectedEvent],
    ) -> None:
        """Add a list of expected state changes to wait for.

        :param state_changes: A list of expected state changes to wait for.
        """
        for expected_state_change in state_changes:
            self.pending_state_changes.append(expected_state_change)
            self.event_tracer.subscribe_event(
                expected_state_change.device,
                expected_state_change.attribute,
            )

    def _is_state_change_occurred(self, state_change: ExpectedEvent) -> bool:
        """Check if a state change occurred.

        :param state_change: The state change to check.

        :return: True if the state change occurred, False otherwise.
        """
        return (
            len(
                self.event_tracer.query_events(
                    predicate=state_change.event_matches
                )
            )
            > 0
        )

    def wait_all(self, timeout: int | float):
        """Wait for all the expected state changes to occur.

        :param timeout: The maximum time (in seconds) to wait for
            the state changes.

        :raises TimeoutError: If not all the expected state changes
            occurred within the timeout.
        """
        if not self.pending_state_changes:
            return

        try:

            shared_timeout_context = assert_that(
                self.event_tracer
            ).within_timeout(timeout)

            for state_change in self.pending_state_changes:
                shared_timeout_context = (
                    shared_timeout_context.has_change_event_occurred(
                        custom_matcher=state_change.event_matches,
                    )
                )

        except AssertionError as assertion_error:
            msg = (
                "Not all the expected events occurred within "
                f"a timeout of {timeout} seconds."
            )

            happened_state_changes = []
            not_happened_state_changes = []

            for state_change in self.pending_state_changes:
                if self._is_state_change_occurred(state_change):
                    happened_state_changes.append(str(state_change))
                else:
                    not_happened_state_changes.append(str(state_change))

            if happened_state_changes:
                msg += "\n\nThe following events occurred:\n"
                msg += "\n".join(happened_state_changes)

            if not_happened_state_changes:
                msg += "\n\nThe following events did not occur:\n"
                msg += "\n".join(not_happened_state_changes)

            # raise TimeoutError with the message and the assertion error
            raise TimeoutError(msg) from assertion_error

    def reset(self):
        """Clear the list of expected state changes."""
        self.event_tracer.unsubscribe_all()
        self.event_tracer.clear_events()
        self.pending_state_changes = []
