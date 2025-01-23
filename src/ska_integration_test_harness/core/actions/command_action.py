"""Action to invoke a Tango command on a device."""

import tango

from .tracer_action import TracerAction


class TangoCommandAction(TracerAction):
    """Send a command to a Tango device and synchronise using a tracer.

    This class represents an action that sends a command to a Tango device and
    then perform a series of checks using the
    :py:class:`ska_tango_testing.integration.TangoEventTracer`.

    The command:

    - is sent to a target :class:`tango.DeviceProxy` instance;
    - can be any tango command;
    - can be sent with or without parameters;
    - may produce a result which is stored in this action instance's
      ``last_command_result`` attribute.

    The preconditions and postconditions verification are performed using the
    same mechanics as the superclass
    :py:class:`ska_integration_test_harness.core.actions.TracerAction`.
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
        super().__init__(**kwargs)

        self.target_device = target_device
        self.command_name = command_name
        self.command_args = command_args or []
        self.command_kwargs = command_kwargs or {}
        self.last_command_result = None

    def execute_procedure(self):
        """Call the command on the target device and store the result.

        Call the command on the target device with the provided arguments and
        keyword arguments. The result of the command is stored in the
        ``last_command_result`` attribute.
        """
        self.last_command_result = self.target_device.command_inout(
            self.command_name, *self.command_args, **self.command_kwargs
        )

    def description(self):
        """Describe the sent command and its arguments.

        :return: a string describing the command and its arguments.
        """
        desc = f"Execute command {self.command_name} "
        desc += f"on device {self.target_device.dev_name()} "
        if self.command_args:
            desc += f"with args {self.command_args} "
        if self.command_kwargs:
            connector = "and" if self.command_args else "with"
            desc += f"{connector} kwargs {self.command_kwargs} "

        return desc.strip() + "."
