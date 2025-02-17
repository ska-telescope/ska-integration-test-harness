"""Common actions for the SKA ITH Core.

**DEPRECATED**: This module is deprecated and will be removed in the future.
Please use the new module :mod:`ska_integration_test_harness.extensions.lrc`
instead.

This module is supposed to contain common actions that can be
re-used across different test contexts and on multiple SKA SUTs.

At the moment, it contains only one action,
:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`, which
sends a command to a Tango device and - optionally -
permits you to wait for the LRC to be completed.
Optionally, it also permits you to fail early if some
LRC error code is detected among events.
"""


from ..lrc.tango_lrc_action import TangoLRCAction

import logging
logging.warning(
    "The 'ska_integration_test_harness.extensions.actions' "
    "module is deprecated "
    "and will be removed in the future. Please use the new "
    "'ska_integration_test_harness.extensions.lrc' module instead."
)

__all__ = ["TangoLRCAction"]
