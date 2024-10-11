"""The abstract definition of a subsystem wrapper."""

import abc

import tango

from ..common_utils.tango_devices_info import DevicesInfoProvider


class SubsystemWrapper(abc.ABC):
    """The abstract definition of a subsystem wrapper.

    A subsystem is a part of the telescope involved in the tests
    (e.g. CSP, TMC, Dishes, etc.). A subsystem has the following properties:

    - has a name
    - has tango devices
    - can be emulated or not

    On a subsystem, we can perform the following operations:

    - access the properties described above
    - get a recap of the subsystem information (system name, emulated or not,
      devices information)

    This class represents the abstract definition of a subsystem wrapper.
    Extend this class and implement the abstract methods to create a
    subsystem wrapper for a specific subsystem. Your child class may be
    also abstract, if you want for example to distinguish between
    emulated and production subsystems.
    """

    @abc.abstractmethod
    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem.

        :return: The name of the subsystem.
        """

    @abc.abstractmethod
    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the sub-system devices as a dictionary.

        :return: A dictionary of device proxies, where the key is an unique
            identifier of the device and the value is the device proxy.

            NOTE: the unique identifier is not necessarily the device name, but
            more something that explains "what role" the device has
            in the subsystem (e.g., "central_node", "dish_1", etc.).
        """

    @abc.abstractmethod
    def is_emulated(self) -> bool:
        """Check if the subsystem is emulated.

        :return: True if the subsystem is emulated, False otherwise.
        """

    def get_recap(
        self, devices_info_provider: DevicesInfoProvider | None = None
    ) -> str:
        """Get a (string) recap of the subsystem information.

        The recap contains the subsystem name, the emulated status and
        the devices information. The devices information is a list of
        the devices in the subsystem, eventually enriched with further
        information (e.g., version, etc.).

        :param devices_info_provider: The provider to get info about Tango
            devices from ska-k8s-config-exporter. If None, only the device
            names are included in the recap.
        """
        res = self.get_subsystem_name()
        if self.is_emulated():
            res += " (emulated)"
        else:
            res += " (production)"
        res += ". Devices:\n"

        for device_key, device in self.get_all_devices().items():
            res += f"- {device_key}: "

            # if a provider is given, try to get more info about the device
            if devices_info_provider is not None:
                device_info = devices_info_provider.get_device_recap(
                    device.dev_name()
                )
                res += device_info
            # otherwise, just print the Tango device name
            else:
                res += device.dev_name()
            res += "\n"

        return res
