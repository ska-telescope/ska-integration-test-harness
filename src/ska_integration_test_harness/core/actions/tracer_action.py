"""An event-based action which uses TangoEventTracer to synchronise."""

import abc
from typing import Callable, SupportsFloat

from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout
from ska_tango_testing.integration.event import ReceivedEvent

from ..assertions.sut_assertion import SUTAssertion
from ..assertions.tracer_assertion import TracerAssertion
from .sut_action import SUTAction


class TracerAction(SUTAction, abc.ABC):
    """An event-based action which uses TangoEventTracer to synchronise.

    This class represents an action where the preconditions and postconditions
    have a strong dependency on the events emitted by the SUT, and so this
    class provides a structure to manage them.

    Concretely, this action:

    - Makes you define the preconditions and postconditions using
      respectively
      :py:class:`ska_integration_test_harness.core.assertions.SUTAssertion` and
      :py:class:`ska_integration_test_harness.core.assertions.TracerAssertion`
      objects (through the :py:meth:`add_preconditions` and
      :py:meth:`add_postconditions` methods).
    - Manages a :class:`ska_tango_testing.integration.TangoEventTracer` to
      trace the events emitted by the SUT and automatically makes all
      the preconditions and postconditions use the same tracer.
    - Manages a shared timeout for the postconditions, so all of them are
      verified within the same time interval.
    - Allows you to define early stop conditions for the postconditions,
      through the :py:meth:`add_early_stop` method (to read more about early
      stop conditions, see
      :py:func:`ska_tango_testing.integration.assertions.with_early_stop`).

    To do this, the class implements many of the lifecycle methods of the
    :py:class:`~ska_integration_test_harness.core.actions.SUTAction` class,
    except for the :py:meth:`execute_procedure` method, which is left to be
    implemented by the subclasses.

    This class is very useful if combined with built-in assertions like
    :py:class:`ska_integration_test_harness.core.assertions.AssertDevicesAreInState`
    and :py:class:`ska_integration_test_harness.core.assertions.AssertDevicesStateChanges`.

    **Usage example**:

    .. code-block:: python

        from ska_integration_test_harness.core.actions import TracerAction
        from ska_integration_test_harness.core.assertions import AssertDevicesAreInState
        from ska_integration_test_harness.core.assertions import AssertDevicesStateChanges

        # To use this class, you need to create a subclass and implement the
        # execute_procedure method.
        class IncrementAttributeBy2(TracerAction):
            def execute_procedure(self):
                # your action logic here to increment the attribute by 2

        # Then you can build action instances and add preconditions and
        # postconditions to them according to your needs.

        action = MyAction().add_preconditions(
            AssertDevicesAreInState(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=42
            ),
        ).add_postconditions(
            AssertDevicesStateChanges(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=43
            ),
            AssertDevicesAreInState(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=44
            ),
        )

        # execute the action within a timeout of 5 seconds
        action.execute(postconditions_timeout=5)

        # ---------------------------------------------------------------
        # alternatively, if you don't want also the pre and postconditions
        # logic in the action class, you can just use the constructor

        class IncrAttrByN(TracerAction):

            def __init__(self, device, attribute_name, n):
                super().__init__()
                self.device = device
                self.attribute_name = attribute_name
                self.n = n

                for incr in range(1, n+1):
                    self.add_postconditions(
                        AssertDevicesStateChanges(
                            devices=[self.device],
                            attribute_name=self.attribute_name,
                            custom_matcher=lambda event:
                                self.is_attr_incremented_by_N(event, incr)
                        )
                    )

            def setup(self):
                super().setup()

                # store the initial value of the attribute
                # (will be useful to verify the increments)
                self.initial_value = self.device.read_attribute(self.attribute_name).value

            def execute_procedure(self):
                # the action logic that increments the attribute by n

            # define a custom matcher to verify the attribute increments
            def is_attr_incremented_by_N(self, event, incr):
                return event.attribute_value == self.initial_value + incr


        action = IncrAttrByN(dev1, "attr1", 3)

        # (here we can still add more preconditions if needed)

        # execute (this time without a timeout)
        action.execute()

    **NOTE**: At the moment, the tracer is managed exclusively
    by the action itself. The timeout instead is potentially injectable
    from the outside as an object of type
    :py:class:`~ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`.

    **NOTE**: The action setters are chainable, so you can chain the calls to
    add preconditions and postconditions, set the timeout, etc. Example:

    .. code-block:: python

        # this is valid code
        MyTracerAction().add_preconditions(
            # ...
        ).add_postconditions(
            # ...
        ).execute(postconditions_timeout=10)

    **NOTE**: This kind of action is particularly useful when you have to
    create factories of base actions whose pre and post conditions are "enriched"
    or "customised" according to the context in which they are used.
    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(self) -> None:
        """Create a new TracerAction instance.

        Initially,

        - the preconditions and postconditions are empty,
        - the tracer is created and set up,
        - no early stop condition is set.

        Preconditions execution by default is not logged, while postconditions
        instead are logged. You can change this behaviour by setting the
        :py:attr:`log_preconditions` and :py:attr:`log_postconditions`
        boolean attributes.
        """
        super().__init__()
        self._preconditions = []
        self._postconditions = []
        self._early_stop = None

        self.tracer = TangoEventTracer()
        """The (managed) tracer instance to use for the pre/post conditions."""

        self.log_preconditions = False
        """Whether to log the preconditions when verifying them.

        Defaults to False.
        """

        self.log_postconditions = True
        """Whether to log the postconditions when verifying them.

        Defaults to True.
        """

    # --------------------------------------------------------------------
    # Configure timeout, preconditions, postconditions and early stop

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

        Postconditions are all verified using the ``timeout`` value
        from the :py:meth:`execute` method, and they all use the same tracer.

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

        To read more about what is an early stop condition, see
        :py:func:`ska_tango_testing.integration.assertions.with_early_stop`.

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
        - sets up the preconditions and the postconditions (also configuring
          the timeout for the postconditions and the tracer for the
          event-based assertions).
        """
        super().setup()

        # reset the tracer
        self.tracer.unsubscribe_all()
        self.tracer.clear_events()

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
            if self.log_preconditions:
                self.logger.info(
                    "Verifying precondition: %s",
                    precondition.describe_assumption(),
                )
            precondition.verify()

    def verify_postconditions(self, timeout: SupportsFloat = 0):
        """Verify all the configured postconditions, within the given timeout.

        This method verifies all the postconditions configured for the action,
        one by one and in the given order. If one of the postconditions fails,
        the method raises an exception and stops the verification.

        NOTE: all the postconditions are verified within the given
        timeout, using the same tracer and considering the early stop
        condition.

        If specified in the initialisation, the postconditions will be logged
        (By default, they are logged).

        :param timeout: the time in seconds to wait for the postconditions to
            be verified. If not specified, it defaults to 0. Potentially,
            it can be:

            - a number, specifying the timeout in seconds,
            - a :py:class:`~ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`
              object, potentially shared among multiple actions.

        :raises AssertionError: if one of the postconditions fails.
        """  # pylint: disable=line-too-long # noqa: E501
        # ensure the timeout is an object (shared or local)
        shared_timeout = ChainedAssertionsTimeout.get_timeout_object(timeout)
        shared_timeout.start()

        super().verify_postconditions(timeout=shared_timeout)

        # verify the postconditions within the timeout
        for postcondition in self.postconditions:
            if self.log_postconditions:
                self.logger.info(
                    "Verifying postcondition: %s",
                    postcondition.describe_assumption(),
                )

            # inject the timeout in the postcondition
            postcondition.timeout = shared_timeout

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
