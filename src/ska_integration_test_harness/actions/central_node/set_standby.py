"""An action to set the central node to STANDBY State."""

from tango import DevState

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.utils.termination_conditions import (
    dishes_have_dish_mode,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode


class SetStandby(TelescopeCommandAction):
    """An action to set the central node to STANDBY State."""

    def __init__(self) -> None:
        super().__init__()
        self.target_device = self.telescope.tmc.central_node
        self.is_long_running_command = True

    def _action(self):
        self._log("Setting the central node to STANDBY state")
        res = self.telescope.tmc.central_node.TelescopeStandby()
        # self.telescope.csp.move_to_off()
        return res

    def termination_condition(self):
        """Central node should be in STANDBY state and so also SDP
        all dishes should be in STANDBY_LP mode and LRC must terminate.
        """
        # LRC must terminate
        expected_events = super().termination_condition()

        # The central node should be in STANDBY state (when )
        expected_events += [
            # The SDP controller should be in STANDBY
            # and subarray nodes should be in OFF state
            ExpectedStateChange(
                self.telescope.sdp.sdp_subarray,
                "State",
                DevState.OFF,
            ),
            ExpectedStateChange(
                self.telescope.sdp.sdp_master, "State", DevState.STANDBY
            ),
        ]

        if self.telescope.tmc.supports_mid():
            expected_events += [
                # (in Mid) CSP controller should be in STANDBY state
                ExpectedStateChange(
                    self.telescope.csp.csp_master, "State", DevState.STANDBY
                ),
                # (in Mid) central node should be in STANDBY state
                ExpectedStateChange(
                    self.telescope.tmc.central_node,
                    "telescopeState",
                    DevState.STANDBY,
                ),
            ]

            # (in Mid) All dishes should be in STANDBY_LP mode
            expected_events += dishes_have_dish_mode(
                self.telescope, DishMode.STANDBY_LP
            )

        return expected_events
