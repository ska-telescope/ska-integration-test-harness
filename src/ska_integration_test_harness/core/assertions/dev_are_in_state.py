"""Verify a set of devices are in a certain state."""

from typing import Any

import tango
from assertpy import assert_that

from .sut_assertion import SUTAssertion


class AssertDevicesAreInState(SUTAssertion):
    """Verify a set of devices are in a certain state.

    This assertion verifies that the given devices right now are in a certain
    state (i.e., their given attribute has a certain value). This assertion
    is defined by:

    - the ``devices`` where the attribute is expected to have a value
    - the attribute name (``attribute_name``)
    - the expected value (``attribute_value``)

    This assertion is expected to be verified considering the current value
    of the attribute, not the value recorded by some kind of event.
    """

    def __init__(
        self,
        devices: list[tango.DeviceProxy],
        attribute_name: str,
        attribute_value: Any,
    ):
        """Create a new AssertDevicesAreInState instance.

        :param devices: the list of devices to verify.
        :param attribute_name: the name of the attribute to assert.
        :param attribute_value: the value of the attribute to assert.
        """
        super().__init__()
        self.devices = devices
        """The list of devices to verify."""

        self.attribute_name = attribute_name
        """The name of the attribute to assert."""

        self.attribute_value = attribute_value
        """The value of the attribute to assert."""

    def verify(self) -> None:
        """Verify the devices are in the expected state.

        This assertion verifies that all the given devices have the
        attribute value equal to the expected value. If any of the
        devices does not have the expected value (or if the attribute
        is not readable), an AssertionError is raised.

        :raises AssertionError: if the current state of the devices
            does not match the expected state or if the attribute is
            not readable.
        """
        for device in self.devices:
            # access the attribute value
            try:
                value = device.read_attribute(self.attribute_name).value
            except tango.DevFailed as df:
                raise AssertionError(
                    f"{self.describe_assumption()} Error reading attribute "
                    f"{device.dev_name()}.{self.attribute_name}."
                ) from df

            # compare it with the expected value
            assert_that(value).described_as(
                f"{self.describe_assumption()} Mismatch in attribute value "
                f"for {device.dev_name()}.{self.attribute_name}. "
            ).is_equal_to(self.attribute_value)

    def describe_assumption(self):
        """Describe the assertion's assumption.

        This assertion verifies that the devices have
        a certain attribute value.

        If you extend this class, please check
        :py:meth:`SUTAssertion.describe_assumption`
        to see how to extend it properly.

        :return: the description of the assumption
        """
        desc = ", ".join(device.dev_name() for device in self.devices)
        desc += f" have attribute {self.attribute_name} value equal "
        desc += f"to {self.attribute_value}."
        return desc
