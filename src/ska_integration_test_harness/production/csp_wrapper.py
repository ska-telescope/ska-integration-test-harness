"""A wrapper for a production CSP."""

import tango
from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

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

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific CSP methods and properties

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
        if self.csp_subarray.obsState != ObsState.EMPTY:
            # set adminMode to 1 so devices
            self._hard_reset()

    def _hard_reset(self) -> None:
        """Hard reset the CSP."""
        # set adminMode to 1 so devices are offline
        self.csp_master.adminMode = 1

        # call init first on CBF devices, then on CSPLMC
        for device in [
            tango.DeviceProxy("mid_csp_cbf/sub_elt/subarray_01"),
            tango.DeviceProxy("mid_csp_cbf/sub_elt/subarray_02"),
            tango.DeviceProxy("mid_csp_cbf/sub_elt/subarray_03"),
            tango.DeviceProxy("mid_csp_cbf/sub_elt/controller"),
            tango.DeviceProxy("mid-csp/subarray/01"),
            tango.DeviceProxy("mid-csp/subarray/02"),
            tango.DeviceProxy("mid-csp/subarray/03"),
            tango.DeviceProxy("mid-csp/control/0"),
        ]:
            device.init()

        # set adminMode to 0 so devices are online
        self.csp_master.adminMode = 0

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (not needed)."""
