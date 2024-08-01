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

## Usage

You can import the components of the test harness as you would any other Python module. For example:

```python
from ska_integration_test_harness.facades.tmc_central_node_facade import (
  TMCCentralNodeFacade
)
```

## Architecture overview

For an overview of the architecture of the test harness and the principles behind it, see the [architecture document](src/ska_integration_test_harness/README.md).

