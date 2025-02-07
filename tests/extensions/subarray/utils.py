# pylint: disable=invalid-name

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

    # -------------------------------------------------------------------------
    # Mock methods

    def set_controller_obs_state(self, obs_state):
        """Set the subarray controller obsState.

        :param obs_state: The new obsState for the subarray controller.
        """
        self.subarray_controller.obsState = obs_state

    def set_obs_state_other_devices(self, obs_state):
        """Set the obsState of all other devices.

        :param obs_state: The new obsState for the devices.
        """
        for device in self.obs_state_devices:
            device.obsState = obs_state

    def set_partial_obs_state(self, obs_state, device_index=0):
        """Set the obsState of a single device, ignoring the others.

        :param obs_state: The new obsState for the device.
        :param device_index: The index of the device to update.
            It defaults to 0 but it can be also 1 or 2.
        """
        self.obs_state_devices[device_index].obsState = obs_state
