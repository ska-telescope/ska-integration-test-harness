"""A wrapper for ObsState JSON commands inputs."""

from dataclasses import dataclass

from ska_integration_test_harness.inputs.json_input import JSONInput


@dataclass
class ObsStateCommandsInput:
    """A wrapper for ObsState JSON commands inputs.

    This class is a wrapper for the JSON commands inputs that are used to
    change the ObsState of a subarray node. It contains the JSON inputs
    for the commands:

    - AssignResources
    - Configure
    - Scan
    - ReleaseResources

    Each of those inputs is represented by a JSONInput object and
    it is optional (you can pass just the ones you need).

    This class is used in particular situations where you need to pass one
    or more of those commands input, else you can pass directly
    the JSONInput objects.

    TODO: maybe add more commands.
    """

    _assign_input: JSONInput | None = None
    _configure_input: JSONInput | None = None
    _scan_input: JSONInput | None = None
    _release_input: JSONInput | None = None

    def __init__(
        self,
        assign_input: JSONInput | None = None,
        configure_input: JSONInput | None = None,
        scan_input: JSONInput | None = None,
        release_input: JSONInput | None = None,
    ):
        """Initialize the ObsStateCommandsInput with the given JSON inputs.

        :param assign_input: The AssignResources JSON input.
        :param configure_input: The Configure JSON input.
        :param scan_input: The Scan JSON input.
        :param release_input: The ReleaseResources JSON input.
        """
        self._assign_input = assign_input
        self._configure_input = configure_input
        self._scan_input = scan_input
        self._release_input = release_input

    @property
    def assign_input(self) -> JSONInput | None:
        """Get the AssignResources JSON input."""
        if self._assign_input is None:
            raise ValueError("AssignResources input is not set.")
        return self._assign_input

    @property
    def configure_input(self) -> JSONInput | None:
        """Get the Configure JSON input."""
        if self._configure_input is None:
            raise ValueError("Configure input is not set.")
        return self._configure_input

    @property
    def scan_input(self) -> JSONInput | None:
        """Get the Scan JSON input."""
        if self._scan_input is None:
            raise ValueError("Scan input is not set.")
        return self._scan_input

    @property
    def release_input(self) -> JSONInput | None:
        """Get the ReleaseResources JSON input."""
        if self._release_input is None:
            raise ValueError("ReleaseResources input is not set.")
        return self._release_input

    def merge(self, other: "ObsStateCommandsInput") -> "ObsStateCommandsInput":
        """Merge this ObsStateCommandsInput with another one.

        This method merges this ObsStateCommandsInput with another instance.
        If a JSON input is not set in this instance, it will be taken from
        the other instance, else it will be taken from this instance.

        :param other: The other ObsStateCommandsInput to merge with.
        :return: A new ObsStateCommandsInput with the merged inputs.
        """
        return ObsStateCommandsInput(
            assign_input=self._assign_input or other._assign_input,
            configure_input=self._configure_input or other._configure_input,
            scan_input=self._scan_input or other._scan_input,
            release_input=self._release_input or other._release_input,
        )

    def __str__(self) -> str:
        """Return the JSON string representation of the inputs."""
        return str(self._to_dict())

    def __repr__(self) -> str:
        """Return the JSON string representation of the inputs."""
        return str(self._to_dict())

    def _to_dict(self) -> dict:
        """Return a dict containing the JSON inputs."""
        res = {}

        if self._assign_input is not None:
            res["AssignResources"] = self._assign_input

        if self._configure_input is not None:
            res["Configure"] = self._configure_input

        if self._scan_input is not None:
            res["Scan"] = self._scan_input

        if self._release_input is not None:
            res["ReleaseResources"] = self._release_input

        return res

    def __eq__(self, other: object) -> bool:
        """Check if two ObsStateCommandsInput are equal."""
        if not isinstance(other, ObsStateCommandsInput):
            return False

        return self._to_dict() == other._to_dict()
