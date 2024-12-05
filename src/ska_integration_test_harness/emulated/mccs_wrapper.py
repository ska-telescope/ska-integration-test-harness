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
