"""Create a `TelescopeAction` to reset the subarray in a certain obs state."""

import time
from typing import Callable

from ska_control_model import ObsState

from ska_integration_test_harness.actions.subarray.subarray_abort import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAbort,
)
from ska_integration_test_harness.actions.subarray.subarray_assign_resources import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAssignResources,
)
from ska_integration_test_harness.actions.subarray.subarray_clear_obs_state import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayClearObsState,
)
from ska_integration_test_harness.actions.subarray.subarray_configure import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayConfigure,
)
from ska_integration_test_harness.actions.subarray.subarray_execute_transition import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayExecuteTransition,
)
from ska_integration_test_harness.actions.subarray.subarray_scan import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayScan,
)
from ska_integration_test_harness.actions.telescope_action import (  # pylint: disable=line-too-long # noqa: E501
    TelescopeAction,
)
from ska_integration_test_harness.actions.telescope_action_sequence import (  # pylint: disable=line-too-long # noqa: E501
    TelescopeActionSequence,
)
from ska_integration_test_harness.inputs.obs_state_commands_input import (  # pylint: disable=line-too-long # noqa: E501
    ObsStateCommandsInput,
)
from ska_integration_test_harness.structure.telescope_wrapper import (  # pylint: disable=line-too-long # noqa: E501
    TelescopeWrapper,
)


class WaitAddedForSkb372(TelescopeAction):
    """Wait added for SKB-372. TODO: remove this class."""

    def _action(self):
        time.sleep(5)

    def termination_condition(self):
        return []


class SubarrayObsStateResetterFactory:
    """Factory to create `TelescopeAction`s to bring subarray in a obs state.

    This factory is used to create `TelescopeAction`s to bring the subarray
    in a certain obs state. The factory provides methods to create composite
    actions that can move subarray to:

    - Empty state
    - Resourcing state
    - Idle state
    - Aborting state
    - Aborted state
    - Configuring state
    - Ready state
    - Scanning state

    The starting state of the subarray is not considered while creating,
    because all the actions are designed to reset the subarray to
    `EMPTY` state first and then move to the target state.
    """

    def __init__(self, commands_inputs: ObsStateCommandsInput) -> None:
        """Initialize with the telescope and the JSON inputs.

        :param commands_inputs: The JSON inputs for the commands to bring
            the subarray in a certain obs state. You can pass just the
            JSON inputs you need, but if one of them is missing, you may
            occur in an error.

        :raises ValueError: If not all inputs are provided and the factory is
            not provided either.
        """
        self.telescope = TelescopeWrapper()
        self.commands_inputs = commands_inputs

    def create_action_to_reset_subarray_to_empty(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `EMPTY`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.EMPTY` state.
        """
        return SubarrayClearObsState()

    def create_action_to_reset_subarray_to_resourcing(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `RESOURCING`.

        :return: A `TelescopeAction` to reset the subarray to the
            `ObsState.RESOURCING` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_empty(),
                SubarrayExecuteTransition(
                    "AssignResources",
                    argin=self.commands_inputs.get_assign_input.get_json_string(),  # pylint: disable=line-too-long # noqa: E501
                ),
            ],
        )

    def create_action_to_reset_subarray_to_idle(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to the `IDLE`.

        :return: A `TelescopeAction` to reset the subarray to the
            `ObsState.IDLE` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_empty(),
                SubarrayAssignResources(self.commands_inputs.get_assign_input),
            ],
        )

    def create_action_to_reset_subarray_to_aborting(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `ABORTING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.ABORTING` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                SubarrayExecuteTransition("Abort", argin=None),
            ],
        )

    def create_action_to_reset_subarray_to_aborted(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `ABORTED`.

        :return: A `TelescopeAction` to reset the subarray to the
            `ObsState.ABORTED` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                SubarrayAbort(),
            ],
        )

    def create_action_to_reset_subarray_to_configuring(
        self,
    ) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `CONFIGURING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.CONFIGURING` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                # WaitAddedForSkb372(),
                SubarrayExecuteTransition(
                    "Configure",
                    argin=self.commands_inputs.get_configure_input.get_json_string(),  # pylint: disable=line-too-long # noqa: E501
                ),
            ],
        )

    def create_action_to_reset_subarray_to_ready(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `READY`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.READY` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                # WaitAddedForSkb372(),
                SubarrayConfigure(self.commands_inputs.get_configure_input),
            ],
        )

    def create_action_to_reset_subarray_to_scanning(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `SCANNING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.SCANNING` state.
        """
        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_ready(),
                SubarrayScan(self.commands_inputs.get_scan_input),
            ],
        )

    @property
    def _map_state_to_method(
        self,
    ) -> dict[ObsState, Callable[[], TelescopeAction]]:
        return {
            ObsState.EMPTY: self.create_action_to_reset_subarray_to_empty,
            ObsState.RESOURCING: self.create_action_to_reset_subarray_to_resourcing,  # pylint: disable=line-too-long # noqa: E501
            ObsState.IDLE: self.create_action_to_reset_subarray_to_idle,
            ObsState.ABORTING: self.create_action_to_reset_subarray_to_aborting,  # pylint: disable=line-too-long # noqa: E501
            ObsState.ABORTED: self.create_action_to_reset_subarray_to_aborted,
            ObsState.CONFIGURING: self.create_action_to_reset_subarray_to_configuring,  # pylint: disable=line-too-long # noqa: E501
            ObsState.READY: self.create_action_to_reset_subarray_to_ready,
            ObsState.SCANNING: self.create_action_to_reset_subarray_to_scanning,  # pylint: disable=line-too-long # noqa: E501
        }

    def create_action_to_reset_subarray_to_state(
        self, target_state: ObsState
    ) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to the given state.

        :param target_state: The target state to which the subarray should
            be reset.
        :return: A `TelescopeAction` to reset the subarray to the given state.
        """
        return self._map_state_to_method[target_state]()
