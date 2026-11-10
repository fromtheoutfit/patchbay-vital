"""patchbay-vital: the patchbay adapter for Vital.

The package re-exports what a consumer uses and nothing else lives here: the models of a preset
(`patchbay_vital.preset`), reading, writing and comparing a `.vital` file
(`patchbay_vital.format`), the parameter map and its scales (`patchbay_vital.parameters`) and the
errors (`patchbay_vital.errors`). Writing a float as Vital does is `patchbay_vital.grisu2`, float32
arithmetic `patchbay_vital.float32`, the plugin state's containers `patchbay_vital.state`, and the
reversible join of a preset's modulations stays in `patchbay_vital.format`; none is re-exported.

Hosting the plugin, `patchbay_vital.host`, and the map's generator, `patchbay_vital.census`, need
pedalboard, which is GPLv3 and comes only with the `host` extra: they are imported by name, and
importing this package never imports them.

`__version__` is the one in pyproject.toml, read from the installed distribution's metadata so
there is one place it is written. Import the package installed (`uv sync`): from a bare src/ on
sys.path there is no distribution to read, so importlib.metadata raises PackageNotFoundError
rather than the package inventing a version.
"""

import importlib.metadata as _metadata

from patchbay_vital.errors import (
    CensusError,
    MalformedPresetError,
    MapMismatchError,
    ParameterRangeError,
    PluginLoadError,
    PluginRenderError,
    PluginStateError,
    PresetFileError,
    UnknownParameterError,
    UnknownSettingError,
    VitalError,
    VitalFormatError,
    VitalHostError,
)
from patchbay_vital.format import diff, dump, dumps, load, loads
from patchbay_vital.parameters import (
    PRESET_ONLY_KEYS,
    DisplayCurve,
    MappedParameter,
    NormalizedScale,
    ParameterMap,
    parameter_map,
)
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
    "PRESET_ONLY_KEYS",
    "CensusError",
    "DisplayCurve",
    "MalformedPresetError",
    "MapMismatchError",
    "MappedParameter",
    "MetadataChange",
    "Modulation",
    "ModulationChange",
    "NormalizedScale",
    "OpaqueChange",
    "ParameterMap",
    "ParameterRangeError",
    "PluginLoadError",
    "PluginRenderError",
    "PluginStateError",
    "PresetDiff",
    "PresetFileError",
    "SettingChange",
    "UnknownParameterError",
    "UnknownSettingError",
    "VitalError",
    "VitalFormatError",
    "VitalHostError",
    "VitalPreset",
    "VitalSettings",
    "__version__",
    "diff",
    "dump",
    "dumps",
    "load",
    "loads",
    "parameter_map",
]
