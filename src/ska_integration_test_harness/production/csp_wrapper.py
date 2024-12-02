"""A wrapper for a production CSP."""

from ska_control_model import AdminMode

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
)
from ska_integration_test_harness.structure.csp_wrapper import CSPWrapper


class ProductionCSPWrapper(CSPWrapper):
    """A wrapper for a production CSP.

    Differently from the emulated CSP wrapper, when a move to on command
    is called, the CSP master is supposed to be in OFF state, so it moves
    to OFF state.
    """

    def __init__(
        self, csp_configuration: CSPConfiguration, all_production: bool = False
    ):
        """Initialise the production CSP wrapper.

        :param csp_configuration: the CSP configuration.
        :param all_production: a flag that tell whether all components
            are production. It is needed in the move to on method.
        """
        super().__init__(csp_configuration)
        self.all_production = all_production
        self.config = csp_configuration

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific CSP methods and properties

    WAIT_FOR_OFF_TIMEOUT = 50

    def before_telescope_state_command(self) -> None:
        """If in Low, adminMode must be set to ONLINE."""

        if (
            self.config.supports_low()
            and self.csp_master.adminMode != AdminMode.ONLINE
        ):
            self.csp_master.adminMode = AdminMode.ONLINE

    def tear_down(self) -> None:
        """Tear down the CSP (not needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (not needed)."""
