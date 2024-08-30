"""Production wrapper for TMC devices."""

import logging

from ska_control_model import ObsState
from ska_ser_logging import configure_logging
from tango import DevState

from ska_integration_test_harness.actions.central_node.central_node_load_dish_config import (  # pylint: disable=line-too-long # noqa E501
    CentralNodeLoadDishConfig,
)
from ska_integration_test_harness.actions.central_node.central_node_release_resources import (  # pylint: disable=line-too-long # noqa E501
    CentralNodeReleaseResources,
)
from ska_integration_test_harness.actions.central_node.move_to_off import (
    MoveToOff,
)
from ska_integration_test_harness.actions.subarray.force_change_of_obs_state import (  # pylint: disable=line-too-long # noqa E501
    ForceChangeOfObsState,
)
from ska_integration_test_harness.actions.subarray.subarray_move_to_off import (  # pylint: disable=line-too-long # noqa E501
    SubarrayMoveToOff,
)
from ska_integration_test_harness.inputs.json_input import JSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.tmc_devices import TMCDevices

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class ProductionTMCDevices(TMCDevices):
    """Production wrapper for TMC devices."""

    def __init__(
        self,
        tmc_configuration,
        default_commands_input: TestHarnessInputs,
        default_vcc_config_input: JSONInput,
    ):
        """Initialise the TMC wrapper.

        :param tmc_configuration: The TMC configuration.
        :param default_commands_input: The default commands input. They
            will be used to reset the TMC devices. Fill it with all
            the inputs with suitable default values. If you don't some
            steps of the tear down procedure may fail.
        :param default_vcc_config_input: The default VCC config input. It
            will be used to reset the VCC config.
        """
        super().__init__(tmc_configuration)
        self.default_commands_input = default_commands_input
        self.default_vcc_config_input = default_vcc_config_input

    def tear_down(self) -> None:
        """Tear down the TMC devices."""
        LOGGER.info(
            "Calling tear down for CentralNode "
            "for SubarrayNode's %s obsstate.",
            self.subarray_node.obsState,
        )

        if self.subarray_node.obsState == ObsState.IDLE:
            LOGGER.info("Calling Release Resource on centralnode")
            CentralNodeReleaseResources(
                self.default_commands_input.get_input(
                    TestHarnessInputs.InputName.RELEASE, fail_if_missing=True
                )
            ).execute()

        ForceChangeOfObsState(
            ObsState.EMPTY, self.default_commands_input
        ).execute()

        # NOTE: temporarily moved here because of synchronization
        if self.central_node.telescopeState != DevState.OFF:
            MoveToOff().execute()

        # reset subarray too
        # TODO: maybe TMCCentralNode and TMCSubarrayNode should be
        # two different classes (?).
        SubarrayMoveToOff().execute()

        # if source dish vcc config is empty or not matching with default
        # dish vcc then load default dish vcc config
        # CSP_SIMULATION_ENABLED condition will be removed after testing
        # with real csp
        if (
            not self.csp_master_leaf_node.sourceDishVccConfig
            or not self.default_vcc_config_input.is_equal_to_json(
                self.csp_master_leaf_node.sourceDishVccConfig
            )
        ):
            CentralNodeLoadDishConfig(self.default_vcc_config_input).execute()
