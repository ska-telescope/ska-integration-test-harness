"""Classes to manage info about Tango devices from ska-k8s-config-exporter."""

from dataclasses import dataclass
from typing import Iterable

import requests


class MissingTangoDeviceException(Exception):
    """Exception raised when a Tango device is not found."""

    def __init__(self, device_name: str):
        """Initializes the exception with the name of the missing device.

        :param device_name: Name of the missing device.
        """
        self.message = f"Tango device '{device_name}' not found."
        super().__init__(self.message)


class DevicesInfoNotAvailableException(Exception):
    """Exception raised when the devices information is not available.

    i.e., when the ska-k8s-config-exporter service is not available.
    """

    def __init__(self, message: str = ""):
        """Initializes the exception."""
        self.message = "Devices information not available."
        if message:
            self.message += f"Potential cause: {message}"
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

    def get_recap(self, include_version: bool = True) -> str:
        """Get a recap of the device information.

        Get a recap of the device information. The recap contains the device
        name and its information (for now, only the version if available).

        :param include_version: If True, the version is included in the recap.
        :return: Recap of the device information.
        """
        res = f"{self.name} "
        if include_version:
            res += f"(version: {self.version or 'not available'})"
        return res

    def __str__(self) -> str:
        """String representation of the device information.

        :return: The string representation.
        """
        return self.get_recap()

    def __repr__(self) -> str:
        """String representation of the device information.

        :return: The string representation.
        """
        return self.get_recap()


class TelescopeDevicesInfo:
    """Collection of devices information from ska-k8s-config-exporter.

    A representation of the devices read from the
    `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
    internal service.

    The collection can be initialized with a set of devices and can be queried
    to get the version of a device by its name.
    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(self, devices: Iterable[TangoDeviceInfo]):
        """Initializes the collection with the given devices.

        :param devices: Association of device names to device information.
        """

        self.devices: dict[str, TangoDeviceInfo] = {}
        """Association of device names to device information."""

        for device_info in devices:
            self.devices[device_info.name] = device_info

    # -----------------------------------------------------------------
    # Access to the devices information

    def get_device_info(self, device_name: str) -> TangoDeviceInfo:
        """Get the information of a device from its name.

        :param device_name: Name of the device.
        :return: Information of the device.
        :raises MissingTangoDevice: If the device is not found.
        """
        if device_name not in self.devices:
            raise MissingTangoDeviceException(device_name)
        return self.devices[device_name]

    def get_device_recap(self, device_name: str) -> str:
        """Get a recap of the given device information.

        Get a recap of the device information for the given device.
        The recap contains the device name and its information
        (for now, only the version). If the device is not found,
        it is reported in the recap.

        :param device_name: Name of the device you want to get the recap.
        :return: Recap of the device information.
        """
        try:
            device_info = self.get_device_info(device_name)
            return device_info.get_recap()
        except MissingTangoDeviceException:
            return (
                f"{device_name} (not found among the "
                "k8s-config-exporter devices information)"
            )

    # -----------------------------------------------------------------
    # Static method to read from ska-k8s-config-exporter

    DEFAULT_SERVICE_NAME = "ska-k8s-config-exporter"
    """Default name of the ska-k8s-config-exporter service."""

    DEFAULT_PORT = 8080
    """Default port where the ska-k8s-config-exporter service is listening."""

    DEFAULT_PATH = "tango_devices"
    """Default path to interrogate the ska-k8s-config-exporter service."""

    @staticmethod
    def read_from_ska_k8s_config_exporter(
        kube_namespace: str,
        service_name: str = DEFAULT_SERVICE_NAME,
        port: int = DEFAULT_PORT,
        path: str = DEFAULT_PATH,
        timeout: int = 10,
    ) -> "TelescopeDevicesInfo":
        """Interrogate ska-k8s-config-exporter and get the devices information.

        Interrogate the
        `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
        service to get the devices information. To do so, this method should
        know:

        - the kubernetes namespace where the service is running (mandatory)
        - the name of the service (has a default value, usually it
          does not need to be changed)
        - the port where the service is listening (has a default value, usually
          it does not need to be changed)
        - the path to interrogate the service (has a default value, usually
          it does not need to be changed)

        If the service is not available, the method raises an exception.

        :param kube_namespace: Kubernetes namespace where the
            service is running.
        :param service_name: Name of the service.
        :param port: Port where the service is listening.
        :param path: Path to interrogate the service.
        :param timeout: Timeout in seconds for the request
            (default: 10 seconds).

        :return: The devices information.

        :raises DevicesInfoNotAvailable: If the service is not available.
        """  # pylint: disable=line-too-long # noqa: E501

        url = f"http://{service_name}.{kube_namespace}:{port}/{path}"
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise DevicesInfoNotAvailableException(
                f"Error when interrogating '{url}'."
            ) from error

        try:
            json_data: dict = response.json()
        except ValueError as error:
            raise DevicesInfoNotAvailableException(
                f"Received invalid JSON data when interrogating '{url}'"
            ) from error

        items = json_data.get("tango_devices_info")
        if items is None or not isinstance(items, dict):
            raise DevicesInfoNotAvailableException(
                f"The received JSON data (from '{url}') does not "
                "contain the expected 'tango_devices_info' key "
                f"or it is not a dictionary (value: {items})."
            )

        return TelescopeDevicesInfo(
            [
                TelescopeDevicesInfo._extract_device_info(name, data)
                for name, data in items.items()
            ]
        )

    @staticmethod
    def _extract_device_info(name: str, data: dict) -> TangoDeviceInfo:
        """Extracts the device information from the data dictionary.

        :param name: Name of the device.
        :param data: Data dictionary. For now, it is expected to have:
            - info.device_versionId: The version of the device
              (may not be present).
        :return: The device information.
        """
        return TangoDeviceInfo(
            name=name, version=data.get("info", {}).get("device_versionId")
        )
