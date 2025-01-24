"""Utilities for testing actions."""

import time
from unittest.mock import MagicMock

from ska_integration_test_harness.core.assertions.attribute import (
    AssertDevicesAreInState,
)
from ska_integration_test_harness.core.assertions.state_changes import (
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
