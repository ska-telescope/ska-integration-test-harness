"""Common actions for the SKA ITH Core.

This module is supposed to contain common actions that can be
re-used across different test contexts and on multiple SKA SUTs.

At the moment, it contains only one action,
:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`, which
sends a command to a Tango device and - optionally - permits you to wait the
LRC to be completed. Optionally it also permits you to fail early if some
LRC error code is detected among events.
"""

from .lrc_action import TangoLRCAction

__all__ = ["TangoLRCAction"]
