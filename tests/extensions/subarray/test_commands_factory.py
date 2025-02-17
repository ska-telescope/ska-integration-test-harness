"""Unit tests for the observation state commands factory."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.core.assertions.dev_state_changes import (
    AssertDevicesStateChanges,
)
from ska_integration_test_harness.extensions.lrc.tango_lrc_action import (
    TangoLRCAction,
)
from ska_integration_test_harness.extensions.subarray.commands_factory import (  # pylint: disable=line-too-long # noqa: E501
    ObsStateCommandDoesNotExist,
    ObsStateCommandsFactory,
)

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateCommandsFactory:
    """Unit tests for the observation state commands factory.

    The tests cover:

    - the happy path (the creation of valid observation state commands
      with or without postconditions)
    - error paths (the creation of an invalid command, the creation
      of a command with a transient postcondition when it should not)

    """

    @pytest.fixture
    @staticmethod
    def obs_state_system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    # -----------------------------------------------------------------
    # Happy paths

    @staticmethod
    def test_create_assign_resources_has_expected_name_target_param(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        command = factory.create_action_with_sync(
            "AssignResources", '{"dummy": "data"}'
        )

        assert_that(command).described_as(
            "A TangoLRCAction is created for the given command."
        ).is_instance_of(TangoLRCAction)
        assert_that(command.command_name).described_as(
            "The command name is set on the action."
        ).is_equal_to("AssignResources")
        assert_that(command.target_device).described_as(
            "The target device is the expected subarray controller."
        ).is_equal_to(obs_state_system.subarray_controller)
        assert_that(command.command_param).described_as(
            "The command param is the expected JSON data."
        ).is_equal_to('{"dummy": "data"}')
        assert_that(command.postconditions).described_as(
            "The postconditions are not set on the action."
        ).is_empty()

    @staticmethod
    def test_create_assign_resources_has_expected_postconditions(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        command = factory.create_action_with_sync(
            "AssignResources",
            '{"dummy": "data"}',
            sync_transient=True,
            sync_quiescent=True,
        )

        assert_that(command.postconditions).described_as(
            "The postconditions are set on the action."
        ).is_length(2)
        assert_that(command.postconditions[0]).described_as(
            "The transient postcondition is a state change assertion"
        ).is_instance_of(AssertDevicesStateChanges)
        assert_that(command.postconditions[0].devices).described_as(
            "The transient postcondition devices "
            "are the expected obs state devices."
        ).is_equal_to(obs_state_system.obs_state_devices)
        assert_that(command.postconditions[0].attribute_name).described_as(
            "The transient postcondition attribute name is 'obsState'."
        ).is_equal_to("obsState")
        assert_that(command.postconditions[0].attribute_value).described_as(
            "The transient postcondition attribute value is RESOURCING."
        ).is_equal_to(ObsState.RESOURCING)
        assert_that(command.postconditions[1]).described_as(
            "The quiescent postcondition is a state change assertion"
        ).is_instance_of(AssertDevicesStateChanges)
        assert_that(command.postconditions[1].devices).described_as(
            "The quiescent postcondition devices "
            "are the expected obs state devices."
        ).is_equal_to(obs_state_system.obs_state_devices)
        assert_that(command.postconditions[1].attribute_name).described_as(
            "The quiescent postcondition attribute name is 'obsState'."
        ).is_equal_to("obsState")
        assert_that(command.postconditions[1].attribute_value).described_as(
            "The quiescent postcondition attribute value is IDLE."
        ).is_equal_to(ObsState.IDLE)
        assert_that(command.postconditions[1].previous_value).described_as(
            "The quiescent postcondition previous value is RESOURCING."
        ).is_equal_to(ObsState.RESOURCING)

    @staticmethod
    def test_create_configure_without_quiescent_postcondition(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        command = factory.create_action_with_sync(
            "Configure",
            '{"dummy": "data"}',
            sync_quiescent=False,
            sync_transient=True,
        )

        assert_that(command.postconditions).described_as(
            "There is only one postcondition (transient)."
        ).is_length(1)
        assert_that(command.postconditions[0]).described_as(
            "The transient postcondition is a state change assertion"
        ).is_instance_of(AssertDevicesStateChanges)
        assert_that(command.postconditions[0].devices).described_as(
            "The transient postcondition devices "
            "are the expected obs state devices."
        ).is_equal_to(obs_state_system.obs_state_devices)
        assert_that(command.postconditions[0].attribute_name).described_as(
            "The transient postcondition attribute name is 'obsState'."
        ).is_equal_to("obsState")
        assert_that(command.postconditions[0].attribute_value).described_as(
            "The transient postcondition attribute value is CONFIGURING."
        ).is_equal_to(ObsState.CONFIGURING)

    @staticmethod
    def test_create_abort_without_transient_postcondition(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        command = factory.create_action_with_sync(
            "Abort", sync_transient=False, sync_quiescent=True
        )

        assert_that(command.postconditions).described_as(
            "There is only one postcondition (quiescent)."
        ).is_length(1)
        assert_that(command.postconditions[0]).described_as(
            "The quiescent postcondition is a state change assertion"
        ).is_instance_of(AssertDevicesStateChanges)
        assert_that(command.postconditions[0].devices).described_as(
            "The quiescent postcondition devices "
            "are the expected obs state devices."
        ).is_equal_to(obs_state_system.obs_state_devices)
        assert_that(command.postconditions[0].attribute_name).described_as(
            "The quiescent postcondition attribute name is 'obsState'."
        ).is_equal_to("obsState")
        assert_that(command.postconditions[0].attribute_value).described_as(
            "The quiescent postcondition attribute value is ABORTED."
        ).is_equal_to(ObsState.ABORTED)
        assert_that(command.postconditions[0].previous_value).described_as(
            "The quiescent postcondition previous value is not set."
        ).is_none()

    # -----------------------------------------------------------------
    # Error paths

    @staticmethod
    def test_create_invalid_command_raises_value_error(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        with pytest.raises(ObsStateCommandDoesNotExist) as exc_info:
            factory.create_action_with_sync("InvalidCommand")

        assert_that(str(exc_info.value)).described_as(
            "The exception message contains the invalid command name."
        ).contains("Command 'InvalidCommand' does not exist")

    @staticmethod
    def test_create_end_command_requiring_transient_sync_raises_value_error(
        obs_state_system: MockSubarraySystem,
    ):
        """Create an observation state command.

        :param obs_state_system: The observation state system.
        """
        obs_state_system.subarray_controller = MagicMock()
        factory = ObsStateCommandsFactory(obs_state_system)

        with pytest.raises(ValueError) as exc_info:
            factory.create_action_with_sync("End", sync_transient=True)

        assert_that(str(exc_info.value)).described_as(
            "The exception message contains the command name."
        ).contains("Command 'End' hasn't a transient obsState transition")
