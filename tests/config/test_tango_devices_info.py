"""Unit tests for TelescopeDevicesInfo class."""

from unittest.mock import patch

import pytest
import requests
from assertpy import assert_that

from ska_integration_test_harness.config.tango_devices_info import (
    DevicesInfoNotAvailableException,
    MissingTangoDeviceException,
    TangoDeviceInfo,
    TelescopeDevicesInfo,
)


class TestTelescopeDevicesInfo:
    """Tests for TelescopeDevicesInfo class using public methods."""

    def test_get_version_returns_version_when_device_exists(self):
        """Returns version when the device exists in collection."""
        devices = [
            TangoDeviceInfo(name="device1", version="1.0.0"),
            TangoDeviceInfo(name="device2", version="2.0.0"),
        ]
        telescope_devices_info = TelescopeDevicesInfo(devices)

        version = telescope_devices_info.get_version("device1")

        assert_that(version).is_equal_to("1.0.0")

    def test_get_version_raises_exception_when_device_does_not_exist(self):
        """Raises MissingTangoDeviceException when device not found."""
        devices = [TangoDeviceInfo(name="device1", version="1.0.0")]
        telescope_devices_info = TelescopeDevicesInfo(devices)

        with pytest.raises(MissingTangoDeviceException) as exc_info:
            telescope_devices_info.get_version("device2")

        assert_that(str(exc_info.value)).contains("device2")

    @patch("requests.get")
    def test_read_from_ska_k8s_calls_expected_url(self, mock_get):
        """Calls the expected URL to get devices information."""
        json_response = {
            "tango_devices_info": {
                "device1": {"info": {"device_versionId": "1.0.0"}},
                "device2": {"info": {"device_versionId": "2.0.0"}},
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
                "device1": {"info": {"device_versionId": "1.0.0"}},
                "device2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        result = TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace"
        )

        assert_that(result.get_version("device1")).is_equal_to("1.0.0")
        assert_that(result.get_version("device2")).is_equal_to("2.0.0")

    @patch("requests.get")
    def test_read_from_ska_k8s_returns_devices_info_with_missing_versions(
        self, mock_get
    ):
        """Populates device info with devices having missing versions."""
        json_response = {
            "tango_devices_info": {
                "device1": {"info": {}},  # No version provided
                "device2": {"info": {"device_versionId": "2.0.0"}},
            }
        }
        mock_get.return_value.json.return_value = json_response
        mock_get.return_value.status_code = 200

        result = TelescopeDevicesInfo.read_from_ska_k8s_config_exporter(
            kube_namespace="namespace"
        )

        assert_that(result.get_version("device1")).is_none()
        assert_that(result.get_version("device2")).is_equal_to("2.0.0")

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
            result.get_version("device1")
