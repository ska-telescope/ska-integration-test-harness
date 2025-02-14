"""Test to verify the setter calls the correct commands sequences.

This module contains a set of tests to verify that the ``ObsStateSetter``
is able to move the system through a sequence of states by executing a
sequence of commands.

See the test class for more details.
"""

import pytest
from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout

from ska_integration_test_harness.core.assertions.dev_state_changes import (
    AssertDevicesStateChanges,
)
from ska_integration_test_harness.extensions.subarray.setter import (
    ObsStateSetter,
)
from ska_integration_test_harness.extensions.subarray.setter_step import (
    ObsStateCommandsInput,
)

from .utils import (
    MockSubarraySystem,
    MockTangoLRCAction,
    MockTangoLRCActionPatcher,
)


class MoveMockSystemThroughStates:
    """A side effect for moving the system through states.

    This class is a callable object and every time it's called, it moves the
    system to the next state in the list.

    At each step the system devices (and the controller)
    are moved to the same state.
    """

    def __init__(
        self, system: MockSubarraySystem, states_sequence: list[ObsState]
    ):
        """Initialise the side effect with the system and the states sequence.

        :param system: The system to move through states.
        :param states_sequence: The sequence of states to move through. The
            first state is the initial state of the system.
        """
        self.system = system
        self.states_sequence = states_sequence
        self.current_state_index = 0

        self.move_system_to_current_index()

    def move_system_to_current_index(self):
        """Move the system to the current state."""
        current_state = self.states_sequence[self.current_state_index]
        self.system.set_controller_obs_state(current_state)
        self.system.set_obs_state_other_devices(current_state)

    def __call__(self, *args, **kwargs):
        """Move the system to the next state."""
        self.current_state_index += 1
        self.move_system_to_current_index()


def assert_command_has_postcondition_for_state(
    command: MockTangoLRCAction, expected_state: ObsState
):
    """Assert that the command has a postcondition for the target state.

    :param command: The command to verify.
    :param expected_state: The expected state for the postcondition.
    """
    for postcondition in command.postconditions:
        if (
            isinstance(postcondition, AssertDevicesStateChanges)
            and postcondition.attribute_name == "obsState"
            and postcondition.attribute_value == expected_state
        ):
            return

    raise AssertionError(
        f"The command {command} has no postcondition "
        f"for the expected state {expected_state}."
    )


def get_position_from_index(index) -> str:
    """Get a semantic position from an index.

    :param index: The index to convert to a position (starting from 0).
    :return: The position as a string
        (0 -> 1st, 1 -> 2nd, 2 -> 3rd, 3 -> 4th, ...)
    """
    position = index + 1
    if position == 1:
        return "1st"
    if position == 2:
        return "2nd"
    if position == 3:
        return "3rd"
    return f"{position}th"


def assert_command_and_postcondition(
    commands: list[MockTangoLRCAction],
    index: int,
    expected_command_name: str,
    expected_state: ObsState,
):
    """Assert that the index-th command is as expected.

    :param commands: The list of commands to verify.
    :param index: The index of the command to verify.
    :param expected_command_name: The expected name of the command.
    :param expected_state: The expected state for the postcondition.
    """
    position = get_position_from_index(index)
    assert_that(commands[index].command_name).described_as(
        f"The {position} command is expected to be {expected_command_name}"
    ).is_equal_to(expected_command_name)
    assert_command_has_postcondition_for_state(commands[index], expected_state)


@pytest.mark.extensions
class TestObsStateSetterSequences:
    """Test to verify the setter calls the correct commands sequences.

    This set of tests is quite peculiar, because it verifies the
    ``ObsStateSetter`` capability to move the system through a sequence
    of states by executing a sequence of commands. To do this without
    actually executing the commands and without actually having real
    devices, we use a couple of tricks:

    - we use ``MockTangoLRCActionPatcher``, a utility class that permits to
      patch the ``TangoLRCAction`` in a way that each instance 1) is
      tracked, 2) receives all the passed parameters as it was a real
      one, 3) can be injected with a side effect
    - we use ``MoveMockSystemThroughStates``, a callable that when called
      moves the system through a preset sequence of states, which can be
      used as a side effect for the ``MockTangoLRCAction`` instances

    Through the combination of these two tricks, we can collect the commands
    ``ObsStateSetter`` executes, verify that they are the expected ones and
    verify their postconditions.

    This set of tests, of course, assumes the correctness of the fact that
    a certain - opportunely synchronised - sequence of commands is able to
    move the system through the given states (in a certain sense, we assume
    the tests respect the observation state machine).

    This set of tests is complementary to the tests in ``TestObsStateSetter``.

    The following cases are covered:

    - ensure the action succeeds immediately if already in the target state
      from all possible starting states (disabling the preconditions check
      so also the not supported target states are tested)
    - move the system from EMPTY to CONFIGURING (normal operational sequence)
    - move the system from IDLE to SCANNING (normal operational sequence)
    - move the system from READY to IDLE (abort-restart sequence)
    - move the system from CONFIGURING to READY (abort sequence)
    - move the system from ABORTED to ABORTING (restart-assign-abort sequence)
    - move the system from FAULT to RESOURCING (restart-assign sequence)
    - move the system from RESETTING to RESTARTING (abort-restart sequence)
    - move the system from SCANNING to ABORTED (abort sequence)
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    @staticmethod
    @pytest.mark.parametrize("target_state", list(ObsState))
    def test_execute_succeds_immediately_if_already_in_target_state(
        system: MockSubarraySystem, target_state: ObsState
    ):
        """The action succeeds immediately if already in target state."""
        setter = ObsStateSetter(system, target_state)
        system.set_controller_obs_state(target_state)
        system.set_obs_state_other_devices(target_state)

        patcher = MockTangoLRCActionPatcher()
        with patcher.patch():
            setter.execute(verify_preconditions=False)

        assert_that(patcher.instances).described_as(
            "No command is expected to be called"
        ).is_empty()

    @staticmethod
    def test_execute_from_empty_to_configuring(system: MockSubarraySystem):
        """The action is able to move the system from EMPTY to CONFIGURING.

        - states sequence: EMPTY -> IDLE -> CONFIGURING
        - commands sequence: AssignResources -> Configure
        """
        commands_input = ObsStateCommandsInput(
            AssignResources='{"dummy": 0}', Configure='{"dummy": 1}'
        )
        setter = ObsStateSetter(
            system, ObsState.CONFIGURING, commands_input=commands_input
        )
        timeout = ChainedAssertionsTimeout(10)

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system, [ObsState.EMPTY, ObsState.IDLE, ObsState.CONFIGURING]
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute(timeout)

        assert_that(patcher.instances).described_as(
            "Two commands are expected to be executed"
        ).is_length(2)

        # **************************************************************
        # 1) Verify Assign Resources command

        assert_that(patcher.instances[0].command_name).described_as(
            "The first command is expected to be AssignResources"
        ).is_equal_to("AssignResources")
        assert_that(patcher.instances[0].target_device).described_as(
            "The first command is expected to target the subarray controller"
        ).is_equal_to(system.subarray_controller)
        assert_that(patcher.instances[0].command_param).described_as(
            "The first command is expected to have the correct input"
        ).is_equal_to('{"dummy": 0}')
        patcher.instances[0].execute.assert_called_once()
        patcher.instances[0].execute.assert_called_once_with(
            timeout, True, True
        )
        assert_command_has_postcondition_for_state(
            patcher.instances[0], ObsState.IDLE
        )

        # **************************************************************
        # 2) Verify Configure command

        assert_that(patcher.instances[1].command_name).described_as(
            "The second command is expected to be Configure"
        ).is_equal_to("Configure")
        assert_that(patcher.instances[1].target_device).described_as(
            "The second command is expected to target the subarray controller"
        ).is_equal_to(system.subarray_controller)
        assert_that(patcher.instances[1].command_param).described_as(
            "The second command is expected to have the correct input"
        ).is_equal_to('{"dummy": 1}')
        patcher.instances[1].execute.assert_called_once()
        patcher.instances[1].execute.assert_called_once_with(
            timeout, True, True
        )
        assert_command_has_postcondition_for_state(
            patcher.instances[1], ObsState.CONFIGURING
        )

    @staticmethod
    def test_execute_from_idle_to_scanning(system: MockSubarraySystem):
        """The action is able to move the system from IDLE to SCANNING.

        - states sequence: IDLE -> READY -> SCANNING
        - commands sequence: Configure -> Scan
        """
        commands_input = ObsStateCommandsInput(
            Configure='{"dummy": 1}', Scan='{"dummy": 2}'
        )
        setter = ObsStateSetter(
            system, ObsState.SCANNING, commands_input=commands_input
        )

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system, [ObsState.IDLE, ObsState.READY, ObsState.SCANNING]
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Two commands are expected"
        ).is_length(2)
        assert_command_and_postcondition(
            patcher.instances, 0, "Configure", ObsState.READY
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "Scan", ObsState.SCANNING
        )

    @staticmethod
    def test_execute_from_ready_to_idle(system: MockSubarraySystem):
        """The action is able to move the system from READY to IDLE.

        - states sequence: READY -> ABORTED -> EMPTY -> IDLE
        - commands sequence: Abort -> Restart -> AssignResources
        """
        commands_input = ObsStateCommandsInput(
            AssignResources='{"dummy": 3}',
        )
        setter = ObsStateSetter(
            system, ObsState.IDLE, commands_input=commands_input
        )

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system,
            [ObsState.READY, ObsState.ABORTED, ObsState.EMPTY, ObsState.IDLE],
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Three commands are expected to be executed"
        ).is_length(3)
        assert_command_and_postcondition(
            patcher.instances, 0, "Abort", ObsState.ABORTED
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "Restart", ObsState.EMPTY
        )
        assert_command_and_postcondition(
            patcher.instances, 2, "AssignResources", ObsState.IDLE
        )

    @staticmethod
    def test_execute_from_configuring_to_ready(system: MockSubarraySystem):
        """The action is able to move the system from CONFIGURING to READY.

        - states sequence: CONFIGURING -> ABORTED -> EMPTY -> IDLE -> READY
        - commands sequence: Abort -> Restart -> AssignResources -> Configure
        """
        commands_input = ObsStateCommandsInput(
            AssignResources='{"dummy": 3}', Configure='{"dummy": 4}'
        )
        setter = ObsStateSetter(
            system, ObsState.READY, commands_input=commands_input
        )

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system,
            [
                ObsState.CONFIGURING,
                ObsState.ABORTED,
                ObsState.EMPTY,
                ObsState.IDLE,
                ObsState.READY,
            ],
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Four commands are expected"
        ).is_length(4)
        assert_command_and_postcondition(
            patcher.instances, 0, "Abort", ObsState.ABORTED
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "Restart", ObsState.EMPTY
        )
        assert_command_and_postcondition(
            patcher.instances, 2, "AssignResources", ObsState.IDLE
        )
        assert_command_and_postcondition(
            patcher.instances, 3, "Configure", ObsState.READY
        )

    @staticmethod
    def test_execute_from_aborted_to_aborting(system: MockSubarraySystem):
        """The action is able to move the system from ABORTED to ABORTING.

        - states sequence: ABORTED -> EMPTY -> RESOURCING -> ABORTING
        - commands sequence: Restart -> AssignResources -> Abort
        """
        commands_input = ObsStateCommandsInput(AssignResources='{"dummy": 2}')
        setter = ObsStateSetter(
            system, ObsState.ABORTING, commands_input=commands_input
        )

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system,
            [
                ObsState.ABORTED,
                ObsState.EMPTY,
                ObsState.RESOURCING,
                ObsState.ABORTING,
            ],
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Three commands are expected"
        ).is_length(3)
        assert_command_and_postcondition(
            patcher.instances, 0, "Restart", ObsState.EMPTY
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "AssignResources", ObsState.RESOURCING
        )
        assert_command_and_postcondition(
            patcher.instances, 2, "Abort", ObsState.ABORTING
        )

    @staticmethod
    def test_execute_from_fault_to_resourcing(system: MockSubarraySystem):
        """The action is able to move the system from FAULT to RESOURCING.

        - states sequence: FAULT -> EMPTY -> RESOURCING
        - commands sequence: Restart -> AssignResources
        """
        commands_input = ObsStateCommandsInput(AssignResources='{"dummy": 2}')
        setter = ObsStateSetter(
            system, ObsState.RESOURCING, commands_input=commands_input
        )

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system, [ObsState.FAULT, ObsState.EMPTY, ObsState.RESOURCING]
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Two commands are expected"
        ).is_length(2)
        assert_command_and_postcondition(
            patcher.instances, 0, "Restart", ObsState.EMPTY
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "AssignResources", ObsState.RESOURCING
        )

    @staticmethod
    def test_execute_from_resetting_to_restarting(system: MockSubarraySystem):
        """The action is able to move the system from RESETTING to RESTARTING.

        - states sequence: RESETTING -> ABORTED -> RESTARTING
        - commands sequence: Abort -> Restart
        """
        setter = ObsStateSetter(system, ObsState.RESTARTING)

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system, [ObsState.RESETTING, ObsState.ABORTED, ObsState.RESTARTING]
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "Two commands are expected"
        ).is_length(2)
        assert_command_and_postcondition(
            patcher.instances, 0, "Abort", ObsState.ABORTED
        )
        assert_command_and_postcondition(
            patcher.instances, 1, "Restart", ObsState.RESTARTING
        )

    @staticmethod
    def test_execute_from_scanning_to_aborted(system: MockSubarraySystem):
        """The action is able to move the system from SCANNING to ABORTED.

        - states sequence: SCANNING -> ABORTED
        - commands sequence: Abort
        """
        setter = ObsStateSetter(system, ObsState.ABORTED)

        # patch the commands and execute a side effect that
        # moves the system through a sequence of states
        side_effect = MoveMockSystemThroughStates(
            system, [ObsState.SCANNING, ObsState.ABORTED]
        )
        patcher = MockTangoLRCActionPatcher(side_effect=side_effect)
        with patcher.patch():
            setter.execute()

        assert_that(patcher.instances).described_as(
            "One command is expected"
        ).is_length(1)
        assert_command_and_postcondition(
            patcher.instances, 0, "Abort", ObsState.ABORTED
        )
