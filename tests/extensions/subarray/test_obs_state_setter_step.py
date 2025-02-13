"""Unit tests for the ObsStateSetterStep class."""

import pytest
from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.obs_state_setter_step import (  # pylint: disable=line-too-long # noqa: E501
    ObsStateSetterStep,
    ObsStateSystemNotConsistent,
)
from ska_integration_test_harness.extensions.subarray.setter_steps import (
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

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateSetterStep:
    """Unit tests for the ObsStateSetterStep class.

    TODO: describe the purpose of the class.
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

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
    # Test Commands utilities

    # @staticmethod
    # def test_execute_terminates_if_system_state_is_target(
    #     system: MockSubarraySystem,
    # ):
    #     """The execute procedure terminates if the system
    # state is the target.

    #     If the system is already in the target state, the execute procedure
    #     should terminate without any action.

    #     :param system: The observation state system.
    #     """
    #     system.set_controller_obs_state(ObsState.ABORTING)
    #     system.set_obs_state_other_devices(ObsState.ABORTING)
    #     setter = ObsStateSetter.get_setter_action(system, ObsState.ABORTING)

    #     setter.next_command = MagicMock()
    #     setter.execute()

    #     setter.next_command.assert_not_called()

    # @staticmethod
    # def test_execute_fails_if_target_is_not_reachable(
    #     system: MockSubarraySystem,
    # ):
    #     """The execute procedure fails if the target is not reachable.

    #     If the target is not reachable, the execute procedure should fail.

    #     :param system: The observation state system.
    #     """
    #     system.set_controller_obs_state(ObsState.ABORTED)
    #     system.set_obs_state_other_devices(ObsState.ABORTED)
    #     setter = ObsStateSetterFromAborted(system, ObsState.FAULT)

    #     with pytest.raises(NotImplementedError) as exc_info:
    #         setter.execute()

    #     assert_that(str(exc_info.value)).described_as(
    #         "The error message references the unsupported target obs state"
    #     ).contains(
    #         "target observation state ObsState.FAULT "
    #         "is not reachable by current decision rules"
    #     )

    # @staticmethod
    # def test_execute_calls_expected_tango_command(
    #     system: MockSubarraySystem,
    # ):
    #     """The execute procedure calls the expected Tango command.

    #     The execute procedure should call the expected Tango command
    #     to move the system to the target state.

    #     :param system: The observation state system.
    #     """
    #     system.set_controller_obs_state(ObsState.IDLE)
    #     system.set_obs_state_other_devices(ObsState.IDLE)
    #     setter = ObsStateSetter.get_setter_action(
    #         system,
    #         ObsState.RESOURCING,
    #         commands_input={
    #             "AssignResources": "DUMMY INPUT",
    #         },
    #     )

    #     # create a timeout object to track when it's passed
    #     timeout = ChainedAssertionsTimeout(10)

    #     # define a side effect to change the system state to RESOURCING
    #     # pylint: disable=unused-argument
    #     def move_system_to_resourcing(*args, **kwargs):
    #         system.set_controller_obs_state(ObsState.RESOURCING)
    #         system.set_obs_state_other_devices(ObsState.RESOURCING)

    #     # tell to use MockTangoLRCAction
    #     with patch.object(
    #         TangoLRCAction, "execute", side_effect=move_system_to_resourcing
    #     ) as mock_execute:
    #         setter.execute(timeout, False, False)

    #     # check if the LRC action was called
    #     mock_execute.assert_called_once()

    #     # check if the LRC action was called with the timeout and
    #     # preconditions flag (not postconditions flag)
    #     mock_execute.assert_called_with(timeout, False)

    # @staticmethod
    # def test_execute_determines_correctly_the_next_step(
    #     system: MockSubarraySystem,
    # ):
    #     """The execute procedure determines correctly the next step.

    #     The execute procedure should determine correctly the next step
    #     to move the system to the target state.

    #     :param system: The observation state system.
    #     """
    #     system.set_controller_obs_state(ObsState.EMPTY)
    #     system.set_obs_state_other_devices(ObsState.EMPTY)
    #     cmd_inputs = ObsStateCommandsInput(AssignResources="DUMMY INPUT")
    #     setter = ObsStateSetter.get_setter_action(
    #         system,
    #         ObsState.READY,
    #         commands_input=cmd_inputs,
    #     )

    #     # create a timeout object to track when it's passed
    #     timeout = ChainedAssertionsTimeout(10)

    #     # define a side effect to change the system state to RESOURCING
    #     # pylint: disable=unused-argument
    #     def move_system_to_idle(*args, **kwargs):
    #         system.set_controller_obs_state(ObsState.IDLE)
    #         system.set_obs_state_other_devices(ObsState.IDLE)

    #     with patch.object(
    #         TangoLRCAction, "execute", side_effect=move_system_to_idle
    #     ):
    #         mock_next_action = MagicMock()
    #         with patch.object(
    #             ObsStateSetter,
    #             "get_setter_action",
    #             side_effect=MagicMock(return_value=mock_next_action),
    #         ) as mock_get_setter_action:
    #             setter.execute(timeout, False, False)

    #     # check if the next action is determined as expected and
    # then executed
    #     mock_get_setter_action.assert_called_once()
    #     # check if the next action receives all the expected parameters
    #     mock_get_setter_action.assert_called_with(
    #         system, ObsState.READY, 1, cmd_inputs, True
    #     )

    #     # the next action is called with the timeout and the preconditions
    # flag
    #     mock_next_action.execute.assert_called_once()
    #     mock_next_action.execute.assert_called_with(
    #         postconditions_timeout=timeout,
    #         verify_preconditions=False,
    #         verify_postconditions=False,
    #     )
