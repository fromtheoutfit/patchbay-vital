"""Files are replaced whole or not at all: staged beside their targets, the mode and link kept.

Only a file a later rename could force back is read, and each directory is flushed once, after
every rename, as a best effort: a flush that fails never undoes or reports a replacement as failed,
and one other than a file system's "unsupported" is logged as a warning.
"""

import errno
import logging
import os
import stat
from pathlib import Path

import pytest

from patchbay_vital.files import replace_file, replace_files

_RESTRICTED = 0o640
_WRITE_ONLY = 0o200


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


_NO_DIRECTORY_FLUSH = pytest.mark.skipif(
    os.name == "nt", reason="Windows cannot open a directory to sync it"
)


@_NO_DIRECTORY_FLUSH
def test_every_directory_is_synced_once_after_every_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both files are flushed and renamed before their directory is flushed, once, after both."""
    events: list[str] = []
    fsync, replace = os.fsync, Path.replace

    def record_sync(fd: int) -> None:
        events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        fsync(fd)

    def record_rename(self: Path, target: Path) -> Path:
        events.append("rename")
        return replace(self, target)

    monkeypatch.setattr(os, "fsync", record_sync)
    monkeypatch.setattr(Path, "replace", record_rename)
    replace_files({tmp_path / "keys.txt": b"keys", tmp_path / "map.json": b"map"})
    assert events == ["file", "file", "rename", "rename", "directory"]


@_NO_DIRECTORY_FLUSH
@pytest.mark.parametrize(
    ("code", "warned"), [(errno.EINVAL, False), (errno.EIO, True)], ids=["EINVAL", "EIO"]
)
def test_a_directory_that_cannot_be_synced_leaves_every_file_replaced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    code: int,
    warned: bool,  # noqa: FBT001 - a parametrized expectation, given by pytest by name
) -> None:
    """A failed flush is no failed replacement: nothing is raised and nothing put back.

    It is logged as a warning, naming the directory and the errno, unless the file system cannot
    flush a directory at all.
    """
    first, second = tmp_path / "keys.txt", tmp_path / "data" / "map.json"
    second.parent.mkdir()
    first.write_bytes(b"old keys")
    second.write_bytes(b"old map")
    fsync = os.fsync

    def refuse_directories(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(code, os.strerror(code))
        fsync(fd)

    monkeypatch.setattr(os, "fsync", refuse_directories)
    with caplog.at_level(logging.WARNING, logger="patchbay_vital.files"):
        replace_files({first: b"new keys", second: b"new map"})
    assert (first.read_bytes(), second.read_bytes()) == (b"new keys", b"new map")
    assert sorted(tmp_path.rglob("*")) == sorted([first, second.parent, second])
    records = [record for record in caplog.records if record.name == "patchbay_vital.files"]
    if warned:
        assert [record.levelno for record in records] == [logging.WARNING] * 2
        for record, directory in zip(records, (first.parent, second.parent), strict=True):
            assert f"directory {directory.resolve()} was not flushed (EIO" in record.getMessage()
    else:
        assert records == []


def test_only_a_file_a_later_rename_could_force_back_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One file is never read; of three, the first two are, before any rename, and the last not."""
    paths = [tmp_path / name for name in ("a.txt", "b.txt", "c.txt")]
    for path in paths:
        path.write_bytes(b"old")
    read: list[str] = []
    read_bytes = Path.read_bytes

    def record(self: Path) -> bytes:
        read.append(self.name)
        return read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", record)
    replace_file(paths[0], b"new")
    assert read == []
    replace_files(dict.fromkeys(paths, b"newer"))
    assert read == ["a.txt", "b.txt"]
    assert [path.read_bytes() for path in paths] == [b"newer"] * 3


@pytest.mark.skipif(
    os.name == "nt" or os.geteuid() == 0, reason="needs POSIX permissions that bind the user"
)
def test_a_file_that_cannot_be_read_is_still_replaced(tmp_path: Path) -> None:
    """A file the user may write but not read is replaced as before, its mode kept."""
    target = tmp_path / "preset.vital"
    target.write_bytes(b"old")
    target.chmod(_WRITE_ONLY)
    replace_file(target, b"new")
    assert stat.S_IMODE(target.stat().st_mode) == _WRITE_ONLY
    target.chmod(_RESTRICTED)
    assert target.read_bytes() == b"new"
    assert sorted(tmp_path.iterdir()) == [target]
