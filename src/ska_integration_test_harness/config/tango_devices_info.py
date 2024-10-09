"""Classes to manage info about Tango devices from ska-k8s-config-exporter."""

from dataclasses import dataclass
from typing import Iterable


class MissingTangoDeviceException(Exception):
    """Exception raised when a Tango device is not found."""

    def __init__(self, device_name: str):
        """Initializes the exception with the name of the missing device.

        :param device_name: Name of the missing device.
        """
        self.message = f"Tango device '{device_name}' not found."
        super().__init__(self.message)


@dataclass
class TangoDeviceInfo:
    """Information about a Tango device from ska-k8s-config-exporter.

    Information related to a Tango device collected by the
    `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
    tool. The information includes:

    - the name of the device (always present)
    - the version of the device (may be None)
    """  # pylint: disable=line-too-long # noqa: E501

    name: str
    """Name of the device in the Tango database."""

    version: str | None = None
    """Version of the device, if available."""

    # TODO: are other information interesting to include here?


class TelescopeDevicesInfo:
    """Collection of devices information from ska-k8s-config-exporter.

    A representation of the devices information collected by the
    `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
    tool. The collection is a mapping of device names to device information.

    The collection can be initialized with a list of devices, and new devices
    can be added to it. The version of a device can be retrieved by its name.
    An exception is raised if the device is not found in the collection.
    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(self, devices: Iterable[TangoDeviceInfo] | None = None):
        """Initializes the collection with the given devices.

        :param devices: Association of device names to device information.
        """

        self.devices: dict[str, TangoDeviceInfo] = {}
        """Association of device names to device information."""

        for device in devices or []:
            self.add_device(device)

    def add_device(self, device_info: TangoDeviceInfo):
        """Adds a device to the collection.

        :param device_info: Information about the device.
        """
        self.devices[device_info.name] = device_info

    def get_version(self, device_name: str) -> str | None:
        """Get the version of a device from its name.

        :param device_name: Name of the device.
        :return: Version of the device, if available.
        :raises MissingTangoDevice: If the device is not found.
        """
        if device_name not in self.devices:
            raise MissingTangoDeviceException(device_name)
        return self.devices[device_name].version
