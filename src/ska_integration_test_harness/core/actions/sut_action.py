"""A generic action on the System Under Test (SUT)."""

import abc
import logging


class SUTAction(abc.ABC):
    """A generic action on the System Under Test (SUT).

    This class is the base class for a framework for defining operations
    on the System Under Test (SUT). An action is supposed to be any kind of
    operation that can be performed on the SUT, such as a procedure, a
    command, or a generic interaction.

    We provide this because we assume that a wide enough testing
    operations have the following common features:

    - the core part is a procedure (e.g.¸ a sequence of one or more commands
    but also a sequence of generic interaction, mostly with Tango devices
    but not necessarily)
    - to be executed, they may assume some preconditions (none by default)
    - after the procedure is executed, they may guarantee some postconditions
    (none by default)
    - they have a name (by default, the class name) and a brief semantic
    description of the operation (by default, nothing)
    - they may be run several times, given the preconditions are satisfied
    - the user may want to log their execution

    **How to use an action as an end user**: An end user can use actions
    simply by creating an instance of the action and calling the
    :py:meth:`execute` method. The action will be executed, and the
    preconditions and postconditions will be verified. The execution
    can be repeated as many times as the user wants, given the
    preconditions are satisfied. Example:

    .. code-block:: python

        action = MyAction()
        action.execute()

    **How to extend an action**: An action can be extended by subclassing
    it and overriding some of the extension points. The extension points are:

    - :py:meth:`setup`: set up the action (optional)
    - :py:meth:`verify_preconditions`: verify the preconditions (optional)
    - :py:meth:`execute_procedure`: act on the SUT (**compulsory**)
    - :py:meth:`verify_postconditions`: verify the postconditions (optional)
    - :py:meth:`name`: a name to identify the action (optional)
    - :py:meth:`description`: a brief description of the action (optional)

    As you may guess, the first four extension points are the steps of
    the action execution. The last two extension points are used to
    identify and describe the action in the logs and in the reports. Example:

    # TODO: add example

    # TODO: add logging mechanism
    """

    def __init__(self, enable_logging: bool = True) -> None:
        """Initialize the action.

        :param enable_logging: True if the action should log the execution,
            False otherwise. By default, logging is enabled.
        """
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.set_logging(enable_logging)

    # ------------------------------------------------------------------
    # ENTRY POINTS FOR EXTERNAL USERS

    def execute(
        self,
        verify_preconditions: bool = True,
        verify_postconditions: bool = True,
    ) -> None:
        """Execute the action and verify the postconditions.

        This method is the entry point for the user to execute the action.
        An execution of an action is a sequence of steps:

        1. **setup**: set up the action
        2. **verify preconditions**: check that the system is in the state
           expected by the action
        3. **execute procedure**: act on the SUT
        4. **verify postconditions**: check that the system is in the state
           expected after the action and eventually synchronize with the
           system

        An action can be executed several times, given the preconditions
        are satisfied.

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
                "Verifying postconditions...",
                self.name(),
            )
            self.verify_postconditions()

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
          are set up (and briefly recap also what is done by superclasses)
        - if you think the method may be extended by your own subclasses,
          put in the docstring a reference to this method docstring
          (e.g., TODO: add example)
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
          is verified (and briefly recap also what is done by superclasses)
        - if you think the method may be extended by your own subclasses,
          put in the docstring a reference to this method docstring
          (e.g., TODO: add example)

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
        custom procedures. If you think is useful, you are encoruaged
        to call the superclass method. You can assume
        :py:meth:`setup` and :py:meth:`verify_preconditions` have been
        called before this method. Some good practices if you override
        this method are:

        - after this method termination, the user may be able to assume
          the system is going to be in the state expected by the action
          after the postconditions are verified
        - TODO: add more

        :raises: AssertionError if the action fails.
        """

    def verify_postconditions(self) -> None:
        """Verify the postconditions of the action (**extension point**).

        This method is called after the action is executed. It should
        verify that the system is in the state expected by the action.
        If the postconditions are not satisfied, the method should raise
        an exception.

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
          is verified (and briefly recap also what is done by superclasses)
        - if you think the method may be extended by your own subclasses,
          put in the docstring a reference to this method docstring
          (e.g., TODO: add example)

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
        a your custom name. Make it be just 1 or few more words. Better
        if it is a single camel case word (e.g., "BringTelescopeInStateX").
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
