"""Mock ska_tango_testing.integration.event.ReceivedEvent for testing."""

from unittest.mock import MagicMock

from ska_tango_testing.integration.event import ReceivedEvent


def create_received_event_mock(
    device_name: str, attribute_name: str, attribute_value: str
):
    """Create a mock for a ReceivedEvent object.

    The mock object:

    - has the properties device_name, attribute_name and attribute_value
    - implements the methods has_device and has_attribute
        (with an exact match)

    :param device_name: The name of the device.
    :param attribute_name: The name of the attribute.
    :param attribute_value: The value of the attribute.
    :return: A mock object for a Received
    """
    event = MagicMock(spec=ReceivedEvent)
    event.device_name = device_name
    event.attribute_name = attribute_name
    event.attribute_value = attribute_value
    event.has_device = (
        lambda target_device_name: event.device_name == target_device_name
    )
    event.has_attribute = (
        lambda target_attribute_name: event.attribute_name
        == target_attribute_name
    )
    return event
