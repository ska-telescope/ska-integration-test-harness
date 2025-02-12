import abc

from ska_control_model import ObsState

from ska_integration_test_harness.core.actions.sut_action import SUTAction
from ska_integration_test_harness.extensions.subarray.obs_state_system import ObsStateSystem

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
    in.

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
    acceptable. If not implemented, just :py:meth:`get_next_action`
    will be considered an acceptable state.
    """

    def __init__(self, system: ObsStateSystem, subarray_id: int):
        """Initializes the step.

        :param system: The system that the step will act on.
        :param subarray_id: The subarray id the step will act on.
        """
        super().__init__()
        self.system = system
        self.subarray_id = subarray_id


    @abc.abstractmethod
    def get_next_action(self, target_state: ObsState) -> SUTAction:
        """Returns the next action to do to move towards the target state.

        This method is supposed to return the next action to do to move
        towards the target state. The action could be a command to be
        sent to the subarray, or actually any other action.

        :param target_state: The target state the system should move to.
        :return: The next action to do.
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
    