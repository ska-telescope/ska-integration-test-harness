"""An emulated MCCS wrapper."""

from ska_integration_test_harness.emulated.utils.teardown_helper import (
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper


class EmulatedMCCSWrapper(MCCSWrapper):
    """An emulated MCCS wrapper."""

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def tear_down(self) -> None:
        """Tear down the MCCS.

        The procedure is the following:
        - Reset the health state for the MCCS master and the MCCS subarray.
        - Clear the command call on the MCCS subarray.
        - Reset the transitions data for the MCCS subarray.
        - Reset the delay for the MCCS subarray.
        """
        EmulatedTeardownHelper.reset_health_state(
            [self.mccs_controller, self.mccs_subarray]
        )
        EmulatedTeardownHelper.clear_command_call([self.mccs_subarray])
        EmulatedTeardownHelper.reset_transitions_data([self.mccs_subarray])
        EmulatedTeardownHelper.reset_delay([self.mccs_subarray])
        EmulatedTeardownHelper.unset_defective_status([self.mccs_subarray])

    def clear_command_call(self) -> None:
        """Clear the command call on the MCCS."""
        EmulatedTeardownHelper.clear_command_call([self.mccs_subarray])
