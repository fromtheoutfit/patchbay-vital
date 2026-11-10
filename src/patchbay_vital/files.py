"""Files replaced whole or not at all: each written beside its target and renamed over it.

A preset can be a person's only copy, and the committed map and the key list derived from it are
read together, so none is left half-written and the two never disagree. `replace_files` writes
every file's bytes to a temporary beside its target, flushes each to disk and keeps the target's
permissions, writing through a symlink to what it points at; only once every temporary is staged
is each renamed over its target, the directory flushed after it so the replacement survives a
crash. A write that fails leaves every file as it was; a rename that fails after an earlier one
succeeded puts the earlier file back from the bytes it held, and no temporary is left behind. What
fails is the `OSError` or `ValueError` the file system raised, which the caller reports as its own
error. `patchbay_vital.format` writes a preset through `replace_file` and `patchbay_vital.census`
the key list and the map through `replace_files` (`vital/preset-file.md`, "dump replaces a file
whole or not at all"). It imports nothing from the package.
"""

import contextlib
import os
import shutil
import uuid
from collections.abc import Mapping
from pathlib import Path


def replace_file(path: Path, raw: bytes) -> None:
    """Replace one file whole or not at all: `replace_files` of it alone."""
    replace_files({path: raw})


def replace_files(files: Mapping[Path, bytes]) -> None:
    """Write every file beside its target, then rename each over, so all change or none does."""
    staged: list[tuple[Path, Path]] = []
    try:
        for path, raw in files.items():
            target = path.resolve()
            temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
            staged.append((target, temporary))
            _stage(target, temporary, raw)
        _rename_each(staged)
    finally:
        for _, temporary in staged:
            temporary.unlink(missing_ok=True)


def _stage(target: Path, temporary: Path, raw: bytes) -> None:
    """Write the bytes to the temporary, flushed to disk, with the target's mode where it exists."""
    with temporary.open("xb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    if target.exists():
        shutil.copymode(target, temporary)


def _rename_each(staged: list[tuple[Path, Path]]) -> None:
    """Rename each temporary over its target; a failure puts every earlier target back."""
    replaced: list[tuple[Path, bytes | None]] = []
    try:
        for target, temporary in staged:
            previous = target.read_bytes() if target.exists() else None
            temporary.replace(target)
            _sync_directory(target.parent)
            replaced.append((target, previous))
    except OSError:
        for target, previous in replaced:
            _put_back(target, previous)
        raise


def _put_back(target: Path, previous: bytes | None) -> None:
    """Restore a target to the bytes it held, or remove one that did not exist; best effort."""
    with contextlib.suppress(OSError):
        if previous is None:
            target.unlink(missing_ok=True)
        else:
            replace_files({target: previous})


def _sync_directory(directory: Path) -> None:
    """Flush the directory entry a rename changed, where the platform lets a directory be opened.

    Windows cannot open one and journals its own metadata.
    """
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
