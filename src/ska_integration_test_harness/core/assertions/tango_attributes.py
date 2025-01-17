"""Assert over one or more Tango attributes."""

from typing import Any, Callable

import tango

from .sut_assertion import SUTAssertion


class AssertTangoAttribute(SUTAssertion):
    """An assertion over a Tango attribute.

    TODO: describe better
    """

    def __init__(
        self,
        device: tango.DeviceProxy,
        attribute_name: str,
        assert_fn: Callable[[Any], bool],
        assert_description: str | None = None,
    ):
        """Create a new assertion over a Tango attribute.

        :param device: The Tango device proxy.
        :param attribute_name: The name of the attribute to assert.
        :param assert_fn: The function to assert the attribute value.
        :param assert_description: The description of the assertion. It is
            optional and can be used to provide more context to the assertion.
        """
        self.device = device
        self.attribute_name = attribute_name
        self.assert_fn = assert_fn
        self.assert_description = assert_description

    def verify(self):
        """Verify a Tango attribute is readable and satisfies a condition.

        This assertion verifies that a Tango attribute is readable and that
        its value satisfies a condition. The condition is specified by the
        ``assert_fn`` parameter in the constructor.

        :raises AssertionError: if the assertion fails
        """
        super().verify()

        try:
            attribute_value = self.device.read_attribute(
                self.attribute_name
            ).value
        except tango.DevFailed as e:
            self.fail("Failed to read the attribute", e)

        if not self.assert_fn(attribute_value):
            self.fail(f"Attribute value is instead {attribute_value}")

    def describe_assumption(self) -> str:
        """Describe the assumption of the assertion.

        This assertion verifies that the Tango attribute
        ``{device}.{attribute_name}`` satisfies a condition.

        If you extend this class, please check
        :py:meth:`SUTAssertion.describe_assumption`
        to see how to extend it properly.

        :return: the description of the assumption
        """
        msg = f"{self._describe_target()} satisfies {self.assert_fn.__name__}"
        if self.assert_description:
            msg += f" ({self.assert_description})"
        return msg

    def _describe_target(self) -> str:
        return f"{self.device.dev_name()}.{self.attribute_name}"


class AssertTangoAttributeHasValue(AssertTangoAttribute):
    """An assertion that a Tango attribute has a specific value.

    TODO: describe better
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        device: tango.DeviceProxy,
        attribute_name: str,
        expected_value: Any,
        assert_description: str | None = None,
        value_preprocessor: Callable[[Any], Any] | None = None,
    ):
        """Create a new assertion that a Tango attribute has a specific value.

        :param device: The Tango device proxy.
        :param attribute_name: The name of the attribute to assert.
        :param expected_value: The expected value of the attribute.
        :param value_preprocessor: A function to preprocess the attribute
            value. This function is applied before comparing the value with the
            expected value. The default function does not modify the value.
            By default, no preprocessing is applied.
        :param assert_description: The description of the assertion. It is
            optional and can be used to provide more context to the assertion.
        """

        def value_is_equal_after_preprocessing(value: Any) -> bool:
            """Check if a value is equal to the expected after preprocessing.

            :param value: The value to check.
            :return: True if the value is equal to the expected value after
            """
            value = (
                value
                if value_preprocessor is None
                else value_preprocessor(value)
            )
            return value == expected_value

        super().__init__(
            device,
            attribute_name,
            value_is_equal_after_preprocessing,
            assert_description,
        )
        self.expected_value = expected_value
        self.value_preprocessor = value_preprocessor

    def describe_assumption(self) -> str:
        """Describe the assumption of the assertion.

        This assertion verifies that the Tango attribute
        ``{device}.{attribute_name}`` has the value ``{expected_value}``
        (eventually, after preprocessing it with ``{value_preprocessor}``).

        :return: the description of the assumption
        """
        res = f"{self._describe_target()} has value {self.assert_fn.__name__}"

        if self.value_preprocessor:
            res += (
                f" after preprocessing with {self.value_preprocessor.__name__}"
            )

        if self.assert_description:
            res += f" ({self.assert_description})"

        return res
