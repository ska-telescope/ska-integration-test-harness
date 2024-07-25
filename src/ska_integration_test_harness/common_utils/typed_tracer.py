"""Extend TangoEventTracer to display event values as enums labels."""

from enum import Enum
from typing import Any

import ska_tango_testing.integration.assertions
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.integration.assertions import ANY_VALUE
from ska_tango_testing.integration.event import ReceivedEvent


class TypedReceivedEvent(ReceivedEvent):
    """Extend ReceivedEvent to display event values as enums.

    An extension of the ReceivedEvent class that has an (optional) reference
    to the event type, so that messages can use string labels instead of
    integer values.
    """

    def __init__(
        self, event: ReceivedEvent, event_enum_class: type | None = None
    ):
        """Initialise the TypedReceivedEvent with the event data.

        :param event: The event data.
        :param event_enum_class: The enum class for the event type.

        :raises ValueError: If the passed class is not an Enum.
        """
        super().__init__(event.event_data)
        self.event_enum = event_enum_class

        if self.event_enum is not None and not issubclass(
            self.event_enum, Enum
        ):
            raise ValueError("The passed class is not an Enum")

    @property
    def attribute_value(self) -> str:
        """The attribute value, eventually converted to an enum.

        :return: the attribute value, eventually converted to an enum.
        """
        attr_value = super().attribute_value
        if self.event_enum is not None:
            attr_value = self.event_enum(attr_value)
        return attr_value

    def __str__(self) -> str:
        """Return a string representation of the event.

        :return: the event as a string.
        """
        return (
            f"ReceivedEvent("
            f"device_name='{self.device_name}', "
            f"attribute_name='{self.attribute_name}', "
            f"attribute_value={str(self.attribute_value)}, "
            f"reception_time={self.reception_time})"
        )


class EventTypeMapper:
    """A class to associate attributes with their corresponding enum class."""

    def __init__(self, event_enum_map: dict[str, type] = {}) -> None:
        self._event_enum_map = {}
        for attr_name, enum_class in event_enum_map.items():
            self.associate_attribute_to_enum(attr_name, enum_class)

    def associate_attribute_to_enum(
        self, attribute_name: str, enum_class: type
    ) -> None:
        """Associate an attribute name to an enum class.

        :param attribute_name: The name of the attribute.
        :param enum_class: The enum class for the attribute.

        :raises ValueError: If the passed class is not an Enum.
        """
        if not issubclass(enum_class, Enum):
            raise ValueError("The passed class is not an Enum.")

        self._event_enum_map[attribute_name] = enum_class

    def get_typed_event(self, event: ReceivedEvent) -> ReceivedEvent:
        """Try to convert the event to a TypedReceivedEvent.

        :param event: The event to be converted.

        :return: The TypedReceivedEvent.
        """
        for attr_name, enum_class in self._event_enum_map.items():
            # check if the event has the attribute name
            # (case insensitive!)
            if event.has_attribute(attr_name):
                return TypedReceivedEvent(event, enum_class)

        return event


class TypedTangoEventTracer(TangoEventTracer):
    """Extend TangoEventTracer to display event values as enums.

    An extension of the TangoEventTracer class that allows for the
    labelling of events with their corresponding event type, so that
    messages can use string labels instead of integer values.
    """

    def __init__(self) -> None:
        super().__init__()
        self._event_enum_map = EventTypeMapper()

    def associate_attribute_to_enum(
        self, attribute_name: str, enum_class: type
    ) -> None:
        """Associate an attribute name to an enum class.

        :param attribute_name: The name of the attribute.
        :param enum_class: The enum class for the attribute.

        :raises ValueError: If the passed class is not an Enum.
        """
        self._event_enum_map.associate_attribute_to_enum(
            attribute_name, enum_class
        )

    def _add_event(self, event: ReceivedEvent) -> None:
        """Override the method to eventually use TypedReceivedEvent, if needed.

        :param event: The event to be added.
        """
        # try to convert the event to a TypedReceivedEvent
        # add the event to the list (as you would normally do)
        super()._add_event(self._event_enum_map.get_typed_event(event))


# Temporary trick to print the correct enum label in the assertion
# error too


def _print_passed_event_args(
    device_name: str | None = ANY_VALUE,
    attribute_name: str | None = ANY_VALUE,
    attribute_value: Any | None = ANY_VALUE,
    previous_value: Any | None = ANY_VALUE,
) -> str:
    """Print the arguments passed to the event query.

    Helper method to print the arguments passed to the event query in a
    human-readable format.

    :param device_name: The device name to match. If not provided, it will
        match any device name.
    :param attribute_name: The attribute name to match. If not provided,
        it will match any attribute name.
    :param attribute_value: The current value to match. If not provided,
        it will match any current value.
    :param previous_value: The previous value to match. If not provided,
        it will match any previous value.

    :return: The string representation of the passed arguments.
    """
    res = ""
    if device_name is not ANY_VALUE:
        res += f"device_name='{device_name}', "
    if attribute_name is not ANY_VALUE:
        res += f"attribute_name='{attribute_name}', "
    if attribute_value is not ANY_VALUE:
        res += f"attribute_value={str(attribute_value)}, "
    if previous_value is not ANY_VALUE:
        res += f"previous_value={previous_value}, "

    return res


# Force this function to be used in the assertion error message
# (instead of the default one)

ska_tango_testing.integration.assertions._print_passed_event_args = (
    _print_passed_event_args
)
