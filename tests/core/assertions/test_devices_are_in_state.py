"""Unit tests for the DevicesAreInState class."""

import pytest
from assertpy import assert_that

from ska_integration_test_harness.core.assertions.devices_are_in_state import (
    AssertDevicesAreInState,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock


@pytest.mark.core
class TestDevicesAreInState:
    """Unit tests for the DevicesAreInState class."""

    def test_all_devices_in_expected_state(self):
        """All devices are in the expected state."""
        devices = [
            create_device_proxy_mock("test/dev/1", "state", "ON"),
            create_device_proxy_mock("test/dev/2", "state", "ON"),
        ]

        assertion = AssertDevicesAreInState(devices, "state", "ON")
        assertion.verify()

    def test_some_devices_not_in_expected_state(self):
        """Some devices are not in the expected state."""
        devices = [
            create_device_proxy_mock("test/dev/1", "state", "ON"),
            create_device_proxy_mock("test/dev/2", "state", "OFF"),
        ]

        assertion = AssertDevicesAreInState(devices, "state", "ON")
        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "The failure description includes a reference to the devices, "
            "the attribute name and the expected value."
        ).contains("test/dev/1", "test/dev/2", "state", "ON").described_as(
            "The failure message includes a specific reference to the "
            "device and attribute that failed."
        ).contains(
            "test/dev/2.state"
        ).described_as(
            "The failure message includes a reference to the observed value."
        ).contains(
            "OFF"
        )

    def test_no_devices_provided(self):
        """No devices are provided."""
        devices = []

        assertion = AssertDevicesAreInState(devices, "state", "ON")
        assertion.verify()

    def test_describe_assumption(self):
        """Describe the assumption of the assertion."""
        devices = [
            create_device_proxy_mock("test/dev/1"),
            create_device_proxy_mock("test/dev/2"),
        ]

        assertion = AssertDevicesAreInState(devices, "state", "ON")
        description = assertion.describe_assumption()

        assert_that(description).described_as(
            "The description includes a reference to the devices, "
            "the attribute name and the expected value."
        ).contains("test/dev/1", "test/dev/2", "state", "ON")
