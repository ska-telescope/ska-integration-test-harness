"""A collection of wrappers for various system components.

:py:class:`~ska_integration_test_harness.structure.telescope_wrapper.TelescopeWrapper`
is the main entry point for the telescope system.

Right now, it exposes the following subsystems (through a wrapper for each):

- TMC
- SDP
- CSP
- Dishes

All the subsystems wrappers are represented by abstract classes, so you can
create your own implementation for each one (e.g., an implementation that
points to the devices of a real subsystem, or an implementation that points
to the devices of an emulated subsystem).

The module also contains a generic
:py:class:`~ska_integration_test_harness.structure.subsystem_wrapper.SubsystemWrapper`
class that can be used as a base class for any subsystem wrapper.
"""  # pylint: disable=line-too-long # noqa: E501

from .csp_wrapper import CSPWrapper
from .dishes_wrapper import DishesWrapper
from .sdp_wrapper import SDPWrapper
from .subsystem_wrapper import SubsystemWrapper
from .telescope_wrapper import TelescopeWrapper
from .tmc_wrapper import TMCWrapper

__all__ = [
    "TelescopeWrapper",
    "TMCWrapper",
    "SDPWrapper",
    "CSPWrapper",
    "DishesWrapper",
    "SubsystemWrapper",
]
