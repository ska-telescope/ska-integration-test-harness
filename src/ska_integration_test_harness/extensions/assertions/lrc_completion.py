"""Assert that the LongRunningCommand has completed successfully."""

import json

import tango
from ska_control_model import ResultCode
from ska_tango_testing.integration.event import ReceivedEvent

from ...core.assertions.tracer_assertion import TracerAssertion


class AssertLRCCompletion(TracerAssertion):
    """Assert that the LongRunningCommand has completed successfully.

    This assertion is an extension of
    :py:class:`~ska_integration_test_harness.core.assertions.TracerAssertion`
    that is specifically designed to verify the completion of a
    LongRunningCommand.

    The usage is very similar to the superclass, with the only difference that
    there is a further method called :py:meth:`monitor_lrc` which will permit
    you to set the LRC to monitor. This is necessary because probably
    when you create the assertion instance, the LRC ID is not yet available.

    In creation phase, you should specify target device and the expected
    result code(s). Then, when the LRC ID is available, you can call
    :py:meth:`monitor_lrc` to set the LRC to monitor. If you don't do that,
    the assertion will fail because it doesn't know which LRC to monitor.

    NOTE: if for some reason your own device emits LRC in different formats,
    you can extend this class and override the :py:meth:`match_lrc_completion`
    method to implement your own custom matcher.
    """

    def __init__(
        self,
        device: tango.DeviceProxy,
        expected_result_codes: (
            "ResultCode | list[ResultCode] | None"
        ) = ResultCode.OK,
        **kwargs,
    ):
        """Create a new AssertLRCCompletion instance.

        :param device: the target device to verify.
        :param expected_result_code: the expected result code of the LRC. If
            you set it to None, any result code is accepted. You can also
            pass a list of result codes to accept multiple result codes. By
            default, it accepts only the OK result code.
        :param kwargs: additional keyword arguments to pass to the superclass.
            (see :py:class:`TracerAssertion`)
        """
        super().__init__(**kwargs)
        self.device = device

        if expected_result_codes is None:
            # all result codes are accepted
            self.expected_result_codes = list(ResultCode)
        elif isinstance(expected_result_codes, ResultCode):
            # the given result code is accepted
            self.expected_result_codes = [expected_result_codes]
        else:
            # the given list of result codes is accepted
            self.expected_result_codes = expected_result_codes

        # the LRC ID to monitor, we don't know it yet
        self.lrc_id: str | None = None

    def setup(self):
        """Subscribe to the LRC completion event."""
        super().setup()

        self.tracer.subscribe_event(self.device, "longRunningCommandResult")

    def monitor_lrc(self, lrc_id: str) -> "AssertLRCCompletion":
        """Set the LRC to monitor.

        NOTE: this method supports the chaining.

        :param lrc_id: the LRC ID to monitor.
        :return: this instance for chaining.
        """
        self.lrc_id = lrc_id
        return self

    def verify(self):
        """Verify the LRC completes and has the expected result code.

        Verify that the LRC has completed and the result code is among the
        expected ones.

        :raises AssertionError: if the LRC ID is not set or if the LRC
        """
        super().verify()

        if self.lrc_id is None:
            raise ValueError("No LRC ID to monitor")

        self.get_assertpy_context().has_change_event_occurred(
            device_name=self.device,
            attribute_name="longRunningCommandResult",
            custom_matcher=self.match_lrc_completion,
        )

    def match_lrc_completion(self, event: ReceivedEvent) -> bool:
        """Check if an event is a LRC completion event (with expected result).

        This method is a custom matcher that will be used by the assertion to
        check if an event is a LRC completion event and, if given, check also
        if the result code is the expected one.

        Expected attribute value format:

        .. code-block:: python

            (lrc_id, '[RESULT_CODE, "result message"]')

        :param event: the event to check.
        :return: True if the event is a LRC completion event with the expected
            result code, False otherwise.
        """
        # (for safety if this method is used as standalone matcher)
        # check the LRC ID is set
        if self.lrc_id is None:
            raise ValueError("No LRC ID to monitor")

        # (for safety if this method is used as standalone matcher)
        # check again device and attribute
        if not event.has_device(self.device) or not event.has_attribute(
            "longRunningCommandResult"
        ):
            return False

        # an attribute change event value is a 2 elements tuple
        if (
            not isinstance(event.attribute_value, tuple)
            or len(event.attribute_value) != 2
        ):
            return False

        # check if the LRC ID is the one we are monitoring
        lrc_id, result_message = event.attribute_value
        if lrc_id != self.lrc_id:
            return False

        # the result message is JSON encoded
        try:
            result = json.loads(result_message)
        except json.JSONDecodeError:
            return False

        # the result is a list, first position should exist
        # and be the result code
        if (
            not isinstance(result, list)
            or len(result) < 1
            or not isinstance(result[0], int)
        ):
            return False

        # check if the result code is the expected one
        return result[0] in [
            result_code.value for result_code in self.expected_result_codes
        ]

    def describe_assumption(self):
        desc = f"{self.device.dev_name()} has recorded a "
        desc += "longRunningCommandResult completion event "

        if self.lrc_id is not None:
            desc += f"for LRC with ID {self.lrc_id} "
        else:
            desc += "(LRC ID not yet set) "

        if self.expected_result_codes:
            desc += "expecting result code(s) "
            desc += ", ".join(
                result_code.name for result_code in self.expected_result_codes
            )
        else:
            desc += "expecting any result code"

        return desc + "."
