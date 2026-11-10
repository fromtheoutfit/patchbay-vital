"""The package's surface is __all__, and its distribution carries the license and its ranges."""

import importlib.metadata
import subprocess
import sys
import types

from packaging.requirements import Requirement
from patchbay import PatchbayError, PatchbayModel, PresetKey

import patchbay_vital
import patchbay_vital.errors
import patchbay_vital.format
import patchbay_vital.parameters
import patchbay_vital.preset


def _is_own_submodule(value: object) -> bool:
    """Say whether a value bound on the package is a module of the package itself."""
    return isinstance(value, types.ModuleType) and value.__name__.startswith("patchbay_vital.")


def test_public_names_are_in_all() -> None:
    """Every name the package binds without a leading underscore is one __all__ exports.

    Its own submodules aside: importing one binds it on the package, the import system's doing
    rather than an export, and `from patchbay_vital import *` does not import them. Any other
    module bound here, `import json` say, is a public name like any other.
    """
    public = {
        name
        for name, value in vars(patchbay_vital).items()
        if not name.startswith("_") and not _is_own_submodule(value)
    }
    assert public <= set(patchbay_vital.__all__)


def test_every_name_in_all_resolves() -> None:
    """__all__ names only what the package binds, each once, so `import *` cannot fail."""
    assert len(set(patchbay_vital.__all__)) == len(patchbay_vital.__all__)
    assert all(hasattr(patchbay_vital, name) for name in patchbay_vital.__all__)


def test_distribution_names_its_license_file() -> None:
    """The installed metadata states the license and names the LICENSE file shipped with it."""
    metadata = importlib.metadata.metadata("patchbay-vital")
    assert metadata["License-Expression"] == "MIT"
    assert metadata.get_all("License-File") == ["LICENSE"]


def test_the_pinned_patchbay_core_is_in_the_declared_range() -> None:
    """The commit [tool.uv.sources] pins is a version the range the wheel declares admits.

    uv does not check the range against a git source, so nothing else holds the two together.
    """
    declared = [Requirement(line) for line in importlib.metadata.requires("patchbay-vital") or ()]
    core = next(requirement for requirement in declared if requirement.name == "patchbay-core")
    assert core.specifier.contains(importlib.metadata.version("patchbay-core"))


def test_pedalboard_is_declared_only_under_the_host_extra() -> None:
    """The wheel asks for pedalboard under `host` alone, in a range the gate's pin satisfies.

    pedalboard is GPLv3 and this package MIT, so a plain install brings none of it (the host
    spec's shape.md, Decision 2).
    """
    declared = [Requirement(line) for line in importlib.metadata.requires("patchbay-vital") or ()]
    pedalboard = [requirement for requirement in declared if requirement.name == "pedalboard"]
    assert len(pedalboard) == 1
    (requirement,) = pedalboard
    assert requirement.marker is not None
    assert requirement.marker.evaluate({"extra": "host"})
    assert not requirement.marker.evaluate({"extra": ""})
    assert requirement.specifier.contains(importlib.metadata.version("pedalboard"))


def test_the_host_extra_declares_numpy_which_host_py_imports() -> None:
    """A package the code imports directly is declared, though core and pedalboard bring it in."""
    declared = [Requirement(line) for line in importlib.metadata.requires("patchbay-vital") or ()]
    (numpy,) = [requirement for requirement in declared if requirement.name == "numpy"]
    assert numpy.marker is not None
    assert numpy.marker.evaluate({"extra": "host"})
    assert numpy.specifier.contains(importlib.metadata.version("numpy"))


def test_importing_the_package_loads_no_pedalboard() -> None:
    """A fresh interpreter with pedalboard made unimportable still imports the package whole.

    The format layer and the map install without the extra; only `patchbay_vital.host` and what
    imports it need pedalboard, and the root re-exports neither.
    """
    code = (
        "import sys\n"
        "sys.modules['pedalboard'] = None\n"
        "import patchbay_vital, patchbay_vital.format, patchbay_vital.parameters\n"
        "import patchbay_vital.state, patchbay_vital.float32, patchbay_vital.grisu2\n"
        "roots = ('pedalboard', 'pedalboard_native')\n"
        "loaded = [n for n, m in sys.modules.items() if n.split('.')[0] in roots and m]\n"
        "assert not loaded, loaded\n"
    )
    # The interpreter running this test, given our own code: a fresh process is the only place an
    # import can be watched from the start.
    result = subprocess.run(  # noqa: S603 - our interpreter and our own code
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_the_names_the_adapter_builds_on_come_from_patchbay_core() -> None:
    """A pinned commit lacking one fails here, ahead of the first adapter module to import it."""
    assert PatchbayModel.__module__ == "patchbay.models"
    assert PresetKey.__module__ == "patchbay.models"
    assert PatchbayError.__module__ == "patchbay.errors"


def test_the_package_re_exports_what_a_consumer_uses() -> None:
    """Each name the root exports is the very object its module defines, not a copy."""
    surface = {
        patchbay_vital.errors: (
            "CensusError",
            "MalformedPresetError",
            "MapMismatchError",
            "ParameterRangeError",
            "PluginLoadError",
            "PluginRenderError",
            "PluginStateError",
            "PresetFileError",
            "UnknownParameterError",
            "UnknownSettingError",
            "VitalError",
            "VitalFormatError",
            "VitalHostError",
        ),
        patchbay_vital.format: ("diff", "dump", "dumps", "load", "loads"),
        patchbay_vital.parameters: (
            "PRESET_ONLY_KEYS",
            "DisplayCurve",
            "MappedParameter",
            "NormalizedScale",
            "ParameterMap",
            "parameter_map",
        ),
        patchbay_vital.preset: (
            "MetadataChange",
            "Modulation",
            "ModulationChange",
            "OpaqueChange",
            "PresetDiff",
            "SettingChange",
            "VitalPreset",
            "VitalSettings",
        ),
    }
    for module, names in surface.items():
        for name in names:
            assert getattr(patchbay_vital, name) is getattr(module, name)
