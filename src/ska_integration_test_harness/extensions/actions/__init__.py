"""Common actions for the SKA ITH Core.

**DEPRECATED**: This module is deprecated and will be removed in the future.
Please use the new module :mod:`ska_integration_test_harness.extensions.lrc`
instead.
"""

import logging

from ..lrc.tango_lrc_action import TangoLRCAction

logging.warning(
    "The 'ska_integration_test_harness.extensions.actions' "
    "module is deprecated "
    "and will be removed in the future. Please use the new "
    "'ska_integration_test_harness.extensions.lrc' module instead."
)

__all__ = ["TangoLRCAction"]
