"""Tear down helper for emulated telescope subsystems."""

import json

from ska_control_model import HealthState
from tango import DeviceProxy


class EmulatedTeardownHelper:
    """Tear down helper for emulated telescope subsystems."""

    @staticmethod
    def clear_command_call(devices: list[DeviceProxy]) -> None:
        """Clear the command call of the given devices."""
        for device in devices:
            device.ClearCommandCallInfo()

    @staticmethod
    def reset_delay(devices: list[DeviceProxy]) -> None:
        """Reset the delay of the given devices."""
        for device in devices:
            device.ResetDelay()

    @staticmethod
    def reset_health_state(devices: list[DeviceProxy]) -> None:
        """Reset the health state of the given devices."""
        for device in devices:
            device.SetDirectHealthState(HealthState.UNKNOWN)

    @staticmethod
    def reset_transitions_data(devices: list[DeviceProxy]) -> None:
        """Reset the transition data of the given devices."""
        for device in devices:
            device.ResetTransitions()

    @staticmethod
    def unset_defective_status(devices: list[DeviceProxy]) -> None:
        """Unset the defective status of the given devices."""
        for device in devices:
            device.SetDefective(json.dumps({"enabled": False}))
