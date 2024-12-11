"""An emulated MCCS wrapper."""

from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper


class EmulatedMCCSWrapper(MCCSWrapper):
    """An emulated MCCS wrapper."""

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def tear_down(self) -> None:
        """Tear down MCCS.

        The procedure is the following:

        - TODO: Add
        """

    def clear_command_call(self) -> None:
        """Clear the command call on the MCCS."""
        # TODO: Add

    # TODO: DO something similar to this
    # def tear_down(self) -> None:
    #     """Tear down the CSP.

    #     The procedure is the following:
    #     - Reset the health state for the CSP master and the CSP subarray.
    #     - Clear the command call on the CSP subarray.
    #     - Reset the transitions data for the CSP subarray.
    #     - Reset the delay for the CSP subarray.
    #     """
    #     EmulatedTeardownHelper.reset_health_state(
    #         [self.csp_master, self.csp_subarray]
    #     )
    #     EmulatedTeardownHelper.clear_command_call([self.csp_subarray])
    #     EmulatedTeardownHelper.reset_transitions_data([self.csp_subarray])
    #     EmulatedTeardownHelper.reset_delay([self.csp_subarray])
    #     EmulatedTeardownHelper.unset_defective_status([self.csp_subarray])
