"""Action to invoke a Tango command on a device."""

from typing import Any

import tango

from .tracer_action import TracerAction


class TangoCommandAction(TracerAction):
    """Send a command to a Tango device and synchronise using a tracer.

    This class represents an action that sends a command to a Tango device and
    then performs a series of checks using the
    :py:class:`ska_tango_testing.integration.TangoEventTracer`.

    The command:

    - is sent to a target :class:`tango.DeviceProxy` instance;
    - can be any Tango command;
    - can be sent with or without parameters;
    - may produce a result which is stored in this action instance's
      ``last_command_result`` attribute.

    The preconditions and postconditions verification are performed using the
    same mechanics as the superclass
    :py:class:`ska_integration_test_harness.core.actions.TracerAction`.
    Contrary to the superclass, this action does not need to be extended
    and is ready to be used as it is.

    **Usage example**:

    .. code-block:: python

        from ska_integration_test_harness.core.actions import TangoCommandAction
        from ska_integration_test_harness.core.assertions import AssertDevicesAreInState
        from ska_integration_test_harness.core.assertions import AssertDevicesStateChanges

        # Then you can build action instances and add preconditions and
        # postconditions to them according to your needs.

        action = TangoCommandAction(
            target_device=dev1,
            command_name="IncreaseAttribute",
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
        )

        # execute the action within a timeout of 5 seconds
        action.execute(postconditions_timeout=5)

    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(
        self,
        target_device: tango.DeviceProxy,
        command_name: str,
        command_param: Any | None = None,
        command_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Create a new TangoCommandAction instance.

        :param target_device: the target device on which to execute
            the command.
        :param command_name: the name of the command to execute.
        :param command_param: the parameter to pass to the command. If not
            specified, it defaults to no parameter.
        :param command_kwargs: additional keyword arguments
            to pass to the command. See
            :py:meth:`tango.DeviceProxy.command_inout`
            for more information on the available keyword arguments.
        """
        super().__init__()

        self.target_device = target_device
        """The target device on which to execute the command."""

        self.command_name = command_name
        """The name of the command to execute."""

        self.command_param = command_param
        """The parameter to pass to the command."""

        self.command_kwargs = command_kwargs or {}
        """Additional keyword arguments.

        (they will be passed to :py:meth:`tango.DeviceProxy.command_inout`)
        """

        self.last_command_result = None
        """The result of the last command execution.

        It is set to None until the command is executed.
        """

    def execute_procedure(self):
        """Call the command on the target device and store the result.

        Call the command on the target device with the provided arguments and
        keyword arguments. The result of the command is stored in the
        ``last_command_result`` attribute.
        """
        self.last_command_result = self.target_device.command_inout(
            self.command_name,
            cmd_param=self.command_param,
            **self.command_kwargs,
        )

    def name(self):
        """Return the name of the action.

        :return: the name of the action.
        """
        return (
            self.__class__.__name__
            + f"(target_device={self.target_device.dev_name()}"
            f", command_name={self.command_name})"
        )

    def description(self):
        """Describe the sent command and its arguments.

        :return: a string describing the command and its arguments.
        """
        desc = f"Execute command {self.command_name}"
        desc += f" on device {self.target_device.dev_name()}"
        if self.command_param:
            desc += f" with param {self.command_param}"
        if self.command_kwargs:
            connector = "and" if self.command_param else "with"
            desc += f" {connector} kwargs {self.command_kwargs}"

        return desc + "."
