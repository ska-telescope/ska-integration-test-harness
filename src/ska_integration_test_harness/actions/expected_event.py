"""An event that is expected to occur after an action is executed.

This module defines the classes that represent the expected events that
should occur after a
:py:class:`tests.test_harness3.telescope_actions.telescope_action.TelescopeAction`
is executed. There are provided two classes:

- a more generic 
  :py:class:`tests.test_harness3.telescope_actions.expected_event.ExpectedEvent`
  class, that allows you to define a custom predicate to check if an event
  matches the expected conditions;
- a specific but very common case where what you want to verify is a state
  change in a Tango device attribute, represented by the
  :py:class:`tests.test_harness3.telescope_actions.expected_event.ExpectedStateChange`.
"""  # pylint: disable=line-too-long # noqa E501

from dataclasses import dataclass
from typing import Any, Callable

from ska_tango_testing.integration.event import ReceivedEvent
from tango import DeviceProxy


@dataclass
class ExpectedEvent:
    """The description of an expected Tango event.

    An event is described by:

    - a tango device (or its name),
    - an attribute (name),
    - a predicate, that evaluates the event object (of type ``ReceivedEvent``)
      and returns a boolean indicating whether the event matches the expected
      conditions.
    """

    device: DeviceProxy | str
    """The Tango device or its name you expect to change state."""

    attribute: str
    """The attribute (name) you expect to change state."""

    predicate: Callable[[ReceivedEvent], bool]
    """The predicate that defines the expected event."""

    def _device_to_str(self) -> str:
        if isinstance(self.device, DeviceProxy):
            return self.device.dev_name()
        return self.device

    def _condition_to_str(self) -> str:
        return f"that matches the custom predicate {self.predicate}"

    def __str__(self) -> str:
        return (
            f"Expected an event with device {self._device_to_str()} "
            f"and attribute {self.attribute} "
            f"{self._condition_to_str()}."
        )

    def event_matches(self, event: ReceivedEvent) -> bool:
        """Check if an event matches the expected event.

        :param event: The event to check.
        :return: True if the event matches the expected event,
            False otherwise.
        """
        return (
            event.has_device(self.device)
            and event.has_attribute(self.attribute)
            and self.predicate(event)
        )


@dataclass
class ExpectedStateChange(ExpectedEvent):
    """An expected state change in a Tango device attribute.

    This class represents a special but very common case of an expected
    event: a state change in a Tango device attribute (i.e., an event that
    contains a certain value for a certain attribute of a certain device).
    Such an event is described by:

    - a device (or its name),
    - an attribute (name),
    - an expected value.

    The predicate is automatically generated comparing the expected value
    with the value of the attribute in each event.
    """

    device: DeviceProxy | str
    """The Tango device or its name you expect to change state."""

    attribute: str
    """The attribute (name) you expect to change state."""

    expected_value: Any
    """The expected value of the attribute."""

    def __init__(
        self,
        device: DeviceProxy | str,
        attribute: str,
        expected_value: Any,
    ) -> None:
        self.expected_value = expected_value
        super().__init__(
            device=device,
            attribute=attribute,
            predicate=lambda event: event.attribute_value
            == self.expected_value,
        )

    def _condition_to_str(self) -> str:
        return (
            f"to have the value {str(self.expected_value)}"
            f" (attribute's current value: {self._read_attribute()})"
        )

    def _read_attribute(self) -> Any:
        if isinstance(self.device, DeviceProxy):
            return self.device.read_attribute(self.attribute).value
        return DeviceProxy(self.device).read_attribute(self.attribute).value
