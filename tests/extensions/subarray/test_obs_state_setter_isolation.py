"""Unit tests for the ObsStateSetter class."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration.assertions import ChainedAssertionsTimeout

from ska_integration_test_harness.extensions.subarray.obs_state_commands_factory import (  # pylint: disable=line-too-long # noqa: E501
    TangoLRCAction,
)
from ska_integration_test_harness.extensions.subarray.obs_state_setter import (
    STATE_CLASS_MAP,
    ObsStateCommandsInput,
    ObsStateSetter,
    ObsStateSetterFromAborted,
    ObsStateSetterFromAborting,
    ObsStateSetterFromConfiguring,
    ObsStateSetterFromEmpty,
    ObsStateSetterFromFault,
    ObsStateSetterFromIdle,
    ObsStateSetterFromReady,
    ObsStateSetterFromResetting,
    ObsStateSetterFromResourcing,
    ObsStateSetterFromRestarting,
    ObsStateSetterFromScanning,
    ObsStateSetterSupportsAbort,
    ObsStateSetterSupportsRestart,
    ObsStateSystemNotConsistent,
)

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateSetterInIsolation:
    """Unit tests for the ObsStateSetter class methods and isolated behaviour.

    This set of unit tests has the responsibility to validate the
    ObsStateSetter class behaviour in isolation. The ObsStateSetter
    is a complex mechanism based on a base class with much common logic,
    some child classes with specific logic for each observation state and
    a data structure to map the observation states to the setter classes.
    The mechanism is recursive and the setter classes are created on-demand
    according to an observed current state.

    This first set of tests if focused on the behaviour in isolation of
    ObsStateSetter instances. Essentially, we create ObsStateSetter instances
    and we check that their methods work as expected. We don't yet instead
    verify (here) the "collaboration" between the ObsStateSetter instances,
    the recursive mechanism and the capability of navigating correctly
    the state transitions. For that there is another test class
    (``TestObsStateSetterCommandsSequences``).
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    # -------------------------------------------------------------------------
    # Test instance creation through the factory method

    @staticmethod
    def test_get_setter_action_returns_expected_setter_instances(
        system: MockSubarraySystem,
    ):
        """The get_setter_action method should return the expected setter.

        This test verifies that the get_setter_action method returns the
        expected setter instance for each ObsState. It verifies also
        that some instances belong to the ObsStateSetterSupportsAbort
        and ObsStateSetterSupportsRestart groups.

        :param system: The observation state system.
        """

        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromEmpty)

        # change starting state and see if the correct setter is returned
        system.set_controller_obs_state(ObsState.RESOURCING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromResourcing).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.IDLE)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromIdle).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.CONFIGURING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromConfiguring).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.READY)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromReady).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.SCANNING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromScanning).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.RESETTING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromResetting).is_instance_of(
            ObsStateSetterSupportsAbort
        )

        system.set_controller_obs_state(ObsState.ABORTING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromAborting)

        system.set_controller_obs_state(ObsState.ABORTED)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromAborted).is_instance_of(
            ObsStateSetterSupportsRestart
        )

        system.set_controller_obs_state(ObsState.FAULT)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromFault).is_instance_of(
            ObsStateSetterSupportsRestart
        )

        system.set_controller_obs_state(ObsState.RESTARTING)
        assert_that(
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)
        ).is_instance_of(ObsStateSetterFromRestarting)

    @staticmethod
    def test_get_setter_action_fails_if_state_is_not_reachable(
        system: MockSubarraySystem,
    ):
        """Setter creation fails when the state is not reachable.

        :param system: The observation state system.
        """
        with pytest.raises(NotImplementedError):
            ObsStateSetter.get_setter_action(system, ObsState.FAULT)

        with pytest.raises(NotImplementedError):
            ObsStateSetter.get_setter_action(system, ObsState.RESETTING)

    @staticmethod
    def test_get_setter_action_fails_when_startig_state_is_not_supported(
        system: MockSubarraySystem,
    ):
        """Setter creation fails when the starting state is not supported.

        :param system: The observation state system.
        """
        # force the starting state to be not supported
        STATE_CLASS_MAP.pop(ObsState.RESETTING)

        # make the system be in that starting state
        system.set_controller_obs_state(ObsState.RESETTING)
        with pytest.raises(NotImplementedError):
            ObsStateSetter.get_setter_action(system, ObsState.EMPTY)

    # -------------------------------------------------------------------------
    # Test ObsStateSetter isolated methods
    # (assumed class obs state, description, verify preconditions)

    @staticmethod
    def test_class_assumed_obs_state_is_correctly_defined(
        system: MockSubarraySystem,
    ):
        """The class assumed obs state is correctly defined.

        (If everything is correct, the class assumed obs
        state should be the same as the target obs state.)

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.RESOURCING)
        setter = ObsStateSetter.get_setter_action(system, ObsState.ABORTED)

        assert_that(setter.assumed_class_obs_state()).described_as(
            "The class starting state is the expected one."
        ).is_equal_to(ObsState.RESOURCING)

        system.set_controller_obs_state(ObsState.IDLE)
        assert_that(setter.assumed_class_obs_state()).described_as(
            "The class starting state is still the initial one."
        ).is_equal_to(ObsState.RESOURCING)

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
        system.set_controller_obs_state(ObsState.IDLE)
        setter = ObsStateSetter.get_setter_action(system, ObsState.SCANNING)

        assert_that(setter.description()).described_as(
            "The setter description reference the subarray ID."
        ).contains("Move subarray 1").described_as(
            "The setter description reference the current obsState."
        ).contains(
            "from ObsState.IDLE"
        ).described_as(
            "The setter description reference the target obsState."
        ).contains(
            "to ObsState.SCANNING"
        )

    @staticmethod
    def test_verify_preconditions_pass_if_the_system_is_in_the_expected_state(
        system: MockSubarraySystem,
    ):
        """Verify preconditions pass if the system is in the expected state.

        If the system is (coherently) in the expected state,
        the preconditions are met and therefore their verification
        should pass.

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)

        setter = ObsStateSetter.get_setter_action(system, ObsState.SCANNING)

        setter.verify_preconditions()

    @staticmethod
    def test_verify_preconditions_pass_if_the_system_state_is_consistent(
        system: MockSubarraySystem,
    ):
        """Preconditions deals with non-trivial transient state consistency.

        Sometimes when the system is in a transient state, some devices
        may be in the next quiescent state. This test verifies an example
        of this situation.

        NOTE: it's not exhaustive, but it's a good example. There are much
        more situations to consider!

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.RESOURCING)
        system.set_partial_obs_state(ObsState.EMPTY, device_index=0)
        system.set_partial_obs_state(ObsState.RESOURCING, device_index=1)
        system.set_partial_obs_state(ObsState.IDLE, device_index=2)

        setter = ObsStateSetter.get_setter_action(system, ObsState.SCANNING)
        setter.verify_preconditions()

    @staticmethod
    def test_verify_preconditions_fail_if_obs_state_is_not_consistent(
        system: MockSubarraySystem,
    ):
        """Verify preconditions fail if the obsState is not consistent.

        If the system is not in the expected state, the preconditions
        are not met and therefore their verification should fail.

        NOTE: it's not exhaustive, but it's a good example. There are much
        more situations to consider!

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.RESOURCING)
        system.set_partial_obs_state(ObsState.RESOURCING, device_index=0)
        system.set_partial_obs_state(ObsState.RESOURCING, device_index=1)
        system.set_partial_obs_state(ObsState.ABORTED, device_index=2)

        setter = ObsStateSetter.get_setter_action(system, ObsState.SCANNING)

        with pytest.raises(ObsStateSystemNotConsistent) as exc_info:
            setter.verify_preconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message that what occurred is a failed assumption"
        ).contains("FAILED ASSUMPTION").described_as(
            "The action name and description should be included"
        ).contains(
            "ObsStateSetterFromResourcing"
        ).contains(
            "Move subarray 1 from ObsState.RESOURCING to ObsState.SCANNING"
        ).described_as(
            "The expected consistent state should be included"
        ).contains(
            "consistent observation state ObsState.RESOURCING"
        ).described_as(
            "The actual devices states should be included"
        ).contains(
            "subarray/dev_a/1=ObsState.RESOURCING"
        ).contains(
            "subarray/dev_b/1=ObsState.RESOURCING"
        ).contains(
            "subarray/dev_c/1=ObsState.ABORTED"
        )

    # -------------------------------------------------------------------------
    # Test Execute process

    @staticmethod
    def test_execute_terminates_if_system_state_is_target(
        system: MockSubarraySystem,
    ):
        """The execute procedure terminates if the system state is the target.

        If the system is already in the target state, the execute procedure
        should terminate without any action.

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.ABORTING)
        system.set_obs_state_other_devices(ObsState.ABORTING)
        setter = ObsStateSetter.get_setter_action(system, ObsState.ABORTING)

        setter.next_command = MagicMock()
        setter.execute()

        setter.next_command.assert_not_called()

    @staticmethod
    def test_execute_fails_if_target_is_not_reachable(
        system: MockSubarraySystem,
    ):
        """The execute procedure fails if the target is not reachable.

        If the target is not reachable, the execute procedure should fail.

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.ABORTED)
        system.set_obs_state_other_devices(ObsState.ABORTED)
        setter = ObsStateSetterFromAborted(system, ObsState.FAULT)

        with pytest.raises(NotImplementedError) as exc_info:
            setter.execute()

        assert_that(str(exc_info.value)).described_as(
            "The error message references the unsupported target obs state"
        ).contains(
            "target observation state ObsState.FAULT "
            "is not reachable by current decision rules"
        )

    @staticmethod
    def test_execute_calls_expected_tango_command(
        system: MockSubarraySystem,
    ):
        """The execute procedure calls the expected Tango command.

        The execute procedure should call the expected Tango command
        to move the system to the target state.

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.IDLE)
        system.set_obs_state_other_devices(ObsState.IDLE)
        setter = ObsStateSetter.get_setter_action(
            system,
            ObsState.RESOURCING,
            commands_input={
                "AssignResources": "DUMMY INPUT",
            },
        )

        # create a timeout object to track when it's passed
        timeout = ChainedAssertionsTimeout(10)

        # define a side effect to change the system state to RESOURCING
        # pylint: disable=unused-argument
        def move_system_to_resourcing(*args, **kwargs):
            system.set_controller_obs_state(ObsState.RESOURCING)
            system.set_obs_state_other_devices(ObsState.RESOURCING)

        # tell to use MockTangoLRCAction
        with patch.object(
            TangoLRCAction, "execute", side_effect=move_system_to_resourcing
        ) as mock_execute:
            setter.execute(timeout, False, False)

        # check if the LRC action was called
        mock_execute.assert_called_once()

        # check if the LRC action was called with the timeout and
        # preconditions flag (not postconditions flag)
        mock_execute.assert_called_with(timeout, False)

    @staticmethod
    def test_execute_determines_correctly_the_next_step(
        system: MockSubarraySystem,
    ):
        """The execute procedure determines correctly the next step.

        The execute procedure should determine correctly the next step
        to move the system to the target state.

        :param system: The observation state system.
        """
        system.set_controller_obs_state(ObsState.EMPTY)
        system.set_obs_state_other_devices(ObsState.EMPTY)
        cmd_inputs = ObsStateCommandsInput(AssignResources="DUMMY INPUT")
        setter = ObsStateSetter.get_setter_action(
            system,
            ObsState.READY,
            commands_input=cmd_inputs,
        )

        # create a timeout object to track when it's passed
        timeout = ChainedAssertionsTimeout(10)

        # define a side effect to change the system state to RESOURCING
        # pylint: disable=unused-argument
        def move_system_to_idle(*args, **kwargs):
            system.set_controller_obs_state(ObsState.IDLE)
            system.set_obs_state_other_devices(ObsState.IDLE)

        with patch.object(
            TangoLRCAction, "execute", side_effect=move_system_to_idle
        ):
            mock_next_action = MagicMock()
            with patch.object(
                ObsStateSetter,
                "get_setter_action",
                side_effect=MagicMock(return_value=mock_next_action),
            ) as mock_get_setter_action:
                setter.execute(timeout, False, False)

        # check if the next action is determined as expected and then executed
        mock_get_setter_action.assert_called_once()
        # check if the next action receives all the expected parameters
        mock_get_setter_action.assert_called_with(
            system, ObsState.READY, 1, cmd_inputs, True
        )

        # the next action is called with the timeout and the preconditions flag
        mock_next_action.execute.assert_called_once()
        mock_next_action.execute.assert_called_with(
            postconditions_timeout=timeout,
            verify_preconditions=False,
            verify_postconditions=False,
        )
