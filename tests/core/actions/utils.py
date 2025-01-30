"""Utilities for testing actions."""

import time
from typing import SupportsFloat
from unittest.mock import MagicMock

from ska_integration_test_harness.core.actions.sut_action import SUTAction
from ska_integration_test_harness.core.assertions.dev_are_in_state import (
    AssertDevicesAreInState,
)
from ska_integration_test_harness.core.assertions.dev_state_changes import (
    AssertDevicesStateChanges,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock


def create_state_change_assertion(
    dev_name, expected_state="ON"
) -> AssertDevicesStateChanges:
    """Create a state change assertion for the given device.

    :param dev_name: the name of the device
    :param expected_state: the expected state (default: "ON")
    :return: the state change assertion
    """
    return AssertDevicesStateChanges(
        [create_device_proxy_mock(dev_name)], "state", expected_state
    )


def create_simple_assertion(
    dev_name, expected_state="ON"
) -> AssertDevicesAreInState:
    """Create a simple assertion for the given device.

    :param dev_name: the name of the device
    :param expected_state: the expected state (default: "ON")
    :return: the state change assertion
    """
    return AssertDevicesAreInState(
        [create_device_proxy_mock(dev_name)], "state", expected_state
    )


def create_mock_assertion(
    duration: float = 0, fail: bool = False
) -> MagicMock:
    """Create a mock assertion."""

    def mock_verify():
        time.sleep(duration)
        if fail:
            raise AssertionError("Mock assertion failed")

    mock = MagicMock()
    mock.verify = MagicMock(side_effect=mock_verify)

    return mock


class MockSUTAction(SUTAction):
    """Mock subclass of SUTAction for testing purposes."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        fail_preconditions=False,
        fail_procedure=False,
        fail_postconditions=False,
        **kwargs,
    ):
        """Initialise the mock action.

        :param fail_preconditions: Flag to indicate if preconditions
            should fail
        :param fail_procedure: Flag to indicate if the procedure should fail
        :param fail_postconditions: Flag to indicate if postconditions
            should fail
        **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.fail_preconditions = fail_preconditions
        self.fail_procedure = fail_procedure
        self.fail_postconditions = fail_postconditions
        self.setup_called = False
        self.preconditions_verified = False
        self.procedure_executed = False
        self.postconditions_verified = False
        self.last_timeout = None

    def setup(self) -> None:
        self.setup_called = True

    def verify_preconditions(self) -> None:
        if self.fail_preconditions:
            raise AssertionError("Preconditions failed")
        self.preconditions_verified = True

    def execute_procedure(self) -> None:
        if self.fail_procedure:
            raise AssertionError("Procedure failed")
        self.procedure_executed = True

    def verify_postconditions(self, timeout: SupportsFloat = 0) -> None:
        self.last_timeout = float(timeout)
        if self.fail_postconditions:
            raise AssertionError("Postconditions failed")
        self.postconditions_verified = True

    def name(self) -> str:
        return "MockSUTAction"

    def description(self) -> str:
        return "Mock a SUT action and track calls"


# pylint: disable=too-many-arguments, too-many-positional-arguments
def assert_action_logged_execution(
    mock_logger: MagicMock,
    action_name: str,
    action_description: str,
    verify_preconditions=True,
    verify_postconditions=True,
    timeout=0,
):
    """Assert that the action logged correctly the execution.

    :param mock_logger: the mock logger
    :param action_name: the name of the action
    :param action_description: the description of the action
    :param verify_preconditions: flag to verify preconditions
    :param verify_postconditions: flag to verify postconditions
    :param timeout: the timeout for verifying postconditions
    """

    mock_logger.info.assert_any_call(
        "Executing action %s: %s "
        "(verify_preconditions=%s, verify_postconditions=%s)",
        action_name,
        action_description,
        verify_preconditions,
        verify_postconditions,
    )
    mock_logger.info.assert_any_call(
        "Action %s: procedure executed successfully. "
        "Verifying postconditions (within a %s seconds timeout)...",
        action_name,
        timeout,
    )
    mock_logger.info.assert_any_call(
        "Action %s: execution completed successfully",
        action_name,
    )
