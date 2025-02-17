"""Factory to create subarray commands for the observation state machine."""

from ska_control_model import ObsState

from ska_integration_test_harness.core.actions.tracer_action import (
    TracerAction,
)

from ...core.assertions import AssertDevicesStateChanges
from ..lrc.tango_lrc_action import TangoLRCAction
from .exceptions import (
    ObsStateCommandDoesNotExist,
    ObsStateCommandHasNoTransition,
)
from .system import DEFAULT_SUBARRAY_ID, ObsStateSystem

COMMANDS_STATES_MAP: "dict[str, dict[str, ObsState | None]]" = {
    "AssignResources": {
        "transient": ObsState.RESOURCING,
        "quiescent": ObsState.IDLE,
    },
    "ReleaseResources": {
        "transient": ObsState.RESOURCING,
        "quiescent": ObsState.EMPTY,
    },
    "ReleaseAllResources": {
        "transient": ObsState.RESOURCING,
        "quiescent": ObsState.EMPTY,
    },
    "Configure": {
        "transient": ObsState.CONFIGURING,
        "quiescent": ObsState.READY,
    },
    "Scan": {
        "transient": ObsState.SCANNING,
        "quiescent": ObsState.READY,
    },
    "EndScan": {
        "transient": None,
        "quiescent": ObsState.READY,
    },
    "End": {
        "transient": None,
        "quiescent": ObsState.IDLE,
    },
    "Abort": {
        "transient": ObsState.ABORTING,
        "quiescent": ObsState.ABORTED,
    },
    "Restart": {
        "transient": ObsState.RESTARTING,
        "quiescent": ObsState.EMPTY,
    },
}
"""A map of the commands and the expected ObsState transitions.

Each first level key is the name of a command. Each value is a dictionary
with two keys: ``"transient"`` and ``"quiescent"``. The values of these
keys are the expected ObsState transitions when the command is executed.

The ``"transient"`` key contains the next intermediate ObsState
:py:class:`ska_control_model.ObsState` which is reached when the process
execution begins. The ``"quiescent"`` key contains the final
ObsState which is reached when the process execution completes.

The ``"transient"`` key can be ``None`` if the command does not trigger
any intermediate ObsState transition.

If your system for some reason behaves differently but you still
want to re-use
:py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsFactory`
, you can override this map in your own factory instance.

TODO: Re-engineer in the following way (idea):

- use pydantic to represent commands synchronisation policies
- make each policy contain:
  - boolean flags for transient and quiescent state sync
  - the expected ObsState for each state
  - boolean flags for LRC sync
  - the expected LRC state
  - boolean flag to fail early if LRC fails
  - list of bad LRC states
- this variable becomes a list of default policies
- the factory holds a list of policies inside (which is a copy of the default)
- every time the user creates a command, a policy is accepted as an argument
  and the specified fields override the default policy

I have to think about this
"""  # pylint: disable=line-too-long # noqa: E501


class ObsStateCommandsFactory:
    """Factory to create subarray commands for the observation state machine.

    This class is a factory that creates actions
    to execute certain commands on subarrays and synchronise on their
    next transient and/or quiescent
    :py:class:`ska_control_model.ObsState`.

    The main method of this class is :py:meth:`create_action_with_sync`,
    which creates a new action to execute a given command on a subarray
    and - `according to your settings` - synchronise on the
    next transient and/or quiescent ObsState.
    It relies on the :py:data:`COMMANDS_STATES_MAP` to know which
    ObsState transitions are triggered by each command and
    to
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSystem`
    to know which devices are involved in the observation state machine
    (which devices needs to be synchronised, and which devices are
    the target of the commands).

    Other useful public methods are:

    - :py:meth:`create_action` to create a new action to execute a
      command without synchronisation
    - :py:meth:`add_transient_sync_to_postconditions` to add a
      synchronisation on the next transient ObsState to an action
      according to the :py:data:`COMMANDS_STATES_MAP`
    - :py:meth:`add_quiescent_sync_to_postconditions` to add a
      synchronisation on the next quiescent ObsState, also according
      to the :py:data:`COMMANDS_STATES_MAP`
    - the ``create_<command>_action`` methods to create actions for
      specific subarray commands (TODO: choose to keep or remove them)

    The produced items are instances of
    :py:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`
    , so you can execute them using the
    :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`
    method, or you can further enrich their preconditions and
    postconditions. The produced instances will have:

    - **no preconditions**
    - **the synchronisation to the next transient and/or quiescent
      ObsState as postconditions** (according to the passed flags)
    """

    def __init__(self, obs_state_system: ObsStateSystem):
        """Create a new factory instance.

        :param obs_state_system: the system that supports observation
            state operations
        """
        self.obs_state_system = obs_state_system
        """The system that supports observation state operations."""

    # -------------------------------------------------------------------
    # Generic command actions

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def create_action_with_sync(
        self,
        command_name: str,
        command_input: str | None = None,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = False,
        sync_quiescent: bool = False,
    ) -> TangoLRCAction:
        """Create a new action to execute a subarray command with sync.

        This action is a quick way to create a new action to execute a
        subarray command and synchronise on the next transient and/or
        quiescent ObsState, according to the transitions encoded in the
        :py:data:`COMMANDS_STATES_MAP`.

        :param command_name: the name of the command
        :param command_input: the input for the command, in a form
            of a JSON string (default: None)
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: set to ``True`` to synchronise
            on the next transient ObsState (default: False)
        :param sync_quiescent: set to ``True`` to synchronise
            on the next quiescent ObsState (default: False)

        :return: the action to execute the command

        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        :raise ObsStateCommandDoesNotExist: if the command does not exist
        :raise ObsStateCommandHasNoTransition: if the command has no transition
        """
        # Create the action
        action = self.create_action(command_name, command_input, subarray_id)

        # Add transient and quiescent sync conditions according to the
        # passed flags
        if sync_transient:
            self.add_transient_sync_to_postconditions(
                action, command_name, subarray_id, None
            )
        if sync_quiescent:
            self.add_quiescent_sync_to_postconditions(
                action,
                command_name,
                subarray_id,
                (
                    self._get_obs_state_transition(command_name, "transient")
                    if sync_transient
                    else None
                ),
            )

        return action

    def create_action(
        self,
        command_name: str,
        command_input: str | None = None,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        fail_if_command_does_not_exist: bool = True,
    ) -> TangoLRCAction:
        """Create a new action to execute a subarray command.

        :param command_name: the name of the command
        :param command_input: the input for the command, in a form
            of a JSON string (default: None)
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param fail_if_command_does_not_exist: whether to raise an exception
            if the command does not exist (default: True)

        :return: the action to execute the command

        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        :raise ObsStateCommandDoesNotExist: if the command does not exist
        """
        if fail_if_command_does_not_exist and not self._does_command_exist(
            command_name
        ):
            raise ObsStateCommandDoesNotExist(command_name)

        return TangoLRCAction(
            self.obs_state_system.get_target_device(command_name, subarray_id),
            command_name,
            command_input,
        )

    def add_transient_sync_to_postconditions(
        self,
        action: TracerAction,
        command_name: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        previous_obs_state: "ObsState | None" = None,
    ) -> None:
        """Append synchronisation on the next transient ObsState to an action.

        :param action: the action to append the synchronisation to
        :param command_name: the name of the command
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param previous_obs_state: the previous ObsState
            (default: None, if not provided, the synchronisation will
            accept any previous ObsState)

        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        :raise ObsStateCommandDoesNotExist: if the command does not exist
        :raise ObsStateCommandHasNoTransition: if the command has no transient
        """
        action.add_postconditions(
            self._get_sync_condition_from_map(
                command_name, subarray_id, "transient", previous_obs_state
            )
        )

    def add_quiescent_sync_to_postconditions(
        self,
        action: TracerAction,
        command_name: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        previous_obs_state: "ObsState | None" = None,
    ) -> None:
        """Append synchronisation on the next quiescent ObsState to an action.

        :param action: the action to append the synchronisation to
        :param command_name: the name of the command
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param previous_obs_state: the previous ObsState
            (default: None, if not provided, the synchronisation will
            accept any previous ObsState)

        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        :raise ObsStateCommandDoesNotExist: if the command does not exist
        :raise ObsStateCommandHasNoTransition: if the command has no quiescent
        """
        action.add_postconditions(
            self._get_sync_condition_from_map(
                command_name, subarray_id, "quiescent", previous_obs_state
            )
        )

    # -------------------------------------------------------------------
    # Internal tools

    def _does_command_exist(self, command_name: str) -> bool:
        """Check if a command exists in the map.

        :param command_name: the name of the command
        :return: whether the command exists
        """
        return command_name in COMMANDS_STATES_MAP and isinstance(
            COMMANDS_STATES_MAP[command_name], dict
        )

    def _command_requires_input(self, command_name: str) -> bool:
        """Check if a command requires input.

        :param command_name: the name of the command
        :return: whether the command requires input
        """
        return COMMANDS_STATES_MAP[command_name].get("requires_input", False)

    def _get_obs_state_transition(
        self, command_name: str, transition_type: str
    ) -> "ObsState | None":
        """Get the ObsState transition for a command.

        :param command_name: the name of the command
        :param transition_type: the type of the transition
            (e.g. "transient" or "quiescent")
        :return: the ObsState transition
        """
        if not self._does_command_exist(command_name):
            raise ObsStateCommandDoesNotExist(command_name)

        return COMMANDS_STATES_MAP[command_name].get(transition_type)

    def _get_sync_condition_from_map(
        self,
        command_name: str,
        subarray_id: int,
        transition_type: str,
        previous_obs_state: "ObsState | None" = None,
    ) -> AssertDevicesStateChanges:
        """Get the sync condition from the map.

        :param command_name: the name of the command
        :param subarray_id: the subarray ID
        :param transition_type: the type of the transition
            (e.g. "transient" or "quiescent")
        :param previous_obs_state: the previous ObsState
            (default: None, if not provided, the synchronisation will
            accept any previous ObsState)

        :return: the sync condition

        :raise ObsStateCommandDoesNotExist: if the command does not exist
        :raise ObsStateCommandHasNoTransition: if the command has no quiescent
        """
        if not self._does_command_exist(command_name):
            raise ObsStateCommandDoesNotExist(command_name)

        obs_state = self._get_obs_state_transition(
            command_name, transition_type
        )
        if obs_state is None:
            raise ObsStateCommandHasNoTransition(command_name, transition_type)

        return AssertDevicesStateChanges(
            devices=self.obs_state_system.get_obs_state_devices(subarray_id),
            attribute_name="obsState",
            attribute_value=obs_state,
            previous_value=previous_obs_state,
        )

    # -------------------------------------------------------------------
    # Specific factory methods for subarray commands

    def create_assign_resources_action(
        self,
        command_input: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the AssignResources command.

        :param command_input: the input for the command, in a form
            of a JSON string
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "AssignResources",
            command_input,
            subarray_id,
            sync_transient,
            sync_quiescent,
        )

    def create_release_resources_action(
        self,
        command_input: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the ReleaseResources command.

        IMPORTANT NOTE: the quiescent ObsState we are synchronising on is
        ``ObsState.EMPTY``. Set ``sync_quiescent`` to ``False`` if you want
        to not do this and add your own postcondition.

        :param command_input: the input for the command, in a form
            of a JSON string
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "ReleaseResources",
            command_input,
            subarray_id,
            sync_transient,
            sync_quiescent,
        )

    def create_release_all_resources_action(
        self,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the ReleaseAllResources command.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "ReleaseAllResources",
            None,
            subarray_id,
            sync_transient,
            sync_quiescent,
        )

    def create_configure_action(
        self,
        command_input: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the Configure command.

        :param command_input: the input for the command, in a form
            of a JSON string
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "Configure",
            command_input,
            subarray_id,
            sync_transient,
            sync_quiescent,
        )

    def create_scan_action(
        self,
        command_input: str,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the Scan command.

        :param command_input: the input for the command, in a form
            of a JSON string
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "Scan", command_input, subarray_id, sync_transient, sync_quiescent
        )

    def create_end_scan_action(
        self,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the EndScan command.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "EndScan",
            None,
            subarray_id,
            sync_transient=False,
            sync_quiescent=sync_quiescent,
        )

    def create_end_action(
        self,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the End command.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "End",
            None,
            subarray_id,
            sync_transient=False,
            sync_quiescent=sync_quiescent,
        )

    def create_abort_action(
        self,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the Abort command.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "Abort", None, subarray_id, sync_transient, sync_quiescent
        )

    def create_restart_action(
        self,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        sync_transient: bool = True,
        sync_quiescent: bool = True,
    ):
        """Create a new action to execute the Restart command.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :param sync_transient: whether to synchronise on the next transient
            ObsState (default: True)
        :param sync_quiescent: whether to synchronise on the next quiescent
            ObsState (default: True)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return self.create_action_with_sync(
            "Restart", None, subarray_id, sync_transient, sync_quiescent
        )
