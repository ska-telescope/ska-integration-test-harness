"""Compose a sequence of actions, under a same common timeout."""

from typing import SupportsFloat

from assertpy import assert_that
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout

from .sut_action import SUTAction


class SUTActionSequence(SUTAction):
    """Compose a sequence of actions, under a same common timeout.

    This class represents a sequence of
    :py:class:`ska_integration_test_harness.core.actions.SUTAction`
    instances grouped together in a sequence to be executed in order.
    The actions have the following properties:

    - Each action is a
      :py:class:`~ska_integration_test_harness.core.actions.SUTAction`
      instance, and can be executed within a timeout by calling
      :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`.
      The verification includes a setup, a verification of preconditions,
      the execution of the procedure, and a verification of postconditions
      (with an eventual synchronisation within the timeout).
    - You can build the sequence by adding actions with :py:meth:`add_actions`.
    - The sequence can be executed in the given order by calling
      :py:meth:`execute`. Every time you call the method, the
      sequence is executed from the beginning, within a shared timeout
      (an action remaining time for verifying postconditions is
      the remaining time left by the previous)
    - Optionally, you can override this class to add further global setup,
      precondition, or postcondition verification.
    """

    def __init__(self, enable_logging=True):
        # the list of actions in the sequence
        self._actions: list[SUTAction] = []

        # internal execution parameters for sequence
        self._shared_timeout = None
        self._verify_preconditions = True
        self._verify_postconditions = True

        super().__init__(enable_logging)

    @property
    def actions(self) -> list[SUTAction]:
        """The ordered list of actions in the sequence.

        :return: The list of actions in the sequence.
        """
        return self._actions

    def add_actions(self, *actions: SUTAction, put_them_at_beginning=False):
        """Add one or more actions to the sequence.

        :param actions: The actions to add to the sequence.
        :param put_them_at_beginning: If True, the actions are added
            at the beginning of the sequence.
        """
        if put_them_at_beginning:
            self._actions = list(actions) + self._actions
        else:
            self._actions += list(actions)

    def set_logging(self, enable_logging: bool):
        """Set the logging for this instance and for the whole sequence.

        This method sets the logging for this instance and for all the
        actions in the sequence. See
        :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.set_logging`
        for more details.

        :param enable_logging: If True, the logging is enabled for this
            instance and for all the actions in the sequence.
        """  # pylint: disable=line-too-long # noqa: E501

        super().set_logging(enable_logging)

        for action in self.actions:
            action.set_logging(enable_logging)

    def execute(
        self,
        postconditions_timeout: SupportsFloat = 0,
        verify_preconditions: bool = True,
        verify_postconditions: bool = True,
    ):
        """Execute the sequence of actions within a shared timeout.

        This method executes the sequence of actions in order, within a
        shared timeout. The timeout is started before the first action
        is executed and each action will essentially have access to the
        remaining time left by the previous actions.

        Each action executions happens respecting the usual
        :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`
        lifecycle. This sequence too follows the same lifecycle (so
        you can override to define a global setup, preconditions, or
        postconditions verification).

        Policies such as ``verify_preconditions`` and ``verify_postconditions``
        are applied to the whole sequence, but they also propagate to each
        action in the sequence, so use them wisely. TODO: see if we can/we
        need to make something better here.

        :param postconditions_timeout: The timeout for verifying postconditions
            of the whole sequence. The timeout is shared among all actions
            in the sequence. If not provided, the timeout is set to 0 (so
            each individual action postconditions should be verified
            immediately after the action execution).
        :param verify_preconditions: If True, the preconditions of this
            instance and of each action in the sequence are verified before
            the action execution.
        :param verify_postconditions: If True, the postconditions of this
            instance and of each action in the sequence are verified after
            the action execution.
        :raises: AssertionError if the preconditions or postconditions are
            not satisfied for this instance or for any of the actions.
            Additional exceptions can be raised by various failures internal
            to the actions.
        """  # noqa: DAR402
        # build an unique timeout object for the whole sequence
        # and ensure that the timeout is started
        self._shared_timeout = ChainedAssertionsTimeout.get_timeout_object(
            postconditions_timeout
        )
        self._shared_timeout.start()

        # store preconditions and postconditions verification policies
        self._verify_preconditions = verify_preconditions
        self._verify_postconditions = verify_postconditions

        # execute this action lifecycle
        # (in execute_procedure I run the sequence of actions)
        return super().execute(
            postconditions_timeout, verify_preconditions, verify_postconditions
        )

    def execute_procedure(self):
        """Run the sequence of actions within the same shared timeout."""
        # ensure that the execution parameters have been set
        assert_that(self._shared_timeout).described_as(
            "A common shared timeout should be defined for the sequence"
        ).is_not_none().is_instance_of(ChainedAssertionsTimeout)
        assert_that(self._verify_preconditions).is_type_of(bool)
        assert_that(self._verify_postconditions).is_type_of(bool)

        # execute the sequence of actions
        for action in self.actions:
            action.execute(
                self._shared_timeout,
                self._verify_preconditions,
                self._verify_postconditions,
            )

    def description(self):
        desc = "Sequence of actions: "
        desc += ", ".join([action.name() for action in self.actions])
        return desc
