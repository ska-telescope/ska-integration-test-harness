"""Tools to put the system in a desired observation state."""

import abc
from typing import SupportsFloat

from assertpy import assert_that
from ska_control_model import ObsState

from ska_integration_test_harness.extensions.subarray.inputs import (
    ObsStateCommandsInput,
)

from ...core.actions.sut_action import SUTAction
from .exceptions import (
    ObsStateDidNotReachTargetState,
    ObsStateSystemNotConsistent,
)
from .setter_step import ObsStateSetterStep
from .steps import (
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
from .system import (
    DEFAULT_SUBARRAY_ID,
    ObsStateSystem,
    read_devices_obs_state,
    read_sys_obs_state,
)

# -------------------------------------------------------------------
# Base class for observation state setters


# pylint: disable=too-many-instance-attributes
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

    The implemented algorithm is a simplification of he observation state
    machine. Essentially:

    - We view the observation state machine as a directed graph, where the
      nodes are the observation states and the edges are the operations that
      can be done for move the system from one observation state to another
    - The graph is very similar to the observation state machine, but it is
      simplified in two ways:

      - the regular operational flow (EMPTY -> RESOURCING -> IDLE -> ...)
        is viewed as unidirectional (so, for example, you can go from
        EMPTY to IDLE but not from IDLE to EMPTY, without aborting and
        restarting first)
      - the edges are not just commands but commands + synchronisations
        policies (so for example, from EMPTY to IDLE there is a single
        "logical" edge that is the "AssignResources" command + the
        synchronisation on the quiescent/stable "IDLE" state,
        while instead from EMPTY to
        RESOURCING there is another logical edge that is the "AssignResources"
        command + the synchronisation on the "RESOURCING" state)

    - The algorithm associate to each state a step and each step is supposed
      to contain the logic to move the system from the current observation
      state to the next one (towards the direction of the target observation
      state)

    - Concretely, what comes out is a sort of cyclic graph we navigate, where:

      - there is EMPTY as the starting point
      - there is the unidirectional operational flow (EMPTY -> IDLE -> ...)
        with their transient and quiescent/stable states
      - ABORTED and ABORTING are accessible calling the "Abort" command
        from any state of the regular operational flow
      - RESTARTING and EMPTY are accessible calling the "Restart" command
        from ABORTED or FAULT
      - (and so on)

    **Internal Structure**

    The steps are represented by
    :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep`
    subclasses and each of them is responsible to move the system from
    a certain starting observation state to the next one (till the target
    observation state is reached). Concretely, most of the steps just
    send a command to the system (according to the direction where
    the target observation state is) and then synchronise on the
    appropriate quiescent or transient state the command should reach.
    You can find a documentation of the existing steps implementations in the
    :py:mod:`ska_integration_test_harness.extensions.subarray.steps` module.

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

    - **consistency definition, verification and handling**:
      the consistency definition may be somewhat loose, we don't yet deal
      situations where a group of devices is not aligned in the same
      assumed state or in compatible states. **WORKAROUND**: you can
      call this action in a try-except block, catch errors and then
      choose to deal with the situation as you prefer (i.e., use this as
      a first-level reset and eventually use a "harder" reset if needed)
    - **procedure reliability**: we know we are in a distributed system and
      we know that not all our systems are always perfectly reliable
      (because of network issues, but also because we are testing them
      so we don't expect them to be perfect); the procedure is designed to
      be robust and to try to detect failures and unexpected behaviours
      (failing LRC, devices not in the expected states, etc.), so in some cases
      it may be a bit flaky or too strict for your needs. **WORKAROUND**:
      you can put the action in a try-except block, catch the exceptions
      and retry it a few times (if you think the issue is due to some
      flaky behaviour); you can override the steps and loose some specific
      constraints (e.g., in some cases if you know the LRC is failing
      but you are sure the system is in a consistent state, you can
      override the step to skip the LRC check).
    - **unreachable states**: some states are not reachable (RESETTING, FAULT). **WORKAROUND**:
      if you really need to reach them you can 1) override the steps to add
      the needed logic or 2) use the setter to reach a state where you
      know you can reach them and then reach them by yourself
    - **unsupported starting states**: the setting procedure starting
      from the transient states ABORTING and RESTARTING
      is not yet implemented. **SOON TO BE IMPLEMENTED**. **WORKAROUND**:
      if you need it right now, you can override the steps by extending
      them and adding the logit to exit from those states

    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(
        self,
        system: ObsStateSystem,
        target_state: ObsState,
        subarray_id: int = DEFAULT_SUBARRAY_ID,
        commands_input: ObsStateCommandsInput | dict | None = None,
    ):
        """Initialize the ObsStateSetter instance.

        :param system: The system that the step will act on.
        :param target_state: The target state the system should move to.
        :param subarray_id: The subarray id the step will act on. It defaults
            to the ``DEFAULT_SUBARRAY_ID`` global constant.
        :param commands_input: The inputs to use for commands such as
            ``AssignResources``, ``Configure`` and ``Scan``. It defaults to
            no inputs (None). You can specify the inputs as a
            :py:class:`~ska_integration_test_harness.extensions.subarray.ObsStateCommandsInput`
            object, as a dictionary or as a dictionary-like object. The
            important thing is that the keys are the command names and the
            values are the inputs for the commands as JSON strings.
        """  # pylint: disable=line-too-long # noqa: E501
        super().__init__()

        # (the parameters are duplicated in the steps, but it's fine)
        # pylint: disable=duplicate-code
        self.system = system
        """The system that the step will act on."""
        self.target_state = target_state
        """The target state the system should move to."""
        self.subarray_id = subarray_id
        """The subarray id the step will act on."""
        self.commands_input = ObsStateCommandsInput.get_object(commands_input)
        """
        The inputs to use for commands such as ``AssignResources``,
        ``Configure`` and ``Scan``.
        """

        # *****************************************************
        # ObsState map to steps

        # initialise the map of observation states to steps
        self.obs_state_steps_map: dict[ObsState, ObsStateSetterStep] = {}
        """The map that associates observation states to steps.

        By default, the map is filled with the default steps defined in
        :py:meth:`configure_default_steps`. You can override the steps
        with the :py:meth:`override_step` method.
        """
        self.configure_default_steps()

        # *****************************************************
        # Other settings

        self.max_steps: int = 5
        """The maximum number of steps that can be executed.

        This is a safety measure to avoid infinite loops if for whatever
        reason the steps are not able to move the system to the target
        observation state and they keep looping. At the moment, the longest
        paths is 5 steps long, so this is a reasonable default.
        """

        self._last_run_steps_execution_count: int = 0
        """The number of steps executed so far in the last run."""

        self.unreachable_states = [ObsState.FAULT, ObsState.RESETTING]
        """A list of unreachable states for the system.

        You can use this list for specifying observation states that
        you are sure the system cannot reach with the current steps.
        If the system is in one of these states, the preconditions
        will fail and the action will not be executed.

        By default, all states are supported, except
        ``FAULT`` and ``RESETTING``.
        """

        # TODO: create a separate step runner that runs the steps
        # and takes care of tracking which step are executed and
        # the states of the system
        # e.g., I could potentially generate in case of errors messages like:
        # followed path:
        # - EMPTY -> RESOURCING (ObsStateSetterStepFromEmpty)
        # - RESOURCING -> ABORTED (ObsStateSetterStepFromResourcing)
        # - ABORTED -> RESTARTING (ObsStateSetterStepFromAborted)

    # -------------------------------------------------------------------
    # Class lifecycle and description methods

    def description(self) -> str:
        return (
            f"Move subarray {self.subarray_id} "
            f"from {str(self._curr_obs_state())} "
            f"to {str(self.target_state)}."
        )

    def verify_preconditions(self):
        """Verify the target state is reachable.

        The target state should not be in the unreachable states list.

        :raises AssertionError: If the target state is in the
            unreachable states.
        """
        super().verify_preconditions()

        assert_that(self.unreachable_states).described_as(
            "The target state should not be in the unreachable states "
            f"({str(self.unreachable_states)})"
        ).does_not_contain(self.target_state)

    def execute_procedure(self):
        """Move towards the target observation state (if not already there).

        The procedure internally loops through the steps to move the system
        from the current observation state to the target observation state.
        At each loop iteration:

        - The system is checked to see if it is already in the target
          observation state
        - If it is, the loop is broken and the action is considered completed
          (the postconditions will verify consistency)
        - If it is not, it's executed the step associated with the current
          observation state to move the system to the next one

        The loop is repeated until the target observation state is reached
        or until the maximum number of steps is reached
        (see :py:attr:`max_steps`).

        Each step shares the same logging and execution settings of this
        action (timeout included).
        """
        # reset the execution counter
        self._last_run_steps_execution_count = 0

        # loop until the target state is reached or the maximum number
        # of steps is reached
        while self._last_run_steps_execution_count < self.max_steps:

            # if the system is already in the target state, we are done
            curr_obs_state = self._curr_obs_state()
            if curr_obs_state == self.target_state:
                break

            self._last_run_steps_execution_count += 1

            # get the step to move from the current observation state
            # to the next one
            step = self.obs_state_steps_map[curr_obs_state]

            # execute the step (propagating this class log policy
            # and other settings - timeout included)
            step.set_logging(self.is_logging_enabled())
            step.execute(**self._last_execution_params.as_dict())

    def verify_postconditions(self, timeout: SupportsFloat = 0):
        """Verify the system reached the observation state consistently.

        The postcondition is verified when:

        - the system is in the target observation state
        - all the devices are in a consistent state (see
          :py:meth:`~ska_integration_test_harness.extensions.subarray.ObsStateSetterStep.verify_preconditions`
          for more details)

        :param timeout: The timeout to use for the verification (It is
            ignored, because when we verify those postconditions we
            are expecting the system to already be in the desired state).
        """
        super().verify_postconditions(timeout)

        # verify that the system is in the target observation state
        if self._curr_obs_state() != self.target_state:
            raise ObsStateDidNotReachTargetState(
                self.target_state, self.subarray_id, self.system, self
            )

        # verify that all the devices are in a consistent state
        # (use the target step precondition to do so)
        step = self.obs_state_steps_map[self.target_state]

        try:
            step.verify_preconditions()
        except ObsStateSystemNotConsistent as exc:
            # TODO: maybe replace with prev. exception, for consistency
            # and clearness in documentation
            raise ObsStateSystemNotConsistent(
                self.target_state,
                read_devices_obs_state(self.system, self.subarray_id),
                self,
                failure_kind="Failed postcondition in action ",
            ) from exc

    # -------------------------------------------------------------------
    # Other Utilities

    def _curr_obs_state(self) -> ObsState:
        """Shortcut to get the current observation state of the system."""
        return read_sys_obs_state(self.system, self.subarray_id)

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
