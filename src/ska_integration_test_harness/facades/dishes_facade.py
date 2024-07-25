"""A facade to expose the dishes devices to the tests."""

from tango import DeviceProxy

from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


class DishesFacade:
    """A facade to expose the dishes devices to the tests."""

    def __init__(self, telescope: TelescopeWrapper) -> None:
        self._telescope = telescope

    @property
    def dish_master_dict(self) -> dict[str, DeviceProxy]:
        """The dish master Tango device proxies as a dictionary.

        The key is the dish name, as a string in the format "dish_XXX".
        """
        return self._telescope.dishes.dish_master_dict

    @property
    def dish_master_list(self) -> list[DeviceProxy]:
        """The dish master Tango device proxies as a list (sorted by key)."""
        return self._telescope.dishes.dish_master_list
