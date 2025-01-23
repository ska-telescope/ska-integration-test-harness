A Generic Core for the ITH as a Platform
=========================================

Temporary documentation for the ITH as a Platform idea. This document
will be used to collect ideas and show example of how the ITH as a Platform
can be used and extended.

- TODO: introduce the idea of the ITH as a Platform
- TODO: introduce the parts of the generic core

Actions, Assertions and Synchronisation
---------------------------------------

TODO: introduce the idea of actions, assertions and synchronisation

Usage Example 1 (simple): Command + LRC & State Synchronisation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this first simple example we will show how to use the action mechanism
with the already provided blocks to execute a simple Tango command and
to check the state of the device after the command execution. To do so:

1. We will create an instance of a ``TangoLRCAction`` that sends a command to a
   device and waits for the LRC to complete.
2. We specify a pre-condition that checks the devices are in a particular state
   before the command is executed (optional, probably you will use them
   just in particular cases where you need to be sure of the initial state).
3. We specify a set of post-conditions to say that we expect the devices to
   transition to a particular state after the command is executed


.. code-block:: python

    import tango
    import json
    
    from ska_integration_test_harness.common.actions import (
        TangoLRCAction
    )
    from ska_integration_test_harness.common.assertions import (
        AssertLRCCompletion
    )
    from ska_integration_test_harness.core.assertions import (
        AssertDevicesStateChanges, AssertDevicesAreInState,
    )
    from ... import ObsState

    # Let's assume we have a Target device that is expected
    # to receive the command
    target_device = tango.DeviceProxy("tmc-low/centralnode/0")

    # ... and a set of other devices that are expected to change state
    # after the command is executed
    subarray_devices = [
        tango.DeviceProxy("tmc-low/subarray/01"),
        tango.DeviceProxy("csp-low/subarray/01"),
        tango.DeviceProxy("sdp-low/subarray/01"),
        tango.DeviceProxy("mccs/subarray/01"),
    ]

    # GOAL: sending 
    
    # Create an instance of an action that sends a command to a device
    command = TangoLRCAction(
        target_device=target_device,
        command_name="AssignResources",
        command_input=json.read("low/input/assign_resources.json"),
    )
    
    # Through pre-conditions I can specify the expected initial state
    # for the action to be run successfully. It's totally optional
    # and in many cases you will not need them (if not to have
    # "stronger" tests)
    command.add_preconditions(
        # I expect the devices to be in the EMPTY state
        AssertDevicesAreInState(
            devices=subarray_devices,
            attribute_name="obsState",
            expected_value=ObsState.EMPTY,
        ),
    )
    
    # It would be good I specify a set of post-conditions to check
    # the state of the devices after the command is executed. Those
    # post-conditions will be used also for synchronisation
    # (within the given common timeout)
    command.add_postconditions(
        # I expect a state change in the devices to the RESOURCING state
        AssertDevicesStateChanges(
            devices=subarray_devices,
            attribute_name="obsState",
            expected_value=ObsState.RESOURCING,
        ),
        # I expect a state change in the devices to the IDLE state
        AssertDevicesStateChanges(
            devices=subarray_devices,
            attribute_name="obsState",
            expected_value=ObsState.IDLE,
            previous_value=ObsState.RESOURCING,
        ), 
    ).set_postconditions_timeout(60) # I can set a timeout for the action

    # I can also add a post-condition to check the LRC completion
    # (and fail early if the LRC fails)
    command.add_lrc_completion_to_postconditions()
    command.add_lrc_errors_to_early_stop()

    # DOUBT: should we really expose a AssertLRCCompletion? Wouldn't
    #        be better some kind of method like
    #        ``add_assert_lrc_completion_postcondition()``?
    #       (or something similar)

    # NOTE: the assertion will be checked in the order they are added
    #       and the action will fail as soon as one of them fails
    
    # NOTE: with the last post-condition I'm also specifying that
    #       the action will fail early if some LRC fail event
    #       is detected

    # NOTE: Potentially I can chain all those methods calls in a single
    #       line, like I would do with a builder pattern

    # Execute the action
    command.execute()



Usage Example 2 (intermediate): Custom action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


In this second example we will show how to create a custom action that
activates a device (through ``adminMode`` attribute) and waits for the
device to be reachable. It is different from the previous one because:

- the action is not actually a command, but something different
- the synchronisation is not really standard, because the subscriptions
  with the tracer are deferred (I cannot do them before the devices are
  reachable!)

Because of this, instead of using the already provided blocks, we will
will directly take the ``SUTAction`` base class and implement a totally
custom procedure.

.. code-block:: python

    import tango

    from ska_integration_test_harness.core.actions import SUTAction
    from ska_tango_testing.integration import TangoEventTracer

    class ActivateSubsystem(SUTAction):
        """Activate a subsystem and ensure it is reachable.
        
        NOTE: when I implement a custom action, I can assume that
        the action execution will happen through the following
        steps (all triggered by the ``execute`` method):

        - setup()
        - verify_preconditions()
        - execute_procedure()
        - verify_postconditions()
        
        As I can see, all those steps are hooks I can override.
        ``execute_procedure`` is the only mandatory one, the others
        are optional.
        """
    

        def __init__(
            self, 
            controller_device: tango.DeviceProxy,
            other_devices: list[tango.DeviceProxy],
            timeout: float = 10
        ):
            self.controller_device = controller_device
            self.other_devices = other_devices
            self.timeout = timeout
            
            self.tracer = TangoEventTracer()

        def setup(self):
            # (always good to call the super method)
            super().setup()

            # clean up the tracer
            self.tracer.unsubscribe_all()
            self.tracer.clear_events()

        # (I am not interested in pre-conditions in this case)

        def execute_procedure(self):
            # Activate the controller device (if not already)
            self.controller_device.adminMode = AdminMode.ONLINE

        def verify_postconditions(self):
            # (always good to call the super method)
            super().verify_postconditions()

            # Subscribe to the telescopeState event (deferred, normally
            # I would do this in the setup method)
            self.tracer.subscribe_event(self.controller_device, "telescopeState")
            for device in self.other_devices:
                self.tracer.subscribe_event(device, "telescopeState")

            # Wait for the devices to be reachable
            assertpy_context = assert_that(tracer).described_as(
                "The devices are expected to be reachable"
            ).within_timeout(self.timeout).has_change_event_occurred(
                self.controller_device, "telescopeState",
                # let's say that the device is reachable when it is in one
                # of the following states (just an example to show how
                # arbitrary complex the post-condition can be)
                custom_matcher=lambda event: event.attribute_value in [
                    tango.DevState.ON,
                    tango.DevState.OFF,
                    tango.DevState.STAND_BY,
                ]
            )

            for device in self.other_devices:
                assertpy_context.has_change_event_occurred(
                    device, "telescopeState", tango.DevState.ON
                )

            # Ensure admin mode now is online for all devices
            for device in self.other_devices + [self.controller_device]:
                assert_that(device.adminMode).is_equal_to(AdminMode.ONLINE)
    
    action = ActivateSubsystem(
        controller_device=tango.DeviceProxy("csp-low/centralnode/01"),
        other_devices=[
            tango.DeviceProxy("csp-low/subarray/01"),
            tango.DeviceProxy("csp-low/subarray/02"),
        ],
        timeout=15
    )

    # Let's say the action is flaky and I want to retry it up to 3 times
    last_error = None
    for i in range(3):
        try:
            action.execute()
            break
        except AssertionError as e:
            logger.warning(f"Attempt {i+1} failed: {e}")
            last_error = e
    else:
        raise AssertionError(
            "The action failed after 3 attempts"
        ) from last_error




