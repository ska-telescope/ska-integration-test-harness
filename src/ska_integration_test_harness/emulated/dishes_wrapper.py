"""A wrapper for emulated dishes."""

from tango import DevState

from ska_integration_test_harness.config.components_config import (
    DishesConfiguration,
)
from ska_integration_test_harness.emulated.utils.teardown_helper import (  # pylint: disable=line-too-long # noqa: E501
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.inputs.dish_mode import DishMode
from ska_integration_test_harness.structure.dishes_wrapper import DishesWrapper


class EmulatedDishesWrapper(DishesWrapper):
    """A wrapper for emulated dishes.

    Differently from the production dishes wrapper, there is no need to
    initialise the dishes in a Tango database (just an initial state setup
    is needed). The tear down procedure is the usual one for emulated devices.
    """

    def __init__(self, dishes_configuration: DishesConfiguration):
        super().__init__(dishes_configuration)
        self._reset_attributes(DishMode.STANDBY_FP)

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific Dishes methods and properties

    def tear_down(self) -> None:
        """Tear down the dishes.

        The procedure is the following:

        - Reset the health state for the dishes.
        - Clear the command call on the dishes.
        - Reset the transitions data for the dishes.
        - Reset the delay for the dishes.
        - Reset the attributes dish mode and state on the dishes.
        """
        EmulatedTeardownHelper.reset_health_state(self.dish_master_list)
        EmulatedTeardownHelper.clear_command_call(self.dish_master_list)
        EmulatedTeardownHelper.reset_transitions_data(self.dish_master_list)
        EmulatedTeardownHelper.reset_delay(self.dish_master_list)
        self._reset_attributes(DishMode.STANDBY_LP)

    def clear_command_call(self) -> None:
        """Clear the command call on the Dishes."""
        EmulatedTeardownHelper.clear_command_call(self.dish_master_list)

    def _reset_attributes(self, dish_mode: DishMode) -> None:
        """Reset the attributes on the Dishes."""
        for dish in self.dish_master_list:
            dish.SetDirectDishMode(dish_mode)
            dish.SetDirectState(DevState.STANDBY)
