"""A facade to TMC."""

from typing import Any, Tuple

import tango
from ska_control_model import ObsState, ResultCode

from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)

from ..actions.central_node.central_node_assign_resources import (
    CentralNodeAssignResources,
)
from ..actions.central_node.central_node_load_dish_config import (
    CentralNodeLoadDishConfig,
)
from ..actions.central_node.central_node_perform_action import (
    CentralNodePerformAction,
)
from ..actions.central_node.central_node_release_resources import (
    CentralNodeReleaseResources,
)
from ..actions.central_node.move_to_off import MoveToOff
from ..actions.central_node.move_to_on import MoveToOn
from ..actions.central_node.set_standby import SetStandby
from ..actions.subarray.force_change_of_obs_state import ForceChangeOfObsState
from ..actions.subarray.subarray_abort import SubarrayAbort
from ..actions.subarray.subarray_configure import SubarrayConfigure
from ..actions.subarray.subarray_end_observation import SubarrayEndObservation
from ..actions.subarray.subarray_end_scan import SubarrayEndScan
from ..actions.subarray.subarray_execute_transition import (
    SubarrayExecuteTransition,
)
from ..actions.subarray.subarray_restart import SubarrayRestart
from ..actions.subarray.subarray_scan import SubarrayScan
from ..inputs.json_input import JSONInput
from ..inputs.test_harness_inputs import TestHarnessInputs
from ..structure.telescope_wrapper import TelescopeWrapper


class TMCFacade:
    """A facade to TMC devices and the actions on them.

    A facade to TMC subsystem, providing a simplified interface to:

    - references to central node device,
    - references to subarray devices and their leaf devices,
    - references to leaf devices to the controllers of CSP and SDP,
    - actions to move the telescope to ON, OFF and STANDBY states,
    - actions to load dish VCC configuration, assign and release resources,
    - actions to configure, scan, end scan, end observation, abort, restart
      the subarray,
    - an action to force the subarray to a certain obs state,
    - a generic action to perform any action on central node or subarray node.

    All the actions can be executed synchronously or asynchronously. When
    executed synchronously, the action waits for the termination condition
    to occur. When executed asynchronously, the action returns immediately
    and the termination condition is not waited. The timeout for the
    termination condition can be customized (otherwise the default action
    timeout is used).
    """

    # pylint: disable=too-many-public-methods

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    # -----------------------------------------------------------
    # CENTRAL NODE DEVICES

    @property
    def central_node(self) -> tango.DeviceProxy:
        """The central node Tango device proxy."""
        return self._telescope.tmc.central_node

    @property
    def csp_master_leaf_node(self) -> tango.DeviceProxy:
        """The CSP master leaf node Tango device proxy."""
        return self._telescope.tmc.csp_master_leaf_node

    @property
    def sdp_master_leaf_node(self) -> tango.DeviceProxy:
        """The SDP master leaf node Tango device proxy."""
        return self._telescope.tmc.sdp_master_leaf_node

    # -----------------------------------------------------------
    # SUBARRAY DEVICES

    @property
    def subarray_node(self):
        """Return Subarray Node Proxy"""
        return self._telescope.tmc.subarray_node

    def set_subarray_id(self, requested_subarray_id: str) -> None:
        """Make the ITH connect to the subarray devices with the given ID.

        By default, the ITH is connected to a certain subarray device.
        This method allows to change the subarray devices that are used
        by the various test harness actions.

        :param requested_subarray_id: Subarray ID to set.
        """
        self._telescope.set_subarray_id(requested_subarray_id)

    @property
    def dish_leaf_node_list(self):
        """Return Dish Leaf Node List"""
        return self._telescope.tmc.dish_leaf_node_list
        # NOTE: in old test harness code, sometimes just the first two
        # dishes were used. I don't know if there was a reason behind that
        # choice. Right now, we are using 4

    @property
    def csp_subarray_leaf_node(self):
        """Return CSP Subarray Leaf Node Proxy"""
        return self._telescope.tmc.csp_subarray_leaf_node

    @property
    def sdp_subarray_leaf_node(self):
        """Return SDP Subarray Leaf Node Proxy"""
        return self._telescope.tmc.sdp_subarray_leaf_node

    # -----------------------------------------------------------
    # ACTIONS YOU CALL ON CENTRAL NODE

    def _setup_and_run_action(
        self,
        action: TelescopeAction,
        wait_termination: bool,
        custom_timeout: int | None = None,
    ) -> Any:
        """Setup and run a telescope action.

        :param action: The action to run.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: The (eventual) result of the action.
        """
        action.set_termination_condition_policy(wait_termination)
        if custom_timeout is not None:
            action.set_termination_condition_timeout(custom_timeout)
        return action.execute()

    def move_to_on(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> None:
        """Move the telescope to ON state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.
        """
        action = MoveToOn()
        self._setup_and_run_action(action, wait_termination, custom_timeout)

    def move_to_off(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> None:
        """Move the telescope to OFF state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.
        """
        action = MoveToOff()
        self._setup_and_run_action(action, wait_termination, custom_timeout)

    def set_standby(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> None:
        """Set the telescope to STANDBY state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.
        """
        action = SetStandby()
        self._setup_and_run_action(action, wait_termination, custom_timeout)

    def load_dish_vcc_configuration(
        self,
        dish_vcc_config: str,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Invoke LoadDishCfg command on central Node.

        :param dish_vcc_config: dish vcc configuration json string.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = CentralNodeLoadDishConfig(dish_vcc_config)
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def assign_resources(
        self,
        assign_input: JSONInput,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Invoke Assign Resource command on central Node.

        :param assign_input: Assign resource input json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = CentralNodeAssignResources(assign_input)
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def release_resources(
        self,
        release_input: JSONInput,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Invoke Release Resource command on central Node.

        :param release_input: Release resource input json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = CentralNodeReleaseResources(release_input)
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    # -----------------------------------------------------------
    # ACTIONS YOU CALL ON SUBARRAY NODE

    def configure(
        self,
        configure_input: JSONInput,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Invoke configure command on subarray Node.

        :param configure_input: json input for configure command.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = SubarrayConfigure(configure_input)
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def end_observation(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> Tuple[ResultCode, str]:
        """Invoke End command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = SubarrayEndObservation()
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def end_scan(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> Tuple[ResultCode, str]:
        """Invoke EndScan command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = SubarrayEndScan()
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def scan(
        self,
        scan_input: JSONInput,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Invoke Scan command on subarray Node.

        :param scan_input: json input for scan command.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used.

        :return: result, message
        """
        action = SubarrayScan(scan_input)
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def abort(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> Tuple[ResultCode, str]:
        """Invoke Abort command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = SubarrayAbort()
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def restart(
        self, wait_termination: bool = True, custom_timeout: int | None = None
    ) -> Tuple[ResultCode, str]:
        """Invoke Restart command on subarray Node.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.

        :return: result, message
        """
        action = SubarrayRestart()
        return self._setup_and_run_action(
            action, wait_termination, custom_timeout
        )

    def force_change_of_obs_state(
        self,
        dest_state_name: ObsState,
        commands_inputs: TestHarnessInputs,
        wait_termination: bool = True,
        custom_timeout: int | None = None,
    ) -> None:
        """Force SubarrayNode obsState to provided obsState.

        :param dest_state_name: Name of the destination obsState.
        :param commands_inputs: The JSON inputs for the commands to bring
            the subarray in a certain obs state. You can pass just the
            JSON inputs you need, but if one of them is missing, you may
            occur in an error.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``wait_termination=True``.
        :raises NotImplementedError: If the procedure to reach the
            target state is not implemented.
        """
        action = ForceChangeOfObsState(dest_state_name, commands_inputs)
        self._setup_and_run_action(action, wait_termination, custom_timeout)

    # -----------------------------------------------------------
    # GENERIC ACTIONS

    def run_command_on_central_node(
        self,
        command_name: str,
        command_input: JSONInput | None = None,
    ) -> Tuple[ResultCode, str]:
        """Run a generic command on central node.

        NOTE: the termination condition is empty, so the action will
        return immediately.

        :param command_name: Name of command to execute.
        :param command_input: Json send as input to execute command.
        """
        action = CentralNodePerformAction(command_name, command_input)
        return action.execute()

    def run_command_on_subarray_node(
        self,
        command_name: str,
        command_input: JSONInput | None = None,
        expected_obs_state: "ObsState | None" = None,
        custom_timeout: int | None = None,
    ) -> Tuple[ResultCode, str]:
        """Run a generic command on subarray node.

        NOTE: the termination condition by default is empty. You can
        although wait for a certain obsState to be reached setting
        expected_obs_state.

        :param command_name: Name of command to execute
        :param command_input: JSON input for the command. By default None.
        :param expected_obs_state: Expected obsState after command execution.
            By default no expected obsState (=> no waiting for termination
            condition).
        :param custom_timeout: A custom timeout (in seconds) to wait for
            the termination condition to occur. If None, the default action
            timeout is used. This parameter is useful only when
            ``expected_obs_state`` is specified.

        :return: result, message
        """
        action = SubarrayExecuteTransition(
            command_name,
            command_input=command_input,
            expected_obs_state=expected_obs_state,
        )
        action.set_termination_condition_policy(expected_obs_state is not None)
        if custom_timeout is not None:
            action.set_termination_condition_timeout(custom_timeout)
        return action.execute()
