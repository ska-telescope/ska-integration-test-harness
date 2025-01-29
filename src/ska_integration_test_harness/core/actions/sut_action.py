"""A generic action on the System Under Test (SUT)."""

import abc
import logging
from typing import SupportsFloat


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
      and an eventual synchronization with the SUT state within a timeout
      (method :py:meth:`verify_postconditions`, optional extension point)
    - A setup phase that prepares the action to be executed and resets
      eventual internal resources (method :py:meth:`setup`, optional extension
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
      ``timeout`` parameter to the :py:meth:`execute` method (by default is 0s,
      and to be working who developed the action should have implemented
      the postconditions verification within a timeout)
    - disable the verification of the preconditions or postconditions
      by passing the flags ``verify_preconditions``
      and ``verify_postconditions`` to the :py:meth:`execute` method
    - disable the logging messages generated by the action by calling
      :py:meth:`set_logging` with the flag ``enable_logging`` set to False

    **How to extend an action**: An action can be extended by subclassing
    it and overriding the extensions points. The only compulsory extension
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
            def verify preconditions(self, timeout: SupportsFloat =0):
                # always call the superclass
                super().verify_preconditions(timeout)

                # e.g., check that the device is in the desired state
                # within the timeout using the tracer
                # ...

        # execute the action and verify the postconditions within 10s
        action = MyAction()
        action.execute(postconditions_timeout=10)

    **NOTE for who extends this class**: When you extend this class, always
    think about the value and semantic meaning. An action is supposed to be
    some meaningful procedure that acts on the SUT; it's a self-contained
    piece of business logic, so choose a meaningful class name, write a
    good docstring, and provide a meaningful short description.
    Since an action implementation will likely be not unit tested code,
    prioritise clarity and readability. Think also about reusability:
    if you find yourself creating several actions that are very similar,
    consider to refactor the common logic in a superclass or to implement
    an unique (possibly unit tested) parametrised action.
    """

    def __init__(self, enable_logging: bool = True) -> None:
        """Initialize the action.

        :param enable_logging: True if the action should log the execution,
            False otherwise. By default, logging is enabled.
        """
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        """The logger for the action."""

        self.logger.setLevel(logging.INFO)
        self.set_logging(enable_logging)

    # ------------------------------------------------------------------
    # ENTRY POINTS FOR EXTERNAL USERS

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
        :param verify_preconditions: True if the preconditions should be
            verified before executing the action, False otherwise. By default,
            the preconditions are verified.
        :param verify_postconditions: True if the postconditions should be
            verified after executing the action, False otherwise. By default,
            the postconditions are verified.
        :raises: AssertionError if the preconditions or postconditions are
            not satisfied. Additional exceptions can be raised by the
            :py:meth:`execute_procedure` method if the action fails.
        """  # noqa: DAR402
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

        # verify the postconditions
        if verify_postconditions:
            self.logger.info(
                "Action %s: procedure executed successfully. "
                "Verifying postconditions (within a %s seconds timeout)...",
                self.name(),
                float(postconditions_timeout),
            )
            self.verify_postconditions(timeout=postconditions_timeout)

        # successful completion
        self.logger.info(
            "Action %s: execution completed successfully",
            self.name(),
        )

    def set_logging(self, enable_logging: bool) -> None:
        """Enable or disable logging for the action.

        Enable or disable the logging messages the action generates during
        its execution. By default, logging is enabled.

        :param enable_logging: True if the action should log the execution,
            False otherwise.
        """
        self.logger.disabled = not enable_logging

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
          terminate quickly and put the synchronization logic in
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
          can be intended as a way to synchronize with the system
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
