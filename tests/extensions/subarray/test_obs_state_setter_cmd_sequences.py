"""Unit tests for the ObsStateSetter class."""

import pytest

from .utils import MockSubarraySystem


@pytest.mark.extensions
class TestObsStateSetterCommandsSequences:
    """Unit tests for the ObsStateSetter class from a broader perspective.

    This set of unit tests is complementer to ``TestObsStateSetterInIsolation``
    and verifies the ObsStateSetter class from a broader perspective. It
    verifies the ObsStateSetter class capabilities to call a correct sequence
    of commands to move the system to the desired target state (and
    so consequently also to self-orchestrate correctly the sequence of
    ObsStateSetter instances that are needed to reach the target state).
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
