# SKA Integration Test Harness - Overview & Getting started

## Overview

Currently (17th October 2024), a test harness for TMC in Mid integration tests,
centred around the TMC subsystem and its interactions with CSP, SDP and the
Dishes. In future, a generic test harness integration testing an
arbitrary combination of production or emulated SKA subsystems.

More information will be added here as the project progresses.

### IMPORTANT: Scope and purpose

Before diving into the (technical) details, it is important to
understand the purpose of this project and its scope. 
For this reason, we strongly suggest you to read the
[dedicated Confluence page](https://confluence.skatelescope.org/pages/viewpage.action?pageId=289699655)


### IMPORTANT: What this repository is about (and what it is not)

A second important thing is to understand what this specific
repository is about and what it is not.
While the term **ITH** sometimes may be used to refer a wider concept
and a large collection of tools, this repository
(at the moment, 17th October 2024) contains a specific subset of tools. So,
let's quickly clarify what you can find here (and what you cannot).

#### What you can find here

This repository essentially contains a Python framework to model the SUT, 
its subsystems and devices and the actions you can perform on them. More 
specifically:

- represent and permit to access the subsystems and the Tango devices
in a structured way, potentially ignoring which subsystem is emulated and which is not;
- simplify complex procedures to bring the SUT in a specific state before
running the tests (e.g., make the actions to set the telescope
in a specific state, synchronizing on events end ensuring the state
is effectively reached);
- simplify teardown procedures, to bring the SUT back to a known state
after the tests are completed;
- call Tango commands on the devices;
- overview on the active devices and their versions.

At the moment (17th October 2024), the SUT consist in:

- a production TMC, which is the "protagonist" of the tests (the subsystem
  which receives most of the commands);
- a production or emulated CSP;
- a production or emulated SDP;
- a set of production or emulated Dishes (where "production" refers to
  the software running on the real devices, and "emulated" to a software
  that just "replicate" the behaviour of the real devices, without
  actually having a complex logic behind; for the purposes of this test
  harness, at the moment, a "production" device doesn't necessarily mean
  it uses the real hardware).

#### What you cannot find (and likely will remain in separate places)

This repository does not contain and will likely never contain:

- the test definitions or implementation (which instead can be found in
  repos such as [SKA TMC Mid Integration](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/)
  and [SKA Software Integration Tests](https://gitlab.com/ska-telescope/ska-sw-integration-testing));
- the Helm charts to deploy the devices in a Kubernetes environment,
  or the pipelines and Make commands to run the tests
  (see previous point repos);
- the specific "low-level" tools to track tango events and make assertions
  on them (see [ska-tango-testing](https://gitlab.com/ska-telescope/ska-tango-testing));
- pipeline support tools, such as the Jira integration scripts (see
  [ska-ser-xray](https://gitlab.com/ska-telescope/ska-ser-xray));
- the code of the emulators for the non-production devices (see
  [ska-tmc-simulators](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-simulators));
- the code of the production devices.

  
#### What you cannot find (yet)

Instead, this repository may (*and will likely*) contain in the future
(but not at the moment, 17th October 2024):

- a test harness which supports TMC Low integration tests;
- a test harness which supports integration tests where TMC is not
  the protagonist.

Stay tuned for updates!


## Installation

To install this test harness you can follow two paths:

1. The first is to import it via `poetry` as a classic dependency.
   
   ```bash
   poetry add --group test ska-integration-test-harness
   ```
   
2. The second is to import it always via `poetry`, but pointing directly
   to the Gitlab repository.

We point out also this second approach since this test harness is
is supposed to evolve quickly, together with the evolution of the
subsystems and the integration tests. This second approach could be
particularly useful in case you want to contribute to the project
and need to apply your own changes quickly.

To point directly the Gitlab repo (potentially also on a specific branch)
and by-pass the semantic versioning,
add the following to your `pyproject.toml` file:

```toml
[tool.poetry.group.test.dependencies]
... rest of your test dependencies ...
ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git", branch = "your branch name" }
```

When you added that, you can run `poetry lock --no-update` to update the
`poetry.lock` file with the new dependency and `poetry install` to install it.
If you make changes to your code and want them reflected in your project,
you can run `poetry update ska-integration-test-harness && poetry install`.


## Usage

Below is an example of how to initialise the test harness through
opportune fixtures in a `pytest` test script. We assume you have available
a `test_harness_config.yaml` file
(see [example](tests/config_examples/valid_test_harness_config.yaml)
and also a set of JSON files for the various required inputs.

### Prerequisites

To use this test harness, first of all, you need a Kubernetes cluster with
all the production and emulated devices running. This part is not
covered by this project, which in fact assumes an environment equivalent
to what is used in the test repository
[SKA TMC-MID Integration](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/)
([docs](https://developer.skao.int/projects/ska-tmc-mid-integration/en/latest/getting_started/getting_started.html)).

Since some of the devices are emulators, you might also want to check 
[this](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-common/-/tree/master/src/ska_tmc_common/test_helpers?ref_type=heads) 
and 
[this](https://developer.skao.int/projects/ska-tmc-common/en/latest/HelperDevices/TangoHelperDevices.html).



### Configuration 

To configure the test harness using the default method,
you need to create a YAML file such as the following:


```yaml
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

```

### Fixtures and facades

To initialise and use this text harness, you will need to
create some fixtures in your test script. The main fixtures you will
create are:

1. a `TelescopeWrapper`, 
2. facades for each of your subsystems.

Now we will not deep dive too much into the details of what they are,
but essentially you can think of the `TelescopeWrapper` as a singleton
representation of the _SUT_, and the _facades_
as "views" of that system that will allow you to access the devices and
interact with them performing (potentially auto-synchronized) actions. E.g., 

```python
# if tmc_central_node is a correctly initialised facade
# to the TMC central node, calling such a command will permit you
# to move the telescope to the ON state, ignoring any details about
# interaction with other emulated/not-emulated devices and also
# ignoring the synchronization (the ITH will guarantee that the
# telescope will be in an ON state after the call, otherwise
# an informative assertion error will be raised)
tmc_central_node.move_to_on(wait_termination=True)
```

So, just to be clear, the `TelescopeWrapper` is something you have to
initialise to have a test harness, and the facades just views which simplify
your interaction with such a test harness. Inspecting the facade
implementations is a good way to explore the mechanisms behind the test
harness, the interaction with the actual Tango devices and the verified
conditions in case you enable the synchronization.

Your fixtures code may look like this:

```python
"""Your fixtures to use the test harness.

(Probably defined in a ``conftest.py`` file)
"""

import pytest
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.dishes_facade import DishesFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_central_node_facade import (
    TMCCentralNodeFacade,
)
from ska_integration_test_harness.facades.tmc_subarray_node_facade import (
    TMCSubarrayNodeFacade,
)
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
        # assign and release, right now, are called on central node
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
    # to log Tango devices versions)
    test_harness_builder.set_kubernetes_namespace(os.getenv("KUBE_NAMESPACE"))


    # build the wrapper of the telescope and its sub-systems
    telescope = test_harness_builder.build()
    yield telescope

    # after a test is completed, reset the telescope to its initial state
    # (obsState=READY, telescopeState=OFF, no resources assigned)
    telescope.tear_down()

    # NOTE: As the code is organized now, I cannot anticipate the
    # teardown of the telescope structure. To run reset now I should
    # init subarray node (with SetSubarrayId), but to do that I need
    # to know subarray_id, which is a parameter of the Gherkin steps.

# -----------------------------------------------------------
# Facades to access the devices

@pytest.fixture
def central_node_facade(telescope_wrapper: TelescopeWrapper):
    """Create a facade to TMC central node and all its operations."""
    central_node_facade = TMCCentralNodeFacade(telescope_wrapper)
    yield central_node_facade


@pytest.fixture
def subarray_node_facade(telescope_wrapper: TelescopeWrapper):
    """Create a facade to TMC subarray node and all its operations."""
    subarray_node = TMCSubarrayNodeFacade(telescope_wrapper)
    yield subarray_node
    # NOTE: in future, this subarray node facade may be merged with central
    # node facade since they belong to the same subsystem.
    # For now, we keep them separated.

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
    """Create a facade to dishes devices."""
    return DishesFacade(telescope_wrapper)
```

Other than the fixtures, you may also want to create a fixture for
the `TangoEventTracer` class, which is a tool to track the events
of the Tango devices and make assertions on them. Check
[ska-tango-testing](https://developer.skao.int/projects/ska-tango-testing/en/latest/guide/integration/getting_started.html)
for more details.

```python

from ska_tango_testing.integration import TangoEventTracer

@pytest.fixture
def event_tracer() -> TangoEventTracer:
    """Create a TangoEventTracer to track the events of the devices."""
    return TangoEventTracer({
        # add here an eventual mapping between attribute names and
        # Enum types they are associated to, so assertion errors
        # will display meaningful labels
        # E.g. "obsState": ObsState
        # (NOTE: DevState is not needed)
    })
```

### Interact with the test harness

In your test script, use the facades to access the devices
and interact with them like in this simplified example:

```python

"""Simple demonstration of how to use the test harness to write a test script.

NOTE: this is not a complete test script, but just a demonstration of how to
use the test harness to make actions over the SUT and access the devices
to make event subscriptions and assertions.
This also is not necessarily a good example of how to write a test script. 
"""

from assertpy import assert_that
from pytest_bdd import given, when, then, scenario
from ska_integration_test_harness.facades.tmc_central_node_facade import (
    TMCCentralNodeFacade,
)
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

@given("the telescope is in ON state")
def given_the_telescope_is_in_on_state(
    central_node_facade: TMCCentralNodeFacade,
):
    """Example of a Gherkin step to set the telescope in the ON state,
    implemented interacting with the TMC central node facade.
    """
    # NOTE: the ``wait_termination=True`` flag is used to make the action
    # synchronous, i.e. the call will block until all the synchronizations
    # conditions are met (explore the method and the action implementation
    # for more details) or, in other words, when the method call execution
    # is completed, you are sure the telescope is in the ON state.
    # This way you DON'T have to explicitly deal with
    # synchronisation assertions (which are not relevant for the tests).
    central_node_facade.move_to_on(wait_termination=True)


@when("the MoveToOff command is issued")
def when_the_movetooff_command_is_issued(
    central_node_facade: TMCCentralNodeFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
):
    """Example of a Gherkin step where a command is issued to the TMC,
    just after the ``TangoEventTracer`` is subscribed to capture the events.

    NOTE: the ``wait_termination=False`` flag is used to not block the call,
    so the tracer can be used separately to check the events.
    """
    # using the facades, I can access the
    # device proxies and subscribe to the devices
    event_tracer.subscribe_event(
        central_node_facade.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(csp.csp_master, "State")
    # (etc.)

    # Then I can issue the command, explicitly telling the call to
    # not wait for the synchronization conditions to be met, 
    # since in the following steps I want to check the events
    # manually (since they are the "object" of this test).
    central_node_facade.move_to_off(wait_termination=False)

@then("the telescope is in OFF state")
def then_the_telescope_is_in_off_state(
    central_node_facade: TMCCentralNodeFacade,
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
        central_node_facade.central_node, "telescopeState", DevState.OFF
    )

```

A good example of tests script written using this test harness is
available in the
[SKA TMC Mid Integration repository](https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/-/merge_requests/234)
