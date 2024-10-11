"""A test wrapper for the dishes."""

import abc

import tango

from ska_integration_test_harness.config.components_config import (
    DishesConfiguration,
)
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)


class DishesWrapper(SubsystemWrapper, abc.ABC):
    """A test wrapper for the dishes."""

    def __init__(self, dishes_configuration: DishesConfiguration):
        """Initialise the dishes wrapper.

        :param dishes_configuration: The dishes configuration.
        """
        super().__init__()
        self._pre_init_dish_names(dishes_configuration)
        self.dish_master_dict = {
            "dish_001": tango.DeviceProxy(
                dishes_configuration.dish_master1_name
            ),
            "dish_036": tango.DeviceProxy(
                dishes_configuration.dish_master2_name
            ),
            "dish_063": tango.DeviceProxy(
                dishes_configuration.dish_master3_name
            ),
            "dish_100": tango.DeviceProxy(
                dishes_configuration.dish_master4_name
            ),
        }

        self.dish1_admin_dev_name = self.dish_master_list[0].adm_name()
        self.dish1_admin_dev_proxy = tango.DeviceProxy(
            self.dish1_admin_dev_name
        )

    # --------------------------------------------------------------
    # Subsystem properties definition

    def get_subsystem_name(self) -> str:
        """Get the name of the subsystem."""
        return "Dishes"

    def get_all_devices(self) -> dict[str, tango.DeviceProxy]:
        """Get all the sub-system devices as a dictionary."""
        return self.dish_master_dict

    # --------------------------------------------------------------
    # Specific Dishes methods and properties

    @abc.abstractmethod
    def _pre_init_dish_names(
        self, dishes_configuration: DishesConfiguration
    ) -> None:
        """An operation that is done before creating the dish device proxies.

        :param dishes_configuration: The dishes configuration.
        """

    @property
    def dish_master_list(self) -> list[tango.DeviceProxy]:
        """Dish Master device proxies as a list (sorted by key)."""
        return [
            self.dish_master_dict[key]
            for key in sorted(self.dish_master_dict.keys())
        ]

    @abc.abstractmethod
    def tear_down(self) -> None:
        """Tear down the dishes (if needed)."""

    @abc.abstractmethod
    def clear_command_call(self) -> None:
        """Clear the command call on the Dishes (if needed)."""
