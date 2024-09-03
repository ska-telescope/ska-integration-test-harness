"""A wrapper for a production CSP."""

from assertpy import assert_that
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
)
from ska_integration_test_harness.structure.csp_wrapper import CSPWrapper


class ProductionCSPWrapper(CSPWrapper):
    """A wrapper for a production CSP.

    TODO: describe differences.
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

    WAIT_FOR_OFF_TIMEOUT = 50

    def move_to_on(self) -> None:
        if not self.all_production:
            # NOTE: in old code this line was BEFORE
            # self.central_node.TelescopeOn(). Empirically,
            # it seems the order not to matter, but I am not sure.

            event_tracer = TangoEventTracer()
            event_tracer.subscribe_event(self.csp_master, "State")

            # NOTE: why CSP should be in OFF state when I want the telescope
            # to be ON? It seems a contradiction.
            if self.csp_master.adminMode != 0:
                self.csp_master.adminMode = 0

            # wait for the CSP master to be in OFF state
            assert_that(event_tracer).described_as(
                "FAIL IN MoveToOn PROCEDURE: "
                f"CSP master ({self.csp_master.dev_name()}) "
                "is supposed to be in OFF state."
            ).within_timeout(
                self.WAIT_FOR_OFF_TIMEOUT
            ).has_change_event_occurred(
                self.csp_master, "State", DevState.OFF
            )

    def move_to_off(self) -> None:
        """Move to OFF for production test wrapper does nothing."""

    def tear_down(self) -> None:
        """Tear down the CSP (not needed)."""

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (not needed)."""
