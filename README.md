# ska-integration-test-harness

## Overview

For now, a test harness for TMC-CSP integration tests. In future,
a generic test harness integration testing an arbitrary combination
of production or emulated SKA subsystems.

More information will be added here as the project progresses.

## Architecture of the test harness

This test harness is code that glues integration test scripts to the SUT. 
It is designed to provide a consistent interface for all tests,
to be **powerful** (allowing for complex tests), to be **flexible**
(extensible to meet the needs of different SUTs and different tests),
to be **easy to use** (so that tests can be written quickly),
to be **easy to maintain** (so that tests can be updated quickly)
and **reliable** (so that tests can be trusted).

For the  time being the test harness is designed to work with Tango Devices,
and specifically to support tests for integration of TMC with CSP in MID,
but it can be extended to work with other types of components.

This test harness comprises:

* **facades**, aimed at providing a consistent interface to the SUT
  so that test scripts are insulated from internal details 
* **actions**, which are the building blocks of tests and each include
  a relatively complex action that can be performed on the SUT
  (like sending a command to a device)
* **wrappers**, which wrap subsystems of the SUT and provide a structured
  interface to them and to their devices, eventually permitting the
  abstraction over some operations (e.g., operations that may differ
  between a production device and an emulator)
* **inputs**, which are used to generate and handle in a structured way
  the JSON input data for the various commands that are sent to the SUT
* **configurations**, which are used to gather configuration data or flags
  from the environment and provide a structured interface to them
* **emulators**, which are real tango devices whose behaviour is programmed
  to simulate in a very simple way the behaviour of real devices.
  The are needed to ensure that SUT is embedded in the environment
  that it expects. 
  <!--TODO: are emulators part of this test harness? -->


## RULES

### RULE 1: Tests are agnostic to the test environment

Test scripts should know as little as possible about the test environments
so that the same test, with different configurations, can be run in different
environments (like the cloud, an ITF, a PSI). 

### RULE 2: Tests are agnostic to the SUT ecosystem

Integration tests make use of emulators and simulators. In many cases test
scripts can be implemented in such a way that they do not know which devices
are real and which are emulated. In this way, the same test script can be run
with different configurations of real and emulated devices.

Of course, somewhere one needs to say that a device is emulated and what
should its behaviour be. This is done in the configuration files/flags and,
because emulated devices are de facto Tango Devices, they should be defined,
implemented and deployed prior to the execution of the test script
(and hence prior to the execution of the test harness).

In some cases it may be necessary for the test script to make assertions on
emulators (i.e. to use them as
@SPY [Spy objects as test doubles - Meszaros](http://xunitpatterns.com/Test%20Spy.html)).
In these cases such a test makes the assumption that the device is emulated.
By carefully writing assertions though, and through the use of 
[tracer objects](https://developer.skao.int/projects/ska-tango-testing/en/latest/guide/integration/index.html#tracer-objects),
it is possible to write tests that can be run with real devices and
emulators without knowing it. See below for examples.

## Conventions

The test harness files have this layout:

.
├── common_utils
├── emulated
│    ├── csp_devices.py
│    ├── dishes_devices.py
│    ├── sdp_devices.py
│    └── utils
│        └── teardown_helper.py
├── production
│    ├── csp_devices.py
│    ├── dishes_devices.py
│    ├── sdp_devices.py
│    └── tmc_devices.py
├── README.md
├── actions
│    ├── central_node
│    │    ├── central_node_assign_resources.py
│    │    ├── central_node_load_dish_config.py
│    │    ├── central_node_perform_action.py
│    │    ├── central_node_release_resources.py
│    │    ├── move_to_off.py
│    │    ├── move_to_on.py
│    │    └── set_standby.py
│    ├── expected_event.py
│    ├── sdp_subarray
│    │    └── subarray_simulate_receive_addresses.py
│    ├── state_change_waiter.py
│    ├── subarray
│    │    ├── force_change_of_obs_state.py
│    │    ├── obs_state_resetter_factory.py
│    │    ├── subarray_abort.py
│    │    ├── subarray_assign_resources.py
│    │    ├── subarray_clear_obs_state.py
│    │    ├── subarray_configure.py
│    │    ├── subarray_end_observation.py
│    │    ├── subarray_end_scan.py
│    │    ├── subarray_execute_transition.py
│    │    ├── subarray_five_point_calibration_scan.py
│    │    ├── subarray_force_abort.py
│    │    ├── subarray_move_to_off.py
│    │    ├── subarray_move_to_on.py
│    │    ├── subarray_release_all_resources.py
│    │    ├── subarray_restart.py
│    │    └── subarray_scan.py
│    ├── telescope_action.py
│    ├── telescope_action_sequence.py
│    └── utils
│        ├── generate_eb_pb_ids.py
├── config
│    ├── components_config.py
│    ├── configuration_factory.py
│    ├── emulation_config.py
│    ├── hardcoded_values.py
│    └── other_config.py
├── facades
│    ├── csp_facade.py
│    ├── dishes_facade.py
│    ├── sdp_facade.py
│    ├── tmc_central_node_facade.py
│    └── tmc_subarray_node_facade.py
├── init
│    └── telescope_structure_factory.py
├── inputs
│    ├── dict_json_input.py
│    ├── dish_mode.py
│    ├── json_input.py
│    ├── obs_state_commands_input.py
│    └── pointing_state.py
└── structure
    ├── csp_devices.py
    ├── dishes_devices.py
    ├── sdp_devices.py
    ├── telescope_wrapper.py
    └── tmc_devices.py

* Facades have to be added in the `facades` folder
* Actions have to be added in the `actions` folder
* Abstract definitions of the wrappers have to be added in the 
  `structure`, while `emulated` and `production` folders contain the
  concrete implementations of the wrappers for the emulated and production
  subsystems.
* Input-related classes have to be added in the `inputs` folder
* configuration-related classes have to be added in the
  `telescope_config` folder.


## How to use this harness

TODO: point to examples of test scripts

TODO: explain how to avoid making assumptions on emulators

## Design decisions

### Why use facades?
As mentioned above we want to insulate test scripts from the details
of the SUT. 

For example, a test that verifies that the SCAN command works as expected,
will use a facade of the TMC Central Node and a facade of the
TMC Subarray Node. These facade will provide properties of the two components
and methods to interact with them. The test script will not know that the
TMC Central Node is a Tango Device and that the TMC Subarray Node is a
Tango Device. It will not know that the TMC Central Node has a property
called `state` and that the TMC Subarray Node has a method called `scan`.
It will only know that there is a facade called `TMC` that has a property
called `central_node` and a facade called `subarray_node` that has
a method called `scan`. 

We opted for having more than just one facade, to avoid bloating a class with
too many unrelated functionalities
([Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)).

Facade is a design pattern
([FACADE](https://refactoring.guru/design-patterns/facade))
that provides a simplified interface to a complex system.
In this case the complex system is part of the SUT.


### Why use actions?

A test script has to interact with the SUT and send it operations to perform.
These operations are complex and require multiple steps, possibly involving
more than one component. In a distributed system like the telescope,
the operations are often asynchronous and involve multiple devices,
each evolving with its own timing.

Very frequently an operation is not just a single command, but a sequence
of commands. In these cases we often have to wait for something to happen
on some part of the SUT before starting a subsequent step. 

Actions are building blocks that encapsulate the complexity of
these operations. They are designed to be easy to use and to be powerful.
They embed both the operation to be performed and their termination condition,
that is checked within a timeout. For the time being termination conditions
can only be expressed with a list of expected tango change events.

An action can eventually be "executed", by calling the `execute` method of
the action. This method will perform the operation, wait for its termination
and return a result. The details of how to execute an action (for example,
what Tango Command to send to a device) are hidden from the test script.

The test scripts invokes a facade method called `scan()`, which instantiates
an action called `SubarrayScan`, adds to it the necessary arguments and then
calls its `execute` method. The `execute` method gathers the necessary
device proxies, sends the `scan` command to the TMC Subarray Node and waits
for the set of events listed in the action to occur.

Actions are based on the
[COMMAND](https://refactoring.guru/design-patterns/command),
[TEMPLATE METHOD](https://refactoring.guru/design-patterns/template-method) and
[COMPOSITE](https://refactoring.guru/design-patterns/composite)
design patterns. To implement an action, one has to subclass the
`TelescopeAction` class and override the methods:

- `_action` to implement the operation to be performed,
- `termination_condition` to implement the termination condition (as a set
  of expected events).


### Why using wrappers?

Wrappers embed the parts of the SUT that the test script needs
to interact with. In the current test harness wrappers wrap Tango
Device Proxies. 
Their responsibility is to hold the details about how to interact
to such devices (i.e. names of commands, format of their input,
attribute names and values, etc.).


### Why using argument factories?

TODO

### Why using configurators?

These are mechanisms that collect configuration data from files or
runtime flags, represent them in objects, and support fixtures to setup the
proper instances of the classes that represent the structure of the SUT
and the facades.

There are a number of classes that represent the default configuration
of the structure of the SUT. For example, the class `TMCConfiguration`
contains the names of the devices that are part of the TMC. The class
`CSPConfiguration` contains the names of the devices that are part of the CSP.

The class `ConfigurationFactory` is used to create instances of these classes.  

The class `TelescopeStructureFactory` is used to create instances
of the facades and the structure of the SUT. It uses the
`ConfigurationFactory` to create the instances of the classes that
represent the structure of the SUT.

## How to extend this harness

At the moment (July 2024) this harness has no well defined extension points.
So to adapt it to your needs the best way is to subclass key existing classes
and override their methods or create your own classes.

Key classes are:

* Facade: create your own facade class.
* Action: create your own action class by subclassing
`TelescopeAction` or `TelescopeActionSequence`.
* Wrapper: create your own wrapper class, by subclassing existing ones.
  You'll need also to subclass the top structure class
  which is `TelescopeWrapper`. 
* TestHarnessConfigurationFactory: subclass it and override its methods
  to provide alternative configurations. 
* TelescopeStructureFactory: subclass it and override its methods to
  instantiate your own facades.

<!-- TODO: explain better this part! -->