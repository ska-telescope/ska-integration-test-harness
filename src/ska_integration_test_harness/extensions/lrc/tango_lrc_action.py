"""Send a LongRunningCommand to a Tango device and synchronise."""

from typing import Any, SupportsFloat

import tango
from assertpy import assert_that
from ska_control_model import ResultCode

from ...core.actions.command_action import TangoCommandAction
from .assert_lrc_completion import AssertLRCCompletion


class TangoLRCAction(TangoCommandAction):
    """Send a LongRunningCommand to a Tango device and synchronise.

    This class represents an action that sends a LongRunningCommand to a Tango
    device and then synchronises on its successful completion (and possibly
    on its errors too). This class is an extension of
    :py:class:`ska_integration_test_harness.core.actions.TangoCommandAction`,
    which inherits the capability of sending Tango commands and synchronising
    through a set of
    :py:class:`ska_integration_test_harness.core.assertions.TracerAssertion`,
    but adds two additional features:

    - the possibility to add to postconditions a check on the completion of
      the LRC, through the method
      :py:meth:`add_lrc_completion_to_postconditions`;
    - the possibility to add to early stop a check on the errors of the LRC,
      through the method :py:meth:`add_lrc_errors_to_early_stop`.

    **Usage example**:

    .. code-block:: python

        from ska_integration_test_harness.core.actions import TangoCommandAction
        from ska_integration_test_harness.core.assertions import AssertDevicesAreInState
        from ska_integration_test_harness.core.assertions import AssertDevicesStateChanges

        # Then you can build action instances and add preconditions and
        # postconditions to them according to your needs.

        action = TangoCommandAction(
            target_device=dev1,
            command_name="IncreaseAttributeLRC",
            command_param=2,
        ).add_preconditions(
            AssertDevicesAreInState(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=42
            ),
        ).add_postconditions(
            AssertDevicesStateChanges(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=43
            ),
            AssertDevicesAreInState(
                devices=[dev1, dev2],
                attribute_name="attr1",
                attribute_value=44
            ),
        ).add_early_stop(
            lambda e: e.attribute_value < 42

        # synchronise on LRC completion (after the state changes)
        ).add_lrc_completion_to_postconditions(

        # monitor LRC errors (if any)
        ).add_lrc_errors_to_early_stop()


        # execute the action within a timeout of 5 seconds
        # (which will stop early if the LRC fails or if it detects
        # an event with an attribute value less than 42)
        action.execute(postconditions_timeout=5)

    Two additional notes:

    - :py:meth:`add_lrc_completion_to_postconditions` and
      :py:meth:`add_lrc_errors_to_early_stop` can be customised passing
      sets of result codes that you want to consider as successful or as
      errors. See the methods documentation for more information.
    - :py:meth:`add_lrc_completion_to_postconditions` can be called multiple
      times with different result codes to track different stages of the LRC
      completion.

    **What if your LRC is not exactly as expected?**

    If your code does not support LRC the way we expect, but it still does
    that in a slightly different way, you can still use this class by
    extending it and overriding it where necessary. For example, let's say:

    1. The command result code is returned in a slightly different format
    2. The event that signals the LRC completion is not emitted on
       ``longRunningCommandResult``, but on a different attribute
    3. The LRC events have a different format than the one supported by
       :py:class:`~ska_integration_test_harness.extensions.assertions.AssertLRCCompletion`

    To handle this:

    1. You override :py:meth:`get_last_lrc_id` to extract the LRC ID from
       your own command result format
    2. You subclass
       :py:class:`~ska_integration_test_harness.extensions.assertions.AssertLRCCompletion`
       and override the method
       :py:meth:`~ska_integration_test_harness.extensions.assertions.AssertLRCCompletion.match_lrc_completion`
       to match your own LRC event format.
    3. You also override the constructor of the assertion class to set your
       own expected attribute name.
    4. You override :py:meth:`_create_assert_lrc_completion_instance` to
       use your own subclass instead of the default one.

    Example:

    .. code-block:: python

        from ska_integration_test_harness.extensions.lrc import TangoLRCAction
        from ska_integration_test_harness.extensions.assertions import AssertLRCCompletion

        # 2,3. Subclass AssertLRCCompletion to match your own LRC event format
        # and set your own expected attribute name
        class MyAssertLRCCompletion(AssertLRCCompletion):

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.expected_attribute_name = "myLRCEvent"

            def match_lrc_completion(self, event: ReceivedEvent) -> bool:
                # your custom implementation here

        # 1,4. Subclass TangoLRCAction
        class MyTangoLRCAction(TangoLRCAction):

            def get_last_lrc_id(self) -> str:
                # your custom implementation here to extract the LRC ID
                return # ...

            def _create_assert_lrc_completion_instance(
                self,
                expected_result_codes: "ResultCode | list[ResultCode] | None",
            ) -> MyAssertLRCCompletion:
                return MyAssertLRCCompletion(
                    # don't forget to pass the target device
                    device=self.target_device,
                    expected_result_codes=expected_result_codes,
                )

            # Now you can use MyTangoLRCAction instead of TangoLRCAction
            my_lrc_action = MyTangoLRCAction(
                target_device=dev1,
                command_name="IncreaseAttributeLRC",
                command_param=2,
            ).add_lrc_completion_to_postconditions(
                expected_result_codes=ResultCode.OK
            ).add_lrc_errors_to_early_stop()


    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(
        self,
        target_device: tango.DeviceProxy,
        command_name: str,
        command_param: Any | None = None,
        command_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        """Create a new TangoLRCAction instance.

        :param target_device: the target device on which to execute
            the command.
        :param command_name: the name of the command to execute.
        :param command_param: the parameter to pass to the command. If not
            specified, it defaults to no parameter.
        :param command_kwargs: additional keyword arguments
            to pass to the command. See
            :py:meth:`tango.DeviceProxy.command_inout`
            for more information on the available keyword arguments.
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
            command_param=command_param,
            command_kwargs=command_kwargs,
            **kwargs,
        )
        # we use this special list to monitor which LRC errors are monitored
        # See add_lrc_errors_to_early_stop for more details
        self._early_stop_lrc_assertions: list[AssertLRCCompletion] = []

    def add_lrc_completion_to_postconditions(
        self,
        expected_result_codes: (
            "ResultCode | list[ResultCode] | None"
        ) = ResultCode.OK,
        put_at_beginning: bool = False,
    ) -> "TangoLRCAction":
        """Add a postcondition to verify the completion of the LRC.

        Call this method to append to postconditions a
        an assertion to check the LRC completes with some
        :py:class:`ska_control_model.ResultCode`. This is done through an
        :py:class:`~ska_integration_test_harness.extensions.assertions.AssertLRCCompletion`
        instance, which assert over events on the ``longRunningCommandResult``
        attribute of the target device.
        The LRC ID will be extracted from the last command execution
        result and this class will automatically be configured in
        all the assertions of this type you add to the action.

        NOTE: to accept multiple result codes as successful, you can pass
        a list of them when calling this method. If you instead want to
        track a whole sequence of LRC events with different result codes,
        you can call this method multiple times.

        :param expected_result_code: the expected result code of the LRC.
            You can:

            - leave it to the default value (``ResultCode.OK``) to accept
              only the OK result code;
            - set it to ``None`` to accept any result code;
            - set it to one or more result codes to accept multiple result
              codes (by passing a single ``ResultCode`` or a list of them).

        :param put_at_beginning: if True, you will verify the LRC completion
            before the other postconditions you configured.
            By default, it is added at the end.
        :return: the action itself, to allow chaining the calls.
        """  # pylint: disable=line-too-long # noqa: E501
        return self.add_postconditions(
            self._create_assert_lrc_completion_instance(
                expected_result_codes=expected_result_codes
            ),
            put_them_at_beginning=put_at_beginning,
        )

    def add_lrc_errors_to_early_stop(
        self,
        error_result_codes: "list[ResultCode] | None" = None,
    ) -> "TangoLRCAction":
        """Add an early stop condition to stop early if the LRC fails.

        Call this method to add an early stop condition to stop the action
        early if some kind of LRC :py:class:`ska_control_model.ResultCode`
        is detected among events. This method will build an early stop
        predicate that will applied in all the existing an future
        postconditions. The LRC ID will be extracted from the last command
        execution result and this class will automatically be configured in
        all the early stop assertions of this type you add to the action.

        :param error_result_codes: the result codes to consider as errors.
            By default, the following result codes are considered as errors:

            .. code-block:: python

                [ResultCode.FAILED, ResultCode.REJECTED, ResultCode.NOT_ALLOWED]

            You can override this default by passing a result code or a list
            of them that you want to consider as errors.

            - ``ResultCode.FAILED``
            - ``ResultCode.REJECTED``
            - ``ResultCode.NOT_ALLOWED``
        """  # pylint: disable=line-too-long # noqa: E501
        # set the default error result codes
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
        lrc_error_assertion = self._create_assert_lrc_completion_instance(
            expected_result_codes=error_result_codes
        )
        # ensure the same tracer is used
        lrc_error_assertion.tracer = self.tracer

        self._early_stop_lrc_assertions.append(lrc_error_assertion)

        return self.add_early_stop(
            lrc_error_assertion.match_lrc_completion,
        )

    def setup(self):
        """Subscribe to all the necessary events, including the LRC event.

        See
        :py:meth:`ska_integration_test_harness.core.actions.TracerAction.setup`
        for more information.
        """
        super().setup()

        # NOTE: be sure to subscribe to the LRC event
        for lrc_error_assertion in self._early_stop_lrc_assertions:
            lrc_error_assertion.setup()

    def verify_postconditions(self, timeout: SupportsFloat = 0) -> None:
        """Verify the postconditions of the action.

        But before, ensure all the LRC assertions are configured with
        the LRC ID from the last command result.

        See
        :py:meth:`ska_integration_test_harness.core.actions.TracerAction.verify_postconditions`
        for more information.

        :param timeout: the time in seconds to wait for the postconditions to
            be verified. If not specified, it defaults to 0. Potentially,
            it can be:

            - a number, specifying the timeout in seconds,
            - a :py:class:`~ska_tango_testing.integration.assertions.ChainedAssertionsTimeout`
              object, potentially shared among multiple actions.

        :raises AssertionError: if one of the postconditions fails.
        """  # pylint: disable=line-too-long # noqa: E501

        last_lrc_id = self.get_last_lrc_id()

        # Point out the LRC ID to monitor in the early stop assertions
        for lrc_error_assertion in self._early_stop_lrc_assertions:
            lrc_error_assertion.monitor_lrc(last_lrc_id)

        # Point out the LRC ID to monitor in the postconditions
        for postcondition in self.postconditions:
            if isinstance(postcondition, AssertLRCCompletion):
                postcondition.monitor_lrc(last_lrc_id)

        return super().verify_postconditions(timeout=timeout)

    def get_last_lrc_id(self) -> str:
        """Extract the LRC ID from the last command result.

        Or fail if the last command result is not as expected.

        :return: the LRC ID from the last command result.
        :raises AssertionError: if the last command result is not as expected.
        """
        assert_that(self.last_command_result).described_as(
            "The last command result is expected to be a iterable of at least "
            "two elements"
        ).is_length(2)

        assert_that(self.last_command_result[1]).described_as(
            "The second element of the last command result is expected to be "
            "a list of at least one element"
        ).is_instance_of(list).is_not_empty()

        assert_that(self.last_command_result[1][0]).described_as(
            "The first element of the second element of the last "
            "command result is expected to be a string (the LRC ID)"
        ).is_instance_of(str)

        return self.last_command_result[1][0]

    def _create_assert_lrc_completion_instance(
        self,
        expected_result_codes: "ResultCode | list[ResultCode] | None",
    ) -> AssertLRCCompletion:
        """Create an instance of AssertLRCCompletion.

        This method is meant to be overridden by subclasses to create
        a custom instance of AssertLRCCompletion, in case the default
        implementation does not fit the needs.

        :param expected_result_codes: the expected result code of the LRC.
            You can:

            - leave it to the default value (``ResultCode.OK``) to accept
              only the OK result code;
            - set it to ``None`` to accept any result code;
            - set it to one or more result codes to accept multiple result
              codes (by passing a single ``ResultCode`` or a list of them).
        :return: an instance of AssertLRCCompletion.
        """
        return AssertLRCCompletion(
            device=self.target_device,
            expected_result_codes=expected_result_codes,
        )

    # -------------------------------------------------------------------
    # (Override the building method from the superclass to specify
    # that the returned self is of the subclass type)

    def add_preconditions(
        self, *preconditions, put_them_at_beginning=False
    ) -> "TangoLRCAction":
        super().add_preconditions(
            *preconditions, put_them_at_beginning=put_them_at_beginning
        )
        return self

    def add_postconditions(
        self, *postconditions, put_them_at_beginning=False
    ) -> "TangoLRCAction":
        super().add_postconditions(
            *postconditions, put_them_at_beginning=put_them_at_beginning
        )
        return self

    def add_early_stop(self, early_stop) -> "TangoLRCAction":
        super().add_early_stop(early_stop)
        return self
