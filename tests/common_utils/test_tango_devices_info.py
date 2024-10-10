"""Unit tests for TelescopeDevicesInfo class."""

from unittest.mock import patch

import pytest
import requests
from assertpy import assert_that

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoNotAvailableException,
    MissingTangoDeviceException,
    TangoDeviceInfo,
    TelescopeDevicesInfo,
)


class TestTelescopeDevicesInfo:
    """Unit tests for TelescopeDevicesInfo class."""

    def test_get_device_info_returns_info_when_device_exists(self):
        """Returns device info when the device exists in the collection."""
        devices = [
            TangoDeviceInfo(name="tango/device/1", version="1.0.0"),
            TangoDeviceInfo(name="tango/device/2", version="2.0.0"),
        ]
        telescope_devices_info = TelescopeDevicesInfo(devices)

        device_info = telescope_devices_info.get_device_info("tango/device/1")

        assert_that(device_info.name).is_equal_to("tango/device/1")
        assert_that(device_info.version).is_equal_to("1.0.0")

    def test_get_device_info_raises_exception_when_device_does_not_exist(self):
        """Raises MissingTangoDeviceException when device not found."""
        devices = [TangoDeviceInfo(name="tango/device/1", version="1.0.0")]
        telescope_devices_info = TelescopeDevicesInfo(devices)

        with pytest.raises(MissingTangoDeviceException) as exc_info:
            telescope_devices_info.get_device_info("tango/device/2")

        assert_that(str(exc_info.value)).contains("tango/device/2")

    def test_get_device_recap_returns_correct_recap(self):
        """Returns a correct recap for an existing device."""
        devices = [
            TangoDeviceInfo(name="tango/device/1", version="1.0.0"),
            TangoDeviceInfo(name="tango/device/2", version=None),
        ]
        telescope_devices_info = TelescopeDevicesInfo(devices)

        recap_device1 = telescope_devices_info.get_device_recap(
            "tango/device/1"
        )
        recap_device2 = telescope_devices_info.get_device_recap(
            "tango/device/2"
        )
        recap_device3 = telescope_devices_info.get_device_recap(
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
    def test_read_from_ska_k8s_calls_expected_url(self, mock_get):
        """Calls the expected URL to get devices information."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {"device_versionId": "1.0.0"}},
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200
        TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace",
            service_name="ska-k8s-config-exporter",
            port=8080,
            path="tango_devices",
        )
        mock_get.assert_called_once_with(
            "http://ska-k8s-config-exporter.namespace:8080/tango_devices",
            timeout=10,
        )

    @patch("requests.get")
    def test_read_from_ska_k8s_returns_devices_info_with_versions(
        self, mock_get
    ):
        """Populates TelescopeDevicesInfo with devices having versions."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {"device_versionId": "1.0.0"}},
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        result = TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace"
        )

        assert_that(
            result.get_device_info("tango/device/1").version
        ).is_equal_to("1.0.0")
        assert_that(
            result.get_device_info("tango/device/2").version
        ).is_equal_to("2.0.0")

    @patch("requests.get")
    def test_read_from_ska_k8s_returns_devices_info_with_missing_versions(
        self, mock_get
    ):
        """Populates device info with devices having missing versions."""
        json_response = {
            "tango_devices_info": {
                "tango/device/1": {"info": {}},  # No version provided
                "tango/device/2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        result = TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace"
        )

        assert_that(result.get_device_info("tango/device/1").version).is_none()
        assert_that(
            result.get_device_info("tango/device/2").version
        ).is_equal_to("2.0.0")

    @patch("requests.get")
    def test_read_from_ska_k8s_raises_exception_on_service_unavailability(
        self, mock_get
    ):
        """Raises DevicesInfoNotAvailableException when service is down."""
        mock_get.side_effect = requests.exceptions.RequestException()

        with pytest.raises(DevicesInfoNotAvailableException) as exc_info:
            TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
                kube_namespace="namespace"
            )

        assert_that(str(exc_info.value)).contains("information not available")

    @patch("requests.get")
    def test_read_from_ska_k8s_raises_exception_on_invalid_json(
        self, mock_get
    ):
        """Raises DevicesInfoNotAvailableException on invalid JSON response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError()

        with pytest.raises(DevicesInfoNotAvailableException) as exc_info:
            TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
                kube_namespace="namespace"
            )

        assert_that(str(exc_info.value)).contains("invalid JSON data")

    @patch("requests.get")
    def test_read_from_ska_k8s_raises_exception_on_invalid_device_info(
        self, mock_get
    ):
        """Raises exception when tango_devices_info is not a dictionary."""
        json_response = {
            "tango_devices_info": None  # Invalid tango_devices_info
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        with pytest.raises(DevicesInfoNotAvailableException) as exc_info:
            TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
                kube_namespace="namespace"
            )

        assert_that(str(exc_info.value)).contains("does not contain")

    @patch("requests.get")
    def test_read_from_ska_k8s_handles_empty_device_info(self, mock_get):
        """Handles empty tango_devices_info gracefully."""
        json_response = {"tango_devices_info": {}}
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        result = TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace"
        )

        with pytest.raises(MissingTangoDeviceException):
            result.get_device_info("tango/device/1")
