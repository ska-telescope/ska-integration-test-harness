"""A collection of default inputs, needed in the initialisation phase."""

from dataclasses import dataclass
from enum import Enum

from ska_integration_test_harness.inputs.json_input import JSONInput


@dataclass
class TestHarnessInputs:
    """A collection of inputs for the test harness.

    This data class is a collection of inputs that may be needed for some
    processes in the test harness. For example, it can be used to specify
    the inputs for the subarray observation state resetter, or also the
    default inputs injected in the test harness to perform various operations
    (such as the teardown).

    The contained inputs are:

    - a default VCC configuration as a JSON, needed for the teardown procedure,
    - a set of JSON inputs for the obsState state machine:
      - assign
      - configure
      - scan
      - release

    A support enum is provided to specify the input names, and
    permit to access in a parametric way the inputs.
    """

    # (this is not a pytest test class)
    __test__ = False

    class InputName(Enum):
        """An enumeration of the possible input names.

        An enumeration of the possible input names that could be
        included as test harness inputs.
        """

        DEFAULT_VCC_CONFIG = "default_vcc_config"
        ASSIGN = "assign"
        CONFIGURE = "configure"
        SCAN = "scan"
        RELEASE = "release"

    default_vcc_config_input: JSONInput | None = None
    """The default VCC configuration input."""

    assign_input: JSONInput | None = None
    """The input for the AssignResources command."""

    configure_input: JSONInput | None = None
    """The input for the Configure command."""

    scan_input: JSONInput | None = None
    """The input for the Scan command."""

    release_input: JSONInput | None = None
    """The input for the ReleaseResources command."""

    def get_input(
        self, input_name: InputName, fail_if_missing: bool = False
    ) -> JSONInput:
        """Get the input with the given name.

        :param input_name: The name of the input to get.
        :param fail_if_missing: If True, raise an exception
          if the input is missing.
        :return: The input with the given name.
        :raises ValueError: If the input is missing and
          fail_if_missing is set to True.
        """
        res = self.__dict__.get(f"{input_name.value}_input")
        if res is None and fail_if_missing:
            raise ValueError(f"Missing input: {input_name}")
        return res

    def get_non_none_json_inputs(self) -> dict[InputName, JSONInput]:
        """Get the non-None JSON inputs as a dictionary.

        :return: A dictionary with the non-None JSON inputs.
        """
        return {
            input_name: self.get_input(input_name)
            for input_name in self.InputName
            if isinstance(self.get_input(input_name), JSONInput)
        }

    def __str__(self) -> str:
        """Return the JSON string representation of the inputs."""
        return str(self.get_non_none_json_inputs())

    def __repr__(self) -> str:
        """Return the JSON string representation of the inputs."""
        return str(self.get_non_none_json_inputs())

    def __eq__(self, other: object) -> bool:
        """Check if two ObsStateCommandsInput are equal."""
        if not isinstance(other, TestHarnessInputs):
            return False

        return (
            self.get_non_none_json_inputs() == other.get_non_none_json_inputs()
        )
