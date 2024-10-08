"""Invoke LoadDishCfg command on CentralNode."""

from ska_integration_test_harness.actions.command_action import (
    TelescopeCommandAction,
)
from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodeLoadDishConfig(TelescopeCommandAction):
    """Invoke LoadDishCfg command on CentralNode."""

    def __init__(self, dish_vcc_config: JSONInput):
        super().__init__()
        self.dish_vcc_config = dish_vcc_config

    def _action(self):
        # AttributeError: LoadDishConfig. Did you mean: 'LoadDishCfg'?
        self._log("Invoking LoadDishCfg on CentralNode")
        result, message = self.telescope.tmc.central_node.LoadDishCfg(
            self.dish_vcc_config.as_str()
        )
        return result, message

    def termination_condition(self):
        """Check if sourceDishVccConfig attribute contains new JSON."""

        def _is_source_dish_cfg_changed(event):
            """Check if sourceDishVccConfig attribute contains new JSON."""
            return not self.dish_vcc_config.is_equal_to_json(
                event.attribute_value
            )

        return [
            ExpectedEvent(
                device=self.telescope.tmc.csp_master_leaf_node,
                attribute="sourceDishVccConfig",
                predicate=_is_source_dish_cfg_changed,
            )
        ]
