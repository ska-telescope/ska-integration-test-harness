"""Unit tests for the AssertLRCCompletion class."""

import pytest
from ska_control_model import ResultCode

from ska_integration_test_harness.extensions.lrc.assert_lrc_completion import (
    AssertLRCCompletion,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event


@pytest.mark.extensions
class TestAssertLRCCompletion:
    """Unit tests for the AssertLRCCompletion class.

    We cover the following cases:

    - LRC completes with expected result code
    - LRC completes with unexpected result code
    - LRC event has invalid format
    - LRC ID is not set and any ID is accepted
    - LRC result code is set as none and any result code is accepted
    - LRC accepts multiple expected result codes
    - LRC ID is set but the event has a different ID
    """

    @staticmethod
    def test_lrc_completes_with_expected_result_code():
        """Passes if LRC completes with expected result code."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc123", '[0, "Success"]'),
        )
        assertion.verify()

    @staticmethod
    def test_lrc_completes_with_unexpected_result_code():
        """Fails if LRC completes with unexpected result code."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc123", '[1, "Failure"]'),
        )

        with pytest.raises(AssertionError):
            assertion.verify()

    @staticmethod
    def test_lrc_event_has_invalid_format():
        """Fails if LRC event has invalid format."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        for attr_name, value in [
            ("longRunningCommandResult", "invalid"),
            ("longRunningCommandResult", ("lrc123", "invalid")),
            ("longRunningCommandResult", ("lrc123", '["invalid"]')),
        ]:
            add_event(assertion.tracer, "test/device/1", attr_name, value)

        with pytest.raises(AssertionError):
            assertion.verify()

    @staticmethod
    def test_lrc_id_not_set_and_any_id_accepted():
        """Passes if LRC ID is not set and any ID is accepted."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc123", '[0, "Success"]'),
        )
        assertion.verify()

    @staticmethod
    def test_lrc_result_code_not_set_and_any_result_code_accepted():
        """
        Passes if LRC result code is not set and any result code is accepted.
        """
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, None)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc123", '[4, "UNKNOWN"]'),
        )
        assertion.verify()

    @staticmethod
    def test_lrc_accepts_multiple_expected_result_codes():
        """Passes if LRC accepts multiple expected result codes."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(
            device, [ResultCode.OK, ResultCode.FAILED]
        )
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc123", '[3, "Failure"]'),
        )
        assertion.verify()

    @staticmethod
    def test_lrc_id_is_set_but_event_has_different_id():
        """Fails if LRC ID is set but the event has a different ID."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            "test/device/1",
            "longRunningCommandResult",
            ("lrc456", '[0, "Success"]'),
        )

        with pytest.raises(AssertionError):
            assertion.verify()
