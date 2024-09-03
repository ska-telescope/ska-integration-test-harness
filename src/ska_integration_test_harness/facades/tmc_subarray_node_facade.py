"""Wrapper for subarray node."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.subarray.force_change_of_obs_state import (  # pylint: disable=line-too-long # noqa: E501
    ForceChangeOfObsState,
)
from ska_integration_test_harness.actions.subarray.subarray_abort import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAbort,
)
from ska_integration_test_harness.actions.subarray.subarray_assign_resources import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayAssignResources,
)
from ska_integration_test_harness.actions.subarray.subarray_configure import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayConfigure,
)
from ska_integration_test_harness.actions.subarray.subarray_end_observation import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayEndObservation,
)
from ska_integration_test_harness.actions.subarray.subarray_end_scan import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayEndScan,
)
from ska_integration_test_harness.actions.subarray.subarray_execute_transition import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayExecuteTransition,
)
from ska_integration_test_harness.actions.subarray.subarray_move_to_off import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayMoveToOff,
)
from ska_integration_test_harness.actions.subarray.subarray_move_to_on import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayMoveToOn,
)
from ska_integration_test_harness.actions.subarray.subarray_release_all_resources import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayReleaseAllResources,
)
from ska_integration_test_harness.actions.subarray.subarray_restart import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayRestart,
)
from ska_integration_test_harness.actions.subarray.subarray_scan import (  # pylint: disable=line-too-long # noqa: E501
    SubarrayScan,
)
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.telescope_wrapper import (  # pylint: disable=line-too-long # noqa: E501
    TelescopeWrapper,
)


class TMCSubarrayNodeFacade:
    """A facade to TMC Subarray Node device and its actions.

    A facade to TMC sub-system, providing a simplified interface to the
    subarray node devices and their actions. It contains:

    - references to subarray node device,
    - references to leaf devices to interact with CSP and SDP subarrays,
    - an action to initialise the subarray setting the subarray ID,
    - actions to move the subarray to ON and OFF states,
    - actions to interact with the obs state of the subarray, making
      individual state changes (through command calls) or forcing the
      change of the obs state to a target state whatever the current state is,
    - various other actions (e.g., five point calibration scan).
    """

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    # -----------------------------------------------------------
    # Subarray devices

    @property
    def dish_leaf_node_list(self):
        """Return Dish Leaf Node List"""
        return self._telescope.tmc.dish_leaf_node_list
        # NOTE: in old test harness code, sometimes just the first two
        # dishes were used. I don't know if there was a reason behind that
        # choice. Right now, we are using 4

    @property
    def subarray_node(self):
        """Return Subarray Node Proxy"""
        return self._telescope.tmc.subarray_node

    @property
    def csp_master_leaf_node(self):
        """Return CSP Master Leaf Node Proxy"""
        return self._telescope.tmc.csp_master_leaf_node

    @property
    def sdp_master_leaf_node(self):
        """Return SDP Master Leaf Node Proxy"""
        return self._telescope.tmc.sdp_master_leaf_node

    @property
    def csp_subarray_leaf_node(self):
        """Return CSP Subarray Leaf Node Proxy"""
        return self._telescope.tmc.csp_subarray_leaf_node

    @property
    def sdp_subarray_leaf_node(self):
        """Return SDP Subarray Leaf Node Proxy"""
        return self._telescope.tmc.sdp_subarray_leaf_node

    # -----------------------------------------------------------
    # Setter for initialising subarray

    def set_subarray_id(self, requested_subarray_id: str) -> None:
        """Create subarray devices for the requested subarray.

        :param requested_subarray_id: Subarray ID to set.
        """
        self._telescope.set_subarray_id(requested_subarray_id)

    # -----------------------------------------------------------
    # Actions over subarray telescope state

    def move_to_on(self, wait_termination: bool = True):
        """Move subarray to ON state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayMoveToOn()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    def move_to_off(self, wait_termination: bool = True):
        """Move Subarray to OFF state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayMoveToOff()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # -----------------------------------------------------------
    # Actions over subarray obs state

    # @sync_configure(device_dict=device_dict)
    def configure(
        self,
        configure_input: JSONInput,
        wait_termination: bool = True,
    ):
        """Invoke configure command on subarray Node.

        :param configure_input: json input for configure command.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayConfigure(configure_input)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_end(device_dict=device_dict)
    def end_observation(self, wait_termination: bool = True):
        """Invoke End command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayEndObservation()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_endscan(device_dict=device_dict)
    def end_scan(self, wait_termination: bool = True):
        """Invoke EndScan command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayEndScan()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    def scan(self, scan_input: JSONInput, wait_termination: bool = True):
        """Invoke Scan command on subarray Node.

        :param scan_input: json input for scan command.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayScan(scan_input)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_abort(device_dict=device_dict)
    def abort(self, wait_termination: bool = True):
        """Invoke Abort command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayAbort()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_restart(device_dict=device_dict)
    def restart(self, wait_termination: bool = True):
        """Invoke Restart command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayRestart()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_assign_resources(device_dict)
    def assign_resources(
        self, assign_input: JSONInput, wait_termination: bool = True
    ):
        """Invoke Assign Resource command on subarray Node

        :param assign_input: Assign resource input json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayAssignResources(assign_input)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_release_resources(device_dict)
    def release_all_resources(self, wait_termination: bool = True):
        """Invoke Release Resource command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = SubarrayReleaseAllResources()
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # -----------------------------------------------------------
    # Generic ob-state transitions actions

    def execute_transition(
        self,
        command_name: str,
        command_input: JSONInput | None = None,
        expected_obs_state: ObsState | None = None,
    ):
        """Execute provided command on subarray

        :param command_name: Name of command to execute
        :param command_input: JSON input for the command. By default None.
        :param expected_obs_state: Expected obsState after command execution.
            By default no expected obsState (=> no waiting for termination
            condition).

        :return: result, message
        """
        action = SubarrayExecuteTransition(
            command_name,
            command_input=command_input,
            expected_obs_state=expected_obs_state,
        )
        action.set_termination_condition_policy(expected_obs_state is not None)
        return action.execute()

    def force_change_of_obs_state(
        self,
        dest_state_name: ObsState,
        commands_inputs: TestHarnessInputs,
        wait_termination: bool = True,
    ) -> None:
        """Force SubarrayNode obsState to provided obsState.

        :param commands_inputs: The JSON inputs for the commands to bring
            the subarray in a certain obs state. You can pass just the
            JSON inputs you need, but if one of them is missing, you may
            occur in an error.

        :param dest_state_name: Name of the destination obsState.
        :param commands_inputs: The JSON inputs for the commands to bring
            the subarray in a certain obs state. You can pass just the
            JSON inputs you need, but if one of them is missing, you may
            occur in an error.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        """
        action = ForceChangeOfObsState(dest_state_name, commands_inputs)
        action.set_termination_condition_policy(wait_termination)
        action.execute()
