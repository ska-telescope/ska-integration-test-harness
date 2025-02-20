"""A wrapper for production dishes."""

import tango

from ska_integration_test_harness.config.components_config import (
    DishesConfiguration,
)
from ska_integration_test_harness.structure.dishes_wrapper import DishesWrapper


class ProductionDishesWrapper(DishesWrapper):
    """A wrapper for production dishes.

    Different from the emulated dishes wrapper, this class initialises
    in the Tango database the real Dish devices.
    """

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific Dishes methods and properties

    def _pre_init_dish_names(
        self, dishes_configuration: DishesConfiguration
    ) -> None:
        """Initialise real dishes in a Tango database.

        :param dishes_configuration: The dishes configuration.
        """
        # Create database object for TMC TANGO DB
        self.db = tango.db.Database()

        # Create database object for Dish1 TANGO DB
        dish1_tango_host = dishes_configuration.dish_master1_name.split("/")[2]
        dish1_host = dish1_tango_host.split(":")[0]
        dish1_port = dish1_tango_host.split(":")[1]
        self.dish1_db = tango.db.Database(dish1_host, dish1_port)

        # Get the Dish1 device class and server
        dish1_info = self.dish1_db.get_device_info(
            "mid-dish/dish-manager/SKA001"
        )
        self.dish1_dev_class = dish1_info.class_name
        self.dish1_dev_server = dish1_info.ds_full_name
