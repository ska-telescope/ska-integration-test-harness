"""Unit tests for TelescopeCommandAction class and its subclasses."""

from assertpy import assert_that

from ska_integration_test_harness.actions.command_action import (
    TransientQuiescentCommandAction,
)
from ska_integration_test_harness.actions.expected_event import (
    ExpectedStateChange,
)

# TODO: test TelescopeCommandAction too


class DummyTransientQuiescentCommand(TransientQuiescentCommandAction):
    """A dummy TransientQuiescentCommandAction subclass for testing purposes.

    It simply returns two different termination conditions
    for the transient and quiescent states.
    """

    def _action(self):
        """A dummy action that does nothing."""

    def termination_condition_for_transient_state(self):
        """Return a dummy termination condition for the transient state."""
        return [
            ExpectedStateChange(
                device="dummy_device",
                attribute="dummy_attribute",
                expected_value="TRANSIENT_STATE",
            )
        ]

    def termination_condition_for_quiescent_state(self):
        """Return a dummy termination condition for the quiescent state."""
        return [
            ExpectedStateChange(
                device="dummy_device",
                attribute="dummy_attribute",
                expected_value="QUIESCENT_STATE",
            )
        ]


class TestTransientQuiescentCommandAction:
    """Unit tests for TransientQuiescentCommandAction class."""

    @staticmethod
    def test_termination_condition_by_default_returns_quiescent_state():
        """The termination condition returns the quiescent state by default."""
        action = DummyTransientQuiescentCommand()

        assert_that(action.synchronise_on_transient_state).described_as(
            "By default, synchronise_on_transient_state should be False"
        ).is_false()

        assert_that(action.termination_condition()).is_length(1)
        assert_that(action.termination_condition()[0].expected_value).contains(
            "QUIESCENT_STATE"
        )

    @staticmethod
    def test_termination_condition_when_set_returns_transient_state():
        """The termination condition returns the transient state when set."""
        action = DummyTransientQuiescentCommand()
        action.set_synchronise_on_transient_state(True)

        assert_that(action.synchronise_on_transient_state).described_as(
            "synchronise_on_transient_state should be set to True"
        ).is_true()

        assert_that(action.termination_condition()).is_length(1)
        assert_that(action.termination_condition()[0].expected_value).contains(
            "TRANSIENT_STATE"
        )
