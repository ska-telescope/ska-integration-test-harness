"""An action which is a command sent to TMC subarray."""

from ska_control_model import ResultCode

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class TelescopeCommandAction(TelescopeAction[tuple[ResultCode, str]]):
    """An action that send a command to some telescope subsystem.

    It is expected to return the tuple of result code and message.
    """
