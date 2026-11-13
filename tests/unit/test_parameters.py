"""A record's scales reach the plugin's own values exactly, and an inconsistent record is refused.

The records built here are from values measured on Vital 1.6.4 (the host spec's
`verification/discovery.md` and `verification/probes.txt`); the committed map, which the generator
wrote from the plugin (`verification/census-run.txt`), is held to the same properties at the end.
"""

import math
from fractions import Fraction
from typing import Literal

import pytest
from hypothesis import example, given
from hypothesis import strategies as st
from patchbay import Parameter, ParameterId, PatchbayValidationError, PresetKey, Quantity, Unit

from patchbay_vital.errors import ParameterRangeError, UnknownParameterError
from patchbay_vital.float32 import next_float32, round_to_float32, to_float32
from patchbay_vital.parameters import (
    PRESET_ONLY_KEYS,
    DisplayCurve,
    MappedParameter,
    NormalizedScale,
    ParameterMap,
    _span,
    displayed_ends,
    parameter_map,
)
from patchbay_vital.preset import SLOT_KEY

_UNIT_INTERVAL = st.floats(min_value=0.0, max_value=1.0, width=32)


def _record(  # noqa: PLR0913 - one argument per measured fact, each named where it is given
    key: str,
    host_id: str,
    *,
    scale: NormalizedScale,
    curve: DisplayCurve,
    preset_default: float,
    unit: Unit,
    host_unit: str = "",
    kind: Literal["continuous", "choice", "boolean"] = "continuous",
    choices: tuple[str, ...] | None = None,
) -> MappedParameter:
    """Build a record whose parameter is what its scales compute, as the generator writes one."""
    ends = sorted((curve.to_display(scale.minimum), curve.to_display(scale.maximum)))
    parameter = Parameter(
        id=ParameterId(key),
        label=host_id.replace("_", " ").title(),
        kind=kind,
        unit=unit,
        minimum=ends[0],
        maximum=ends[1],
        default=Quantity(value=curve.to_display(preset_default), unit=unit),
        choices=choices,
    )
    return MappedParameter(
        parameter=parameter,
        host_id=host_id,
        scale=scale,
        curve=curve,
        preset_default=preset_default,
        host_unit=host_unit,
    )


_ATTACK = _record(
    "env_1_attack",
    "envelope_1_attack",
    scale=NormalizedScale(kind="linear", minimum=0.0, maximum=2.378420114517212),
    curve=DisplayCurve(kind="quartic", multiply=1.0),
    preset_default=0.14949999749660492,
    unit=Unit.seconds,
    host_unit="secs",
)
_CUTOFF = _record(
    "filter_1_cutoff",
    "filter_1_cutoff",
    scale=NormalizedScale(kind="linear", minimum=8.0, maximum=136.0),
    curve=DisplayCurve(kind="linear", multiply=1.0, offset=-60.0),
    preset_default=60.0,
    unit=Unit.semitones,
    host_unit="semitones",
)
_LFO = _record(
    "lfo_1_frequency",
    "lfo_1_frequency",
    scale=NormalizedScale(kind="linear", minimum=-7.0, maximum=9.0),
    curve=DisplayCurve(kind="exponential_inverted", multiply=1.0),
    preset_default=1.0,
    unit=Unit.seconds,
    host_unit="secs",
)
_DECAY = _record(
    "reverb_decay_time",
    "reverb_decay_time",
    scale=NormalizedScale(kind="linear", minimum=-6.0, maximum=6.0),
    curve=DisplayCurve(kind="exponential", multiply=1.0),
    preset_default=0.0,
    unit=Unit.seconds,
    host_unit="secs",
)
_VOLUME = _record(
    "volume",
    "volume",
    scale=NormalizedScale(kind="linear", minimum=0.0, maximum=7399.4404296875),
    curve=DisplayCurve(kind="square_root", multiply=1.0, offset=-80.0),
    preset_default=5473.04052734375,
    unit=Unit.db,
    host_unit="dB",
)
_LEVEL = _record(
    "osc_1_level",
    "oscillator_1_level",
    scale=NormalizedScale(kind="linear", minimum=0.0, maximum=1.0),
    curve=DisplayCurve(kind="quadratic", multiply=1.0),
    preset_default=0.7071067690849304,
    unit=Unit.none,
)
_TEMPO = _record(
    "beats_per_minute",
    "beats_per_minute",
    scale=NormalizedScale(kind="linear", minimum=0.3333333432674408, maximum=5.0),
    curve=DisplayCurve(kind="linear", multiply=60.0),
    preset_default=2.0,
    unit=Unit.bpm,
)
_POLYPHONY = _record(
    "polyphony",
    "polyphony",
    scale=NormalizedScale(kind="indexed", minimum=1.0, maximum=32.0),
    curve=DisplayCurve(kind="linear", multiply=1.0),
    preset_default=8.0,
    unit=Unit.none,
    host_unit="voices",
)
_SWITCH = _record(
    "filter_1_on",
    "filter_1_switch",
    scale=NormalizedScale(kind="indexed", minimum=0.0, maximum=1.0),
    curve=DisplayCurve(kind="linear", multiply=1.0),
    preset_default=0.0,
    unit=Unit.none,
    kind="boolean",
)
_RECORDS = (_ATTACK, _CUTOFF, _LFO, _DECAY, _VOLUME, _LEVEL, _TEMPO, _POLYPHONY, _SWITCH)


@pytest.mark.parametrize(
    ("record", "normalized", "preset", "shown"),
    [
        # (normalized, the preset value the state held, the display text) from the probes.
        (_ATTACK, 0.0, 0.0, "0"),
        (_ATTACK, 0.06285685300827026, 0.14949999749660492, None),
        (_ATTACK, 0.5, 1.189210057258606, "2.00002"),
        (_ATTACK, 1.0, 2.378420114517212, "32.0003"),
        (_CUTOFF, 0.0, 8.0, "-52"),
        (_CUTOFF, 0.40625, 60.0, "0"),
        (_CUTOFF, 0.9, 123.19999694824219, "63.2"),
        (_CUTOFF, 1.0, 136.0, "76"),
        (_LFO, 0.0, -7.0, "128"),
        (_LFO, 0.5, 1.0, "0.5"),
        (_LFO, 1.0, 9.0, "0.00195312"),
        (_VOLUME, 0.0, 0.0, "-80"),
        (_VOLUME, 0.7396560311317444, 5473.04052734375, "-6.02"),
        (_VOLUME, 0.5, 3699.72021484375, "-19.1747"),
        (_VOLUME, 1.0, 7399.4404296875, "6.02"),
        (_LEVEL, 0.5, 0.5, "0.25"),
        (_TEMPO, 0.0, 0.3333333432674408, "20"),
        (_TEMPO, 0.10000000149011612, 0.800000011920929, None),  # a fused multiply-add's value
        (_TEMPO, 0.3571428656578064, 2.0, "120"),
        (_TEMPO, 1.0, 5.0, "300"),
        (_POLYPHONY, 0.0, 1.0, "1"),
        (_POLYPHONY, 0.22580644488334656, 8.0, None),
        (_POLYPHONY, 0.5, 17.0, "17"),
        (_POLYPHONY, 1.0, 32.0, "32"),
        (_SWITCH, 0.5, 1.0, None),
    ],
)
def test_a_measured_value_is_reached_exactly(
    record: MappedParameter, normalized: float, preset: float, shown: str | None
) -> None:
    """A normalized value gives the preset value the plugin held, and its display the text shown.

    The display is compared at the precision the plugin prints, six significant digits.
    """
    assert record.scale.to_preset(normalized) == preset
    if shown is not None:
        assert f"{record.to_display(preset):.6g}" == shown


@pytest.mark.parametrize("record", _RECORDS, ids=lambda record: record.id)
@given(normalized=_UNIT_INTERVAL)
@example(normalized=0.0)
@example(normalized=1.0)
@example(normalized=5.2383727406426375e-33)  # volume's preset 3.9e-29, absorbed by the offset
def test_a_value_the_parameter_holds_comes_back_exactly(
    record: MappedParameter, normalized: float
) -> None:
    """A displayed value goes to a preset value and back to the same display, every time.

    The preset value the parameter holds comes back through the normalized path; the preset value
    the display maps to is one the scale holds, which a set of the display holds again; and it is
    the held one, but where the display does not name it (`_unnamed_by_its_display`): there
    neighbouring presets share the display, which cannot say which of them was held. The
    normalized value need not come back, many landing on one float32 preset value. The pinned
    values of `tests/data/pinned-values.txt` run in
    `test_every_pinned_value_comes_back_on_every_record`, not as `@example`s here.
    """
    _assert_comes_back(record, normalized)


def _assert_comes_back(record: MappedParameter, normalized: float) -> None:
    """Assert a value's display, held preset and preset come back, and what a set of it holds.

    Every check is exact on every value. The one excuse, `_unnamed_by_its_display`, is consulted
    only where the preset the display maps to is not the held one, so it excuses nothing that
    holds. On `volume` every float32 normalized value that consults it is counted, with the
    shipped methods and this module's own predicate, by the revision after PR 14's sixth review
    (`verification/floor-pass.txt`): on each, `back` is what a set of the display's float32
    holds, the one value the excuse allows. No value of the other 68 groups consults it, by the
    fourth review's reproduction over every float32 normalized value (`verification/sweep.txt`),
    checked against the shipped methods on 200,010 values a group.
    """
    preset = record.scale.to_preset(normalized)
    display = record.from_normalized(normalized)
    back = record.to_preset(display)
    assert record.to_display(back) == display
    assert record.scale.to_preset(record.scale.to_normalized(preset)) == preset
    assert record.scale.to_preset(record.to_normalized(display)) == back
    assert back == preset or _unnamed_by_its_display(record, display, preset, back)


def _unnamed_by_its_display(
    record: MappedParameter, display: float, preset: float, back: float
) -> bool:
    """Say whether a display does not name its held preset, and `back` is what a set of it holds.

    The display names a preset where the curve's own float32 for it, `curve.to_preset`, is that
    preset: then nothing is excused. Where it is not, `back` must be what a set of that float32
    holds, the scale's value at its normalized value, worked out here from the scale's and the
    curve's primitives, never from `to_preset`, so a wrong rule in the map cannot agree with itself
    (`_what_a_set_holds`). The display, shown by `back` as well, is checked beside it in
    `_assert_comes_back`. A value of the record's own scale and curve, never its name.

    The float32 on that float32's other side, which `to_preset` takes where what a set holds does
    not show the display, is not excused: the floor pass excuses every `volume` value it counts
    with what a set holds and none with the other side, so a record that needed the other side
    would fail the property, not be excused by it. It replaces `_shares_its_display`, which asked
    only whether the float32 beside the preset toward `back` shows its display: on a monotone
    curve that holds wherever `back` shows it, so it excused any preset that showed the display
    (the sixth review's finding 1).
    """
    own, held, _ = _what_a_set_holds(record, display)
    return own != preset and back == held


_SHARED = 1.4252698059502449e-24
"""A `volume` value in binade -80, far below its floor, found by a seeded search (the sixth
review's shape.md): its display's own float32 is another held preset, about 1,200 float32s from
it, and the held float32s around that preset show the display too."""


def test_a_display_excuses_only_what_a_set_of_its_own_float32_holds() -> None:
    """Where a display does not name its preset, only what a set of it holds is excused.

    At `_SHARED` the display maps to its own float32, held and another preset: excused. A held
    float32 three steps from it shows the display as well, but no set of the display holds it, so
    it is refused (the sixth review's finding 1, its second scenario), and so is the held float32
    above it, on its other side, which shows the display too: the floor pass excuses no value with
    it. At the held float32's own value the display names it, so the preset `_SHARED` held, which
    shows the same display, is refused (the first scenario). At 2 ** -43 the curve's float32 is
    unheld and what a set of it holds does not show the display, so the map takes the float32 on
    its other side, 2 ** -43 itself, and the excuse is not asked; the float32 above 2 ** -43 is the
    first a display names among its neighbours.
    """
    scale = _VOLUME.scale
    preset = scale.to_preset(_SHARED)
    display = _VOLUME.to_display(preset)
    own, held, other = _what_a_set_holds(_VOLUME, display)
    back = _VOLUME.to_preset(display)
    assert back == own == held != preset
    assert scale.holds(own)
    assert _unnamed_by_its_display(_VOLUME, display, preset, back)
    far = next_float32(next_float32(next_float32(own, 0.0), 0.0), 0.0)
    assert scale.holds(far)
    assert _VOLUME.to_display(far) == display
    assert not _unnamed_by_its_display(_VOLUME, display, preset, far)
    above = next_float32(own, 1.0)
    assert above == other
    assert scale.holds(above)
    assert _VOLUME.to_display(above) == display
    assert not _unnamed_by_its_display(_VOLUME, display, preset, above)
    assert not _unnamed_by_its_display(_VOLUME, display, own, preset)
    last = 2.0**-43
    display = _VOLUME.to_display(last)
    own, held, other = _what_a_set_holds(_VOLUME, display)
    assert own != last
    assert not scale.holds(own)
    assert _VOLUME.to_display(held) != display
    assert _VOLUME.to_preset(display) == other == last
    first = next_float32(last, 1.0)
    assert _VOLUME.to_preset(_VOLUME.to_display(first)) == first
    assert not _unnamed_by_its_display(_VOLUME, _VOLUME.to_display(first), first, last)


_PINNED = ("tests", "data", "pinned-values.txt")
_PINNED_SETS = ("volume_floor", "powers_of_two")


def _pinned(pytestconfig: pytest.Config) -> dict[str, tuple[float, ...]]:
    """Read `tests/data/pinned-values.txt`, each set's values in the file's order.

    The one place the pinned values are written, read from pytest's root as every repository file
    is (`base/testing/tests.md`); `test_vital_plugin.py` reads it with a reader of its own. A line
    that is not `<set> <float32> <name>`, of a set named here, fails the test reading it, naming
    the file and the line; a missing file fails it naming the path.
    """
    path = pytestconfig.rootpath.joinpath(*_PINNED)
    found: dict[str, list[float]] = {name: [] for name in _PINNED_SETS}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("#"):
            continue
        name, _, rest = line.partition(" ")
        text, _, label = rest.partition(" ")
        try:
            value = float(text)
        except ValueError:
            value = math.nan
        if name not in found or not label or to_float32(value) != value:
            pytest.fail(f"{path.name}:{number} is not '<set> <float32> <name>': {line!r}")
        found[name].append(value)
    return {name: tuple(values) for name, values in found.items()}


def test_the_pinned_values_file_holds_two_named_sets(pytestconfig: pytest.Config) -> None:
    """The file holds `volume`'s four floor values and the envelope's three, each in `[0, 1]`."""
    pinned = _pinned(pytestconfig)
    assert {name: len(values) for name, values in pinned.items()} == {
        "volume_floor": 4,
        "powers_of_two": 3,
    }
    assert all(0.0 <= value <= 1.0 for values in pinned.values() for value in values)


def test_every_pinned_value_comes_back_on_every_record(pytestconfig: pytest.Config) -> None:
    """Every pinned value holds the property on every hand-built record, on every run.

    These were the property's `@example`s. A decorator runs at import, before pytest's root is
    known, and a repository file is read from that root alone (`base/testing/tests.md`), so the
    file's values run here instead, on every record as an `@example` runs: a regression that only
    they reach fails this test by name whatever Hypothesis draws (MC in the sixth review's
    `verification/mutation.txt`, the seeded regression of the revision after PR 14's review).
    """
    for values in _pinned(pytestconfig).values():
        for normalized in values:
            for record in _RECORDS:
                _assert_comes_back(record, normalized)


def test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset(
    pytestconfig: pytest.Config,
) -> None:
    """Where the curve's own float32 for a display is one the scale skips, a held one is taken.

    At each pinned floor value the float32 nearest the curve's inverse is not one the scale holds:
    before issue #15 the map gave it, and a set of the display held a neighbour, shown at the
    display or a double from it, as Vital holds it. The map now takes a held float32 next to it
    that shows the display, so the value comes back as every value does.
    """
    record = parameter_map().find(ParameterId("volume"))
    for normalized in _pinned(pytestconfig)["volume_floor"]:
        _assert_comes_back(record, normalized)
        display = record.from_normalized(normalized)
        assert not record.scale.holds(record.curve.to_preset(display)), normalized


def _what_a_set_holds(record: MappedParameter, display: float) -> tuple[float, float, float]:
    """Return the curve's float32 for a display, what a set of it holds, and its other side."""
    own = record.curve.to_preset(display)
    held = record.scale.to_preset(record.scale.to_normalized(own))
    return own, held, next_float32(own, math.copysign(math.inf, own - held))


_FLOOR_PRESETS = (
    4.3339647768216114e-16,  # issue #13's value: what a set of the curve's float32 holds
    2.567198129153469e-14,  # here and below, the float32 on the curve's float32's other side
    1.0653287198800557e-13,
    1.1368683772161603e-13,
)
"""The preset `to_preset` gives at each `volume_floor` value of `tests/data/pinned-values.txt`, in
the file's order: the first by the rule's first branch, the other three by its second."""


def _floor_presets(pytestconfig: pytest.Config) -> list[tuple[float, float]]:
    """Pair each pinned floor value with its preset here, failing if the two differ in number."""
    return list(zip(_pinned(pytestconfig)["volume_floor"], _FLOOR_PRESETS, strict=True))


def test_a_display_takes_what_a_set_of_the_curve_s_float32_holds(
    pytestconfig: pytest.Config,
) -> None:
    """At issue #13's value both float32s next to the curve's own show the display; Vital's wins.

    The curve's float32 is one the scale skips. A set of it holds the float32 below, Vital's own
    rounding of it, which shows the display; the one above is held and shows it too. The map takes
    what the set holds (the first branch of `to_preset`), so the order of the branches decides
    here, and a set of the display holds what a set of it held before issue #15.
    """
    record = parameter_map().find(ParameterId("volume"))
    for normalized, preset in _floor_presets(pytestconfig)[:1]:
        display = record.from_normalized(normalized)
        _, held, other = _what_a_set_holds(record, display)
        assert record.to_preset(display) == held == preset, normalized
        assert record.scale.holds(other), normalized
        assert record.to_display(other) == display, normalized


def test_else_a_display_takes_the_float32_on_the_other_side(pytestconfig: pytest.Config) -> None:
    """Where what a set holds shows another display, the float32 on the curve's other side is taken.

    At the other three pinned floor values a set of the curve's float32 holds a float32 next to it
    whose display is a double from the one given, as a set of the display held before issue #15.
    The float32 on the curve's float32's other side is held and shows the display (the second
    branch of `to_preset`).
    """
    record = parameter_map().find(ParameterId("volume"))
    for normalized, preset in _floor_presets(pytestconfig)[1:]:
        display = record.from_normalized(normalized)
        _, held, other = _what_a_set_holds(record, display)
        assert record.to_display(held) != display, normalized
        assert record.to_preset(display) == other == preset, normalized


def _nearest_quotient(scale: NormalizedScale, preset: float) -> float:
    """Return the float32 nearest a preset's exact quotient, `(preset - minimum) / span`.

    Worked out here from `Fraction` primitives, never imported from `parameters.py`, whose
    `_landing` takes the same quotient as its first step: the tests compute the value they expect
    on their own, so the code cannot agree with its own mistake (the sixth review's finding 8, and
    MD in its `verification/mutation.txt`).
    """
    return round_to_float32((Fraction(preset) - Fraction(scale.minimum)) / Fraction(scale.span))


@pytest.mark.parametrize("name", ["env_1_delay", "env_3_hold"])
def test_a_held_power_of_two_comes_back_through_the_normalized_path(
    pytestconfig: pytest.Config, name: str
) -> None:
    """A held power of two's normalized value is the one that lands on it, not the one below.

    On the 12 `env_N_delay` and `env_N_hold` records, at 126 powers of two each, the float32
    nearest `preset / span` multiplies back short of the power, where the float32 spacing halves,
    and lands one float32 below it: before issue #15 the map gave it, and a set of 1.0 s held
    0.9999999403953552 on Vital. The map now steps to the float32 that lands on the power, here
    each pinned value itself.
    """
    record = parameter_map().find(ParameterId(name))
    scale = record.scale
    for normalized in _pinned(pytestconfig)["powers_of_two"]:
        _assert_comes_back(record, normalized)
        preset = scale.to_preset(normalized)
        assert math.frexp(preset)[0] == 0.5, normalized  # noqa: PLR2004 - a power's significand
        nearest = _nearest_quotient(scale, preset)
        assert scale.to_preset(nearest) == next_float32(preset, 0.0), normalized
        assert scale.to_normalized(preset) == normalized, normalized


def test_a_scale_holds_its_values_and_none_past_its_ends() -> None:
    """A value a normalized value in [0, 1] lands on is held; a float32 past either end is not.

    Some normalized value past 1 or below 0 lands on the float32 just past each end of `[0, 1]`,
    but the host sets no such value, so the plugin cannot hold it.
    """
    scale = _LEVEL.scale
    assert (scale.minimum, scale.maximum) == (0.0, 1.0)
    assert all(scale.holds(value) for value in (0.0, 0.5, 1.0))
    for past in (next_float32(1.0, 2.0), next_float32(0.0, -1.0)):
        assert scale.to_preset(scale.to_normalized(past)) == past, past
        assert not scale.holds(past), past


def test_an_arbitrary_display_keeps_the_curve_s_float32() -> None:
    """Issue #16, characterized: an arbitrary display keeps the curve's unheld float32.

    `beats_per_minute` at 216.85141355537831 is a display no preset shows exactly: the float32
    nearest the curve's inverse is not one the scale holds, and neither what a set of it holds nor
    the float32 on its other side shows the display, so `to_preset` keeps it (the third branch).
    Issue #16 has the map take what a set of it holds instead, and reverses this test on purpose;
    whether that or the nearer held neighbour is right stays issue #8's finding 1. So the test
    asserts only what #16 would change: the value kept at this display, the curve's own float32,
    unheld.
    """
    display = 216.85141355537831
    back = _TEMPO.to_preset(display)
    assert back == _TEMPO.curve.to_preset(display)
    assert not _TEMPO.scale.holds(back)


def test_the_step_toward_a_preset_stays_where_the_host_can_set_it() -> None:
    """Where only a normalized value past 1 lands on a preset, `to_normalized` keeps the nearest.

    On a span of 2 ** 24 from -1, the nearest quotient for the maximum, 1, lands one below it, and
    the float32 above 1, which the host cannot set, lands on it: so the maximum is not one the
    scale holds, and its normalized value stays 1.
    """
    top = 2.0**24
    scale = NormalizedScale(kind="linear", minimum=-1.0, maximum=top)
    assert scale.span == top
    assert scale.to_preset(1.0) == top - 1
    assert scale.to_preset(next_float32(1.0, 2.0)) == top
    assert scale.to_normalized(top) == 1.0
    assert not scale.holds(top)


def test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it() -> None:
    """Where the nearest quotient lands on a preset, `to_normalized` gives it and steps nowhere.

    Near the top of `beats_per_minute`'s scale two float32 normalized values land on one preset.
    At the first preset here the float32 above the nearest quotient lands on it too, and at the
    second the one below does: the nearest is the value either way, as before issue #15, so the
    fix changes no normalized value that already landed.
    """
    scale = _TEMPO.scale
    for preset, beside in ((4.999998569488525, math.inf), (4.999999523162842, -math.inf)):
        nearest = _nearest_quotient(scale, preset)
        assert scale.to_preset(nearest) == preset
        assert scale.to_preset(next_float32(nearest, beside)) == preset
        assert scale.to_normalized(preset) == nearest


def test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken() -> None:
    """A float32 only a normalized value above 1 lands on is no preset, though it shows the display.

    A record made up to reach `to_preset`'s second branch past the scale: its maximum, 1, is not
    held, a set of it landing one float32 below, which shows another display; the float32 above
    1 shows the maximum's display, and the normalized value above 1 lands on it, which the host
    cannot set. So the scale does not hold it and the display keeps the curve's float32, the
    maximum (the third branch), never a preset past the scale.
    """
    top, display = 1.0, 2.0**30
    record = _record(
        "made_up",
        "made_up",
        scale=NormalizedScale(kind="linear", minimum=-0.89999920129776, maximum=top),
        curve=DisplayCurve(kind="linear", multiply=0.9999999478459358, offset=1073741823.0),
        preset_default=top,
        unit=Unit.none,
    )
    scale = record.scale
    own, held, other = _what_a_set_holds(record, display)
    assert (own, held, other) == (top, next_float32(top, 0.0), next_float32(top, 2.0))
    assert record.to_display(held) != display
    assert record.to_display(other) == display
    past = next_float32(1.0, 2.0)
    assert (scale.to_normalized(other), scale.to_preset(past)) == (past, other)
    assert not scale.holds(other)
    assert record.to_preset(display) == top
    assert record.to_normalized(display) == 1.0


@pytest.mark.parametrize("record", _RECORDS, ids=lambda record: record.id)
def test_the_bounds_are_the_scales_ends(record: MappedParameter) -> None:
    """A parameter's bounds are its preset bounds displayed, and reach them back exactly."""
    parameter = record.parameter
    ends = {record.scale.minimum, record.scale.maximum}
    assert {record.to_preset(parameter.minimum), record.to_preset(parameter.maximum)} == ends
    assert record.from_normalized(0.0) in {parameter.minimum, parameter.maximum}
    assert record.from_normalized(1.0) in {parameter.minimum, parameter.maximum}


def test_a_decreasing_curve_puts_the_bounds_in_order() -> None:
    """An LFO's period falls as its preset value rises, and its parameter still runs up."""
    assert (_LFO.parameter.minimum, _LFO.parameter.maximum) == (0.001953125, 128.0)
    assert _LFO.from_normalized(0.0) == _LFO.parameter.maximum


def test_a_value_outside_the_bounds_is_the_package_s_range_error() -> None:
    """Past either bound, by display or by normalized value, is refused naming what it was."""
    for value in (_CUTOFF.parameter.minimum - 1.0, _CUTOFF.parameter.maximum + 0.5):
        with pytest.raises(ParameterRangeError) as caught:
            _CUTOFF.to_preset(value)
        assert (caught.value.parameter_id, caught.value.given) == ("filter_1_cutoff", value)
    with pytest.raises(ParameterRangeError) as normalized:
        _CUTOFF.from_normalized(1.5)
    assert (normalized.value.minimum, normalized.value.maximum) == (0.0, 1.0)


def test_a_record_holds_together_in_float32_so_a_libm_an_ulp_apart_still_reads_it() -> None:
    """A bound a double ulp off the curve's value, as another libm's pow may give, validates.

    The committed bounds are this machine's libm's; another's, an ulp apart, still reaches the
    scale's end in float32, and the parameter's own bound is still taken by `to_preset`.
    """
    ulp = _CUTOFF.parameter.model_copy(update={"maximum": math.nextafter(76.0, 100.0)})
    record = MappedParameter.model_validate(_changed(_CUTOFF, parameter=ulp.model_dump()))
    assert record.to_preset(record.parameter.maximum) == 136.0  # noqa: PLR2004 - the scale's end
    assert record.to_preset(76.0) == 136.0  # noqa: PLR2004 - this libm's own display of it


_OVERSAMPLING = _record(
    "oversampling",
    "oversampling",
    scale=NormalizedScale(kind="indexed", minimum=0.0, maximum=3.0),
    curve=DisplayCurve(kind="exponential", multiply=1.0),
    preset_default=1.0,
    unit=Unit.none,
    host_unit="x",
)


def test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step() -> None:
    """Oversampling shows 1, 2, 4 and 8; a display of 4.5 is held as 2, the plugin's step."""
    assert _OVERSAMPLING.to_preset(4.5) == 2.0  # noqa: PLR2004 - log2(4.5) is 2.17, rounded
    assert _OVERSAMPLING.scale.to_preset(_OVERSAMPLING.to_normalized(4.5)) == 2.0  # noqa: PLR2004
    assert _POLYPHONY.to_preset(8.4) == 8.0  # noqa: PLR2004 - the nearest voice count


def test_a_choice_or_a_boolean_takes_a_whole_index_and_nothing_else() -> None:
    """Core's rule for them: a value that is no index is out of range, by display or normalized."""
    choice = _record(
        "filter_1_model",
        "filter_1_model",
        scale=NormalizedScale(kind="indexed", minimum=0.0, maximum=2.0),
        curve=DisplayCurve(kind="linear", multiply=1.0),
        preset_default=0.0,
        unit=Unit.none,
        kind="choice",
        choices=("Analog", "Dirty", "Ladder"),
    )
    assert choice.to_preset(1.0) == 1.0
    for record, value in ((choice, 1.5), (_SWITCH, 0.5)):
        with pytest.raises(ParameterRangeError) as caught:
            record.to_preset(value)
        assert caught.value.given == value
        with pytest.raises(ParameterRangeError):
            record.to_normalized(value)


def test_a_scale_s_span_is_kept_by_its_bounds_so_a_copy_has_its_own() -> None:
    """The float32 difference is computed once per pair of bounds, never stored on the scale."""
    scale = NormalizedScale(kind="linear", minimum=-7.0, maximum=9.0)
    assert scale.span == 16.0  # noqa: PLR2004 - 9 less -7
    assert "span" not in vars(scale)
    assert scale.model_copy(update={"maximum": 1.0}).span == 8.0  # noqa: PLR2004 - 1 less -7
    hits = _span.cache_info().hits
    assert scale.span == 16.0  # noqa: PLR2004
    assert _span.cache_info().hits == hits + 1


@pytest.mark.parametrize(
    ("minimum", "maximum", "normalized", "preset"),
    [(0.0, 1.0, 0.5, 1.0), (0.0, 2.0, 0.25, 1.0), (-1.0, 0.0, 0.5, -1.0)],
)
def test_a_half_on_the_grid_goes_away_from_zero(
    minimum: float, maximum: float, normalized: float, preset: float
) -> None:
    """The census's grid lands on a half, 0.5 on every boolean; the plugin takes it away from zero.

    `round` would take 0.5 to 0 and fit no boolean; the committed map fits every grid point.
    """
    scale = NormalizedScale(kind="indexed", minimum=minimum, maximum=maximum)
    assert scale.to_preset(normalized) == preset
    assert round(0.5) == 0


def test_a_record_s_displayed_ends_are_the_scale_s_through_its_curve_in_order() -> None:
    """One place computes the ends `to_preset` bounds by, sorted whatever the curve's direction."""
    falling = DisplayCurve(kind="linear", multiply=-2.0, offset=1.0)
    scale = NormalizedScale(kind="linear", minimum=0.0, maximum=1.0)
    assert displayed_ends(falling, scale) == (-1.0, 1.0)
    assert displayed_ends(falling, scale) is displayed_ends(falling, scale)


def test_a_preset_value_beyond_the_host_s_range_still_displays() -> None:
    """Presets hold values past the host's range (flanger_dry_wet 0.7072 against 0..0.5)."""
    assert _LEVEL.to_display(2.0) == 4.0  # noqa: PLR2004 - the quadratic's value, past its range


def _changed(record: MappedParameter, **fields: object) -> dict[str, object]:
    """Return a record's fields as data with some replaced, to build it again."""
    return {**record.model_dump(), **fields}


def test_a_record_whose_parameter_is_not_its_scales_is_refused() -> None:
    """Bounds and default reach the scale's ends and the preset default, or the record is wrong."""
    wider = _CUTOFF.parameter.model_copy(update={"maximum": 77.0})
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(_changed(_CUTOFF, parameter=wider.model_dump()))
    step = _CUTOFF.parameter.model_copy(
        update={"maximum": 76.0 + 2.0**-16}
    )  # a float32 step at 136
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(_changed(_CUTOFF, parameter=step.model_dump()))
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(_changed(_CUTOFF, preset_default=61.0))
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(_changed(_CUTOFF, preset_default=200.0))


@pytest.mark.parametrize(
    "scale",
    [
        {"kind": "linear", "minimum": 0.1, "maximum": 1.0},  # 0.1 is no float32
        {"kind": "linear", "minimum": 1.0, "maximum": 1.0},
        {"kind": "linear", "minimum": 2.0, "maximum": 1.0},
        {"kind": "indexed", "minimum": 0.0, "maximum": 1.5},
    ],
)
def test_a_scale_that_does_not_hold_together_is_refused(scale: dict[str, object]) -> None:
    """A scale's bounds are float32 values in order, whole numbers for an indexed one."""
    with pytest.raises(PatchbayValidationError):
        NormalizedScale.model_validate(scale)


def test_a_curve_multiplies_by_something() -> None:
    """A zero multiply would display every value as its offset."""
    with pytest.raises(PatchbayValidationError):
        DisplayCurve(kind="linear", multiply=0.0)


def test_a_choice_or_boolean_is_an_index_shown_as_it_is() -> None:
    """A choice runs from index 0 on an indexed scale with a plain curve."""
    choice = _record(
        "filter_1_model",
        "filter_1_model",
        scale=NormalizedScale(kind="indexed", minimum=0.0, maximum=2.0),
        curve=DisplayCurve(kind="linear", multiply=1.0),
        preset_default=0.0,
        unit=Unit.none,
        kind="choice",
        choices=("Analog", "Dirty", "Ladder"),
    )
    assert choice.from_normalized(1.0) == 2.0  # noqa: PLR2004 - the last of three indices
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(
            _changed(choice, scale={**choice.scale.model_dump(), "kind": "linear"})
        )
    with pytest.raises(PatchbayValidationError):
        MappedParameter.model_validate(_changed(choice, choice_labels=("Analog",)))
    labelled = MappedParameter.model_validate(_changed(choice, choice_labels=("", "", "Ladder")))
    assert labelled.choice_labels == ("", "", "Ladder")


def _map(*records: MappedParameter) -> ParameterMap:
    return ParameterMap(
        instrument="Vital",
        vital_version="1.6.4",
        host="pedalboard 0.9.26",
        machine="arm64",
        parameters=records,
    )


def test_a_map_finds_a_record_by_its_preset_key() -> None:
    """An id is the preset key; one the map lacks is the package's error, naming the instrument."""
    found = _map(_ATTACK, _CUTOFF, _VOLUME)
    assert found.find(ParameterId("filter_1_cutoff")) is found.parameters[1]
    assert found.parameters[0].preset_key == PresetKey("env_1_attack")
    with pytest.raises(UnknownParameterError) as caught:
        found.find(ParameterId("filter_1_cutofff"))
    assert (caught.value.parameter_id, caught.value.instrument) == ("filter_1_cutofff", "Vital")


def test_a_map_holds_its_records_sorted_and_each_once() -> None:
    """Sorted by id, so a lookup can bisect; no id and no host id twice."""
    with pytest.raises(PatchbayValidationError):
        _map(_CUTOFF, _ATTACK)
    with pytest.raises(PatchbayValidationError):
        _map(_ATTACK, _ATTACK)
    twin = MappedParameter.model_validate(_changed(_CUTOFF, host_id=_ATTACK.host_id))
    with pytest.raises(PatchbayValidationError):
        _map(_ATTACK, twin)


def test_the_format_s_keys_are_the_map_s_but_the_slots_with_the_preset_only_ones() -> None:
    """`settings_keys.txt` is derived: the map's ids, no per-slot key, and `chorus_damping`."""
    slot = MappedParameter.model_validate(
        _changed(
            _LEVEL,
            parameter={**_LEVEL.parameter.model_dump(), "id": "modulation_1_amount"},
            host_id="modulation_1_amount",
        )
    )
    keys = _map(_ATTACK, _CUTOFF, slot, _LEVEL).settings_keys()
    assert keys == ("chorus_damping", "env_1_attack", "filter_1_cutoff", "osc_1_level")
    assert {"chorus_damping"} == PRESET_ONLY_KEYS


def test_a_map_comes_back_from_its_json() -> None:
    """The committed form is the model's JSON, so it reads back as the same map."""
    original = _map(*sorted(_RECORDS, key=lambda record: record.id))
    assert ParameterMap.model_validate_json(original.model_dump_json()) == original


# The committed map, as `verification/census-run.txt` counts it.
_HOSTED, _SLOTS = 903, 448
_KINDS = {"continuous": 581, "boolean": 243, "choice": 79}


def test_the_committed_map_holds_every_hosted_parameter() -> None:
    """Every parameter Vital 1.6.4 exposes, the 448 per-slot ones among them, by its preset key."""
    committed = parameter_map()
    assert (committed.instrument, committed.vital_version) == ("Vital", "1.6.4")
    assert (committed.host, committed.machine) == ("pedalboard 0.9.26", "arm64")
    assert len(committed.parameters) == _HOSTED
    assert sum(bool(SLOT_KEY.fullmatch(record.id)) for record in committed.parameters) == _SLOTS
    kinds = dict.fromkeys(_KINDS, 0)
    for record in committed.parameters:
        kinds[record.parameter.kind] += 1
    assert kinds == _KINDS


def test_the_format_s_key_list_is_derived_from_the_committed_map(
    pytestconfig: pytest.Config,
) -> None:
    """`settings_keys.txt` is the map's ids but the per-slot ones, and the preset-only keys."""
    path = pytestconfig.rootpath / "src" / "patchbay_vital" / "settings_keys.txt"
    assert tuple(path.read_text(encoding="utf-8").splitlines()) == parameter_map().settings_keys()


@given(index=st.integers(min_value=0, max_value=_HOSTED - 1), normalized=_UNIT_INTERVAL)
@example(index=0, normalized=0.0)
@example(index=_HOSTED - 1, normalized=1.0)
def test_every_committed_record_comes_back_exactly(index: int, normalized: float) -> None:
    """The map's records hold the property its hand-built ones do, whichever is drawn."""
    _assert_comes_back(parameter_map().parameters[index], normalized)


def test_the_committed_map_tells_its_choices_apart() -> None:
    """The six lists with empty or repeated names are told apart; the plugin's names kept beside."""
    labelled = [record for record in parameter_map().parameters if record.choice_labels is not None]
    assert sorted(record.id for record in labelled) == [
        "filter_1_style",
        "filter_2_style",
        "filter_fx_style",
        "osc_1_distortion_type",
        "osc_2_distortion_type",
        "osc_3_distortion_type",
    ]
    style = parameter_map().find(ParameterId("filter_1_style"))
    assert style.parameter.choices is not None
    assert style.parameter.choices[4:6] == ("B/P/N", "option_5")
    assert style.choice_labels is not None
    assert style.choice_labels[5] == ""
