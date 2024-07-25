"""Test the dummy module."""

from assertpy import assert_that

from ska_integration_test_harness.dummy import hello_world


def test_hello_world(expected_greeting: str) -> None:
    """The hello_world function returns the expected greeting."""
    assert_that(hello_world()).is_equal_to(expected_greeting)
