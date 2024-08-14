# ska-integration-test-harness

## Overview

For now, a test harness for TMC-CSP integration tests. In future,
a generic test harness integration testing an arbitrary combination
of production or emulated SKA subsystems.

More information will be added here as the project progresses.


## Installation

For now, the harness is not yet packaged for installation. To use it,
you can still import it through `poetry`, adding to your `pyproject.toml`
the following dependency:

```toml
[tool.poetry.dependencies]
... rest of your dependencies ...
ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git" }
```

Then , you can run `poetry lock --no-update` to update the `poetry.lock` file with the new dependency and `poetry install` to install it.

If you wish, you can also specify a branch, e.g. `ska-integration-test-harness = { git = "https://gitlab.com/ska-telescope/ska-integration-test-harness.git", branch = "main" }`.

If you change something in your code and want to have it updated in your project, you can run `poetry update ska-integration-test-harness && poetry install`.


## Architecture overview

For an overview of the architecture of the test harness and the principles behind it, see the [architecture document](src/ska_integration_test_harness/README.md).


## Usage


Here it follows an example of how to initialize the test harness through
opportune fixtures in a `pytest` test script. We assume you created 
a ``FileJSONInput`` class, which is a subclass of the ``JSONInput`` class
that reads the string from a file in a certain folder in your own test data
folder). We assume also that you have a `test_harness_config.yaml` file.

The YAML file may look like this:

```yaml
# A configuration file for the TMC-CSP integration tests in MID

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

  # Expected devices (when production)
  # dish_master1_name: "ska001/elt/master"
  # dish_master2_name: "ska036/elt/master"
  # dish_master3_name: "ska063/elt/master"
  # dish_master4_name: "ska100/elt/master"

```

The fixture to initialize the test harness may look like this:

```python
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
from ska_integration_test_harness.inputs.obs_state_commands_input import (
    ObsStateCommandsInput,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)
from <your path>.file_json_input import FileJSONInput

# how to initialize the wrappers
@pytest.fixture
def telescope_wrapper() -> TelescopeWrapper:
    """Create an unique test harness with proxies to all devices."""

    test_harness_builder = TestHarnessBuilder()

    # read a configuration file and validate it
    test_harness_builder.read_from_file(
        "tests/tmc_csp_refactor3/test_harness_config.yaml"
    )
    test_harness_builder.validate_configurations()

    # set some JSON inputs for the teardown procedures
    test_harness_builder.default_inputs.assign_input = FileJSONInput(
        "centralnode", "assign_resources_mid"
    )
    test_harness_builder.default_inputs.configure_input = FileJSONInput(
        "subarray", "configure_mid"
    )
    test_harness_builder.default_inputs.scan_input = FileJSONInput(
        "subarray", "scan_mid"
    )
    test_harness_builder.default_inputs.release_input = FileJSONInput(
        "centralnode", "release_resources_mid"
    )
    # an alternative in-line way to provide the JSON input
    test_harness_builder.default_inputs.default_vcc_config_input = DictJSONInput(
        {
            "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
            "tm_data_sources": [
                "car://gitlab.com/ska-telescope/ska-telmodel-data?"
                + "ska-sdp-tmlite-repository-1.0.0#tmdata"
            ],
            "tm_data_filepath": (
                "instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json",
            ),
        }
    )
    test_harness_builder.validate_default_inputs()

    # create the telescope wrapper
    telescope = test_harness_builder.build()
    yield telescope

    # reset it after the test are finished
    # NOTE: As the code is organized now, I cannot anticipate the
    # teardown of the telescope structure. To run reset now I should
    # init subarray node (with SetSubarrayId), but to do that I need
    # to know subarray_id, which is a parameter of the Gherkin steps.
    telescope.tear_down()

```

The fixtures to initialize the facades instead may look like those:

```python
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

# (given a telescope_wrapper fixture)

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

Then, in your test script you can use the facades to access the devices
and interact with them. 

