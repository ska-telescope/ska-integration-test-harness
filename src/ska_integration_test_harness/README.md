# Architecture overview of the SKA Integration Test Harness

This document provides an overview of the architecture of the SKA Integration Test Harness and the principles behind it. It is on purpose written as an
high-level document, to provide a general understanding of the design decisions
and the conventions used in the test harness, more than a detailed description
of the code.

Since the test harness is still in development, both the code and the design
may change in the future. The overall principles, however, will likely remain
the same.

This document is updated the last time on July-August 2024.

## Architecture of the test harness

This test harness is code that glues integration test scripts to the SUT. 
It is designed to provide a consistent interface for all tests,
to be **powerful** (allowing for complex tests), to be **flexible**
(extensible to meet the needs of different SUTs and different tests),
to be **easy to use** (so that tests can be written quickly),
to be **easy to maintain** (so that tests can be updated quickly)
and **reliable** (so that tests can be trusted).

For the  time being (August 2024) the test harness is designed to work with Tango Devices,
and specifically to support tests for integration of TMC with CSP in MID,
but it can be extended to work with other types of components.

This test harness comprises:

* **facades**, aimed at providing a consistent interface to the SUT
  so that test scripts are insulated from internal details 
* **actions**, which are the building blocks of tests and each include
  a relatively complex action that can be performed on the SUT
  (like sending a command to a device)
* **wrappers**, which wrap subsystems of the SUT and provide a structured
  interface to them and to their devices, eventually providing an
  abstraction over some operations (e.g., operations that may differ
  between a production device and an emulator)
* **inputs**, which are used to generate 
  the JSON input data for the various commands that are sent to the SUT
* **configurations**, which are used to gather configuration data or flags
  from the environment and provide a structured interface to them
* **emulators**, which are real tango devices whose behaviour is programmed
  to simulate in a very simple way the behaviour of real devices.
  They are needed to ensure that SUT is embedded in the environment
  that it expects.
  - for now, emulators are those used in the TMC-MID integration
    tests ([Code](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-common/-/tree/master/src/ska_tmc_common/test_helpers?ref_type=heads), [Documentation](https://developer.skao.int/projects/ska-tmc-common/en/latest/HelperDevices/TangoHelperDevices.html))

## RULES

### RULE 1: Tests are agnostic to the test environment

Test scripts should know as little as possible about the test environments
so that the same test, with different configurations, can be run in different
environments (like the cloud, an ITF, a PSI). 
As a consequence a test script should interact only with facades, with wrappers and with inputs: 
no actions, no configurations. Interaction with wrappers is needed to write meaningful assertions. 

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
emulators without knowing which is which. See below for examples.

## Architecture

![configurations](architecture-config.png "Logical architecture of the test harness (configurations)")
![configurations, facades and wrappers](architecture-facades.png "Logical architecture of the test harness (facades)")
![configurations, facades and wrappers](architecture-actions.png "Logical architecture of the test harness (actions and wrappers)")


(the source code of these diagrams is in `*.plantuml` and can be updated with `java -jar plantuml.jar *.plantuml`; likewise for the other diagrams, or use the attached Makefile and do ```make update-diagrams```).


## Conventions

The test harness files are organized in the following way:

* Facades have to be added in the `facades` folder
* Actions have to be added in the `actions` folder
* Abstract definitions of the wrappers have to be added in the 
  `structure`, while `emulated` and `production` folders contain the
  concrete implementations of the wrappers for the emulated and production
  subsystems.
* Input-related classes have to be added in the `inputs` folder
* configuration-related classes have to be added in the
  `config` folder.
* The `init` folder contains all the factories needed to initialize
  the test harness. 

The top-level ```tests``` folder contains the unit tests for the harness itself.

## Design decisions

### Why using facades?
As mentioned above we want to insulate test scripts from the details
of the SUT. 

For example, a test that verifies that the SCAN command works as expected,
will use a facade of the TMC Central Node and a facade of the
TMC Subarray Node. These facades will provide properties of the two components
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
In this case the complex system is the test harness itself, with the wrappers
that represent the SUT and the actions that act over the wrappers.


### Why using actions?

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
They embed both the operations to be performed and their termination condition,
that is checked within a timeout. Termination conditions
can only be expressed with a list of expected tango change events.

An action can eventually be "executed", by calling the `execute` method of
the action. This method will perform the operation, wait for its termination
and return a result. The details of how to execute an action (for example,
what Tango Command to send to a device) are hidden from the test script.

The test scripts invokes a facade method called `scan()`, which instantiates
an action called `SubarrayScan`, adds to it the necessary arguments and then
calls its `execute` method. The `execute` method gathers the necessary
device proxies, sends the `scan` command to the appropriate device and waits
for the set of events listed in the action to occur.

Actions are based on the
[COMMAND](https://refactoring.guru/design-patterns/command),
[TEMPLATE METHOD](https://refactoring.guru/design-patterns/template-method) and
[COMPOSITE](https://refactoring.guru/design-patterns/composite)
design patterns. 

To implement an action, one has to extend the
`TelescopeAction` base class and override the abstract methods (to define the *procedure* that implements the action and the *synchronization condition* that defines when the action is completed).


### Why using wrappers?

Wrappers embed the parts of the SUT that the test script needs
to interact with. In the current version of the harness, wrappers wrap Tango
Device Proxies. 
Their responsibility is to hold and hide the details about how to interact
to such devices (i.e. names of commands, format of their input,
attribute names and values, etc.).

The main access point to the wrappers (`TelescopeWrapper`) is intended to be a [SINGLETON](https://refactoring.guru/design-patterns/singleton), so once it's initialized,
you can access it from everywhere in the code just by accessing its instance. 
This way multiple facades and actions can share the same 
(already configured) instance of the wrapper without being aware of it
and without the need to pass it around.


### Why using JON data builder?

Some actions over the telescope (such as the *scan*, *configure*, *assign resources* commands) require an input argument that is a JSON string.
Also some *reset* procedures require default arguments to be used to call
the various commands. 

Passing these arguments around as strings or dictionaries is not a good
practice, because it makes the code more technical (full of type conversions,
explicit file reading, etc.) and so less readable. The idea of argument
factories is to provide a structured object-oriented way to represent those
arguments.

An abstract base class (`JSONInput`) defines what is expected from a JSON input (return a string or a dictionary, create a copy of itself with some
values changed, etc.). Through a concrete implementation of this class, 
one can specify how to generate this JSON (e.g., accessing your own test data folders, associating keywords to each or your specific input, 
through a hardcoded dictionary, etc.).

This solution is inspired by various creational design patterns, such as
[FACTORY METHOD](https://refactoring.guru/design-patterns/factory-method),
[ABSTRACT FACTORY](https://refactoring.guru/design-patterns/abstract-factory)
and [BUILDER](https://refactoring.guru/design-patterns/builder).

In `inputs` folder you can find some examples of JSON input classes, but also
other input-output related classes.

### Why using configuration classes?

These are mechanisms that collect configuration data from files or 
runtime flags, represent them in objects, and support fixtures to setup 
the proper instances of the test harness.

There are a number of classes that represent the default configuration of 
the structure of the SUT. For example, the class `TMCConfiguration` contains
 the names (i.e. TRLs) of the devices that are part of the TMC. The class
`CSPConfiguration` contains the names of the devices that are part of the CSP.
The directive to use the emulated or the production devices is another
example of configuration data (very important for the initialization of the
test harness).

Since the configuration may come from different sources (environment variables,
hardcoded values, files, etc.) and since it's easy to loose track of them an
object-oriented approach is used to represent them in a structured way and
to provide a consistent interface to them. To avoid inconsistencies, a 
*factory* class is used to create
all the instances of those configurations. This way, the test harness 
initialization procedure or any other part of the
code can access the same configurations.

## How to use and extend this harness

At the moment (August 2024) this harness has no well-defined
extension points yet and it is pretty specific to the TMC-CSP integration tests 
in MID. Based on feedback and on the evolution of the project, the harness will be extended to be more flexible and to support more use cases. 

### How to use this test harness

To use this test harness you need to:

- Import the library `ska_integration_test_harness` in your test script.
  Right now, the library is not yet published as a package, but you can
  import it from the git source code (see the top-level `README.md` file).
- In your test setup, initialize once the wrappers using the appropriate builders
  you can find in the `init` module.
  - *A good place to do this may be a `pytest.fixture`. For how `pytest` fixtures
    work, a good way you can use to execute the *teardown* method after 
    your test are finished is to*:
    - *create an instance using the appropriate builder,*
    - *`yield` it to the test function,*
    - *and then call the `teardown` method on the instance, which will
      be executed after the test is finished.*
  - The builder will ask you to load and validate some configuration files.
    The main one is a YAML file, that for each subsystem it contains:
    - a flag to tell if the device is emulated or production,
    - the names of the devices that are part of the subsystem.
  - The builder will also ask you to provide some JSON inputs for various
    commands (mostly needed for the `teardown` procedures).
- The same way, initialize the facades you need (just creating instances of them
  and passing your wrapper instance to them).
- In your tests, use the facade methods to interact with the SUT and the
  facade properties to access directly the (already configured) device
  proxies.
  - *Remember: each facade represent a subsytem, so if you want to access a
    certain device, ask yourself: which subsystem does it belong to?*
  - *Since this test harness is focused on TMC, most if not all of the actions
    are done by calling commands on TMC central node or TMC subarray node.*

For a more detailed example, see the top-level `README.md` in this repository.

Within the current limitations, your main ways to extend this test harness
are

- **Add new actions**: you can add new actions by sub-classing 
  the `TelescopeAction` class and implementing the abstract methods. 
  You can also create a sequence of actions by sub-classing the 
  `TelescopeActionSequence` class and implementing the abstract methods.
- **Add new facades**: you can create new facades that access the telescope
  wrappers and the actions, hiding the implementation details for the tester.
- **Add new input classes**: you can create new input classes that generate
  the JSON input for the actions in your own ways (e.g., accessing your own
  test data folders, etc.).

If you wish to do more, you may copy this structure and adapt it to your needs.


### How you will be able to extend this test harness in the future

In the future, the test harness will be more flexible and will not be centered
strictly on the TMC-X integration tests in MID. 


Please reach out to the developers of this test harness because the end goal
is to transform this code into a platform that is separate from its customizations. 
Understanding where to put the boundary between the two is important and can only be done
by understanding the needs of the users.
