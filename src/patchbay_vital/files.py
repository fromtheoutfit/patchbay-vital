"""A file replaced whole or not at all: written beside the target and renamed over it.

A preset can be a person's only copy, and the committed map and the key list derived from it are
read together, so neither is left half-written. `replace_file` writes the bytes to a temporary
beside the target, flushes them to disk, keeps the target's permissions, writes through a symlink
to what it points at, and renames the temporary over the target. A failure leaves the file as it
was and no temporary behind; what fails is the `OSError` or `ValueError` the file system raised,
which the caller reports as its own error. `patchbay_vital.format` writes a preset through it and
`patchbay_vital.census` the map and the key list (`vital/preset-file.md`, "dump replaces a file
whole or not at all"). It imports nothing from the package.
"""

import os
import shutil
import uuid
from pathlib import Path


def replace_file(path: Path, raw: bytes) -> None:
    """Write `raw` beside the file and rename it over, so a failure leaves the file as it was."""
    target = path.resolve()
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as file:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        if target.exists():
            shutil.copymode(target, temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
