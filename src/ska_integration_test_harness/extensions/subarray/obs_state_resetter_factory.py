"""A factory to create actions to reset the obs state of a subarray."""

from ska_control_model import ObsState, ResultCode

from ...core.actions.sequence import SUTActionSequence
from ...core.assertions import AssertDevicesStateChanges
from ..actions import TangoLRCAction
from .obs_state_commands_factory import ObsStateCommandsFactory
from .obs_state_system import DEFAULT_SUBARRAY_ID, ObsStateSystem


class ObsStateResetterFactory:
    """Factory to create actions to reset the obs state of a subarray.

    # NOTE: this is a draft, and will likely change in the future!

    This class is a factory to create actions to reset the obs state of
    a subarray-based system to a given target observation state
    (independently from the state the system is currently in). The factory
    will create a
    :py:class:`~ska_integration_test_harness.core.actions.SUTActionSequence`
    of
    :py:class:`~ska_integration_test_harness.extensions.subarray.actions.TangoLRCAction`
    that move the system from the current state
    (the state read from the
    :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSystem`
    main device) to a given target state.

    The reset procedure (created calling :meth:`create_reset_to_action`)
    works as follows:

    - Let's divide the observation state graph in three + 1 parts:
      - the ``ObsState.EMPTY`` state
      - the states that support an ``Abort`` operation (i.e., the regular
        operational states
        ``ObsState.RESOURCING``, ``ObsState.IDLE``, ``ObsState.CONFIGURING``,
        ``ObsState.READY``, ``ObsState.SCANNING``), let's call them
        ``support_abort``
      - the states that support a ``Restart`` operation (i.e., the final
        states ``ObsState.ABORTED``, ``ObsState.FAULT``)
      - the states that do not support any operation (i.e., the transient
        states ``ObsState.ABORTING`` and ``ObsState.RESTARTING``)
    - We can see there three main areas as connected though a directed
      graph, that essentially is a big cycle:
      - from ``ObsState.EMPTY`` we can go to ``support_abort`` by calling
        the regular operational commands (e.g., ``AssignResources``, ...)
      - inside ``support_abort`` you move through the states in the order
        (after you assigned resources, you can ``Configure`` and ``Scan``)
      - from any ``support_abort`` you can move to ``ObsState.ABORTING`` and
        ``ObsState.ABORTED`` by calling the ``Abort`` command (this permits
        you to reach the ``support_restart`` area)
      - from any ``support_restart`` you can move to ``ObsState.RESTARTING``
        and ``ObsState.EMPTY`` by calling the ``Restart`` command
    - Our reset procedure will follow the following rules, according to the
      current state and to the desired state:
      1. if ``starting_state == target_state == ObsState.EMPTY``, nothing to do
      2. if ``target_state == ObsState.EMPTY != starting_state``, we need to
         follow the Abort & Restart path to reach empty (it should be
         possible from any starting state, except from ``ObsState.ABORTING``,
         ``ObsState.RESTARTING`` and ``ObsState.RESETTING``
         where we don't have a procedure yet)
      3. for ``target_state in [ObsState.ABORTING, ObsState.ABORTED]``, if
         ``starting_state in support_abort``, we call the ``Abort`` command,
         otherwise we first reach the ``ObsState.RESOURCING`` state (passing
         through the ``ObsState.EMPTY`` state) and then we call the ``Abort``
         command.
      4. for ``target_state in [ObsState.RESTARTING, ObsState.EMPTY]``, if
         ``starting_state in support_restart``, we call the ``Restart`` command,
         otherwise we first reach the ``ObsState.ABORTED`` state (passing
         through ``ObsState.EMPTY`` and ``ObsState.RESOURCING``) and then we
         call the ``Restart`` command.
      5. for any other target state, we first reset to ``ObsState.EMPTY``
         (using the Nr. 1 rule)

    The commands synchronisation is done as follows:

    - all steps are commands, that synchronise the following conditions:
      - the transient state (if ``sync_transient`` is True, default: True)
      - the quiescent state (unless you explicitly want to reach a transient
        state and not the following quiescent state)
      - the LRC state (if ``sync_lrc`` is True, default: True, unless you
        want to reach a transient state so it's not necessary to wait a
        LRC to complete)
    - any step of the sequence will fail early if a LRC error event is detected
      (if ``early_fail_on_lrc_failure`` is True, default: True)

    Playing with the flags you can make more or less strict the
    synchronisation. If you wish to have more control on the synchronisation
    for LRC, you can disable the ``sync_lrc`` flag and the
    ``early_fail_on_lrc_failure`` flag and then use
    :meth:`make_sequence_sync_lrc` and
    :meth:`make_sequence_fail_early_on_lrc_failure` to control the
    synchronisation on LRC (excluding some specific commands or changing
    the expected result codes).
    """  # pylint: disable=line-too-long # noqa: E501

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        obs_state_system: ObsStateSystem,
        sync_transient: bool = True,
        sync_lrc: bool = True,
        early_fail_on_lrc_failure: bool = True,
    ):
        """Initialise the factory.

        :param obs_state_system: the system that supports observation
            state operations
        :param sync_transient: whether to synchronise transient states
            when resetting the obs state (default: True)
        :param sync_lrc: whether to synchronise LRC states when resetting
            the obs state (default: True)
        :param early_fail_on_lrc_failure: whether to fail early if the
            LRC state cannot be synchronised (default: True)
        """
        self.obs_state_system = obs_state_system
        """The system that supports observation state operations."""

        self.commands_factory = ObsStateCommandsFactory(obs_state_system)
        """The factory to create the commands to change the obs state."""

        self.sync_transient = sync_transient
        """Flag to synchronise transient states when resetting the obs state.

        If True, for commands that move a system first to a transient state
        and then to a quiescent state, the synchronisation will be done
        **also on the transient state**. If False, the synchronisation will
        be done **only on the quiescent state**.
        """

        self.sync_lrc = sync_lrc
        """Flag to tell that all the commands should synchronise on LRC.

        If True, all the commands of the given sequence will synchronise
        on the LRC state. If False, the commands will synchronise only
        on the state changes.
        """

        self.early_fail_on_lrc_failure = early_fail_on_lrc_failure
        """Flag to tell that the sequence should fail early on LRC failure.

        If True, the sequence will fail early if the a LRC error event
        is detected. If False, the sequence will continue even if a LRC
        error event is detected.
        """

        self.support_abort = [
            ObsState.RESOURCING,
            ObsState.IDLE,
            ObsState.CONFIGURING,
            ObsState.READY,
            ObsState.SCANNING,
        ]
        """The states that support an abort operation."""

        self.support_restart = [
            ObsState.ABORTED,
            ObsState.FAULT,
        ]
        """The states that support a restart operation."""

        self.transient_states = [
            ObsState.RESOURCING,
            ObsState.CONFIGURING,
            ObsState.SCANNING,
            ObsState.ABORTING,
            ObsState.RESTARTING,
        ]
        """The transient states."""

    def create_reset_to_action(
        self, target_obs_state: str, subarray_id: int = DEFAULT_SUBARRAY_ID
    ) -> SUTActionSequence:
        """Create an action to reset the obs state to the target state.

        This method will create a sequence of actions to reset the obs state
        of the subarray-based system to the given target observation state.
        The sequence will be created according to the rules described in the
        class documentation.

        :param target_obs_state: the target observation state
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :return: the action to reset the obs state
        """
        sequence = SUTActionSequence()

        # get the current observation state
        starting_state = self.obs_state_system.get_main_obs_state_device(
            subarray_id
        ).obsState

        # fail if the starting state is not yet supported
        if starting_state in [
            ObsState.ABORTING,
            ObsState.RESTARTING,
            ObsState.RESETTING,
        ]:
            raise NotImplementedError(
                f"Cannot reset from {starting_state}. We didn't yet "
                " implemented a procedure to reset from this state."
            )

        # create the action to reset the observation state
        mapping = {
            ObsState.EMPTY: self._reset_to_empty,
            ObsState.RESOURCING: self._reset_to_resourcing,
            ObsState.IDLE: self._reset_to_idle,
            ObsState.CONFIGURING: self._reset_to_configuring,
            ObsState.READY: self._reset_to_ready,
            ObsState.SCANNING: self._reset_to_scanning,
            ObsState.ABORTING: self._reset_to_aborting,
            ObsState.ABORTED: self._reset_to_aborted,
            ObsState.RESTARTING: self._reset_to_restarting,
        }

        if target_obs_state not in mapping:
            raise NotImplementedError(
                f"Cannot reset to {target_obs_state}. We didn't yet "
                " implemented a procedure to reset to this state."
            )

        mapping[target_obs_state](sequence, starting_state, subarray_id)

        if self.sync_lrc:
            self.make_sequence_sync_lrc(sequence)

        if self.early_fail_on_lrc_failure:
            self.make_sequence_fail_early_on_lrc_failure(sequence)

        # return the sequence of actions
        return sequence

    def make_sequence_sync_lrc(
        self,
        sequence: SUTActionSequence,
        exclude_commands: list[str] | None = None,
        expected_result_codes: (
            ResultCode | list[ResultCode] | None
        ) = ResultCode.OK,
        put_at_beginning: bool = False,
    ):
        """The sequence steps should synchronise on LRC, when appropriate.

        This method will add the LRC synchronisation to all the commands
        in the sequence, unless the command is in the exclude list. Actions
        which last postcondition synchronises on a transient state will
        be automatically excluded from the LRC synchronisation
        (e.g., you don't want to synchronise on LRC completion if you
        are waiting to reach ``ObsState.CONFIGURING``, otherwise you
        will reach also ``ObsState.READY``).

        :param sequence: the sequence of actions
        :param exclude_commands: the list of commands to exclude from
            the LRC synchronisation
        :param expected_result_code: the expected result code of the LRC.
            Please, see the documentation of
            :py:meth:`~ska_integration_test_harness.extensions.actions.TangoLRCAction.add_lrc_completion_to_postconditions`
            for more details.
        :param put_at_beginning: if True, you will verify the LRC completion
            before the other postconditions you configured.
            By default, it is added at the end.
            Please, see the documentation of
            :py:meth:`~ska_integration_test_harness.extensions.actions.TangoLRCAction.add_lrc_completion_to_postconditions`
            for more details.
        """  # pylint: disable=line-too-long # noqa: E501
        for action in sequence.actions:
            if not isinstance(action, TangoLRCAction):
                continue

            if action.command_name in (exclude_commands or []):
                continue

            # check the last postcondition refers to a transient state
            last_postcondition = None
            for postcondition in action.postconditions:
                if isinstance(postcondition, AssertDevicesStateChanges):
                    last_postcondition = postcondition
            if last_postcondition is None:
                continue

            # if the last postcondition synchronises on a transient state,
            # exclude the LRC synchronisation
            if last_postcondition.attribute_value in self.transient_states:
                continue

            # add the LRC synchronisation
            action.add_lrc_completion_to_postconditions(
                expected_result_codes, put_at_beginning
            )

    def make_sequence_fail_early_on_lrc_failure(
        self,
        sequence: SUTActionSequence,
        exclude_commands: list[str] | None = None,
        error_result_codes: list[ResultCode] | None = None,
    ):
        """The sequence should fail early on LRC failure.

        This method will add the LRC errors as early stop conditions to
        all the commands in the sequence, unless the command is in the
        exclude list.

        :param sequence: the sequence of actions
        :param exclude_commands: the list of commands to exclude from
            the LRC error early stop
        :param error_result_codes: the list of error result codes that
            should trigger the early stop. If None, it will use the
            default error codes for the TangoLRCAction.
            Please, see the documentation of
            :py:meth:`~ska_integration_test_harness.extensions.actions.TangoLRCAction.add_lrc_errors_to_early_stop`
            for more details.
        """  # pylint: disable=line-too-long # noqa: E501
        for action in sequence.actions:
            if not isinstance(action, TangoLRCAction):
                continue

            if action.command_name in (exclude_commands or []):
                continue

            action.add_lrc_errors_to_early_stop(error_result_codes)

    # ----------------------------------------------------------------------
    # SPECIAL CASES: does not assume to pass through EMPTY

    def _reset_to_empty(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.EMPTY``.

        - in the base case, it's already in ``ObsState.EMPTY`` so
          nothing to do
        - in the alternative case, if the system requires an abort
          do it, then restart
        - the final synchronisation is on the quiescent state
          (on the transient state only if required)

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        # if the system is already in the empty state, nothing to do
        if starting_state == ObsState.EMPTY:
            return

        # if the starting state supports an abort, do it
        if starting_state in self.support_abort:
            sequence.add_actions(
                self.commands_factory.create_abort_action(
                    subarray_id,
                    sync_transient=self.sync_transient,
                    sync_quiescent=True,
                )
            )
            starting_state = ObsState.ABORTED

        # if the starting state supports a restart, do it
        if starting_state in self.support_restart:
            sequence.add_actions(
                self.commands_factory.create_restart_action(
                    subarray_id,
                    sync_transient=self.sync_transient,
                    sync_quiescent=True,
                )
            )

    def _reset_to_aborting(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.ABORTING``.

        - if the system is already in a state that supports abort, it will
          call the abort command
        - if the system is not yet in a state that supports abort, it will
          first reach the RESOURCING state and then call the abort command
        - the final synchronisation is on the transient state

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        # If we are not yet in a state that supports abort,
        # we need to go to RESOURCING first
        if starting_state not in self.support_abort:
            self._reset_to_resourcing(sequence, starting_state, subarray_id)

        # Now we can abort
        sequence.add_actions(
            self.commands_factory.create_abort_action(
                subarray_id,
                sync_transient=True,
                sync_quiescent=False,
            )
        )

    def _reset_to_aborted(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.ABORTED``.

        - if the system is already in a state that supports abort, it will
          call the abort command
        - if the system is not yet in a state that supports abort, it will
          first reach the RESOURCING state and then call the abort command
        - the final synchronisation is on the quiescent state
          (on the transient state only if required)

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        # If we are not yet in a state that supports abort,
        # we need to go to RESOURCING first
        if starting_state not in self.support_abort:
            self._reset_to_resourcing(sequence, starting_state, subarray_id)

        # Now we can abort
        sequence.add_actions(
            self.commands_factory.create_abort_action(
                subarray_id,
                sync_transient=self.sync_transient,
                sync_quiescent=True,
            )
        )

    def _reset_to_restarting(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.RESTARTING``.

        - if the system is already in a state that supports restart, it will
          call the restart command
        - if the system is not yet in a state that supports restart, it will
          first reach the ABORTED state and then call the restart command
        - the final synchronisation is on the transient state

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        # If we are not yet in a state that supports restart,
        # we need to go to ABORTED first
        if starting_state not in self.support_restart:
            self._reset_to_aborted(sequence, starting_state, subarray_id)

        # Now we can restart
        sequence.add_actions(
            self.commands_factory.create_restart_action(
                subarray_id,
                sync_transient=True,
                sync_quiescent=False,
            )
        )

    # ----------------------------------------------------------------------
    # REGULAR CASES: assume to pass through EMPTY

    def _reset_to_resourcing(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.RESOURCING``.

        - it will make sure the system is in ``ObsState.EMPTY``
        - if will call ``AssingResources`` synchronising on the transient

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        self._reset_to_empty(sequence, starting_state, subarray_id)
        sequence.add_actions(
            self.commands_factory.create_assign_resources_action(
                subarray_id,
                sync_transient=True,
                sync_quiescent=False,
            )
        )

    def _reset_to_idle(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.IDLE``.

        - it will make sure the system is in the ``ObsState.EMPTY`` state
        - it will call ``AssignResources`` synchronising on the
          quiescent state (on the transient state only if required)

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        self._reset_to_empty(sequence, starting_state, subarray_id)
        sequence.add_actions(
            self.commands_factory.create_assign_resources_action(
                subarray_id,
                sync_transient=self.sync_transient,
                sync_quiescent=True,
            )
        )

    def _reset_to_configuring(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.CONFIGURING``.

        - it will make sure the system is in the ``ObsState.IDLE`` state
        - it will call ``Configure`` synchronising on the transient state

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        self._reset_to_idle(sequence, starting_state, subarray_id)
        sequence.add_actions(
            self.commands_factory.create_configure_action(
                subarray_id,
                sync_transient=True,
                sync_quiescent=False,
            )
        )

    def _reset_to_ready(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.READY``.

        - it will make sure the system is in the ``ObsState.CONFIGURING`` state
        - it will call ``Configure`` synchronising on the quiescent state
          (on the transient state only if required)

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        self._reset_to_configuring(sequence, starting_state, subarray_id)
        sequence.add_actions(
            self.commands_factory.create_configure_action(
                subarray_id,
                sync_transient=self.sync_transient,
                sync_quiescent=True,
            )
        )

    def _reset_to_scanning(
        self,
        sequence: SUTActionSequence,
        starting_state: ObsState,
        subarray_id: int,
    ):
        """Create an action to reset the obs state to ``ObsState.SCANNING``.

        - it will make sure the system is in the ``ObsState.READY`` state
        - it will call ``Scan`` synchronising on the transient state

        :param action: the existing action sequence
        :param starting_state: the starting observation state
        :param subarray_id: the subarray ID
        """
        self._reset_to_ready(sequence, starting_state, subarray_id)
        sequence.add_actions(
            self.commands_factory.create_scan_action(
                subarray_id,
                sync_transient=True,
                sync_quiescent=False,
            )
        )
