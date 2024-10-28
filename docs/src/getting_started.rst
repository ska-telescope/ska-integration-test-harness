Overview and Getting Started
===============================

Overview
--------

Currently (October 2024), a test harness for TMC in Mid integration
tests, centred around the TMC subsystem and its interactions with CSP,
SDP and the Dishes. In future, a generic test harness integration
testing an arbitrary combination of production or emulated SKA
subsystems.

More information will be added here as the project progresses.

IMPORTANT: Scope and purpose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before diving into the (technical) details, it is important to
understand the purpose of this project and its scope. For this reason,
we strongly suggest you read the `dedicated Confluence
page <https://confluence.skatelescope.org/pages/viewpage.action?pageId=289699655>`__

IMPORTANT: What this repository is about (and what it is not)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A second important thing is to understand what this specific repository
is about and what it is not. While the term **ITH** sometimes may be
used to refer to a wider concept and a large collection of tools, this
repository contains a specific subset
of tools. So, let’s quickly clarify what you can find here (and what you
cannot).

What you can find here
^^^^^^^^^^^^^^^^^^^^^^

This repository essentially contains a Python framework to model the
SUT, its subsystems and devices and the actions you can perform on them.
More specifically:

-  represent and allow access to the subsystems and the Tango devices
   in a structured way, regardless of whether a subsystem is emulated
   or it is not;
-  simplify complex procedures to bring the SUT into a specific state
   before running the tests (e.g., call the commands to put the telescope
   in the desired state, synchronise when the events have finished, and ensure the state
   is effectively reached);
-  simplify teardown procedures, to bring the SUT back to a known state
   after the tests are completed;
-  overview of the active devices and their versions.

At the moment, the SUT consists of:

-  a production TMC, which is the “protagonist” of the tests (the
   subsystem which receives most of the commands);
-  a production or emulated CSP;
-  a production or emulated SDP;
-  a set of production or emulated Dishes.

**NOTE:** for the purposes of this test harness, we use the term
*production* to refer to real software that needs to be tested, and
*emulated* to refer to software that replicates the behaviour of
the real devices without having complex logic behind it. The term
*production* doesn't mean we are using the real hardware.

What you cannot find (and likely will remain in separate places)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This repository does not contain and will likely never contain:

-  the test definitions or implementation (which instead can be found in
   repos such as `SKA TMC Mid
   Integration <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/>`__
   and `SKA Software Integration
   Tests <https://gitlab.com/ska-telescope/ska-sw-integration-testing>`__);
-  the Helm charts to deploy the devices in a Kubernetes environment, or
   the pipelines and Make commands to run the tests (see repos in the
   previous point);
-  the specific “low-level” tools to track Tango events and make
   assertions on them (see
   `ska-tango-testing <https://gitlab.com/ska-telescope/ska-tango-testing>`__);
-  pipeline support tools, such as the Jira integration scripts (see
   `ska-ser-xray <https://gitlab.com/ska-telescope/ska-ser-xray>`__);
-  the code of the emulators for the non-production subsystem devices (see
   `ska-tmc-simulators <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-simulators>`__);
-  the code of the production devices.

What you cannot find (yet)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Instead, this framework may (*and will likely*) support in the future
(**but not at the moment**):

- TMC Low integration tests;
- integration tests where TMC is not involved (e.g.,
  stand-alone tests of a single subsystem);
- tests with multiple subarrays.

Stay tuned for updates!

Installation
------------

To install this test harness you can follow two paths:

1. The first is to import it via ``poetry`` as a classic dependency.

   .. code:: bash

      poetry add --group test ska-integration-test-harness

2. The second is to import it always via ``poetry``, but pointing
   directly to the GitLab repository.

We point out also this second approach since this test harness is
supposed to evolve quickly, together with the evolution of the
subsystems and the integration tests. This second approach could be
particularly useful in case you want to contribute to the project and
need to apply your own changes quickly.

To point directly to the GitLab repo (potentially also to a specific
branch) and bypass the semantic versioning, add the following to your
``pyproject.toml`` file:

.. code:: toml

   [tool.poetry.group.test.dependencies]
   ... rest of your test dependencies ...
   ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git", branch = "your branch name" }

When you added that, you can run ``poetry lock --no-update`` to update
the ``poetry.lock`` file with the new dependency and ``poetry install``
to install it. If you make changes to your code and want them reflected
in your project, you can run

.. code:: bash

   poetry update ska-integration-test-harness && poetry install


Usage
-----

Below we explain how to use the test harness in your test scripts.

Prerequisites
~~~~~~~~~~~~~

To use this test harness, first of all, you need a Kubernetes cluster
with all the production and emulated devices running. This part is not
covered by this project, which in fact assumes an environment equivalent
to that used in the test repository `SKA TMC-Mid
Integration <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/>`__
(`docs <https://developer.skao.int/projects/ska-tmc-mid-integration/en/latest/getting_started/getting_started.html>`__).

Since some of the devices are emulators, you might also want to check
`this documentation page <https://developer.skao.int/projects/ska-tmc-common/en/latest/HelperDevices/TangoHelperDevices.html>`__
and - if necessary - 
`the emulator implementations <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-common/-/tree/master/src/ska_tmc_common/test_helpers?ref_type=heads>`__.

.. _configuration_example:

Configuration
~~~~~~~~~~~~~

To configure the test harness using the default method, you need to
create a YAML file that specifies things like the
expected device names and whether the devices are emulated or not. The
file will look like this:

.. code:: yaml

   # Example of a valid test harness configuration file

   tmc:
     is_emulated: false # Not supported otherwise, default is false

     # Expected device names (Required)
     centralnode_name: "ska_mid/tm_central/central_node"
     tmc_subarraynode1_name: "ska_mid/tm_subarray_node/1"
     tmc_csp_master_leaf_node_name: "ska_mid/tm_leaf_node/csp_master"
     tmc_csp_subarray_leaf_node_name: "ska_mid/tm_leaf_node/csp_subarray01"
     tmc_sdp_master_leaf_node_name: "ska_mid/tm_leaf_node/sdp_master"
     tmc_sdp_subarray_leaf_node_name: "ska_mid/tm_leaf_node/sdp_subarray01"
     tmc_dish_leaf_node1_name: "ska_mid/tm_leaf_node/d0001"
     tmc_dish_leaf_node2_name: "ska_mid/tm_leaf_node/d0036"
     tmc_dish_leaf_node3_name: "ska_mid/tm_leaf_node/d0063"
     tmc_dish_leaf_node4_name: "ska_mid/tm_leaf_node/d0100"

   csp:
     is_emulated: false # Supported true too, default is true

     # Expected device names
     csp_master_name: "mid-csp/control/0"
     csp_subarray1_name: "mid-csp/subarray/01"

   sdp:
     is_emulated: true # Supported false too, default is true

     # Expected device names (Required)
     sdp_master_name: "mid-sdp/control/0"
     sdp_subarray1_name: "mid-sdp/subarray/01"

   dishes:
     is_emulated: true # Supported false too, default is true

     # Expected device names (Required)
     dish_master1_name: "ska001/elt/master"
     dish_master2_name: "ska036/elt/master"
     dish_master3_name: "ska063/elt/master"
     dish_master4_name: "ska100/elt/master"

Fixtures and facades
~~~~~~~~~~~~~~~~~~~~

To initialise and use this text harness, you will need to create some
fixtures in your test script. The main fixtures you will create are:

1. a ``TelescopeWrapper``,
2. facades for each of your subsystems.

Now we will not deep dive too much into the details of what they are,
but essentially you can think of the ``TelescopeWrapper`` as a singleton
representation of the *SUT*, and the *facades* as “views” of that system
that will allow you to access the devices and interact with them
performing (potentially auto-synchronised) actions. Here an example of
how you can use the facades to interact with the devices:

.. code:: python

   # if tmc_central_node is a correctly initialised facade
   # to the TMC central node, calling such a command will permit you
   # to move the telescope to the ON state, ignoring any details about
   # interaction with other emulated/not-emulated devices and also
   # ignoring the synchronisation (the ITH will guarantee that the
   # telescope will be in an ON state after the call, otherwise
   # an informative assertion error will be raised)
   tmc_central_node.move_to_on(wait_termination=True)

To be clear, the ``TelescopeWrapper`` is something you have to
initialise to have a test harness, and the facades are just views which
simplify your interaction with the test harness. Inspecting the
facade implementations is a good way to explore the mechanisms behind
the test harness, the interaction with the actual Tango devices and the
verified conditions in case you enable the synchronisation.

Your fixtures code may look like this:

.. code:: python

   """Your fixtures to use the test harness.

   (Probably defined in a ``conftest.py`` file)
   """

   import pytest
   from ska_integration_test_harness.facades.csp_facade import CSPFacade
   from ska_integration_test_harness.facades.dishes_facade import DishesFacade
   from ska_integration_test_harness.facades.sdp_facade import SDPFacade
   from ska_integration_test_harness.facades.tmc_facade import TMCFacade
   from ska_integration_test_harness.init.test_harness_builder import (
       TestHarnessBuilder,
   )
   from ska_integration_test_harness.inputs.json_input import FileJSONInput
   from ska_integration_test_harness.inputs.test_harness_inputs import (
       TestHarnessInputs,
   )
   from ska_integration_test_harness.structure.telescope_wrapper import (
       TelescopeWrapper,
   )

   # -----------------------------------------------------------
   # Set up the test harness

   @pytest.fixture
   def default_commands_inputs() -> TestHarnessInputs:
       """Declare some JSON inputs for TMC commands."""
       return TestHarnessInputs(
           # assign and release, right now, are called on the central node
           assign_input=FileJSONInput(
               "json-inputs/centralnode/assign_resources.json"
           ),
           release_input=FileJSONInput(
               "json-inputs/centralnode/release_resources.json"
           ),

           # configure and scan are called on subarray node
           configure_input=FileJSONInput("json-inputs/subarray/configure.json"),
           scan_input=FileJSONInput("json-inputs/subarray/scan.json"),

           default_vcc_config_input=FileJSONInput(
               "json-inputs/default_vcc_config.json"
           ),
       )


   @pytest.fixture
   def telescope_wrapper(
       default_commands_inputs: TestHarnessInputs,
   ) -> TelescopeWrapper:
       """Create and initialise an unique SUT wrapper."""
       test_harness_builder = TestHarnessBuilder()

       # import from a configuration file device names and emulation directives
       # for TMC, CSP, SDP and the Dishes
       test_harness_builder.read_config_file(
           "tests/tmc_csp_refactor3/test_harness_config.yaml"
       )
       test_harness_builder.validate_configurations()

       # set the default inputs for the TMC commands,
       # which will be used for teardown procedures
       test_harness_builder.set_default_inputs(default_commands_inputs)
       test_harness_builder.validate_default_inputs()

       # set the kubernetes namespace where the devices are running
       # (so we can access
       # https://gitlab.com/ska-telescope/ska-k8s-config-exporter
       # to log Tango device versions)
       test_harness_builder.set_kubernetes_namespace(os.getenv("KUBE_NAMESPACE"))


       # build the wrapper of the telescope and its subsystems
       telescope = test_harness_builder.build()
       yield telescope

       # after a test is completed, reset the telescope to its initial state
       # (obsState=READY, telescopeState=OFF, no resources assigned)
       telescope.tear_down()

       # NOTE: As the code is organised now, I cannot anticipate the
       # teardown of the telescope structure. To run reset now I should
       # init subarray node (with SetSubarrayId), but to do that I need
       # to know subarray_id, which is a parameter of the Gherkin steps.

   # -----------------------------------------------------------
   # Facades to access the devices

   @pytest.fixture
   def tmc(telescope_wrapper: TelescopeWrapper):
       """Create a facade to TMC devices."""
       return TMCFacade(telescope_wrapper)

   @pytest.fixture
   def csp(telescope_wrapper: TelescopeWrapper):
       """Create a facade to CSP devices."""
       return CSPFacade(telescope_wrapper)


   @pytest.fixture
   def sdp(telescope_wrapper: TelescopeWrapper):
       """Create a facade to SDP devices."""
       return SDPFacade(telescope_wrapper)


   @pytest.fixture
   def dishes(telescope_wrapper: TelescopeWrapper):
       """Create a facade to Dish devices."""
       return DishesFacade(telescope_wrapper)

Other than the fixtures, you may also want to create a fixture for the
``TangoEventTracer`` class, which is a tool to track the events of the
Tango devices and make assertions on them. Check
`ska-tango-testing <https://developer.skao.int/projects/ska-tango-testing/en/latest/guide/integration/getting_started.html>`__
for more details.

.. code:: python


   from ska_tango_testing.integration import TangoEventTracer

   @pytest.fixture
   def event_tracer() -> TangoEventTracer:
       """Create a TangoEventTracer to track the events of the devices."""
       return TangoEventTracer({
           # add here the mapping between attribute names and the
           # Enum types they are associated with, so assertion errors
           # will display meaningful labels
           # E.g. "obsState": ObsState
           # (NOTE: DevState is not needed)
       })

Interact with the test harness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your test script, use the facades to access the devices and interact
with them as shown in this simplified example:

.. code:: python


   """Simple demonstration of how to use the test harness to write a test script.

   NOTE: this is not a complete test script, but just a demonstration of how to
   use the test harness to make actions on the SUT and access the devices
   to make event subscriptions and assertions.
   This also is not necessarily a good example of how to write a test script. 
   """

   from assertpy import assert_that
   from pytest_bdd import given, when, then, scenario
   from ska_integration_test_harness.facades.tmc_facade import TMCFacade
   from ska_tango_testing.integration import TangoEventTracer
   from tango import DevState

   @given("the telescope is in ON state")
   def given_the_telescope_is_in_on_state(
       tmc: TMCFacade,
   ):
       """Example of a Gherkin step to set the telescope in the ON state,
       implemented interacting with the TMC central node facade.
       """
       # NOTE: the ``wait_termination=True`` flag is used to make the action
       # synchronous, i.e. the call will block until all the synchronisation
       # conditions are met (explore the method and the action implementation
       # for more details) or, in other words, when the method call execution
       # is completed, you are sure the telescope is in the ON state.
       # This way you DON'T have to explicitly deal with
       # synchronisation assertions (which are not relevant for the tests).
       tmc.move_to_on(wait_termination=True)


   @when("the MoveToOff command is issued")
   def when_the_movetooff_command_is_issued(
       tmc: TMCFacade,
       csp: CSPFacade,
       event_tracer: TangoEventTracer,
   ):
       """Example of a Gherkin step where a command is issued to the TMC,
       just after the ``TangoEventTracer`` is subscribed to capture the events.

       NOTE: the ``wait_termination=False`` flag is used to not block the call,
       so the tracer can be used separately to check the events.
       """
       # using the facades, I have access to the
       # device proxies and I can subscribe to the events
       event_tracer.subscribe_event(
           tmc.central_node, "telescopeState"
       )
       event_tracer.subscribe_event(csp.csp_master, "State")
       # (etc.)

       # Then I can issue the command, explicitly telling the call to
       # not wait for the synchronisation conditions to be met, 
       # since in the following steps I want to check the events
       # manually (since they are the "object" of this test).
       tmc.move_to_off(wait_termination=False)

   @then("the telescope is in OFF state")
   def then_the_telescope_is_in_off_state(
       tmc: TMCFacade,
       csp: CSPFacade,
       event_tracer: TangoEventTracer,
   ):
       """Example of a Gherkin step to check the state of the telescope,
       implemented always accessing the facades devices to write assertions.
       """
       # in then steps, tools like the TangoEventTracer can be used
       # to check the events occurred after the command was issued.
       # Of course, I am assuming in a fixture or in some previous step
       # the tracer was subscribed to the events of the devices.
       # I also assume that the tracer has no potentially "old" duplicated
       # events which may make the test pass even if the telescope is not
       assert_that(event_tracer).described_as(
           "TMC should have reached the OFF state within 60 seconds."
       ).within_timeout(60).has_change_event_occurred(
           tmc.central_node, "telescopeState", DevState.OFF
       )

A good example of tests script written using this test harness is
available in the `SKA TMC Mid Integration
repository <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/-/merge_requests/234>`__.
To read more about the architecture and the principles behind the test
harness, check :doc:`./architecture_overview`.
