"""A wrapper for a production CSP."""

import tango
from assertpy import assert_that
from ska_control_model import AdminMode, HealthState
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from ska_integration_test_harness.actions.various import ResetPSTLow
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

        if self.config.supports_low():

            # When in Low, the PST device is needed and
            # the admin mode must be set to ONLINE
            self.ensure_admin_mode_online()

            # set the PST device too
            self.pst = tango.DeviceProxy(self.config.pst_name)

            # set the CBF processor devices too
            self.cbf_proc1 = tango.DeviceProxy("low-cbf/processor/0.0.0")
            self.cbf_proc2 = tango.DeviceProxy("low-cbf/processor/0.0.1")

    def ensure_admin_mode_online(self) -> None:
        """Ensure the CSP master is in ONLINE admin mode."""
        if self.csp_master.adminMode != AdminMode.ONLINE:
            # set ADMIN mode to ONLINE
            self.csp_master.adminMode = AdminMode.ONLINE

            # wait for the CSP admin to transition to ONLINE
            tracer = TangoEventTracer(
                {
                    "healthState": HealthState,
                }
            )
            tracer.subscribe_event(self.csp_master, "state")
            tracer.subscribe_event(self.csp_master, "healthState")
            tracer.subscribe_event(self.csp_subarray, "state")
            tracer.subscribe_event(self.csp_subarray, "healthState")
            assert_that(tracer).described_as(
                "FAIL IN CSP SETUP: "
                "The CSP admin doesn't transition to ONLINE."
            ).within_timeout(10).has_change_event_occurred(
                self.csp_master, "state", DevState.ON
            ).has_change_event_occurred(
                self.csp_subarray, "state", DevState.ON
            ).has_change_event_occurred(
                self.csp_master, "healthState", HealthState.UNKNOWN
            ).has_change_event_occurred(
                self.csp_subarray, "healthState", HealthState.UNKNOWN
            )
        assert_that(self.csp_master.adminMode).described_as(
            "FAIL IN CSP SETUP: The CSP admin mode is supposed to be ONLINE."
        ).is_equal_to(AdminMode.ONLINE)

    def set_serial_number_of_cbf_processor(self):
        """Sets serial number for cbf processor.

        TODO: is this something that should be parametrised?
        """
        self.cbf_proc1.serialnumber = "XFL14SLO1LIF"
        self.cbf_proc1.subscribetoallocator("low-cbf/allocator/0")
        self.cbf_proc1.register()

        self.cbf_proc2.serialnumber = "XFL1HOOQ1Y44"
        self.cbf_proc2.subscribetoallocator("low-cbf/allocator/0")
        self.cbf_proc2.register()

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific CSP methods and properties

    def before_move_to_on(self) -> None:
        """If in Low, the PST On command must be called."""
        if self.config.supports_low():
            self.pst.On()

    def after_move_to_on(self) -> None:
        """If in Low, set the serial numbers in the CBF processor"""
        if self.config.supports_low():
            self.set_serial_number_of_cbf_processor()

    def tear_down(self) -> None:
        """Tear down the CSP.

        This method will:

        - reset PST (if in Low) obsState to IDLE
        """
        if self.config.supports_low():
            ResetPSTLow().execute()

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP (not needed)."""
