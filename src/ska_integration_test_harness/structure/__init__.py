"""A collection of wrappers for various system components.

``TelescopeWrapper`` is the main entry point for the telescope system.

Right now, it exposes the following sub-systems (through a wrapper for each):

- TMC
- SDP
- CSP
- Dishes

All the subsystems wrappers are represented by abstract classes, so you can
create your own implementation for each one (e.g., an implementation that
points to the devices of a real subsystem, or an implementation that points
to the devices of an emulated subsystem).
"""

from .csp_wrapper import CSPWrapper
from .dishes_wrapper import DishesWrapper
from .sdp_wrapper import SDPWrapper
from .telescope_wrapper import TelescopeWrapper
from .tmc_wrapper import TMCWrapper

__all__ = [
    "TelescopeWrapper",
    "TMCWrapper",
    "SDPWrapper",
    "CSPWrapper",
    "DishesWrapper",
]
