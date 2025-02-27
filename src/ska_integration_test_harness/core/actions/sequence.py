"""Compose a sequence of actions, under a same common timeout."""

from .sut_action import SUTAction


class SUTActionSequence(SUTAction):
    """Compose a sequence of actions, under a same common timeout.

    This class represents a sequence of
    :py:class:`ska_integration_test_harness.core.actions.SUTAction`
    instances grouped together in a sequence to be executed in order.
    The actions have the following properties:

    - Each action is a
      :py:class:`~ska_integration_test_harness.core.actions.SUTAction`
      instance, and can be executed within a shared timeout by calling
      :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`.
      The verification includes a setup, a verification of preconditions,
      the execution of the procedure, and a verification of postconditions
      (with an eventual synchronisation within the timeout).
    - Execution parameters such as the timeout and the flags to enable/disable
      precondition and postcondition verification are shared among all the
      actions in the sequence. The shared timeout is started before the first
      postcondition evaluation.
    - You can build the sequence by adding actions with :py:meth:`add_actions`.
    - The sequence can be executed in the given order by calling
      :py:meth:`execute`. Every time you call the method, the
      sequence is executed from the beginning, within a shared timeout
      (an action remaining time for verifying postconditions is
      the remaining time left by the previous)
    - Optionally, you can override this class to add further global setup,
      precondition, or postcondition verification.

    **Example**:

    .. code-block:: python

        from ska_integration_test_harness.core.actions import SUTActionSequence

        # create a sequence of actions
        sequence = SUTActionSequence()

        # add actions to the sequence
        sequence.add_actions(action1, action2, action3)

        # execute the sequence (within the same shared timeout)
        sequence.execute(postconditions_timeout=10)
    """

    def __init__(self):
        # the list of actions in the sequence
        self._actions: list[SUTAction] = []

        # internal execution parameters for sequence
        self._shared_timeout = None
        self._verify_preconditions = True
        self._verify_postconditions = True

        super().__init__()

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
            self._actions.extend(actions)

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

    def execute_procedure(self):
        """Run the sequence of actions within the same shared timeout."""
        for action in self.actions:
            action.execute(**self._last_execution_params.as_dict())

    def description(self):
        desc = "Sequence of actions: "
        desc += ", ".join([action.name() for action in self.actions])
        return desc
