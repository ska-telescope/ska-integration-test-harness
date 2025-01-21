"""Verify there are recorded state changes for the given devices."""

from typing import Any, Callable

import tango
from ska_tango_testing.integration.event import ReceivedEvent

from .tracer_assertion import TracerAssertion


class AssertDevicesStateChanges(TracerAssertion):
    """Verify there are recorded state changes for the given devices.

    This assertion verifies that the given devices have recorded state changes
    in the TangoEventTracer within a given timeout and without early stop
    events.

    The state change events could be defined by the following parameters
    (all optional and combinable):

    - by a certain value
    - by a certain previous value
    - by a custom matcher

    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        devices: list[tango.DeviceProxy],
        attribute_name: str,
        attribute_value: Any | None = None,
        previous_value: Any | None = None,
        custom_matcher: Callable[[ReceivedEvent], bool] | None = None,
        **kwargs,
    ) -> None:
        """Create a new AssertDevicesStateChanges instance.

        :param devices: the list of devices to verify.
        :param attribute_name: the name of the attribute to assert.
        :param attribute_value: the value of the attribute to assert.
            If omitted, any value is accepted.
        :param previous_value: the previous value of the attribute to assert.
            If omitted, previous value is not checked.
        :param custom_matcher: a custom matcher to use for the assertion.
            If omitted, no further custom check is performed.
        :param kwargs: additional keyword arguments to pass to the superclass.
            (see :py:class:`TracerAssertion`)
        """
        super().__init__(**kwargs)
        self.devices = devices
        self.attribute_name = attribute_name
        self.attribute_value = attribute_value
        self.previous_value = previous_value
        self.custom_matcher = custom_matcher

    def setup(self) -> None:
        """Subscribe to the state change events of the devices."""
        super().setup()

        for device in self.devices:
            self.tracer.subscribe_event(device, self.attribute_name)

    def verify(self) -> None:
        """Verify the devices have recorded state changes.

        Verify that the devices have recorded state changes in the
        TangoEventTracer within the given timeout and without early stop
        events. The events should be related to the attribute specified
        in the constructor and, accordingly to the specified parameters:

        - have a certain value (if specified)
        - have a certain previous value (if specified)
        - match a custom matcher (if specified)

        :raises AssertionError: if the timeout is reached before the
            expected events are recorded or if the events are not as
            expected or if some early fa
        """
        super().verify()

        # take the existing assertpy context
        context = self.get_assertpy_context()

        # foreach device, chain to the context an event check
        for device in self.devices:
            context.has_change_event_occurred(
                device_name=device.dev_name(),
                attribute_name=self.attribute_name,
                attribute_value=self.attribute_value,
                previous_value=self.previous_value,
                custom_matcher=self.custom_matcher,
            )

    def describe_assumption(self) -> str:
        """Describe the assumption of the assertion.

        This assertion verifies that the devices
        ``{devices}`` have recorded state changes
        for the attribute ``{attribute_name}``.

        If you extend this class, please check
        :py:meth:`SUTAssertion.describe_assumption`
        to see how to extend it properly.

        :return: the description of the assumption
        """
        desc = ", ".join(device.dev_name() for device in self.devices)
        desc += " have recorded state changes "
        desc += f"in the attribute {self.attribute_name} "

        if self.previous_value is not None:
            desc += f"from {self.previous_value} "
        if self.attribute_value is not None:
            desc += f"to {self.attribute_value} "
        if self.custom_matcher is not None:
            desc += f"matching {self.custom_matcher.__name__} "
        if self.timeout.initial_timeout > 0:
            desc += f"within {self._timeout.initial_timeout} seconds "
            desc += f"(remaining {self._timeout.get_remaining_timeout()}) "

        if self.early_stop:
            desc += f"using early stop sentinel {self.early_stop} "

        return desc.strip() + "."
