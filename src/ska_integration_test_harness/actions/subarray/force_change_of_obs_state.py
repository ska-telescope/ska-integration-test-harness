"""Force the change of the ObsState in Subarray."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.subarray.obs_state_resetter_factory import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayObsStateResetterFactory,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)


class ForceChangeOfObsState(TelescopeAction[None]):
    """Force the change of the ObsState in Subarray to a target state.

    This action is used to force the change of the ObsState in TMC Subarray,
    regardless of the current state of the Subarray.
    The action will move the state machine to the target state, by executing
    the necessary steps to reach it (e.g. assign, configure, scan) in a
    correct and consistent way.

    This action has no termination condition, but you can customize:

    - the wait timeout of each of the steps, by calling the method
        ``set_termination_condition_timeout(timeout)``.
    - the termination condition policy of the last step, by calling the method
        ``set_termination_condition_policy(True)`` (to ensure all
        steps wait for the termination condition) or
        ``set_termination_condition_policy(False)`` (to make the last step
        not wait for the termination condition).

    By default each step will keep the default wait termination condition
    and each step will wait for its termination condition.
    """

    def __init__(
        self,
        dest_state_name: ObsState,
        commands_input: TestHarnessInputs,
    ):
        """Initialise the action with the target state and the JSON inputs.

        :param dest_state_name: The target state to reach.
        :param commands_inputs: The JSON inputs for the commands to bring
            the subarray in a certain obs state. You can pass just the
            JSON inputs you need, but if one of them is missing, you may
            occur in an error when executing the action.
        """
        super().__init__()

        self.dest_state_name = dest_state_name
        self.commands_input = commands_input

    def _action(self):
        current_state = ObsState(self.telescope.tmc.subarray_node.obsState)
        self._log(
            "Using a sequence of actions to force the change of the "
            f"ObsState in Subarray from {str(current_state)} to "
            f"{str(self.dest_state_name)}."
        )

        # create a sequence of actions to reset the subarray to the
        # given target state
        obs_state_resetter_action = SubarrayObsStateResetterFactory(
            self.commands_input
        ).create_action_to_reset_subarray_to_state(self.dest_state_name)

        # propagate the termination condition timeout and policy to the
        # sequence of actions
        obs_state_resetter_action.set_termination_condition_timeout(
            self.termination_condition_timeout
        )
        obs_state_resetter_action.set_termination_condition_policy(
            self.wait_termination
        )

        # execute the sequence of actions
        obs_state_resetter_action.execute()

        current_state = ObsState(self.telescope.tmc.subarray_node.obsState)
        self._log(
            "After running a sequence of actions, the ObsState in Subarray is "
            f"{str(current_state)} (expected: {str(self.dest_state_name)}). "
            "Clearing command call in emulators. "
        )

        self.telescope.clear_command_call()

    def termination_condition(self):
        """No expected outcome for this action."""
        return []
