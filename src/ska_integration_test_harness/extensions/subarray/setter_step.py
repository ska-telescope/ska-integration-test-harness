"""A step in the procedure of setting the subarray to a target obs state."""

import abc

import tango
from ska_control_model import ObsState

from ...core.actions.sut_action import SUTAction
from ..lrc.tango_lrc_action import TangoLRCAction
from ..subarray.inputs import ObsStateCommandsInput
from .commands_factory import ObsStateCommandsFactory
from .exceptions import (
    ObsStateMissingCommandInput,
    ObsStateSystemNotConsistent,
)
from .system import DEFAULT_SUBARRAY_ID, ObsStateSystem, read_devices_obs_state


class ObsStateSetterStep(SUTAction, abc.ABC):
    """A step in the procedure of setting the subarray to a target obs state.

    This class represents a step in the Observation State setting procedure
    (represented instead by the class
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    ). A step is a
    :py:class:`ska_integration_test_harness.core.actions.SUTAction` and:

    - as a precondition it assumes the system is in a given state and that
      the given state is consistent (see :py:meth:`verify_preconditions`)
    - the executed procedure is (usually) the execution of a command, that
      is supposed to move the system in the direction of the target state
      in the observation state machine
    - the post-condition in not implemented, since it probably would be
      redundant to what done by the command executed (in some cases
      you may consider to implement it - e.g., for steps that do nothing
      except waiting for something to happen)

    Steps are supposed to be orchestrated by
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    and they are supposed to be executed in a dynamic sequence (according
    to which system states are observed, a different step could be loaded).
    At the moment, steps are supposed to be 1:1 mapped with the possible
    observation states, so the logic to decide what to do from a given
    starting state is well encapsulated in the respective step.
    This way to deal with the observation state machine is inspired by the
    `State design pattern <https://refactoring.guru/design-patterns/state>`_
    (because we have a state machine and we want to encapsulate the logic
    of each state in a separate class)
    and partially also by the
    `Strategy design pattern <https://refactoring.guru/design-patterns/strategy>`_
    (because we imagine that that the logic to decide what to do can be
    encapsulated in a separate class, and potentially replaced by another
    one injected from outside).

    **Extension points**

    Concretely, this class remains abstract because it implements
    :py:class:`~ska_integration_test_harness.core.actions.SUTAction`
    only partially:
    while :py:meth:`verify_preconditions` is implemented to check that the
    system is in a (overall) consistent state
    (see :py:meth:`get_accepted_obs_states`),
    :py:meth:`execute_procedure` remains abstract because each step
    should implement it with its own logic to make the system move one step
    in the observation state machine.

    The class leaves also abstract the method
    :py:meth:`get_assumed_obs_state`, because each step should know in which
    state the system should be to consider the step executable. The method
    :py:meth:`get_accepted_obs_states` instead has a default implementation
    that returns just the assumed state, but it can be overridden to return
    a wider range of states (useful when the state is transient/not stable).

    :py:mod:`ska_integration_test_harness.extensions.subarray.steps` contains
    the concrete implementations of the steps.

    **Other utilities**

    NOTE: since in many cases the logic to move the system in the observation
    state machine is the execution of a command, this class provides an
    important utility method called
    :py:meth:`run_subarray_command`
    that allows to send commands to the right subarray and synchronise
    on the right transient or quiescent state, dealing also with LRC
    completion and LRC errors.

    TODO: conclude. Essentially this will become the action that does
    the step while ObsStateSetter will become a coordinator. tests will
    adjust accordingly (most of the existent will be on this class, the
    remaining on the coordinator).
    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(
        self,
        system: ObsStateSystem,
        target_state: ObsState,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        commands_input: ObsStateCommandsInput | dict | None = None,
    ):
        """Initializes the step.

        :param system: The system that the step will act on.
        :param target_state: The target state the system should move to.
        :param subarray_id: The subarray id the step will act on. It defaults
            to the value of :py:const:`DEFAULT_SUBARRAY_ID`.
        :param commands_input: The inputs to use for commands such as
            ``AssignResources``, ``Configure`` and ``Scan``. It defaults to
            no inputs (None).
        """
        super().__init__()
        self.system = system
        """The system that the step will act on."""
        self.target_state = target_state
        """The target state the system should move to."""
        self.subarray_id = subarray_id
        """The subarray id the step will act on."""
        self.commands_input = ObsStateCommandsInput.get_object(commands_input)
        """
        The inputs to use for commands, such as ``AssignResources``,
        ``Configure`` and ``Scan``.
        """

        self.commands_factory = ObsStateCommandsFactory(system)
        """The factory to create the subarray commands to be executed."""

    # --------------------------------------------------------------------
    # Main extension points

    @abc.abstractmethod
    def execute_procedure(self) -> None:
        """Implement the logic to move the system one step towards the target.

        This method should implement the logic to move the system one step
        towards the target state in the observation state machine. Essentially,
        assuming you are in the state that the step is supposed to handle
        and that the system is in a consistent state (see
        :py:meth:`verify_preconditions` and:py:meth:`get_accepted_obs_states`),
        this method should implement the logic to move the system one step
        in the direction of the target state, acting as a "routing function"
        in the observation state machine.

        To implement this step you can use the utility method
        :py:meth:`run_subarray_command` to send commands to the subarray
        and synchronise on the right transient or quiescent state, dealing
        also with LRC completion and LRC errors. Alternatively, you can
        implement your own logic independently of the commands/actions.
        Whatever you choose, remember that at the end of the execution
        the system should be in a consistent state (so make sure the code
        you put here synchronises on the right states or implement
        :py:meth:`verify_postconditions` to do it; if you send commands
        through the action framework, they will automatically synchronise
        so no need to worry about it).

        See also
        :py:class:`ska_integration_test_harness.core.actions.SUTAction`
        for more details.
        """

    @abc.abstractmethod
    def get_assumed_obs_state(self) -> ObsState:
        """Returns the obs state the system should be in to execute the step.

        This method returns the observation state the system should be in
        to consider the step executable. The system should be in this state
        when the step is executed.

        :return: The observation state the system should be in to consider
            the step executable.
        """

    def get_accepted_obs_states(self) -> list[ObsState]:
        """Returns the obs states the devices could be when executing the step.

        This method returns the list of observation states the system devices
        could be in to consider the system state "consistent" and
        therefore the step to be executable safely. By default, this method
        returns a list with just the assumed state (as returned by
        :py:meth:`get_assumed_obs_state`). For quiescent/stable states
        this is enough, but for transient states you may want to
        override it and return
        also the close quiescent/stable states (since the system is
        distributed some devices could still be in the original state
        while others are already in the transient state).

        :return: The list of observation states the devices could be in to
            consider the system state "consistent" and therefore the step
            execution to be possible.
        """
        return [self.get_assumed_obs_state()]

    # --------------------------------------------------------------------
    # Action methods

    def verify_preconditions(self):
        """Verify the system is in a consistent observation state.

        The system is in a consistent observation state if all the devices
        are in an accepted observation state (as defined by the class
        through the
        :py:meth:`accepted_obs_states_for_devices` method).

        TODO: should I check also the assumed state? Is it strictly necessary?

        :raise ObsStateSystemNotConsistent: if the system is not in a
            consistent observation state
        """
        super().verify_preconditions()

        device_obs_states = read_devices_obs_state(
            self.system, self.subarray_id
        )

        for _, obs_state in device_obs_states.items():
            if obs_state not in self.get_accepted_obs_states():
                raise ObsStateSystemNotConsistent(
                    self.get_assumed_obs_state(), device_obs_states, self
                )

    def description(self) -> str:
        return (
            f"Executing a transition step to move subarray {self.subarray_id} "
            f"from {str(self.get_assumed_obs_state())} "
            f"towards {str(self.target_state)}"
        )

    # --------------------------------------------------------------------
    # Utilities

    def send_subarray_command_and_synchronise(
        self,
        command_name: str,
        sync_transient: bool = False,
    ) -> None:
        """Send a command on the subarray and synchronise on the right state.

        This method is a utility to quickly send a command to the subarray
        and synchronise on the right transient or quiescent state, dealing
        also with LRC completion and LRC errors.

        It relies to :py:meth:`create_subarray_command` to create the
        command action, then it executes it propagating the timeout
        and the parameters of the execution from this
        :py:class:`ska_integration_test_harness.core.actions.SUTAction`.

        :param command_name: The name of the command to execute.
        :param sync_transient: Whether to synchronise on the transient state
            or on the quiescent state. Default is False

        :raise ObsStateMissingCommandInput: if the input for the command
            is required but missing
        """
        command_action = self.create_subarray_command(
            command_name, sync_transient
        )
        command_action.set_logging(not self.logger.disabled)
        command_action.execute(
            self._last_execution_params["postconditions_timeout"],
            self._last_execution_params["verify_preconditions"],
            # (postconditions are always verified by the command action,
            # independently of the value of the parameter)
            True,
        )

    def create_subarray_command(
        self,
        command_name: str,
        sync_transient: bool = False,
    ) -> TangoLRCAction:
        """Creates a command action to be sent to the subarray.

        This method is a utility to quickly create a
        :py:class:`ska_integration_test_harness.extensions.lrc.TangoLRCAction`
        already configured:

        - with the correct target device (done by the factory)
        - pointed to the correct subarray ID
        - using the set input (automatically set according to the command
          name)
        - synchronising on the right transient or quiescent state

        For the synchronisation, through the parameter ``sync_transient``,
        you can choose to synchronise:

        - on the next quiescent/stable state + LRC completion
        - or on the next transient state (with no LRC completion)

        Moreover, the LRC action is already configured to stop early if any
        LRC error is detected.

        TODO: if I add in factory something like "does command support
        transient state?" I could here synchronise on:
        ``transient -> quiescent -> LRC completion``
        instead of just ``quiescent -> LRC completion``. Actually I don't
        know if it's desirable or not (just an idea).

        :param command_name: The name of the command to execute.
        :param sync_transient: Whether to synchronise on the transient state
            or on the quiescent state. Default is False.

        :return: The command action to be executed.

        :raise ObsStateMissingCommandInput: if the input for the command
            is required but missing
        """  # pylint: disable=line-too-long # noqa: E501
        # get the input from the command name from the input object
        # and raise an exception if the input is missing
        if hasattr(self.commands_input, command_name):
            if getattr(self.commands_input, command_name) is None:
                raise ObsStateMissingCommandInput(
                    command_name, self.commands_input, self
                )
            command_input = getattr(self.commands_input, command_name)
        else:
            command_input = None

        # create the action synchronising alternatively on the transient
        # or quiescent state
        command_action = self.commands_factory.create_action_with_sync(
            command_name,
            command_input,
            subarray_id=self.subarray_id,
            sync_transient=sync_transient,
            sync_quiescent=not sync_transient,
        )

        # if we synchronise on the transient state, we want also
        # to add the LRC completion to the postconditions
        if not sync_transient:
            command_action.add_lrc_completion_to_postconditions()

        # in any case, we want to monitor the LRC errors
        command_action.add_lrc_errors_to_early_stop()

        return command_action

    def _devices_obs_state(self) -> dict[tango.DeviceProxy, ObsState]:
        """Return the observation state of all the devices.

        :return: a dictionary with the devices and their observation states
        """
        return read_devices_obs_state(self.system, self.subarray_id)
