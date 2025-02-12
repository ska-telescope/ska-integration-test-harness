"""Implementations for the subarray setter steps.

This module contains concrete implementations for the steps that set the
observation state of a subarray system. Each class is meant to handle the
procedure from a specific starting state. E.g.,

:py:class:`~ska_integration_test_harness.extensions.subarray.setter_steps.ObsStateSetterStepFromEmpty`
assumes the system is in the EMPTY state, etc.

Some of those classed directly inherit from
:py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`,
while other are grouped under more specific abstract classes, like
:py:class:`~ska_integration_test_harness.extensions.subarray.setter_steps.ObsStateSetterStepSupportsAbort`
or
:py:class:`~ska_integration_test_harness.extensions.subarray.setter_steps.ObsStateSetterStepSupportsRestart`
(useful to group states that support the ``Abort`` or ``Restart`` commands).

See :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`
for more details on the purpose and characteristics of these classes.
"""  # pylint: disable=line-too-long # noqa: E501

import abc

from ska_control_model import ObsState

from ...core.actions.sut_action import SUTAction
from .obs_state_setter_step import ObsStateSetterStep

# -------------------------------------------------------------------
# *** EMPTY ***
# Rules: simple, just begin the normal operational flow


class ObsStateSetterStepFromEmpty(ObsStateSetterStep):
    """Step to handle transitions from EMPTY state.

    From an empty state, whatever the target state is (except
    ``EMPTY`` and unsupported states), the system should just
    begin the normal operational flow.

    Routing rules:
    - If the target state is ``RESOURCING`` (or something that will
      require immediate abort), send ``AssignResources``
      synchronizing on the transient state.
    - Any other state is supposed to be reached passing through ``IDLE``,
      so I send ``AssignResources`` synchronizing on the quiescent state
      (+ verifying LRC completion and errors).

    LRC errors will always be used as early stop conditions.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.EMPTY

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        return self.get_subarray_command_action(
            self.subarray_id,
            "AssignResources",
            self.commands_inputs.AssignResources,
            # I synchronise on the the transient state if my target
            # is RESOURCING or if I already know I will have to
            # abort immediately
            sync_transient=(
                target_state
                in [
                    ObsState.RESOURCING,
                    ObsState.ABORTING,
                    ObsState.ABORTED,
                    ObsState.RESTARTING,
                ]
            ),
        )


# -------------------------------------------------------------------
# *** STATES THAT SUPPORT ABORT ***


class ObsStateSetterStepSupportsAbort(ObsStateSetterStep, abc.ABC):
    """Step to handle transitions from states that support Abort.

    Routing rules:
    - If the target state is ``ABORTING``, send ``Abort`` synchronizing
      on the transient state.
    - For any other state, send ``Abort`` synchronizing on the quiescent
      state (+ verifying LRC completion and errors).

    LRC errors will always be used as early stop conditions.
    """

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        return self.get_subarray_command_action(
            self.subarray_id,
            "Abort",
            sync_transient=(target_state == ObsState.ABORTING),
        )


class ObsStateSetterStepFromIdle(ObsStateSetterStepSupportsAbort):
    """Step to handle transitions from an IDLE state.

    Routing rules:
    - For ``READY`` and ``SCANNING``, I have to ``Configure`` synchronizing
      on the quiescent state (and verifying LRC completion).
    - For ``CONFIGURING``, I have to ``Configure`` synchronizing on the
      transient state.
    - For any other state, I have to ``Abort`` first.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.IDLE

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        if target_state not in [
            ObsState.CONFIGURING,
            ObsState.READY,
            ObsState.SCANNING,
        ]:
            return super().get_next_action(target_state)

        return self.get_subarray_command_action(
            self.subarray_id,
            "Configure",
            self.commands_inputs.Configure,
            sync_transient=(target_state == ObsState.CONFIGURING),
        )


class ObsStateSetterStepFromReady(ObsStateSetterStepSupportsAbort):
    """Step to handle transitions from a READY state.

    Routing rules:
    - If the target state is ``SCANNING``, I have to ``Scan`` synchronizing
      on the transient state.
    - For any other state, I have to ``Abort`` first.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.READY

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        if target_state != ObsState.SCANNING:
            return super().get_next_action(target_state)

        return self.get_subarray_command_action(
            self.subarray_id,
            "Scan",
            self.commands_inputs.Scan,
            sync_transient=True,
        )


# -------------------------------------------------------------------
# *** TRANSIENT STATES THAT SUPPORT ABORT ***


class ObsStateSetterStepFromResourcing(ObsStateSetterStepSupportsAbort):
    """Step to handle transitions from a RESOURCING state.

    Being a transient state, not all devices may be in ``RESOURCING`` state.
    Some devices may still be in ``EMPTY`` state,
    while others may already be in ``IDLE`` state.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.RESOURCING

    def get_accepted_obs_states(self) -> list[ObsState]:
        return [ObsState.EMPTY, ObsState.RESOURCING, ObsState.IDLE]


class ObsStateSetterStepFromConfiguring(ObsStateSetterStepSupportsAbort):
    """Step to handle transitions from a CONFIGURING state.

    Being a transient state, not all devices may be in ``CONFIGURING`` state.
    Some devices may still be in ``IDLE`` state, while others may already
    be in ``READY`` state.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.CONFIGURING

    def get_accepted_obs_states(self) -> list[ObsState]:
        return [ObsState.IDLE, ObsState.CONFIGURING, ObsState.READY]


class ObsStateSetterStepFromScanning(ObsStateSetterStepSupportsAbort):
    """Step to handle transitions from a SCANNING state.

    Being a transient state, not all devices may be in ``SCANNING`` state.
    Some devices may already be in ``READY`` state (because they already
    completed the scan or because they are not yet started).
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.SCANNING

    def get_accepted_obs_states(self) -> list[ObsState]:
        return [ObsState.SCANNING, ObsState.READY]


# -------------------------------------------------------------------
# *** STATES THAT SUPPORT RESTART ***


class ObsStateSetterStepSupportsRestart(ObsStateSetterStep, abc.ABC):
    """Step to handle transitions from states that support Restart.

    Routing rules:
    - If the target state is ``RESTARTING``, send ``Restart`` synchronizing
      on the transient state.
    - For any other state, send ``Restart`` synchronizing on the quiescent
      state (+ verifying LRC completion and errors).
    """

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        return self.get_subarray_command_action(
            self.subarray_id,
            "Restart",
            sync_transient=(target_state == ObsState.RESTARTING),
        )


class ObsStateSetterStepFromFault(ObsStateSetterStepSupportsRestart):
    """Step to handle transitions from a FAULT state.

    A FAULT state may have devices in unpredictable states.
    This implementation assumes all states are acceptable.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.FAULT

    def get_accepted_obs_states(self) -> list[ObsState]:
        return list(ObsState)


class ObsStateSetterStepFromAborted(ObsStateSetterStepSupportsRestart):
    """Step to handle transitions from an ABORTED state."""

    def get_step_obs_state(self) -> ObsState:
        return ObsState.ABORTED


# -------------------------------------------------------------------
# *** OTHER STATES ***


class ObsStateSetterStepFromAborting(ObsStateSetterStep):
    """Step to handle transitions from an ABORTING state.

    Being a transient state, not all devices may be in ``ABORTING`` state.
    Some devices may already be in ``ABORTED`` state, while some others
    may still be in the previous state (
    ``RESOURCING``, ``IDLE``, ``CONFIGURING``, ``READY``, ``SCANNING``,
    ``RESETTING``).

    At the moment, no procedure is defined to exit from this state.
    In future we may attempt a wait operation.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.ABORTING

    def get_accepted_obs_states(self) -> list[ObsState]:
        return [
            ObsState.RESOURCING,
            ObsState.IDLE,
            ObsState.CONFIGURING,
            ObsState.READY,
            ObsState.SCANNING,
            ObsState.RESETTING,
            ObsState.ABORTING,
            ObsState.ABORTED,
        ]

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        raise NotImplementedError(
            "No procedure yet defined to exit from ABORTING state."
        )


class ObsStateSetterStepFromRestarting(ObsStateSetterStep):
    """Step to handle transitions from a RESTARTING state.

    Being a transient state, not all devices may be in ``RESTARTING`` state.
    Some devices may already be in ``EMPTY`` state, while some others
    may still be in ``ABORTED`` or in ``FAULT`` state.

    At the moment, no procedure is defined to exit from this state.
    In future we may attempt a wait operation.
    """

    def get_step_obs_state(self) -> ObsState:
        return ObsState.RESTARTING

    def get_accepted_obs_states(self) -> list[ObsState]:
        return [ObsState.EMPTY, ObsState.ABORTED, ObsState.FAULT]

    def get_next_action(self, target_state: ObsState) -> SUTAction:
        raise NotImplementedError(
            "No procedure yet defined to exit from RESTARTING state."
        )
