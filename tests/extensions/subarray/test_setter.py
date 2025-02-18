"""Unit tests for the ObsStateSetter class."""

import pytest
from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.setter import (
    ObsStateDidNotReachTargetState,
    ObsStateSetter,
)
from ska_integration_test_harness.extensions.subarray.setter_step import (  # pylint: disable=line-too-long # noqa
    ObsStateCommandsInput,
    ObsStateSetterStep,
    ObsStateSystemNotConsistent,
)

from .utils import MockSubarraySystem


class MockObsStateSetterStep(ObsStateSetterStep):
    """A mock step for testing purposes."""

    def get_assumed_obs_state(self):
        return ObsState.IDLE

    def execute_procedure(self):
        """Do nothing."""


@pytest.mark.platform
@pytest.mark.extensions
class TestObsStateSetter:
    """Unit tests for the ObsStateSetter class.

    The tests cover:

    - the action description
    - the ObsState Steps map construction and manipulation
    - the preconditions and postconditions verification

    The execution of the action is not tested here, but in the complementary
    ``TestObsStateSetterSequences`` class.
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    # -------------------------------------------------------------------
    # Tests on description

    @staticmethod
    def test_description_contains_expected_references(
        system: MockSubarraySystem,
    ):
        """The description contains references to the expected attributes.

        We expect:

        - the subarray ID to be referenced
        - the current observation state to be referenced
        - the new observation state to be referenced
        """
        setter = ObsStateSetter(system, ObsState.SCANNING, subarray_id=4)
        system.set_controller_obs_state(ObsState.IDLE)

        assert_that(setter.description()).described_as(
            "The description contains a reference to the subarray ID"
        ).contains("Move subarray 4").described_as(
            "The description contains a reference to the current obs state"
        ).contains(
            "from ObsState.IDLE"
        ).described_as(
            "The description contains a reference to the new observation state"
        ).contains(
            "to ObsState.SCANNING"
        )

    # -------------------------------------------------------------------
    # Tests on ObsState Steps map

    @staticmethod
    def test_obs_state_steps_map_contains_all_and_only_obs_states(
        system: MockSubarraySystem,
    ):
        """The map contains all and only the expected observation states."""
        setter = ObsStateSetter(system, ObsState.EMPTY)

        for obs_state in ObsState:
            assert_that(setter.obs_state_steps_map.keys()).described_as(
                f"The map keys contains the observation state {str(obs_state)}"
            ).contains(obs_state)
            assert_that(
                setter.obs_state_steps_map[obs_state].get_assumed_obs_state()
            ).described_as(
                f"The step associated to {obs_state} assumes the correct "
                "observation state"
            )

        assert_that(setter.obs_state_steps_map.keys()).described_as(
            "The map contains all and only the expected observation states"
        ).is_length(len(list(ObsState)))

    @staticmethod
    def test_obs_state_steps_are_initialised_with_class_info(
        system: MockSubarraySystem,
    ):
        """The map elements are correctly initialised with the class info.

        We expect:

        - the system to be the same
        - the target to be the same
        - the subarray ID to be the same
        - the input to be the same
        """
        setter_input = ObsStateCommandsInput(AssignResources='{"dummy": 0}')
        setter = ObsStateSetter(system, ObsState.READY, 5, setter_input)

        for obs_state in ObsState:
            assert_that(
                setter.obs_state_steps_map[obs_state].system
            ).described_as(
                f"The step associated to {obs_state} has the correct system"
            ).is_equal_to(
                system
            )
            assert_that(
                setter.obs_state_steps_map[obs_state].target_state
            ).described_as(
                f"The step associated to {obs_state} has the correct target"
            ).is_equal_to(
                ObsState.READY
            )
            assert_that(
                setter.obs_state_steps_map[obs_state].subarray_id
            ).described_as(
                f"The step associated to {obs_state} has the "
                "correct subarray ID"
            ).is_equal_to(
                5
            )
            assert_that(
                setter.obs_state_steps_map[obs_state].commands_input
            ).described_as(
                f"The step associated to {obs_state} has the correct input"
            ).is_equal_to(
                setter_input
            )

    @staticmethod
    def test_obs_state_steps_map_is_overridable(
        system: MockSubarraySystem,
    ):
        """The map can be overridden with a custom one."""
        setter_input = ObsStateCommandsInput(AssignResources='{"dummy": 0}')
        setter = ObsStateSetter(system, ObsState.RESOURCING, 3, setter_input)

        setter.override_step(ObsState.IDLE, MockObsStateSetterStep)

        assert_that(setter.obs_state_steps_map[ObsState.IDLE]).described_as(
            "The map is expected to be successfully overridden with an "
            "instance of the new class"
        ).is_instance_of(MockObsStateSetterStep)
        new_instance = setter.obs_state_steps_map[ObsState.IDLE]
        assert_that(new_instance.system).described_as(
            "The new instance has the correct system"
        ).is_equal_to(system)
        assert_that(new_instance.target_state).described_as(
            "The new instance has the correct target"
        ).is_equal_to(ObsState.RESOURCING)
        assert_that(new_instance.subarray_id).described_as(
            "The new instance has the correct subarray ID"
        ).is_equal_to(3)
        assert_that(new_instance.commands_input).described_as(
            "The new instance has the correct input"
        ).is_equal_to(setter_input)

    @staticmethod
    def test_obs_state_override_fails_when_step_dont_support_given_state(
        system: MockSubarraySystem,
    ):
        """The override fails when the step doesn't support the given state."""
        setter = ObsStateSetter(system, ObsState.EMPTY)

        with pytest.raises(ValueError) as exc_info:
            setter.override_step(ObsState.ABORTING, MockObsStateSetterStep)

        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the not-assumed state"
        ).contains("ObsState.ABORTING")
        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the actual assumed state"
        ).contains("ObsState.IDLE")
        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the given class name"
        ).contains("MockObsStateSetterStep")

    # -------------------------------------------------------------------
    # Tests on preconditions

    @staticmethod
    @pytest.mark.parametrize(
        "target_state",
        [
            ObsState.EMPTY,
            ObsState.IDLE,
            ObsState.RESOURCING,
            ObsState.READY,
            ObsState.CONFIGURING,
            ObsState.SCANNING,
            ObsState.ABORTED,
            ObsState.ABORTING,
            ObsState.RESTARTING,
        ],
    )
    def test_preconditions_pass_when_target_state_is_reachable(
        system: MockSubarraySystem, target_state: ObsState
    ):
        """The preconditions pass when the target state is reachable."""
        setter = ObsStateSetter(system, target_state)

        setter.verify_preconditions()

    @staticmethod
    @pytest.mark.parametrize(
        "target_state", [ObsState.FAULT, ObsState.RESETTING]
    )
    def test_preconditions_fail_when_target_state_is_not_reachable(
        system: MockSubarraySystem, target_state: ObsState
    ):
        """The preconditions fail when the target state is not reachable."""
        setter = ObsStateSetter(system, target_state)

        with pytest.raises(AssertionError) as exc_info:
            setter.verify_preconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the target state"
        ).contains(str(target_state))

    # -------------------------------------------------------------------
    # Tests on postconditions

    @staticmethod
    @pytest.mark.parametrize("target_state", list(ObsState))
    def test_postconditions_pass_when_target_state_is_reached_consistently(
        system: MockSubarraySystem, target_state: ObsState
    ):
        """The postconditions pass when the system in target state.

        (consistently)
        """
        setter = ObsStateSetter(system, target_state)
        system.set_controller_obs_state(target_state)
        system.set_obs_state_other_devices(target_state)

        setter.verify_postconditions()

    @staticmethod
    def test_postconditions_fail_when_system_is_not_in_target_state(
        system: MockSubarraySystem,
    ):
        """The postconditions fail when the system is not in target state."""
        setter = ObsStateSetter(system, ObsState.READY, subarray_id=8)
        system.set_controller_obs_state(ObsState.CONFIGURING)
        system.set_obs_state_other_devices(ObsState.IDLE)

        with pytest.raises(ObsStateDidNotReachTargetState) as exc_info:
            setter.verify_postconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the target state"
        ).contains(
            "is expected to be in the target observation state ObsState.READY"
        ).described_as(
            "The error message is expected to contain the actual state"
        ).contains(
            "but is in ObsState.CONFIGURING"
        ).described_as(
            "The error message is expected to mention the the subarray ID"
        ).contains(
            "subarray 8"
        ).described_as(
            "The error message is expected to mention the actual state of "
            "the devices"
        ).contains(
            "subarray/dev_a/1=ObsState.IDLE"
        ).contains(
            "subarray/dev_b/1=ObsState.IDLE",
        ).contains(
            "subarray/dev_c/1=ObsState.IDLE"
        ).described_as(
            "The action name and description are expected to be mentioned"
        ).contains(
            setter.name()
        ).contains(
            setter.description()
        )

    @staticmethod
    def test_postconditions_fail_when_system_state_is_not_consistent(
        system: MockSubarraySystem,
    ):
        """The postconditions fail when the system state is not consistent."""
        setter = ObsStateSetter(system, ObsState.ABORTED, subarray_id=3)
        system.set_controller_obs_state(ObsState.ABORTED)
        system.set_obs_state_other_devices(ObsState.ABORTED)
        system.set_partial_obs_state(ObsState.ABORTING, 1)

        with pytest.raises(ObsStateSystemNotConsistent) as exc_info:
            setter.verify_postconditions()

        assert_that(str(exc_info.value)).described_as(
            "The error message is expected to contain the target state"
        ).contains(
            "is expected to be in a consistent observation state "
            "ObsState.ABORTED"
        ).described_as(
            "The error message is expected to mention the actual state of "
            "the devices"
        ).contains(
            "subarray/dev_a/1=ObsState.ABORTED"
        ).contains(
            "subarray/dev_b/1=ObsState.ABORTING",
        ).contains(
            "subarray/dev_c/1=ObsState.ABORTED"
        ).described_as(
            "The action name and description are expected to be mentioned"
        ).contains(
            setter.name()
        ).contains(
            setter.description()
        ).described_as(
            "The error message is expected to mention the the subarray ID"
        ).contains(
            "subarray 3"
        )
