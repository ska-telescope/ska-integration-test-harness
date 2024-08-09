"""A collection of default inputs, needed in the initialization phase."""

from dataclasses import dataclass

from ska_integration_test_harness.inputs.json_input import JSONInput


@dataclass
class DefaultInputs:
    """A collection of default inputs, needed in the initialization phase.

    For now, it contains:

    - a default VCC configuration as a JSON, needed for the teardown procedure,
    - a set of JSON inputs for the obsState state machine:
      - assign
      - configure
      - scan
      - release
      they will also be used in the teardown procedure.
    """

    default_vcc_config_input: JSONInput = None
    """The default VCC configuration input."""

    assign_input: JSONInput = None
    """The input for the AssignResources command."""

    configure_input: JSONInput = None
    """The input for the Configure command."""

    scan_input: JSONInput = None
    """The input for the Scan command."""

    release_input: JSONInput = None
    """The input for the ReleaseResources command."""

    def mandatory_attributes(self) -> list[str]:
        """Return the names of the mandatory attributes.

        :return: List of attribute names.
        """
        return [
            "default_vcc_config_input",
            "assign_input",
            "configure_input",
            "scan_input",
            "release_input",
        ]
