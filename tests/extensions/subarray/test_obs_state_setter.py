"""Unit tests for the ObsStateSetter class."""

import pytest

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateSetter:
    """Unit tests for the ObsStateSetter class.

    TODO: change this description to reflect the actual class being tested.
    """

    @pytest.fixture
    @staticmethod
    def system() -> MockSubarraySystem:
        """Create an observation state system for testing purposes."""
        return MockSubarraySystem()

    @pytest.fixture(autouse=True)
    @staticmethod
    def stub_system_state(system: MockSubarraySystem):
        """Stub the methods that observe the system state.

        Stub the methods that observe the system state so ``ObsStateSetter``
        sees the system as it always is in a consistent expected state.

        :param system: The system to stub.
        """
