"""A wrapper for an emulated CSP."""

from tango import DevState

from ska_integration_test_harness.emulated.utils.teardown_helper import (  # pylint: disable=line-too-long # noqa: E501
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.structure.csp_wrapper import (  # pylint: disable=line-too-long # noqa: E501
    CSPDevices,
)


class EmulatedCSPDevices(CSPDevices):
    """A wrapper for an emulated CSP."""

    def move_to_on(self) -> None:
        # NOTE: in old code this line was AFTER
        # self.central_node.TelescopeOn(). Empirically,
        # it seems the order not to matter, but I am not sure.
        self.csp_subarray.SetDirectState(DevState.ON)

    def move_to_off(self) -> None:
        self.csp_subarray.SetDirectState(DevState.OFF)

    def tear_down(self) -> None:
        """Tear down the CSP."""
        EmulatedTeardownHelper.reset_health_state(
            [self.csp_master, self.csp_subarray]
        )
        EmulatedTeardownHelper.clear_command_call([self.csp_subarray])
        EmulatedTeardownHelper.reset_transitions_data([self.csp_subarray])
        EmulatedTeardownHelper.reset_delay([self.csp_subarray])
        EmulatedTeardownHelper.unset_defective_status([self.csp_subarray])

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP."""
        EmulatedTeardownHelper.clear_command_call([self.csp_subarray])
