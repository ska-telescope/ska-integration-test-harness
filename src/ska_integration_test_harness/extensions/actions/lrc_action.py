"""Send a LongRunningCommand to a Tango device and synchronise."""

import tango
from assertpy import assert_that
from ska_control_model import ResultCode

from ...core.actions.command_action import TangoCommandAction
from ..assertions.lrc_completion import AssertLRCCompletion


class TangoLRCAction(TangoCommandAction):
    """Send a LongRunningCommand to a Tango device and synchronise.

    This action is an extension of
    :py:class:`ska_integration_test_harness.core.actions.TangoCommandAction`
    that is specifically designed to send and synchronise a
    SKA LongRunningCommand to a Tango device.

    This action can be used exactly as the superclass, with the only difference
    that (optionally) you have two additional methods

    - :py:meth:`add_lrc_completion_to_postconditions`, which will verify the
      completion of the LRC;
    - :py:meth:`add_lrc_errors_to_early_stop`, which will monitor the
      LRC for errors and stop the test if any are detected.

    The preconditions and postconditions verification are performed using the
    same mechanics as the superclass (with the only exception of the two
    additional checks).
    """

    def __init__(
        self,
        target_device: tango.DeviceProxy,
        command_name: str,
        command_args: list | None = None,
        command_kwargs: dict | None = None,
        **kwargs,
    ) -> None:
        """Create a new TangoCommandAction instance.

        :param target_device: the target device on which to execute
            the command.
        :param command_name: the name of the command to execute.
        :param command_args: the positional arguments to pass to the command.
        :param command_kwargs: the keyword arguments to pass to the command.
        :param kwargs: additional keyword arguments to pass to the superclass.
            See
            :py:class:`ska_integration_test_harness.core.actions.TracerAction`
            and
            :py:class:`ska_integration_test_harness.core.actions.SUTAction`
            for more information on the available keyword arguments.
        """
        super().__init__(
            target_device=target_device,
            command_name=command_name,
            command_args=command_args,
            command_kwargs=command_kwargs,
            **kwargs,
        )
        # we use this special list to monitor which LRC errors are monitored
        # See add_lrc_errors_to_early_stop for more details
        self._early_stop_lrc_assertions: list[AssertLRCCompletion] = []

    def add_lrc_completion_to_postconditions(
        self,
        expected_result_codes: (
            ResultCode | list[ResultCode] | None
        ) = ResultCode.OK,
        put_at_beginning: bool = False,
    ) -> "TangoLRCAction":
        """Add a postcondition to verify the completion of the LRC.

        :param expected_result_code: the expected result code of the LRC. If
            you set it to None, any result code is accepted. You can also
            pass a list of result codes to accept multiple result codes. By
            default, it accepts only the OK result code.
        :param put_at_beginning: if True, the postcondition is added at the
            beginning of the postconditions list. By default, it is added at
            the end.
        """
        return self.add_postconditions(
            AssertLRCCompletion(
                device=self.target_device,
                expected_result_codes=expected_result_codes,
            ),
            put_them_at_beginning=put_at_beginning,
        )

    def add_lrc_errors_to_early_stop(
        self,
        error_result_codes: list[ResultCode] | None = None,
    ) -> "TangoLRCAction":
        """Add a postcondition to verify the completion of the LRC.

        :param error_result_codes: the error result codes of the LRC. By
            default, the error result codes are:

            - ``ResultCode.FAILED``
            - ``ResultCode.REJECTED``
            - ``ResultCode.NOT_ALLOWED``

            TODO: which other error codes may represent a failure?
        """
        if error_result_codes is None:
            error_result_codes = [
                ResultCode.FAILED,
                ResultCode.REJECTED,
                ResultCode.NOT_ALLOWED,
            ]

        # NOTE: we create an instance of the assertion to monitor the LRC
        # completion, but in a negative way. We will never run verify on it,
        # but:
        # - in setup we use it to ensure we are subscribed to the LRC event
        # - in execute_procedure we use it to say which LRC to monitor
        # - here we use it's method match_lrc_completion as a predicate
        #   for the early stop
        lrc_error_assertion = AssertLRCCompletion(
            device=self.target_device,
            expected_result_codes=error_result_codes,
            tracer=self.tracer,
        )
        self._early_stop_lrc_assertions.append(lrc_error_assertion)

        return self.add_early_stop(
            lrc_error_assertion.match_lrc_completion,
        )

    def setup(self):
        """Subscribe to all the necessary events, including the LRC event."""
        super().setup()

        # NOTE: be sure to subscribe to the LRC event
        if len(self._early_stop_lrc_assertions) > 0:
            self._early_stop_lrc_assertions[0].setup()

    def verify_postconditions(self):
        """Verify the postconditions of the action.

        But before, ensure all the LRC assertions are configured with
        the LRC ID from the last command result.
        """

        last_lrc_id = self.get_last_lrc_id()

        # Point out the LRC ID to monitor in the early stop assertions
        for lrc_error_assertion in self._early_stop_lrc_assertions:
            lrc_error_assertion.monitor_lrc(last_lrc_id)

        # Point out the LRC ID to monitor in the postconditions
        for postcondition in self.postconditions:
            if isinstance(postcondition, AssertLRCCompletion):
                postcondition.monitor_lrc(last_lrc_id)

        return super().verify_postconditions()

    def get_last_lrc_id(self) -> str:
        """Extract the LRC ID from the last command result.

        Or fail if the last command result is not as expected.

        :return: the LRC ID from the last command result.
        :raises AssertionError: if the last command result is not as expected.
        """
        assert_that(self.last_command_result).described_as(
            "The last command result is expected to be a tuple"
        ).is_instance_of(tuple).described_as(
            "The last command result is expected to have at least two elements"
        ).is_length(
            2
        )

        assert_that(self.last_command_result[1]).described_as(
            "The second element of the last command result is expected to be "
            "a list of at least one element"
        ).is_instance_of(list).is_not_empty()

        assert_that(self.last_command_result[1][0]).described_as(
            "The first element of the second element of the last "
            "command result is expected to be a string (the LRC ID)"
        ).is_instance_of(str)

        return self.last_command_result[1][0]

    # -------------------------------------------------------------------
    # (Override the building method from the superclass to specify
    # that the returned self is of the subclass type)

    # TODO: maybe do this, to facilitate the chaining also
