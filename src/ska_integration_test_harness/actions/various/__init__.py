"""Various actions for the test harness.

At the moment, it contains:

- the procedure to move the PST Low device to the ON state
- the procedure to reset PST Low
"""

from ska_control_model import ObsState
from tango import DevState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)


class MoveToOnPST(TelescopeAction[None]):
    """Move the PST Low device to the ON state (if not already there)."""

    def _action(self) -> None:
        assert self.telescope.csp.pst is not None
        if self.telescope.csp.pst.state != DevState.ON:
            self._log("Moving the PST Low device to ON state")
            self.telescope.csp.pst.On()
        else:
            self._log("PST Low device is already in ON state")

    def termination_condition(self):
        """The PST Low device is in the ON state."""
        return [
            ExpectedStateChange(
                self.telescope.csp.pst,
                "state",
                DevState.ON,
            )
        ]


class MoveToOffPST(TelescopeAction[None]):
    """Move the PST Low device to the OFF state (if not already there)."""

    def _action(self) -> None:
        assert self.telescope.csp.pst is not None
        if self.telescope.csp.pst.state != DevState.OFF:
            self._log("Moving the PST Low device to OFF state")
            self.telescope.csp.pst.Off()
        else:
            self._log("PST Low device is already in OFF state")

    def termination_condition(self):
        """The PST Low device is in the OFF state."""
        return [
            ExpectedStateChange(
                self.telescope.csp.pst,
                "state",
                DevState.OFF,
            )
        ]


class ResetPSTObsState(TelescopeAction[None]):
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
