"""The core of the Integration Test Harness as a Platform.

The core of the Integration Test Harness as a Platform is a set of
classes and functions that provide the basic functionalities to create
integration tests for complex Tango-based systems. The core has the following
features:

- The core is generic and by itself it doesn't even talk about telescopes
  and SKA, but is more intended as a framework to integration test any
  kind of complex system based on Tango devices.
- The core is extendable and adaptable to many different testing contexts,
  but also usable as it is.
- The core relies on :py:mod:`ska_tango_testing` for the event tracing
  and assertion mechanisms.
- The core is unit tested code, and it is expected to be reliable and robust.

The core is composed of the following main components:

- :py:mod:`ska_integration_test_harness.core.actions`: a set of classes
  that represent the actions that can be performed on your system and the
  consequent synchronisation. The concept
  of action includes both very generic procedures and more specific ones
  (e.g., like a command execution). You can use the actions as building
  blocks to represent the interactions with your system in a structured way.

- :py:mod:`ska_integration_test_harness.core.assertions`: a set of classes
  that represent verification procedures on your system. The assertions may
  be simple checks (e.g., a set of devices are in a certain state) or more
  complex event-based checks. You can use the assertions in actions
  as synchronisation points and preconditions/postconditions, but potentially
  also as standalone checks.

NOTE: all the core components are usually represented as class hierarchies,
so you can:

- use the given (non-abstract) classes as they are
- extend the base or the intermediate classes to create your own custom
  pieces of code

In :py:mod:`ska_integration_test_harness.extensions` you can find some already
implemented and tested extensions that may be useful for many
SKA testing contexts.

"""
