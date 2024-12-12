"""Generate some termination conditions for the subarray."""

from ska_control_model import ObsState

from ska_integration_test_harness.actions.expected_event import (
    ExpectedEvent,
    ExpectedStateChange,
)
from ska_integration_test_harness.inputs.json_input import StrJSONInput
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)


def all_subarrays_have_obs_state(
    telescope: TelescopeWrapper, expected_obs_state: ObsState
) -> list[ExpectedEvent]:
    """Termination condition for waiting subarrays to have a certain obs state.

    Generate a termination condition for waiting all active subarray devices
    (across TMC, CSP and SDP) to have a certain obs state.

    :param telescope: The telescope wrapper.
    :param expected_obs_state: The expected obs state.

    :return: The termination condition, as a sequence of expected events.
    """
    res = [
        ExpectedStateChange(
            telescope.csp.csp_subarray, "obsState", expected_obs_state
        ),
        ExpectedStateChange(
            telescope.sdp.sdp_subarray, "obsState", expected_obs_state
        ),
        ExpectedStateChange(
            telescope.tmc.subarray_node, "obsState", expected_obs_state
        ),
    ]

    # csp subarray leaf node may not be yet initialised
    if telescope.tmc.is_subarray_initialised():
        res.extend(
            [
                ExpectedStateChange(
                    telescope.tmc.csp_subarray_leaf_node,
                    "cspSubarrayObsState",
                    expected_obs_state,
                ),
                ExpectedStateChange(
                    telescope.tmc.sdp_subarray_leaf_node,
                    "sdpSubarrayObsState",
                    expected_obs_state,
                ),
            ]
        )

    return res


# TODO: remove if not used
# def subsystems_have_telescope_state(
#     telescope: TelescopeWrapper, expected_state: tango.DevState
# ) -> list[ExpectedEvent]:
#     """Termination condition for waiting devices to have a certain state.

#     Generate a termination condition for waiting all active controller and
#     subarray devices (across CSP and SDP) to have a certain telescope
#     state. The involved devices are:

#     - CSP Master Node (State attribute, only if Mid is supported)
#     - SDP Subarray Node (State attribute)
#     - SDP Master Node (State attribute)

#     :param telescope: The telescope wrapper.
#     :param expected_state: The expected state.

#     :return: The termination condition, as a sequence of expected events.
#     """
#     res = [
#         ExpectedStateChange(
#             telescope.tmc.central_node,
#             "telescopeState",
#             expected_state,
#         ),
#         ExpectedStateChange(
#             telescope.sdp.sdp_subarray, "State", expected_state
#         ),
#         ExpectedStateChange(telescope.sdp.sdp_master,
# "State", expected_state),
#     ]

#     # CSP is supposed to change state only if Mid is supported
#     if telescope.tmc.supports_mid():
#         res.append(
#             ExpectedStateChange(
#                 telescope.csp.csp_master, "State", expected_state
#             ),
#         )
#     return res


def dishes_have_dish_mode(
    telescope: TelescopeWrapper, expected_dish_mode: str
) -> list[ExpectedEvent]:
    """Termination condition for waiting dishes to have a certain dish mode.

    Generate a termination condition for waiting all active dishes to have a
    certain dish mode.


    :param telescope: The telescope wrapper.
    :param expected_dish_mode: The expected dish mode.

    :return: The termination condition, as a sequence of expected events.
    """
    return [
        ExpectedStateChange(dish, "dishMode", expected_dish_mode)
        for dish in telescope.dishes.dish_master_list
    ]


def resources_are_released(telescope: TelescopeWrapper) -> list[ExpectedEvent]:
    """Termination condition to check that resources are released.

    The assignedResources attribute of the SubarrayNode should be empty.

    :param telescope: The telescope wrapper.

    :return: The termination condition, as a sequence of expected events.
    """
    # pre_action_attr_value = telescope.tmc.subarray_node.assignedResources

    return [
        ExpectedEvent(
            device=telescope.tmc.subarray_node,
            attribute="assignedResources",
            # predicate=lambda event: not event.attribute_value,
            predicate=lambda event: len(event.attribute_value) == 0
            or (
                len(event.attribute_value) == 1
                and StrJSONInput(event.attribute_value[0]).as_dict()
            ),
        )
    ]
