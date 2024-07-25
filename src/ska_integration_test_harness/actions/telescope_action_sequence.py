"""A sequence of `TelescopeAction`s, executed in order."""

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class TelescopeActionSequence(TelescopeAction):
    """A sequence of `TelescopeAction`s, executed in order.

    This action is used to group a sequence of actions together, so that the
    can be executed as a single action. The sub-actions are executed in
    the order they are provided and the synchronization is done after
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
    """

    def __init__(
        self,
        steps: list[TelescopeAction],
    ) -> None:
        """Initialize the action with the telescope and the steps.

        :param steps: The list of sub-actions to be executed.
        """
        super().__init__()
        self.steps = steps

    def _action(self):
        """Execute the sequence of actions."""
        for step in self.steps:
            step.execute()

    def termination_condition(self):
        return []

    def set_termination_condition_timeout(self, timeout: int | float) -> None:
        for step in self.steps:
            step.set_termination_condition_timeout(timeout)

        # self does not really have a termination condition, so
        # the timeout is not really used. We still call super()
        # through to keep track of the timeout value.
        super().set_termination_condition_timeout(timeout)

    def set_termination_condition_policy(self, wait: bool) -> None:
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
