"""A wrapper class that contains all the telescope subsystems."""

from ska_integration_test_harness.common_utils.tango_devices_info import (
    DevicesInfoProvider,
    DevicesInfoServiceException,
)
from ska_integration_test_harness.structure.csp_wrapper import CSPWrapper
from ska_integration_test_harness.structure.dishes_wrapper import DishesWrapper
from ska_integration_test_harness.structure.mccs_wrapper import MCCSWrapper
from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper
from ska_integration_test_harness.structure.subsystem_wrapper import (
    SubsystemWrapper,
)
from ska_integration_test_harness.structure.tmc_wrapper import TMCWrapper


class TelescopeWrapper:
    """A wrapper class that contains all the telescope subsystems.

    This infrastructural class is used as an unique entry point to access
    all the telescope subsystems and its devices. Given an instance of this
    class, using its properties, it is possible to access the TMC, SDP, CSP,
    and Dishes subsystems.

    This class is a *Singleton*, so this mean that there is only one instance
    of it in the entire code. This is done to avoid the creation of multiple
    "telescope" instances, potentially inconsistently initialised with
    different subsystem instances (which may be configured differently).

    To initialise the telescope test structure, create an instance of this
    class and call the `set_up` method with the instances of the TMC, SDP, CSP,
    and Dishes subsystems. After the initialisation, in any point of the
    code you can create an instance of this class and have it already
    initialised with the subsystems.

    .. code-block:: python

        # Initialise the telescope test structure
        telescope = TelescopeWrapper()
        telescope.set_up(tmc, sdp, csp, dishes)

        # ...

        # In any point of the code, you have access to the subsystems
        # (and their devices) using the properties of the telescope instance.
        telescope = TelescopeWrapper()
        do_something(telescope.tmc.central_node)

    When you are done with testing, you can tear down the entire telescope
    test structure and reset it to the initial state calling the `tear_down`
    method.

    .. code-block:: python

        # Tear down the telescope test structure
        telescope = TelescopeWrapper()
        telescope.tear_down()

    The *Singleton* is a pretty much standard design pattern. To learn more
    about it, you can refer to the following resources.

    - General idea explanation: https://refactoring.guru/design-patterns/singleton
    - Python implementation: https://www.geeksforgeeks.org/singleton-pattern-in-python-a-complete-guide/
    """  # pylint: disable=line-too-long # noqa: E501

    # -----------------------------------------------------------------
    # SINGLETON PATTERN IMPLEMENTATION

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelescopeWrapper, cls).__new__(cls)
        return cls._instance

    # -----------------------------------------------------------------
    # Subsystem access points

    _tmc: TMCWrapper | None = None
    _sdp: SDPWrapper | None = None
    _csp: CSPWrapper | None = None
    _dishes: DishesWrapper | None = None
    _mccs: MCCSWrapper | None = None

    @property
    def tmc(self) -> TMCWrapper:
        """A wrapper for the TMC subsystem and its devices.

        :return: The TMCDevices instance.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()
        return self._tmc

    @property
    def sdp(self) -> SDPWrapper:
        """A wrapper for the SDP subsystem and its devices.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()
        return self._sdp

    @property
    def csp(self) -> CSPWrapper:
        """A wrapper for the CSP subsystem and its devices.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()
        return self._csp

    @property
    def dishes(self) -> DishesWrapper:
        """A wrapper for the dishes subsystem and its devices.

        :return: The DishesDevices instance.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()

        if not self.tmc.supports_mid():
            raise ValueError(
                "Dishes subsystem is not available in the current setup."
            )

        return self._dishes

    @property
    def mccs(self) -> MCCSWrapper:
        """A wrapper for the MCCS subsystem and its devices.

        :return: The MCCSDevices instance.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()

        if not self.tmc.supports_low():
            raise ValueError(
                "MCCS subsystem is not available in the current setup."
            )

        return self._mccs

    # -----------------------------------------------------------------
    # Recap generation tools

    devices_info_provider: DevicesInfoProvider | None = None
    """The devices info provider used to access the devices information.

    (Used for recap purposes).
    """

    def get_required_subsystems(self) -> dict[SubsystemWrapper]:
        """Get all the required subsystems (based on the TMC configuration).

        :return: The list of all the required subsystems.
        """
        required_subsystems = {
            "TMC": self._tmc,
            "SDP": self._sdp,
            "CSP": self._csp,
        }

        if self._tmc and self._tmc.supports_mid():
            required_subsystems["Dishes"] = self._dishes

        if self._tmc and self._tmc.supports_low():
            required_subsystems["MCCS"] = self._mccs

        return required_subsystems

    def get_active_subsystems(self) -> list[SubsystemWrapper]:
        """Get all the active subsystems.

        :return: The list of all the subsystems.
        """
        return [
            subsystem
            for subsystem in [
                self._tmc,
                self._sdp,
                self._csp,
                self._dishes,
                self._mccs,
            ]
            if subsystem and isinstance(subsystem, SubsystemWrapper)
        ]

    def get_subsystems_recap(self, update_devices_info: bool = True) -> str:
        """Get a recap of the active subsystems and their devices.

        Get a recap of the active subsystems, their production-emulated
        status, and the devices they contain.

        :param update_devices_info: If True, the devices info provider
            is updated before getting the subsystems recaps.

        :return: The recap string.
        """
        recap = ""

        if self.devices_info_provider and update_devices_info:
            try:
                self.devices_info_provider.update()
            except DevicesInfoServiceException as error:
                recap += (
                    "WARNING: Devices info provider update failed with "
                    f"error:\n{error}\n\n"
                )

        for subsystem in self.get_active_subsystems():
            recap += subsystem.get_recap(self.devices_info_provider) + "\n"

        if recap == "":
            recap = "No subsystems are currently set up."

        return recap

    # -----------------------------------------------------------------
    # Initialisation and tear down methods

    actions_default_timeout: int = 60
    """The default timeout (in seconds) used in the telescope actions."""

    # pylint: disable=too-many-arguments disable=too-many-positional-arguments
    def set_up(
        self,
        tmc: TMCWrapper,
        sdp: SDPWrapper,
        csp: CSPWrapper,
        dishes: DishesWrapper | None = None,
        mccs: MCCSWrapper | None = None,
    ) -> None:
        """Initialise the telescope test structure with the given devices.

        :param tmc: The TMC subsystem wrapper.
        :param sdp: The SDP subsystem wrapper.
        :param csp: The CSP subsystem wrapper.
        :param dishes: The Dishes subsystem wrapper (required for mid).
        :param mccs: The MCCS subsystem wrapper (required for low).
        """
        self._tmc = tmc
        self._sdp = sdp
        self._csp = csp
        self._dishes = dishes
        self._mccs = mccs

    def tear_down(self) -> None:
        """Tear down the entire telescope test structure.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()

        # REFACTOR NOTE: tear_down may be worth of being an action

        self.tmc.tear_down()
        self.sdp.tear_down()
        self.csp.tear_down()

        if self.tmc.supports_mid():
            self.dishes.tear_down()

        if self.tmc.supports_low():
            self.mccs.tear_down()

    def fail_if_not_set_up(self) -> None:
        """Fail if a valid structure is not set up.

        :raises ValueError: If one or more subsystems are missing.
        """
        required_subsystems = self.get_required_subsystems()

        missing_subsystems = [
            subsystem_name
            for subsystem_name, subsystem in required_subsystems.items()
            if not subsystem
        ]

        if missing_subsystems:
            raise ValueError(
                "Telescope test structure is not correctly set up for "
                f"{'low' if self._tmc.supports_low() else 'mid'} target. "
                "The following (required) subsystems are missing: "
                f"{missing_subsystems}.\n"
                "Please set up the telescope test structure first calling the "
                "`set_up` method and ensure the following "
                f"subsystems are added: {list(required_subsystems.keys())}."
            )

    # -----------------------------------------------------------------
    # Other "technical" commands
    # (if you are looking for the "business" commands, check the
    # TelescopeAction subclasses)

    def clear_command_call(self) -> None:
        """Clear the command call on the telescope (if needed).

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()

        # REFACTOR NOTE: this is something that has a lot to do with the
        # fact of a system being emulated or not. Can we maybe have something
        # like `s.clear_command_call() for s in self.get_emulated()`?

        self.sdp.clear_command_call()
        self.csp.clear_command_call()

        if self.tmc.supports_mid():
            self.dishes.clear_command_call()

        if self.tmc.supports_low():
            self.mccs.clear_command_call()

    def set_subarray_id(self, subarray_id: int) -> None:
        """Create subarray devices for the requested subarray.

        :param subarray_id: The Subarray ID to set.

        :raises ValueError: If one or more subsystems are missing.
        """
        self.fail_if_not_set_up()

        self.sdp.set_subarray_id(subarray_id)
        self.csp.set_subarray_id(subarray_id)

        # if we are in low, also MCCS has a subarray
        if self.tmc.supports_low():
            self.mccs.set_subarray_id(subarray_id)

        self.tmc.set_subarray_id(subarray_id)
