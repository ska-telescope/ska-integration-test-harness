"""Execute provided command on subarray Node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class SubarrayExecuteTransition(TelescopeCommandAction):
    """Execute a given command on subarray Node and expect a certain obsState.

    This action is the call of a generic command on the subarray Node, where:

    - the called Tango command is generic and can be specified as a
      constructor argument (``command_name``),
    - the expected outcome of the command is also generic and can be
      (optionally) specified as a parameter (``expected_obs_state``),
    - (always optionally) a JSON input can be provided as an argument
      to the constructor (``command_input``).

    The command target is the TMC SubarrayNode.
    """

    # TODO: unit test (and possibly see where it is appropriate to use)

    def __init__(
        self,
        command_name: str,
        expected_obs_state: ObsState | None = None,
        command_input: JSONInput | None = None,
    ):
        """Initialize with the command name and the expected obsState.

        :param command_name: The name of the command to be executed.
        :param expected_obs_state: The expected obsState after
            the command is executed.
        :param command_input: The JSON input for the command.
        """
        super().__init__()

        self.command_name = command_name
        """The name of the command to be executed (e.g., "Configure")."""

        self.expected_obs_state = expected_obs_state
        """The expected obsState after the command is executed.

        (e.g., ObsState.READY). If not provided, the action will have an empty
        termination condition. If provided, the termination condition will be
        that all subarrays must have the expected obsState.
        """

        self.command_input = command_input
        """The JSON input for the command (if any)."""

    def _action(self):
        self._log(f"Invoking {self.command_name} on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.command_inout(
            self.command_name, self.command_input.get_json_string()
        )
        return result, message

    def termination_condition(self):
        if self.expected_obs_state is None:
            self._log(
                "No expected obsState provided, no termination condition."
            )
            return []

        self._log(
            "Expecting all subarrays to have "
            f"obsState {self.expected_obs_state}"
        )
        return all_subarrays_have_obs_state(
            self.telescope, self.expected_obs_state
        )
