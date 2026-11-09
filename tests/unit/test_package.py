"""The package's surface is __all__, and its distribution carries the license."""

import importlib.metadata
import types

import patchbay_vital


def test_public_names_are_in_all() -> None:
    """Every name the package binds without a leading underscore is one __all__ exports.

    Its submodules aside: importing a submodule binds it on the package, the import system's doing
    rather than an export, and `from patchbay_vital import *` does not import them.
    """
    public = {
        name
        for name, value in vars(patchbay_vital).items()
        if not name.startswith("_") and not isinstance(value, types.ModuleType)
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
