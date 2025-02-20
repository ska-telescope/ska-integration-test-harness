"""A factory to generate configurations for the test harness' components."""

import abc

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    MCCSConfiguration,
    SDPConfiguration,
    TMCConfiguration,
)
from ska_integration_test_harness.config.test_harness_config import (
    TestHarnessConfiguration,
)


class ConfigurationReader(abc.ABC):
    """A factory that reads from somewhere the test harness configuration.

    This abstract class defines the interface of a configuration reader
    that is able to collect subsystem configurations and create a
    TestHarnessConfiguration object.

    Currently, the supported subsystems are:

    - TMC
    - CSP
    - SDP
    - the dishes
    - the emulation configuration

    None of those configurations are mandatory and the correctness of the
    configuration is not checked by this class, since it is delegated to
    a separate validator that can make its own checks according to the
    testing context.

    The concrete implementations of this class may read the configuration
    from different sources, such as environment variables and configuration
    files.
    """

    # -------------------------------------------------------------------------
    # Main access point (that can be used to read all the configurations)

    def get_test_harness_configuration(self) -> TestHarnessConfiguration:
        """Get all the configurations needed for the test harness.

        return: A collection of all the test harness configurations that
            have been found by the reader.
        """

        if self.get_target() == "mid":
            return TestHarnessConfiguration(
                tmc_config=self.get_tmc_configuration(),
                csp_config=self.get_csp_configuration(),
                sdp_config=self.get_sdp_configuration(),
                dishes_config=self.get_dish_configuration(),
            )
        if self.get_target() == "low":
            return TestHarnessConfiguration(
                tmc_config=self.get_tmc_configuration(),
                csp_config=self.get_csp_configuration(),
                sdp_config=self.get_sdp_configuration(),
                mccs_config=self.get_mccs_configuration(),
            )
        raise ValueError(
            f"Invalid 'target' field: {self.get_target()}. "
            "It must be 'mid' or 'low'. You can leave it empty to "
            "use the default value ('mid')."
        )

    # -------------------------------------------------------------------------
    # Subsystems configuration readers

    @abc.abstractmethod
    def get_target(self) -> str:
        """Get the target environment for the configuration.

        return: The target environment for the configuration.
        """

    @abc.abstractmethod
    def get_tmc_configuration(self) -> TMCConfiguration | None:
        """Get the configuration for the TMC.

        return: The TMC configuration (if any).
        """

    @abc.abstractmethod
    def get_csp_configuration(self) -> CSPConfiguration | None:
        """Get the configuration for the CSP.

        return: The CSP configuration (if any).
        """

    @abc.abstractmethod
    def get_sdp_configuration(self) -> SDPConfiguration | None:
        """Get the configuration for the SDP.

        return: The SDP configuration (if any).
        """

    @abc.abstractmethod
    def get_dish_configuration(self) -> DishesConfiguration | None:
        """Get the configuration for the dishes.

        return: The dishes configuration (if any).
        """

    @abc.abstractmethod
    def get_mccs_configuration(self) -> MCCSConfiguration | None:
        """Get the configuration for the MCCS.

        return: The MCCS configuration (if any).
        """
