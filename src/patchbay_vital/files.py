"""Files replaced whole or not at all: each written beside its target and renamed over it.

A preset can be a person's only copy, and the committed map and the key list derived from it are
read together, so none is left half-written and the two never disagree. `replace_files` writes
every file's bytes to a temporary beside its target, flushes each to disk and keeps the target's
permissions, writing through a symlink to what it points at, and reads the bytes of every target
but the last, which a later rename could force back; only once every temporary is staged is each
renamed over its target. A write or a read that fails leaves every file as it was; a rename that
fails after an earlier one succeeded puts the earlier file back from the bytes it held, so an
earlier target must be readable, and no temporary is left behind. The last file can never be put
back, so it is never read: `replace_file` reads nothing, and needs no read permission.

Once every file is renamed nothing can fail: each directory a rename changed is then flushed
once, so the replacement survives a crash, as a best effort. A file system that cannot flush a
directory (`_UNSUPPORTED`, some FUSE, SMB and NFS mounts) is passed over; any other failure there
leaves the files replaced but maybe not durable, a degraded result, which is logged as a warning
through this module's logger, naming the directory and the errno, and never raised. What fails is
the `OSError` or `ValueError` the file system raised, which the caller reports as its own error.
`patchbay_vital.format` writes a preset through `replace_file` and `patchbay_vital.census` the key
list and the map through `replace_files` (`vital/preset-file.md`, "dump replaces a file whole or
not at all"). It imports nothing from the package.
"""

import contextlib
import errno
import logging
import os
import shutil
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path

_LOG = logging.getLogger(__name__)

_UNSUPPORTED = frozenset({errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EBADF})
"""What a file system that cannot flush a directory gives: ENOTSUP and EOPNOTSUPP are two values on
macOS and one on Linux."""


def replace_file(path: Path, raw: bytes) -> None:
    """Replace one file whole or not at all: `replace_files` of it alone, which reads nothing."""
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
        held = [_held(target) for target, _ in staged[:-1]]
        _rename_each(staged, held)
    finally:
        for _, temporary in staged:
            temporary.unlink(missing_ok=True)
    for directory in dict.fromkeys(target.parent for target, _ in staged):
        _sync_directory(directory)


def _stage(target: Path, temporary: Path, raw: bytes) -> None:
    """Write the bytes to the temporary, flushed to disk, with the target's mode where it exists."""
    with temporary.open("xb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    if target.exists():
        shutil.copymode(target, temporary)


def _held(target: Path) -> bytes | None:
    """Return the bytes a target holds, to put it back, or None where it does not exist."""
    return target.read_bytes() if target.exists() else None


def _rename_each(staged: Sequence[tuple[Path, Path]], held: Sequence[bytes | None]) -> None:
    """Rename each temporary over its target; a failure puts every earlier target back.

    `held` is what every target but the last held, the last never needing putting back.
    """
    done = 0
    try:
        for target, temporary in staged:
            temporary.replace(target)
            done += 1
    except OSError:
        for (target, _), previous in zip(staged[:done], held[:done], strict=True):
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
    """Flush the directory entry a rename changed, as a best effort, where it can be opened.

    Windows cannot open a directory and journals its own metadata. A file system that cannot flush
    one is passed over; any other failure is logged as a warning, the files already replaced.
    """
    if os.name == "nt":
        return
    try:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as error:
        if error.errno not in _UNSUPPORTED:
            name = errno.errorcode.get(error.errno, str(error.errno)) if error.errno else "no errno"
            _LOG.warning(
                "replaced, but the directory %s was not flushed (%s: %s), so the replacement may"
                " not survive a crash",
                directory,
                name,
                error.strerror or error,
            )
