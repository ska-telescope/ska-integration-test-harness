"""Common extension to send Long Running Commands and synchronizing on them.

This module contains actions and assertions to send **Long Running Commands**
(**LRC**) to a Tango device, synchronizing on it's completion and optionally
failing early if some error code is detected in the LRC events. The library
implements LRC verification assuming your devices are compliant with the
SKA LMC (Long Running Command) standard.

The main access point to this module is the
:class:`~ska_integration_test_harness.extensions.lrc.TangoLRCAction` class,
which can be used like a
:py:class:`~ska_integration_test_harness.core.actions.TangoCommandAction`
but with additional features to synchronize on the LRC completion and
detect LRC errors to eventually fail early.

The class relies on
:py:class:`~ska_integration_test_harness.extensions.lrc.AssertLRCCompletion`
to implement LRC completion verification and error detection. Probably you
will not need to use this class directly.

If for some reason your devices emit LRC in different formats, with a bit
of handwork you can extend the classes and override the methods to adapt
them to your needs.
"""

from .tango_lrc_action import TangoLRCAction
from .assert_lrc_completion import AssertLRCCompletion

__all__ = ["TangoLRCAction", "AssertLRCCompletion"]
