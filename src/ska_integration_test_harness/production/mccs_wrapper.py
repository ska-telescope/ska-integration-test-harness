"""A production MCCS wrapper."""

from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper


class ProductionMCCSWrapper(MCCSWrapper):
    """A production MCCS wrapper."""

    # TODO: set admin mode values of MCCS devices

    # def set_admin_mode_values_mccs(self):
    #     """Set the adminMode values of MCCS devices."""
    #     max_retries: int = 3
    #     mccs_pasdbus_prefix = "low-mccs/pasdbus/*"
    #     mccs_prefix = "low-mccs/*"
    #     if self.mccs_controller.adminMode != AdminMode.ONLINE:
    #         db = tango.Database()
    #         pasd_bus_trls = db.get_device_exported(mccs_pasdbus_prefix)
    #         for pasd_bus_trl in pasd_bus_trls:
    #             pasdbus = tango.DeviceProxy(pasd_bus_trl)
    #             retry_communication(pasdbus, 30)

    #         device_trls = db.get_device_exported(mccs_prefix)
    #         devices = []
    #         for device_trl in device_trls:
    #             if "daq" in device_trl or "calibrationstore" in device_trl:
    #                 device = tango.DeviceProxy(device_trl)
    #                 retry_communication(device, 30)
    #             else:
    #                 device = tango.DeviceProxy(device_trl)
    #                 retry: int = 0
    #                 while (
    #                     device.adminMode != AdminMode.ONLINE
    #                     and retry <= max_retries
    #                 ):
    #                     try:
    #                         device.adminMode = AdminMode.ONLINE
    #                         devices.append(device)
    #                         time.sleep(0.1)
    #                     except tango.DevFailed as df:
    #                         logger.info(
    #                             "Issue occurred during setting the admin "
    #                             "mode: %s",
    #                             df,
    #                         )
    #                         retry += 1
    #                         time.sleep(0.1)

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific MCCS methods and properties

    def tear_down(self) -> None:
        """TODO: Add"""

    def clear_command_call(self) -> None:
        """TODO: Add"""
