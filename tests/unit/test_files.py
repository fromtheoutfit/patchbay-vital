"""Files are replaced whole or not at all: staged beside their targets, the mode and link kept."""

import os
import stat
from pathlib import Path

import pytest

from patchbay_vital.files import replace_file, replace_files

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


def test_several_files_are_staged_before_any_is_renamed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A write failing on the second file leaves the first as it was: nothing was renamed yet."""
    first, second = tmp_path / "keys.txt", tmp_path / "map.json"
    first.write_bytes(b"old keys")
    second.write_bytes(b"old map")
    synced = 0
    fsync = os.fsync

    def refuse_second(fd: int) -> None:
        nonlocal synced
        synced += 1
        if synced == 2:  # noqa: PLR2004 - the second file's bytes
            msg = "no room"
            raise OSError(msg)
        fsync(fd)

    monkeypatch.setattr(os, "fsync", refuse_second)
    with pytest.raises(OSError, match="no room"):
        replace_files({first: b"new keys", second: b"new map"})
    assert (first.read_bytes(), second.read_bytes()) == (b"old keys", b"old map")
    assert sorted(tmp_path.iterdir()) == [first, second]


def test_a_rename_failing_after_an_earlier_one_puts_the_earlier_file_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both files change or neither does: the first is restored from the bytes it held."""
    first, second, third = tmp_path / "a.txt", tmp_path / "b.txt", tmp_path / "c.txt"
    first.write_bytes(b"old a")
    renames = 0
    replace = Path.replace

    def failing_second(self: Path, target: Path) -> Path:
        nonlocal renames
        renames += 1
        if renames == 2:  # noqa: PLR2004 - the second file's rename
            msg = f"cannot rename over {target.name}"
            raise OSError(msg)
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_second)
    with pytest.raises(OSError, match=r"cannot rename over b\.txt"):
        replace_files({first: b"new a", second: b"new b", third: b"new c"})
    assert first.read_bytes() == b"old a"
    assert not second.exists()
    assert not third.exists()
    assert sorted(tmp_path.iterdir()) == [first]


def test_a_file_that_did_not_exist_is_removed_again_when_a_later_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A target made by the first rename is unmade when the second fails, as it was not there."""
    first, second = tmp_path / "a.txt", tmp_path / "b.txt"
    replace = Path.replace

    def failing_second(self: Path, target: Path) -> Path:
        if target == second:
            msg = "cannot rename"
            raise OSError(msg)
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_second)
    with pytest.raises(OSError, match="cannot rename"):
        replace_files({first: b"a", second: b"b"})
    assert sorted(tmp_path.iterdir()) == []


@pytest.mark.skipif(os.name == "nt", reason="Windows cannot open a directory to sync it")
def test_the_directory_is_synced_after_the_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The directory entry the rename changed is flushed too, so the replacement is durable."""
    target = tmp_path / "map.json"
    synced: list[bool] = []
    fsync = os.fsync

    def record(fd: int) -> None:
        synced.append(stat.S_ISDIR(os.fstat(fd).st_mode))
        fsync(fd)

    monkeypatch.setattr(os, "fsync", record)
    replace_file(target, b"new")
    assert synced == [False, True]
