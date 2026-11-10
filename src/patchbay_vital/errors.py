"""The exceptions patchbay-vital raises: one root, each carrying the fields that say what failed.

`VitalError` is the root and derives from patchbay's `PatchbayError`, so a caller catches
everything this package reports with one `except`, and everything any patchbay package reports
with another. Under it, `VitalFormatError` is a preset's: a preset that cannot be read is
`MalformedPresetError` or `UnknownSettingError`, never pydantic's or `json`'s error, and a file that
cannot be reached is `PresetFileError`, never an `OSError`. `VitalHostError` is the hosted plugin's:
a plugin that cannot be loaded is `PluginLoadError`, state bytes the codec cannot read are
`PluginStateError`, and a render the plugin cannot give is `PluginRenderError`. `CensusError` is
the generator's, naming a parameter it cannot fit. A model built directly refuses as patchbay's
`PatchbayValidationError`, as every model on `PatchbayModel` does.

A failure core's protocol names derives from the root and from core's own error for it as well:
`UnknownParameterError` is a `ParameterNotFoundError`, and `ParameterRangeError` a
`ValueOutOfRangeError`, so a caller holding core's types, its contract tests among them, catches
them, and this package's one root still holds.

Each error takes its fields as arguments, keeps them as attributes and passes them to `Exception`,
so `args` and pickling carry them, and builds its message from them in `__str__`. The fields are
plain values, so this module imports nothing else from the package and every other module can import
it.
"""

from patchbay import ParameterNotFoundError, PatchbayError, ValueOutOfRangeError


class VitalError(PatchbayError):
    """The root of every exception patchbay-vital raises."""


class VitalFormatError(VitalError):
    """A preset could not be read or written."""


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


class VitalHostError(VitalError):
    """The hosted plugin could not be loaded, or its state not read or written."""


class PluginLoadError(VitalHostError):
    """No Vital could be loaded from a path: nothing there, or the host refused what is."""

    def __init__(self, path: str, reason: str) -> None:
        """Name the path and say why it gave no Vital."""
        super().__init__(path, reason)
        self.path = path
        self.reason = reason

    def __str__(self) -> str:
        """Say which path, and why."""
        return f"no Vital loaded from {self.path!r}: {self.reason}"


class PluginStateError(VitalHostError):
    """Bytes are not a state the plugin's container holds as this package reads it."""

    def __init__(self, reason: str) -> None:
        """Say why."""
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:
        """Give the reason."""
        return f"plugin state: {self.reason}"


class PluginRenderError(VitalHostError):
    """The plugin did not render what it was asked to: a length it cannot give, or another."""

    def __init__(self, reason: str) -> None:
        """Say why."""
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:
        """Give the reason."""
        return f"plugin render: {self.reason}"


class UnknownParameterError(VitalError, ParameterNotFoundError):
    """An id the parameter map does not hold; core's `ParameterNotFoundError` too."""


class ParameterRangeError(VitalError, ValueOutOfRangeError):
    """A value outside what a parameter takes; core's `ValueOutOfRangeError` too."""


class CensusError(VitalError):
    """The generator cannot fit a parameter it measured, so the map cannot be written."""

    def __init__(self, label: str, reason: str) -> None:
        """Name the parameter by its label and say what does not fit."""
        super().__init__(label, reason)
        self.label = label
        self.reason = reason

    def __str__(self) -> str:
        """Say which parameter, and why."""
        return f"cannot fit {self.label!r}: {self.reason}"
