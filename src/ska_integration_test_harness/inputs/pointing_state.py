"""Enum class for PointingState values."""

from enum import IntEnum, unique


@unique
class PointingState(IntEnum):
    """Enum class for PointingState values."""

    # TODO: Should I import this from somewhere else?
    READY = 0
    SLEW = 1
    TRACK = 2
    SCAN = 3
    UNKNOWN = 4
    NONE = 5
