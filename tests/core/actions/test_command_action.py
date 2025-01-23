"""Unit tests for the TangoCommandAction class."""

from unittest.mock import MagicMock

from assertpy import assert_that
import pytest

from ska_integration_test_harness.core.actions.command_action import (
    TangoCommandAction,
)


@pytest.mark.core
class TestTangoCommandAction:
    """Unit tests for the TangoCommandAction class."""
 
    def test_execute_procedure_with_args_and_kwargs(self):
        """Execute procedure with command arguments and keyword arguments."""
        device = MagicMock()
        device.command_inout.return_value = "result"
        action = TangoCommandAction(
            target_device=device,
            command_name="TestCommand",
            command_args=[1, 2],
            command_kwargs={"param": "value"},
        )

        action.execute_procedure()

        device.command_inout.assert_called_once_with(
            "TestCommand", 1, 2, param="value"
        )
        assert_that(action.last_command_result).is_equal_to("result")

    def test_execute_procedure_without_args_and_kwargs(self):
        """Execute procedure without command arguments and keyword args."""
        device = MagicMock()
        device.command_inout.return_value = "result"
        action = TangoCommandAction(
            target_device=device,
            command_name="TestCommand",
        )

        action.execute_procedure()

        device.command_inout.assert_called_once_with("TestCommand")
        assert_that(action.last_command_result).is_equal_to("result")

    def test_description_includes_command_and_arguments(self):
        """Description includes the command name and its arguments."""
        device = MagicMock()
        device.dev_name.return_value = "test/device"
        action = TangoCommandAction(
            target_device=device,
            command_name="TestCommand",
            command_args=[1, 2],
            command_kwargs={"param": "value"},
        )

        description = action.description()

        assert_that(description).contains(
            "Execute command TestCommand",
            "on device test/device",
            "with args [1, 2]",
            "and kwargs {'param': 'value'}",
        )

    def test_description_without_arguments(self):
        """Description without command arguments and keyword arguments."""
        device = MagicMock()
        device.dev_name.return_value = "test/device"
        action = TangoCommandAction(
            target_device=device,
            command_name="TestCommand",
        )

        description = action.description()

        assert_that(description).contains(
            "Execute command TestCommand",
            "on device test/device",
        ).does_not_contain("with args", "and kwargs")
