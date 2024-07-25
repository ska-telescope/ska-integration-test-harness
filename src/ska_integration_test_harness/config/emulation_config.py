"""Determine which components are real and which are emulated.

This module exposes a tool to represent the configuration which tells which
components are emulated and which are production ones.
"""

from dataclasses import dataclass


@dataclass
class EmulationConfiguration:
    """Representation of which components are emulated.

    Each of the attribute is a boolean that indicates whether the corresponding
    component is emulated. If the attribute is ``True``, the component
    is emulated. If ``False``, the component is a production one.
    """

    csp: bool = False
    sdp: bool = False
    dish: bool = False

    def all_emulated(self) -> bool:
        """Check if all components are emulated.

        return: ``True`` when all components are emulated, ``False`` otherwise.
        """
        return self.csp and self.sdp and self.dish

    def all_production(self) -> bool:
        """Check if all components are production ones.

        return: ``True`` when all components are production ones,
            ``False`` otherwise.
        """
        return not self.csp and not self.sdp and not self.dish
