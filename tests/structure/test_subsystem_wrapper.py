"""Unit tests for the SubsystemWrapper class."""

from unittest.mock import MagicMock

import tango
from assertpy import assert_that

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)
from tests.common_utils.utils import inject_device_info


# Mock subclass to implement abstract methods for testing
class MockSubsystemWrapper(SubsystemWrapper):
    """Mock implementation of SubsystemWrapper for testing."""

    def get_subsystem_name(self) -> str:
        return "MockSubsystem"

    def get_all_devices(self) -> dict[str, MagicMock]:
        # Mocking tango.DeviceProxy objects for devices
        device1 = MagicMock(spec=tango.DeviceProxy)
        device1.dev_name.return_value = "tango/device/1"
        device2 = MagicMock(spec=tango.DeviceProxy)
        device2.dev_name.return_value = "tango/device/2"
        return {"tango/device/1": device1, "tango/device/2": device2}

    def is_emulated(self) -> bool:
        return False


class TestSubsystemWrapper:
    """Unit tests for the SubsystemWrapper class.

    For now, we are testing the get_recap method.
    """

    def test_get_recap_production_without_devices_info(self):
        """Returns recap for production system without devices info."""
        subsystem = MockSubsystemWrapper()

        recap = subsystem.get_recap()

        assert_that(recap).is_equal_to(
            "MockSubsystem (production). Devices:\n"
            "- tango/device/1: tango/device/1\n"
            "- tango/device/2: tango/device/2\n"
        )

    def test_get_recap_emulated_without_devices_info(self):
        """Returns recap for emulated system without devices info."""
        # Mock an emulated subsystem
        subsystem = MockSubsystemWrapper()
        subsystem.is_emulated = MagicMock(return_value=True)

        recap = subsystem.get_recap()

        assert_that(recap).is_equal_to(
            "MockSubsystem (emulated). Devices:\n"
            "- tango/device/1: tango/device/1\n"
            "- tango/device/2: tango/device/2\n"
        )

    def test_get_recap_production_with_devices_info(self):
        """Returns recap for production system with devices info."""
        # Inject actual devices info
        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        inject_device_info(devices_info_provider, "tango/device/1", "1.0.0")
        inject_device_info(devices_info_provider, "tango/device/2", None)

        subsystem = MockSubsystemWrapper()
        recap = subsystem.get_recap(devices_info_provider)

        assert_that(recap).is_equal_to(
            "MockSubsystem (production). Devices:\n"
            "- tango/device/1: tango/device/1 (version: 1.0.0)\n"
            "- tango/device/2: tango/device/2 (version: not available)\n"
        )

    def test_get_recap_emulated_with_devices_info(self):
        """Returns recap for emulated system with devices info."""
        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        inject_device_info(devices_info_provider, "tango/device/1", "1.0.0")
        inject_device_info(devices_info_provider, "tango/device/2", None)

        subsystem = MockSubsystemWrapper()
        subsystem.is_emulated = MagicMock(return_value=True)

        recap = subsystem.get_recap(devices_info_provider)

        assert_that(recap).is_equal_to(
            "MockSubsystem (emulated). Devices:\n"
            "- tango/device/1: tango/device/1 (version: 1.0.0)\n"
            "- tango/device/2: tango/device/2 (version: not available)\n"
        )

    def test_get_recap_with_empty_devices_info(self):
        """Returns recap for production system with empty devices info."""
        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        devices_info_provider.last_devices_info = {}

        subsystem = MockSubsystemWrapper()
        recap = subsystem.get_recap(devices_info_provider)

        assert_that(recap).contains(
            "MockSubsystem (production). Devices:\n", 
            "- tango/device/1: tango/device/1 (not found",
            "- tango/device/2: tango/device/2 (not found",
        )