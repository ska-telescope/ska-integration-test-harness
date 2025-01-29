"""Testing utilities."""

from datetime import datetime

from assertpy import assert_that


def assert_elapsed_time_is_closed_to(
    start_time: datetime,
    expected_seconds: float,
    tolerance: float,
) -> None:
    """Assert that the elapsed time is close to the expected value.

    :param start_time: the start time
    :param expected_seconds: the expected elapsed time in seconds
    :param tolerance: the tolerance in seconds
    """
    elapsed_time = (datetime.now() - start_time).total_seconds()

    assert_that(elapsed_time).described_as(
        "The elapsed time is close to the expected value"
    ).is_close_to(expected_seconds, tolerance)
