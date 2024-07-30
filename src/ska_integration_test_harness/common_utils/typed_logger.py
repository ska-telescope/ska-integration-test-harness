"""Create a logger that accepts typed log messages."""

from typing import Callable

import tango
from ska_tango_testing.integration.event import ReceivedEvent
from ska_tango_testing.integration.logger import TangoEventLogger

from ska_integration_test_harness.common_utils.typed_tracer import (
    EventTypeMapper,
)


# provide a quick utility function to log events
# (instead of a full logger)
def log_events(
    device_attribute_map: dict["str | tango.DeviceProxy", list[str]],
    attribute_enum_map: dict[str, type] | None = None,
    dev_factory: Callable[[str], tango.DeviceProxy] | None = None,
) -> TangoEventLogger:
    """Log events from devices and attributes, optionally specifying enums,


    :param device_attribute_map: A dictionary mapping devices to a list
        of attribute names you are interested in logging. Each device
        could be specified either as a device name (str) or as a
        :py:class:`tango.DeviceProxy` instance.
    :param attribute_enum_map: A dictionary mapping attributes to the
        corresponding enum class that should be used to interpret the
        attribute values.
    :param dev_factory: An optional factory function that can be used instead
        of the default :py:class:`tango.DeviceProxy` constructor
        (if you need to customize the device proxy creation).

    :return: The `TangoEventLogger` instance that is used to log
        the given events.
    """
    logger = TangoEventLogger()
    event_enum_map = EventTypeMapper(attribute_enum_map)

    def typed_msg_builder(event: ReceivedEvent) -> str:
        """Build a log message from a TypedReceivedEvent."""
        event = event_enum_map.get_typed_event(event)
        return (
            f"    EVENT_LOGGER: At {event.reception_time}, "
            f"{event.device_name} " + f"{event.attribute_name} changed to "
            f"{str(event.attribute_value)}."
        )

    for device, attr_list in device_attribute_map.items():
        for attr in attr_list:
            logger.log_events_from_device(
                device,
                attr,
                dev_factory=dev_factory,
                message_builder=typed_msg_builder,
            )

    return logger
