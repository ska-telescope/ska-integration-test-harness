"""Unit tests for the ObsStateSetterStep class."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.core.assertions.dev_state_changes import (
    AssertDevicesStateChanges,
)
from ska_integration_test_harness.extensions.actions.lrc_action import (
    TangoLRCAction,
)
from ska_integration_test_harness.extensions.assertions.lrc_completion import (
    AssertLRCCompletion,
)
from ska_integration_test_harness.extensions.subarray.setter_step import (
    ObsStateCommandsInput,
    ObsStateMissingCommandInput,
    ObsStateSetterStep,
    ObsStateSystemNotConsistent,
)
from ska_integration_test_harness.extensions.subarray.setter_steps_imp import (
    ObsStateSetterStepFromAborted,
    ObsStateSetterStepFromAborting,
    ObsStateSetterStepFromConfiguring,
    ObsStateSetterStepFromEmpty,
    ObsStateSetterStepFromFault,
    ObsStateSetterStepFromIdle,
    ObsStateSetterStepFromReady,
    ObsStateSetterStepFromResetting,
    ObsStateSetterStepFromResourcing,
    ObsStateSetterStepFromRestarting,
    ObsStateSetterStepFromScanning,
)

from .utils import MockSubarraySystem, MockTangoLRCActionPatcher


@pytest.mark.extensions
class TestObsStateSetterStep:
    """Unit tests for the ObsStateSetterStep class.

    The following tests are focused on the ObsStateSetterStep class as
    a standalone class. The following tests are done:

    - Initialization and input reception: the class should be able to
      receive the commands input in different formats.
    - Action name and description: the class should be able to provide
      a meaningful name and description.
    - Get assumed and accepted obsState: the subclasses implementation
      provide coherent and sensed assumed and accepted obsState.
    - Preconditions verification: the class should be able to verify
      the preconditions for the action; various subclasses are tested
      checking both more or less strict valid and un-valid preconditions.
    - Commands utilities: the class should be able to create the
      appropriate commands for the action, considering the input and
      the context; the class should also be able to execute those
      commands with the expected settings.
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    # -------------------------------------------------------------------------
    # Test initialization & input reception

    @staticmethod
    def test_init_without_input_creates_empty_default_commands_input(
        system: MockSubarraySystem,
    ):
        """The initialization without input creates an empty default.

        If the initialization is called without input, the commands_input
        attribute should be an empty dictionary.

        :param system: The observation state system.
        """
        setter = ObsStateSetterStepFromEmpty(system, ObsState.IDLE)

        assert_that(setter.commands_input).is_instance_of(
            ObsStateCommandsInput
        )
        assert_that(setter.commands_input.AssignResources).is_none()
        assert_that(setter.commands_input.Configure).is_none()
        assert_that(setter.commands_input.Scan).is_none()

    @staticmethod
    def test_init_accepts_input_as_a_dict(system: MockSubarraySystem):
        """The initialization accepts input as a dictionary.

        The initialization should accept the input as a dictionary and
        store it in the commands_input attribute.

        :param system: The observation state system.
        """
        commands_input = {
            "AssignResources": '{"dummy": "input"}',
            "Configure": '{"another_dummy": "input"}',
        }
        setter = ObsStateSetterStepFromEmpty(
            system, ObsState.IDLE, commands_input=commands_input
        )

        assert_that(setter.commands_input).is_instance_of(
            ObsStateCommandsInput
        )
        assert_that(setter.commands_input.AssignResources).is_equal_to(
            '{"dummy": "input"}'
        )
        assert_that(setter.commands_input.Configure).is_equal_to(
            '{"another_dummy": "input"}'
        )
        assert_that(setter.commands_input.Scan).is_none()

    @staticmethod
    def test_init_accepts_input_as_an_object(system: MockSubarraySystem):
        """The initialization accepts input as an object.

        The initialization should accept the input as an object and
        store it in the commands_input attribute.

        :param system: The observation state system.
        """
        commands_input = ObsStateCommandsInput(Scan='{"dummy": "input"}')
        setter = ObsStateSetterStepFromEmpty(
            system, ObsState.IDLE, commands_input=commands_input
        )

        assert_that(setter.commands_input).is_equal_to(commands_input)

    # -------------------------------------------------------------------------
    # Test action name and description

    @staticmethod
    def test_setter_description_includes_relevant_information(
        system: MockSubarraySystem,
    ):
        """The setter description should include relevant information:

        - the subarray ID
        - the current obsState
        - the target obsState

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.READY)
        setter = ObsStateSetterStepFromReady(system, ObsState.SCANNING)

        assert_that(setter.description()).described_as(
            "The setter description reference the subarray ID."
        ).contains("subarray 1").described_as(
            "The setter description mention this is just one step"
        ).contains(
            "Executing a transition step to move"
        ).described_as(
            "The setter description reference the current obsState."
        ).contains(
            "from ObsState.READY"
        ).described_as(
            "The setter description reference the target obsState."
        ).contains(
            "towards ObsState.SCANNING"
        )

    # -------------------------------------------------------------------------
    # Test get assumed and accepted obsState

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "assumed_obs_state"),
        [
            (ObsStateSetterStepFromEmpty, ObsState.EMPTY),
            (ObsStateSetterStepFromResourcing, ObsState.RESOURCING),
            (ObsStateSetterStepFromIdle, ObsState.IDLE),
            (ObsStateSetterStepFromConfiguring, ObsState.CONFIGURING),
            (ObsStateSetterStepFromReady, ObsState.READY),
            (ObsStateSetterStepFromScanning, ObsState.SCANNING),
            (ObsStateSetterStepFromResetting, ObsState.RESETTING),
            (ObsStateSetterStepFromAborting, ObsState.ABORTING),
            (ObsStateSetterStepFromAborted, ObsState.ABORTED),
            (ObsStateSetterStepFromFault, ObsState.FAULT),
            (ObsStateSetterStepFromRestarting, ObsState.RESTARTING),
        ],
    )
    def test_get_assumed_obs_state_returns_assumed_obs_state(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        assumed_obs_state: ObsState,
    ):
        """The get_assumed_obs_state method returns the expected obsState.

        The get_assumed_obs_state method should return the expected obsState
        for each ObsStateSetterStep class (Independently of the current
        system state and the target obsState).

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param assumed_obs_state: The expected obsState.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)
        setter = step_class(system, ObsState.EMPTY)

        assert_that(setter.get_assumed_obs_state()).is_equal_to(
            assumed_obs_state
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "assumed_obs_state"),
        [
            (ObsStateSetterStepFromEmpty, ObsState.EMPTY),
            (ObsStateSetterStepFromIdle, ObsState.IDLE),
            (ObsStateSetterStepFromReady, ObsState.READY),
            (ObsStateSetterStepFromAborted, ObsState.ABORTED),
        ],
    )
    def test_get_accepted_obs_states_default_to_the_assumed_one_for_quiescent(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        assumed_obs_state: ObsState,
    ):
        """The get_accepted_obs_states method returns the assumed obsState.

        The get_accepted_obs_states method should return the assumed obsState
        for each ObsStateSetterStep class that represents a quiescent state.

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param assumed_obs_state: The expected obsState.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)
        setter = step_class(system, ObsState.EMPTY)

        assert_that(setter.get_accepted_obs_states()).is_equal_to(
            [assumed_obs_state]
        )

    # -------------------------------------------------------------------------
    # Test preconditions verification

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "assumed_obs_state"),
        [
            (ObsStateSetterStepFromEmpty, ObsState.EMPTY),
            (ObsStateSetterStepFromResourcing, ObsState.RESOURCING),
            (ObsStateSetterStepFromIdle, ObsState.IDLE),
            (ObsStateSetterStepFromConfiguring, ObsState.CONFIGURING),
            (ObsStateSetterStepFromReady, ObsState.READY),
            (ObsStateSetterStepFromScanning, ObsState.SCANNING),
            (ObsStateSetterStepFromResetting, ObsState.RESETTING),
            (ObsStateSetterStepFromAborting, ObsState.ABORTING),
            (ObsStateSetterStepFromAborted, ObsState.ABORTED),
            (ObsStateSetterStepFromFault, ObsState.FAULT),
            (ObsStateSetterStepFromRestarting, ObsState.RESTARTING),
        ],
    )
    def test_preconditions_pass_if_all_devices_are_in_assumed_state(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        assumed_obs_state: ObsState,
    ):
        """Preconditions pass if all devices are in the assumed state.

        If all devices are in the assumed state, the preconditions are met
        and therefore their verification should pass.

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param assumed_obs_state: The expected obsState.
        """
        system.set_controller_obs_state(assumed_obs_state)
        system.set_obs_state_other_devices(assumed_obs_state)
        setter = step_class(system, ObsState.EMPTY)

        setter.verify_preconditions()

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "dev_a_state", "dev_b_state", "dev_c_state"),
        [
            (
                ObsStateSetterStepFromResourcing,
                ObsState.EMPTY,
                ObsState.RESOURCING,
                ObsState.IDLE,
            ),
            (
                ObsStateSetterStepFromConfiguring,
                ObsState.IDLE,
                ObsState.CONFIGURING,
                ObsState.READY,
            ),
            (
                ObsStateSetterStepFromScanning,
                ObsState.READY,
                ObsState.SCANNING,
                ObsState.READY,
            ),
            (
                ObsStateSetterStepFromResetting,
                ObsState.FAULT,
                ObsState.RESETTING,
                ObsState.IDLE,
            ),
            (
                ObsStateSetterStepFromAborting,
                ObsState.IDLE,
                ObsState.ABORTING,
                ObsState.ABORTED,
            ),
            (
                ObsStateSetterStepFromRestarting,
                ObsState.ABORTED,
                ObsState.RESTARTING,
                ObsState.EMPTY,
            ),
        ],
    )
    def test_transient_precond_accepts_devices_in_close_states(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        dev_a_state: ObsState,
        dev_b_state: ObsState,
        dev_c_state: ObsState,
    ):
        """Transient preconditions accept devices in close states.

        If devices are in close states, the preconditions are met and therefore
        their verification should pass.

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param dev_a_state: The first device state.
        :param dev_b_state: The second device state.
        :param dev_c_state: The third device state.
        """
        system.set_controller_obs_state(dev_b_state)
        system.set_partial_obs_state(dev_a_state, device_index=0)
        system.set_partial_obs_state(dev_b_state, device_index=1)
        system.set_partial_obs_state(dev_c_state, device_index=2)
        setter = step_class(system, ObsState.EMPTY)

        setter.verify_preconditions()

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "assumed_obs_state", "divergent_device_obs_state"),
        [
            (ObsStateSetterStepFromEmpty, ObsState.EMPTY, ObsState.RESTARTING),
            (ObsStateSetterStepFromIdle, ObsState.IDLE, ObsState.RESOURCING),
            (
                ObsStateSetterStepFromReady,
                ObsState.READY,
                ObsState.CONFIGURING,
            ),
            (
                ObsStateSetterStepFromAborted,
                ObsState.ABORTED,
                ObsState.ABORTING,
            ),
        ],
    )
    def test_quiescent_precond_fail_if_a_device_is_not_in_assumed_obs_state(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        assumed_obs_state: ObsState,
        divergent_device_obs_state: ObsState,
    ):
        """Quiescent preconditions fail if a device is not in assumed obsState.

        If a device has not the assumed obsState, the preconditions are not met
        and therefore their verification should fail.

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param assumed_obs_state: The expected obsState.
        :param divergent_device_obs_state: The divergent device obsState.
        """
        system.set_controller_obs_state(assumed_obs_state)
        system.set_obs_state_other_devices(assumed_obs_state)
        system.set_partial_obs_state(
            divergent_device_obs_state, device_index=0
        )
        setter = step_class(system, ObsState.EMPTY)

        with pytest.raises(ObsStateSystemNotConsistent) as exc_info:
            setter.verify_preconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message includes action name and description"
        ).contains(step_class.__name__).contains(
            setter.description()
        ).described_as(
            "The error message includes the expected consistent state"
        ).contains(
            f"consistent observation state {str(assumed_obs_state)}"
        ).described_as(
            "The error message includes the actual devices states"
        ).contains(
            f"subarray/dev_a/1={str(divergent_device_obs_state)}"
        ).contains(
            f"subarray/dev_b/1={str(assumed_obs_state)}"
        ).contains(
            f"subarray/dev_c/1={str(assumed_obs_state)}"
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("step_class", "dev_a_state", "dev_b_state", "dev_c_state"),
        [
            (
                ObsStateSetterStepFromResourcing,
                ObsState.FAULT,
                ObsState.RESOURCING,
                ObsState.ABORTING,
            ),
            (
                ObsStateSetterStepFromConfiguring,
                ObsState.IDLE,
                ObsState.CONFIGURING,
                ObsState.FAULT,
            ),
            (
                ObsStateSetterStepFromScanning,
                ObsState.READY,
                ObsState.SCANNING,
                ObsState.FAULT,
            ),
            (
                ObsStateSetterStepFromResetting,
                ObsState.EMPTY,
                ObsState.RESETTING,
                ObsState.IDLE,
            ),
            (
                ObsStateSetterStepFromAborting,
                ObsState.IDLE,
                ObsState.ABORTING,
                ObsState.FAULT,
            ),
            (
                ObsStateSetterStepFromRestarting,
                ObsState.ABORTED,
                ObsState.RESTARTING,
                ObsState.ABORTING,
            ),
        ],
    )
    def test_transient_precond_fail_if_a_device_is_not_in_accepted_state(
        system: MockSubarraySystem,
        step_class: type[ObsStateSetterStep],
        dev_a_state: ObsState,
        dev_b_state: ObsState,
        dev_c_state: ObsState,
    ):
        """Transient preconditions fail if a device is not in accepted state.

        If a device has not an accepted obsState, the preconditions
        are not met and therefore their verification should fail.

        :param system: The observation state system.
        :param step_class: The ObsStateSetterStep class.
        :param dev_a_state: The first device state.
        :param dev_b_state: The second device state (in this case it will
            always be the assumed obsState).
        :param dev_c_state: The third device state.
        """
        system.set_controller_obs_state(dev_b_state)
        system.set_partial_obs_state(dev_a_state, device_index=0)
        system.set_partial_obs_state(dev_b_state, device_index=1)
        system.set_partial_obs_state(dev_c_state, device_index=2)
        setter = step_class(system, ObsState.EMPTY)

        with pytest.raises(ObsStateSystemNotConsistent) as exc_info:
            setter.verify_preconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message includes action name and description"
        ).contains(step_class.__name__).contains(
            setter.description()
        ).described_as(
            "The error message includes the expected consistent state"
        ).contains(
            f"consistent observation state {str(dev_b_state)}"
        ).described_as(
            "The error message includes the actual devices states"
        ).contains(
            f"subarray/dev_a/1={str(dev_a_state)}"
        ).contains(
            f"subarray/dev_b/1={str(dev_b_state)}"
        ).contains(
            f"subarray/dev_c/1={str(dev_c_state)}"
        )

    # -------------------------------------------------------------------------
    # Test Commands utilities (creation and execution)

    @staticmethod
    def test_create_command_that_synchronise_on_transient(
        system: MockSubarraySystem,
    ):
        """Create a command that synchronises on transient state.

        We expect the command to be pointed to the correct target device,
        to have the expected timeout and parameters and

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.READY)
        system.set_obs_state_other_devices(ObsState.READY)
        setter = ObsStateSetterStepFromReady(system, ObsState.ABORTING)

        command = setter.create_subarray_command("Abort", sync_transient=True)

        assert_that(command).is_instance_of(TangoLRCAction)
        assert_that(command.target_device).is_equal_to(
            system.subarray_controller
        )
        assert_that(command.command_name).is_equal_to("Abort")
        assert_that(command.preconditions).described_as(
            "The command is supposed to have no preconditions"
        ).is_length(0)
        assert_that(command.early_stop).described_as(
            "The early stop is supposed to be set"
        ).is_not_none()
        assert_that(command.postconditions).described_as(
            "The command is supposed to have 1 postcondition "
            "to check the transient state"
        ).is_length(1)

        postcondition = command.postconditions[0]
        assert_that(postcondition).is_instance_of(AssertDevicesStateChanges)
        assert_that(postcondition.devices).described_as(
            "The postcondition is supposed to check the system devices"
        ).is_equal_to(
            [
                system.obs_state_devices[0],
                system.obs_state_devices[1],
                system.obs_state_devices[2],
            ]
        )
        assert_that(postcondition.attribute_name).described_as(
            "The postcondition is supposed to check the obsState attribute"
        ).is_equal_to("obsState")
        assert_that(postcondition.attribute_value).described_as(
            "The postcondition is supposed to check the transient state"
        ).is_equal_to(ObsState.ABORTING)

    @staticmethod
    def test_create_command_that_synchronise_on_quiescent_and_lrc_completion(
        system: MockSubarraySystem,
    ):
        """Create a command that synchronises on quiescent state.

        We expect the command to be pointed to the correct target device,
        to have the expected timeout and parameters and

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.ABORTED)
        system.set_obs_state_other_devices(ObsState.ABORTED)
        setter = ObsStateSetterStepFromAborted(system, ObsState.EMPTY)

        command = setter.create_subarray_command(
            "Restart", sync_transient=False
        )

        assert_that(command).is_instance_of(TangoLRCAction)
        assert_that(command.target_device).is_equal_to(
            system.subarray_controller
        )
        assert_that(command.command_name).is_equal_to("Restart")
        assert_that(command.preconditions).described_as(
            "The command is supposed to have no preconditions"
        ).is_length(0)
        assert_that(command.early_stop).described_as(
            "The early stop is supposed to be set"
        ).is_not_none()
        assert_that(command.postconditions).described_as(
            "The command is supposed to have 2 postcondition "
            "to check the quiescent state and the LRC completion"
        ).is_length(2)

        # check first postcondition
        postcondition = command.postconditions[0]
        assert_that(postcondition).is_instance_of(AssertDevicesStateChanges)
        assert_that(postcondition.devices).described_as(
            "The postcondition is supposed to check the system devices"
        ).is_equal_to(
            [
                system.obs_state_devices[0],
                system.obs_state_devices[1],
                system.obs_state_devices[2],
            ]
        )
        assert_that(postcondition.attribute_name).described_as(
            "The postcondition is supposed to check the obsState attribute"
        ).is_equal_to("obsState")
        assert_that(postcondition.attribute_value).described_as(
            "The postcondition is supposed to check the quiescent state"
        ).is_equal_to(ObsState.EMPTY)

        # check second postcondition
        postcondition = command.postconditions[1]
        assert_that(postcondition).is_instance_of(AssertLRCCompletion)
        assert_that(postcondition.device).described_as(
            "The postcondition is supposed to check the LRC completion "
            "on the subarray device that receives the command"
        ).is_equal_to(system.subarray_controller)

    @staticmethod
    @pytest.mark.parametrize(
        ("command_name", "expected_command_input"),
        [
            ("AssignResources", '{"dummy": "input"}'),
            ("Configure", '{"another_dummy": "input"}'),
            ("Scan", '{"another_dummy": "input"}'),
        ],
    )
    def test_create_command_uses_appropriate_input(
        system: MockSubarraySystem,
        command_name: str,
        expected_command_input: str,
    ):
        """Create command uses the appropriate input for each command.

        We expect the method to be able to use the correct inputs for each
        command.

        :param system: The observation state system.
        :param command_name: The command name.
        :param expected_command_input: The expected command input.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)
        setter = ObsStateSetterStepFromIdle(
            system,
            ObsState.READY,
            commands_input={
                "AssignResources": '{"dummy": "input"}',
                "Configure": '{"another_dummy": "input"}',
                "Scan": '{"another_dummy": "input"}',
            },
        )

        command = setter.create_subarray_command(command_name)

        assert_that(command).is_instance_of(TangoLRCAction)
        assert_that(command.command_name).is_equal_to(command_name)
        assert_that(command.command_param).described_as(
            "The command is supposed to have the expected input"
        ).is_equal_to(expected_command_input)

    @staticmethod
    @pytest.mark.parametrize(
        "command_name", ["AssignResources", "Configure", "Scan"]
    )
    def test_create_command_fails_if_an_input_is_missing(
        system: MockSubarraySystem, command_name: str
    ):
        """Create command fails if an input is missing.

        We expect the method to raise an error if the input for the command
        is missing.

        :param system: The observation state system.
        :param command_name: The command name.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)

        # define inputs, but remove the one for the command
        command_inputs = {
            "AssignResources": '{"dummy": "input"}',
            "Configure": '{"another_dummy": "input"}',
            "Scan": '{"another_dummy": "input"}',
        }
        command_inputs[command_name] = None
        setter = ObsStateSetterStepFromIdle(
            system, ObsState.READY, commands_input=command_inputs
        )

        with pytest.raises(ObsStateMissingCommandInput) as exc_info:
            setter.create_subarray_command(command_name)

        assert_that(str(exc_info.value)).described_as(
            "The error message includes the missing command input name"
        ).contains(f"Missing input for command {command_name}").described_as(
            "The error message is expected to include the passed inputs"
        ).contains(
            str(command_inputs)
        ).described_as(
            "The error message is expected to include the action name"
            " and description"
        ).contains(
            setter.name()
        ).contains(
            setter.description()
        )

    @staticmethod
    def test_send_command_enable_or_disable_log_according_to_action_setting(
        system: MockSubarraySystem,
    ):
        """Send command enables or disables log according to action setting.

        We expect the method to "propagate" the log setting to the command
        being sent.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)
        setter = ObsStateSetterStepFromIdle(system, ObsState.ABORTED)
        # setter.set_logging(True) (default)

        patcher = MockTangoLRCActionPatcher()
        with patcher.patch():
            setter.send_subarray_command_and_synchronise("Abort")

            assert_that(patcher.instances).is_length(1)
            instance = patcher.instances[0]
            assert_that(instance.target_device).is_equal_to(
                system.subarray_controller
            )
            assert_that(instance.command_name).is_equal_to("Abort")
            assert_that(instance.is_logging_enabled()).is_true()

        # try to set to False and repeat the test
        patcher.reset()
        setter.set_logging(False)
        with patcher.patch():
            setter.send_subarray_command_and_synchronise("Abort")

            assert_that(patcher.instances).is_length(1)
            instance = patcher.instances[0]
            assert_that(instance.target_device).is_equal_to(
                system.subarray_controller
            )
            assert_that(instance.command_name).is_equal_to("Abort")
            assert_that(instance.is_logging_enabled()).is_false()

    @staticmethod
    def test_send_command_executes_the_command_with_timeout_and_other_settings(
        system: MockSubarraySystem,
    ):
        """Send command executes the command with timeout and other settings.

        We expect the method to execute the command with the expected
        action timeout and other settings.
        """
        system.set_controller_obs_state(ObsState.READY)
        system.set_obs_state_other_devices(ObsState.READY)
        setter = ObsStateSetterStepFromIdle(
            system,
            ObsState.CONFIGURING,
            commands_input={
                "Scan": '{"dummy": "input"}',
            },
        )
        # simulate being in an execution context
        mock_timeout = MagicMock()
        # pylint: disable=protected-access
        setter._last_execution_params = {
            "postconditions_timeout": mock_timeout,
            "verify_preconditions": False,
            "verify_postconditions": False,
        }

        patcher = MockTangoLRCActionPatcher()
        with patcher.patch():
            setter.send_subarray_command_and_synchronise("Scan")

            assert_that(patcher.instances).is_length(1)
            instance = patcher.instances[0]
            assert_that(instance.target_device).is_equal_to(
                system.subarray_controller
            )
            assert_that(instance.command_name).is_equal_to("Scan")
            assert_that(instance.command_param).is_equal_to(
                '{"dummy": "input"}'
            )

            # verify the execute call arguments
            instance.execute.assert_called_once()
            instance.execute.assert_called_once_with(mock_timeout, False, True)
