"""A validator for the input data."""

import abc
import logging
from json import JSONDecodeError

from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)


class InputValidator(abc.ABC):
    """A validator for the input data.

    It provides interfaces for two main validation steps:

    - a step to validate the presence of a needed set of inputs
    - a step to validate each input individually

    It provides also a minimal log.info utility to log the validation steps.
    """

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__()

        self.logger = logger
        """An optional logger used to log the errors and warnings, while
        they are found during the validation."""

        self.logger_prefix = "INPUT VALIDATION: "
        """The prefix used to log the validation messages."""

    @abc.abstractmethod
    def validate_inputs_presence(self, inputs: TestHarnessInputs) -> None:
        """Validate the presence of the required inputs.

        A given set of inputs must contain all the needed inputs to run
        the tests.

        If the logger is set, all the errors and warnings are logged.

        :raises ValueError: If any critical error is found.
        """

    @abc.abstractmethod
    def validate_inputs_correctness(self, inputs: TestHarnessInputs) -> None:
        """Check the correctness of the given inputs.

        Validate all inputs using the configured validation rules.
        If any critical error is found, a ValueError is raised.

        :raises ValueError: If any critical error is found.
        """

    def _log_info(self, message: str) -> None:
        """Log an info message if a logger is available.

        :param message: The message to log.
        """
        if self.logger:
            self.logger.info(f"{self.logger_prefix}{message}")

    # NOTE: the following class is really similar to the ConfigurationValidator
    # class. In future, configurations and inputs could benefit from a common
    # class structure, but it is not clear if it is worth it.


class BasicInputValidator(InputValidator):
    """A basic validator for the input data.

    For how it is implemented now:
    - it checks the presence of the inputs for:
        - default VCC config
        - assign
        - configure
        - scan
        - release
    - it checks each of those input is a valid JSON

    Instead, it doesn't check the semantic correctness of the JSONs.
    """

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.required_inputs = [
            TestHarnessInputs.InputName.DEFAULT_VCC_CONFIG,
            TestHarnessInputs.InputName.ASSIGN,
            TestHarnessInputs.InputName.CONFIGURE,
            TestHarnessInputs.InputName.SCAN,
            TestHarnessInputs.InputName.RELEASE,
        ]
        """The list of the required inputs."""

    def validate_inputs_presence(self, inputs: TestHarnessInputs) -> None:
        """Validate the presence of the required inputs."""
        self._log_info("Checking the presence of the required inputs:")

        for input_name in self.required_inputs:
            if not inputs.get_input(input_name, fail_if_missing=False):
                raise ValueError(
                    f"The required default input {input_name} is missing. "
                    f"Required inputs: {self.required_inputs}"
                )
            self._log_info(f"Required default input for '{input_name}': OK.")

        self._log_info("All required inputs are present.")

    def validate_inputs_correctness(self, inputs: TestHarnessInputs) -> None:
        """Ensure all the passed inputs are valid JSONs."""
        self._log_info("Ensuring the given inputs are valid JSONs.")

        for (
            input_name,
            input_data,
        ) in inputs.get_non_none_json_inputs().items():
            try:
                input_data.as_dict()
            except JSONDecodeError as json_error:
                raise ValueError(
                    f"The set default input {input_name} is not valid JSON."
                ) from json_error

            self._log_info(f"Input {input_name}: OK.")

        self._log_info("All the inputs are valid JSONs.")
