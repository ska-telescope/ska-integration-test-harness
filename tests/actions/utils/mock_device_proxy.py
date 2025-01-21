"""Patch tango.DeviceProxy for testing."""

from typing import Any
from unittest.mock import MagicMock, patch

import tango


class DeviceProxyMock(MagicMock):
    """Mock class for mocking the DeviceProxy class.

    It supports the instance check for the DeviceProxy class.
    """

    def __instancecheck__(self, instance: Any) -> bool:
        """If it has a dev_name and subscribe_event, then it is a DeviceProxy.

        :param instance: The instance to check.
        :return: True if the instance is a DeviceProxy, False otherwise.
        """
        return all(
            hasattr(instance, method)
            for method in ["dev_name", "subscribe_event"]
        )


def create_device_proxy_mock(
    device_name: str, attribute_name: str | None = None, attribute_value=None
) -> MagicMock:
    """Create a mock for a DeviceProxy object.

    The mock object has a given device name and a given attribute wih a
    given value.

    :param device_name: The name of the device.
    :param attribute_name: The name of the attribute you want to exist in this
        device proxy.
    :param attribute_value: The value you want the attribute to have.

    :return: A mock object for a DeviceProxy.
    """
    mock_device_proxy = DeviceProxyMock(spec=tango.DeviceProxy)
    mock_device_proxy.dev_name.return_value = device_name

    if attribute_name is not None and attribute_value is not None:
        setattr(mock_device_proxy, attribute_name, attribute_value)
        mock_device_proxy.read_attribute.return_value = MagicMock(
            value=attribute_value
        )

    return mock_device_proxy


def patch_device_proxy(
    device_name: str | None = None,
    attribute_name: str | None = None,
    attribute_value: Any | None = None,
) -> Any:
    """Patch the DeviceProxy class to return a mock object.

    The mock object may contain a given name, attribute name and
    attribute value. It they are all set, the return value is initialised
    with these values.

    :param device_name: The name of the device.
    :return: The patched mock object.
    """
    if (
        device_name is None
        or attribute_name is None
        or attribute_value is None
    ):
        return patch("tango.DeviceProxy", new_callable=DeviceProxyMock)

    return patch(
        "tango.DeviceProxy",
        new_callable=DeviceProxyMock,
        return_value=create_device_proxy_mock(
            device_name, attribute_name, attribute_value
        ),
    )
