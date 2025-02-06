"""Tools to put the system in a desired observation state."""

import abc

from assertpy import assert_that
from pydantic import BaseModel
from ska_control_model import ObsState

from ...core.actions.sut_action import SUTAction
from .obs_state_commands_factory import ObsStateCommandsFactory
from .obs_state_system import DEFAULT_SUBARRAY_ID, ObsStateSystem

STATE_CLASS_MAP: dict[ObsState, type] = {}
"""Map ``ObsState`` to the classes that support them as starting states.

This class maps the observation states to the classes that support them
as starting states to move towards another observation state. The map
is filled after all the classes are defined, but you can
extend/override it if you need to.
"""

NOT_REACHABLE_STATES = [
    ObsState.FAULT,
    ObsState.RESETTING,
]
"""List of observation states that are not reachable by the system.

You can override this if your subclasses somehow support these states.
"""


class ObsStateCommandsInput(BaseModel):
    """Input for the observation state commands.

    This class represents the input for the observation state commands
    to be used during the observation state set procedure.
    """

    AssignResources: str | None = None
    Configure: str | None = None
    Scan: str | None = None

    @staticmethod
    def get_object(
        cmd_inputs: "ObsStateCommandsInput | dict",
    ) -> "ObsStateCommandsInput":
        """Get the object from a dictionary or an object.

        :param cmd_inputs: the dictionary or object to convert
        :return: the object
        """
        if cmd_inputs is None:
            return ObsStateCommandsInput()

        if isinstance(cmd_inputs, dict):
            return ObsStateCommandsInput(**cmd_inputs)
        return cmd_inputs


# -------------------------------------------------------------------
# Base class for observation state setters


class ObsStateSetter(SUTAction, abc.ABC):
    """Tool to put the system in a desired observation state.

    TODO: describe the class

    TODO: how may I embed the conditional LRC synchronization and early
    stop in an elegant way?
    """

    @staticmethod
    def get_setter_action(
        system: ObsStateSystem,
        target_obs_state: ObsState,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        commands_input: ObsStateCommandsInput | dict | None = None,
        enable_logging=True,
    ) -> "ObsStateSetter":
        """Get the appropriate setter action from the current system state.

        Given the current system state, check which is the appropriate
        setter action to use to move the system towards the target
        observation state.

        :param system: the system to put in the desired observation state
        :param target_obs_state: the desired observation state
        :param subarray_id: the subarray ID
        :param commands_input: the input for the commands. Specify them
            as a dictionary or as an :py:class:`ObsStateCommandsInput`
            instance (default: no input for any command, you can leave
            like that if you think you don't need to execute
            any ``AssignResources``, ``Configure`` or ``Scan`` command)
        :param enable_logging: whether to enable logging (default: True)

        :return: the appropriate setter action
        :raise NotImplementedError: if the current observation state is not
            supported by the decision rules or if the target observation state
            is not reachable by the current decision rules
        """

        current_obs_state = system.get_main_obs_state_device(
            subarray_id
        ).obsState

        if current_obs_state not in STATE_CLASS_MAP:
            raise NotImplementedError(
                f"Failure in get_setter_action: "
                f"From the current observation state ({current_obs_state}) "
                "the current decision rules do not support any setter action."
            )

        if target_obs_state in NOT_REACHABLE_STATES:
            raise NotImplementedError(
                f"Failure in get_setter_action: "
                f"The target observation state ({target_obs_state}) "
                "is not reachable by current decision rules."
            )

        return STATE_CLASS_MAP[current_obs_state](
            system,
            target_obs_state,
            subarray_id,
            commands_input,
            enable_logging,
        )

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        system: ObsStateSystem,
        target_obs_state: ObsState,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        commands_input: ObsStateCommandsInput | dict | None = None,
        enable_logging=True,
    ):
        """Initialize the ObsStateSetter.

        :param system: the system to put in the desired observation state
        :param target_obs_state: the desired observation state
        :param subarray_id: the subarray ID
        :param commands_input: the input for the commands. Specify them
            as a dictionary or as an :py:class:`ObsStateCommandsInput`
            instance (default: no input for any command, you can leave
            like that if you think you don't need to execute
            any ``AssignResources``, ``Configure`` or ``Scan`` command)
        :param enable_logging: whether to enable logging (default: True)
        """
        super().__init__(enable_logging)

        self.system = system
        self.target_obs_state = target_obs_state
        self.subarray_id = subarray_id

        self.command_factory = ObsStateCommandsFactory(self.system)

        self.commands_input = ObsStateCommandsInput.get_object(commands_input)

    def description(self) -> str:
        return (
            f"Move subarray {self.subarray_id} "
            f"from {self.class_starting_obs_state()} "
            f"to {self.target_obs_state}."
        )

    def class_starting_obs_state(self):
        """Return the observation state that is expected by the class.

        :return: the observation state expected by the class as a
            starting point for the observation state set procedure
        """
        return STATE_CLASS_MAP[self.__class__]

    def verify_preconditions(self):
        """Verify the system is the class obs. state and it's consistent.

        The preconditions for a successful observation state change are:

        - the system is in a consistent observation state
        - the consistent observation state is the one expected by the class
        """
        self._system_is_in_class_starting_obs_state()
        self._system_obs_state_is_consistent()

    def execute_procedure(self):
        """Move towards the target observation state (if not already there).

        The procedure:

        - verifies if the system is already in the target observation state
        - if not, it tries to move the system towards the
          target observation state according to the given decision rules
          (sending a command and then )
        - if the decision rules are not enough to move the system to the
          target observation state, the method should raise an exception
        - after executing the command, I determine the next setter to use
          given the new observation state
        """
        # verify if the system is already in the target observation state
        if self._system_obs_state() == self.target_obs_state:
            return

        # ensure target state is reachable
        if self.target_obs_state in NOT_REACHABLE_STATES:
            raise NotImplementedError(
                f"Failure in {self.name()} action ({self.description()}): "
                f"The target observation state ({self.target_obs_state}) "
                "is not reachable by current decision rules."
            )

        # compute the next command that should be run
        command = self.next_command()
        command.set_logging(not self.logger.disabled)

        # run it
        command.execute(**self._last_execution_params)

        # determine the next setter to use and execute it
        self.get_setter_action(
            self.system,
            self.target_obs_state,
            self.subarray_id,
            self.commands_input,
            not self.logger.disabled,
        ).execute(**self._last_execution_params)

    def next_command(self) -> SUTAction:
        """Return the next command to send to move towards the target state.

        This method should return the next command to send to move the system
        towards the target observation state. If the system cannot move towards
        the target observation state from the current one, just raise an
        exception by calling the superclass method.

        You can not consider non-reachable states in this decision
        (they are dealt separately). You can also ignore the case where
        the system is already in the target observation state.

        :return: the next command to send
        :raise NotImplementedError: if the system cannot move
            towards the target observation state from the current one
        """
        raise NotImplementedError(
            f"Failure in {self.name()} action ({self.description()}): "
            "The system cannot move towards the target observation state "
            f"({self.target_obs_state}) from the current state "
            f"({self.class_starting_obs_state()})."
        )

    # -------------------------------------------------------------------
    # Internal utilities for the class

    def _system_obs_state(self) -> ObsState:
        """Return the current observation state of the system.

        :return: the current observation state of the system, read from the
            coordinator device (which observation state should be
            representative for the whole system).
        """
        return self.system.get_main_obs_state_device(self.subarray_id).obsState

    def _system_is_in_class_starting_obs_state(self):
        """Verify the system is in the expected class observation state."""
        assert_that(self._system_obs_state()).described_as(
            f"{self.description()} FAILED ASSUMPTION: "
            "The system is expected to be in the class observation state "
            "As a starting point for the observation state set procedure."
        ).is_equal_to(self.class_starting_obs_state())

    def _accepted_obs_states_for_devices(self) -> list[ObsState]:
        """Define the accepted observation states for the devices.

        This method defines which observation states for the devices are
        handled by the class. The method should return a list of observation
        states that are accepted by the class.

        By default, the only accepted observation state is the one defined
        in the state-class mapping.

        :return: the list of accepted observation states
        """
        return [self.class_starting_obs_state()]

    def _system_obs_state_is_consistent(self):
        """Verify the system is in a consistent observation state."""
        for device in self.system.get_obs_state_devices(self.subarray_id):
            assert_that(device.obsState).described_as(
                self.description()
                + "FAILED ASSUMPTION: "
                + " The system devices are expected to be in a "
                "consistent observation state, but "
                f"device {device.dev_name()} is not."
            ).is_in(self._accepted_obs_states_for_devices())

    def _get_command_input_or_fail(self, command_name: str) -> str:
        """Get the command input or raise an exception if it is missing.

        :param command_name: the name of the command
        :return: the command input
        :raise ValueError: if the command input is missing
        """
        command_input = getattr(self.commands_input, command_name)
        if command_input is None:
            raise ValueError(
                f"Failure in {self.name()} action ({self.description()}): "
                f"The {command_name} command input is missing. "
                "Set it using the ``commands_input`` parameter in "
                "the constructor."
            )
        return command_input


# -------------------------------------------------------------------
# Specific classes for observation state setters


# *** EMPTY ***
# Rules: simple, just begin the normal operational flow


class ObsStateSetterEmpty(ObsStateSetter):
    """Set Observation State starting from an empty state.

    From an empty state, whatever the target state is (except
    ``EMPTY`` and the unsupported states), the system should just
    begin the normal operational flow.

    Routing rules:
    - if the target state is ``RESOURCING`` (or something that will
      require immediate abort), send ``AssignResources``
      synchronising on the transient state
    - any other state is supposed to be reached passing through ``IDLE``,
      so I send ``AssignResources`` synchronising on the quiescent state
      (+ verifying LRC completion and errors)

    LRC errors will always be used as early stop conditions.
    """

    def next_command(self):
        command_input = self._get_command_input_or_fail("AssignResources")

        # I don't need to synchronise on the transient state if 1)
        # the target state is RESOURCING or 2) the target state is
        # something I will reach passing through an Abort command
        sync_quiescent = self.target_obs_state not in [
            ObsState.RESOURCING,
            ObsState.ABORTING,
            ObsState.ABORTED,
            ObsState.RESTARTING,
        ]

        action = self.command_factory.create_assign_resources_action(
            command_input, self.subarray_id, True, sync_quiescent
        ).add_lrc_errors_to_early_stop()

        if sync_quiescent:
            action.add_lrc_completion_to_postconditions()

        return action


# *** STATES THAT SUPPORT ABORT ***
# Rules: other than the normal operational flow,
# they support the Abort command --> we can put it in a super class


class ObsStateSetterSupportsAbort(ObsStateSetter, abc.ABC):
    """Set Observation State starting from a state that supports Abort.

    This (still abstract) class is meant to be used as a base class for
    all the classes that set the observation state starting from a state
    that supports the Abort command. Subclass it and implement
    partially the :py:meth:`next_command` method to define the routing
    rules for the specific state.

    - if the target state is ``ABORTING``, send ``Abort`` synchronising
      on the transient state
    - for any other state, send ``Abort`` synchronising on the quiescent
      state (+ verifying LRC completion and errors)

    LRC errors will always be used as early stop conditions.
    """

    def next_command(self):
        sync_quiescent = self.target_obs_state != ObsState.ABORTING

        action = self.command_factory.create_abort_action(
            self.subarray_id, True, sync_quiescent
        ).add_lrc_errors_to_early_stop()

        if sync_quiescent:
            action.add_lrc_completion_to_postconditions()

        return action


class ObsStateSetterResourcing(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a RESOURCING state.

    Being a transient state, some devices may already be in ``IDLE`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.RESOURCING, ObsState.IDLE]


class ObsStateSetterIdle(ObsStateSetterSupportsAbort):
    """Set Observation State starting from an IDLE state.

    Routing rules:

    - for ``READY`` and ``SCANNING``, I have to ``Configure`` synchronising
      on the quiescent state (and verifying LRC completion)
    - for ``CONFIGURING``, I have to ``Configure`` synchronising on the
      transient state
    - for any other state, I have to ``Abort`` first
      (see :py:class:`ObsStateSetterSupportsAbort`)

    LRC errors will always be used as early stop conditions.
    """

    def next_command(self):
        # if the target state is not one of the consecutive states
        # I Abort first
        if self.target_obs_state not in [
            ObsState.CONFIGURING,
            ObsState.READY,
            ObsState.SCANNING,
        ]:
            return super().next_command()

        command_input = self._get_command_input_or_fail("Configure")

        sync_quiescent = self.target_obs_state != ObsState.CONFIGURING

        action = self.command_factory.create_configure_action(
            command_input, self.subarray_id, True, sync_quiescent
        ).add_lrc_errors_to_early_stop()

        if sync_quiescent:
            action.add_lrc_completion_to_postconditions()

        return action


class ObsStateSetterConfiguring(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a CONFIGURING state.

    Being a transient state, some devices may already be in ``READY`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.CONFIGURING, ObsState.READY]


class ObsStateSetterReady(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a READY state.

    Routing rules:

    - for ``SCANNING``, I have to ``Scan`` synchronising on the transient state
    - for any other state, I have to ``Abort`` first
      (see :py:class:`ObsStateSetterSupportsAbort`)

    LRC errors will always be used as early stop conditions.
    """

    def next_command(self):
        # if the target state is not SCANNING, I Abort first
        if self.target_obs_state != ObsState.SCANNING:
            return super().next_command()

        command_input = self._get_command_input_or_fail("Scan")

        return self.command_factory.create_scan_action(
            command_input, self.subarray_id, True, False
        ).add_lrc_errors_to_early_stop()


class ObsStateSetterScanning(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a SCANNING state.

    Being a transient state, some devices may already be in ``READY`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.SCANNING, ObsState.READY]


class ObsStateSetterResetting(ObsStateSetterSupportsAbort):
    """Set Observation State starting from an RESETTING state.

    Being a transient state, some devices may already be in ``IDLE`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.RESETTING, ObsState.IDLE]


# *** STATES THAT SUPPORT RESTART ***
# Rules: the operational flow has been interrupted, what we can do is
# restart the system to the system to EMPTY state
# (or to the transient RESTARTING state)


class ObsStateSetterSupportsRestart(ObsStateSetter, abc.ABC):
    """Set Observation State starting from a state that supports Restart.

    This (still abstract) class is meant to be used as a base class for
    all the classes that set the observation state starting from a state
    that supports the Restart command. Subclass it and implement
    partially the :py:meth:`next_command` method to define the routing
    rules for the specific state.

    - if the target state is ``RESTARTING``, send ``Restart`` synchronising
      on the transient state
    - for any other state, send ``Restart`` synchronising on the quiescent
      state (+ verifying LRC completion and errors)

    LRC errors will always be used as early stop conditions.
    """

    def next_command(self):
        sync_quiescent = self.target_obs_state != ObsState.RESTARTING

        action = self.command_factory.create_restart_action(
            self.subarray_id, True, sync_quiescent
        ).add_lrc_errors_to_early_stop()

        if sync_quiescent:
            action.add_lrc_completion_to_postconditions()

        return action


class ObsStateSetterFault(ObsStateSetterSupportsRestart):
    """Set Observation State starting from a FAULT state.

    Fault is particular. I am not sure, but I think that if the system
    is in FAULT, some devices may be in any state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsRestart`.
    """

    def _accepted_obs_states_for_devices(self):
        return list(ObsState)


class ObsStateSetterAborted(ObsStateSetterSupportsRestart):
    """Set Observation State starting from an ABORTED state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsRestart`.
    """


# *** REMAINING STATES ***
# Rules: the remaining states are closed ends because I cannot send any
# command to move from them to another state (they simply exist)
# to terminate when the system is in one of these states

# TODO: maybe the action here could be to just wait a postcondition
# to be satisfied (e.g. the system is in the target state)


class ObsStateSetterAborting(ObsStateSetter):
    """Set Observation State starting from an ABORTING state.

    ABORTING is a transient state, so some devices may already be in
    ``ABORTED`` state.

    Routing rules: I cannot send any command to move from ABORTING to
    another state, so next command will always fail.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.ABORTING, ObsState.ABORTED]


class ObsStateSetterRestarting(ObsStateSetter):
    """Set Observation State starting from a RESTARTING state.

    RESTARTING is a transient state, so some devices may already be in
    ``EMPTY`` state.

    Routing rules: I cannot send any command to move from RESTARTING to
    another state, so next command will always fail.
    """

    def _accepted_obs_states_for_devices(self):
        return [ObsState.RESTARTING, ObsState.EMPTY]


# -------------------------------------------------------------------
# Fill the state-class map

STATE_CLASS_MAP[ObsState.EMPTY] = ObsStateSetterEmpty
STATE_CLASS_MAP[ObsState.RESOURCING] = ObsStateSetterResourcing
STATE_CLASS_MAP[ObsState.IDLE] = ObsStateSetterIdle
STATE_CLASS_MAP[ObsState.CONFIGURING] = ObsStateSetterConfiguring
STATE_CLASS_MAP[ObsState.READY] = ObsStateSetterReady
STATE_CLASS_MAP[ObsState.SCANNING] = ObsStateSetterScanning
STATE_CLASS_MAP[ObsState.RESETTING] = ObsStateSetterResetting
STATE_CLASS_MAP[ObsState.FAULT] = ObsStateSetterFault
STATE_CLASS_MAP[ObsState.ABORTED] = ObsStateSetterAborted
STATE_CLASS_MAP[ObsState.ABORTING] = ObsStateSetterAborting
STATE_CLASS_MAP[ObsState.RESTARTING] = ObsStateSetterRestarting
