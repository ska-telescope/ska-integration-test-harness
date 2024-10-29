"""Production wrapper for TMC devices."""

import logging

from ska_control_model import ObsState
from tango import DevState

from ..actions.central_node.central_node_load_dish_config import (
    CentralNodeLoadDishConfig,
)
from ..actions.central_node.central_node_release_resources import (
    CentralNodeReleaseResources,
)
from ..actions.central_node.move_to_off import MoveToOff
from ..actions.subarray.force_change_of_obs_state import ForceChangeOfObsState
from ..inputs.test_harness_inputs import TestHarnessInputs
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
        - Load the default dish VCC configuration (if needed).
        """
        self.logger.info(
            "Calling tear down for TMC (Starting subarray state: %s)",
            str(ObsState(self.subarray_node.obsState)),
        )

        if self.subarray_node.obsState == ObsState.IDLE:
            CentralNodeReleaseResources(
                self.default_commands_input.get_input(
                    TestHarnessInputs.InputName.RELEASE, fail_if_missing=True
                )
            ).execute()

        ForceChangeOfObsState(
            ObsState.EMPTY, self.default_commands_input
        ).execute()

        if self.central_node.telescopeState != DevState.OFF:
            MoveToOff().execute()

        # NOTE: is it really needed?
        # SubarrayMoveToOff().execute()

        # if source dish vcc config is empty or not matching with default
        # dish vcc then load default dish vcc config
        # CSP_SIMULATION_ENABLED condition will be removed after testing
        # with real csp
        expected_vcc_config = (
            self.default_commands_input.default_vcc_config_input
        )
        if (
            not self.csp_master_leaf_node.sourceDishVccConfig
            or not expected_vcc_config.is_equal_to_json(
                self.csp_master_leaf_node.sourceDishVccConfig
            )
        ):
            CentralNodeLoadDishConfig(expected_vcc_config).execute()

        self.logger.info("TMC tear down completed.")
