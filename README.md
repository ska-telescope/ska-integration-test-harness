# SKA Integration Test Harness - Overview & Getting started

## Overview

Currently, a test harness for TMC-CSP integration tests. In future,
a generic test harness integration testing an arbitrary combination
of production or emulated SKA subsystems.

More information will be added here as the project progresses.


## Installation

Currently, the harness is not yet packaged for installation. To use it,
import it via `poetry` by adding the following dependency
to your `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
... rest of your dependencies ...
ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git" }
```

Then, you can run `poetry lock --no-update` to update the
`poetry.lock` file with the new dependency and `poetry install` to install it.

If you wish, you can also specify a branch, e.g.,  
`ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git", branch = "main" }`.

If you make changes to your code and want them reflected in your project,
you can run 
`poetry update ska-integration-test-harness && poetry install`.


## Architecture overview

For an overview of the architecture of the test harness and the principles behind it, see the [architecture document](src/ska_integration_test_harness/README.md).


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

To initialise the test harness, create a `TelescopeWrapper` object, 
set it up with the various configured subsystems and then create your facades.
To initialise the test harness you can use the `TestHarnessBuilder` class.

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
    """Default JSON inputs for TMC commands."""
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
    """Create an unique test harness with proxies to all devices."""
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
    # for more details). In theory, I could avoid the flag,
    # since the default value is True
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
    # not wait for the synchronization conditions to be met
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
    assert_that(event_tracer).described_as(
        "TMC and CSP should have reached the OFF state within 60 seconds."
    ).within_timeout(60).has_change_event_occurred(
        central_node_facade.central_node, "telescopeState", DevState.OFF
    ).has_change_event_occurred(
        csp.csp_master, "State", DevState.OFF
    )

```
