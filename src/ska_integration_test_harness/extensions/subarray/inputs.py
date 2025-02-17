"""Input class for the observation state commands."""

from pydantic import BaseModel


class ObsStateCommandsInput(BaseModel):
    """Input class for the observation state commands.

    This class represents the input for the observation state commands
    to be used during the observation state set procedure. At the moment, it
    includes the inputs for the commands:

    - ``AssignResources``
    - ``Configure``
    - ``Scan``

    All of them are optionally settable, so you can set only the ones you
    think you need.

    This class is a :py:mod:`pydantic.BaseModel`. Usually, where we ask
    for an input of this type, you can pass a dictionary with the same
    keys as the attributes of this class and classes will convert it
    to the right object automatically.
    """

    AssignResources: str | None = None
    """Input for the ``AssignResources`` command."""

    Configure: str | None = None
    """Input for the ``Configure`` command."""

    Scan: str | None = None
    """Input for the ``Scan`` command."""

    @staticmethod
    def get_object(
        cmd_inputs: "ObsStateCommandsInput | dict | None",
    ) -> "ObsStateCommandsInput":
        """Get the object from a dictionary or an object (or from None).

        :param cmd_inputs: the dictionary or object to convert
        :return: the object
        """
        if cmd_inputs is None:
            return ObsStateCommandsInput()

        if isinstance(cmd_inputs, dict):
            return ObsStateCommandsInput(**cmd_inputs)

        return cmd_inputs
