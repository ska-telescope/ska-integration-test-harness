"""Invoke LoadDishCfg command on CentralNode."""

from ska_integration_test_harness.actions.expected_event import ExpectedEvent
from ska_integration_test_harness.actions.telescope_action import (
    TelescopeAction,
)
from ska_integration_test_harness.inputs.json_input import JSONInput


class CentralNodeLoadDishConfig(TelescopeAction):
    """Invoke LoadDishCfg command on CentralNode."""

    def __init__(self, dish_vcc_config: JSONInput):
        super().__init__()
        self.dish_vcc_config = dish_vcc_config

    def _action(self):
        # AttributeError: LoadDishConfig. Did you mean: 'LoadDishCfg'?
        result, message = self.telescope.tmc.central_node.LoadDishCfg(
            self.dish_vcc_config.get_json_string()
        )
        return result, message

    def termination_condition(self):
        def _is_source_dish_cfg_changed(event):
            # if not current_value and future_value:
            #     return False
            # return json.loads(current_value) == json.loads(future_value)
            return not self.dish_vcc_config.is_equal_to_json(
                event.attribute_value
            )

        # TODO: be careful about this wait
        return [
            ExpectedEvent(
                device=self.telescope.tmc.csp_master_leaf_node,
                attribute="sourceDishVccConfig",
                # predicate=lambda event: _is_source_dish_cfg_changed(
                #     event.attribute_value, self.dish_vcc_config
                # ),
                predicate=_is_source_dish_cfg_changed,
            )
        ]
