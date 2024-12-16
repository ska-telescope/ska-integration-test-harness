"""A wrapper for an emulated CSP."""

from ska_integration_test_harness.emulated.utils.teardown_helper import (  # pylint: disable=line-too-long # noqa: E501
    EmulatedTeardownHelper,
)
from ska_integration_test_harness.structure.csp_wrapper import (  # pylint: disable=line-too-long # noqa: E501
    CSPWrapper,
)


class EmulatedCSPWrapper(CSPWrapper):
    """A wrapper for an emulated CSP.

    Differently from the production CSP wrapper, when a move to on or
    move to off command is called, the CSP master is set to the desired
    state directly. Moreover, the tear down implements the usual
    procedure for emulated devices.
    """

    # --------------------------------------------------------------
    # Subsystem properties definition

    def is_emulated(self) -> bool:
        return True

    # --------------------------------------------------------------
    # Specific CSP methods and properties

    def tear_down(self) -> None:
        """Tear down the CSP.

        The procedure is the following:
        - Reset the health state for the CSP master and the CSP subarray.
        - Clear the command call on the CSP subarray.
        - Reset the transitions data for the CSP subarray.
        - Reset the delay for the CSP subarray.
        """
        EmulatedTeardownHelper.reset_health_state(
            [self.csp_master, self.csp_subarray]
        )
        EmulatedTeardownHelper.clear_command_call([self.csp_subarray])
        EmulatedTeardownHelper.reset_transitions_data([self.csp_subarray])
        EmulatedTeardownHelper.reset_delay([self.csp_subarray])
        EmulatedTeardownHelper.unset_defective_status([self.csp_subarray])

    def clear_command_call(self) -> None:
        """Clear the command call on the CSP."""
        EmulatedTeardownHelper.clear_command_call([self.csp_subarray])
