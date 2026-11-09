"""What the unit tests of a preset share: strategies, an empty slot and a preset to start from.

A plain module and not a conftest: a property test takes these at its decorator or under `@given`,
where a function-scoped fixture fails hypothesis's health check, and the gate's negative test q
writes a conftest of its own at tests/unit/conftest.py.
"""

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
