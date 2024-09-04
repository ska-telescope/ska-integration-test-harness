# Architecture overview of the SKA Integration Test Harness

This document provides an overview of the architecture of the SKA Integration Test Harness and the principles behind it. It is on purpose written as a
high-level document, to provide a general understanding of the design decisions
and the conventions used in the test harness, more than a detailed description
of the code.

Since the test harness is still in development, both the code and the design
may change in the future. The overall principles, however, will likely remain
the same.

This document is updated the last time on 3rd September 2024.

## Architecture of the test harness

This test harness is code that glues integration test scripts to the SUT.
It is designed to provide a consistent interface for all tests,
to be **powerful** (allowing for complex tests), to be **flexible**
(extensible to meet the needs of different SUTs and different tests),
to be **easy to use** (so that tests can be written quickly),
to be **easy to maintain** (so that tests can be updated quickly)
and **reliable** (so that tests can be trusted).

As of September 2024 the test harness is designed to work with Tango Devices,
and specifically to support tests for integration of TMC with CSP in MID,
but it can be extended to work with other types of components.

This test harness comprises:

* **facades**, aimed at providing a consistent interface to the SUT
  so that test scripts are insulated from internal details 
* **actions**, which are the building blocks of tests and each include
  a relatively complex action that can be performed on the SUT
  (like sending a command to a device)
* **wrappers**, which wrap sub-systems of the SUT and provide a structured
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
  - Currently, emulators are those used in the TMC-MID integration
    tests ([Code](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-common/-/tree/master/src/ska_tmc_common/test_helpers?ref_type=heads), [Documentation](https://developer.skao.int/projects/ska-tmc-common/en/latest/HelperDevices/TangoHelperDevices.html)). To use this test harness you have to
    deploy them in your environment and configure the test harness
    with the right device names.

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

![configurations](uml-docs/architecture-config.png "Logical architecture of the test harness (configurations)")
![configurations, facades and wrappers](uml-docs/architecture-facades.png "Logical architecture of the test harness (facades)")
![configurations, facades and wrappers](uml-docs/architecture-actions.png "Logical architecture of the test harness (actions and wrappers)")


(the source code of these diagrams is in `*.plantuml` and can be updated with `java -jar plantuml.jar *.plantuml`; likewise for the other diagrams, or use the attached Makefile and do ```make update-diagrams```).


## Conventions

The test harness files are organized in the following way:

* Facades have to be added in the `facades` folder
* Actions have to be added in the `actions` folder
* Abstract definitions of the wrappers have to be added in the 
  `structure`, while `emulated` and `production` folders contain the
  concrete implementations of the wrappers for the emulated and production
  sub-systems.
* Input-related classes have to be added in the `inputs` folder
* configuration-related classes have to be added in the
  `config` folder.
* The `init` folder contains all the factories needed to initialise
  the test harness. 

The top-level `tests` folder contains the unit tests for the harness itself.

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

For example, let's consider a test script that wants to send a scan command
to the TMC Subarray Node and synchronize at the end of the scan:

- the test script has (somehow - *see main README.md*) access to a facade
  of the TMC Subarray Node;
- the facade exposes a `scan()` method, which can be called by the tests;
- the `scan()` method which instantiates
  an action called `SubarrayScan`, adds to it the necessary arguments and 
  then calls its `execute` method;
- who implemented the class, defined all the related logic to send the scan
  command and - *optionally* - synchronize at the end of the scan operation
  in the same place (implementing two abstract methods);
- the actions interact with the correct wrappers (and consequently to the
  Tango devices) to perform the operation.

Actions are based on the
[COMMAND](https://refactoring.guru/design-patterns/command),
[TEMPLATE METHOD](https://refactoring.guru/design-patterns/template-method) and
[COMPOSITE](https://refactoring.guru/design-patterns/composite)
design patterns. 

To implement an action, one has to extend the
`TelescopeAction` base class and override the abstract methods
(to define the *procedure* that implements the action and the
*synchronization condition* that defines when the action is completed).
Note also that actions can be composed in sequences,
to perform more complex operations.(see `TelescopeActionSequence`). Note also
that actions can also be defined as a complex inheritance hierarchy, to
define common behaviours and to specialize them (give a look to the
existing actions to see how they are implemented).


### Why using wrappers?

Wrappers embed the parts of the SUT that the test script needs
to interact with. In the current version of the harness, wrappers wrap Tango
Device Proxies. 
Their responsibilities are to:

- define the structure of the SUT (i.e. which sub-systems are part of it and
  which devices are part of each sub-system);
- hold and hide some technical details about the interaction with such devices,
  that may differ between emulated and production devices;
- implement teardown procedures that are needed to reset the SUT to a known
  state after executing of a test.

The main access point to the wrappers (`TelescopeWrapper`)
is intended to be a
[SINGLETON](https://refactoring.guru/design-patterns/singleton),
so once it's initialised,
you can access it from everywhere in the code just by accessing its instance. 
This way multiple facades and actions can share the same 
(already configured) instance of the wrapper without being aware of it
and without the need to pass it around.

> NOTE: while the abstract and/or generic classes contained in the `structure`
> package never point to `actions` (to avoid cyclic dependencies), their
> concrete implementations in the `emulated` and `production` packages
> may need to point to actions to perform the operations.


### Why using JSON data builder?

Some actions over the telescope (such as the *scan*, *configure*,
*assign resources* commands) require an input argument that is a JSON string.
Also some *reset* procedures require default arguments to be used to call
the various commands. 

Passing these arguments around as strings or dictionaries is not a good
practice, because it makes the code more technical (full of type conversions,
explicit file reading, etc.) and so less readable. The idea of argument
factories is to provide a structured object-oriented representation of those
arguments.

An abstract base class (`JSONInput`) defines what is expected from a JSON input
(return a string or a dictionary, create a copy of itself with some
values changed, etc.). Through a concrete implementation of this class, 
one can specify how to generate this JSON (e.g., accessing your own test 
data folders, associating keywords to each or your specific input, 
through a hardcoded dictionary, etc.). A few ready-to-use implementations
are provided in the `inputs` folder.

We chose to use this infrastructure because a JSON input, normally,
can be represented in many ways (a string, a dictionary, a reference to a 
file, etc.) and we want a consistent way to represent it in the test harness
context. Moreover, sometimes we want to be able to deal with guaranteed and
validated input (e.g., when we set the initial default input),
sometimes we want to explicitly handle the case of un-valid
input (e.g., for un-happy paths tests) and sometimes we want to just ignore
that (an action that just sends a commands wants to deal the same way with
valid and invalid input).

The main inspiration behind this mechanism is the
[FACTORY METHOD](https://refactoring.guru/design-patterns/factory-method),
[ABSTRACT FACTORY](https://refactoring.guru/design-patterns/abstract-factory)
and [BUILDER](https://refactoring.guru/design-patterns/builder) are indirect
inspirations too.

In `inputs` folder you can find some examples of JSON input classes, but also
other input-output related classes. One of the most important is the
`TestHarnessInputs` class, which is a structured representation of the
input data needed to initialise the test harness (and sometimes to do
other operations). This class is used by the initialisation procedures
to load and validate the JSON input for the commands used in the teardown
procedures.

### Why using configuration classes?

These are mechanisms that collect configuration data from files or 
runtime flags, represent them in objects, and support fixtures to setup 
the proper instances of the test harness.

There are a number of classes that represent the default configuration of
the structure of the SUT. For example, the class `TMCConfiguration` contains
the names (i.e. TRLs) of the devices that are part of the TMC. The class
`CSPConfiguration` contains the names of the devices that are part of the CSP.
The directive to use the emulated or the production devices is another
example of configuration data (very important for the initialisation of the
test harness). 

All the needed configurations are collected in a single
class called `TestHarnessConfigurations`, which represents the configuration
used to initialise the test harness. The initialisation procedure refers to
this class (and to a few readers and validators) to load and validate the
configuration files and use them to set up the test harness.

Since the configuration may come from different sources (environment variables,
hardcoded values, files, etc.) and since it's easy to lose track of them an
object-oriented approach is used to represent them in a structured way and
to provide a consistent interface to them. To avoid inconsistencies, a 
*factory* class is used to create
all the instances of those configurations (see `config.reader` module).
Configurations may be also subject to validation, to ensure that the
configuration is correct and consistent to what is deployed
(see `config.validator` module).

Currently, the main representation of the configuration is through YAML files. An
example of valid configuration file is provided in 
[this file used in unit tests](../../tests/config_examples/valid_test_harness_config.yaml).

### Why having an initialisation procedure?

A complete test harness can be - potentially - set up just by creating a
`TelescopeWrapper` and initialising it with sub-systems wrappers (properly
initialised with configuration classes and input). Since this can be quite
complex, a default initialisation procedure is encoded in a builder class,
which:



- reads the configuration from a YAML file;

- validates it (checking all required fields and sections are set, that the
  device names point to existing and reachable Tango devices, etc.);

- collects the default input;

- validates them;

- uses the input and the configuration to create the instances of the
  wrappers.

To do each of those steps, the builder uses a set of classes that potentially
can be extended to support custom initialisation procedures.

The initialisation procedure makes heavy use of the
[ABSTRACT FACTORY](https://refactoring.guru/design-patterns/abstract-factory)
and [BUILDER](https://refactoring.guru/design-patterns/builder) design patterns.
In a certain sense, then the various internal tools are
[STRATEGIES](https://refactoring.guru/design-patterns/strategy) used by
the builder to compose the test harness.

## How to use and extend this harness

At the moment (September 2024) this harness has no well-defined
extension points yet and it is pretty specific to the TMC-CSP integration tests 
in MID. Based on feedback and on the evolution of the project, the harness will be extended to be more flexible and to support more use cases. 

### How to use this test harness right now as is

To use this test harness *as is*, you can follow the instructions in the
main [README.md](../../README.md) file.

### How to extend this test harness (within the current limitations)

Right now (September 2024) the test harness is designed for integration
tests of the TMC with CSP in MID. Probably, it is still capable of
supporting TMC-X in MID integrations tests. 

Even if it is not yet generic, it still supports some level of customisation.
Within the current limitations, your main ways to extend and/or customize
this test harness are:

- **Add new actions**: you can add new actions by sub-classing 
  the `TelescopeAction` class and implementing the abstract methods. 
  You can also create a sequence of actions by sub-classing the 
  `TelescopeActionSequence` class and implementing the abstract methods.
  The actions can then be called from your tests, or also from new facades
  you may create.

  > **Example**: you want to send a particular command to some
  > SUT device and wait for some device to reach a particular state $\to$
  > *you create a new action that sends the command and specifies the
  > expected state as a termination condition.*

  > **Example**: you want to encode a complex procedure that requires
  > multiple steps and synchronization points $\to$ *you use the composite
  > action mechanism to create a sequence of actions that perform the
  > procedure. If there is the need of using if-then-else constructs or similar
  > you can create a new action that acts as an orchestrator of other actions.*

- **Add new facades**: you can create new facades that access the telescope
  wrappers and the actions. If you need to change just some behaviours or you
  want to extend an existing facade, you can do that by sub-classing it and
  using it instead of the original one.

  > **Example**: you want to expose your new action from a facade
  > that is already used in your tests $\to$ *you sub-class the facade and
  > add the new method that calls the new action. Now you will use your
  > new extended version instead of the base one.*

- **Add new input classes**: you can create new input classes that generate
  the JSON input for the actions in your own ways.

  > **Example**: you have a collection of JSON files in a your
  > test data folder and you want to use them as input $\to$ *you sub-class
  > the file-based input class, you specify how to access your test data
  > and you permit to access one of those files just specifying a keyword
  > in the constructor of the input class (e.g., `MyFileJsonInput('scan')`).*

- **Customize the init procedure (and the wrappers)**: 
  the initialisation procedure explained
  in the main README.md file can be customized:
  - sub-classing various configuration, validation, reader and factory classes
  and injecting them in the builder, so they will be used instead of the
  original one;
  - creating an overall new initialisation procedure (maybe sub-classing
  the existing one, maybe creating a new one from scratch).

  Customizing the initialisation procedure may be a necessary step if you
  want to replace, modify and/or extend what makes the test harness
  `structure` (the `TelescopeWrapper`, the sub-systems wrappers, etc.).

  > **Example**: you want to implement a your own wrapper, which
  > should be activated only if a new configuration flag is used $\to$ 
  > *you add the needed parameters
  > in the YAML file and you extend the configuration classes and the
  > reader to support it, (optionally) you subclass the input validator and you
  > inject it into the initialisation builder, you subclass the wrapper
  > of the sub-system you want to replace and to use it in your test harness
  > you subclass the factory that produces the wrappers and override the
  > method that creates the wrapper for that sub-system.*


### How you will be able to extend this test harness in the future

In the future, the test harness will be more flexible and will not be centered
strictly on the TMC-X integration tests in MID. 

Probably, there will be a generic *core*, made by an elastic infrastructure,
the action mechanism, some generic and parametric actions, the input classes
and a generic and flexible configuration and initialisation mechanism. Then,
partially through extension, partially through configuration, you will be able
to adapt the test harness to your needs.

Please contact *Emanuele Lena*, *Giorgio Brajnik* and/or *Verity Allan*
if you think this test harness can be useful for your tests, if you have
any questions, proposals or feedback. Of course, you are more than welcome
also if you want to contribute to the development of this test harness.

## Applications

Right now (September 2024), this test harness is used for the new set of 
[TMC-CSP MID integration tests](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/-/merge_requests/234), which use the test harness
to test the subarray-related operations over the TMC (with a production
CSP and emulated SDP and Dishes).
