"""Unit tests for the ObsStateSetter class."""

import pytest

from ska_integration_test_harness.extensions.subarray.setter import (
    ObsStateSetter,
)

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateSetterGraphPath:
    """Unit tests for the ObsStateSetter class.

    This set of unit tests has the objective to validate the ObsStateSetter
    class behaviour. We can divide the test cases into two categories:

    1. Tests on individual Setter instances (to validate the class behaviour
       in isolation and unit test the individual methods)
    2. Tests that simulate a complete ObsState setting scenario (to validate
       the capability of the class to follow the expected path of commands)

    This class focuses on the second category, where we simulate a few
    ObsState setting scenarios and we check it the expected sequence of
    commands is called. To do so, we use the MockSubarraySystem class to
    simulate the Subarray System and its devices and we stub the methods that
    return the system and devices state to always return the expected state
    by the classes (so from ObsStateSetter perspective it looks like the
    system and devices are always in the expected state). We also patch
    TangoLRCAction to avoid executing the commands and synchronising after.

    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    @pytest.fixture(autouse=True)
    @staticmethod
    def stub_system_state(system: MockSubarraySystem):
        """System state is always the one expected by ObsStateSetter.

        This fixture stubs the methods that return the system state and the
        devices state, so that the ObsStateSetter always observes the assumed
        class observation state as the actual system and devices state.
        """
        # the system is always in the expected state
        # pylint: disable=protected-access
        ObsStateSetter._system_obs_state = (
            lambda self: self.assumed_class_obs_state()
        )

        # all the devices are always in the expected state
        # pylint: disable=protected-access
        ObsStateSetter._devices_obs_state = lambda self: {
            system.obs_state_devices[0]: self.assumed_class_obs_state(),
            system.obs_state_devices[1]: self.assumed_class_obs_state(),
            system.obs_state_devices[2]: self.assumed_class_obs_state(),
        }

    # -------------------------------------------------------------------------
    # Test instance creation through the factory method
