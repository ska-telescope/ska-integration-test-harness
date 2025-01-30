"""Interface for a system that supports observation state operations."""

from typing import Protocol

import tango

DEFAULT_SUBARRAY_ID = 1


class ObsStateSubarrayDoesNotExist(ValueError):
    """Exception to raise when an given subarray ID does not exist."""

    def __init__(self, obs_state_id: int, further_info: str = ""):
        self.obs_state_id = obs_state_id
        msg = f"Subarray ID {obs_state_id} does not exist. "
        if further_info:
            msg += f"Further info: {further_info}"
        super().__init__(msg)


class ObsStateSystem(Protocol):
    """Interface for a system that supports observation state operations.

    This interface represent a generic system that supports operations
    related to the :py:class:`ska_control_model.ObsState` state machine
    on one or more subarrays.

    The interface is empty, is meant to be implemented by a client class and
    is used to fill the missing knowledge that
    :py:mod:`~ska_integration_test_harness.extensions.subarray`
    needs to operate on the subarray lifecycle. Clients should implement:

    - :py:meth:`get_target_device`, to tell which is the target device for
        a given command on a given subarray ID
    - :py:meth:`get_main_obs_state_device`, to tell which is the main device
        that changes the observation state on a given subarray ID
    - :py:meth:`get_obs_state_devices`, to tell which are the devices that
        are involved in the observation state machine on a given subarray ID

    The methods are meant to support multiple subarrays, so they should
    accept a ``subarray_id`` parameter to specify the subarray ID they
    are referring to. If the passed subarray ID does not exist, the methods
    should raise :py:exc:`ObsStateIDDoesNotExist`.
    """

    def get_target_device(
        self, command_name: str, subarray_id: int = DEFAULT_SUBARRAY_ID
    ) -> tango.DeviceProxy:
        """Get the device that should receive the given command.

        Given a command name, this method should return the device proxy
        that is supposed to receive and handle the command (if the command
        is directed to subarray Nr. ``subarray_id``).

        :param command_name: the name of the command
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :return: the device proxy of the target device
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """

    def get_main_obs_state_device(
        self, subarray_id: int = DEFAULT_SUBARRAY_ID
    ) -> tango.DeviceProxy:
        """Get the main device that changes the observation state.

        This method should return the "main" device proxy that is
        representative for the whole system observation state for
        the subarray Nr. ``subarray_id``. The returned device should
        be the one whose ``obsState`` attribute is supposed to be
        the "reference" for the observation state of the system.

        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :return: the device proxy of the main device
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """

    def get_obs_state_devices(
        self, subarray_id: int = DEFAULT_SUBARRAY_ID
    ) -> list[tango.DeviceProxy]:
        """Get the devices that are involved in the observation state.

        This method should return the list of device proxies that are
        involved in the observation state machine for the subarray Nr.
        ``subarray_id``. The returned devices should be the ones whose
        ``obsState`` attribute is supposed to change according to the
        observation state of the system.

        :param obs_state: the observation state
        :param subarray_id: the subarray ID (default: DEFAULT_SUBARRAY_ID)
        :return: the list of device proxies. Try to return them in a
            order that is meaningful for the system (it's recommended to
            return first "controlled" devices, then "monitoring" devices).
            Consider the order you give here will be the order of the
            state change assertions, so make it more or less similar to
            the order you expect the devices to change state.
        :raise ObsStateIDDoesNotExist: if the passed subarray ID does not exist
        """
