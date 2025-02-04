"""Unit tests for the TangoCommandAction class."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

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
            command_param="PARAM",
            command_kwargs={"timeout": 10},
        )

        action.execute_procedure()

        device.command_inout.assert_called_once_with(
            "TestCommand", cmd_param="PARAM", timeout=10
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

        device.command_inout.assert_called_once_with(
            "TestCommand", cmd_param=None
        )
        assert_that(action.last_command_result).is_equal_to("result")

    def test_description_includes_command_and_arguments(self):
        """Description includes the command name and its arguments."""
        device = MagicMock()
        device.dev_name.return_value = "test/device"
        action = TangoCommandAction(
            target_device=device,
            command_name="TestCommand",
            command_param="PARAM",
            command_kwargs={"timeout": 10},
        )

        description = action.description()

        assert_that(description).contains(
            "Execute command TestCommand",
            "on device test/device",
            "with param PARAM",
            "and kwargs {'timeout': 10}",
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
