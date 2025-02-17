"""Exceptions for the subarray common extension.

This module contains the exceptions that are used by
:py:mod:`~ska_integration_test_harness.extensions.subarray` to signal
problems in the observation state management, togheter with some
tips and guidelines on how to troubleshoot them.

TODO: improve troubleshooting guidelines.
"""

import tango
from ska_control_model import ObsState

from ska_integration_test_harness.core.actions.sut_action import SUTAction

from .inputs import ObsStateCommandsInput
from .system import ObsStateSystem, read_devices_obs_state, read_sys_obs_state


class ObsStateCommandDoesNotExist(ValueError):
    """Exception raised when a command is not found in the map."""

    def __init__(self, command_name: str):
        """Create a new exception instance.

        :param command_name: the name of the command
        """
        super().__init__(
            f"Command '{command_name}' does not exist or is not supported."
        )


class ObsStateCommandHasNoTransition(ValueError):
    """Exception raised when a command has no transition in the map."""

    def __init__(self, command_name: str, transition_type: str):
        """Create a new exception instance.

        :param command_name: the name of the command
        :param transition_type: the type of the transition
            (e.g. "transient" or "quiescent")
        """
        super().__init__(
            f"Command '{command_name}' hasn't a {transition_type} "
            "obsState transition."
        )


class ObsStateMissingCommandInput(ValueError):
    """Raised when a command input is missing.

    If you see this raised while using some class, probably you forgot to
    set the input for a command. Check the input object you are using
    in your setter constructor or in the setter method. If you are not
    sure on which input to use, check the documentation of the input
    class :py:class:`~ObsStateCommandsInput` for the correct structure.
    """

    def __init__(
        self,
        command_name: str,
        inputs: ObsStateCommandsInput,
        action: SUTAction,
    ):
        """Initializes the exception.

        :param command_name: The name of the command that is missing an input.
        :param inputs: The input object that is missing the input.
        :param action: The action that is missing the input.
        """
        super().__init__(
            f"FAILED ASSUMPTION for action {action.name()} "
            f"({action.description()}): "
            f"Missing input for command {command_name} "
            f"in obs state inputs: {inputs.model_dump()}"
        )


class ObsStateSystemNotConsistent(AssertionError):
    """Raised when the system is not in a consistent observation state.

    If you see this raised while using some class it means that the system
    has been found in an inconsistent observation state. Conceptually, an
    inconsistent observation state is when one or more of your subarray
    devices are in a state that is not compatible with the state you
    assume to be in.

    For quiescent/stable states, it means that one or more devices are
    not in the expected state (e.g., if the expected state is ``IDLE``,
    but one device is still stuck in ``CONFIGURING`` or is in some unexpected
    state like ``FAULT`` or ``ABORTING``).

    For transient states, the pool of accepted states is usually wider,
    since we configured the classes to accept also eventual previous and
    next states. So if it fails it means that one or more devices are
    not in the set of accepted states.

    To conclude, if you see this error please analyse carefully the log
    and the state of the devices to understand what is going wrong.
    """

    def __init__(
        self,
        expected_state: ObsState,
        observed_states: dict[tango.DeviceProxy, ObsState],
        action: SUTAction,
        failure_kind: str = "FAILED ASSUMPTION for action ",
    ):
        """Initializes the exception.

        :param expected_state: The expected observation state.
        :param observed_states: The observed observation states.
        :param action: The action that failed the assumption.
        :param failure_kind: The kind of failure. It is used as a preamble
            to the error message. Default is "FAILED ASSUMPTION for action ".

        """
        msg = (
            f"{failure_kind}{action.name()} - "
            f"({action.description()}):\n"
            f"The system is expected to be in a consistent observation state "
            f"{str(expected_state)}, but it is observed to be in an "
            "inconsistent state: "
        )

        msg += ", ".join(
            [
                f"{device.dev_name()}={str(obs_state)}"
                for device, obs_state in observed_states.items()
            ]
        )
        super().__init__(msg)


class ObsStateDidNotReachTargetState(AssertionError):
    """Exception for when the system did not reach the target state.

    Exception to raise when the system did not reach the target state
    after a
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    action is executed. It specifically is raised when a system main device
    ``obsState`` attribute value is not equal to the expected target state.
    """

    def __init__(
        self,
        expected_state: ObsState,
        subarray_id: int,
        system: ObsStateSystem,
        action: SUTAction,
    ):
        self.expected_state = expected_state
        self.subarray_id = subarray_id
        self.actual_state = read_sys_obs_state(system, subarray_id)
        self.devices_states = read_devices_obs_state(system, subarray_id)
        self.action = action

        msg = (
            f"Failed postcondition in action "
            f"{action.name()} - {action.description()}:\n"
            f"The subarray {self.subarray_id} (represented by "
            f"{system.get_main_obs_state_device().dev_name()}) "
            "after the action completion is expected to be in the "
            f"target observation state {str(expected_state)}, "
            f"but is in {str(self.actual_state)}.\n"
            "Devices state: "
        )

        msg += "\n".join(
            f"{dev.dev_name()}={str(state)}"
            for dev, state in self.devices_states.items()
        )

        super().__init__(msg)
