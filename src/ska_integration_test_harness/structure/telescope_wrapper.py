"""A wrapper class that contains all the telescope sub-systems."""

from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer

from ska_integration_test_harness.structure.csp_wrapper import CSPWrapper
from ska_integration_test_harness.structure.dishes_wapper import DishesWrapper
from ska_integration_test_harness.structure.sdp_wrapper import SDPWrapper
from ska_integration_test_harness.structure.tmc_wrapper import TMCWrapper


class TelescopeWrapper:
    """A wrapper class that contains all the telescope sub-systems.

    This infrastructural class is used as an unique entry point to access
    all the telescope sub-systems and its devices. Given an instance of this
    class, using its properties, it is possible to access the TMC, SDP, CSP,
    and Dishes sub-systems.

    This class is a *Singleton*, so this mean that there is only one instance
    of it in the entire code. This is done to avoid the creation of multiple
    "telescope" instances, potentially inconsistently initialized with
    different sub-subsystems (which may be configured differently).

    To initialize the telescope test structure, create an instance of this
    class and call the `set_up` method with the instances of the TMC, SDP, CSP,
    and Dishes sub-systems. After the initialization, in any point of the
    code you can create an instance of this class and have it already
    initialized with the sub-systems.

    ```python

        # Initialize the telescope test structure
        telescope = TelescopeWrapper()
        telescope.set_up(tmc, sdp, csp, dishes)

        # ...

        # In any point of the code, you can access the sub-systems
        # (and their devices) using the properties of the telescope instance.
        telescope = TelescopeWrapper()
        do_something(telescope.tmc.central_node)

    When you are done with testing, you can tear down the entire telescope
    test structure and reset it to the initial state calling the `tear_down`
    method.

    ```python

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

    _tmc: TMCWrapper | None = None
    _sdp: SDPWrapper | None = None
    _csp: CSPWrapper | None = None
    _dishes: DishesWrapper | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelescopeWrapper, cls).__new__(cls)
        return cls._instance

    # -----------------------------------------------------------------
    # Subsystem access points

    @property
    def tmc(self) -> TMCWrapper:
        """A wrapper for the TMC sub-system and its devices.

        :return: The TMCDevices instance.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()
        return self._tmc

    @property
    def sdp(self) -> SDPWrapper:
        """A wrapper for the SDP sub-system and its devices.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()
        return self._sdp

    @property
    def csp(self) -> CSPWrapper:
        """A wrapper for the CSP sub-system and its devices.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()
        return self._csp

    @property
    def dishes(self) -> DishesWrapper:
        """A wrapper for the dishes sub-system and its devices.

        :return: The DishesDevices instance.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()
        return self._dishes

    # -----------------------------------------------------------------
    # Initialization and tear down methods

    def set_up(
        self,
        tmc: TMCWrapper,
        sdp: SDPWrapper,
        csp: CSPWrapper,
        dishes: DishesWrapper,
    ) -> None:
        """Initialize the telescope test structure with the given devices."""
        self._tmc = tmc
        self._sdp = sdp
        self._csp = csp
        self._dishes = dishes
        # TODO: Add here "health checks" (?)

    TEARDOWN_TIMEOUT = 50

    def tear_down(self) -> None:
        """Tear down the entire telescope test structure.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()

        # Subscribe to the obsState events to be sure that
        # teardown moves the system to the expected state.
        event_tracer = TangoEventTracer()
        event_tracer.subscribe_event(self.tmc.subarray_node, "obsState")
        event_tracer.subscribe_event(self.csp.csp_subarray, "obsState")
        event_tracer.subscribe_event(self.sdp.sdp_subarray, "obsState")

        self.tmc.tear_down()
        self.sdp.tear_down()
        self.csp.tear_down()
        self.dishes.tear_down()

        # Assert the system is in the expected state after the teardown
        assert_that(event_tracer).described_as(
            "FAIL IN TEARDOWN PROCEDURE: "
            "TMC Subarray node "
            f"({self.tmc.subarray_node}) "
            "ObsState is supposed to be EMPTY after the teardown."
        ).within_timeout(self.TEARDOWN_TIMEOUT).has_change_event_occurred(
            self.tmc.subarray_node, "obsState", ObsState.EMPTY
        )
        assert_that(event_tracer).described_as(
            "FAIL IN TEARDOWN PROCEDURE: "
            "CSP Subarray node "
            f"({self.csp.csp_subarray}) "
            "obsState is supposed to be EMPTY after the teardown."
        ).within_timeout(self.TEARDOWN_TIMEOUT).has_change_event_occurred(
            self.csp.csp_subarray, "obsState", ObsState.EMPTY
        )
        assert_that(event_tracer).described_as(
            "FAIL IN TEARDOWN PROCEDURE: "
            "SDP Subarray node "
            f"({self.sdp.sdp_subarray}) "
            "obsState is supposed to be EMPTY after the teardown."
        ).within_timeout(self.TEARDOWN_TIMEOUT).has_change_event_occurred(
            self.sdp.sdp_subarray, "obsState", ObsState.EMPTY
        )

    def fail_if_not_set_up(self) -> None:
        """Fail if the telescope test structure is not set up.

        :raises ValueError: If one or more sub-systems are missing.
        """
        if (
            self._tmc is None
            or self._sdp is None
            or self._csp is None
            or self._dishes is None
        ):
            raise ValueError(
                "Telescope test structure is not set up "
                "(one or more sub-systems are missing). Sub-systems: "
                f"TMC={self._tmc}, SDP={self._sdp}, "
                f"CSP={self._csp}, Dishes={self._dishes}.\n"
                "Please set up the telescope test structure first calling the "
                "`set_up` method."
            )

    # -----------------------------------------------------------------
    # Other "technical" commands
    # (if you are looking for the "business" commands, check the
    # TelescopeAction subclasses)

    def clear_command_call(self) -> None:
        """Clear the command call on the telescope (if needed).

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()

        self.sdp.clear_command_call()
        self.csp.clear_command_call()
        self.dishes.clear_command_call()

    def set_subarray_id(self, subarray_id: int) -> None:
        """Create subarray devices for the requested subarray.

        :param subarray_id: The Subarray ID to set.

        :raises ValueError: If one or more sub-systems are missing.
        """
        self.fail_if_not_set_up()

        self.sdp.set_subarray_id(subarray_id)
        self.csp.set_subarray_id(subarray_id)
        self.tmc.set_subarray_id(subarray_id)
