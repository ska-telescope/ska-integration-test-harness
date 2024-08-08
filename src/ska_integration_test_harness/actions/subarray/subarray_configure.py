"""Invoke configure command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.pointing_state import PointingState


class SubarrayConfigure(TelescopeCommandAction):
    """Invoke configure command on subarray Node."""

    def __init__(self, configure_input: JSONInput):
        super().__init__()
        self.configure_input = configure_input

    def _action(self):
        logging.info("Invoking Configure on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Configure(
            self.configure_input.get_json_string()
        )
        return result, message

    def termination_condition(self):
        # TODO: should add this too?
        # if Resource(device_dict.get("tmc_subarraynode")) == "READY":
        #         invoked_from_ready = True
        # if invoked_from_ready:
        #         the_waiter.set_wait_for_configuring()

        # all SA must be in READY state
        res = all_subarrays_have_obs_state(self.telescope, ObsState.READY)

        for device in self.telescope.dishes.dish_master_list:
            res.extend(
                [
                    ExpectedStateChange(device, "dishMode", DishMode.OPERATE),
                    ExpectedStateChange(
                        device, "pointingState", PointingState.TRACK
                    ),
                ]
            )

        return res
