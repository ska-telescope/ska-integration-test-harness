"""Factory to create subarray commands for the observation state machine."""

from ska_control_model import ObsState

from ...core.assertions import AssertDevicesStateChanges
from ..actions.lrc_action import TangoLRCAction
from .obs_state_system import DEFAULT_SUBARRAY_ID, ObsStateSystem


class ObsStateCommandsFactory:
    """Factory to create subarray commands for the observation state machine.

    This class is a factory that creates actions
    to execute certain commands on subarrays and synchronise on their
    next transient and/or quiescent
    :py:class:`ska_control_model.ObsState`.

    The produced items are instances of
    :py:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`
    , so you can execute them using the
    :py:meth:`~ska_integration_test_harness.core.actions.SUTAction.execute`
    method, or you can further enrich their preconditions and
    postconditions.

    **NOTE**: the produced instances will have:

    - **no preconditions**
    - **only the postconditions** to check the **observation state changes**
      after the command execution

    If you wish to add more preconditions or postconditions, you can
    do it using the
    :py:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`
    methods. In particular, we strongly suggest to add there
    LRC verification and early failure conditions (which are **not**
    yet configured by default in the factory).

    This class contains the domain knowledge about which commands are
    available on subarrays and which :py:class:`~ska_control_model.ObsState`
    are triggered by each command. To know where to call the commands
    and which devices are involved in the observation state machine,
    the factory needs an instance of
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSystem`
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

    def create_subarray_command_action(
        self,
        command_name: str,
        command_input: str | None = None,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
    ) -> TangoLRCAction:
        """Create a new action to execute a subarray command.

        :param command_name: the name of the command
        :param command_input: the input for the command, in a form
            of a JSON string (default: None)
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :return: the action to execute the command
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
        return TangoLRCAction(
            self.obs_state_system.get_target_device(command_name, subarray_id),
            command_name,
            command_input,
        )

    def add_obs_state_sync_to_postconditions(
        self,
        action: TangoLRCAction,
        obs_state: ObsState,
        previous_obs_state: ObsState | None = None,
        add_postconditions: bool = True,
    ) -> None:
        """Append synchronisation on a given ObsState to an action.

        :param action: the action to append the synchronisation to
        :param obs_state: the ObsState to synchronise on
        :param previous_obs_state: the previous ObsState (default: None)
        :param add_postconditions: whether to add or not the postcondition
            (default: True, setting it to False may be useful to avoid
            repeating a similar if-else block every time you call this method)
        """
        if add_postconditions:
            action.add_postconditions(
                AssertDevicesStateChanges(
                    self.obs_state_system.get_obs_state_devices(
                        action.subarray_id
                    ),
                    "obsState",
                    obs_state,
                    previous_value=previous_obs_state,
                )
            )
        return action

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
        action = self.create_subarray_command_action(
            "AssignResources", command_input, subarray_id
        )
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.RESOURCING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.IDLE,
            ObsState.RESOURCING,
            add_postconditions=sync_quiescent,
        )

        return action

    def release_all_resources_action(
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
        action = self.create_subarray_command_action(
            "ReleaseAllResources", subarray_id
        )
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.RESOURCING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.EMPTY,
            ObsState.RESOURCING,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action(
            "Configure", command_input, subarray_id
        )
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.CONFIGURING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.READY,
            ObsState.CONFIGURING,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action(
            "Scan", command_input, subarray_id
        )
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.SCANNING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.READY,
            ObsState.SCANNING,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action("EndScan", subarray_id)
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.READY,
            ObsState.SCANNING,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action("End", subarray_id)
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.IDLE,
            ObsState.READY,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action("Abort", subarray_id)
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.ABORTING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.ABORTED,
            ObsState.ABORTING,
            add_postconditions=sync_quiescent,
        )

        return action

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
        action = self.create_subarray_command_action("Restart", subarray_id)
        self.add_obs_state_sync_to_postconditions(
            action, ObsState.RESTARTING, add_postconditions=sync_transient
        )
        self.add_obs_state_sync_to_postconditions(
            action,
            ObsState.EMPTY,
            ObsState.RESTARTING,
            add_postconditions=sync_quiescent,
        )

        return action
