"""Unit tests for assertions over Tango attributes."""

from unittest.mock import MagicMock

import pytest
import tango
from assertpy import assert_that

from ska_integration_test_harness.core.assertions.tango_attributes import (
    AssertTangoAttribute,
    AssertTangoAttributeHasValue,
)


@pytest.mark.core
class TestAssertTangoAttribute:
    """Unit tests for the AssertTangoAttribute class."""

    def test_verify_attribute_satisfies_condition(self):
        """Verify that a Tango attribute satisfies a condition."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 42
        )

        assertion.verify()

    def test_verify_attribute_fails_condition(self):
        """Verify that a Tango attribute fails a condition."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 43
        )

        with pytest.raises(
            AssertionError, match="Attribute value is instead 42"
        ):
            assertion.verify()

    def test_verify_attribute_read_fails(self):
        """Verify that a Tango attribute read fails."""
        device = MagicMock()
        device.read_attribute.side_effect = tango.DevFailed("Read failed")
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 42
        )

        with pytest.raises(
            AssertionError, match="Failed to read the attribute"
        ):
            assertion.verify()

    def test_describe_assumption_with_description(self):
        """Describe the assumption with a custom description."""

        def custom_assertion(x):
            return x >= 42

        device = MagicMock()
        assertion = AssertTangoAttribute(
            device, "test_attribute", custom_assertion, "Custom description"
        )

        description = assertion.describe_assumption()
        assert_that(description).described_as(
            "The assertiond description contains my custom description"
        ).contains("(Custom description)").described_as(
            "The assertion description contains "
            "a reference to the custom assertion"
        ).contains(
            "custom_assertion"
        )

    def test_describe_assumption_without_description(self):
        """Describe the assumption without a custom description."""
        device = MagicMock()
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 42
        )

        description = assertion.describe_assumption()
        assert_that(description).does_not_contain("Custom description")

@pytest.mark.core
class TestAssertTangoAttributeHasValue:
    """Unit tests for the AssertTangoAttributeHasValue class."""

    def test_verify_attribute_has_expected_value(self):
        """Verify that a Tango attribute has the expected value."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 42)

        assertion.verify()

    def test_verify_attribute_does_not_have_expected_value(self):
        """Verify that a Tango attribute does not have the expected value."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 43)

        with pytest.raises(
            AssertionError, match="Attribute value is instead 42"
        ):
            assertion.verify()

    def test_verify_attribute_with_preprocessing(self):
        """A Tango attribute has the expected value after preprocessing."""
        device = MagicMock()
        device.read_attribute.return_value.value = " 42 "
        assertion = AssertTangoAttributeHasValue(
            device,
            "test_attribute",
            42,
            value_preprocessor=lambda x: int(x.strip()),
        )

        assertion.verify()

    def test_describe_assumption_with_preprocessing(self):
        """Describe the assumption with a value preprocessor."""

        def custom_preprocessor(x):
            return x

        device = MagicMock()
        assertion = AssertTangoAttributeHasValue(
            device,
            "test_attribute",
            42,
            value_preprocessor=custom_preprocessor,
        )

        description = assertion.describe_assumption()
        assert_that(description).contains("after preprocessing")

    def test_describe_assumption_without_preprocessing(self):
        """Describe the assumption without a value preprocessor."""
        device = MagicMock()
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 42)

        description = assertion.describe_assumption()
        assert_that(description).does_not_contain("after preprocessing")
