"""Module to get information about Tango devices from ska-k8s-config-exporter.

This module contains classes to get information about Tango devices from the
`ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
service. The information includes the name and version of the active
Tango devices.

The main classes are:

- :class:`TangoDeviceInfo`: Information about a Tango device.
- :class:`DevicesInfoProvider`: Provider to communicate with the
  service and get the devices information.
"""  # pylint: disable=line-too-long # noqa: E501

from dataclasses import dataclass
from datetime import datetime

import requests


class DevicesInfoServiceException(Exception):
    """The devices information is not available or something went wrong.

    i.e., when the ska-k8s-config-exporter service is not available.
    """

    def __init__(self, message: str = ""):
        """Initializes the exception."""
        self.message = (
            "Something went wrong when interrogating the devices information."
        )
        if message:
            self.message += f" Potential cause: {message}"
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
        """String representation of the device information."""
        return self.get_recap()

    def __repr__(self) -> str:
        """String representation of the device information."""
        return self.get_recap()


class DevicesInfoProvider:
    """Provider to get info about Tango devices from ska-k8s-config-exporter.

    This class communicates with the
    `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
    service to fetch
    and store the information about Tango devices. It also provides methods
    to retrieve device information and recaps.
    """  # pylint: disable=line-too-long # noqa: E501

    DEFAULT_SERVICE_NAME = "ska-k8s-config-exporter-service"
    """Default name of the ska-k8s-config-exporter service."""

    DEFAULT_PORT = 8080
    """Default port where the ska-k8s-config-exporter service is listening."""

    DEFAULT_PATH = "tango_devices"
    """Default path to interrogate the ska-k8s-config-exporter service."""

    def __init__(
        self,
        kube_namespace: str,
        service_name: str = DEFAULT_SERVICE_NAME,
        port: int = DEFAULT_PORT,
        path: str = DEFAULT_PATH,
    ):
        """Initializes the DevicesInfoProvider with connection parameters.

        :param kube_namespace: Kubernetes namespace where the
            service is running.
        :param service_name: Name of the ska-k8s-config-exporter service
            (has a default value).
        :param port: Port where the service is listening
            (has a default value).
        :param path: Path to interrogate the service
            (has a default value).
        """
        # -----------------------------------------------------------------
        # details to connect to the ska-k8s-config-exporter service

        self.kube_namespace = kube_namespace
        """Kubernetes namespace where the service is running."""
        self.service_name = service_name
        """Name of the ska-k8s-config-exporter service."""
        self.port = port
        """Port where the service is listening."""
        self.path = path
        """Path to interrogate on the service to get all devices."""

        # -----------------------------------------------------------------
        # devices information

        self.last_devices_info: dict[str, TangoDeviceInfo] = {}
        """Last devices information fetched from the service."""
        self.last_update_time: datetime | None = None
        """Time when the last update was done."""

    def get_update_service_url(self) -> str:
        """Get the URL to update the devices information.

        :return: URL to update the devices information.
        """
        return (
            f"http://{self.service_name}.{self.kube_namespace}"
            f":{self.port}/{self.path}"
        )

    def update(self, timeout: int = 10) -> None:
        """Update the local devices information by calling the service.

        Fetches the latest devices information from the ska-k8s-config-exporter
        service and updates the internal state.

        :param timeout: Timeout in seconds for the request
            (default: 10 seconds).
        :raises DevicesInfoServiceException: If the service
            is not available, or it does not respond as expected.
        """
        url = self.get_update_service_url()
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise DevicesInfoServiceException(
                f"Error when interrogating '{url}'."
            ) from error

        try:
            json_data: dict = response.json()
        except ValueError as error:
            raise DevicesInfoServiceException(
                f"Received invalid JSON data when interrogating '{url}'"
            ) from error

        items = json_data.get("tango_devices_info")
        if items is None or not isinstance(items, dict):
            raise DevicesInfoServiceException(
                f"The received JSON data (from '{url}') does not "
                "contain the expected 'tango_devices_info' key "
                f"or it is not a dictionary (value: {items})."
            )

        self.last_devices_info = {
            name: self._extract_device_info(name, data)
            for name, data in items.items()
        }
        self.last_update_time = datetime.now()

    def get_device_recap(self, device_name: str) -> str:
        """Get a recap of the given device information.

        The recap contains the device name and its information (for now,
        only the version). If the device is not found, it is reported
        in the recap.

        :param device_name: Name of the device to get the recap.
        :return: Recap of the device information.
        """
        if device_name in self.last_devices_info:
            return str(self.last_devices_info[device_name])

        return (
            f"{device_name} (not found among the "
            "k8s-config-exporter devices information)"
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
