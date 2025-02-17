"""Common assertions for the SKA ITH Core.

**DEPRECATED**: This module is deprecated and will be removed in the future.
Please use the new module :mod:`ska_integration_test_harness.extensions.lrc`
instead.
"""  # pylint: disable=line-too-long # noqa: E501

import logging

from ..lrc.assert_lrc_completion import AssertLRCCompletion

logging.warning(
    "The 'ska_integration_test_harness.extensions.assertions' "
    "module is deprecated "
    "and will be removed in the future. Please use the new "
    "'ska_integration_test_harness.extensions.lrc' module instead."
)

__all__ = ["AssertLRCCompletion"]
