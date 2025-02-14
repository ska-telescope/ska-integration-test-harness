"""Tools to put the system in a desired observation state."""

import abc
from typing import SupportsFloat

from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.setter_steps_imp import (
    ObsStateSetterStepFromAborted,
    ObsStateSetterStepFromAborting,
    ObsStateSetterStepFromConfiguring,
    ObsStateSetterStepFromEmpty,
    ObsStateSetterStepFromFault,
    ObsStateSetterStepFromIdle,
    ObsStateSetterStepFromReady,
    ObsStateSetterStepFromResetting,
    ObsStateSetterStepFromResourcing,
    ObsStateSetterStepFromRestarting,
    ObsStateSetterStepFromScanning,
)

from ...core.actions.sut_action import SUTAction
from .setter_step import ObsStateCommandsInput, ObsStateSetterStep
from .system import DEFAULT_SUBARRAY_ID, ObsStateSystem, read_obs_state

STATE_CLASS_MAP: dict[ObsState, type] = {}
"""Map ``ObsState`` to the classes that support them as starting states.

This class maps the observation states to the classes that support them
as starting states to move towards another observation state. The map
is filled after all the classes are defined, but you can
extend/override it if you need to.
"""

NOT_REACHABLE_STATES = [
    ObsState.FAULT,
    ObsState.RESETTING,
]
"""List of observation states that are not reachable by the system.

You can override this if your subclasses somehow support these states.
"""


class ObsStateDidNotReachTargetState(AssertionError):
    """Exception for when the system did not reach the target state.

    Exception to raise when the system did not reach the target state
    after a
    :py:class:`ska_integration_test_harness.extensions.subarray.ObsStateSetter`
    action is executed. It specifically is raised when a system main device
    ``obsState`` attribute value is not equal to the expected target state.
    """

    def __init__(
        self,
        expected_state: ObsState,
        actual_state: ObsState,
        system: ObsStateSystem,
        action: SUTAction,
    ):
        # self.expected_state = expected_state
        # self.actual_state = actual_state
        # self.devices_states =
        # self.action = action

        # msg = (
        #     f"Failed postcondition in "
        #     f"{action.name()} - {action.description()}:\n"
        #     "The system (represented by "
        #     f"{system.get_main_obs_state_device().dev_name()}) "
        #     "after the action completion is supposed to be in the "
        #     f"target observation state {str(expected_state)}, "
        #     f"but it is in the observation state {str(actual_state)}.\n"
        #     "Devices state: "
        # )

        # msg += "\n".join(
        #     f"{dev.dev_name()}: {str(state)}"
        #     for dev, state in devices_states.items()
        # )

        # super().__init__(msg)
        pass


# -------------------------------------------------------------------
# Base class for observation state setters


class ObsStateSetter(SUTAction, abc.ABC):
    """Tool to put the system in a desired observation state.

    This class is a tool to put an observation state-based system
    (:py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSystem`)
    in a desired target :py:class:`~ska_control_model.ObsState` starting
    from (almost) any observation state. The general idea is to pilot
    the system through the observation state machine
    (**as defined in ADR-8**) to reach the desired target observation state
    through a sequence of steps.

    As an end used, you can use this class like a normal
    :py:class:`~ska_integration_test_harness.core.actions.SUTAction`. Through
    the parameters you will specify:

    - the system you want to put in the desired observation state
    - the desired target observation state
    - the subarray ID you are working with
    - the input for eventual commands that will be executed to move the system
      from the current observation state to the target observation state
      (**NOTE**: this is fully optional, you can leave it as None and you can
      also specify only some input if you think you don't need to execute
      some commands, but consider that the execution will raise a
      :py:exc:ska_integration_test_harness.extensions.subarray.ObsStateMissingCommandInput`
      exception if a command should be sent and the input is missing)

    When you execute the action, the timeout you specify will be shared
    by all the steps and so by all the commands and synchronisations that
    will done to move the system towards the target observation state.

    Here an example of how you can use this class:

    .. code-block:: python

        from ska_integration_test_harness.extensions.subarray import (
            ObsStateSetter
        )

        # (please see the ObsStateSystem protocol)

        system = YourOwnObsStateSystem()

        # create a setter action to move the system from the current
        # observation state to the SCANNING state
        setter = ObsStateSetter(
            system,
            ObsState.SCANNING,
            subarray_id=1, # (optional, if omitted it will be 1)
            commands_input={
                "AssignResources": <...>,
                "Configure": <...>,
                "Scan": <...>,
            }, # (this time the input are likely to be needed)
        )

        setter.execute(100) # (100 seconds timeout)

    **Default Algorithm**

    TODO: describe intuitively the default algorithm

    **Internal Structure**

    The steps are represented by
    :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`
    subclasses and each of them is responsible to move the system from
    a certain starting observation state to the next one (till the target
    observation state is reached). Concretely, most of the steps just
    send a command to the system (according to the direction where
    the target observation state is) and then synchronise on the
    appropriate quiescent or transient state the command should reach.
    You can find a documentation of the existing steps in the
    :py:mod:`ska_integration_test_harness.extensions.subarray.setter_steps_impl`
    module.

    The step mechanism is designed to be easily extensible and overrideable.
    This class holds internally a map of observation states to the steps
    that will deal with them (the :py:attr:`obs_states_steps_map` attribute).
    You can override the steps with the
    :py:meth:`override_step` method, that allows you to replace the
    default step with a new one, automatically filled with all the necessary
    information. By default, after the construction, the map is filled
    with the default steps defined in :py:meth:`configure_default_steps`.

    The mechanism is inspired by the
    `State design pattern <https://refactoring.guru/design-patterns/state>`_
    (because we have a state machine and we want to encapsulate the logic
    of each state in a separate class)
    and also by the
    `Strategy design pattern <https://refactoring.guru/design-patterns/strategy>`_
    (because we imagine that that the logic to decide what to do can be
    encapsulated in a separate class, and potentially replaced by another
    one injected from outside).

    **Current Limitations and Workarounds**

    TODO: describe the current limitations and the workarounds better

    This class and
    the whole structure is a first implementation of a tool to manage the
    the observation state transitions. However, it still have weaknesses
    and limitations. For example:

    - The routing rules are quite simple and sometimes you make useless
      aborts and restarts (sometimes this may be necessary, but sometimes
      it is just a waste of time; I opted for the simplicity and for
      the solution that is more likely to work in most cases).
      **CURRENT WORKAROUND**: you can override the routing rules
      (the :py:meth:`next_command` method) to implement more complex
      routing rules
    - The consistency checks are quite simple and sometimes you may want
      something more strict and also the fact that the consistency is verified
      as precondition does not exclude the possibility of inconsistencies
      at the time a command is sent. Also, it may happen sometime that
      you are in a transient state and when you send a command you are
      already in the quiescent state. **CURRENT WORKAROUND**:
      To some extent, those
      limitations cannot really be solved because they are inherent
      to the distributed nature of the system. However, you can
      override the :py:meth:`verify_preconditions` method to
      implement some stricter or weaker checks, or can you just run
      this action using a retry mechanism to deal with errors coming
      from commands sended from the wrong state.

    """  # pylint: disable=line-too-long # noqa: E501

    # (I think it's worth to keep the enable_logging parameter here)
    # (maybe this is a signal that it should be removed everywhere)
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        system: ObsStateSystem,
        target_state: ObsState,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        commands_input: ObsStateCommandsInput | dict | None = None,
        enable_logging: bool = True,
    ):
        """Initialize the ObsStateSetter.thelts
            to the value of :py:const:`DEFAULT_SUBARRAY_ID`.
        :param commands_input: The inputs to use for commands such as
            ``AssignResources``, ``Configure`` and ``Scan``. It defaults to
            no inputs (None).
        :param enable_logging: If True, the logger will be enabled. It defaults
            to True. The same policy will be applied to all the steps
            and commands executed.
        """
        super().__init__(enable_logging=enable_logging)

        # (the parameters are duplicated in the steps, but it's fine)
        # pylint: disable=duplicate-code
        self.system = system
        """The system that the step will act on."""
        self.target_state = target_state
        """The target state the system should move to."""
        self.subarray_id = subarray_id
        """The subarray id the step will act on."""
        self.commands_input = (
            ObsStateCommandsInput.get_object(commands_input)
            or ObsStateCommandsInput()
        )
        """
        The inputs to use for commands such as ``AssignResources``,
        ``Configure`` and ``Scan.
        """

        # initialise the map of observation states to steps
        self.obs_state_steps_map: dict[ObsState, ObsStateSetterStep] = {}
        """The map that associates observation states to steps.

        By default, the map is filled with the default steps defined in
        :py:meth:`configure_default_steps`. You can override the steps
        with the :py:meth:`override_step` method.
        """
        self.configure_default_steps()

    # -------------------------------------------------------------------
    # Class lifecycle and description methods

    def description(self) -> str:
        return (
            f"Move subarray {self.subarray_id} "
            f"from {str(self._system_obs_state())} "
            f"to {str(self.target_state)}."
        )

    # TODO: what to do with preconditions? Could I verify I am in a
    # supported state? Actually long term all the states will be supported
    # so it is not a big deal.

    def execute_procedure(self):
        """Move towards the target observation state (if not already there).

        The procedure:

        # TODO: describe the procedure
        """

    def verify_postconditions(self, timeout: SupportsFloat = 0):
        """The system reached the observation state consistently."""

    # -------------------------------------------------------------------
    # Other Utilities

    def override_step(
        self, obs_state: ObsState, new_step_class: type[ObsStateSetterStep]
    ):
        """Override a step with a new class.

        This method allows you to override a step with a
        (automatically created) instance of a new
        :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`
        subclass that will be used to move the system from the
        given observation state to the next one towards the target state.

        :param obs_state: The observation state to override the step for.
        :param new_step_class: The new class to use for the step.

        :raises ValueError: If the new step is not compatible with the
            requested observation state.
        """
        # Create an instance of the new step class
        new_step = new_step_class(
            self.system,
            self.target_state,
            self.subarray_id,
            self.commands_input,
        )

        # verify that the new step is compatible with the requested state
        if not new_step.get_assumed_obs_state() == obs_state:
            raise ValueError(
                f"Step class {new_step_class.__name__} is not compatible with "
                f"the observation state {str(obs_state)}, because it "
                "assumes the observation state "
                f"{str(new_step.get_assumed_obs_state())}. Please check how "
                "is implemented the method ``get_assumed_obs_state`` "
                "in the new step class."
            )

        # Replace the old step with the new one
        self.obs_state_steps_map[obs_state] = new_step

    def configure_default_steps(self):
        """Configure the default steps for the observation states.

        This method configures the default steps for the observation states.
        It is called by the constructor to set up the default steps.

        If you modify some class setting (e.g., subarray_id, commands_input,
        etc.), please call this method again to reconfigure the steps.
        """
        self.override_step(ObsState.EMPTY, ObsStateSetterStepFromEmpty)
        self.override_step(
            ObsState.RESOURCING, ObsStateSetterStepFromResourcing
        )
        self.override_step(ObsState.IDLE, ObsStateSetterStepFromIdle)
        self.override_step(
            ObsState.CONFIGURING, ObsStateSetterStepFromConfiguring
        )
        self.override_step(ObsState.READY, ObsStateSetterStepFromReady)
        self.override_step(ObsState.SCANNING, ObsStateSetterStepFromScanning)
        self.override_step(ObsState.RESETTING, ObsStateSetterStepFromResetting)
        self.override_step(ObsState.ABORTING, ObsStateSetterStepFromAborting)
        self.override_step(ObsState.ABORTED, ObsStateSetterStepFromAborted)
        self.override_step(ObsState.FAULT, ObsStateSetterStepFromFault)
        self.override_step(
            ObsState.RESTARTING, ObsStateSetterStepFromRestarting
        )

    def _system_obs_state(self) -> ObsState:
        """Get the overall observation state of the system.

        :return: The overall observation state of the system.
        """
        return read_obs_state(
            self.system.get_main_obs_state_device(self.subarray_id)
        )
