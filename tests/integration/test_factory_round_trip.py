"""Every preset Vital installed comes back byte for byte, and the set of them is the one expected.

Each comes back through the file's own reader and writer, and through a core `Patch` and its JSON
(`patchbay_vital.patch`), which needs no plugin either.

The presets are Vital's and may not be redistributed, so they are read where an installed Vital
keeps them and the tests that read them skip, saying so, where they are absent; those carry the
`integration` marker, and the manifest's own count, which reads nothing installed, does not. The
manifest is committed: its length is the count, so a missing directory cannot pass on zero cases,
and a pack removed or newly installed fails by name until the manifest is changed deliberately.
`User/` is where Vital keeps a person's own saves, so the walk leaves it out.
"""

from pathlib import Path

import pytest
from patchbay import Patch

from patchbay_vital import dumps, loads
from patchbay_vital.patch import patch_of, preset_of

_ROOT = Path.home() / "Music" / "Vital"
_USER = "User"
_MANIFEST = Path("tests") / "data" / "factory-manifest.txt"
_FACTORY_HEADING, _PACKS_HEADING = "# Factory", "# Packs"
_FACTORY_COUNT, _PACK_COUNT = 7, 68


def _groups(root: Path) -> dict[str, list[str]]:
    """Return the manifest's paths under each of its headings."""
    groups: dict[str, list[str]] = {_FACTORY_HEADING: [], _PACKS_HEADING: []}
    heading = _FACTORY_HEADING
    for line in (root / _MANIFEST).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            heading = line
        else:
            groups[heading].append(line)
    return groups


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize over the manifest itself, so every expected preset is a case wherever it runs."""
    groups = _groups(metafunc.config.rootpath)
    if "factory_preset" in metafunc.fixturenames:
        metafunc.parametrize("factory_preset", groups[_FACTORY_HEADING])
    if "pack_preset" in metafunc.fixturenames:
        metafunc.parametrize("pack_preset", groups[_PACKS_HEADING])


@pytest.fixture
def presets_root() -> Path:
    """Return where an installed Vital keeps its presets, or skip saying they are not here."""
    if not _ROOT.is_dir():
        pytest.skip(f"no installed Vital presets at {_ROOT}")
    return _ROOT


def _assert_round_trip(root: Path, relative: str) -> None:
    """Assert one file comes back byte for byte, naming the first offset that does not."""
    text = (root / relative).read_bytes().decode("utf-8")
    written = dumps(loads(text))
    if written != text:
        offset = next(
            (
                i
                for i, (ours, theirs) in enumerate(zip(written, text, strict=False))
                if ours != theirs
            ),
            min(len(written), len(text)),
        )
        pytest.fail(f"{relative}: differs at offset {offset}: {written[offset : offset + 60]!r}")


def test_the_manifest_holds_the_expected_count(pytestconfig: pytest.Config) -> None:
    """The count is the manifest's length, Factory and packs apart, each path once."""
    groups = _groups(pytestconfig.rootpath)
    assert len(groups[_FACTORY_HEADING]) == _FACTORY_COUNT
    assert len(groups[_PACKS_HEADING]) == _PACK_COUNT
    paths = [path for group in groups.values() for path in group]
    assert len(set(paths)) == len(paths)


@pytest.mark.integration
def test_the_installed_presets_are_the_manifest_s(
    presets_root: Path, pytestconfig: pytest.Config
) -> None:
    """A listed file missing, or an unlisted one present, fails by name."""
    listed = {path for group in _groups(pytestconfig.rootpath).values() for path in group}
    found = {
        path.relative_to(presets_root).as_posix()
        for path in presets_root.rglob("*.vital")
        if path.relative_to(presets_root).parts[0] != _USER
    }
    assert sorted(listed - found) == [], "listed in the manifest and not installed"
    assert sorted(found - listed) == [], "installed and not listed in the manifest"


@pytest.mark.integration
def test_a_factory_preset_round_trips(presets_root: Path, factory_preset: str) -> None:
    """`dumps(loads(text)) == text` for one of Vital's own presets."""
    _assert_round_trip(presets_root, factory_preset)


@pytest.mark.integration
def test_a_pack_preset_round_trips(presets_root: Path, pack_preset: str) -> None:
    """`dumps(loads(text)) == text` for one preset of an artist pack."""
    _assert_round_trip(presets_root, pack_preset)


def _assert_round_trip_through_a_patch(root: Path, relative: str) -> None:
    """Assert one file comes back byte for byte through a patch, and through the patch's JSON."""
    text = (root / relative).read_bytes().decode("utf-8")
    patch = patch_of(loads(text))
    assert dumps(preset_of(patch)) == text, relative
    assert dumps(preset_of(Patch.model_validate_json(patch.model_dump_json()))) == text, relative


@pytest.mark.integration
def test_a_factory_preset_round_trips_through_a_patch(
    presets_root: Path, factory_preset: str
) -> None:
    """`preset_of(patch_of(preset))` writes the bytes one of Vital's own presets holds."""
    _assert_round_trip_through_a_patch(presets_root, factory_preset)


@pytest.mark.integration
def test_a_pack_preset_round_trips_through_a_patch(presets_root: Path, pack_preset: str) -> None:
    """The same for one preset of an artist pack, its out-of-range floats and old keys kept."""
    _assert_round_trip_through_a_patch(presets_root, pack_preset)
