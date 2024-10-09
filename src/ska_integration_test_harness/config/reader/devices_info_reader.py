"""Abstract definition of a reader for devices information."""

import abc

from ..tango_devices_info import TelescopeDevicesInfo


class DevicesInfoNotAvailableException(Exception):
    """Exception raised when the devices information is not available."""

    def __init__(self, message: str = ""):
        """Initializes the exception."""
        self.message = "Devices information not available."
        if message:
            self.message += f"Potential cause: {message}"
        super().__init__(self.message)


class TelescopeDevicesInfoReader(abc.ABC):
    """Abstract definition of a reader for devices information.

    It exposes a method to read the devices information from the
    `ska-k8s-config-exporter <https://gitlab.com/ska-telescope/ska-k8s-config-exporter>`_
    service.

    If the service is not available, the method should raise an exception.
    """  # pylint: disable=line-too-long # noqa: E501

    # pylint: disable=too-few-public-methods

    @abc.abstractmethod
    def read_devices_info(self) -> TelescopeDevicesInfo:
        """Read the devices information.

        return: The devices information.
        """
