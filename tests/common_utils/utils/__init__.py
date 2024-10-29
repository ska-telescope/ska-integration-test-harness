"""Utils for unit testing common_utils module."""

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
    TangoDeviceInfo,
)


def inject_device_info(
    devices_info_provider: DevicesInfoProvider, device_name: str, version: str
):
    """Add a device to the devices information provider.

    :param devices_info_provider: The devices information provider.
    :param device_name: The name of the device to add.
    :param version: The version of the device to add.
    """
    devices_info_provider.last_devices_info[device_name] = TangoDeviceInfo(
        name=device_name, version=version
    )
