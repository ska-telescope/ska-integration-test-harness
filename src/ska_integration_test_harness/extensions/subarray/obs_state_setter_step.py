"""A step in the procedure of setting the subarray obs state + utilities."""

import abc

from pydantic import BaseModel
from ska_control_model import ObsState

from ska_integration_test_harness.extensions.actions.lrc_action import (
    TangoLRCAction,
)

from ...core.actions.sut_action import SUTAction
from .obs_state_commands_factory import ObsStateCommandsFactory
from .obs_state_system import ObsStateSystem


class ObsStateCommandsInput(BaseModel):
    """Input for the observation state commands.

    This class represents the input for the observation state commands
    to be used during the observation state set procedure.
    """

    AssignResources: str | None = None
    Configure: str | None = None
    Scan: str | None = None

    @staticmethod
    def get_object(
        cmd_inputs: "ObsStateCommandsInput | dict",
    ) -> "ObsStateCommandsInput":
        """Get the object from a dictionary or an object.

        :param cmd_inputs: the dictionary or object to convert
        :return: the object
        """
        if cmd_inputs is None:
            return ObsStateCommandsInput()

        if isinstance(cmd_inputs, dict):
            return ObsStateCommandsInput(**cmd_inputs)
        return cmd_inputs


class ObsStateSetterStep(abc.ABC):
    """A step in the procedure of setting the subarray obs state.

    This class represents a step in the Observation State setting procedure
    (represented instead by the class
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    ).

    Each step could be mapped to a given :py:class:`ska_control_model.ObsState`
    and could be seen as the operations to do to move from the current system
    state (the one the step is supposed to be executed in, represented
    by :py:meth:`get_step_obs_state`) to
    the target state (the one the step is supposed to move the system to).

    Steps acts as
    `Strategies <https://refactoring.guru/design-patterns/strategy>`_
    used by the
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    instances to deal with specific observation states the subarray could be
    in. We assume a 1:1 mapping between the steps and the observation states,
    but:

    - several specific steps could share common characteristics by
      inheriting from a common intermediate class
    - potentially we imagine a step could be replaced by another one

    **Extension points**

    Concretely, ``ObsStateSetterStep`` is an abstract class which main
    extension point is the :py:meth:`get_next_action`, which is supposed to
    return the next command to be executed to move in the observation state
    machine towards the target state. Essentially, this method could be seen
    as a local "routing policy", a way to decide what to do based on the
    state the system is in.

    :py:meth:`get_step_obs_state` is the second required extension point,
    which should return the observation state the system should be in to
    execute this step.

    Another optional extension point is the :py:meth:`get_accepted_obs_states`,
    which permits you to define which observation states the devices could
    be in to consider the system state "consistent" and therefore the
    step execution to be possible. This method is useful when the step
    represents a **transient state**, and so the different devices that
    compose the system could be in different specific states. Overriding
    this method you can define which are those states that are considered
    acceptable. If not implemented, :py:meth:`get_next_action` only
    will be considered an acceptable state.

    **Other utilities**

    NOTE: since the actions generated by :py:meth:`get_next_action` will
    likely be Tango subarray commands, this class provides the following
    utilities:

    - a :py:attr:`system` attribute, which is the system the step will act on
    - a :py:attr:`subarray_id` attribute, which is the subarray id the step
      will act on
    - a :py:attr:`commands_inputs` attribute, which is a collection of
      the inputs to use for commands such as ``AssignResources``,
      ``Configure`` and ``Scan``
    - a :py:attr:`commands_factory` attribute, which is a factory to create
      the commands to be executed
    - a :py:meth:`get_subarray_command_action` method, which is a utility
      to quickly create actions that are commands and decorate them
      with the right post conditions and early stop conditions

    You don't need to use these utilities while extending this class, but
    the are there for you if you need them and they can be used to standardise
    the code. In the future we could consider to move that logic somewhere
    else but for now it's here.
    """

    def __init__(
        self,
        system: ObsStateSystem,
        subarray_id: int,
        commands_inputs: ObsStateCommandsInput,
    ):
        """Initializes the step.

        :param system: The system that the step will act on.
        :param subarray_id: The subarray id the step will act on.
        :param commands_inputs: The inputs to use for commands such as
            ``AssignResources``, ``Configure`` and ``Scan``.
        """
        super().__init__()
        self.system = system
        """The system that the step will act on."""
        self.subarray_id = subarray_id
        """The subarray id the step will act on."""
        self.commands_inputs = commands_inputs
        """
        The inputs to use for commands such as ``AssignResources``,
        ``Configure`` and ``Scan.
        """

        self.commands_factory = ObsStateCommandsFactory(system)
        """The factory to create the subarray commands to be executed."""

    @abc.abstractmethod
    def get_next_action(self, target_state: ObsState) -> SUTAction:
        """Returns the next action to do to move towards the target state.

        This method is supposed to return the next action to do to move
        towards the target state. The action could be a command to be
        sent to the subarray, or actually any other action.

        NOTE: when overriding this method you can assume the non-implemented
        target states are not supported by default. If you want to not
        support other specific target states, you can raise a
        :py:class:`NotImplementedError`.

        :param target_state: The target state the system should move to.
        :return: The next action to do.

        :raises NotImplementedError: If the target state is not supported.
        """

    @abc.abstractmethod
    def get_step_obs_state(self) -> ObsState:
        """Returns the obs state this step is supporting.

        :return: The observation state the system should be in when this step
            is executed.
        """

    def get_accepted_obs_states(self) -> list[ObsState]:
        """Returns the obs states the devices could be when executing the step.

        This method is useful when the step represents a **transient state**,
        and so the different devices that compose the system could be in
        different specific states. Overriding this method you can define
        which are those states that are considered acceptable.

        By default, each step expects all devices to be in the state
        returned by :py:meth:`get_step_obs_state`.

        :return: The list of observation states the devices could be in to
            consider the system state "consistent" and therefore the step
            execution to be possible.
        """
        return [self.get_step_obs_state()]

    def get_subarray_command_action(
        self,
        subarray_id: int,
        command_name: str,
        command_input: str | None = None,
        sync_transient: bool = False,
    ) -> TangoLRCAction:
        """Creates a command action to be sent to the subarray.

        This method is a utility to quickly create a
        :py:class:`ska_integration_test_harness.extensions.actions.TangoLRCAction`
        already configured to synchronise alternatively:

        - on the next quiescent/stable state + LRC completion
        - on the next transient state (with no LRC completion)

        Moreover, the LRC action is already configured to stop early if any
        LRC error is detected.

        TODO: if I add in factory something like "does command support
        transient state?" I could here synchronise on:
        ``transient -> quiescent -> LRC completion``
        instead of just ``quiescent -> LRC completion``. Actually I don't
        know if it's desirable or not (just an idea).

        :param subarray_id: The subarray id the command is for.
        :param command_name: The name of the command to execute.
        :param command_input: The input for the command. Default is None
            (since not all commands require an input).
        :param sync_transient: Whether to synchronise on the transient state
            or on the quiescent state. Default is False.
        :return: The command action to be executed.
        """  # pylint: disable=line-too-long # noqa: E501
        command_action = self.commands_factory.create_action_with_sync(
            subarray_id,
            command_name,
            command_input,
            sync_transient,
            not sync_transient,
        )

        if not sync_transient:
            command_action.add_lrc_completion_to_postconditions()

        command_action.add_lrc_errors_to_early_stop()

        return command_action
