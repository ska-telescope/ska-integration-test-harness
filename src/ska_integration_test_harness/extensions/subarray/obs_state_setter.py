"""Tools to put the system in a desired observation state."""

import abc

import tango
from ska_control_model import ObsState

from ...core.actions.sut_action import SUTAction
from .obs_state_commands_factory import ObsStateCommandsFactory
from .obs_state_setter_step import (
    ObsStateCommandsInput,
    ObsStateSystemNotConsistent,
)
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


# -------------------------------------------------------------------
# Error classes to be raised when preconditions are not satisfied


class ObsStateSystemNotInExpectedState(AssertionError):
    """Raised when the system is not in the expected observation state."""

    def __init__(
        self,
        expected_state: ObsState,
        current_state: ObsState,
        action: SUTAction,
    ):
        super().__init__(
            f"FAILED ASSUMPTION for action {action.name()} "
            f"({action.description()}): "
            f"The system is expected to be in the observation state "
            f"{str(expected_state)}, but it is observed to be in the state "
            f"{str(current_state)}."
        )


# -------------------------------------------------------------------
# Base class for observation state setters


class ObsStateSetter(SUTAction, abc.ABC):
    """Tool to put the system in a desired observation state.

    This class is a tool to put an observation state-based system
    (:py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSystem`)
    in a desired target :py:class:`~ska_control_model.ObsState` starting
    from (almost) any observation state. The general idea is to pilot
    the system towards the target observation state by sending
    the appropriate commands and synchronising on the right states. The
    commands are created by a
    :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsFactory`
    and the input is given by an :py:class:`~ObsStateCommandsInput` instance.

    The class is abstract, because it is meant to be the base class for
    a set of subclasses, implemented in a way that each subclass represents
    a specific (`starting`) observation state and implements the routing rules
    to move towards the `target` observation state. This idea is not new,
    but it is an application of the
    `State Design Pattern <https://refactoring.guru/design-patterns/state>`_.

    **Usage as an end user**: to use this class, you can just call the
    :py:meth:`get_setter_action` (static) method to get the appropriate
    initial setter action, which can be executed simply by calling the
    :py:meth:`execute` method (passing an appropriate timeout, which will
    be shared by all the commands). The method will automatically
    return the appropriate setter action according to the system's
    current observation state. Example:

    .. code-block:: python

        from ska_integration_test_harness.extensions.subarray import (
            ObsStateSetter
        )

        # (please see the ObsStateSystem protocol)
        system = YourOwnObsStateSystem()

        # get the appropriate setter action
        setter = ObsStateSetter.get_setter_action(
            system,
            ObsState.SCANNING, # your target observation state
            subarray_id=1, # your subarray ID

            # the input for the commands
            commands_input={
                "AssignResources": <...>,
                "Configure": <...>,
                "Scan": <...>,
            },
        )

        # execute the setter action within a shared timeout (e.g. 100 seconds)
        setter.execute(100)

    **Implemented algorithm**: the implemented algorithm is quite simple.
    Intuitively:

    - let's divide our states in three categories:

      - the regular operational flow states
        (``EMPTY, RESOURCING, IDLE, CONFIGURING, READY, SCANNING``)
      - the states for the abort & restart procedure
        (``ABORTING, ABORTED, RESTARTING``)
      - the remaining states

        - ``FAULT``, which in a certain sense can be seen as part
          of the abort & restart procedure, since it
          supports the ``Restart`` command
        - ``RESETTING``, which - in theory - can be aborted and be
          reduced to the abort & restart procedure


    - if in any point of the procedure the system **current state**
      is equal to the **target state**, I just return
    - if the **target state** is in the operational flow and the
      **starting state** "comes before", I just follow the regular
      operational flow. If instead the **target state** "comes after",
      at the moment I abort first and then I follow the regular
      operational flow. At the moment, I abort also if the **initial state**
      is a transient state (``RESOURCING, CONFIGURING, SCANNING``)
    - if the **target state** is in the abort & restart procedure and
      the **starting state** "comes before" or is part of the regular
      operational flow, I just follow the abort & restart procedure.
      If instead the **target state** "comes after", I first terminate
      the abort procedure, then I enter in the regular operational flow
      (``RESOURCING``) to just abort again and then follow the abort &
      restart procedure till I reach the **target state**

    A few exceptional cases (that may be improved in the future):

    - :py:data:`NOT_REACHABLE_STATES` are states that are not reachable
      by the system. If the target state is one of these states, the
      procedure will always raise an exception
    - if the starting state is a transient state in the regular
      operational flow, to reach any state an ``Abort`` command will be called
      first
    - if the starting state is a transient state in the abort & restart
      procedure, at the moment I have no rules to deal with it and the
      procedure will always raise an exception. A slight improvement
      could be to at least try to wait for the transient state to end
    - the regular operational flow is followed just through the
      "main direction"
      (``EMPTY -> RESOURCING -> IDLE -> CONFIGURING -> READY -> SCANNING``),
      not really considering the other possible paths. This is a simplification
      to avoid too complex routing rules

    A further notes about obs-state consistency and preconditions:

    - before sending any command, the system is verified to be in the expected
      current state (the one expected by the class) and also it is verified
      to be in a consistent state (all the devices are in an accepted state,
      or at least in a state that can be accepted by the class). All this
      logic is encoded in the :py:meth:`verify_preconditions` method
    - since this class is a
      :py:class:`~ska_integration_test_harness.core.actions.SUTAction`,
      the preconditions are verified before executing the action and a failure
      will be raised if they are not satisfied. Conceptually, this means this
      classes structure is meant to deal **only with cases where the system
      is in a consistent state**. If it detects an inconsistency, it will
      fail.

    **Extending the class**: this class structure is designed to be
    easily extensible and overrideable. You can extend the class by
    creating new subclasses that represent new (or existing) observation
    states, implement the routing rules in the :py:meth:`next_command`
    method and then add the new class to the :py:data:`STATE_CLASS_MAP` data
    structure (which maps the observation states to the classes that
    support them as starting states). You can also override the
    :py:meth:`_accepted_obs_states_for_devices` method to define which
    observation states for the devices are handled by the class. Potentially,
    you can override any other method to implement more complex behaviours.
    Here an example on how you can override the routing rules for the
    ``IDLE`` state to reach ``EMPTY`` or ``RESOURCING`` by the
    ``ReleaseAllResources`` command:

    .. code-block:: python

        from ska_control_model import ObsState
        from ska_integration_test_harness.extensions.subarray.obs_state_setter import (
            ObsStateSetterFromIdle, STATE_CLASS_MAP
        )

        class CustomObsStateSetterFromIdle(ObsStateSetterFromIdle):

            def next_command(self):
                # the particular target states I want to deal are
                # EMPTY and RESOURCING. If the target state is not
                # one of these, I can just call the superclass method
                # and use the default routing rules
                if not self.target_obs_state in [
                    ObsState.EMPTY, ObsState.RESOURCING
                ]:
                    return super().next_command()

                # To reach EMPTY or RESOURCING from IDLE, I just
                # need to release all resources.
                # To do so, I just have to be careful to synchronise
                # on the transient state only (if the target state is
                # RESOURCING) or on the quiescent state + LRC completion
                # (if the target state is EMPTY)

                sync_quiescent = self.target_obs_state != ObsState.RESOURCING

                action = self.command_factory.create_release_all_resources_action(
                    self.subarray_id, True, sync_quiescent
                ).add_lrc_errors_to_early_stop()

                if sync_quiescent:
                    action.add_lrc_completion_to_postconditions()

                return action

        # add the new class to the STATE_CLASS_MAP, overriding the IDLE state
        STATE_CLASS_MAP[ObsState.IDLE] = CustomObsStateSetterFromIdle

        # (now if I call get_setter_action my custom class will be used
        # if I happen to pass through the IDLE state)

    **Final notes on the status of this class structure**: this class and
    the whole structure is a first implementation of a tool to manage the
    the observation state transitions. However, it still have weaknesses
    and limitations. For example:

    - The routing rules are quite simple and sometimes you make useless
      aborts and restarts (sometimes this may be necessary, but sometimes
      it is just a waste of time; I opted for the simplicity and for
      the solution that is more likely to work in most cases).
      **CURRENT WORKAROUND**: you can override the routing rules
      (the :py:meth:`next_command` method) to implement more complex
      routing rules
    - The consistency checks are quite simple and sometimes you may want
      something more strict and also the fact that the consistency is verified
      as precondition does not exclude the possibility of inconsistencies
      at the time a command is sent. Also, it may happen sometime that
      you are in a transient state and when you send a command you are
      already in the quiescent state. **CURRENT WORKAROUND**:
      To some extent, those
      limitations cannot really be solved because they are inherent
      to the distributed nature of the system. However, you can
      override the :py:meth:`verify_preconditions` method to
      implement some stricter or weaker checks, or can you just run
      this action using a retry mechanism to deal with errors coming
      from commands sended from the wrong state.

    """  # pylint: disable=line-too-long # noqa: E501

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
        current_obs_state = ObsStateSetter._read_obs_state(
            system.get_main_obs_state_device(subarray_id)
        )

        # fail if the current observation state is not supported
        # or if the target observation state is not reachable
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

        # create the appropriate setter action according to the mapping
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
            f"from {str(self.assumed_class_obs_state())} "
            f"to {str(self.target_obs_state)}."
        )

    def assumed_class_obs_state(self):
        """Return the observation state that is expected by the class.

        To perform the observation state set procedure, the class assumes
        the system is in a certain observation state. This method returns
        the observation state that is expected by the class. By default,
        we can just read it from the
        :py:data:`STATE_CLASS_MAP` data structure.

        :return: the observation state expected by the class as a
            starting point for the observation state set procedure

        :raise RuntimeError: if the class is not correctly inserted in the
            STATE_CLASS_MAP (this is a bug in the class structure)
        """
        # find the key in STATE_CLASS_MAP that points to the class
        # that is the current class
        for key, value in STATE_CLASS_MAP.items():
            if value == self.__class__:
                return key

        raise RuntimeError(
            f"The given class {self.__class__} is not correctly "
            "inserted in the STATE_CLASS_MAP. "
            "This is a bug in the class structure. Please read carefully "
            "the documentation and the examples."
        )

    def verify_preconditions(self):
        """Verify the system is in a consistent observation state.

        The system is in a consistent observation state if all the devices
        are in an accepted observation state (as defined by the class
        through the
        :py:meth:`accepted_obs_states_for_devices` method).

        :raise ObsStateSystemNotConsistent: if the system is not in a
            consistent observation state
        """
        super().verify_preconditions()

        device_obs_states = self._devices_obs_state()

        for _, obs_state in device_obs_states.items():
            if obs_state not in self.accepted_obs_states_for_devices():
                raise ObsStateSystemNotConsistent(
                    self.assumed_class_obs_state(), device_obs_states, self
                )

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
        # if the system is already in the target observation state, terminate
        if self._system_obs_state() == self.target_obs_state:
            return

        # ensure target state is reachable
        if self.target_obs_state in NOT_REACHABLE_STATES:
            raise NotImplementedError(
                f"Failure in {self.name()} action ({self.description()}): "
                f"The target observation state {str(self.target_obs_state)} "
                "is not reachable by current decision rules."
            )

        # if this class is the expected starting point, execute (a step of)
        # the procedure. Otherwise skip and delegate to the next setter
        if self._system_obs_state() == self.assumed_class_obs_state():

            # compute the command that should be run
            command = self.next_command()
            command.set_logging(not self.logger.disabled)

            # run the command
            command.execute(
                self._last_execution_params["postconditions_timeout"],
                self._last_execution_params["verify_preconditions"],
            )

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
            f"({self.assumed_class_obs_state()})."
        )

    # -------------------------------------------------------------------
    # Internal utilities for the class

    def _system_obs_state(self) -> ObsState:
        """Return the current observation state of the system.

        :return: the current observation state of the system, read from the
            coordinator device (which observation state should be
            representative for the whole system).
        """
        return self._read_obs_state(
            self.system.get_main_obs_state_device(self.subarray_id)
        )

    def _devices_obs_state(self) -> dict[tango.DeviceProxy, ObsState]:
        """Return the observation state of all the devices.

        :return: a dictionary with the devices and their observation states
        """
        return {
            device: self._read_obs_state(device)
            for device in self.system.get_obs_state_devices(self.subarray_id)
        }

    @staticmethod
    def _read_obs_state(device: tango.DeviceProxy) -> ObsState:
        """Read the observation state from a device.

        :param device: the device to read the observation state from
        :return: the observation state
        """
        return ObsState(device.obsState)

    def accepted_obs_states_for_devices(self) -> list[ObsState]:
        """Define the accepted observation states for the devices.

        This method defines which observation states for the devices are
        handled by the class. The method should return a list of observation
        states that are accepted by the class.

        By default, the only accepted observation state is the one defined
        in the state-class mapping. Subclasses can override this method
        to define more accepted observation states.

        :return: the list of accepted observation states
        """
        return [self.assumed_class_obs_state()]

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


class ObsStateSetterFromEmpty(ObsStateSetter):
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


class ObsStateSetterFromResourcing(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a RESOURCING state.

    Being a transient state, not all devices may be in ``RESOURCING`` state.
    Some devices may still be in ``EMPTY`` state,
    while others may already be in ``IDLE`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def accepted_obs_states_for_devices(self):
        return [ObsState.EMPTY, ObsState.RESOURCING, ObsState.IDLE]


class ObsStateSetterFromIdle(ObsStateSetterSupportsAbort):
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


class ObsStateSetterFromConfiguring(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a CONFIGURING state.

    Being a transient state, not all devices may be in ``CONFIGURING`` state.
    Some devices may still be in ``IDLE`` state, while others may already
    be in ``READY`` state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def accepted_obs_states_for_devices(self):
        return [ObsState.IDLE, ObsState.CONFIGURING, ObsState.READY]


class ObsStateSetterFromReady(ObsStateSetterSupportsAbort):
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


class ObsStateSetterFromScanning(ObsStateSetterSupportsAbort):
    """Set Observation State starting from a SCANNING state.

    Being a transient state, not all devices may be in ``SCANNING`` state.
    Some devices may already be in ``READY`` state (because they already
    completed the scan or because they are not yet started).

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def accepted_obs_states_for_devices(self):
        return [ObsState.SCANNING, ObsState.READY]


class ObsStateSetterFromResetting(ObsStateSetterSupportsAbort):
    """Set Observation State starting from an RESETTING state.

    Resetting is not really a supported state. In this case we assume
    consistency every time we enter in this state. Override with
    your own rules if you need to.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsAbort`.
    """

    def accepted_obs_states_for_devices(self):
        return list(ObsState)


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


class ObsStateSetterFromFault(ObsStateSetterSupportsRestart):
    """Set Observation State starting from a FAULT state.

    Fault is a particular state. I am not sure, but I think that if the system
    is in FAULT, devices may potentially be in any state. At the moment,
    we will assume it's like that. Override with your own rules if you need to.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsRestart`.
    """

    def accepted_obs_states_for_devices(self):
        return list(ObsState)


class ObsStateSetterFromAborted(ObsStateSetterSupportsRestart):
    """Set Observation State starting from an ABORTED state.

    Routing rules are the ones from :py:class:`ObsStateSetterSupportsRestart`.
    """


# *** REMAINING STATES ***
# Rules: the remaining states are closed ends because I cannot send any
# command to move from them to another state (they simply exist)
# to terminate when the system is in one of these states

# TODO: maybe the action here could be to just wait a postcondition
# to be satisfied (e.g. the system is in the target state)


class ObsStateSetterFromAborting(ObsStateSetter):
    """Set Observation State starting from an ABORTING state.

    ``ABORTING`` is a transient state, so some devices may already be in
    ``ABORTED`` state. Some devices may also still be in the previous
    state (any state that supports the ``Abort`` command,
    so ``RESOURCING, IDLE, CONFIGURING, READY, SCANNING, RESETTING``,
    but also ``EMPTY``, since an ``AssignResources`` or a ``ReleaseResources``
    command may have been sent).


    Routing rules: I cannot send any command to move from ABORTING to
    another state, so next command will always fail.
    """

    def accepted_obs_states_for_devices(self):
        return [
            ObsState.ABORTING,
            ObsState.ABORTED,
            # states that support abort
            # pylint: disable=duplicate-code
            ObsState.RESOURCING,
            ObsState.IDLE,
            ObsState.CONFIGURING,
            ObsState.READY,
            ObsState.SCANNING,
            ObsState.RESETTING,
            # states that may still be in the previous state of transient
            # states that support the Abort command
            ObsState.EMPTY,
        ]


class ObsStateSetterFromRestarting(ObsStateSetter):
    """Set Observation State starting from a RESTARTING state.

    ``RESTARTING`` is a transient state, so some devices may already be in
    ``EMPTY`` state. Some devices may also still be in the previous
    state (any state that supports the ``Restart`` command,
    so ``FAULT, RESETTING``).

    Routing rules: I cannot send any command to move from RESTARTING to
    another state, so next command will always fail.
    """

    def accepted_obs_states_for_devices(self):
        return [
            ObsState.RESTARTING,
            ObsState.EMPTY,
            ObsState.FAULT,
            ObsState.RESETTING,
        ]


# -------------------------------------------------------------------
# Fill the state-class map

STATE_CLASS_MAP[ObsState.EMPTY] = ObsStateSetterFromEmpty
STATE_CLASS_MAP[ObsState.RESOURCING] = ObsStateSetterFromResourcing
STATE_CLASS_MAP[ObsState.IDLE] = ObsStateSetterFromIdle
STATE_CLASS_MAP[ObsState.CONFIGURING] = ObsStateSetterFromConfiguring
STATE_CLASS_MAP[ObsState.READY] = ObsStateSetterFromReady
STATE_CLASS_MAP[ObsState.SCANNING] = ObsStateSetterFromScanning
STATE_CLASS_MAP[ObsState.RESETTING] = ObsStateSetterFromResetting
STATE_CLASS_MAP[ObsState.FAULT] = ObsStateSetterFromFault
STATE_CLASS_MAP[ObsState.ABORTED] = ObsStateSetterFromAborted
STATE_CLASS_MAP[ObsState.ABORTING] = ObsStateSetterFromAborting
STATE_CLASS_MAP[ObsState.RESTARTING] = ObsStateSetterFromRestarting
