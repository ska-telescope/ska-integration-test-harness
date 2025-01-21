"""An event-based action which uses TangoEventTracer to synchronise."""

import abc
from typing import Callable

from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout
from ska_tango_testing.integration.event import ReceivedEvent

from ..assertions.sut_assertion import SUTAssertion
from ..assertions.tracer_assertion import TracerAssertion
from .sut_action import SUTAction


class TracerAction(SUTAction, abc.ABC):
    """An event-based action which uses TangoEventTracer to synchronise.

    This class represents an action where the synchronisation is based on the
    events emitted by the TangoEventTracer. Concretely, this action:

    - represents the preconditions and the postconditions of the action
      as assertion objects TODO: add references to the classes
    - while the preconditions are generic assertions, the postconditions
      are event-based assertions, which are verified using a tracer and
      with a postcondition

    At the moment, the tracer and the timeout are managed exclusively by
    the action itself (i.e., this class takes care of creating the objects,
    resetting them and injecting them into the assertions), but in the
    future we could make them injectable from the outside (and so potentially
    shared in different actions).

    The :py:meth:`verify` method needs to be overridden in the subclasses
    to implement the actual action.
    """

    def __init__(
        self,
        postconditions_timeout: float = 0,
        preconditions: list[SUTAssertion] | None = None,
        postconditions: list[TracerAssertion] | None = None,
    ):
        """Create a new TracerAction instance.

        :param postconditions_timeout: the timeout value that you
            are going to wait for the postconditions to be verified. NOTE:
            the given timeout will **ALWAYS** override the one eventually set
            in the postconditions!
        :param preconditions: the list of preconditions that need to be
            verified before the action is executed.
        :param postconditions: the list of postconditions that need to be
            verified after the action is executed. NOTE: the given timeout
            will **ALWAYS** override the one given in the postconditions!
        """
        super().__init__()
        self.preconditions = []
        self.postconditions = []
        self.add_preconditions(*preconditions or [])
        self.add_postconditions(*postconditions or [])

        self.postconditions_timeout = postconditions_timeout
        self.tracer = TangoEventTracer()

        # self.early_stop = early_stop
        # :param postconditions_early_stop: an optional early stop condition
        # to be used during the postconditions verification.
        # If any event matches this predicate, the verification will
        # stop immediately. If the postconditions already have an early stop,
        # it will be combined with this one using a logical OR.

    # --------------------------------------------------------------------
    # Configure timeout, preconditions, postconditions and early stop

    @property
    def postconditions_timeout(self) -> float:
        """The timeout value for the postconditions.

        NOTE: as timeout value, we intend the initial timeout value, not the
        remaining one (which at the moment is managed exclusively internally).

        :return: the timeout value for the postconditions.
        """
        return self._timeout.initial_timeout

    @postconditions_timeout.setter
    def postconditions_timeout(self, value: float):
        """Set the timeout value for the postconditions.

        NOTE: as timeout value, we intend the initial timeout value, not the
        remaining one (which at the moment is managed exclusively internally).

        Every time you execute this action, you may expect this timeout to be
        reset to the given value.

        :param value: the timeout value for the postconditions.
        """
        self._timeout = ChainedAssertionsTimeout(value)

    def add_preconditions(
        self, *preconditions: SUTAssertion, put_them_at_beginning: bool = False
    ) -> "TracerAction":
        """Add one or more preconditions to the action.

        NOTE: to favour a fluent interface, this method and
        also :py:meth:`add_postconditions` return the action itself, so that
        you can chain the calls.

        Usage example:

        .. code-block:: python

            action = TracerAction(
                postconditions_timeout=10
            ).add_preconditions(
                SUTAssertion1(), SUTAssertion2(), # ...
            .add_postconditions(
                TracerAssertion1(), TracerAssertion2(), # ...
            )

        :param preconditions: the preconditions to add.
        :param put_them_at_beginning: whether to put the preconditions at the
            beginning of the list (default is False, i.e., append them at the
            end). If True, the preconditions will be verified before the
            ones already existing.
        :return: the action itself, to allow chaining the calls.
        """
        if put_them_at_beginning:
            self.preconditions = list(preconditions) + self.preconditions
        else:
            self.preconditions.extend(preconditions)

        return self

    def add_postconditions(
        self,
        *postconditions: TracerAssertion,
        put_them_at_beginning: bool = False
    ) -> "TracerAction":
        """Add one or more postconditions to the action.

        NOTE: to favour a fluent interface, this method and
        also :py:meth:`add_preconditions` return the action itself, so that
        you can chain the calls.

        Usage example:

        .. code-block:: python

            action = TracerAction(
                postconditions_timeout=10
            ).add_preconditions(
                SUTAssertion1(), SUTAssertion2(), # ...
            ).add_postconditions(
                TracerAssertion1(), TracerAssertion2(), # ...
            )

        :param postconditions: the postconditions to add.
        :param put_them_at_beginning: whether to put the postconditions at the
            beginning of the list (default is False, i.e., append them at the
            end). If True, the postconditions will be verified before the
            ones already existing.
        :return: the action itself, to allow chaining the calls.
        """
        # add the postconditions at the beginning or at the end
        if put_them_at_beginning:
            self.postconditions = list(postconditions) + self.postconditions
        else:
            self.postconditions.extend(postconditions)

        return self

    # --------------------------------------------------------------------
    # Lifecycle methods

    def setup(self):
        """Reset the tracer and the timeout, and setup the pre/post conditions.

        This setup method:

        - resets the tracer, unsubscribing all the events and clearing the
          event list;
        - resets the timeout to the initial value;
        - sets up the preconditions and the postconditions (also configuring
          the timeout for the postconditions and the tracer for the
          event-based assertions).
        """
        super().setup()

        # reset the tracer
        self._reset_tracer()

        # reset the timeout
        self._reset_timeout()

        # setup the preconditions
        for precondition in self.preconditions:
            precondition.setup()

        # setup the postconditions
        for postcondition in self.postconditions:
            postcondition.setup()

    def verify_preconditions(self):
        """Verify all the configured preconditions.

        This method verifies all the preconditions configured for the action,
        one by one and in the given order. If one of the preconditions fails,
        the method raises an exception and stops the verification.

        :raises AssertionError: if one of the preconditions fails.
        """
        super().verify_preconditions()

        for precondition in self.preconditions:
            precondition.verify()

    def verify_postconditions(self):
        """Verify all the configured postconditions, within the given timeout.

        This method verifies all the postconditions configured for the action,
        one by one and in the given order. If one of the postconditions fails,
        the method raises an exception and stops the verification.

        NOTE: all the postconditions are verified within the given

        :raises AssertionError: if one of the postconditions fails.
        """
        super().verify_postconditions()

        for postcondition in self.postconditions:
            postcondition.verify()

    # (the verify method needs to be overridden, as it is abstract in the
    #  parent class)

    # --------------------------------------------------------------------
    # Internal utilities

    def _reset_tracer(self):
        """Reset events and subscriptions and inject into the assertions.

        This method resets the tracer, unsubscribing all the events and
        clearing the event list, and injects the new object in all the
        postconditions and also in all the preconditions that are
        :py:class:`TracerAssertion` instances.
        """
        self.tracer.unsubscribe_all()
        self.tracer.clear_events()

        for precondition in self.preconditions:
            if isinstance(precondition, TracerAssertion):
                precondition.tracer = self.tracer

        for postcondition in self.postconditions:
            postcondition.tracer = self.tracer

    def _reset_timeout(self):
        """Reset the timeout to initial value and inject into the assertions.

        This method resets the timeout to the initial value and injects the
        new object in all the postconditions.
        """
        self._timeout = ChainedAssertionsTimeout(self.postconditions_timeout)

        for postcondition in self.postconditions:
            postcondition.timeout = self._timeout

    @staticmethod
    def _create_combined_early_stop(
        conditions: list[Callable[[ReceivedEvent], bool]]
    ) -> Callable[[ReceivedEvent], bool]:
        """Create a combined early stop condition from a list of conditions.

        This method creates a new early stop condition that is a combination
        of all the given conditions, using a logical OR.

        :param conditions: the list of conditions to combine.
        :return: the combined early stop condition.
        """

        def combined_early_stop(event: ReceivedEvent) -> bool:
            """A combination of multiple early stop conditions.

            :param event: the event to check.
            :return: whether the postconditions verification should stop.
            """
            return any(condition(event) for condition in conditions)

        return combined_early_stop

    @staticmethod
    def _apply_early_stop_to_tracer_conditions(
        postconditions: list[TracerAssertion],
        early_stop: Callable[[ReceivedEvent], bool],
    ) -> None:
        """Apply an early stop condition to a list of postconditions.

        This method applies the given early stop condition to all the
        postconditions, combining it with the one already set in the
        postconditions (if any) using a logical OR.

        :param postconditions: the postconditions to apply the early stop to.
        :param early_stop: the early stop condition to apply.
        """
        for postcondition in postconditions:
            if postcondition.early_stop is None:
                postcondition.early_stop = early_stop
            else:
                postcondition.early_stop = (
                    TracerAction._create_combined_early_stop(
                        [postcondition.early_stop, early_stop]
                    )
                )
