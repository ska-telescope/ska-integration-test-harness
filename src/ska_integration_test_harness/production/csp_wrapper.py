"""A wrapper for a production CSP."""

# import tango
from assertpy import assert_that
from ska_control_model import AdminMode
from ska_tango_testing.integration import TangoEventTracer

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

        # When in Low, the PST device is needed and
        # the admin mode must be set to ONLINE
        if self.config.supports_low():
            self.ensure_admin_mode_online()
            # TODO: connection to PST crashed before, we have to
            # check if it continues to crash even after the synchronization
            # on the admin mode
            # self.pst = tango.DeviceProxy(self.config.pst_name)

    def ensure_admin_mode_online(self) -> None:
        """Ensure the CSP master is in ONLINE admin mode."""
        if self.csp_master.adminMode != AdminMode.ONLINE:

            tracer = TangoEventTracer()
            tracer.subscribe_event(self.csp_master, "isCommunicating")

            self.csp_master.adminMode = AdminMode.ONLINE

            assert_that(tracer).described_as(
                "FAIL IN CSP SETUP: "
                "The CSP admin doesn't transition to ONLINE."
            ).within_timeout(10).has_change_event_occurred(
                self.csp_master, "isCommunicating", True
            )
        assert_that(self.csp_master.adminMode).described_as(
            "FAIL IN CSP SETUP: The CSP admin mode is supposed to be ONLINE."
        ).is_equal_to(AdminMode.ONLINE)

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific CSP methods and properties

    def before_move_to_on(self) -> None:
        """If in Low, the PST On command must be called."""
        # if self.config.supports_low():
        # self.pst.On()

    def tear_down(self) -> None:
        """Tear down the CSP (not needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (not needed)."""
