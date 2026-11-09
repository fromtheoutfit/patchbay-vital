"""patchbay-vital: the patchbay adapter for Vital.

The package re-exports what a consumer uses and nothing else lives here: the models of a preset
(`patchbay_vital.preset`), reading, writing and comparing a `.vital` file
(`patchbay_vital.format`) and the errors (`patchbay_vital.errors`). Writing a float as Vital does is
`patchbay_vital.grisu2`, and the reversible join of a preset's modulations stays in
`patchbay_vital.format`; neither is re-exported here.

`__version__` is the one in pyproject.toml, read from the installed distribution's metadata so
there is one place it is written. Import the package installed (`uv sync`): from a bare src/ on
sys.path there is no distribution to read, so importlib.metadata raises PackageNotFoundError
rather than the package inventing a version.
"""

import importlib.metadata as _metadata

from patchbay_vital.errors import (
    MalformedPresetError,
    PresetFileError,
    UnknownSettingError,
    VitalFormatError,
)
from patchbay_vital.format import diff, dump, dumps, load, loads
from patchbay_vital.preset import (
    MetadataChange,
    Modulation,
    ModulationChange,
    OpaqueChange,
    PresetDiff,
    SettingChange,
    VitalPreset,
    VitalSettings,
)

__version__ = _metadata.version("patchbay-vital")

__all__ = [
    "MalformedPresetError",
    "MetadataChange",
    "Modulation",
    "ModulationChange",
    "OpaqueChange",
    "PresetDiff",
    "PresetFileError",
    "SettingChange",
    "UnknownSettingError",
    "VitalFormatError",
    "VitalPreset",
    "VitalSettings",
    "__version__",
    "diff",
    "dump",
    "dumps",
    "load",
    "loads",
]
