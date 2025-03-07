"""Create a mocked ``TangoEventTracer`` and populate it with events."""

import time
from threading import Thread
from unittest.mock import MagicMock

from ska_tango_testing.integration import TangoEventTracer

from tests.actions.utils.mock_received_event import create_received_event_mock


def create_mock_event_tracer() -> MagicMock:
    """
    Create a mock TangoEventTracer instance.

    :return: A MagicMock instance of TangoEventTracer, with no events.
    """
    tracer = MagicMock(spec=TangoEventTracer)
    tracer.events = []
    return tracer


def add_event(
    event_tracer: MagicMock | TangoEventTracer,
    device: str,
    attribute: str,
    value: int,
) -> MagicMock:
    """
    Add an event to the event tracer.

    :param event_tracer: The event tracer.
    :param device: The device name.
    :param attribute: The attribute name.
    :param value: The attribute value.
    """
    event_mock = create_received_event_mock(device, attribute, value)
    if isinstance(event_tracer, MagicMock):
        event_tracer.events.append(event_mock)
    elif isinstance(event_tracer, TangoEventTracer):
        event_tracer._add_event(event_mock)  # pylint: disable=protected-access
    else:
        raise TypeError(
            "ERROR IN TEST SETUP: when adding an event to the event tracer, "
            "the given tracer must be a MagicMock or a TangoEventTracer"
        )

    return event_mock


def delayed_add_event(
    event_tracer: MagicMock,
    device: str,
    attribute: str,
    value: int,
    delay: float,
) -> None:
    """
    Add an event to the event tracer after a delay.

    :param event_tracer: The event tracer.
    :param device: The device name.
    :param attribute: The attribute name.
    :param value: The attribute value.
    :param delay: The delay in seconds.
    """

    def _add_event():
        time.sleep(delay)
        add_event(event_tracer, device, attribute, value)

    Thread(target=_add_event).start()
