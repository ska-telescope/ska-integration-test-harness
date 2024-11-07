"""Create a Telescope Action to reset the subarray in a certain obs state."""

from typing import Callable

from ska_control_model import ObsState

from ska_integration_test_harness.actions.central_node.central_node_assign_resources import (  # pylint: disable=line-too-long # noqa: E501
    CentralNodeAssignResources,
)
from ska_integration_test_harness.actions.subarray.subarray_abort import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAbort,
)
from ska_integration_test_harness.actions.subarray.subarray_clear_obs_state import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayClearObsState,
)
from ska_integration_test_harness.actions.subarray.subarray_configure import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayConfigure,
)
from ska_integration_test_harness.actions.subarray.subarray_restart import (
    SubarrayRestart,
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
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.telescope_wrapper import (  # pylint: disable=line-too-long # noqa: E501
    TelescopeWrapper,
)


class SubarrayObsStateResetterFactory:
    """Factory to create Telescope Actions to bring subarray in a obs state.

    This factory is used to create
    :py:class:`~ska_integration_test_harness.actions.telescope_action.TelescopeAction` s
    to bring the subarray
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
    """  # pylint: disable=line-too-long # noqa: E501

    def __init__(self, commands_inputs: TestHarnessInputs) -> None:
        """Initialise with the telescope and the JSON inputs.

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
        assign_resources_action = CentralNodeAssignResources(
            self.commands_inputs.get_input(
                TestHarnessInputs.InputName.ASSIGN, fail_if_missing=True
            )
        )
        assign_resources_action.set_synchronise_on_transient_state(True)

        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_empty(),
                assign_resources_action,
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
                CentralNodeAssignResources(
                    self.commands_inputs.get_input(
                        TestHarnessInputs.InputName.ASSIGN,
                        fail_if_missing=True,
                    )
                ),
            ],
        )

    def create_action_to_reset_subarray_to_configuring(
        self,
    ) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `CONFIGURING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.CONFIGURING` state.
        """
        configure_action = SubarrayConfigure(
            self.commands_inputs.get_input(
                TestHarnessInputs.InputName.CONFIGURE, fail_if_missing=True
            )
        )
        configure_action.set_synchronise_on_transient_state(True)

        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                configure_action,
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
                SubarrayConfigure(
                    self.commands_inputs.get_input(
                        TestHarnessInputs.InputName.CONFIGURE,
                        fail_if_missing=True,
                    )
                ),
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
                SubarrayScan(
                    self.commands_inputs.get_input(
                        TestHarnessInputs.InputName.SCAN, fail_if_missing=True
                    )
                ),
            ],
        )

    def create_action_to_reset_subarray_to_aborting(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `ABORTING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.ABORTING` state.
        """
        abort_action = SubarrayAbort()
        abort_action.set_synchronise_on_transient_state(True)

        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_idle(),
                abort_action,
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

    def create_action_to_reset_subarray_to_restarting(self) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to `RESTARTING`.

        :return: A `TelescopeAction` to reset the subarray to
            the `ObsState.RESTARTING` state.
        """
        reset_action = SubarrayRestart()
        reset_action.set_synchronise_on_transient_state(True)

        return TelescopeActionSequence(
            [
                self.create_action_to_reset_subarray_to_aborted(),
                reset_action,
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
            ObsState.CONFIGURING: self.create_action_to_reset_subarray_to_configuring,  # pylint: disable=line-too-long # noqa: E501
            ObsState.READY: self.create_action_to_reset_subarray_to_ready,
            ObsState.SCANNING: self.create_action_to_reset_subarray_to_scanning,  # pylint: disable=line-too-long # noqa: E501
            ObsState.ABORTING: self.create_action_to_reset_subarray_to_aborting,  # pylint: disable=line-too-long # noqa: E501
            ObsState.ABORTED: self.create_action_to_reset_subarray_to_aborted,
            ObsState.RESTARTING: self.create_action_to_reset_subarray_to_restarting,  # pylint: disable=line-too-long # noqa: E501
        }

    def create_action_to_reset_subarray_to_state(
        self, target_state: ObsState
    ) -> TelescopeAction:
        """Create a `TelescopeAction` to reset the subarray to the given state.

        :param target_state: The target state to which the subarray should
            be reset.
        :return: A `TelescopeAction` to reset the subarray to the given state.
        :raises NotImplementedError: If the procedure to reach the
            target state is not implemented.
        """
        if target_state not in self._map_state_to_method:
            raise NotImplementedError(
                f"Resetting subarray to {target_state} is not implemented."
            )

        return self._map_state_to_method[target_state]()
