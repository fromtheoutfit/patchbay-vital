"""What the unit and the integration tests share: the rows recorded under `tests/data/`.

`volume-floor.txt` holds `volume`'s values at or below its floor, and `power-of-two-presets.txt` a
held power of two whose normalized path lands short of it, each row a value and the step it lands
at today; `stepped` reads a row's step the one way every test reads it. A conftest, not a plain
module like `tests/unit/builders.py`: `tests/` is no package, so pytest puts each test file's own
directory on the import path and `tests/integration` never sees a module of `tests/unit`. The
tests that read the rows take a fixture, so one reader serves both, here in the directory that
holds them (`base/testing/tests.md`). A script outside pytest reads the same files through
`recorded_rows`.
"""

import math
import struct
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

_HEX_DIGITS = 8
"""A float32 written as its bits, as `tests/data/fma-vectors.txt` writes one."""

_WIDTHS = (32, 64)
"""The widths `stepped` counts in, float32 and double."""

_STEPS = frozenset({-1, 0, 1})
"""The distances a row may record, one step either way or none: the property's bound."""


def recorded_rows(path: Path) -> tuple[tuple[float, int], ...]:
    """Return each row's normalized value and the signed steps it lands at, as its file counts them.

    A line is a row but a blank one or a `#` comment. A row that is not eight hex digits and a
    step of -1, 0 or +1, or a file with no row, raises ValueError naming the file and the line.
    """
    rows: list[tuple[float, int]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        try:
            token, steps = fields[0], int(fields[1])
            if len(token) != _HEX_DIGITS or steps not in _STEPS:
                raise ValueError(token)  # noqa: TRY301 - one refusal for every malformed shape
            value: float = struct.unpack(">f", bytes.fromhex(token))[0]
        except (IndexError, ValueError) as error:
            msg = f"{path.name}:{number}: not a float32's hex digits and a step of -1, 0 or +1"
            raise ValueError(msg) from error
        rows.append((value, steps))
    if not rows:
        msg = f"{path.name} holds no row"
        raise ValueError(msg)
    return tuple(rows)


def stepped(value: float, steps: int, width: int) -> float:
    """Return the float `steps` steps from `value` in value order, float32 steps or doubles.

    `width` is 32 or 64; `value` must be one of that width exactly. A row's step column is read
    through this, in the unit and the integration tests alike. ValueError for another width or a
    value of another width.
    """
    dtype = np.float32 if width == _WIDTHS[0] else np.float64
    if width not in _WIDTHS or float(dtype(value)) != value:
        msg = f"not a float of width {width}: {value!r}"
        raise ValueError(msg)
    x = dtype(value)
    toward = dtype(math.copysign(math.inf, steps))
    for _ in range(abs(steps)):
        x = np.nextafter(x, toward)
    return float(x)


@pytest.fixture(name="stepped")
def _stepped() -> Callable[[float, int, int], float]:
    """Return `stepped`, so a test taking fixtures reads a row's step as the others do."""
    return stepped


@pytest.fixture
def volume_floor(pytestconfig: pytest.Config) -> tuple[tuple[float, int], ...]:
    """Return `volume`'s recorded values at or below its floor, each with its set's display step.

    The steps are today's map (`tests/data/volume-floor.txt`'s header names the issue that changes
    them); every test that holds them reads them here, so a change to the file reaches each.
    """
    return recorded_rows(pytestconfig.rootpath / "tests" / "data" / "volume-floor.txt")


@pytest.fixture
def power_of_two_presets(pytestconfig: pytest.Config) -> tuple[tuple[float, int], ...]:
    """Return the recorded values whose held power of two the normalized path lands short of.

    Each with the float32 steps the preset a set holds lands from it, today's map
    (`tests/data/power-of-two-presets.txt`'s header names the issue that changes them).
    """
    return recorded_rows(pytestconfig.rootpath / "tests" / "data" / "power-of-two-presets.txt")
