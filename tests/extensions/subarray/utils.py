"""Utilities for testing the subarray extension."""

from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.obs_state_system import (
    ObsStateSystem,
)

from ...actions.utils.mock_device_proxy import create_device_proxy_mock


class MockSubarraySystem(ObsStateSystem):
    """Mock subarray system for testing purposes.

    It uses mock device proxies to simulate the subarray controller and
    a few obs state devices.
    """

    def __init__(self):
        self.subarray_controller = create_device_proxy_mock(
            "subarray/controller/1", "obsState", ObsState.EMPTY
        )

        self.obs_state_devices = [
            create_device_proxy_mock(
                "subarray/dev_a/1", "obsState", ObsState.EMPTY
            ),
            create_device_proxy_mock(
                "subarray/dev_b/1", "obsState", ObsState.EMPTY
            ),
            create_device_proxy_mock(
                "subarray/dev_c/1", "obsState", ObsState.EMPTY
            ),
        ]

    def get_target_device(self, command_name: str, subarray_id: int = 1):
        return self.subarray_controller

    def get_main_obs_state_device(self, subarray_id: int = 1):
        return self.subarray_controller

    def get_obs_state_devices(self, subarray_id: int = 1):
        return self.obs_state_devices
