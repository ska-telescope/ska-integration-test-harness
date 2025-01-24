

ITH as a Platform: Introduction and practical examples
======================================================

Temporary documentation for the ITH as a Platform idea. This document
will be used to collect ideas and show example of how the ITH as a Platform
can be used and extended.

- TODO: introduce the idea of the ITH as a Platform
- TODO: introduce the parts of the generic core

A quick guide to find stuff:

- API documentation for the core: :py:mod:`ska_integration_test_harness.core`
- API documentation for the extensions:
  :py:mod:`ska_integration_test_harness.extensions`
- git branch & MR where I am working on this:
  
  - Merge Request: `MR 13 <https://gitlab.com/ska-telescope/ska-integration-test-harness/-/merge_requests/13>`_
  - Git Branch `sst-1018-ith-as-platform-actions <https://gitlab.com/ska-telescope/ska-integration-test-harness/-/tree/sst-1018-ith-as-platform-actions>`_

- Jira tickets:
  
  - `SST-1018 (generic ticket) <https://jira.skatelescope.org/browse/SST-1018>`_
  - `SST-1019 (CSP.LMC support) <https://jira.skatelescope.org/browse/SST-1019>`_

- Code snippets examples: :doc:`./ith_as_a_platform` (this document)

Actions, Assertions and Synchronisation
---------------------------------------

TODO: introduce the idea of actions, assertions and synchronisation. For
the moment, read:

- :py:mod:`ska_integration_test_harness.core.actions`
- :py:mod:`ska_integration_test_harness.core.assertions`

Usage Example 1 (simple): Command + LRC & State Synchronisation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this first simple example we will show how to use the action mechanism
with the already provided blocks to execute a simple **Tango command call**,
the consequent **LRC completion check** and the **state synchronisation**.

Let's assume we have a Tango device and that we want to send it a command.
Let's also assume
that command 1) is a Long Running Command (LRC) and 2) will change the state
of some other devices to a particular state. Let's say we want to be sure
the command is executed correctly (without errors) and that the desired states
are reached. To do so, we proceed the following way:

1. we define the command as a
   :py:class:`ska_integration_test_harness.extensions.actions.TangoLRCAction`
2. we define a pre condition
   :py:class:`ska_integration_test_harness.core.assertions.AssertDevicesAreInState`
   to check the initial state of the devices and be sure the action is executed
   from a valid initial state
3. we define the expected state transitions as post conditions using the class
   :py:class:`ska_integration_test_harness.core.assertions.AssertDevicesStateChanges`
4. we add some directives to impose a timeout, to synchronise also the LRC
   completion and to fail early if some LRC error is detected
5. given the action object enriched with all those directives, we execute it


.. code-block:: python

    import tango
    import json
    
    from ska_integration_test_harness.extensions.actions import (
        TangoLRCAction
    )
    from ska_integration_test_harness.core.assertions import (
        AssertDevicesStateChanges, AssertDevicesAreInState,
    )
    from <...> import ObsState

    # The device where the command will be sent
    target_device = tango.DeviceProxy("tmc-low/centralnode/0")

    # the devices that are expected to change state as result of the command
    subarray_devices = [
        tango.DeviceProxy("tmc-low/subarray/01"),
        tango.DeviceProxy("csp-low/subarray/01"),
        tango.DeviceProxy("sdp-low/subarray/01"),
        tango.DeviceProxy("mccs/subarray/01"),
    ]


    # 1. Create an instance of an action that sends a command to a device
    command = TangoLRCAction(
        target_device=target_device,
        command_name="AssignResources",
        command_input=json.read("low/input/assign_resources.json"),
    )
    
    # 2. Through pre-conditions I can specify the expected initial state
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
    
    # 3. Through post-conditions I can specify the expected state changes
    # after the action is executed.
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
    )

    # 4. Through some further directives I impose the fact that I want
    # to synchronise the LRC completion and that I want to fail early
    # if some LRC error is detected. I set also a timeout for the action
    # to define the maximum time the action can take to complete (if no
    # LRC error is detected)
    command.add_lrc_completion_to_postconditions()
    command.add_lrc_errors_to_early_stop()
    command.set_timeout(30)

    # 5. Execute the action
    command.execute()

Some further comments on this code:

- The pre-conditions will be verified before the command is called and
  if they fail the command will not be executed
- The post-conditions will be verified after the command is called, they will
  be verified in the order they are added and if one fails the others will not
  be verified.
- The timeout determines the maximum wait time for
  the post-conditions to be verified (it doesn't affect the pre-conditions
  or the command call)
- The LRC completion check is itself a post-condition, so it will be
  verified after the command is called and after the other post-conditions
  are verified, within the same shared timeout. Potentially you can specify
  which result codes are considered as successful completions.
- The LRC error can be seen as a sort of "sentinel", that monitor the
  events and stops the post-conditions verification early if a
  LRC error is detected. Potentially you can specify which result codes
  are considered as errors.
- The synchronisation is internally managed using a
  :py:class:`ska_tango_testing.integration.TangoEventTracer`; all the
  subscriptions and the events resets are done automatically, as well as
  the memorisation of the LRC ID.

Usage Example 2 (intermediate): Custom action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not all the actions are simple command calls, and also not all action
synchronisation logic is standard. In this second example we will show how
to create a custom action that operates on a device Tango attribute to
configure a set of devices to be reachable (and waits for them to be).

Let's assume we have a controller device that has to be activated to make
it and some other devices reachable. Let's say that the controller device
has an attribute ``adminMode`` that can be set to ``ONLINE`` to activate
the devices. Let's also say that to detect the reachability of the devices
we can subscribe to the ``telescopeState`` event and that we consider the
devices reachable when they are in one of the following states:
``ON``, ``OFF``, ``STAND_BY``, but the subscription must be done **after** the
activation of the controller device (otherwise it will not work). Finally,
let's say this is a setup procedure and for some reason it is flaky, and
we want to retry it up to 3 times.

To do so, we proceed the following way:

1. We define a custom action subclassing the base class
   :py:class:`ska_integration_test_harness.core.actions.SUTAction`, which
   if essentially an empty shell
2. We override the ``execute_procedure`` method to implement the custom
   activation logic (in this case, setting the ``adminMode`` attribute)
3. We override the ``verify_postconditions`` method to implement the custom
   synchronisation logic (in this case, subscribing to the event and waiting
   for the devices to be reachable). We override also the ``setup`` method
   to clean up the event tracer and permit multiple runs
4. Provide a semantic description of the action (and use it when failing)
5. Create an action instance and run it with a retry loop


.. code-block:: python

    import tango

    from ska_integration_test_harness.core.actions import SUTAction
    from ska_tango_testing.integration import TangoEventTracer
    from <...> import AdminMode

    # Step 1: subclass the base class SUTAction to create a custom action
    # from scratch.
    class ActivateSubsystem(SUTAction):
        """Activate a subsystem and ensure it is reachable."""
    

        def __init__(
            self, 
            controller_device: tango.DeviceProxy,
            other_devices: list[tango.DeviceProxy],
            timeout: float = 10, 
            **kwargs
        ):  
            """Initialise the action.

            :param controller_device: the device that has to be activated
            :param other_devices: the devices that have to be reachable
            :param timeout: the maximum time to wait for the devices
                to be reachable
            :param kwargs: additional parameters, see the base class
                :py:class:`ska_integration_test_harness.core.actions.SUTAction`
                for more details. 

            """
            # we always call the super method and pass the kwargs. This is a
            # trick to allow retro-compatibility with the base class in the
            # required parameters.
            super().__init__(**kwargs)

            self.controller_device = controller_device
            self.other_devices = other_devices
            self.timeout = timeout
            
            self.tracer = TangoEventTracer()

        # (I am not interested in pre-conditions and I can simply skip them)

        # ---------------------------------------------------------------------
        # Step 2: implement the custom activation logic
        def execute_procedure(self):
            self.controller_device.adminMode = AdminMode.ONLINE

        # ---------------------------------------------------------------------
        # Step 3: implement the custom synchronisation logic (and clean up)

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
                self.description() + 
                " Controller device is supposed to be reachable."
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
                assertpy_context.described_as(
                    self.description() + 
                    f" Device {device.dev_name()} is supposed to be reachable."
                ).has_change_event_occurred(
                    device, "telescopeState", tango.DevState.ON
                )

            # Ensure admin mode now is online for all devices
            for device in self.other_devices + [self.controller_device]:
                assert_that(device.adminMode).described_as(
                    self.description() + 
                    f" {device.dev_name()}.adminMode is supposed to be online."
                ).is_equal_to(AdminMode.ONLINE)

        def setup(self):
            # (always good to call the super method)
            super().setup()

            # clean up the tracer
            self.tracer.unsubscribe_all()
            self.tracer.clear_events()

        # ---------------------------------------------------------------------
        # Step 4: provide a semantic description of the action

        def description(self):
            return (
                f"Activate the subsystem {self.controller_device.name} and "
                f"ensure the devices {', '.join(d.name for d in self.other_devices)} "
                f"are reachable (within {self.timeout}s)."
            )

    # ---------------------------------------------------------------------
    # Step 5: create an action instance and retry it up to 3 times
    
    action = ActivateSubsystem(
        controller_device=tango.DeviceProxy("csp-low/centralnode/01"),
        other_devices=[
            tango.DeviceProxy("csp-low/subarray/01"),
            tango.DeviceProxy("csp-low/subarray/02"),
        ],
        timeout=15
    )

    errors = []
    for i in range(3):
        try:
            action.execute()
            break
        except AssertionError as e:
            logger.warning(f"Attempt {i+1} failed: {e}")
            errors.append(e)
    else:
        raise AssertionError(
            "The action failed after 3 attempts. Errors:\n" + 
            "\n".join(errors)
        ) from e[-1]

Some further comments on this code:

- The action base class is an empty shell, but it provides the basic
  structure of an action execution, which happens in the following way:
  when the ``execute`` method is called,
  
  1. the action is set up (``setup`` method)
  2. the pre-conditions are verified (``verify_preconditions`` method)
  3. the custom procedure is executed (``execute_procedure`` method)
  4. the post-conditions are verified (``verify_postconditions`` method)

- every time an action is executed, the first step is always the ``setup``
  method, which is a good place to clean up procedure to enable multiple
  runs of the action
- ``execute_procedure`` is the only mandatory method to implement, it is
  the place where the custom logic of the action is implemented
- ``verify_preconditions`` and ``verify_postconditions`` are optional
  methods, but they are very useful to ensure the action is executed in
  a valid state and that the expected results are reached
- the ``description`` method is a semantic description of the action, it
  is used when the action fails to provide a meaningful error message
- the retry loop is a simple way to retry the action up to 3 times