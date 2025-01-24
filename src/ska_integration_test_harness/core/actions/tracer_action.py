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
    events emitted by the
    :class:`ska_tango_testing.integration.TangoEventTracer`.
    Concretely, this action:

    - accept a set of pre-conditions and post-conditions, expressed as
      :py:class:`SUTAssertion` and :py:class:`TracerAssertion` instances;
    - has a common tracer for all post-condition assertions (and also
      for the pre-conditions, if they are event-based);
    - has an unique shared timeout for all post-condition assertions;
    - permits to add early stop conditions for the post-conditions.

    At the moment, the tracer and the timeout are managed exclusively by
    the action itself (i.e., this class takes care of creating the objects,
    resetting them and injecting them into the assertions), but in the
    future we could make them injectable from the outside (and so potentially
    shared in different actions).

    Usage example:

    TODO: add a usage example

    The :py:meth:`verify` method needs to be overridden in the subclasses
    to implement the actual action.
    """

    def __init__(
        self,
        enable_logging: bool = True,
        log_preconditions: bool = False,
        log_postconditions: bool = True,
    ) -> None:
        """Create a new TracerAction instance.

        :param enable_logging: whether to enable logging
            (default is True).
        :param log_preconditions: whether to log the preconditions when
            verifying them (default is False).
        :param log_postconditions: whether to log the postconditions
            when verifying them (default is True).
        """
        super().__init__(enable_logging=enable_logging)
        self._preconditions = []
        self._postconditions = []

        self.tracer = TangoEventTracer()
        self.set_timeout(0)
        self._early_stop = None

        self._log_preconditions = log_preconditions
        self._log_postconditions = log_postconditions

    # --------------------------------------------------------------------
    # Configure timeout, preconditions, postconditions and early stop

    @property
    def timeout(self) -> float:
        """The timeout value for the postconditions.

        NOTE: as timeout value, we intend the initial timeout value, not the
        remaining one (which at the moment is managed exclusively internally).

        :return: the timeout value for the postconditions.
        """
        return self._timeout.initial_timeout

    def set_timeout(self, timeout: float) -> "TracerAction":
        """Set the timeout value for the postconditions.

        This method sets the timeout value for the postconditions, and also
        resets the timeout object to the new value.

        :param timeout: the new timeout value.
        :return: the action itself, to allow chaining the calls.
        """
        self._timeout = ChainedAssertionsTimeout(timeout)

        # set the timeout for the postconditions
        for postcondition in self.postconditions:
            postcondition.timeout = self._timeout
        return self

    @property
    def preconditions(self) -> list[SUTAssertion]:
        """The preconditions of the action.

        The preconditions are the assertions that need to be verified before
        the action is executed, that guarantee that the system is in
        a state that supports the action.
        Use :py:meth:`add_preconditions` to add new
        preconditions. Eventual preconditions will use the same tracer.

        :return: the preconditions of the action.
        """
        return self._preconditions

    def add_preconditions(
        self, *preconditions: SUTAssertion, put_them_at_beginning: bool = False
    ) -> "TracerAction":
        """Add one or more preconditions to the action.

        Add more preconditions to the action, to be verified before the
        action is executed. The preconditions are verified in the order
        they are added, unless the ``put_them_at_beginning`` parameter is set
        in which case they are verified before the ones already existing.

        Try to add preconditions that terminate immediately. If a precondition
        requires a tracer, it will use the same tracer as the action.

        NOTE: to favour a fluent interface, this method and
        also :py:meth:`add_postconditions` return the action itself, so that
        you can chain the calls.

        Usage example:

        .. code-block:: python

            action = TracerAction().add_preconditions(
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
        # eventual preconditions with a tracer will use the same tracer
        for precondition in preconditions:
            if isinstance(precondition, TracerAssertion):
                precondition.tracer = self.tracer

        # concatenate them at the beginning or at the end
        if put_them_at_beginning:
            self._preconditions = list(preconditions) + self._preconditions
        else:
            self._preconditions.extend(preconditions)

        return self

    @property
    def postconditions(self) -> list[TracerAssertion]:
        """The postconditions of the action.

        The postconditions are the assertions that need to be verified after
        the action is executed, that guarantee that the system is in
        the expected state after the action. Use :py:meth:`add_postconditions`
        to add new postconditions.

        Postconditions are all verified using the same tracer and they
        share the :py:meth:`timeout` value.

        :return: the postconditions of the action.
        """
        return self._postconditions

    def add_postconditions(
        self,
        *postconditions: TracerAssertion,
        put_them_at_beginning: bool = False
    ) -> "TracerAction":
        """Add one or more postconditions to the action.

        Add more postconditions to the action, to be verified after the
        action is executed. The postconditions are verified in the order
        they are added, unless the ``put_them_at_beginning`` parameter is set
        in which case they are verified before the ones already existing.

        Your postcondition tracer and timeout will be overridden by the
        action's tracer and timeout. The post-condition eventual early stop
        will be combined with the action's early stop.

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
        # all postconditions will use the same tracer and timeout
        # + combine early stop
        for postcondition in postconditions:
            postcondition.tracer = self.tracer
            postcondition.timeout = self._timeout
            postcondition.early_stop = TracerAction._combine_early_stop(
                postcondition.early_stop, self._early_stop
            )

        # add the postconditions at the beginning or at the end
        if put_them_at_beginning:
            self._postconditions = list(postconditions) + self._postconditions
        else:
            self._postconditions.extend(postconditions)

        return self

    @property
    def early_stop(self) -> Callable[[ReceivedEvent], bool] | None:
        """The early stop condition for the postconditions.

        This early stop condition is used to stop the verification of the
        postconditions before the timeout expires if some kind of error
        condition is detected. Each postcondition may have its own early
        stop condition, but this one is applied to all of them.

        Use :py:meth:`add_early_stop` to add a new early stop condition, which
        will be combined with the existing one (if any) using a logical OR.

        :return: the early stop condition for the postconditions.
        """
        return self._early_stop

    def add_early_stop(
        self, early_stop: Callable[[ReceivedEvent], bool]
    ) -> "TracerAction":
        """Add an early stop condition for the postconditions.

        Add a new early stop condition for the postconditions, which will be
        combined with the existing one (if any) using a logical OR.

        :param early_stop: the early stop condition to add.
        :return: the action itself, to allow chaining the calls.
        """
        self._early_stop = TracerAction._combine_early_stop(
            self._early_stop, early_stop
        )

        # apply the new early stop to all the postconditions
        for postcondition in self.postconditions:
            postcondition.early_stop = TracerAction._combine_early_stop(
                postcondition.early_stop, early_stop
            )
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
        self.tracer.unsubscribe_all()
        self.tracer.clear_events()

        # reset the timeout
        self.set_timeout(self.timeout)

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

        If specified in the initialisation, the preconditions will be logged
        (By default, they are not logged).

        :raises AssertionError: if one of the preconditions fails.
        """
        super().verify_preconditions()

        for precondition in self.preconditions:
            if self._log_preconditions:
                self.logger.info(
                    "Verifying precondition: %s",
                    precondition.describe_assumption(),
                )
            precondition.verify()

    def verify_postconditions(self):
        """Verify all the configured postconditions, within the given timeout.

        This method verifies all the postconditions configured for the action,
        one by one and in the given order. If one of the postconditions fails,
        the method raises an exception and stops the verification.

        NOTE: all the postconditions are verified within the given
        timeout, using the same tracer and considering the early stop
        condition.

        If specified in the initialisation, the postconditions will be logged
        (By default, they are logged).

        :raises AssertionError: if one of the postconditions fails.
        """
        super().verify_postconditions()

        for postcondition in self.postconditions:
            if self._log_postconditions:
                self.logger.info(
                    "Verifying postcondition: %s",
                    postcondition.describe_assumption(),
                )
            postcondition.verify()

    # (the verify method needs to be overridden, as it is abstract in the
    #  parent class)

    # --------------------------------------------------------------------
    # Internal utilities

    @staticmethod
    def _combine_early_stop(
        condition1: Callable[[ReceivedEvent], bool] | None,
        condition2: Callable[[ReceivedEvent], bool] | None,
    ) -> Callable[[ReceivedEvent], bool] | None:
        """Combine two early stop conditions using a logical OR.

        This method combines two early stop conditions using a logical OR,
        creating a new early stop condition that is satisfied if at least
        one of the two conditions is satisfied. If one of the conditions is
        ``None``, the other one is returned as is.

        :param condition1: the first early stop condition.
        :param condition2: the second early stop condition.
        :return: the combined early stop condition.
        """
        # one of the conditions is None -> return the other one
        if condition1 is None:
            return condition2

        if condition2 is None:
            return condition1

        # both conditions are not None -> combine them
        def combined_early_stop(event: ReceivedEvent) -> bool:
            """A combination of two early stop conditions.

            :param event: the event to check.
            :return: whether the postconditions verification should stop.
            """
            return condition1(event) or condition2(event)

        return combined_early_stop
