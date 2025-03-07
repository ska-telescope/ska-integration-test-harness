"""Mock ska_tango_testing.integration.event.ReceivedEvent for testing."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import tango
from ska_tango_testing.integration.event import ReceivedEvent


def create_received_event_mock(
    device_name: str,
    attribute_name: str,
    attribute_value: str,
    seconds_ago: float = 0,
):
    """Create a mock for a ReceivedEvent object.

    The mock object:

    - has the properties device_name, attribute_name and attribute_value
    - implements the methods has_device and has_attribute
        (with an exact match)

    :param device_name: The name of the device.
    :param attribute_name: The name of the attribute.
    :param attribute_value: The value of the attribute.
    :param seconds_ago: The number of seconds ago the event occurred.
        It is optional and defaults to 0.
    :return: A mock object for a Received
    """
    event = MagicMock(spec=ReceivedEvent)
    event.device_name = device_name
    event.attribute_name = attribute_name
    event.attribute_value = attribute_value
    event.reception_time = datetime.now() - timedelta(seconds=seconds_ago)

    def has_device(target_device_name):
        """Check if the event is for a given device."""
        if isinstance(target_device_name, tango.DeviceProxy):
            target_device_name = target_device_name.dev_name()
        return event.device_name == target_device_name

    event.has_device = has_device
    event.has_attribute = (
        lambda target_attribute_name: event.attribute_name.lower()
        == target_attribute_name.lower()
    )
    device_name_str = (
        device_name if isinstance(device_name, str) else device_name.dev_name()
    )

    def to_str(_):
        """Return a string representation of the event."""
        msg = "ReceivedEvent("
        msg += f"device_name={device_name_str}, "
        msg += f"attribute_name={attribute_name}, "
        msg += f"attribute_value={attribute_value})"
        return msg

    event.__str__ = to_str

    return event
