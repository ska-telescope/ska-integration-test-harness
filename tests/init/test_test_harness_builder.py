"""Unit tests for TestHarnessBuilder."""

from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
)
from ska_integration_test_harness.init.test_harness_builder import (
    TestHarnessBuilder,
)
from ska_integration_test_harness.inputs.json_input import (
    JSONInput,
    StrJSONInput,
)
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TestTestHarnessBuilder:
    """Unit tests for TestHarnessBuilder.

    Since this is a particularly critical component, we test it minimising
    the use of mocks and patches. We use them only when strictly necessary
    (e.g., Tango API). The used configurations are realistic ones, taken
    from TMC-CSP Mid integration tests. The passed input instead are JSON,
    but not semantically meaningful (it doesn't matter for the tests,
    since they will be needed only in teardown procedures or similar).
    """

    # pylint: disable=too-many-public-methods

    @pytest.fixture(autouse=True)
    def telescope_wrapper_is_not_yet_defined(self):
        """Ensure the telescope wrapper is not yet defined."""
        TelescopeWrapper._instance = None  # pylint: disable=protected-access

    CONFIG_DATA_DIR = "tests/config_examples"

    @pytest.fixture
    def config_file(self) -> str:
        """Create a path to a valid configuration file."""
        return f"{self.CONFIG_DATA_DIR}/valid_test_harness_config.yaml"

    @pytest.fixture
    def missing_section_config_file(self) -> str:
        """Create a path to a configuration file with a missing section."""
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_section.yaml"

    @pytest.fixture
    def missing_key_config_file(self) -> str:
        """Create a path to a configuration file with a missing key."""
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_centralnode_name.yaml"

    @pytest.fixture
    def valid_low_config_file(self) -> str:
        """Create a path to a valid low configuration file."""
        return f"{self.CONFIG_DATA_DIR}/valid_test_harness_config_low.yaml"

    @pytest.fixture
    def missing_mccs_config_file(self) -> str:
        """Create a path to a configuration file with missing MCCS config."""
        return f"{self.CONFIG_DATA_DIR}/missing_mccs_low.yaml"

    @pytest.fixture
    def valid_json_input(self) -> JSONInput:
        """Create an example of valid JSON input."""
        return StrJSONInput('{"key": "value"}')

    @pytest.fixture
    def invalid_json_input(self) -> JSONInput:
        """Create an example of invalid JSON input."""
        return StrJSONInput('{"key": "value"')

    # -------------------------------------------------------------------------
    # Test configuration collection procedures

    def test_validate_config_with_valid_file_terminates_successfully(
        self, config_file: str
    ):
        """When a valid configuration file is passed, the validation succeeds.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder()

        builder.read_config_file(config_file)

        with patch("tango.DeviceProxy", MagicMock()):
            builder.validate_configurations()

        assert_that(builder.is_config_validated()).is_true()

    def test_validate_config_with_missing_section_raises_value_error(
        self, missing_section_config_file: str
    ):
        """When a config file misses a subsystem section,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.read_config_file(missing_section_config_file)

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    def test_validate_config_with_missing_key_raises_value_error(
        self, missing_key_config_file: str
    ):
        """When a config file misses a key in a subsystem section,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.read_config_file(missing_key_config_file)

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    def test_validate_config_with_no_config_raises_value_error(self):
        """When no configuration is set, the validation raises a ValueError."""
        builder = TestHarnessBuilder()
        assert_that(builder.is_config_validated()).is_false()

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    def test_validate_config_with_valid_low_config_terminates_successfully(
        self, valid_low_config_file: str
    ):
        """When a valid low configuration file is passed, validation succeeds.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder()

        builder.read_config_file(valid_low_config_file)

        with patch("tango.DeviceProxy", MagicMock()):
            builder.validate_configurations()

        assert_that(builder.is_config_validated()).is_true()

    def test_validate_config_low_with_missing_mccs_config_raises_value_error(
        self, missing_mccs_config_file: str
    ):
        """When a low config file misses the MCCS section,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.read_config_file(missing_mccs_config_file)

        with pytest.raises(ValueError):
            builder.validate_configurations()
        assert_that(builder.is_config_validated()).is_false()

    # -------------------------------------------------------------------------
    # Test input collection procedures

    def test_validate_input_with_valid_input_terminates_successfully(
        self, valid_json_input: JSONInput
    ):
        """When all default inputs are passed and they are valid,
        the validation succeeds.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )

        builder.validate_default_inputs()

        assert_that(builder.are_default_inputs_validated()).is_true()

    def test_validate_input_with_missing_value_raises_value_error(
        self, valid_json_input: JSONInput
    ):
        """When a default input is missing,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                # scan_input=valid_json_input
            )
        )

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated())

    def test_validate_input_with_invalid_input_raises_value_error(
        self, invalid_json_input: str
    ):
        """When a default input is invalid,
        the validation raises a ValueError."""
        builder = TestHarnessBuilder()

        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=invalid_json_input,
                assign_input=invalid_json_input,
                configure_input=invalid_json_input,
                release_input=invalid_json_input,
                scan_input=invalid_json_input,
            )
        )

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated()).is_false()

    def test_validate_input_with_no_input_raises_value_error(self):
        """When no default input is set, the validation raises a ValueError."""
        builder = TestHarnessBuilder()
        assert_that(builder.are_default_inputs_validated()).is_false()

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated()).is_false()

    def test_validate_input_without_default_vcc_is_successful_when_in_low(
        self, valid_json_input: JSONInput, valid_low_config_file: str
    ):
        """When in Low mode, the default VCC input is not required.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder().read_config_file(valid_low_config_file)

        builder.set_default_inputs(
            TestHarnessInputs(
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )

        builder.validate_default_inputs()

        assert_that(builder.are_default_inputs_validated()).is_true()

    def test_validate_default_vcc_is_required_in_mid_mode(
        self, valid_json_input: JSONInput, config_file: str
    ):
        """When in Mid mode, the default VCC input is required.

        (HAPPY PATH)
        """
        builder = TestHarnessBuilder().read_config_file(config_file)

        builder.set_default_inputs(
            TestHarnessInputs(
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )

        with pytest.raises(ValueError):
            builder.validate_default_inputs()
        assert_that(builder.are_default_inputs_validated()).is_false()

    # -------------------------------------------------------------------------
    # Test build method

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_valid_config_and_inputs_terminates_successfully(
        self, config_file: str, valid_json_input: JSONInput
    ):
        """HAPPY PATH: when the correct configs and inputs are passed,
        the build method completes successfully."""

        builder = TestHarnessBuilder()

        builder.read_config_file(config_file)
        builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        builder.validate_default_inputs()

        telescope_wrapper = builder.build()

        assert_that(telescope_wrapper).is_instance_of(TelescopeWrapper)
        telescope_wrapper.fail_if_not_set_up()

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_not_validated_but_config_and_input_logs_warning(
        self, config_file: str, valid_json_input: JSONInput
    ):
        """HAPPY PATH (but with warnings): when the correct configs and inputs
        are passed, the build method completes successfully. Since no explicit
        validation is done (and a logger is available), a warning is logged."""

        # patch method logging.getLogger to return MagicMock
        builder = TestHarnessBuilder()
        mock_logger = MagicMock()
        builder.logger = mock_logger

        builder.read_config_file(config_file)
        # builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        # builder.validate_default_inputs()
        telescope_wrapper = builder.build()

        assert_that(telescope_wrapper).is_instance_of(TelescopeWrapper)
        telescope_wrapper.fail_if_not_set_up()

        # check that the warnings were logged
        mock_logger.warning.assert_called()
        logger_warning_calls = mock_logger.warning.call_args_list
        assert_that(len(logger_warning_calls)).described_as(
            "Expected at least 2 warning logs, for missing validations"
        ).is_greater_than_or_equal_to(2)

        # (args[1] because of log.warning("PREFIX: %s", *args) signature)
        assert_that(logger_warning_calls[0].args[1]).described_as(
            "Expected warning for missing validation of configurations"
        ).contains_ignoring_case(
            "build", "test harness", "without validating", "configurations"
        )
        assert_that(logger_warning_calls[1].args[1]).described_as(
            "Expected warning for missing validation of default inputs"
        ).contains_ignoring_case(
            "build", "test harness", "without validating", "default inputs"
        )

    @patch("tango.DeviceProxy", MagicMock())
    @patch("tango.db.Database", MagicMock())
    def test_build_with_invalid_config_raises_some_error(
        self, missing_section_config_file: str
    ):
        """When an invalid configuration is passed, the build method is
        expected to fail. In this case, the failure is an attribute error
        (since the initialisation procedure will not be able to find
        a required attribute).
        """

        builder = TestHarnessBuilder()

        builder.read_config_file(missing_section_config_file)
        with pytest.raises(AttributeError):
            builder.build()

    @patch("tango.DeviceProxy")
    @patch("tango.db.Database", MagicMock())
    def test_build_logs_a_recap_of_subsystems_and_devices(
        self,
        mock_device_proxy: MagicMock,
        config_file: str,
        valid_json_input: JSONInput,
    ):
        """When the build method is called, a recap of the subsystems and
        devices is logged. This is useful for debugging purposes."""

        # patch method logging.getLogger to return MagicMock
        builder = TestHarnessBuilder()
        mock_logger = MagicMock()
        builder.logger = mock_logger
        mock_device_proxy.return_value = MagicMock()
        mock_device_proxy.return_value.dev_name.return_value = "mock/device/1"

        builder.read_config_file(config_file)
        builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        builder.validate_default_inputs()
        builder.build()

        mock_logger.info.assert_called()
        logger_info_calls = mock_logger.info.call_args_list
        assert_that(logger_info_calls[-1].args[1]).described_as(
            "Expected last log to contain the recap of subsystems"
        ).contains(
            "recap",
            "subsystems",
            "devices",
            "TMC (production). Devices:",
            "CSP (production). Devices:",
            "SDP (emulated). Devices:",
            "Dishes (emulated). Devices:",
            "- central_node: mock/device/1",
            "- sdp_master: mock/device/1",
            "- csp_master: mock/device/1",
            "- dish_001: mock/device/1",
        )

    @patch("tango.DeviceProxy")
    @patch("tango.db.Database", MagicMock())
    @patch(
        "ska_integration_test_harness.init."
        "test_harness_builder.DevicesInfoProvider"
    )
    def test_build_uses_devices_info_provider_if_kube_namespace_is_set(
        self,
        mock_devices_info_provider: MagicMock,
        mock_device_proxy: MagicMock,
        config_file: str,
        valid_json_input: JSONInput,
    ):
        """When the build method is called, it uses a DevicesInfoProvider
        to get the devices information. This is useful for debugging purposes.
        """

        # patch method logging.getLogger to return MagicMock
        builder = TestHarnessBuilder()
        mock_logger = MagicMock()
        builder.logger = mock_logger
        mock_device_proxy.return_value = MagicMock()
        mock_device_proxy.return_value.dev_name.return_value = "mock/device/1"
        dev_info_provider = MagicMock(spec=DevicesInfoProvider)
        dev_info_provider.get_device_recap = MagicMock()
        dev_info_provider.get_device_recap.return_value = (
            "mock/device/1 (mocked devices info recap)"
        )
        mock_devices_info_provider.return_value = dev_info_provider

        builder.set_kubernetes_namespace("mock kube namespace")
        builder.read_config_file(config_file)
        builder.validate_configurations()
        builder.set_default_inputs(
            TestHarnessInputs(
                default_vcc_config_input=valid_json_input,
                assign_input=valid_json_input,
                configure_input=valid_json_input,
                release_input=valid_json_input,
                scan_input=valid_json_input,
            )
        )
        builder.validate_default_inputs()
        telescope = builder.build()

        assert_that(telescope.devices_info_provider).described_as(
            "Expected the telescope wrapper to have a devices_info_provider"
        ).is_equal_to(dev_info_provider)
        mock_devices_info_provider.assert_called_with("mock kube namespace")
        dev_info_provider.update.assert_called()
        dev_info_provider.get_device_recap.assert_called_with("mock/device/1")
        logger_info_calls = mock_logger.info.call_args_list
        assert_that(logger_info_calls[-1].args[1]).described_as(
            "Expected last log to contain the recap of subsystems"
        ).contains(
            "- central_node: mock/device/1 (mocked devices info recap)",
            "- sdp_master: mock/device/1 (mocked devices info recap)",
            "- csp_master: mock/device/1 (mocked devices info recap)",
            "- dish_001: mock/device/1 (mocked devices info recap)",
        )
