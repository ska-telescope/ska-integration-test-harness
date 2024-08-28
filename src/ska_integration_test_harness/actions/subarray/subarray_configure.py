"""Invoke configure command on subarray Node."""

import logging

from ska_control_model import ObsState

from ska_integration_test_harness.actions.command_action import (
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.expected_event import (
    ExpectedEvent,
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    all_subarrays_have_obs_state,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.pointing_state import PointingState


class SubarrayConfigure(TransientQuiescentCommandAction):
    """Invoke configure command on subarray Node.

    This action is expected to move the subarray to the CONFIGURING state
    (transient) and then to the READY state (quiescent and stable).
    """

    def __init__(self, configure_input: JSONInput):
        super().__init__()
        self.configure_input = configure_input

    def _action(self):
        logging.info("Invoking Configure on TMC SubarrayNode")
        result, message = self.telescope.tmc.subarray_node.Configure(
            self.configure_input.get_json_string()
        )
        return result, message

    def termination_condition_for_quiescent_state(self) -> list[ExpectedEvent]:
        """All subarrays must reach the READY state.

        Also, all dishes must be in OPERATE dishMode and TRACK pointingState.
        """
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

    def termination_condition_for_transient_state(self) -> list[ExpectedEvent]:
        """All subarrays must reach the CONFIGURING state."""
        return all_subarrays_have_obs_state(
            self.telescope, ObsState.CONFIGURING
        )
