"""The package's surface is __all__, and its distribution carries the license and its range."""

import importlib.metadata
import types

from packaging.requirements import Requirement
from patchbay import PatchbayError, PatchbayModel, PresetKey

import patchbay_vital


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


def test_the_names_the_adapter_builds_on_come_from_patchbay_core() -> None:
    """A pinned commit lacking one fails here, ahead of the first adapter module to import it."""
    assert PatchbayModel.__module__ == "patchbay.models"
    assert PresetKey.__module__ == "patchbay.models"
    assert PatchbayError.__module__ == "patchbay.errors"
