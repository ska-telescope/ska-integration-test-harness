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

    assign_input: JSONInput | None = None
    """The input for the AssignResources command."""

    configure_input: JSONInput | None = None
    """The input for the Configure command."""

    scan_input: JSONInput | None = None
    """The input for the Scan command."""

    release_input: JSONInput | None = None
    """The input for the ReleaseResources command."""

    @property
    def get_assign_input(self) -> JSONInput | None:
        """Get the AssignResources JSON input (or fail if not set)."""
        if self.assign_input is None:
            raise ValueError("AssignResources input is not set.")
        return self.assign_input

    @property
    def get_configure_input(self) -> JSONInput | None:
        """Get the Configure JSON input (or fail if not set)."""
        if self.configure_input is None:
            raise ValueError("Configure input is not set.")
        return self.configure_input

    @property
    def get_scan_input(self) -> JSONInput | None:
        """Get the Scan JSON input (or fail if not set)."""
        if self.scan_input is None:
            raise ValueError("Scan input is not set.")
        return self.scan_input

    @property
    def get_release_input(self) -> JSONInput | None:
        """Get the ReleaseResources JSON input (or fail if not set)."""
        if self.release_input is None:
            raise ValueError("ReleaseResources input is not set.")
        return self.release_input

    def merge(self, other: "ObsStateCommandsInput") -> "ObsStateCommandsInput":
        """Merge this ObsStateCommandsInput with another one.

        This method merges this ObsStateCommandsInput with another instance.
        If a JSON input is not set in this instance, it will be taken from
        the other instance, else it will be taken from this instance.

        :param other: The other ObsStateCommandsInput to merge with.
        :return: A new ObsStateCommandsInput with the merged inputs.
        """
        return ObsStateCommandsInput(
            assign_input=self.assign_input or other.assign_input,
            configure_input=self.configure_input or other.configure_input,
            scan_input=self.scan_input or other.scan_input,
            release_input=self.release_input or other.release_input,
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

        if self.assign_input is not None:
            res["AssignResources"] = self.assign_input

        if self.configure_input is not None:
            res["Configure"] = self.configure_input

        if self.scan_input is not None:
            res["Scan"] = self.scan_input

        if self.release_input is not None:
            res["ReleaseResources"] = self.release_input

        return res

    def __eq__(self, other: object) -> bool:
        """Check if two ObsStateCommandsInput are equal."""
        if not isinstance(other, ObsStateCommandsInput):
            return False

        return self._to_dict() == other._to_dict()
