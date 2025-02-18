"""A generic action on the System Under Test (SUT)."""

import abc
import logging
from dataclasses import dataclass
from typing import SupportsFloat

from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout


@dataclass
class SUTActionLastExecutionParams:
    """The parameters from the last action execution.

    This class contains the parameters that were passed to the
    :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`
    method the last time the action was executed.

    The parameters are:

    - the timeout for the postconditions verification, automatically
      converted to a
      :py:class:`ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`
      object
    - a flag that tells if preconditions should be verified
    - a flag that tells if postconditions should be verified
    """  # pylint: disable=line-too-long # noqa: E501

    postconditions_timeout: ChainedAssertionsTimeout = (
        ChainedAssertionsTimeout(0)
    )
    """The timeout for the postconditions verification."""

    verify_preconditions: bool = True
    """True if the preconditions should be verified, False otherwise."""

    verify_postconditions: bool = True
    """True if the postconditions should be verified, False otherwise."""

    def as_dict(self) -> dict:
        """Return the object as a dictionary.

        :return: The object as a dictionary.
        """
        return {
            "postconditions_timeout": self.postconditions_timeout,
            "verify_preconditions": self.verify_preconditions,
            "verify_postconditions": self.verify_postconditions,
        }

    @staticmethod
    def from_params(
        postconditions_timeout: SupportsFloat = 0,
        verify_preconditions: bool = True,
        verify_postconditions: bool = True,
    ) -> "SUTActionLastExecutionParams":
        """Create a new instance from the parameters.

        It automatically creates the timeout object from the given
        numerical value.

        :param postconditions_timeout: The timeout for the postconditions
            verification. By default, the timeout is 0s.
        :param verify_preconditions: True if the preconditions should be
            verified, False otherwise. By default, the preconditions are
            verified.
        :param verify_postconditions: True if the postconditions should be
            verified, False otherwise. By default, the postconditions are
            verified.

        :return: A new instance of the class.
        """
        return SUTActionLastExecutionParams(
            postconditions_timeout=ChainedAssertionsTimeout.get_timeout_object(
                postconditions_timeout
            ),
            verify_preconditions=verify_preconditions,
            verify_postconditions=verify_postconditions,
        )


class SUTAction(abc.ABC):
    """A generic action on the System Under Test (SUT).

    This class is the base class for the
    :py:mod:`~ska_integration_test_harness.core.actions` framework and
    it provides an empty shell for defining a generic interaction with
    the SUT.

    An action is a self-contained operation that can be executed with
    the :py:meth:`execute` method. An action is supposed to be made of:

    - A core procedure that acts on the SUT
      (method :py:meth:`execute_procedure`, the only compulsory extension
      point)
    - The verification of some preconditions before the procedure is executed
      (method :py:meth:`verify_preconditions`, optional extension point)
    - The verification of some postconditions after the procedure is executed
      and an eventual synchronisation with the SUT state within a timeout
      (method :py:meth:`verify_postconditions`, optional extension point)
    - A setup phase that prepares the action to be executed and resets
      any internal resources (method :py:meth:`setup`, optional extension
      point)
    - A name and a brief description of the action (methods :py:meth:`name`
      and :py:meth:`description`, optional extension points)

    **How to use an action as an end user**: An end user can use actions
    simply by creating an instance of the action and calling the
    :py:meth:`execute` method. The action will be executed, and the
    preconditions and postconditions will be verified. The execution
    can be repeated as many times as the user wants, given the
    preconditions are satisfied. Optionally, the user can also:

    - use a timeout for the postconditions verification by passing the
      ``timeout`` parameter to the :py:meth:`execute` method
      (by default it is 0s, and to be working who developed the action
      should have implemented the postconditions
      verification within a timeout)
    - disable the verification of the preconditions or postconditions
      by passing the flags ``verify_preconditions``
      and ``verify_postconditions`` to the :py:meth:`execute` method
    - disable the logging messages generated by the action by calling
      :py:meth:`set_logging` with the flag ``enable_logging`` set to False

    **How to extend an action**: An action can be extended by subclassing
    it and overriding the extension points. The only compulsory extension
    point is the :py:meth:`execute_procedure` method. The other extension
    points are optional and can be used to add custom preconditions,
    postconditions, setup, name, and description.

    **Extension and usage example**:

    .. code-block:: python

        from ska_integration_test_harness.core.actions import SUTAction

        # define a new action
        class MyAction(SUTAction):

            def setup(self):  # optional
                super().setup() # always call the superclass

                # e.g., reset a tracer, clear the events
                # subscribe to the attributes, etc.
                # ...

            def execute_procedure(self): # compulsory
                # (compulsory) act on the SUT

                # e.g., run some kind of interaction algorithm to reach
                # a certain state
                # ...

            # optional
            def verify_preconditions(self, timeout: SupportsFloat = 0):
                # always call the superclass
                super().verify_preconditions(timeout)

                # e.g., check that the device is in the desired state
                # within the timeout using the tracer
                # ...

        # execute the action and verify the postconditions within 10s
        action = MyAction()
        action.execute(postconditions_timeout=10)

    **NOTE for those who extend this class**:
    When you extend this class, always
    think about the value and semantic meaning. An action is supposed to be
    some meaningful procedure that acts on the SUT; it's a self-contained
    piece of business logic, so choose a meaningful class name, write a
    good docstring, and provide a meaningful short description.
    Since an action implementation will likely not be unit tested code,
    prioritise clarity and readability. Think also about reusability:
    if you find yourself creating several actions that are very similar,
    consider refactoring the common logic into a superclass or implementing
    a single (possibly unit tested) parametrised action.
    """

    def __init__(self) -> None:
        """Initialize the action.

        By default, the action logs the execution messages.
        """
        super().__init__()

        self.logger = logging.getLogger(self.__class__.__name__)
        """The logger for the action."""

        # enable logging
        self.logger.setLevel(logging.INFO)
        self.set_logging(True)

        self._last_execution_params = SUTActionLastExecutionParams()
        """Parameters passed the last time :py:meth:`execute` was called."""

    # ------------------------------------------------------------------
    # ENTRY POINTS FOR EXTERNAL USERS & UTILITIES

    def execute(
        self,
        postconditions_timeout: SupportsFloat = 0,
        verify_preconditions: bool = True,
        verify_postconditions: bool = True,
    ) -> None:
        """Execute the action and verify the postconditions.

        This method is the entry point for the user to execute the action.
        An execution of an action consists of the following steps:

        1. :py:meth:`setup` is called to prepare the action to be executed
           (and reset eventual internal resources).
        2. :py:meth:`verify_preconditions` is called to check if the
            preconditions are satisfied. If the preconditions are not
            satisfied, an exception is raised.
        3. :py:meth:`execute_procedure` is called to act on the SUT.
        4. :py:meth:`verify_postconditions` is called to check if the
            postconditions are satisfied (within the given ``timeout``).
            If the postconditions are not satisfied, an exception is raised.

        An action is supposed to be executable multiple times, given the
        preconditions are satisfied.

        The user can pass a ``timeout`` to the method to set a timeout
        for the postconditions verification. By default, the timeout is 0s.

        Through the ``verify_preconditions`` and
        ``verify_postconditions`` flags, the user can decide if the
        preconditions and postconditions should be verified. By default, both
        preconditions and postconditions are verified.

        :param postconditions_timeout: The timeout for the
            postconditions verification. By default, the timeout is 0s.
            You can pass a float or an integer, or also a
            :py:class:`ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`
            object. If you pass a numerical value, internally it is
            converted into an object to make it be "shared by default"
            inside the action.
            The timeout will start before verifying the postconditions. If you
            want to start it before, you should create the timeout object
            by yourself and pass it already started.
        :param verify_preconditions: True if the preconditions should be
            verified before executing the action, False otherwise. By default,
            the preconditions are verified.
        :param verify_postconditions: True if the postconditions should be
            verified after executing the action, False otherwise. By default,
            the postconditions are verified.
        :raises: AssertionError if the preconditions or postconditions are
            not satisfied. Additional exceptions can be raised by the
            :py:meth:`execute_procedure` method if the action fails.
        """  # pylint: disable=line-too-long # noqa: E501 # noqa: DAR402
        # store locally the last execution parameters
        self._last_execution_params = SUTActionLastExecutionParams.from_params(
            postconditions_timeout=postconditions_timeout,
            verify_preconditions=verify_preconditions,
            verify_postconditions=verify_postconditions,
        )

        # setup and the action and prepare it to be executed
        self.logger.info(
            "Executing action %s: %s "
            "(verify_preconditions=%s, verify_postconditions=%s)",
            self.name(),
            self.description(),
            verify_preconditions,
            verify_postconditions,
        )
        self.setup()

        # verify the preconditions
        if verify_preconditions:
            self.verify_preconditions()

        # execute the action
        self.execute_procedure()

        # ensure the timeout is started
        self._last_execution_params.postconditions_timeout.start()

        # verify the postconditions
        if verify_postconditions:
            self.logger.info(
                "Action %s: procedure executed successfully. "
                "Verifying postconditions (within a %s seconds timeout)...",
                self.name(),
                float(postconditions_timeout),
            )
            self.verify_postconditions(
                # pass the timeout (as an object)
                timeout=self._last_execution_params.postconditions_timeout
            )

        # successful completion
        self.logger.info(
            "Action %s: execution completed successfully",
            self.name(),
        )

    def set_logging(self, enable_logging: bool) -> None:
        """Enable or disable logging for the action.

        Enable or disable the logging messages the action generates during
        its execution. By default, logging is enabled.

        TODO: should this be a runtime configuration or a class-level
        configuration?

        :param enable_logging: True if the action should log the execution,
            False otherwise.
        """
        self.logger.disabled = not enable_logging

    def is_logging_enabled(self) -> bool:
        """Check if the logging is enabled for the action.

        :return: True if the action logs the execution, False otherwise.
        """
        return not self.logger.disabled

    # ------------------------------------------------------------------
    # EXTENSION HOOKS - ACTION EXECUTION STEPS

    def setup(self) -> None:
        """Set up the action (**optional extension point**).

        This method is called before the action is executed and
        any assertion is verified. It should set up action resources
        in a way such that all the preconditions can be verified,
        the action's procedure executed, and the postconditions
        verified.

        **HOW TO EXTEND**: Override this method in a subclass to add
        custom setup. Always call the superclass method when
        overriding this method. Some good practices if you override
        this method are:

        - make it be idempotent
        - after this method termination, the user may be able to assume
          the action instance is ready to verify preconditions and
          execute the procedure. Make it capable of resetting any kind
          of resources such as tracers, timeouts, etc.
        - always call the superclass method
        - in the docstring of the method, specify the resources that
          are set up (and briefly recap also what is done by superclasses,
          potentially referencing the superclasses method docstring)
        """

    def verify_preconditions(self) -> None:
        """Verify the preconditions (**optional extension point**).

        This method is called before the action is executed. It should
        verify that all the system in the state required by the action.
        If the preconditions are not satisfied, the method should raise
        an exception.

        **HOW TO EXTEND**: Override this method in a subclass to add
        custom preconditions. Always call the superclass method when
        overriding this method. You can assume
        :py:meth:`setup` has been called before this method. Some good
        practices if you override this method are:

        - make it be idempotent
        - always call the superclass method
        - try to put here only assertions that are fast to compute
          (i.e., without timeouts)
        - after this method termination, the user may be able to assume
          the system is in the state expected by the action to be executed
          correctly
        - in the docstring of the method, specify which precondition
          is verified (and briefly recap also what is done by superclasses,
          potentially referencing the superclasses method docstring)

        :raises: AssertionError if the preconditions are not satisfied.
        """  # noqa: DAR402

    @abc.abstractmethod
    def execute_procedure(self) -> None:
        """Act on the SUT (**compulsory extension point**).

        This method is the core of the action. It should execute the
        procedure of the action. The procedure is the sequence of
        commands, interactions, or any other operation that the action
        is supposed to perform on the SUT.

        **HOW TO EXTEND**: Override this method in a subclass to add
        custom procedures. If it exists, you may consider to call the
        superclass method but it is not compulsory. You can assume
        :py:meth:`setup` and :py:meth:`verify_preconditions` have been
        called before this method and :py:meth:`verify_postconditions`
        will be called after.

        - unless the action purpose is to embed conditional logic,
          assume the system is in the expected state defined by the
          preconditions through :py:meth:`verify_preconditions`
        - if the operation you are done is asynchronous, make this method
          terminate quickly and put the synchronisation logic in
          :py:meth:`verify_postconditions`
        - describe in the docstring what the action does (this method
          docstring, but also the class docstring)

        :raises: AssertionError if the action fails.
        """

    def verify_postconditions(self, timeout: SupportsFloat = 0) -> None:
        """Verify the postconditions of the action (**extension point**).

        This method is called after the action is executed. It should
        verify that the system reaches the state that is expected after
        a successful execution of the action.
        If the postconditions are not satisfied, the method should raise
        an exception. The verification should be done within the given
        timeout.

        **HOW TO EXTEND**: Override this method in a subclass to add
        custom postconditions. Always call the superclass method when
        overriding this method. You can assume
        :py:meth:`setup`, :py:meth:`verify_preconditions`, and
        :py:meth:`execute_procedure` have been called before this method
        Some good practices if you override this method are:

        - make it be idempotent
        - always call the superclass method
        - the assertions you put here can be slow (e.g., with timeouts) and
          can be intended as a way to synchronise with the system
          (e.g., waiting for a device to be ready)
        - after this method termination, the user may be able to assume
          the system is in the state expected by the action
        - in the docstring of the method, specify which postcondition
          is verified (and briefly recap also what is done by superclasses,
          potentially referencing the superclasses method docstring)
        - use the given timeout to set a timeout for the verification
          (if you need to wait for something to happen)

        :param timeout: the time in seconds to wait for the postconditions to
          be verified. If not specified, it defaults to 0.
        :raises: AssertionError if the postconditions are not satisfied.
        """

    # ------------------------------------------------------------------
    # EXTENSION HOOKS - ACTION DESCRIPTION

    def name(self) -> str:
        """A name to identify the action (**optional extension point**).

        This method returns a string that is used to identify the action
        in the logs and in the reports. The default implementation returns
        the class name.

        **HOW TO EXTEND**: Override this method in a subclass to provide
        a your custom name. Make it be just 1 or few more words. We don't
        really suggest to override this method unless you have a good reason
        to do so (override instead the :py:meth:`description` method).

        , override instead the :py:meth:`description` method.
        """
        return self.__class__.__name__

    def description(self) -> str:
        """A brief description of the action (**optional extension point**).

        This method returns a string that is used to describe very briefly
        what this action is supposed to do in the logs and in the reports.
        The default implementation returns an empty string.

        **HOW TO EXTEND**: Override this method in a subclass to provide
        a your custom description. Make it be a single small sentence
        that describes the action semantically
        (e.g., "Bring the telescope in X state").
        """
        return ""
