"""A generic action executed over the telescope and its subsystems."""

import abc
from typing import Any

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.state_change_waiter import (
    StateChangeWaiter,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TelescopeAction(abc.ABC):
    """A generic action executed over the telescope and its subsystems.

    An action is made by:

    - the action itself, which is the procedure that interacts
        with telescope subsystems (TMC, CSP, SDP, Dishes);
    - a termination condition, which is a set
        of expected events that should occur after the action is executed
        and which define a successful completion of the action.

    This class is a template for such actions.

    To create a new action, you create a subclass of ``TelescopeAction``
    and you implement the abstract methods
    :py:meth:`_action` and :py:meth:`termination_condition`.
    You define your business logic in the
    :py:meth:`_action` method and you define the termination condition
    in the :py:meth:`termination_condition` method, as a list of
    :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedEvent`
    instances (or subclasses).

    To run an action, you call the method :py:meth:`execute`. The action
    is executed and the termination condition is waited for until a timeout.
    You can customize the timeout by calling the method
    :py:meth:`set_termination_condition_timeout`
    before calling the :py:meth:`execute` method.
    If you want, you can also execute the action without waiting for the
    termination condition to occur by calling the
    :py:meth:`set_wait_termination_policy`
    method (passing ``False`` as argument to deactivate the waiting).

    If your action needs some parameters, you can override the
    :py:meth:`__init__` method to accept them and store them as
    instance attributes.

    The same action can potentially be executed multiple times.

    This class is strongly inspired by the Command design pattern
    (https://refactoring.guru/design-patterns/command), since it abstracts
    a potentially complex action into a class, incapsulating and hiding
    the execution details of the action itself, such as having available
    a telescope instance and waiting for the termination condition to occur.
    Since it leaves you some methods to implement (that will instead
    be called by this class itself), it is also inspired
    by the Template Method design pattern
    (https://refactoring.guru/design-patterns/template-method).
    """  # pylint: disable=line-too-long # noqa E501

    DEFAULT_TERMINATION_CONDITION_TIMEOUT = 30
    """The default timeout for the termination condition (in seconds)."""

    def __init__(self) -> None:
        super().__init__()
        self.telescope = TelescopeWrapper()
        self._state_change_waiter = StateChangeWaiter()

        self.termination_condition_timeout = (
            self.DEFAULT_TERMINATION_CONDITION_TIMEOUT
        )
        self.wait_termination = True

    def set_termination_condition_timeout(self, timeout: int | float) -> None:
        """Change the timeout for the termination condition.

        The timeout is the maximum time to wait for the termination
        condition to occur. You can change it at any time before
        calling the :py:meth:`execute` method.

        :param timeout: The new timeout for the termination condition
            (in seconds).
        """
        self.termination_condition_timeout = timeout

    def set_termination_condition_policy(self, wait: bool) -> None:
        """Change the policy for waiting for the termination condition.

        If you call this method with ``wait=False``, the termination
        condition will not be waited for when calling the
        :py:meth:`execute` method. If you call this method with
        ``wait=True``, the termination condition will be waited for
        when calling the :py:meth:`execute` method.

        :param wait: If True, the termination condition will be waited
            for when calling the :py:meth:`execute` method. If False,
            the termination condition will not be waited for.
        """
        self.wait_termination = wait

    @abc.abstractmethod
    def _action(self) -> Any | None:
        """The action executed by the command.

        Override this method to implement your business logic
        (i.e., your interaction with the SUT components). Remember
        you already have available the telescope instance
        as ``self.telescope`` (which you can use to access all the
        subsystems devices).

        If you need to return something from the action, you can
        do it. Else you can also return nothing.

        :return: The result of the action (optional)
        """
        # TODO: make this class be a generic to permit to
        # specify the return type of the _action method

    @abc.abstractmethod
    def termination_condition(self) -> list[ExpectedEvent]:
        """The termination condition of the action.

        The termination condition is a list of expected events. Override
        this method to define the expected events that should occur. Remember
        that by default this method is called *BEFORE* the action is executed,
        so you can use the telescope instance to access the devices
        and get any information you need to define the termination condition.

        :return: A list of expected events that define the termination
            condition of the action. They should be instances of
            :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedEvent`
            or subclasses, like the very useful
            :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedStateChange`.
        """  # pylint: disable=line-too-long # noqa E501

    def execute(self) -> Any | None:
        """Execute the command.

        This method executes the command by performing the action
        and waiting for the expected outcome to occur. If the expected
        outcome does not occur within a timeout,
        a TimeoutError is raised. Before calling this method, you can
        customize the timeout for the termination condition by calling
        the method :py:meth:`change_timeout` and passing the new timeout.
        You can also execute the action without waiting for the
        termination condition by calling first the method
        :py:meth:`set_wait_termination_policy` and passing
        ``False`` as argument.

        :raises TimeoutError: If the expected outcome does not occur
            within a timeout.
        """

        if self.wait_termination:
            # Subscribe to the expected state changes
            self._state_change_waiter.reset()
            self._state_change_waiter.add_expected_state_changes(
                self.termination_condition()
            )

        # Execute the action
        res = self._action()

        if self.wait_termination:
            # Wait for the expected state changes to occur within a timeout
            # or raise a TimeoutError
            self._state_change_waiter.wait_all(
                self.termination_condition_timeout
            )

        return res
