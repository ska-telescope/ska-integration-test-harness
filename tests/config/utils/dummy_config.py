"""A dummy configuration for testing purposes."""

from dataclasses import dataclass

from ska_integration_test_harness.config.components_config import (
    SubsystemConfiguration,
)


@dataclass
class DummySubsystemConfiguration(SubsystemConfiguration):
    """A dummy configuration for testing purposes.

    This configuration contains a minimal set of attributes and methods to
    facilitate testing of validators.
    """

    device_name: str = None
    required_attribute: str = None
    optional_attribute: int = 0

    def get_device_names(self) -> dict[str, str]:
        """Return the names of the attributes that contain device names.

        :return: List of attribute names.
        """
        return {"device_name": self.device_name}

    def mandatory_attributes(self) -> list[str]:
        """Return the names of the mandatory attributes.

        :return: List of attribute names.
        """
        return ["device_name", "required_attribute"]
