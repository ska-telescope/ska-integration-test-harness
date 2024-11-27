"""A wrapper to all the configurations needed to setup the test harness."""

from dataclasses import dataclass
from enum import Enum

from ska_integration_test_harness.config.components_config import (
    CSPConfiguration,
    DishesConfiguration,
    SDPConfiguration,
    SubsystemConfiguration,
    TMCConfiguration,
)


@dataclass
class TestHarnessConfiguration:
    """A wrapper to all the configurations needed to setup the test harness.

    This class is a wrapper to all the configurations needed to setup the test
    harness. It is used to pass all the configurations to the test harness
    factory, so it can create the needed test harness wrappers.

    Each field of this class is a configuration for a different subsystem of
    the test harness, such as the TMC, CSP, SDP, and the dishes. Even if they
    are marked as optional, for now they are all required, as the test harness
    is strictly built for TMC-Mid integration tests. In the future, we may
    support an elastic choice of which subsystems to include, so this
    configuration may be useful to select only the needed subsystems.

    A support enum is provided to specify the subsystem names, and
    allow access to the configurations in a parametric way.
    """

    # (this is not a pytest test class)
    __test__ = False

    class SubsystemName(Enum):
        """An enumeration of the possible subsystem names.

        An enumeration of the possible subsystems that could be included in the
        the test harness configuration.
        """

        TMC = "tmc"
        CSP = "csp"
        SDP = "sdp"
        DISHES = "dishes"

    tmc_config: TMCConfiguration | None = None
    csp_config: CSPConfiguration | None = None
    sdp_config: SDPConfiguration | None = None
    dishes_config: DishesConfiguration | None = None

    # TODO Low: Add MCCS configuration

    def get_included_subsystems(self) -> list[SubsystemConfiguration]:
        """Get the list of subsystems that are included in the configuration.

        :return: A list with the names of the included subsystems.
        """
        return [
            config
            for config in self.__dict__.values()
            if isinstance(config, SubsystemConfiguration)
            and config is not None
        ]

    def get_subsystem_config(
        self, subsystem_name: SubsystemName
    ) -> SubsystemConfiguration:
        """Get the configuration for a specific subsystem.

        :param subsystem_name: The name of the subsystem you want to get the
            configuration for.

        :return: The configuration for the specified subsystem.
        :raises ValueError: If the specified subsystem is not included in the
            configuration.
        """
        return self.__dict__.get(f"{subsystem_name.value}_config")

    def all_emulated(self) -> bool:
        """Check if, among the included subsystems, all are emulated.

        :return: True if all the subsystems are emulated, False otherwise.
        """
        return all(
            config.is_emulated for config in self.get_included_subsystems()
        )

    def all_production(self) -> bool:
        """Check if, among the included subsystems, all are in production.

        :return: True if all the subsystems are in production, False otherwise.
        """
        return all(
            not config.is_emulated for config in self.get_included_subsystems()
        )
