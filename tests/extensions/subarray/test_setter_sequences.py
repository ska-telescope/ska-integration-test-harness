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
    command: MockTangoLRCAction, target_state: ObsState
):
    """Assert that the command has a postcondition for the target state."""
    for postcondition in command.postconditions:
        if (
            isinstance(postcondition, AssertDevicesStateChanges)
            and postcondition.attribute_name == "obsState"
            and postcondition.attribute_value == target_state
        ):
            return

    raise AssertionError(
        f"The command {command} has no postcondition "
        f"for the target state {target_state}."
    )


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

        - states sequence: IDLE -> CONFIGURING -> SCANNING
        - commands sequence: Configure -> Scan
        """
        commands_input = ObsStateCommandsInput(
            Configure='{"dummy": 0}', Scan='{"dummy": 1}'
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

        assert_that(patcher.instances[0].command_name).described_as(
            "The first command is expected to be Configure"
        ).is_equal_to("Configure")
        assert_command_has_postcondition_for_state(
            patcher.instances[0], ObsState.READY
        )

        assert_that(patcher.instances[1].command_name).described_as(
            "The second command is expected to be Scan"
        ).is_equal_to("Scan")
        assert_command_has_postcondition_for_state(
            patcher.instances[1], ObsState.SCANNING
        )
