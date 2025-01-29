"""Common assertions for the SKA ITH Core.

This module is supposed to contain common assertions that can be
re-used across different test contexts and on multiple SKA SUTs.

At the moment, it contains only one assertion,
:class:`~ska_integration_test_harness.extensions.assertions.AssertLRCCompletion`,
which is used in
:class:`~ska_integration_test_harness.extensions.actions.TangoLRCAction`
to check if the LRC has been completed successfully. Standalone use is
possible as well but not suggested, since the assertion requires a custom
interaction to set the Long Running Command ID.
"""  # pylint: disable=line-too-long # noqa: E501

from .lrc_completion import AssertLRCCompletion

__all__ = ["AssertLRCCompletion"]
