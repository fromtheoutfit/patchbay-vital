"""The exceptions patchbay-vital raises: one root, each carrying the fields that say what failed.

`VitalError` is the root and derives from patchbay's `PatchbayError`, so a caller catches
everything this package reports with one `except`, and everything any patchbay package reports
with another. Under it, `VitalFormatError` is a preset's: a preset that cannot be read is
`MalformedPresetError` or `UnknownSettingError`, never pydantic's or `json`'s error, and a file that
cannot be reached is `PresetFileError`, never an `OSError`. `VitalHostError` is the hosted plugin's:
a plugin that cannot be loaded is `PluginLoadError`, state bytes the codec cannot read, or a read,
a state or a value the plugin refuses, are `PluginStateError`, a render the plugin cannot give is
`PluginRenderError`, and a parameter map measured on another machine, or from another plugin,
than this one is `MapMismatchError`, naming what differs; nothing pedalboard raises leaves the
host. `CensusError` is the
generator's, naming a parameter it cannot fit. A model built directly refuses as patchbay's
`PatchbayValidationError`, as every model on `PatchbayModel` does.

A failure core's protocol names derives from the root and from core's own error for it as well:
`UnknownParameterError` is a `ParameterNotFoundError`, and `ParameterRangeError` a
`ValueOutOfRangeError`, so a caller holding core's types, its contract tests among them, catches
them, and this package's one root still holds.

Each error takes its fields as arguments, keeps them as attributes and passes them to `Exception`,
so `args` and pickling carry them, and builds its message from them in `__str__`. The three that
carry a reason alone share one private base, which prefixes the reason with what failed. The fields
are plain values, so this module imports nothing else from the package and every other module can
import it.
"""

from typing import ClassVar

from patchbay import ParameterNotFoundError, PatchbayError, ValueOutOfRangeError


class VitalError(PatchbayError):
    """The root of every exception patchbay-vital raises."""


class _ReasonError(VitalError):
    """An error whose one field is the reason, said after what failed."""

    _prefix: ClassVar[str]

    def __init__(self, reason: str) -> None:
        """Say why."""
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:
        """Say what failed, then the reason."""
        return f"{self._prefix}: {self.reason}"


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


class MalformedPresetError(VitalFormatError, _ReasonError):
    """A text is not a preset this package can read, or a value cannot be written as one."""

    _prefix = "malformed preset"


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
    """The hosted plugin could not be loaded, its state not read or written, or its map not used."""


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


class PluginStateError(VitalHostError, _ReasonError):
    """Bytes are not a state this package reads, or the plugin refused a read or a write."""

    _prefix = "plugin state"


class PluginRenderError(VitalHostError, _ReasonError):
    """The plugin did not render what it was asked to: a length it cannot give, or another."""

    _prefix = "plugin render"


class MapMismatchError(VitalHostError):
    """The parameter map was measured on another machine, or from another plugin, than this one.

    The map's scales are exact for the build and the version of the plugin they were measured
    through; another build may round differently and another version hold other parameters, so the
    map is not used and a new census here is the remedy. `what` names the field that differs,
    `machine`, `instrument` or `vital_version`; `measured` is the map's value and `found` this one.
    """

    def __init__(self, what: str, measured: str, found: str) -> None:
        """Name the field that differs, the map's value for it and the one found here."""
        super().__init__(what, measured, found)
        self.what = what
        self.measured = measured
        self.found = found

    def __str__(self) -> str:
        """Say which field, and both values."""
        return f"the map's {self.what} is {self.measured!r}, here {self.found!r}"


class UnknownParameterError(VitalError, ParameterNotFoundError):
    """An id the parameter map does not hold, or a host id the plugin does not host.

    Core's `ParameterNotFoundError` too, whose `parameter_id` is a plain string: the census asks
    the host for display texts by pedalboard's key, which only the host reads.
    """


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
