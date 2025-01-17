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
        """Assertion passes when a Tango attribute satisfies a condition."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 42
        )

        assertion.verify()

    def test_verify_attribute_fails_condition(self):
        """Assertion fails when a Tango attribute doesn't match."""
        device = MagicMock()
        device.dev_name.return_value = "test/device/01"
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 43
        )

        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "A reference to the device and attribute name is included"
        ).contains("test/device/01").contains("test_attribute").described_as(
            "The assertion contains a reference to the fact it failed"
        ).contains(
            "FAILED"
        ).described_as(
            "The assertion contains a reference "
            "to the observed attribute value"
        ).contains(
            "Attribute value is instead 42"
        )

    def test_verify_attribute_read_fails(self):
        """Assertion fails when reading a Tango attribute fails."""
        device = MagicMock()
        device.dev_name.return_value = "test/device/01"
        device.read_attribute.side_effect = tango.DevFailed("Read failed")
        assertion = AssertTangoAttribute(
            device, "test_attribute", lambda x: x == 42
        )

        with pytest.raises(AssertionError) as exc_info:
            assertion.verify()

        assert_that(str(exc_info.value)).described_as(
            "A reference to the device and attribute name is included"
        ).contains("test/device/01").contains("test_attribute").described_as(
            "The assertion contains a reference to the fact it failed"
        ).contains(
            "FAILED"
        ).described_as(
            "The assertion contains a reference "
            "to the fact that the read failed"
        ).contains(
            "Failed to read the attribute"
        )

    def test_describe_assumption_with_description(self):
        """Description of the assumption contains a custom description."""

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
        """An assertion can be described without a custom description."""
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
        """Assertion passes when a Tango attribute has the expected value."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 42)

        assertion.verify()

    def test_verify_attribute_does_not_have_expected_value(self):
        """Assertion fails when the attribute hasn't the expected value."""
        device = MagicMock()
        device.read_attribute.return_value.value = 42
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 43)

        with pytest.raises(
            AssertionError, match="Attribute value is instead 42"
        ):
            assertion.verify()

    def test_verify_attribute_with_preprocessing(self):
        """Assertion uses a value preprocessor before comparing values."""
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
        """An assertion is described with a value preprocessor."""

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
        """An assertion is described without a value preprocessor."""
        device = MagicMock()
        assertion = AssertTangoAttributeHasValue(device, "test_attribute", 42)

        description = assertion.describe_assumption()
        assert_that(description).does_not_contain("after preprocessing")
