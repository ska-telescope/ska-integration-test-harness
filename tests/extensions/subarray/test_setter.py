"""Unit tests for the ObsStateSetter class."""

import pytest
from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.setter import (
    ObsStateSetter,
)
from ska_integration_test_harness.extensions.subarray.setter_step import (  # pylint: disable=line-too-long # noqa
    ObsStateCommandsInput,
    ObsStateSetterStep,
)

from .utils import MockSubarraySystem


class MockObsStateSetterStep(ObsStateSetterStep):
    """A mock step for testing purposes."""

    def get_assumed_obs_state(self):
        return ObsState.IDLE

    def execute_procedure(self):
        """Do nothing."""


@pytest.mark.extensions
class TestObsStateSetter:
    """Unit tests for the ObsStateSetter class.

    TODO: change this description to reflect the actual class being tested.
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
    # Tests on ObsState - Steps map

    @staticmethod
    def test_obs_state_steps_map_contains_all_and_only_obs_states(
        system: MockSubarraySystem,
    ):
        """The map contains all and only the expected observation states."""
        setter = ObsStateSetter(system, ObsState.EMPTY)

        for obs_state in ObsState:
            assert_that(setter.obs_states_steps_map.keys()).described_as(
                f"The map keys contains the observation state {str(obs_state)}"
            ).contains(obs_state)
            assert_that(
                setter.obs_states_steps_map[obs_state].get_assumed_obs_state()
            ).described_as(
                f"The step associated to {obs_state} assumes the correct "
                "observation state"
            )

        assert_that(setter.obs_states_steps_map.keys()).described_as(
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
                setter.obs_states_steps_map[obs_state].system
            ).described_as(
                f"The step associated to {obs_state} has the correct system"
            ).is_equal_to(
                system
            )
            assert_that(
                setter.obs_states_steps_map[obs_state].target_state
            ).described_as(
                f"The step associated to {obs_state} has the correct target"
            ).is_equal_to(
                ObsState.READY
            )
            assert_that(
                setter.obs_states_steps_map[obs_state].subarray_id
            ).described_as(
                f"The step associated to {obs_state} has the "
                "correct subarray ID"
            ).is_equal_to(
                5
            )
            assert_that(
                setter.obs_states_steps_map[obs_state].commands_input
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

        assert_that(setter.obs_states_steps_map[ObsState.IDLE]).described_as(
            "The map is expected to be successfully overridden with an "
            "instance of the new class"
        ).is_instance_of(MockObsStateSetterStep)
        new_instance = setter.obs_states_steps_map[ObsState.IDLE]
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
