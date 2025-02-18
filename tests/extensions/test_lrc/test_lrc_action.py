"""Unit tests for the TangoLRCAction class."""

from datetime import datetime

import pytest
from assertpy import assert_that
from ska_control_model import ResultCode

from ska_integration_test_harness.extensions.lrc.assert_lrc_completion import (
    AssertLRCCompletion,
)
from ska_integration_test_harness.extensions.lrc.tango_lrc_action import (
    TangoLRCAction,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event, delayed_add_event
from tests.utils import assert_elapsed_time_is_closed_to

from ...core.actions.utils import create_state_change_assertion


@pytest.mark.platform
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

    @staticmethod
    def test_lrc_verification_succeeds_when_lrc_completion_detected():
        """Test that the action passes when LRC completion is detected.

        (Given a LRC ID is set on the last command result)
        """
        device = create_device_proxy_mock("test/device/1")
        action = TangoLRCAction(device, "MoveToOn")
        action.add_postconditions(
            create_state_change_assertion("test/device/1"),
        ).add_lrc_completion_to_postconditions().add_lrc_errors_to_early_stop()
        action.last_command_result = ("Running", ["LRC_1234"])

        add_event(action.tracer, "test/device/1", "state", "ON")
        add_event(
            action.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("LRC_1234", '[0, "ok, LRC completed"]'),
        )

        action.verify_postconditions()

    @staticmethod
    def test_lrc_verification_fails_when_lrc_error_detected():
        """Test that the action fails when LRC error is detected.

        (Given a LRC ID is set on the last command result)
        """
        device = create_device_proxy_mock("test/device/1")
        action = TangoLRCAction(device, "MoveToOn")
        action.add_postconditions(
            create_state_change_assertion("test/device/1"),
        ).add_lrc_completion_to_postconditions().add_lrc_errors_to_early_stop()
        action.last_command_result = ("Running", ["LRC_1234"])

        add_event(action.tracer, "test/device/1", "state", "ON")
        add_event(
            action.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("LRC_1234", '[1, "error, LRC failed"]'),
        )

        with pytest.raises(AssertionError):
            action.verify_postconditions()

    @staticmethod
    def test_lrc_verification_fails_when_lrc_completion_not_detected():
        """Test that the action fails when LRC completion is not detected.

        (Given a LRC ID is set on the last command result)
        """
        device = create_device_proxy_mock("test/device/1")
        action = TangoLRCAction(device, "MoveToOn")
        action.add_postconditions(
            create_state_change_assertion("test/device/1"),
        ).add_lrc_completion_to_postconditions().add_lrc_errors_to_early_stop()
        action.last_command_result = ("Running", ["LRC_1234"])

        add_event(action.tracer, "test/device/1", "state", "ON")

        with pytest.raises(AssertionError):
            action.verify_postconditions()

    # ---------------------------------------------------------------------
    # A few integration tests with a timeout

    @staticmethod
    def test_lrc_succeed_if_lrc_completes_within_timeout():
        """A LRC action accepts a timeout for postconditions verification."""
        device = create_device_proxy_mock("test/device/1")
        device.command_inout.return_value = ("Running", ["LRC_1234"])
        action = (
            TangoLRCAction(device, "MoveToOn")
            .add_lrc_completion_to_postconditions()
            .add_lrc_errors_to_early_stop()
        )
        delayed_add_event(
            action.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("LRC_1234", '[0, "ok, LRC completed"]'),
            delay=0.5,
        )

        start_time = datetime.now()
        action.execute(postconditions_timeout=1)

        assert_elapsed_time_is_closed_to(start_time, 0.5, 0.1)

    @staticmethod
    def test_lrc_fails_when_lrc_failure_is_detected():
        """A LRC action fails if the LRC fails within the timeout."""
        device = create_device_proxy_mock("test/device/1")
        device.command_inout.return_value = ("Running", ["LRC_1234"])
        action = TangoLRCAction(device, "MoveToOn")
        action.add_postconditions(
            create_state_change_assertion("test/device/1"),
        ).add_lrc_completion_to_postconditions().add_lrc_errors_to_early_stop()
        delayed_add_event(
            action.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("LRC_1234", '[3, "error, LRC failed"]'),
            delay=0.5,
        )

        start_time = datetime.now()
        with pytest.raises(AssertionError):
            action.execute(postconditions_timeout=1)

        assert_elapsed_time_is_closed_to(start_time, 0.5, 0.1)
