"""All the remaining configuration options for the telescope.

This module contains all the configuration options that doesn't fit in the
other configuration classes.
"""

from dataclasses import dataclass


@dataclass
class OtherDevicesConfigurations:
    """All the remaining configuration options for the telescope.

    (The configuration options that doesn't fit in the other
    specific configuration classes.)
    """

    sdp_queue_connector = "mid-sdp/queueconnector/01"

    alarm_handler1 = "alarm/handler/01"
