"""Unit tests for the TangoLRCAction class."""

from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from ska_control_model import ResultCode

from ska_integration_test_harness.extensions.actions.lrc_action import (
    TangoLRCAction,
)
from ska_integration_test_harness.extensions.assertions.lrc_completion import (
    AssertLRCCompletion,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
# from tests.actions.utils.mock_event_tracer import add_event

from ...core.actions.utils import (
    create_state_change_assertion,
)


@pytest.mark.extensions
class TestTangoLRCAction:
    """Unit tests for the TangoLRCAction class.

    We verify the following cases:

    - a LRC verification is correctly added to postconditions
    - a LRC error is correctly added to early stops
    - during verification, if a correct LRC completion is detected,
      the action passes
    - during verification, if a LRC error is detected, the action fails
    - during verification, if a LRC completion is not detected,
      the action fails

    """

    @staticmethod
    def test_add_lrc_completion_to_postconditions():
        """Test that a LRC completion is correctly added to postconditions."""
        device = create_device_proxy_mock("test/device/1")
        action = TangoLRCAction(device, "MoveToOn")
        action.add_postconditions(
            create_state_change_assertion("test/device/1"),
        )

        action.add_lrc_completion_to_postconditions(
            expected_result_codes=[ResultCode.OK, ResultCode.ABORTED],
        )

        assert_that(action.postconditions).described_as(
            "A new assertion is added for LRC completion in postconditions"
        ).is_length(2)
        assert_that(action.postconditions[1]).described_as(
            "The new assertion is for LRC completion"
        ).is_instance_of(AssertLRCCompletion)
        assert_that(
            action.postconditions[1].expected_result_codes
        ).described_as(
            "The new assertion result codes are correctly set"
        ).is_equal_to(
            [ResultCode.OK, ResultCode.ABORTED]
        )
        assert_that(action.postconditions[1].device).described_as(
            "The new assertion device is the command target device"
        ).is_equal_to(device)

    @staticmethod
    def test_lrc_error_is_added_to_early_stop():
        """Test that a LRC error is correctly added to early stop."""
        device = create_device_proxy_mock("test/device/1")
        action = TangoLRCAction(device, "MoveToOn")
        post_cond = create_state_change_assertion("test/device/1")
        action.add_postconditions(post_cond)

        action.add_lrc_errors_to_early_stop(
            error_result_codes=[ResultCode.FAILED],
        )

        assert_that(post_cond.early_stop).described_as(
            "A new assertion is added for LRC errors in early stop"
        ).is_not_none()
        assert_that(action.early_stop).described_as(
            "The new assertion is added to the action early stop"
        ).is_not_none()


