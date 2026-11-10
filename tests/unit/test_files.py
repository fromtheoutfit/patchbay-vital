"""A file is replaced whole or not at all: the temporary beside it, the mode kept, the link kept."""

import os
import stat
from pathlib import Path

import pytest

from patchbay_vital.files import replace_file

_RESTRICTED = 0o640


def test_a_failed_write_leaves_the_file_as_it_was_and_no_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the bytes cannot reach the disk, the target is untouched, nothing left beside it."""
    target = tmp_path / "map.json"
    target.write_bytes(b"old")

    def refuse(fd: int) -> None:
        msg = f"no room for {fd}"
        raise OSError(msg)

    monkeypatch.setattr(os, "fsync", refuse)
    with pytest.raises(OSError, match="no room"):
        replace_file(target, b"new")
    assert target.read_bytes() == b"old"
    assert sorted(tmp_path.iterdir()) == [target]


def test_writing_over_a_file_keeps_its_permissions(tmp_path: Path) -> None:
    """The target's mode survives the rename, as a person set it."""
    target = tmp_path / "keys.txt"
    target.write_bytes(b"old")
    target.chmod(_RESTRICTED)
    replace_file(target, b"new")
    assert target.read_bytes() == b"new"
    assert stat.S_IMODE(target.stat().st_mode) == _RESTRICTED
    assert sorted(tmp_path.iterdir()) == [target]


def test_writing_through_a_symlink_keeps_the_link(tmp_path: Path) -> None:
    """A link is followed: what it points at is replaced and the link still points there."""
    real = tmp_path / "real.json"
    real.write_bytes(b"old")
    link = tmp_path / "link.json"
    link.symlink_to(real)
    replace_file(link, b"new")
    assert link.is_symlink()
    assert real.read_bytes() == b"new"


def test_a_file_that_was_not_there_is_made(tmp_path: Path) -> None:
    """The first write makes the file, with nothing to keep the mode of."""
    target = tmp_path / "new.json"
    replace_file(target, b"first")
    assert target.read_bytes() == b"first"
