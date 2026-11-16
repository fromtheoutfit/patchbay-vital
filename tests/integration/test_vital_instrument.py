"""The instrument against the installed Vital: core's contract, and what the model holds it to.

These run where Vital is installed at the host's `DEFAULT_PATH` and skip by name elsewhere, CI
among the places, and where the committed map was measured on another machine. The module loads
Vital once; each test gets a new bus and a new `VitalInstrument` over it, whose construction loads
the start preset, twice, so every test starts on the same model and the same plugin state.

The plugin's own floats are read through the diagnostic read, `instrument.host.state()`, with the
host's `_floats`, to hold the plugin to the model; nothing reads them as the instrument's state.
Every audio assertion is a measure against a named tolerance whose comment gives the probe its
number came from (`verification/probes.txt` and `verification/probes-2.txt` of the instrument
spec, `agent-os/specs/2026-11-15-1448-the-instrument/`); none compares samples. An expected value
is written out or worked out from primitives, never by the map's `to_preset` or the instrument.

No test here may hang the gate. Vital answers a text it cannot read with a modal alert and never
returns to its caller (issue #20), so every load a test sends passes the instrument's guard first,
and the loads that block live only in that spec's transcripts, each run in a process of its own.
"""

import json
import math
import platform
import struct
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from patchbay import (
    EventBus,
    Instrument,
    Note,
    ParameterChanged,
    ParameterId,
    Patch,
    Pattern,
    PresetKey,
    Quantity,
    RenderCompleted,
    RenderRequest,
    Unit,
)
from patchbay.testing import CONTRACT_TESTS, RecordingSubscriber
from patchbay.testing.contract_tests import ContractTest

from patchbay_vital import dumps, loads
from patchbay_vital.errors import ParameterRangeError, PatchRefusedError, RenderRefusedError
from patchbay_vital.format import split_modulations
from patchbay_vital.host import DEFAULT_PATH, VitalHost, _floats
from patchbay_vital.instrument import (
    FULL_SCALE,
    LOADS,
    MAX_SAMPLES,
    VitalInstrument,
)
from patchbay_vital.parameters import parameter_map
from patchbay_vital.patch import check_loadable, patch_of
from patchbay_vital.preset import VitalPreset
from patchbay_vital.start import start_preset

pytestmark = pytest.mark.integration

_RATE = 48000
_PARAMETERS = 903
_BOUNDS = 2 * _PARAMETERS
_OFF_GRID_DEFAULTS = 22
_PRESETS = Path.home() / "Music" / "Vital"
_MANIFEST = Path("tests") / "data" / "factory-manifest.txt"
_UPGRADED = Path("tests") / "data" / "upgraded-floats.txt"
_MANIFEST_LENGTH = 75
_UPGRADED_FLOATS, _UPGRADED_PRESETS = 46, 11  # probes-2.txt, section 9c
_PLUCKED = "Factory/Presets/Plucked String.vital"

_OPENING_ENDS = 7200  # samples, 0.15 s: the start preset's opening is over (probes.txt: by 4,889)
_QUIET = 1e-6  # peak where nothing sounds (probes.txt, sections 1 and 8: exactly 0)
_TRANSIENT = 0.05  # peak of a render of no notes on the start preset (probes.txt: 0.0165 to 0.021)
_OPENING_SOUND = 0.1  # peak of a render of no notes on Plucked String (probes.txt: 0.21 to 0.37)
_CENTROID_RATIO = 3.6  # high cutoff's centroid over low's (probes-2.txt: 7.331 least, 40 renders)
_AUDIBLE = 0.007  # RMS of a held note (probes-2.txt: 0.014134 least of 40 renders; 0 with no MIDI)
_AH_EH = "Factory/Presets/Ah Eh Ee Oh.vital"  # tests/data/upgraded-floats.txt: stack style 9 as 10
_OOLACILE = "Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass.vital"
_MENDED = 42  # of the 46 upgraded floats: a set of the value shown puts Vital on the model's
_REFUSED = {  # flanger_center's file value shows a display outside its bounds, 8 to 136
    ("Factory/Presets/Touch Tone.vital", "flanger_center"),
    ("Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak.vital", "flanger_center"),
    (_OOLACILE, "flanger_center"),
}
_KEPT = {  # a float no set lands on: the model's, then the one Vital goes on holding
    (_OOLACILE, "modulation_10_amount"): (0.19999998807907104, 0.07499999552965164),
}
"""What a set of the value `get` shows does to each float Vital upgrades, counted on Vital 1.6.4
through pedalboard 0.9.26 on arm64 (`verification/upgraded-set-count.txt` of the revision after
PR 23's second review, `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/`)."""
_OWN_LENGTH = 0.5  # a note's level where another of its pitch ended, over its level alone: 1.00
# for the bytes that move it (0.143944 of 0.143940, this revision's overlap-probe.txt; 0.143945
# of 0.143942, overlap-probe-2.txt) and 0 for bytes that do not (0.000000 in both)
_ENVELOPE_WINDOW, _ENVELOPE_HOP = 0.02, 0.005  # seconds: the overlap probes' Hann envelope
_HELD_FROM, _HELD_TO = 0.2, 1.4
"""The seconds a measure of the held note is taken over. The note sounds from 0 to 1.5 s: the
segment starts past the opening, which is over by 0.102 s, and past the note's own attack, and
ends before its release, so it holds the steady note and neither of its ends."""

_C4_BAR = Pattern(
    tempo_bpm=120.0,
    bars=1,
    beats_per_bar=4,
    notes=(Note(pitch=60, velocity=100, start_beats=0.0, duration_beats=3.0, channel=0),),
)
"""One C4 held for 1.5 s in a bar of 2 s, as the probes played it."""

_NO_NOTES = Pattern(tempo_bpm=120.0, bars=1, beats_per_bar=4, notes=())
_NO_TAIL = RenderRequest(sample_rate=_RATE, tail_seconds=0.0)


@pytest.fixture(scope="module")
def vital() -> VitalHost:
    """Return the module's one loaded Vital, or skip saying why: no Vital, or another machine."""
    if not DEFAULT_PATH.exists():
        pytest.skip(f"no Vital at {DEFAULT_PATH}")
    measured, running = parameter_map().machine, platform.machine()
    if measured != running:
        pytest.skip(f"the map was measured on {measured!r}, this is {running!r}")
    return VitalHost()


@pytest.fixture
def bus() -> EventBus:
    """Give each test a bus no other test has published on."""
    return EventBus()


@pytest.fixture
def instrument(bus: EventBus, vital: VitalHost) -> VitalInstrument:
    """Give each test a new instrument over the module's Vital, on the start preset again.

    Its construction loads the start preset twice, which leaves the plugin holding the start's
    903 floats whatever the test before it set (`test_the_next_instrument_starts_clean`).
    """
    return VitalInstrument(bus, vital)


def _recorder(bus: EventBus) -> RecordingSubscriber:
    recorder = RecordingSubscriber()
    bus.subscribe(None, recorder)
    return recorder


def _float32(value: float) -> float:
    """Return the float32 nearest a double, by `struct`."""
    held: float = struct.unpack("<f", struct.pack("<f", value))[0]
    return held


def _what_a_set_holds(own: float, minimum: float, maximum: float) -> float:
    """Return the float32 a set of a float32 holds, from primitives, as the plugin computes it.

    The span is the float32 difference of the scale's ends, the normalized value the float32
    nearest the exact quotient, and the value held that times the span plus the minimum, rounded
    once: each a correctly rounded double of an exact `Fraction`, narrowed by `struct`.
    """
    span = _float32(float(Fraction(maximum) - Fraction(minimum)))
    normalized = _float32(float((Fraction(own) - Fraction(minimum)) / Fraction(span)))
    return _float32(float(Fraction(normalized) * Fraction(span) + Fraction(minimum)))


def _state_floats(instrument: VitalInstrument) -> dict[str, float]:
    """Return the plugin's own floats, through the diagnostic read."""
    return _floats(instrument.host.state())


def _model_floats(preset: VitalPreset) -> dict[str, float]:
    """Return what the model says each of the 903 holds: its float, or the default without one."""
    _, slots = split_modulations(preset.modulations)
    held = {str(key): value for key, value in (*preset.settings.values.items(), *slots.items())}
    return {
        record.preset_key: held.get(record.preset_key, record.preset_default)
        for record in parameter_map().parameters
    }


def _quantity(value: float, unit: Unit = Unit.none) -> Quantity:
    return Quantity(value=value, unit=unit)


def _peaks(audio: NDArray[np.float32]) -> NDArray[np.float32]:
    """Return the larger magnitude of the channels, sample by sample."""
    peaks: NDArray[np.float32] = np.abs(audio).max(axis=0)
    return peaks


def _held(audio: NDArray[np.float32]) -> NDArray[np.float32]:
    """Return the mean of the channels over the held note, `_HELD_FROM` to `_HELD_TO` seconds."""
    held: NDArray[np.float32] = audio.mean(axis=0)[int(_HELD_FROM * _RATE) : int(_HELD_TO * _RATE)]
    return held


def _rms(audio: NDArray[np.float32]) -> float:
    """Return the RMS of the held note, the probes' measure of whether a render is audible."""
    return float(np.sqrt((_held(audio).astype(np.float64) ** 2).mean()))


def _centroid(audio: NDArray[np.float32]) -> float:
    """Return the spectral centroid of the held note in Hz, the probes' measure, written once.

    The mean of the channels over the held note, under a Hann window so that the segment's two
    ends add no spectrum of their own, the magnitude of its real FFT, and that magnitude's
    frequency-weighted mean. A segment whose magnitudes sum to nothing is silence, and fails by
    that name instead of dividing by it.
    """
    held = _held(audio)
    magnitude = np.abs(np.fft.rfft(held * np.hanning(held.size)))
    total = float(magnitude.sum())
    if total == 0.0:
        pytest.fail("the held note is silent: there is no spectrum to take a centroid of")
    return float((np.fft.rfftfreq(held.size, 1 / _RATE) * magnitude).sum() / total)


def _level(audio: NDArray[np.float32], start: float, end: float) -> float:
    """Return the overlap probes' level of a render between two times, in seconds, written once.

    Its RMS under a Hann window of `_ENVELOPE_WINDOW` every `_ENVELOPE_HOP`, both channels,
    divided by the window's own RMS, and the median of those whose centres fall in the span.
    """
    size, hop = round(_ENVELOPE_WINDOW * _RATE), round(_ENVELOPE_HOP * _RATE)
    window = np.hanning(size)
    norm = float(np.sqrt(np.mean(window**2)))
    signal = audio.astype(np.float64)
    starts = np.arange(0, signal.shape[1] - size, hop)
    centres = (starts + size / 2) / _RATE
    inside = starts[(centres >= start) & (centres <= end)]
    levels = [np.sqrt(np.mean((signal[:, at : at + size] * window) ** 2)) / norm for at in inside]
    return float(np.median(levels))


def _two_bars(*notes: tuple[int, float, float]) -> Pattern:
    """Return two bars at 120 bpm of C4s on the first channel, each (velocity, start, duration)."""
    return Pattern(
        tempo_bpm=120.0,
        bars=2,
        beats_per_bar=4,
        notes=tuple(
            Note(pitch=60, velocity=v, start_beats=at, duration_beats=d, channel=0)
            for v, at, d in notes
        ),
    )


def _manifest(pytestconfig: pytest.Config) -> list[str]:
    """Return the installed presets the manifest lists, or skip where none is installed."""
    lines = (pytestconfig.rootpath / _MANIFEST).read_text(encoding="utf-8").splitlines()
    listed = [line for line in lines if not line.startswith("#")]
    assert len(listed) == _MANIFEST_LENGTH
    if not _PRESETS.is_dir():
        pytest.skip(f"no installed Vital presets at {_PRESETS}")
    return listed


def _upgraded(pytestconfig: pytest.Config) -> dict[str, dict[str, tuple[float | None, float]]]:
    """Read `tests/data/upgraded-floats.txt`: by preset and key, the file's float and Vital's.

    A line that is not `<preset><TAB><key><TAB><float or absent><TAB><float>` fails the test that
    reads it, naming the file and the line, and so does a file that holds no line or repeats one.
    """
    path = pytestconfig.rootpath / _UPGRADED
    found: dict[str, dict[str, tuple[float | None, float]]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        try:
            preset, key, written, held = fields
            in_file = None if written == "absent" else float(written)
            row = (in_file, float(held))
        except ValueError:
            pytest.fail(f"{path.name}:{number} is not '<preset> <key> <float|absent> <float>'")
        if key in found.setdefault(preset, {}):
            pytest.fail(f"{path.name}:{number} repeats {key} of {preset}")
        found[preset][key] = row
    if not found:
        pytest.fail(f"{path.name} holds no float")
    return found


# --- core's contract -----------------------------------------------------------------------------


@pytest.mark.parametrize("contract_test", CONTRACT_TESTS, ids=lambda test: test.__name__)
def test_contract_against_vital(
    contract_test: ContractTest, instrument: Instrument, bus: EventBus
) -> None:
    """Each of core's contract tests passes against the installed Vital, as core wrote it."""
    contract_test(instrument, bus)


def test_the_next_instrument_starts_clean(bus: EventBus, vital: VitalHost) -> None:
    """After a render and a set of every parameter, a new instrument starts on the start preset.

    The model is the start preset, and the plugin, read through the diagnostic read, holds the
    start's 903 floats, its routing and its sections but the sample, which every load delays by
    4 samples: so one test's state does not reach the next, in the model or in the plugin.
    """
    first = VitalInstrument(bus, vital)
    first.render(_C4_BAR, _NO_TAIL)
    for parameter in first.parameters():
        far = (
            parameter.minimum if parameter.default.value == parameter.maximum else parameter.maximum
        )
        first.set(parameter.id, _quantity(far, parameter.unit))
    start = _model_floats(start_preset())
    moved = _state_floats(first)
    assert sum(moved[key] != held for key, held in start.items()) == _PARAMETERS
    second = VitalInstrument(EventBus(), vital)
    assert second.preset is start_preset()
    assert _state_floats(second) == start
    state = loads(vital.state().decode("utf-8"))
    assert state.modulations == start_preset().modulations
    assert {k: v for k, v in state.opaque.items() if k != "sample"} == {
        k: v for k, v in start_preset().opaque.items() if k != "sample"
    }


# --- what a set holds ----------------------------------------------------------------------------


def test_after_a_set_at_each_bound_the_plugin_holds_the_model_s_float(
    instrument: VitalInstrument,
) -> None:
    """All 1,806 bounds, counted: `get` returns the bound and Vital holds the model's float."""
    counted = 0
    for record in parameter_map().parameters:
        parameter = record.parameter
        for bound in (parameter.maximum, parameter.minimum):
            value = _quantity(bound, parameter.unit)
            instrument.set(parameter.id, value)
            assert instrument.get(parameter.id) == value
            held = _model_floats(instrument.preset)[record.preset_key]
            assert _state_floats(instrument)[record.preset_key] == held, (parameter.id, bound)
            counted += 1
    assert counted == _BOUNDS


def test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """Finding 1, decided, on Vital: `beats_per_minute` at 216.85141355537831.

    The float32 a set of that display holds, worked out from primitives, is 3.6141905784606934,
    shown as 216.8514347076416. Vital holds that float, `get` returns that display and the
    event's `new` carries it. The float32 below it is nearer the display given and is not taken.
    """
    tempo = ParameterId("beats_per_minute")
    given = 216.85141355537831
    held = _what_a_set_holds(_float32(given / 60.0), _float32(1 / 3), 5.0)
    assert held == 3.6141905784606934  # noqa: PLR2004 - the value the issue gives
    recorder = _recorder(bus)
    instrument.set(tempo, _quantity(given, Unit.bpm))
    shown = _quantity(held * 60.0, Unit.bpm)
    assert shown.value == 216.8514347076416  # noqa: PLR2004 - the display the issue gives
    assert instrument.get(tempo) == shown
    assert _state_floats(instrument)["beats_per_minute"] == held
    (changed,) = recorder.of_type(ParameterChanged)
    assert changed.new == shown


@pytest.mark.parametrize(
    "case",
    [
        ("chorus_voices", 6.0, 8.0, 2.0),  # 1.5 in fours: a tie, away from zero
        ("chorus_voices", 5.0, 4.0, 1.0),  # 1.25 in fours
        ("oversampling", 3.0, 4.0, 2.0),  # log2(3) is 1.58, the step of 4
    ],
    ids=["chorus_voices 6", "chorus_voices 5", "oversampling 3"],
)
def test_a_value_between_steps_is_taken_and_vital_holds_the_nearest_step(
    instrument: VitalInstrument, case: tuple[str, float, float, float]
) -> None:
    """Finding 4, decided, on Vital: the parameter, the value given, the display, the preset."""
    name, given, shown, held = case
    instrument.set(ParameterId(name), _quantity(given))
    assert instrument.get(ParameterId(name)) == _quantity(shown)
    assert _state_floats(instrument)[name] == held


def test_a_set_of_the_value_already_shown_leaves_vital_holding_its_off_grid_float(
    instrument: VitalInstrument,
) -> None:
    """Finding 3, decided, on Vital: the 22 defaults the scale does not hold, counted.

    A set of each one's own display changes neither the model nor what Vital holds, which is the
    float the preset gave it, one no set through the host can land on.
    """
    off_grid = [r for r in parameter_map().parameters if not r.scale.holds(r.preset_default)]
    assert len(off_grid) == _OFF_GRID_DEFAULTS
    for record in off_grid:
        instrument.set(record.id, instrument.get(record.id))
    assert instrument.preset is start_preset()
    state = _state_floats(instrument)
    assert all(state[record.preset_key] == record.preset_default for record in off_grid)


def test_a_set_of_the_value_shown_on_an_upgraded_float_sets_vital_to_the_model_s(
    instrument: VitalInstrument, pytestconfig: pytest.Config
) -> None:
    """PR 23's finding 1, on Vital: the model holds `osc_1_stack_style` 9, Vital plays 10.

    Ah Eh Ee Oh is older than Vital 1.6.4, which upgrades its stack style as it loads (issue
    #22; `tests/data/upgraded-floats.txt`). 9 is a step a set lands on, so a set of the value
    `get` shows reaches Vital, which then holds 9, the model's float. Where the presets are not
    installed this skips, saying so.
    """
    listed = _manifest(pytestconfig)
    assert _AH_EH in listed
    stack = ParameterId("osc_1_stack_style")
    instrument.load_patch(patch_of(loads((_PRESETS / _AH_EH).read_text(encoding="utf-8"))))
    assert instrument.get(stack) == _quantity(9.0)
    assert _state_floats(instrument)["osc_1_stack_style"] == 10.0  # noqa: PLR2004 - Vital's upgrade
    instrument.set(stack, _quantity(9.0))
    assert _state_floats(instrument)["osc_1_stack_style"] == 9.0  # noqa: PLR2004 - the model's
    assert instrument.get(stack) == _quantity(9.0)


def test_a_set_of_the_value_shown_mends_42_of_the_upgraded_floats_is_refused_on_3_and_kept_on_1(
    instrument: VitalInstrument, pytestconfig: pytest.Config
) -> None:
    """Finding A of PR 23's second review, counted on Vital over all 46 floats it upgrades.

    For each float `tests/data/upgraded-floats.txt` records, on its preset as loaded, the value
    `get` shows is set, and what Vital then holds is read through the diagnostic read:

    - mended, 42: the set reaches Vital, which then holds the model's float, for a key the file
      lacks the parameter's default;
    - refused, 3: `flanger_center`, whose file value shows a display outside its bounds, so the
      set is `ParameterRangeError` and nothing changes;
    - kept, 1: `modulation_10_amount` on Oolacile Evil Dubstep Bass, a float no set lands on, so
      the keep rule keeps it, the model is the same object and Vital goes on holding its
      upgraded float. No set can put Vital on the model's float there.

    The three refused and the one kept are written out. What the model should hold for a preset
    older than the plugin is issue #22's to decide. Where the presets are not installed this
    skips, saying so.
    """
    recorded = _upgraded(pytestconfig)
    assert set(recorded) <= set(_manifest(pytestconfig))
    mended = 0
    refused: set[tuple[str, str]] = set()
    kept: dict[tuple[str, str], tuple[float, float]] = {}
    for relative, floats in recorded.items():
        text = (_PRESETS / relative).read_bytes().decode("utf-8")
        instrument.load_patch(patch_of(loads(text)))
        for key, (_, upgraded) in floats.items():
            before = instrument.preset
            assert _state_floats(instrument)[key] == upgraded, (relative, key)
            try:
                instrument.set(ParameterId(key), instrument.get(ParameterId(key)))
            except ParameterRangeError:
                refused.add((relative, key))
                assert instrument.preset is before, (relative, key)
                assert _state_floats(instrument)[key] == upgraded, (relative, key)
                continue
            model, state = _model_floats(instrument.preset)[key], _state_floats(instrument)[key]
            if state == model:
                mended += 1
            else:
                assert instrument.preset is before, (relative, key)
                kept[(relative, key)] = (model, state)
    assert refused == _REFUSED
    assert kept == _KEPT
    assert mended == _MENDED
    assert mended + len(refused) + len(kept) == _UPGRADED_FLOATS


def test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour_on_vital(
    instrument: VitalInstrument,
) -> None:
    """The case the keep rule leaves, as Vital has it today, for core's wording to decide.

    The issue drafted for fromtheoutfit/patchbay in this spec's shape.md, "Instrument.get: a value
    `get` has returned is not always one `set` lands on", asks what core's clause promises here.
    `chorus_feedback` starts on the float32 of 0.4, which no normalized value lands on; `get`
    returns its display, another value is set, and that display is set back. Vital then holds the
    float32 a set of 0.4 lands on, worked out here from primitives, and `get` returns that
    float's display and not the value given.
    """
    feedback = ParameterId("chorus_feedback")
    started = _float32(0.4)
    first = instrument.get(feedback)
    assert first == _quantity(started * 100.0, Unit.percent)
    instrument.set(feedback, _quantity(10.0, Unit.percent))
    instrument.set(feedback, first)
    held = _what_a_set_holds(started, _float32(-0.95), _float32(0.95))
    assert held != started
    assert _state_floats(instrument)["chorus_feedback"] == held
    assert instrument.get(feedback) == _quantity(held * 100.0, Unit.percent) != first


# --- loads ---------------------------------------------------------------------------------------


def test_one_load_after_a_set_leaves_the_off_grid_floats_off_and_a_second_holds_them(
    instrument: VitalInstrument,
) -> None:
    """Why every load is made twice: a measured workaround, held so a new Vital fails by name.

    On Vital 1.6.4 through pedalboard 0.9.26 on arm64, after a set of every parameter, one load
    of the start preset's text leaves exactly the 22 defaults the scale does not hold off the
    text's floats, and a second load of the same text holds all 903 (the instrument spec's
    `verification/probes.txt`, sections 6 and 9). No cause is known. A Vital that needs one load
    fails the first count here, and one that needs three the second.
    """
    assert LOADS == 2  # noqa: PLR2004 - the workaround's own number
    for parameter in instrument.parameters():
        far = (
            parameter.minimum if parameter.default.value == parameter.maximum else parameter.maximum
        )
        instrument.set(parameter.id, _quantity(far, parameter.unit))
    text = dumps(start_preset()).encode("utf-8")
    start = _model_floats(start_preset())
    off_grid = {
        r.preset_key for r in parameter_map().parameters if not r.scale.holds(r.preset_default)
    }
    instrument.host.load_state(text)
    once = _state_floats(instrument)
    assert {key for key, held in start.items() if once[key] != held} == off_grid
    assert len(off_grid) == _OFF_GRID_DEFAULTS
    instrument.host.load_state(text)
    assert _state_floats(instrument) == start


def test_a_patch_of_values_alone_loads_as_the_start_preset_with_those_values(
    instrument: VitalInstrument,
) -> None:
    """The short form on Vital: the model is the start with those values, and Vital holds it."""
    instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    values = {
        ParameterId("filter_1_on"): _quantity(1.0),
        ParameterId("filter_1_cutoff"): _quantity(12.0, Unit.semitones),
    }
    instrument.load_patch(Patch(instrument="Vital", values=values))
    expected = {**_model_floats(start_preset()), "filter_1_on": 1.0, "filter_1_cutoff": 72.0}
    assert _model_floats(instrument.preset) == expected
    assert _state_floats(instrument) == expected
    assert instrument.preset.opaque == start_preset().opaque


def test_a_patch_refused_part_way_leaves_the_model_and_vital_as_they_were(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """A whole patch bad only at its last value: Vital, read back, holds what it held."""
    instrument.set(ParameterId("filter_1_cutoff"), _quantity(12.0, Unit.semitones))
    before, state = instrument.preset, _state_floats(instrument)
    recorder = _recorder(bus)
    whole = instrument.patch()
    moved = {
        parameter.id: _quantity(
            parameter.minimum
            if whole.values[parameter.id].value == parameter.maximum
            else parameter.maximum,
            parameter.unit,
        )
        for parameter in instrument.parameters()
    }
    past = _quantity(math.nextafter(-80.0, -math.inf), Unit.db)
    bad = Patch(
        instrument="Vital", values={**moved, ParameterId("volume"): past}, opaque=whole.opaque
    )
    with pytest.raises(PatchRefusedError) as caught:
        instrument.load_patch(bad)
    assert caught.value.reason.startswith("volume: ")
    assert instrument.preset is before
    assert _state_floats(instrument) == state
    assert recorder.events == ()


def test_each_installed_preset_loads_through_a_patch_and_comes_back_byte_for_byte(
    instrument: VitalInstrument, pytestconfig: pytest.Config
) -> None:
    """For each manifest preset: the model after `load_patch(patch())` writes the text loaded.

    Each passes the guard before Vital is given it. The preset is carried in a patch, loaded,
    given back by `patch()` and loaded again, and the model then writes the file's own bytes.
    """
    for relative in _manifest(pytestconfig):
        text = (_PRESETS / relative).read_bytes().decode("utf-8")
        preset = loads(text)
        check_loadable(preset, parameter_map())
        instrument.load_patch(patch_of(preset))
        instrument.load_patch(instrument.patch())
        assert dumps(instrument.preset) == text, relative


def test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none(
    instrument: VitalInstrument, pytestconfig: pytest.Config
) -> None:
    """Over the installed presets, the plugin's 903 floats against the model's, counted.

    After `load_patch`, which loads twice, the floats Vital holds that are not the model's are
    exactly those `tests/data/upgraded-floats.txt` records, 46 on 11 presets, each Vital's own
    upgrade of a preset older than it: on the other 64 Vital holds the model's float on all 903.
    A third load holds the same floats. So for a preset older than the plugin, `get` reports the
    file's value where Vital plays its upgraded one, which for a choice is another setting by
    name: the limit the instrument's docstring states, and issue #22's to decide. A Vital that
    upgrades otherwise, or needs another number of loads, fails here naming the preset.
    """
    recorded = _upgraded(pytestconfig)
    assert sum(len(keys) for keys in recorded.values()) == _UPGRADED_FLOATS
    assert len(recorded) == _UPGRADED_PRESETS
    listed = _manifest(pytestconfig)
    assert set(recorded) <= set(listed)
    for relative in listed:
        text = (_PRESETS / relative).read_bytes()
        preset = loads(text.decode("utf-8"))
        instrument.load_patch(patch_of(preset))
        model, state = _model_floats(instrument.preset), _state_floats(instrument)
        differing = {key: state[key] for key, held in model.items() if state[key] != held}
        expected = recorded.get(relative, {})
        assert differing == {key: held for key, (_, held) in expected.items()}, relative
        _, slots = split_modulations(preset.modulations)
        in_file = {**preset.settings.values, **slots}
        for key, (written, _) in expected.items():
            assert in_file.get(PresetKey(key)) == written, (relative, key)
        instrument.host.load_state(text)
        assert _state_floats(instrument) == state, relative


# --- renders -------------------------------------------------------------------------------------


def test_a_note_lands_on_the_sample_core_s_rule_gives_it(instrument: VitalInstrument) -> None:
    """At 100,003 samples, where the time of the sample itself lands one early (probes.txt).

    At 60 bpm and 48 kHz the beat 100003 / 48000 falls on sample 100,003. Nothing sounds from the
    end of the opening to the note, and the first sample that is not zero is the note's own: the
    builder's half sample past it is what puts it there.
    """
    sample = 100003
    late = Pattern(
        tempo_bpm=60.0,
        bars=1,
        beats_per_bar=4,
        notes=(
            Note(pitch=60, velocity=100, start_beats=sample / _RATE, duration_beats=1.0, channel=0),
        ),
    )
    assert _NO_TAIL.sample_at(late, sample / _RATE) == sample
    peaks = _peaks(instrument.render(late, _NO_TAIL).audio)
    assert float(peaks[_OPENING_ENDS:sample].max()) < _QUIET
    assert int(np.nonzero(peaks[_OPENING_ENDS:])[0][0]) + _OPENING_ENDS == sample


def test_two_notes_of_one_pitch_that_overlap_each_sound_for_their_own_length(
    instrument: VitalInstrument,
) -> None:
    """PR 23's finding 5, on Vital: as core's reference instrument sums a sine per note.

    On the start preset, C4 from beat 0 to 2 and C4 from 1 to 3 (0 to 1 s, 0.5 to 1.5 s). After
    the first ends, the second sounds at its level alone, under the probes' window: on one
    channel Vital would release both at the first note-off, and the builder moves the second to
    a channel of its own. The same for two struck on one sample, one beat and three long.
    """
    overlap = instrument.render(_two_bars((100, 0.0, 2.0), (100, 1.0, 2.0)), _NO_TAIL).audio
    later_alone = instrument.render(_two_bars((100, 1.0, 2.0)), _NO_TAIL).audio
    assert _level(later_alone, 1.05, 1.45) > _AUDIBLE
    assert _level(overlap, 1.05, 1.45) / _level(later_alone, 1.05, 1.45) > _OWN_LENGTH
    together = instrument.render(_two_bars((100, 0.0, 1.0), (50, 0.0, 3.0)), _NO_TAIL).audio
    longer_alone = instrument.render(_two_bars((50, 0.0, 3.0)), _NO_TAIL).audio
    assert _level(longer_alone, 0.55, 0.95) > _AUDIBLE
    assert _level(together, 0.55, 0.95) / _level(longer_alone, 0.55, 0.95) > _OWN_LENGTH


def test_a_note_left_sounding_is_not_heard_in_the_next_render(instrument: VitalInstrument) -> None:
    """A note held to the end of the bar gets no note-off, the render ending first.

    It still sounds in the last samples of its own render, and the next render, of no notes, is
    quiet once its opening is over: the host resets the plugin before each render.
    """
    to_the_end = Pattern(
        tempo_bpm=120.0,
        bars=1,
        beats_per_bar=4,
        notes=(Note(pitch=60, velocity=100, start_beats=0.0, duration_beats=4.0, channel=0),),
    )
    ringing = _peaks(instrument.render(to_the_end, _NO_TAIL).audio)
    assert float(ringing[-100:].max()) > _AUDIBLE
    after = _peaks(instrument.render(_NO_NOTES, _NO_TAIL).audio)
    assert float(after[_OPENING_ENDS:].max()) < _QUIET


def test_a_render_of_no_notes_on_the_start_preset_is_its_small_transient_and_no_warning(
    instrument: VitalInstrument,
) -> None:
    """The opening on the start preset: under `_TRANSIENT`, over by `_OPENING_ENDS`, no warning."""
    result = instrument.render(_NO_NOTES, _NO_TAIL)
    peaks = _peaks(result.audio)
    assert float(peaks.max()) < _TRANSIENT
    assert float(peaks[_OPENING_ENDS:].max()) < _QUIET
    assert result.warnings == ()
    assert result.elapsed_seconds > 0.0


def test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding(
    instrument: VitalInstrument, pytestconfig: pytest.Config
) -> None:
    """Today's behaviour, held so that the host's fix has to change this test on purpose.

    Issue #21, "The host: a render opens with the preset's own sound though no note was played",
    asks for a render that does not. Until it lands: Plucked String, one of Vital's own presets,
    rendered with no MIDI at all, peaks above `_OPENING_SOUND` in its first 100 ms, where the
    probes measured 0.21 to 0.37 over six renders and the start preset's transient is under
    `_TRANSIENT`.
    """
    assert _PLUCKED in _manifest(pytestconfig)
    preset = loads((_PRESETS / _PLUCKED).read_bytes().decode("utf-8"))
    check_loadable(preset, parameter_map())
    instrument.load_patch(patch_of(preset))
    peaks = _peaks(instrument.render(_NO_NOTES, _NO_TAIL).audio)
    assert float(peaks[: _RATE // 10].max()) > _OPENING_SOUND > _TRANSIENT


def test_a_render_that_clips_carries_one_warning_and_the_event_carries_it(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """Eight notes at full velocity with volume and the oscillator's level at their maximum.

    Vital gives samples past full scale, up to 2.1 (probes.txt, section 3), and the result holds
    them as given, with exactly one warning that the `RenderCompleted` carries too.
    """
    instrument.set(ParameterId("volume"), _quantity(instrument.parameters()[-1].maximum, Unit.db))
    instrument.set(ParameterId("osc_1_level"), _quantity(1.0))
    chord = Pattern(
        tempo_bpm=120.0,
        bars=1,
        beats_per_bar=4,
        notes=tuple(
            Note(pitch=pitch, velocity=127, start_beats=0.0, duration_beats=2.0, channel=0)
            for pitch in (36, 40, 43, 48, 52, 55, 60, 64)
        ),
    )
    recorder = _recorder(bus)
    result = instrument.render(chord, _NO_TAIL)
    assert float(_peaks(result.audio).max()) > FULL_SCALE
    (warning,) = result.warnings
    assert warning.startswith("clipped: the render peaks at ")
    (completed,) = recorder.of_type(RenderCompleted)
    assert completed.warnings == result.warnings
    assert len(recorder.events) == 1


def test_a_render_of_no_samples_leaves_vital_as_it_was(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """An empty result and one event, and Vital, read back, holds what it held."""
    instant = Pattern(tempo_bpm=23_040_000.0, bars=1, beats_per_bar=4, notes=_C4_BAR.notes)
    assert _NO_TAIL.samples(instant) == 0
    state = _state_floats(instrument)
    recorder = _recorder(bus)
    result = instrument.render(instant, _NO_TAIL)
    assert result.audio.shape == (2, 0)
    assert [type(event) for event in recorder.events] == [RenderCompleted]
    assert instrument.preset is start_preset()
    assert _state_floats(instrument) == state


def test_the_longest_render_is_given_and_one_sample_more_is_refused(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """`MAX_SAMPLES` is a length Vital gives, every sample finite, and the next one is refused."""
    longest = Pattern(tempo_bpm=60.0, bars=1, beats_per_bar=1024, notes=())
    request = RenderRequest(sample_rate=2**14, tail_seconds=0.0)
    assert request.samples(longest) == MAX_SAMPLES
    result = instrument.render(longest, request)
    assert result.audio.shape == (2, MAX_SAMPLES)
    recorder = _recorder(bus)
    state = _state_floats(instrument)
    longer = RenderRequest(sample_rate=2**14, tail_seconds=1 / 2**14)
    assert longer.samples(longest) == MAX_SAMPLES + 1
    with pytest.raises(RenderRefusedError) as caught:
        instrument.render(longest, longer)
    assert (
        caught.value.reason
        == f"a render of {MAX_SAMPLES + 1} samples is past MAX_SAMPLES, {MAX_SAMPLES}"
    )
    assert recorder.events == ()
    assert _state_floats(instrument) == state


def test_the_spectral_centroid_moves_with_the_cutoff(instrument: VitalInstrument) -> None:
    """Filter 1 on, a C4 held 1.5 s: a higher cutoff gives a higher centroid, by a named ratio.

    The cutoff is set to the displays the probes used, those of normalized 0.3 and 0.8: -13.6
    and 50.4 semitones about 60, worked out here from the scale's 8 to 136. Each render is first
    held to be audible, its RMS over the held note above `_AUDIBLE`, so a silent render fails as
    silence; then the high cutoff's centroid over the low's exceeds `_CENTROID_RATIO`. The probes
    measured 320.56 Hz and 2,349.97 Hz on 20 renders each, a least ratio of 7.331.
    """
    centroids = []
    for normalized in (0.3, 0.8):
        preset_value = _float32(float(Fraction(_float32(normalized)) * 128 + 8))
        instrument.load_patch(Patch(instrument="Vital", values={}))
        instrument.set(ParameterId("filter_1_on"), _quantity(1.0))
        instrument.set(
            ParameterId("filter_1_cutoff"), _quantity(preset_value - 60.0, Unit.semitones)
        )
        assert _state_floats(instrument)["filter_1_cutoff"] == preset_value
        audio = instrument.render(_C4_BAR, _NO_TAIL).audio
        assert _rms(audio) > _AUDIBLE, normalized
        centroids.append(_centroid(audio))
    low, high = centroids
    assert high / low > _CENTROID_RATIO, (low, high)


def test_what_the_data_file_of_upgraded_floats_holds(pytestconfig: pytest.Config) -> None:
    """46 floats on 11 presets, each a manifest preset, read by a reader that fails by name."""
    recorded = _upgraded(pytestconfig)
    lines = (pytestconfig.rootpath / _MANIFEST).read_text(encoding="utf-8").splitlines()
    assert set(recorded) <= set(lines)
    assert (sum(len(keys) for keys in recorded.values()), len(recorded)) == (
        _UPGRADED_FLOATS,
        _UPGRADED_PRESETS,
    )
    assert json.dumps(sorted(recorded["Factory/Presets/Ah Eh Ee Oh.vital"].items())) == (
        '[["osc_1_stack_style", [9.0, 10.0]]]'
    )
