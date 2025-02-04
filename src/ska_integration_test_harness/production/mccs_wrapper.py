"""A production MCCS wrapper."""

import tango
from ska_control_model import AdminMode

from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper


class ProductionMCCSWrapper(MCCSWrapper):
    """A production MCCS wrapper."""

    def __init__(self, mccs_configuration):
        super().__init__(mccs_configuration)

        # set admin mode values of MCCS devices
        if self.mccs_controller.adminMode != AdminMode.ONLINE:
            self.set_admin_mode_values_mccs()

    def set_admin_mode_values_mccs(self):
        """Set the adminMode values of MCCS devices.

        (Procedure taken from here:
        https://gitlab.com/ska-telescope/mccs/ska-low-mccs/-/blob/main/notebooks/admin_mode_all_devices.ipynb?ref_type=heads
        )
        """  # pylint: disable=line-too-long # noqa: E501
        db = tango.Database()

        for device_name in db.get_device_exported("low-mccs/*"):
            device = tango.DeviceProxy(device_name)
            if device.adminMode != AdminMode.ONLINE:
                device.adminMode = AdminMode.ONLINE

        # All devices should be online
        for device_name in db.get_device_exported("low-mccs/*"):
            assert tango.DeviceProxy(device_name).adminMode == AdminMode.ONLINE

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def tear_down(self) -> None:
        """Nothing specific to be done for production MCCS."""

    def clear_command_call(self) -> None:
        """Nothing specific to be done for production MCCS."""
