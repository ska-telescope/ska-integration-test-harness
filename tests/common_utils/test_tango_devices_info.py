"""Unit tests for DevicesInfoProvider class and its utilities."""

from unittest.mock import patch

import pytest
import requests
from assertpy import assert_that

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
    DevicesInfoServiceException,
)
from tests.common_utils.utils import inject_device_info


class TestDevicesInfoProvider:
    """Unit tests for DevicesInfoProvider class."""

    def test_get_device_recap_returns_correct_recap(self):
        """Returns a correct recap for an existing device."""
        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        inject_device_info(devices_info_provider, "tango/device/1", "1.0.0")
        inject_device_info(devices_info_provider, "tango/device/2", None)

        recap_device1 = devices_info_provider.get_device_recap(
            "tango/device/1"
        )
        recap_device2 = devices_info_provider.get_device_recap(
            "tango/device/2"
        )
        recap_device3 = devices_info_provider.get_device_recap(
            "tango/device/3"
        )

        assert_that(recap_device1).is_equal_to(
            "tango/device/1 (version: 1.0.0)"
        )
        assert_that(recap_device2).is_equal_to(
            "tango/device/2 (version: not available)"
        )
        assert_that(recap_device3).contains(
            "tango/device/3 (not found among the "
            "k8s-config-exporter devices information)"
        )

    @patch("requests.get")
    def test_update_calls_expected_url(self, mock_get):
        """Calls the expected URL to update devices information."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {"device_versionId": "1.0.0"}},
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        devices_info_provider = DevicesInfoProvider(
            kube_namespace="dummy-namespace"
        )
        devices_info_provider.update()

        mock_get.assert_called_once_with(
            "http://ska-k8s-config-exporter-service.dummy-namespace"
            ":8080/tango_devices",
            timeout=10,
        )

    @patch("requests.get")
    def test_update_populates_devices_info_with_versions(self, mock_get):
        """Populates DevicesInfoProvider with devices having versions."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {"device_versionId": "1.0.0"}},
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        devices_info_provider.update()

        assert_that(
            devices_info_provider.get_device_recap("tango/device/1")
        ).is_equal_to("tango/device/1 (version: 1.0.0)")
        assert_that(
            devices_info_provider.get_device_recap("tango/device/2")
        ).is_equal_to("tango/device/2 (version: 2.0.0)")

    @patch("requests.get")
    def test_update_handles_missing_versions(self, mock_get):
        """Populates device info with devices having missing versions."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {}},  # No version provided
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        devices_info_provider.update()

        assert_that(
            devices_info_provider.get_device_recap("tango/device/1")
        ).is_equal_to("tango/device/1 (version: not available)")
        assert_that(
            devices_info_provider.get_device_recap("tango/device/2")
        ).is_equal_to("tango/device/2 (version: 2.0.0)")

    @patch("requests.get")
    def test_update_raises_exception_on_service_unavailability(self, mock_get):
        """Raises DevicesInfoServiceException when service is down."""
        mock_get.side_effect = requests.exceptions.RequestException()

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")

        with pytest.raises(DevicesInfoServiceException) as exc_info:
            devices_info_provider.update()

        assert_that(str(exc_info.value)).contains("Error when interrogating")

    @patch("requests.get")
    def test_update_raises_exception_on_invalid_json(self, mock_get):
        """Raises DevicesInfoServiceException on invalid JSON response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError()

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")

        with pytest.raises(DevicesInfoServiceException) as exc_info:
            devices_info_provider.update()

        assert_that(str(exc_info.value)).contains("invalid JSON data")

    @patch("requests.get")
    def test_update_raises_exception_on_invalid_device_info(self, mock_get):
        """Raises exception when returned data has not the expected format."""
        json_response = {
            "tango_devices_info": None  # Invalid tango_devices_info
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")

        with pytest.raises(DevicesInfoServiceException) as exc_info:
            devices_info_provider.update()

        assert_that(str(exc_info.value)).contains("does not contain")

    @patch("requests.get")
    def test_update_handles_empty_device_info(self, mock_get):
        """Handles empty tango_devices_info gracefully."""
        json_response = {"tango_devices_info": {}}
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        devices_info_provider = DevicesInfoProvider(kube_namespace="namespace")
        devices_info_provider.update()

        recap = devices_info_provider.get_device_recap("tango/device/1")
        assert_that(recap).contains("tango/device/1 (not found among the")
