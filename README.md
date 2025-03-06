# SKA Integration Test Harness - Overview & Getting started

Currently (March 2025) this repository contains two separate things:

1. **The Monolith TMC Test Harness** is a test harness for testing TMC in
   Mid and Low. 

   This test harness is essentially an interface to use TMC in Mid and Low
   together with the controlled subsystems CSP, SDP, Dishes and MCCS.
   We call it a *Monolith* because it's a single python library specific
   for TMC that contains all the logic for dealing with different
   testing scenarios:

   - it can interface to TMC-Mid as well as TMC-Low,
   - when in Mid, it can interface to both production and emulated
     CSP, SDP and Dishes,
   - when in Low, it interfaces to emulated CSP, SDP and MCCS.

   In all the cases, the interactions are piloted by TMC.

   If you need to use it this test harness, you can attach to the version
   `0.3.0` of the `ska-tmc-integration-test-harness` package. The `0.4.0`
   supports it as well, but it includes also components for the Test Harness
   as a Platform.

   On the long term, this monolithic test harness will be moved somewhere else.

   For the documentation of the monolithic TMC test harness, please refer to
   [this section of the documentation](https://developer.skao.int/projects/ska-integration-test-harness/en/latest/?badge=latest).

2. **The Test Harness as a Platform** is instead a collection of building
   blocks that you can use to build your own test harness for integration
   testing your specific SKA subsystem. It is a generic framework made by

   - a generic **core** package that provides the basic building blocks
     for building a test harness,
   - some **common extensions** that implement some common SKAO use cases
     (e.g., sending Tango Long Running Commands and synchronising after them).

   You can take those building blocks and use or extend them to build your
   own **specific customisation**. 

   You can find more information about this approach in
   [this other section of the documentation](https://developer.skao.int/projects/ska-integration-test-harness/en/latest/ith_as_a_platform.html).

   At the moment (March 2025/version `0.4.0`) the Test Harness as a
   Platform it is made by few building blocks, but it is growing, and
   [it can evolve according to your needs](https://developer.skao.int/projects/ska-integration-test-harness/en/latest/ith_as_a_platform.html#development-process). On the long term, this will be the
   main focus of this repository.

