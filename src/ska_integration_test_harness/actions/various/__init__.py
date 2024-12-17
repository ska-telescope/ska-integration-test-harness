"""Various actions for the test harness.

At the moment, it contains:

- the procedure to move the PST Low device to the ON state
- the procedure to reset PST Low
"""

import tango
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

    def __init__(self, pst_device: tango.DeviceProxy):
        super().__init__()
        self.pst_device = pst_device

    def _action(self) -> None:
        if self.pst_device != DevState.ON:
            self._log("Moving the PST Low device to ON state")
            self.pst_device.On()
        else:
            self._log("PST Low device is already in ON state")

    def termination_condition(self):
        """The PST Low device is in the ON state."""
        return [
            ExpectedStateChange(
                self.pst_device,
                "state",
                DevState.ON,
            )
        ]


class MoveToOffPST(TelescopeAction[None]):
    """Move the PST Low device to the OFF state (if not already there)."""

    def __init__(self, pst_device: tango.DeviceProxy):
        super().__init__()
        self.pst_device = pst_device

    def _action(self) -> None:
        if self.pst_device.state != DevState.OFF:
            self._log("Moving the PST Low device to OFF state")
            self.pst_device.Off()
        else:
            self._log("PST Low device is already in OFF state")

    def termination_condition(self):
        """The PST Low device is in the OFF state."""
        return [
            ExpectedStateChange(
                self.pst_device,
                "state",
                DevState.OFF,
            )
        ]


class ResetPSTObsState(TelescopeAction[None]):
    """Reset the PST Low device to the default obs state (IDLE)."""

    def __init__(self, pst_device: tango.DeviceProxy):
        super().__init__()
        self.pst_device = pst_device

    def _action(self) -> None:
        if self.pst_device.obsState != ObsState.IDLE:
            self._log("Resetting the PST Low device to IDLE state")
            self.pst_device.obsreset()
        else:
            self._log("PST Low device is already in IDLE state")

    def termination_condition(self):
        """The PST Low device is in the ON state."""
        return [
            ExpectedStateChange(
                self.pst_device,
                "obsState",
                ObsState.IDLE,
            )
        ]
