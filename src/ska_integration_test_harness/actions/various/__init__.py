"""Various actions for the test harness.

At the moment, it contains:

- the procedure to reset PST Low
"""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class ResetPSTLow(TelescopeAction[None]):
    """Reset the PST Low device to the default obs state (IDLE)."""

    def _action(self) -> None:
        if self.telescope.csp.pst.obsState != ObsState.IDLE:
            self._log("Resetting the PST Low device to IDLE state")
            self.telescope.csp.pst.obsreset()
        else:
            self._log("PST Low device is already in IDLE state")

    def termination_condition(self):
        """The PST Low device is in the ON state."""
        return [
            ExpectedStateChange(
                self.telescope.csp.pst,
                "obsState",
                ObsState.IDLE,
            )
        ]
