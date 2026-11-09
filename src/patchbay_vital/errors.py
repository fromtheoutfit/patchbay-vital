"""The exceptions patchbay-vital raises: one root, each carrying the fields that say what failed.

`VitalFormatError` is the root and derives from patchbay's `PatchbayError`, so a caller catches
everything this package reports with one `except`, and everything any patchbay package reports with
another. A preset that cannot be read is `MalformedPresetError` or `UnknownSettingError`, never
pydantic's or `json`'s error, and a file that cannot be reached is `PresetFileError`, never an
`OSError`. A model built directly refuses as patchbay's `PatchbayValidationError`, as every model on
`PatchbayModel` does.

Each error takes its fields as arguments, keeps them as attributes and passes them to `Exception`,
so `args` and pickling carry them, and builds its message from them in `__str__`. The fields are
plain values, so this module imports nothing else from the package and every other module can import
it.
"""

from patchbay import PatchbayError


class VitalFormatError(PatchbayError):
    """The root of every exception patchbay-vital raises."""


class UnknownSettingError(VitalFormatError):
    """A preset holds a key Vital has never been seen to write, so its format has changed."""

    def __init__(self, key: str) -> None:
        """Name the key that is not known."""
        super().__init__(key)
        self.key = key

    def __str__(self) -> str:
        """Say which key."""
        return f"unknown preset key {self.key!r}"


class MalformedPresetError(VitalFormatError):
    """A text is not a preset this package can read, or a value cannot be written as one."""

    def __init__(self, reason: str) -> None:
        """Say why."""
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:
        """Give the reason."""
        return f"malformed preset: {self.reason}"


class PresetFileError(VitalFormatError):
    """A preset file could not be read or written."""

    def __init__(self, path: str, reason: str) -> None:
        """Name the path and say what went wrong with it."""
        super().__init__(path, reason)
        self.path = path
        self.reason = reason

    def __str__(self) -> str:
        """Say which file, and why."""
        return f"preset file {self.path!r}: {self.reason}"
