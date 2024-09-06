"""A mock state change waiter for testing purposes."""


class MockStateChangeWaiter:
    """A mock state change waiter for testing purposes."""

    def __init__(self):
        """Initialise the state change waiter."""
        self.expected_state_changes = []

    def reset(self):
        """Reset the state change waiter."""
        self.expected_state_changes = []

    def add_expected_state_changes(self, state_changes):
        """Add expected state changes to the waiter."""
        self.expected_state_changes.extend(state_changes)

    def wait_all(self, timeout):
        """Wait for all expected state changes to occur."""
        # In a real scenario, this would wait for state changes
