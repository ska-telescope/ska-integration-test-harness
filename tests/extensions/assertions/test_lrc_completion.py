"""Unit tests for the AssertLRCCompletion class."""

import pytest
from assertpy import assert_that
from ska_control_model import ResultCode

from ska_integration_test_harness.extensions.assertions.lrc_completion import (
    AssertLRCCompletion,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock
from tests.actions.utils.mock_event_tracer import add_event


@pytest.mark.extensions
class TestAssertLRCCompletion:
    """Unit tests for the AssertLRCCompletion class.

    We cover the following cases:

    - LRC ID is not set
    - LRC completes with expected result code
    - LRC completes with unexpected result code
    - LRC event has invalid format
    """

    @staticmethod
    def test_lrc_id_not_set_raises_value_error():
        """Raises ValueError if LRC ID is not set."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()

        with pytest.raises(ValueError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).contains("No LRC ID to monitor")

    @staticmethod
    def test_lrc_completes_with_expected_result_code():
        """Passes if LRC completes with expected result code."""
        device = create_device_proxy_mock("test/device/1")
        assertion = AssertLRCCompletion(device, ResultCode.OK)
        assertion.setup()
        assertion.monitor_lrc("lrc123")

        add_event(
            assertion.tracer,
            device,
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
            device,
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
            add_event(assertion.tracer, device, attr_name, value)

        with pytest.raises(AssertionError):
            assertion.verify()
