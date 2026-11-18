"""What the unit tests share: strategies, an empty slot, a preset, what a set holds, a watch.

What a set holds is worked out from primitives, for the instrument's tests and the patch's alike.
The stand-in watch is what the host's and the instrument's tests put in place of the one that
answers Vital's alert, so they run alike on macOS and where there is no AppKit.
A plain module and not a conftest: a property test takes these at its decorator or under `@given`,
where a function-scoped fixture fails hypothesis's health check, and the gate's negative test q
writes a conftest of its own at tests/unit/conftest.py.
"""

import struct
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from fractions import Fraction

from hypothesis import strategies as st

from patchbay_vital.errors import PluginStateError
from patchbay_vital.host import Alert
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


class StandInWatch:
    """A watch in place of AppKit's: it says when it is in place, and notes a fake's alerts.

    A fake plugin raises an alert by calling `alert`, or `unreadable_alert` for one whose words
    the watch could not read. With no watch in place that is its caller waiting for ever, so it
    fails the test there, by name. `entered` counts the writes watched. Like the real watch, it
    refuses to be entered while it is in place, and `may_write_here` follows `main_thread_only`.
    """

    def __init__(self) -> None:
        """Start out of place, on a platform where a load is the main thread's."""
        self.main_thread_only = True
        self.in_place = False
        self.entered = 0
        self._alerts: list[Alert] | None = None

    def may_write_here(self) -> bool:
        """Whether a state may be written from this thread: any, unless `main_thread_only`."""
        return not self.main_thread_only or threading.current_thread() is threading.main_thread()

    @contextmanager
    def answered(self) -> Iterator[list[Alert]]:
        """Be in place for the length of the block; yield the list its alerts are noted in."""
        if self._alerts is not None:
            msg = "the alert watch is already in place: a state write was begun inside another"
            raise PluginStateError(msg)
        alerts: list[Alert] = []
        self._alerts, self.in_place = alerts, True
        self.entered += 1
        try:
            yield alerts
        finally:
            self._alerts, self.in_place = None, False

    def alert(self, message: str, informative: str) -> None:
        """Raise an alert, as Vital does for a text it cannot read."""
        assert self._alerts is not None, (
            "an alert with no watch in place: its caller waits for ever"
        )
        self._alerts.append(Alert(message, informative))

    def unreadable_alert(self, unread: BaseException) -> None:
        """Raise an alert whose words the watch could not read, what the read raised kept."""
        assert self._alerts is not None, (
            "an alert with no watch in place: its caller waits for ever"
        )
        self._alerts.append(Alert("", "", unread))


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
