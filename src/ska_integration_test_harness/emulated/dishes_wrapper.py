"""A wrapper for emulated dishes."""

from tango import DevState

from ska_integration_test_harness.config.components_config import (
    DishesConfiguration,
)
from ska_integration_test_harness.emulated.utils.teardown_helper import (  # pylint: disable=line-too-long # noqa: E501
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode
from ska_integration_test_harness.structure.dishes_wapper import DishesDevices


class EmulatedDishesDevices(DishesDevices):
    """A wrapper for emulated dishes."""

    def __init__(self, dishes_configuration: DishesConfiguration):
        super().__init__(dishes_configuration)
        self._setup_attributes()

    def _pre_init_dish_names(
        self, dishes_configuration: DishesConfiguration
    ) -> None:
        """Do nothing when dishes are emulated.

        :param dishes_configuration: The dishes configuration.
        """

    def tear_down(self) -> None:
        """Tear down the dishes."""
        EmulatedTeardownHelper.reset_health_state(self.dish_master_list)
        EmulatedTeardownHelper.clear_command_call(self.dish_master_list)
        EmulatedTeardownHelper.reset_transitions_data(self.dish_master_list)
        EmulatedTeardownHelper.reset_delay(self.dish_master_list)
        self._reset_attributes()

    def clear_command_call(self) -> None:
        """Clear the command call on the Dishes."""
        EmulatedTeardownHelper.clear_command_call(self.dish_master_list)

    def _reset_attributes(self) -> None:
        """Reset the attributes on the Dishes."""
        for dish in self.dish_master_list:
            dish.SetDirectDishMode(DishMode.STANDBY_LP)
            dish.SetDirectState(DevState.STANDBY)

    def _setup_attributes(self) -> None:
        """Set the attributes on the Dishes."""
        for dish in self.dish_master_list:
            # NOTE: why here STANDARD_FP and not STANDBY_LP?
            dish.SetDirectDishMode(DishMode.STANDBY_FP)
            dish.SetDirectState(DevState.STANDBY)
