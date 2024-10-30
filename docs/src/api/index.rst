API Documentation
===================

The following API documentation is divided into two main sections:

1. The core mechanisms of the ska-integration-test-harness.
2. The specific actions, facades and structures that are currently implemented.

The first section is a general overview of the core mechanisms that
make up the ska-integration-test-harness (e.g., such as the telescope
definition, the abstract subsystem wrappers, the extension points to create
actions and the configuration and initialisation mechanisms).

The section is a sort of enumeration of the main concrete classes and
components that are part of the ska-integration-test-harness for testing
TMC-CSP in Mid (at the time of writing).

**IMPORTANT NOTE**: A very crucial difference between the two sections 
is that the first
includes unit tested code, while the second, since it has been considered
more related to the specific SUT logic than to the test harness itself,
is not unit tested (and in a certain sense, the integration tests that
use the test harness are the validation of the correctness of the
implementation of the second section). **The coverage metrics of the
test harness are calculated only on the first section** (*at the time of
writing, the coverage on the first section is approximately 90%, while
the overall coverage is around 60%*).

An example of tests that use what is described in the second section
are the ones introduced in `ska-tmc-mid-integration` by this
`merge request <https://gitlab.com/ska-telescope/ska-tmc-mid-integration/-/merge_requests/1>`_.


.. toctree::
   :maxdepth: 2

   core_api
   extension_api



