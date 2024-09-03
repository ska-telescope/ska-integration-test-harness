"""Unit tests on the telescope wrapper class."""

from unittest.mock import MagicMock

from assertpy import assert_that

from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class TestTelescopeWrapper:
    """Unit tests for the TelescopeWrapper class.

    Test a few base mechanics of the telescope wrapper as the test harness
    access point. We don't test instead anything related to the actual
    interaction with the telescope (since there is no actual telescope
    available in this test environment).
    """

    @staticmethod
    def test_telescope_wrapper_exposes_setup_subsystems():
        """The telescope wrapper exposes the setup subsystems."""
        telescope = TelescopeWrapper()
        tmc = MagicMock()
        sdp = MagicMock()
        csp = MagicMock()
        dishes = MagicMock()

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

        assert_that(telescope.fail_if_not_set_up).raises(ValueError)
        assert_that(telescope.tmc).raises(ValueError)
        assert_that(telescope.sdp).raises(ValueError)
        assert_that(telescope.csp).raises(ValueError)
        assert_that(telescope.dishes).raises(ValueError)

    @staticmethod
    def test_telescope_wrapper_is_a_singleton():
        """When creating a second instance, it returns the same subsystems."""
        telescope = TelescopeWrapper()
        tmc = MagicMock()
        sdp = MagicMock()
        csp = MagicMock()
        dishes = MagicMock()

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
