"""Pytest configuration file."""

from pytest import fixture


@fixture
def expected_greeting() -> str:
    """The expected greeting message."""
    return "Hello, World!"
