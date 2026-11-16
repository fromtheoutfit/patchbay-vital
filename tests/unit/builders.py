"""What the unit tests share: strategies, an empty slot, a preset, and what a set holds.

What a set holds is worked out from primitives, for the instrument's tests and the patch's alike.
A plain module and not a conftest: a property test takes these at its decorator or under `@given`,
where a function-scoped fixture fails hypothesis's health check, and the gate's negative test q
writes a conftest of its own at tests/unit/conftest.py.
"""

import struct
from fractions import Fraction

from hypothesis import strategies as st

from patchbay_vital.preset import (
    KNOWN_SETTINGS,
    MODULATION_SLOTS,
    Modulation,
    VitalPreset,
    VitalSettings,
)

FLOATS = st.floats(allow_nan=False, allow_infinity=False, width=32)
KEYS = st.sampled_from(sorted(KNOWN_SETTINGS))
EMPTY_SLOT = Modulation(
    source=None, destination=None, amount=0.0, bipolar=0.0, bypass=0.0, power=0.0, stereo=0.0
)
_METADATA = {
    "author": "",
    "comments": "",
    "macro1": "M1",
    "macro2": "M2",
    "macro3": "M3",
    "macro4": "M4",
    "preset_style": "",
    "synth_version": "1.6.4",
}


def make_preset(**changes: object) -> VitalPreset:
    """Return a valid preset of empty slots with `changes` applied."""
    fields = {
        **_METADATA,
        "settings": VitalSettings(values={}),
        "modulations": (EMPTY_SLOT,) * MODULATION_SLOTS,
        "opaque": {},
    }
    return VitalPreset.model_validate({**fields, **changes})


def _round32(value: Fraction) -> float:
    """Return the float32 nearest an exact value: the nearer of the two a double's rounding gives.

    `float(Fraction)` is correctly rounded to a double, and every value here is far enough from a
    float32 tie that the double's rounding to float32 is the exact value's.
    """
    held: float = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    return held


def what_a_set_holds(own: float, minimum: float, maximum: float) -> tuple[float, float]:
    """Return the normalized value a host is sent for a float32, and the float32 it then holds.

    From primitives, as the plugin computes them on a linear scale: the span is the float32
    difference of the scale's ends, the normalized value the float32 nearest the exact quotient,
    and the value held that normalized value times the span plus the minimum, rounded once. Never
    the map's `to_preset` or `to_normalized`.
    """
    span = _round32(Fraction(maximum) - Fraction(minimum))
    normalized = _round32((Fraction(own) - Fraction(minimum)) / Fraction(span))
    return normalized, _round32(Fraction(normalized) * Fraction(span) + Fraction(minimum))
