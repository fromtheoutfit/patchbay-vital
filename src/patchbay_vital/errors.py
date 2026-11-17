"""The exceptions patchbay-vital raises: one root, each carrying the fields that say what failed.

`VitalError` is the root and derives from patchbay's `PatchbayError`, so a caller catches
everything this package reports with one `except`, and everything any patchbay package reports
with another. Under it, `VitalFormatError` is a preset's: a preset that cannot be read is
`MalformedPresetError` or `UnknownSettingError`, never pydantic's or `json`'s error, and a file that
cannot be reached is `PresetFileError`, never an `OSError`. `VitalHostError` is the hosted plugin's:
a plugin that cannot be loaded is `PluginLoadError`, state bytes the codec cannot read, or a read,
a state or a value the plugin refuses, a state it answers with its alert and a state it ignores
are `PluginStateError`, a render the plugin cannot give is `PluginRenderError`, a parameter map
measured on another machine, or from another plugin, than this one is `MapMismatchError`, naming
what differs, and a state loaded from a thread that is not the main one, where the host makes no
load, is `PluginThreadError`; nothing pedalboard raises leaves the host. `CensusError` is the
generator's, naming a parameter it cannot fit. A model built directly refuses as patchbay's
`PatchbayValidationError`, as every model on `PatchbayModel` does.

A failure core's protocol names derives from the root and from core's own error for it as well:
`UnknownParameterError` is a `ParameterNotFoundError`, `ParameterRangeError` a
`ValueOutOfRangeError`, `ParameterUnitError` a `UnitMismatchError`, `PatchRefusedError` a
`PatchRejectedError` and `RenderRefusedError` a `RenderFailedError`, so a caller holding core's
types, its contract tests among them, catches them, and this package's one root still holds. Each
takes core's own fields, in core's order, and core's message. The instrument raises the last three:
a value in another unit than the parameter's, a patch it does not load, and a render it does not
give.

Each error takes its fields as arguments, keeps them as attributes and passes them to `Exception`,
so `args` and pickling carry them, and builds its message from them in `__str__`. The three that
carry a reason alone share one private base, which prefixes the reason with what failed. The fields
are plain values, so this module imports nothing else from the package and every other module can
import it.
"""

from typing import ClassVar

from patchbay import (
    ParameterNotFoundError,
    PatchbayError,
    PatchRejectedError,
    RenderFailedError,
    UnitMismatchError,
    ValueOutOfRangeError,
)


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
    """Bytes are not a state this package reads, or the plugin refused a read or a write.

    A write the plugin answered with its alert is one too, the alert's own words in the reason,
    and so is a write it ignored, which a marker set before it shows. Also what an instrument
    raises once the plugin has refused a load and the model's own text after it, its state then
    unknown, and for every later call that would reach the plugin.
    """

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


class PluginThreadError(VitalHostError):
    """A state was to be loaded from a thread that is not the main one, and was not.

    On macOS Vital answers a text it cannot read with an alert, which only the main thread can
    open. From another thread the load raises instead, the plugin's parameters are then read
    stale, and the process dies at its next render (the spec of issue #20's
    `verification/probes-3-counts.txt`). So the host makes no load there: this is raised before
    the plugin is called, and nothing is changed. `thread` is the name of the thread that asked.
    """

    def __init__(self, thread: str) -> None:
        """Name the thread the load was asked from."""
        super().__init__(thread)
        self.thread = thread

    def __str__(self) -> str:
        """Say where a load is made, and where this one was asked from."""
        return f"a state is loaded from the main thread only, not from {self.thread!r}"


class UnknownParameterError(VitalError, ParameterNotFoundError):
    """An id the parameter map does not hold, or a host id the plugin does not host.

    Core's `ParameterNotFoundError` too, whose `parameter_id` is a plain string: the census asks
    the host for display texts by pedalboard's key, which only the host reads.
    """


class ParameterRangeError(VitalError, ValueOutOfRangeError):
    """A value outside what a parameter takes; core's `ValueOutOfRangeError` too."""


class ParameterUnitError(VitalError, UnitMismatchError):
    """A value in another unit than the parameter's own; core's `UnitMismatchError` too.

    `expected` is the parameter's unit and `given` the value's, each the unit's name.
    """


class PatchRefusedError(VitalError, PatchRejectedError):
    """A patch the instrument does not load, nothing about it changed; a `PatchRejectedError` too.

    `reason` says why and, where one entry of the patch refused it, names that entry's key: the
    first to refuse, in the order the patch is checked. The error that refused it is the cause.
    """


class RenderRefusedError(VitalError, RenderFailedError):
    """A render the instrument does not give; core's `RenderFailedError` too.

    `reason` names the limit passed and its value, the pitch and sample of a note no MIDI channel
    is left to voice, or what the plugin gave in place of the render, the host's error then the
    cause.
    """


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
