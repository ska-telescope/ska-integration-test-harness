# pylint: disable=duplicate-code
"""A wrapper for TMC and all integration tests sub-components."""

from typing import Tuple

import tango
from ska_control_model import ResultCode

from ska_integration_test_harness.actions.central_node.central_node_assign_resources import (  # pylint: disable=line-too-long # noqa E501
    CentralNodeAssignResources,
)
from ska_integration_test_harness.actions.central_node.central_node_load_dish_config import (  # pylint: disable=line-too-long # noqa E501
    CentralNodeLoadDishConfig,
)
from ska_integration_test_harness.actions.central_node.central_node_perform_action import (  # pylint: disable=line-too-long # noqa E501
    CentralNodePerformAction,
)
from ska_integration_test_harness.actions.central_node.central_node_release_resources import (  # pylint: disable=line-too-long # noqa E501
    CentralNodeReleaseResources,
)
from ska_integration_test_harness.actions.central_node.move_to_off import (
    MoveToOff,
)
from ska_integration_test_harness.actions.central_node.move_to_on import (
    MoveToOn,
)
from ska_integration_test_harness.actions.central_node.set_standby import (
    SetStandby,
)
from ska_integration_test_harness.common_utils.deprecated import DeprecatedMeta
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TMCCentralNodeFacade(metaclass=DeprecatedMeta):
    """A facade to TMC Central Node device and its actions.

    A facade to TMC subsystem, providing a simplified interface to the
    central node device and its actions. It contains:

    - references to central node device,
    - references to master leaf devices to interact with CSP and SDP,
    - properties to get and set telescope state,
    - actions to move the telescope to ON, OFF and STANDBY states,
    - actions to load dish VCC configuration, assign and release resources,
    - a generic action to perform any action on central node.

    **IMPORTANT NOTE**: This facade is deprecated,
    since we want to use a facade for each subsystem. Please use
    :py:class:`~ska_integration_test_harness.facades.tmc_facade.TMCFacade`
    instead.
    """

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
    # Central Node telescope state actions

    def move_to_on(self, wait_termination: bool = True) -> None:
        """Move the telescope to ON state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        """
        action = MoveToOn()
        action.set_termination_condition_policy(wait_termination)
        action.execute()

    def move_to_off(self, wait_termination: bool = True) -> None:
        """Move the telescope to OFF state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        """
        action = MoveToOff()
        action.set_termination_condition_policy(wait_termination)
        action.execute()

    def set_standby(self, wait_termination: bool = True) -> None:
        """Set the telescope to STANDBY state.

        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        """
        action = SetStandby()
        action.set_termination_condition_policy(wait_termination)
        action.execute()

    # -----------------------------------------------------------
    # Central Node specific actions

    def load_dish_vcc_configuration(
        self, dish_vcc_config: str, wait_termination: bool = True
    ) -> Tuple[ResultCode, str]:
        """Invoke LoadDishCfg command on central Node.

        :param dish_vcc_config: Dishes VCC configuration json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = CentralNodeLoadDishConfig(dish_vcc_config)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_assign_resources(device_dict=device_dict)
    def assign_resources(
        self, assign_json: str, wait_termination: bool = True
    ) -> Tuple[ResultCode, str]:
        """Invoke Assign Resource command on central Node.

        :param assign_json: Assign resource input json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = CentralNodeAssignResources(assign_json)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # @sync_release_resources(device_dict=device_dict, timeout=500)
    def release_resources(
        self, input_string: str, wait_termination: bool = True
    ) -> Tuple[ResultCode, str]:
        """Invoke Release Resource command on central Node.

        :param input_string: Release resource input json.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.

        :return: result, message
        """
        action = CentralNodeReleaseResources(input_string)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()

    # -----------------------------------------------------------
    # Generic action

    def perform_action(
        self,
        command_name: str,
        input_json: JSONInput,
        wait_termination: bool = True,
    ) -> Tuple[ResultCode, str]:
        """Execute provided command on central node.

        :param command_name: Name of command to execute.
        :param input_json: Json send as input to execute command.
        :param wait_termination: set to False if you don't want to
            wait for the termination condition. By default the termination
            condition is waited.
        """
        action = CentralNodePerformAction(command_name, input_json)
        action.set_termination_condition_policy(wait_termination)
        return action.execute()
