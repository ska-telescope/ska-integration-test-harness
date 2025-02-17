# pylint: disable=invalid-name

"""Utilities for testing the subarray extension."""

from unittest.mock import MagicMock, patch

from ska_control_model import ObsState

from ska_integration_test_harness.extensions.lrc.tango_lrc_action import (
    TangoLRCAction,
)
from ska_integration_test_harness.extensions.subarray.system import (
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


class MockTangoLRCAction(TangoLRCAction):
    """A mock for the TangoLRCAction class."""

    def __init__(
        self,
        target_device,
        command_name,
        command_param=None,
        side_effect=None,
        **kwargs
    ):
        super().__init__(target_device, command_name, command_param, **kwargs)

        self.execute = MagicMock(side_effect=side_effect)
        """
        Execute is a mock that will be called instead of the real method.

        If given, it will also have a side effect that can be used to
        simulate the behaviour of the real method.
        """

    def is_logging_enabled(self) -> bool:
        """Check if the logger is enabled.

        :return: True if the logger is enabled, False otherwise.
        """
        return not self.logger.disabled


DEFAULT_PATCH_PATH = (
    "ska_integration_test_harness.extensions.subarray"
    ".commands_factory.TangoLRCAction"
)
"""
The default path to the class to patch (from the subarray commands factory).
"""


class MockTangoLRCActionPatcher:
    """A class to patch TangoLRCAction and track the instances created.

    Usage example:

    .. code-block:: python

        patcher = MockTangoLRCActionPatcher()
        with patcher.patch():
            # here the code that generates TangoLRCAction instances

            assert len(patcher.instances) == 1
            action = patcher.instances[0]
            # etc.
    """

    def __init__(self, patch_path: str = DEFAULT_PATCH_PATH, side_effect=None):
        """Create a new patcher.

        :param patch_path: The path to the class to patch. It defaults to
            the TangoLRCAction class from the subarray commands factory.
        :param side_effect: The side effect to inject in the mock instances.
        """
        self.patch_path: str = patch_path
        self.instances: list[MockTangoLRCAction] = []
        self.side_effect = side_effect

    def reset(self):
        """Reset the list of instances created."""
        self.instances = []

    def create_instance(self, *args, **kwargs) -> MockTangoLRCAction:
        """Create a new instance of the patched class.

        And track its creation as a side effect.

        :param args: Positional arguments to pass to the constructor.
        :param kwargs: Keyword arguments to pass to the constructor.
        :return: The new instance.
        """
        instance = MockTangoLRCAction(
            *args, **kwargs, side_effect=self.side_effect
        )
        self.instances.append(instance)
        return instance

    def patch(self):
        """Patch the TangoLRCAction class.

        Usage example:

        .. code-block:: python

            patcher = MockTangoLRCActionPatcher()
            with patcher.patch():
                # here the code that generates TangoLRCAction instances

                assert len(patcher.instances) == 1
                action = patcher.instances[0]
                # etc.

        :return: Whatever ``unittest.mock.patch`` returns.
        """
        return patch(self.patch_path, side_effect=self.create_instance)
