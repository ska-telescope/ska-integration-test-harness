"""Production wrapper for TMC devices."""

import logging

from ska_control_model import ObsState

from ..actions.central_node.central_node_load_dish_config import (
    CentralNodeLoadDishConfig,
)
from ..actions.central_node.central_node_release_resources import (
    CentralNodeReleaseResources,
)
from ..actions.central_node.move_to_off import MoveToOff
from ..actions.central_node.set_standby import SetStandby
from ..actions.subarray.force_change_of_obs_state import ForceChangeOfObsState
from ..inputs.test_harness_inputs import TestHarnessInputs
from ..structure.telescope_wrapper import TelescopeWrapper
from ..structure.tmc_wrapper import TMCWrapper


class ProductionTMCWrapper(TMCWrapper):
    """Production wrapper for TMC devices."""

    def __init__(
        self,
        tmc_configuration,
        default_commands_input: TestHarnessInputs,
    ):
        """Initialise the TMC wrapper.

        :param tmc_configuration: The TMC configuration.
        :param default_commands_input: The default commands input. They
            will be used to reset the TMC devices. Fill it with all
            the inputs with suitable default values. If you don't some
            steps of the tear down procedure may fail.
        """
        super().__init__(tmc_configuration)

        # set some default command inputs (needed for tear down)
        self.default_commands_input = default_commands_input

        # configure logging (used also in tear down)
        self.logger = logging.getLogger(__name__)

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Specific TMC methods and properties

    def tear_down(self) -> None:
        """Tear down the TMC devices.

        This method will:

        - Release resources from the central node
          (if the subarray is in a IDLE state).
        - Force the subarray state to EMPTY.
        - Move the central node to OFF.
        - Move the subarray to OFF.
        - Load the default dish VCC configuration (if needed and if in Mid).
        """
        self.logger.info(
            "Calling tear down for TMC (Starting subarray state: %s)",
            str(ObsState(self.subarray_node.obsState)),
        )

        # eventually release resources from the central node
        if self.subarray_node.obsState == ObsState.IDLE:
            CentralNodeReleaseResources(
                self.default_commands_input.get_input(
                    TestHarnessInputs.InputName.RELEASE, fail_if_missing=True
                )
            ).execute()

        # reset the subarray state to EMPTY
        ForceChangeOfObsState(
            ObsState.EMPTY, self.default_commands_input
        ).execute()

        # if we are in Mid, reset dishes config
        if self.supports_mid():
            # if source dish vcc config is empty or not matching with default
            # dish vcc then load default dish vcc config
            # CSP_SIMULATION_ENABLED condition will be removed after testing
            # with real csp
            expected_vcc_config = (
                self.default_commands_input.default_vcc_config_input
            )
            if self.central_node.isDishVccConfigSet and (
                not self.csp_master_leaf_node.sourceDishVccConfig
                or not expected_vcc_config.is_equal_to_json(
                    self.csp_master_leaf_node.sourceDishVccConfig
                )
            ):
                CentralNodeLoadDishConfig(expected_vcc_config).execute()

        # ensure the central node is in OFF state (except from a special
        # case where we are in Low and CSP is production, where I
        # have to call a stand by)
        if self.supports_low() and not TelescopeWrapper().csp.is_emulated():
            SetStandby().execute()
        else:
            MoveToOff().execute()

        self.logger.info("TMC tear down completed.")
