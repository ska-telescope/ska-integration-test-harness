"""A set of facades to interact with the telescope devices.

A set of facades to interact with the telescope devices, abstracting the
complexities of the interaction with and between the devices.
"""

from .csp_facade import CSPFacade
from .dishes_facade import DishesFacade
from .sdp_facade import SDPFacade
from .tmc_central_node_facade import TMCCentralNodeFacade
from .tmc_facade import TMCFacade
from .tmc_subarray_node_facade import TMCSubarrayNodeFacade

__all__ = [
    "TMCCentralNodeFacade",
    "TMCSubarrayNodeFacade",
    "TMCFacade",
    "CSPFacade",
    "DishesFacade",
    "SDPFacade",
]
