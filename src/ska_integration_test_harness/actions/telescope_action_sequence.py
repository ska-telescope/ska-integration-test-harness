"""A sequence of `TelescopeAction`s, executed in order."""

from typing import Generic, TypeVar

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

# Define a generic type variable
T = TypeVar("T", bound=object)


class TelescopeActionSequence(TelescopeAction[T], Generic[T]):
    """A sequence of `TelescopeAction`, executed in order.

    This action is used to group a sequence of actions together, so that the
    can be executed as a single action. The sub-actions are executed in
    the order they are provided and the synchronisation is done after
    each sub action (step). By default, this action does not have further
    termination conditions.

    By default, each step keeps the default wait termination condition
    timeout. Calling the ``set_termination_condition_timeout(timeout)``
    method you will apply the change to each of the steps.

    By default, the termination condition policy is set to wait for the
    termination condition of each of the steps. Calling
    ``set_termination_condition_policy(False)`` you will make the last
    step to not wait for the termination condition (but all the others
    will still keep their previous policy).
    Calling ``set_termination_condition_policy(True)`` you will
    make all the steps to wait for the termination condition. If you need,
    you can set the termination condition policy for each step by calling
    the method on each of them (you can access them through :py:attr:`steps`).

    Usage example:

    .. code-block:: python

        # Create a sequence of actions
        sequence = TelescopeActionSequence([
            action1,
            action2,
            action3,
        ])

        # Execute the sequence
        result = sequence.execute()

        # (you can always access the steps, set policies, etc.)
        sequence.steps[0].set_termination_condition_timeout(10)
        sequence.set_logging_policy(True)
        # ...

    """

    def __init__(
        self,
        steps: list[TelescopeAction],
    ) -> None:
        """Initialise the action with the telescope and the steps.

        :param steps: The list of sub-actions to be executed.
        """
        super().__init__()
        self.steps = steps

    def _action(self) -> T:
        """Execute the sequence of actions.

        The steps are executed in order. The synchronisation is done after
        each step. The result of the last step is returned.

        :return: The result of the last step."""
        for step in self.steps[:-1]:
            step.execute()

        return self.steps[-1].execute()

    def termination_condition(self):
        """The sequence by itself does not have a termination condition.

        The termination condition is handled by the steps. If configured,
        the termination condition of the last step will be used.

        :return: An empty list.
        """
        return []

    def set_termination_condition_timeout(self, timeout: int | float) -> None:
        """Propagate a new timeout value to each of the steps.

        :param timeout: The new timeout value.
        """

        for step in self.steps:
            step.set_termination_condition_timeout(timeout)

        # self does not really have a termination condition, so
        # the timeout is not really used. We still call super()
        # through to keep track of the timeout value.
        super().set_termination_condition_timeout(timeout)

    def set_termination_condition_policy(self, wait: bool) -> None:
        """Set the termination condition policy for the steps as follows.

        - set to True: all the steps will wait for the termination condition.
        - set to False: the last step will not wait for the
            termination condition.

        :param wait: The new policy value.
        """

        if wait:
            # make all the steps to wait for the termination condition
            for step in self.steps:
                step.set_termination_condition_policy(True)
        else:
            # make the last step to not wait for the termination condition
            # (all the others will keep their previous policy)
            self.steps[-1].set_termination_condition_policy(False)

        # self does not really have a termination condition, so
        # we don't need to do anything else. We still call super()
        # through to keep track of the policy value.
        super().set_termination_condition_policy(wait)

    def set_logging_policy(self, do_logging: bool) -> None:
        """Propagate a new logging policy to each of the steps.

        :param do_logging: The new logging policy value.
        """

        # logging policy is propagated to all the steps
        for step in self.steps:
            step.set_logging_policy(do_logging)

        # self itself uses the new logging policy
        super().set_logging_policy(do_logging)
