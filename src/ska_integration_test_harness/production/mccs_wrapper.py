"""A production MCCS wrapper."""

from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper


class ProductionMCCSWrapper(MCCSWrapper):
    """A production MCCS wrapper."""

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def tear_down(self) -> None:
        """TODO: Add"""

    def clear_command_call(self) -> None:
        """TODO: Add"""
