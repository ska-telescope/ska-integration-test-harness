"""Unit tests for TestHarnessFactory."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.config.reader.yaml_config_reader import (
    YAMLConfigurationReader,
)
from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)
from ska_integration_test_harness.emulated.csp_devices import (
    EmulatedCSPDevices,
)
from ska_integration_test_harness.emulated.dishes_devices import (
    EmulatedDishesDevices,
)
from ska_integration_test_harness.emulated.sdp_devices import (
    EmulatedSDPDevices,
)
from ska_integration_test_harness.init.test_harness_factory import (
    TestHarnessFactory,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.production.csp_devices import (
    ProductionCSPDevices,
)
from ska_integration_test_harness.production.dishes_devices import (
    ProductionDishesDevices,
)
from ska_integration_test_harness.production.sdp_devices import (
    ProductionSDPDevices,
)
from ska_integration_test_harness.production.tmc_devices import (
    ProductionTMCDevices,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TestTestHarnessFactory:
    """Tests for TestHarnessFactory"""

    CONFIG_DATA_DIR = "tests/config_examples"

    @pytest.fixture
    def config(self) -> TestHarnessConfiguration:
        """Read a valid configuration for the test harness."""
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(
            f"{self.CONFIG_DATA_DIR}/valid_test_harness_config.yaml"
        )
        return reader.get_test_harness_configuration()

    def test_create_tmc_wrapper_with_production_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates a production TMC wrapper with correct config"""
        config.tmc_config.is_emulated = False
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            tmc_wrapper = factory.create_tmc_wrapper()

        assert_that(tmc_wrapper).is_instance_of(ProductionTMCDevices)
        mock_device_proxy.assert_called()

    def test_create_csp_wrapper_with_emulated_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates an emulated CSP wrapper with correct config"""
        config.csp_config.is_emulated = True
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            csp_wrapper = factory.create_csp_wrapper()

        assert_that(csp_wrapper).is_instance_of(EmulatedCSPDevices)
        mock_device_proxy.assert_called()  # Emulated should call DeviceProxy

    def test_create_csp_wrapper_with_production_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates a production CSP wrapper with correct config"""
        config.csp_config.is_emulated = False
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            csp_wrapper = factory.create_csp_wrapper()

        assert_that(csp_wrapper).is_instance_of(ProductionCSPDevices)
        mock_device_proxy.assert_called()

    def test_create_sdp_wrapper_with_emulated_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates an emulated SDP wrapper with correct config"""
        config.sdp_config.is_emulated = True
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            sdp_wrapper = factory.create_sdp_wrapper()

        assert_that(sdp_wrapper).is_instance_of(EmulatedSDPDevices)
        mock_device_proxy.assert_called()  # Emulated should call DeviceProxy

    def test_create_sdp_wrapper_with_production_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates a production SDP wrapper with correct config"""
        config.sdp_config.is_emulated = False
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            sdp_wrapper = factory.create_sdp_wrapper()

        assert_that(sdp_wrapper).is_instance_of(ProductionSDPDevices)
        mock_device_proxy.assert_called()

    def test_create_dishes_wrapper_with_emulated_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates an emulated Dishes wrapper with correct config"""
        config.dishes_config.is_emulated = True
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch("tango.DeviceProxy", MagicMock()) as mock_device_proxy:
            dishes_wrapper = factory.create_dishes_wrapper()

        assert_that(dishes_wrapper).is_instance_of(EmulatedDishesDevices)
        mock_device_proxy.assert_called()  # Emulated should call DeviceProxy

    @staticmethod
    def _decorate_config_for_production_dishes(
        config: TestHarnessConfiguration,
    ):
        """Decorates the config with production dishes config"""
        config.dishes_config.is_emulated = False
        config.dishes_config.dish_master1_name = "tango://tango-databaseds.dish-lmc-1.svc.cluster.local:10000/mid-dish/dish-manager/SKA001"  # pylint: disable=line-too-long # noqa: E501
        config.dishes_config.dish_master2_name = "tango://tango-databaseds.dish-lmc-2.svc.cluster.local:10000/mid-dish/dish-manager/SKA036"  # pylint: disable=line-too-long # noqa: E501
        config.dishes_config.dish_master3_name = "tango://tango-databaseds.dish-lmc-3.svc.cluster.local:10000/mid-dish/dish-manager/SKA063"  # pylint: disable=line-too-long # noqa: E501
        config.dishes_config.dish_master4_name = "tango://tango-databaseds.dish-lmc-4.svc.cluster.local:10000/mid-dish/dish-manager/SKA100"  # pylint: disable=line-too-long # noqa: E501

    def test_create_dishes_wrapper_with_production_config(
        self, config: TestHarnessConfiguration
    ):
        """Creates a production Dishes wrapper with correct config"""
        self._decorate_config_for_production_dishes(config)
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch(
            "tango.DeviceProxy", MagicMock()
        ) as mock_device_proxy, patch("tango.db.Database", MagicMock()):
            dishes_wrapper = factory.create_dishes_wrapper()

        assert_that(dishes_wrapper).is_instance_of(ProductionDishesDevices)
        mock_device_proxy.assert_called()

    def test_create_telescope_wrapper(self, config: TestHarnessConfiguration):
        """Creates a telescope wrapper set up for TMC-CSP MID testing.

        The call is expected to create a TelescopeWrapper with:
        - production TMC and CSP
        - emulated SDP and Dishes
        """
        inputs = TestHarnessInputs()
        factory = TestHarnessFactory(config, inputs)

        with patch(
            "tango.DeviceProxy", MagicMock()
        ) as mock_device_proxy, patch("tango.db.Database", MagicMock()):
            telescope_wrapper = factory.create_telescope_wrapper()

        assert_that(telescope_wrapper).is_instance_of(TelescopeWrapper)
        assert_that(telescope_wrapper.tmc).is_instance_of(ProductionTMCDevices)
        assert_that(telescope_wrapper.csp).is_instance_of(ProductionCSPDevices)
        assert_that(telescope_wrapper.sdp).is_instance_of(EmulatedSDPDevices)
        assert_that(telescope_wrapper.dishes).is_instance_of(
            EmulatedDishesDevices
        )
        mock_device_proxy.assert_called()

        # Telescope is set up and it is not expected to fail when
        # calling this method
        telescope_wrapper.fail_if_not_set_up()
