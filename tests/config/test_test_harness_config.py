"""Unit tests for the TestHarnessConfiguration wrapper class."""

from assertpy import assert_that

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)


class TestTestHarnessConfiguration:
    """Unit tests for TestHarnessConfiguration."""

    @staticmethod
    def test_included_subsystems_returns_all_configs() -> None:
        """Returns all non-None subsystem configurations."""
        tmc_config = TMCConfiguration()
        csp_config = CSPConfiguration()
        sdp_config = SDPConfiguration()
        dishes_config = DishesConfiguration()
        config = TestHarnessConfiguration(
            tmc_config, csp_config, sdp_config, dishes_config
        )

        included_subsystems = config.get_included_subsystems()

        assert_that(included_subsystems).contains(
            tmc_config, csp_config, sdp_config, dishes_config
        )

    @staticmethod
    def test_included_subsystems_excludes_none_configs() -> None:
        """Excludes None configurations from the included subsystems list."""
        tmc_config = TMCConfiguration()
        csp_config = CSPConfiguration()
        config = TestHarnessConfiguration(tmc_config, csp_config)

        included_subsystems = config.get_included_subsystems()

        assert_that(included_subsystems).contains(tmc_config, csp_config)
        assert_that(included_subsystems).does_not_contain(None)

    @staticmethod
    def test_all_emulated_returns_true_when_nothing_is_production() -> None:
        """Returns True when all subsystems are emulated."""
        tmc_config = TMCConfiguration(is_emulated=True)
        csp_config = CSPConfiguration(is_emulated=True)
        sdp_config = SDPConfiguration(is_emulated=True)
        dishes_config = DishesConfiguration(is_emulated=True)
        config = TestHarnessConfiguration(
            tmc_config, csp_config, sdp_config, dishes_config
        )

        result = config.all_emulated()

        assert_that(result).is_true()

    @staticmethod
    def test_all_emulated_returns_false_when_something_is_production() -> None:
        """Returns False when not all subsystems are emulated."""
        tmc_config = TMCConfiguration(is_emulated=True)
        csp_config = CSPConfiguration(is_emulated=False)
        config = TestHarnessConfiguration(tmc_config, csp_config)

        result = config.all_emulated()

        assert_that(result).is_false()

    @staticmethod
    def test_all_production_returns_true_when_nothing_is_emulated() -> None:
        """Returns True when all subsystems are in production."""
        tmc_config = TMCConfiguration(is_emulated=False)
        csp_config = CSPConfiguration(is_emulated=False)
        sdp_config = SDPConfiguration(is_emulated=False)
        dishes_config = DishesConfiguration(is_emulated=False)
        config = TestHarnessConfiguration(
            tmc_config, csp_config, sdp_config, dishes_config
        )

        result = config.all_production()

        assert_that(result).is_true()

    @staticmethod
    def test_all_production_returns_false_when_something_is_emulated() -> None:
        """Returns False when not all subsystems are in production."""
        tmc_config = TMCConfiguration(is_emulated=False)
        csp_config = CSPConfiguration(is_emulated=True)
        config = TestHarnessConfiguration(tmc_config, csp_config)

        result = config.all_production()

        assert_that(result).is_false()

    @staticmethod
    def test_included_subsystems_empty_when_no_configs() -> None:
        """Returns an empty list when no subsystems are included."""
        config = TestHarnessConfiguration()

        included_subsystems = config.get_included_subsystems()

        assert_that(included_subsystems).is_empty()

    @staticmethod
    def test_get_config_returns_correct_config() -> None:
        """Returns the correct subsystem configuration."""
        tmc_config = TMCConfiguration()
        csp_config = CSPConfiguration()
        config = TestHarnessConfiguration(tmc_config, csp_config)

        result = config.get_subsystem_config(
            TestHarnessConfiguration.SubsystemName.TMC
        )

        assert_that(result).is_equal_to(tmc_config)

    @staticmethod
    def test_get_config_returns_none_for_missing_config() -> None:
        """Returns None when the requested config is missing."""
        config = TestHarnessConfiguration()

        result = config.get_subsystem_config(
            TestHarnessConfiguration.SubsystemName.TMC
        )

        assert_that(result).is_none()
