"""Unit tests on the telescope wrapper class."""

from unittest.mock import MagicMock, patch

import pytest
import tango
from assertpy import assert_that

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
    DevicesInfoServiceException,
)
from ska_integration_test_harness.emulated.dishes_wrapper import (
    EmulatedDishesWrapper,
)
from ska_integration_test_harness.emulated.sdp_wrapper import (
    EmulatedSDPWrapper,
)
from ska_integration_test_harness.production.csp_wrapper import (
    ProductionCSPWrapper,
)
from ska_integration_test_harness.production.tmc_wrapper import (
    ProductionTMCWrapper,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)
from tests.actions.utils.mock_device_proxy import create_device_proxy_mock


class MockProductionTMCWrapper(ProductionTMCWrapper):
    """Mock implementation of ProductionTMCWrapper for testing."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self) -> None:
        """Init does nothing."""
        # pylint: disable=super-init-not-called
        self.central_node = create_device_proxy_mock(
            "ska_mid/tm_central/central_node"
        )
        self.subarray_node = create_device_proxy_mock(
            "ska_mid/tm_subarray_node/1"
        )
        self.csp_master_leaf_node = create_device_proxy_mock(
            "ska_mid/tm_leaf_node/csp_master"
        )
        self.sdp_master_leaf_node = create_device_proxy_mock(
            "ska_mid/tm_leaf_node/sdp_master"
        )
        self.dish_leaf_node_list = [
            create_device_proxy_mock("ska_mid/tm_leaf_node/dish_1"),
            create_device_proxy_mock("ska_mid/tm_leaf_node/dish_2"),
            create_device_proxy_mock("ska_mid/tm_leaf_node/dish_3"),
            create_device_proxy_mock("ska_mid/tm_leaf_node/dish_4"),
        ]
        self.csp_subarray_leaf_node = None
        self.sdp_subarray_leaf_node = None
        self._config = MagicMock()
        self._config.supports_mid.return_value = True


class MockEmulatedSDPWrapper(EmulatedSDPWrapper):
    """Mock implementation of EmulatedSDPWrapper for testing."""

    def __init__(self) -> None:
        """Init does nothing."""
        # pylint: disable=super-init-not-called
        self.sdp_master = create_device_proxy_mock("mid-sdp/control/0")
        self.sdp_subarray = create_device_proxy_mock("mid-sdp/subarray/1")


class MockProductionCSPWrapper(ProductionCSPWrapper):
    """Mock implementation of ProductionCSPWrapper for testing."""

    def __init__(self) -> None:
        """Init does nothing."""
        # pylint: disable=super-init-not-called
        self.csp_master = create_device_proxy_mock("mid-csp/elt/master")
        self.csp_subarray = create_device_proxy_mock("mid-csp/elt/subarray_1")


class MockEmulatedDishesWrapper(EmulatedDishesWrapper):
    """Mock implementation of EmulatedDishesWrapper for testing."""

    def __init__(self) -> None:
        """Init does nothing."""
        # pylint: disable=super-init-not-called
        self.dish_master_dict = {
            "dish_001": MagicMock(spec=tango.DeviceProxy),
            "dish_036": MagicMock(spec=tango.DeviceProxy),
            "dish_063": MagicMock(spec=tango.DeviceProxy),
            "dish_100": MagicMock(spec=tango.DeviceProxy),
        }
        self.dish1_admin_dev_name = "dish_001_admin"
        self.dish1_admin_dev_proxy = MagicMock(spec=tango.DeviceProxy)
        self.dish1_admin_dev_proxy.dev_name.return_value = (
            self.dish1_admin_dev_name
        )
        self.dish_master_dict["dish_001"].dev_name.return_value = (
            "ska001/elt/master"
        )
        self.dish_master_dict["dish_036"].dev_name.return_value = (
            "ska036/elt/master"
        )
        self.dish_master_dict["dish_063"].dev_name.return_value = (
            "ska063/elt/master"
        )
        self.dish_master_dict["dish_100"].dev_name.return_value = (
            "ska100/elt/master"
        )


class TestTelescopeWrapper:
    """Unit tests for the TelescopeWrapper class.

    Test a few base mechanics of the telescope wrapper as the test harness
    access point. We don't test instead anything related to the actual
    interaction with the telescope (since there is no actual telescope
    available in this test environment).
    """

    @pytest.fixture(autouse=True)
    def telescope_wrapper_is_not_yet_defined(self):
        """Ensure the telescope wrapper is not yet defined."""
        TelescopeWrapper._instance = None  # pylint: disable=protected-access

    @staticmethod
    def create_subsystems():
        """Create an instance for each subsystem, mocking __init__.

        :return: A production TMC wrapper, an emulated SDP wrapper,
            A production CSP wrapper, and an emulated Dishes wrapper
            (all opportunely mocked).
        """

        tmc = MockProductionTMCWrapper()
        sdp = MockEmulatedSDPWrapper()
        csp = MockProductionCSPWrapper()
        dishes = MockEmulatedDishesWrapper()

        return tmc, sdp, csp, dishes

    # -----------------------------------------------------------------------
    # Setup tests

    def test_telescope_wrapper_exposes_setup_subsystems(self):
        """The telescope wrapper exposes the setup subsystems."""
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()

        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )

        assert_that(telescope.tmc).is_equal_to(tmc)
        assert_that(telescope.sdp).is_equal_to(sdp)
        assert_that(telescope.csp).is_equal_to(csp)
        assert_that(telescope.dishes).is_equal_to(dishes)

    @staticmethod
    def test_telescope_wrapper_fails_if_not_set_up():
        """The telescope wrapper fails if not set up."""
        telescope = TelescopeWrapper()
        tmc, _, _, _ = TestTelescopeWrapper.create_subsystems()
        telescope._tmc = tmc  # pylint: disable=protected-access

        with pytest.raises(ValueError) as exc_info:
            telescope.fail_if_not_set_up()

        assert_that(str(exc_info.value)).described_as(
            "TMC is expected to be set up, but not SDP, CSP, and Dishes."
        ).contains("SDP=None", "CSP=None", "Dishes=None").does_not_contain(
            "TMC=None"
        )

        with pytest.raises(ValueError):
            _ = telescope.sdp

        with pytest.raises(ValueError):
            _ = telescope.csp

        with pytest.raises(ValueError):
            _ = telescope.dishes

    # -----------------------------------------------------------------------
    # Singleton status tests

    @staticmethod
    def test_telescope_wrapper_is_a_singleton():
        """When creating a second instance, it returns the same subsystems."""
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = TestTelescopeWrapper.create_subsystems()

        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )

        telescope2 = TelescopeWrapper()

        assert_that(telescope2.tmc).is_equal_to(tmc)
        assert_that(telescope2.sdp).is_equal_to(sdp)
        assert_that(telescope2.csp).is_equal_to(csp)
        assert_that(telescope2.dishes).is_equal_to(dishes)

    # -----------------------------------------------------------------------
    # Subsystems recap tests

    def test_subsystems_recap_recaps_all_subsystems(self):
        """The telescope wrapper exposes the subsystems recap."""
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()
        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )

        recap = telescope.get_subsystems_recap()

        assert_that(recap).described_as(
            "The recap contains the (set) subsystems and emulated status."
        ).contains(
            "TMC (production)",
            "SDP (emulated)",
            "CSP (production)",
            "Dishes (emulated)",
        )

    def test_subsystems_recap_handles_no_subsystems_set_up(self):
        """The recap contains a message when no subsystems are set up."""
        telescope = TelescopeWrapper()

        recap = telescope.get_subsystems_recap()

        assert_that(recap).described_as(
            "The recap contains no subsystem when not set up."
        ).contains(
            "No subsystems are currently set up.",
        ).does_not_contain(
            "TMC",
            "SDP",
            "CSP",
            "Dishes",
        )

    def _mock_devices_info_provider(self) -> MagicMock:
        """Mock a devices info provider with a get_recap method.

        :return: A devices info provider mocked instance.
        """
        devices_info_provider = MagicMock(spec=DevicesInfoProvider)

        def get_recap(dev_name):
            """Return a mock recap for the given device name."""
            return f"{dev_name} (mock recap)"

        devices_info_provider.get_device_recap = get_recap
        return devices_info_provider

    def test_subsystems_recap_when_devices_info_is_set_calls_update(self):
        """When the devices info is set, it is updated and used for recaps."""
        # setup a telescope with subsystems and a devices info provider
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()
        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )
        telescope.devices_info_provider = self._mock_devices_info_provider()

        # get the recap
        recap = telescope.get_subsystems_recap(update_devices_info=True)

        # the recap method called for an update and
        # generates the expected result
        telescope.devices_info_provider.update.assert_called_once()
        assert_that(recap).described_as(
            "The devices info provider is updated and used for recaps."
        ).contains(
            "- central_node: ska_mid/tm_central/central_node (mock recap)",
            "- subarray_node: ska_mid/tm_subarray_node/1 (mock recap)",
            "- sdp_master: mid-sdp/control/0 (mock recap)",
            "- csp_master: mid-csp/elt/master (mock recap)",
            "- dish_001: ska001/elt/master (mock recap)",
        ).described_as(
            "Not initialised TMC devices are included with special flag."
        ).contains(
            "- csp_subarray_leaf_node: not yet set",
            "- sdp_subarray_leaf_node: not yet set",
        )

    def test_subsystems_recap_does_not_call_update_if_specified(self):
        """When the devices info is set, you can specify not to update it."""
        # setup a telescope with subsystems and a devices info provider
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()
        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )
        telescope.devices_info_provider = self._mock_devices_info_provider()

        # get the recap
        recap = telescope.get_subsystems_recap(update_devices_info=False)

        # the recap method did not call for an update
        telescope.devices_info_provider.update.assert_not_called()
        assert_that(recap).described_as(
            "The devices info provider is not updated when specified."
        ).contains(
            "- central_node: ska_mid/tm_central/central_node (mock recap)",
            "- csp_master: mid-csp/elt/master (mock recap)",
        )

    def test_subsystems_recap_handles_gently_info_provider_update_fail(self):
        """If the devices info provider update fails, it is handled gently."""
        # setup a telescope with subsystems and a devices info provider
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()
        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )
        telescope.devices_info_provider = self._mock_devices_info_provider()
        # pylint: disable=line-too-long # noqa: E501
        telescope.devices_info_provider.update.side_effect = (
            DevicesInfoServiceException("Mock update failed")
        )

        # get the recap
        recap = telescope.get_subsystems_recap(update_devices_info=True)

        # the recap method called for an update and
        # generates the expected result
        telescope.devices_info_provider.update.assert_called_once()
        assert_that(recap).described_as(
            "The devices info provider is updated and used for recaps."
        ).contains(
            "- central_node: ska_mid/tm_central/central_node (mock recap)",
            "- csp_master: mid-csp/elt/master (mock recap)",
        ).contains(
            "Devices info provider update failed",
        )

    # -----------------------------------------------------------------------
    # Set subarray ID

    def test_telescope_wrapper_set_subarray_id_initialises_subarray_devices(
        self,
    ):
        """The set_subarray_id method initialises the subarray devices."""
        telescope = TelescopeWrapper()
        tmc, sdp, csp, dishes = self.create_subsystems()
        telescope.set_up(
            tmc=tmc,
            sdp=sdp,
            csp=csp,
            dishes=dishes,
        )

        assert_that(telescope.tmc.csp_subarray_leaf_node).described_as(
            "FAILED ASSUMPTION: CSP subarray leaf node is not set."
        ).is_none()
        assert_that(telescope.tmc.sdp_subarray_leaf_node).described_as(
            "FAILED ASSUMPTION: SDP subarray leaf node is not set."
        ).is_none()

        with patch("tango.DeviceProxy") as mock_device_proxy:
            telescope.set_subarray_id(1)

        # The subarray devices are called with the expected names
        mock_device_proxy.assert_any_call("ska_mid/tm_subarray_node/1")
        mock_device_proxy.assert_any_call(
            "ska_mid/tm_leaf_node/csp_subarray01"
        )
        mock_device_proxy.assert_any_call(
            "ska_mid/tm_leaf_node/sdp_subarray01"
        )
        mock_device_proxy.assert_any_call("mid-sdp/subarray/01")
        mock_device_proxy.assert_any_call("mid-csp/subarray/01")

        # The subarray devices are set to the expected values
        assert_that(telescope.tmc.csp_subarray_leaf_node).described_as(
            "The CSP subarray leaf node is set."
        ).is_not_none().is_equal_to(mock_device_proxy.return_value)
        assert_that(telescope.tmc.sdp_subarray_leaf_node).described_as(
            "The SDP subarray leaf node is set."
        ).is_not_none().is_equal_to(mock_device_proxy.return_value)
        assert_that(telescope.tmc.subarray_node).described_as(
            "The subarray node is expected to change."
        ).is_equal_to(mock_device_proxy.return_value)
        assert_that(telescope.csp.csp_subarray).described_as(
            "The CSP subarray is expected to change."
        ).is_equal_to(mock_device_proxy.return_value)
        assert_that(telescope.sdp.sdp_subarray).described_as(
            "The SDP subarray is expected to change."
        ).is_equal_to(mock_device_proxy.return_value)
