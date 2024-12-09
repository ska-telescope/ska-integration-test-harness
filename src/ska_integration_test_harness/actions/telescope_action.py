"""A generic action executed on the telescope and its subsystems."""

import abc
import logging
from typing import Any, Generic, TypeVar

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.state_change_waiter import (
    StateChangeWaiter,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)

# Define a generic type variable
T = TypeVar("T", bound=object)


class TelescopeAction(abc.ABC, Generic[T]):
    """A generic action executed on the telescope and its subsystems.

    An action is made by:

    - the action itself, which is the procedure that interacts
      with telescope subsystems (TMC, CSP, SDP, Dishes);
    - a termination condition, which is a set
      of expected events that should occur after the action is executed
      and which define a successful completion of the action;
    - a return type T, which is the type of the expected result
      of the action.


    This class is a template for such actions.

    **SUBCLASS AN ACTION**

    To create a new action, you create a subclass of ``TelescopeAction``
    and you implement the abstract methods
    :py:meth:`_action` and :py:meth:`termination_condition`.
    You define your business logic in the
    :py:meth:`_action` method and you define the termination condition
    in the :py:meth:`termination_condition` method, as a list of
    :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedEvent`
    instances (or subclasses).

    Here a few guidelines about the usage.

    - If your action needs some parameters, you can override the
      :py:meth:`__init__` method to accept them and store them as
      instance attributes.
    - When you implement an action you have to specify a return type.
      If your action doesn't return anything, you can specify ``None`` as
      return type.
    - Even if the action has no termination condition,
      you should still specify that by returning an empty list of expected
      events in the :py:meth:`termination_condition` method.
    - If in your action you need to access the telescope
      instance, you can do it by using the attribute ``self.telescope``.
      If you need to log something (only if the logging policy is active),
      you can use the method :py:meth:`_log`. If for some reason you need,
      you can also access the internal configuration and the components.


    Usage example:

    .. code-block:: python

        from tango import DevState
        from ska_integration_test_harness.actions.telescope_action import (
            TelescopeAction
        )
        from ska_integration_test_harness.actions.expected_events import (
            ExpectedStateChange
        )


        # create an action that returns nothing
        # and has no termination condition. It takes a parameter through.
        class MyAction(TelescopeAction[None]):
            def __init__(self, my_parameter: int):
                super().__init__()
                self.my_parameter = my_parameter

            def _action(self):
                # your business logic here
                pass

            def termination_condition(self):
                return []

        # create an action that - if necessary - runs
        # a certain Tango command on TMC central node and terminates
        # when that device reaches a certain state. The action then
        # returns true or false depending if the command was necessary or not.
        # Some further logging is done if the command wasn't necessary.
        class CentralNodeMoveToOn(TelescopeAction[bool]):
            def _action(self):
                if self.telescope.tmc.central_node.State != DevState.ON:
                    self.telescope.tmc.central_node.On()
                    return True

                self._log(
                    "Central node is already ON. No need to run the command."
                )
                return False

            def termination_condition(self):
                return [
                    ExpectedStateChange(
                        device=self.telescope.tmc.central_node,
                        attribute="State",
                        expected_value=DevState.ON,
                    )
                ]

    **EXECUTE AN ACTION**

    To run an action, you call the method :py:meth:`execute`. By default,
    when called the method:

    - the action is executed;
    - the termination condition is waited for until it occurs;
    - some logging is performed to report the execution beginning and end;
    - if the termination condition does not occur within a timeout,
      a TimeoutError is raised.


    Before calling the :py:meth:`execute` method, you can customise some
    configurations of the action:

    - you can change the timeout for the termination condition by calling
      the method :py:meth:`set_termination_condition_timeout` and passing
      the new timeout;
    - you can execute the action without waiting for the termination condition
      by calling the method :py:meth:`set_termination_condition_policy`
      and passing ``False`` as argument;
    - you can deactivate the logging policy by calling the method
      :py:meth:`set_logging_policy` and passing ``False`` as argument.


    **NOTE**: An already configured action can be executed multiple times.

    Usage example:

    .. code-block:: python

        # create an instance of the action
        action = MyAction(my_parameter=42)

        # [optional] customise the timeout for the termination condition
        action.set_termination_condition_timeout(10)

        # [optional] execute the action without waiting for the
        # termination condition to occur
        action.set_termination_condition_policy(False)

        # [optional] deactivate the logging policy
        action.set_logging_policy(False)

        # execute the action
        action.execute()

        # execute the action again
        action.execute()

    **RATIONALE AND INSPIRATIONS**

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

    def __init__(self) -> None:
        """Initialise the action, with default configurations and tools."""
        super().__init__()

        # ----------------------------------------------------------------
        # Action internal tools

        self.telescope = TelescopeWrapper()
        """The telescope instance, which you can use to access all the
        subsystem devices (TMC, CSP, SDP, Dishes)."""

        self._state_change_waiter = StateChangeWaiter()
        """The state change waiter, which is used to wait for the
        termination condition to occur."""

        self._logger = logging.getLogger(__name__)
        """A logger to display messages during the action execution"""

        # ----------------------------------------------------------------
        # Action data

        self._last_execution_result: T | None = None
        """The result of the last execution of the action."""

        # ----------------------------------------------------------------
        # Action configurations

        self.termination_condition_timeout: float = (
            self.telescope.actions_default_timeout
        )
        """The timeout for the termination condition (in seconds).

        It defaults to the one specified in the telescope wrapper class
        (**at the moment of the action creation**).
        """

        self.wait_termination: bool = True
        """If True, the termination condition will be waited for."""

        self.do_logging = True
        """If True, the action will log its execution beginning and end."""

    # ----------------------------------------------------------------
    # Configurations setters

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

    def set_logging_policy(self, do_logging: bool) -> None:
        """Change the policy for logging the action.

        If you call this method with ``do_logging=False``, the action
        will not log its execution beginning and end. If you call this
        method with ``do_logging=True``, the action will log its execution
        beginning and end.

        :param do_logging: If True, the action will log its execution
            beginning and end. If False, it will not.
        """
        self.do_logging = do_logging

    # ----------------------------------------------------------------
    # Actions execution & result getter

    def get_last_execution_result(self) -> T | None:
        """Get the result of the last execution of the action (if any).

        :return: The result of the last execution of the action (if any).
        """
        return self._last_execution_result

    def execute(self) -> Any | None:
        """Execute the action.

        By default, when called the method:

        - the action is executed;
        - the termination condition is waited for until it occurs;
        - some logging is performed to report the execution beginning and end;
        - if the termination condition does not occur within a timeout,
          a TimeoutError is raised.

        Before calling the :py:meth:`execute` method, you can customise some
        configurations of the action:

        - you can change the timeout for the termination condition by calling
          the method :py:meth:`set_termination_condition_timeout` and passing
          the new timeout;
        - you can execute the action without waiting
          for the termination condition
          by calling the method :py:meth:`set_termination_condition_policy`
          and passing ``False`` as argument;
        - you can deactivate the logging policy by calling the method
          :py:meth:`set_logging_policy` and passing ``False`` as argument.

        **NOTE**: An already configured action can be executed multiple times.

        Usage example:

        .. code-block:: python

            # create an instance of the action
            action = MyAction(my_parameter=42)

            # [optional] customise the timeout for the termination condition
            action.set_termination_condition_timeout(10)

            # [optional] execute the action without waiting for the
            # termination condition to occur
            action.set_termination_condition_policy(False)

            # [optional] deactivate the logging policy
            action.set_logging_policy(False)

            # execute the action
            action.execute()

            # execute the action again
            action.execute()

        :raises TimeoutError: If the expected outcome does not occur
            within a timeout.
        """

        # Log the beginning of the action execution
        log_msg = "Starting action execution"
        if self.wait_termination:
            log_msg += (
                f" (wait_termination=True, "
                f"timeout={self.termination_condition_timeout})"
            )
        else:
            log_msg += " (wait_termination=False)"
        self._log(log_msg)

        if self.wait_termination:
            # Subscribe to the expected state changes
            self._state_change_waiter.reset()
            self._state_change_waiter.add_expected_state_changes(
                self.termination_condition()
            )

        # Execute the action and store the result
        self._last_execution_result = self._action()

        if self.wait_termination:
            # Wait for the expected state changes to occur within a timeout
            # or raise a TimeoutError

            try:
                self._state_change_waiter.wait_all(
                    self.termination_condition_timeout
                )
            except TimeoutError as e:
                self._log(
                    "TimeoutError while waiting for termination condition",
                    log_error=True,
                )
                raise e

        # Log the end of the action execution
        self._log("Action execution completed")

        # Return the result of the action
        return self.get_last_execution_result()

    # ----------------------------------------------------------------
    # Extension points

    @abc.abstractmethod
    def _action(self) -> Any | None:
        """The action executed by the command.

        Override this method to implement your business logic
        (i.e., your interaction with the SUT components). Remember
        you already have available the telescope instance
        as ``self.telescope`` (which you can use to access all the
        subsystem devices).

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
        so you can access the devices states and attributes and store
        some useful information to define the termination condition.

        Also remember that the termination condition is being waited *AFTER*
        the action procedure is executed. So, you can define
        a termination condition that is based on the action result
        (through the use opportune lambda functions based on the
        call of the action result getter ``get_last_execution_result``).

        :return: A list of expected events that define the termination
            condition of the action. They should be instances of
            :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedEvent`
            or subclasses, like the very useful
            :py:class:`tests.test_harness3.telescope_actions.expected_events.ExpectedStateChange`.
        """  # pylint: disable=line-too-long # noqa E501

    # ----------------------------------------------------------------
    # Action internal utilities

    def _log(self, message: str, log_error: bool = False) -> None:
        """Log a message during the action execution.

        This method logs a message during the action execution. The message
        is prefixed with the name of the action class. The logging is
        performed only if the attribute :py:attr:`do_logging` is set to
        ``True``.

        :param message: The message to log.
        :param log_error: If True, the message is logged as an error message.
        """
        if not self.do_logging:
            return

        if log_error:
            self._logger.error("%s: %s", self.__class__.__name__, message)
        else:
            self._logger.info("%s: %s", self.__class__.__name__, message)
