"""Utilities for the subarray extension."""

import tango
from ska_control_model import ObsState


def read_obs_state(device: tango.DeviceProxy) -> ObsState:
    """Read the obsState attribute from a given device.

    :param device: The device proxy to read the obsState attribute from.
    :return: The ObsState value read from the device.
    """
    return ObsState(device.obsState)
