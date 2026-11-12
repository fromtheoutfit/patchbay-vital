"""The installed Vital, hosted: the map is the plugin's; its state and renders are as measured.

Vital may not be redistributed, so these tests run where it is installed, at the host's
`DEFAULT_PATH`, and skip saying so elsewhere, CI among the places. Audio is not sample-reproducible
(the host spec's shape.md, Decision 10), so every audio assertion is a measure with a named
tolerance, and each says which probe its number came from (`verification/probes.txt`,
`verification/host-probes.txt`). A state's floats are read with the host's own `_floats`, so a test
compares what the census reads.
"""

import base64
import json
import platform
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from patchbay import ParameterId

from patchbay_vital import loads
from patchbay_vital.census import build_map
from patchbay_vital.errors import ParameterRangeError, PluginRenderError, UnknownParameterError
from patchbay_vital.host import DEFAULT_PATH, VitalHost, _floats
from patchbay_vital.parameters import PRESET_ONLY_KEYS, MappedParameter, parameter_map
from patchbay_vital.state import unwrap, wrap

pytestmark = pytest.mark.integration

_RATE = 48000
_PRESETS = Path.home() / "Music" / "Vital"
_MANIFEST = Path("tests") / "data" / "factory-manifest.txt"
_FIXTURE = Path("tests") / "data" / "init-media-replaced.vital"
_MANIFEST_LENGTH = 75
_SAMPLE_DELAY = 4  # samples a state load delays the embedded sample by (probes: 4 a load, 3 loads)
_SAMPLE_STEPS = 1  # 16-bit steps a load moves a sample value by (this test: -5000 read back -4999)
_SECOND_LOAD_ULPS = 8  # float32 steps a value moves on a second load (probes: at most 7, 7 presets)
_JSON_ROUTE_VARIATION = 0.5  # 20 ms RMS variation of the routed render (probes: 1.351)
_CONTROL_VARIATION = 0.1  # the same, unrouted (probes: 0.0176)
_QUIET = 1e-6  # peak from 0.15 s to a note at 0.5 s (host probes: 0, the start's transient gone)
_ONSET = 1e-3  # where a note has begun (host probes: past 1e-3 at +5 to +8 samples)
_ONSET_SAMPLES = 96  # 2 ms at 48 kHz, a generous bound on that


@pytest.fixture(scope="module")
def vital() -> VitalHost:
    """Return the module's one loaded Vital, or skip saying why: no Vital, or another machine.

    A load takes about two seconds, so the module shares one plugin; `host` resets it per test.
    The map is the machine's it was measured on, so on another the host would refuse it and the
    census test would compare another machine's name: both skip here, by name.
    """
    if not DEFAULT_PATH.exists():
        pytest.skip(f"no Vital at {DEFAULT_PATH}")
    measured, running = parameter_map().machine, platform.machine()
    if measured != running:
        pytest.skip(f"the map was measured on {measured!r}, this is {running!r}")
    return VitalHost()


@pytest.fixture(scope="module")
def initial(vital: VitalHost) -> bytes:
    """Return the state the plugin loaded with, before any test touched it."""
    return vital.state()


@pytest.fixture
def host(vital: VitalHost, initial: bytes) -> VitalHost:
    """Return the module's Vital holding its initial state again, so each test starts there.

    A load delays the embedded sample by 4 samples (the plugin-state standard), which no test here
    depends on; every setting, routing and section is the initial state's.
    """
    vital.load_state(initial)
    return vital


def _ulps(a: float, b: float) -> int:
    """Return how many float32 steps two values of one sign are apart."""
    bits = np.array([a, b], dtype=np.float32).view(np.int32)
    return abs(int(bits[0]) - int(bits[1]))


def test_the_census_regenerates_the_committed_map(host: VitalHost) -> None:
    """Measured again, the plugin gives the map in the repository, record for record."""
    committed = parameter_map()
    assert (host.name, host.version) == (committed.instrument, committed.vital_version)
    assert build_map(host) == committed


def test_every_hosted_parameter_is_mapped_and_every_record_hosted(host: VitalHost) -> None:
    """The map and the plugin agree on which parameters there are, both ways."""
    assert host.unmapped_parameters() == ()
    assert sorted(host.parameter_ids()) == sorted(parameter_map().ids())


def _one_of_each() -> list[MappedParameter]:
    """One record per kind, scale and curve the map holds, the first of each by id."""
    seen: dict[tuple[str, str, str], MappedParameter] = {}
    for record in parameter_map().parameters:
        seen.setdefault((record.parameter.kind, record.scale.kind, record.curve.kind), record)
    return list(seen.values())


def _held_after_a_set(host: VitalHost, record: MappedParameter, display: float) -> float:
    """Set a display through the host, normalized as the map gives it; return the state's value."""
    host.set(record.id, record.to_normalized(display))
    return _floats(host.state())[record.preset_key]


def test_a_value_set_through_the_host_is_the_one_the_state_holds(host: VitalHost) -> None:
    """Per kind, scale and curve: a displayed value set normalized lands on its preset value."""
    for record in _one_of_each():
        parameter = record.parameter
        middle = record.from_normalized(0.37)
        for display in (parameter.minimum, middle, parameter.maximum):
            held = _held_after_a_set(host, record, display)
            assert held == record.to_preset(display), (record.id, display)
            assert record.from_normalized(host.get(record.id)) == record.to_display(held)


def test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value(
    host: VitalHost,
    initial: bytes,
    volume_floor: tuple[tuple[float, int], ...],
    stepped: Callable[[float, int, int], float],
) -> None:
    """At or below the floor, Vital holds the normalized path's value, not an unheld float32.

    Each row of `tests/data/volume-floor.txt` is a normalized value at or below `volume`'s
    2 ** -43 whose display maps to a float32 the scale does not hold. Set from `initial`, as the
    probe set it, Vital holds the scale's value at `to_normalized`'s result, exactly, never the
    float32 nearest the curve's inverse (`record.curve.to_preset`), and its display lands at the
    row's step from the display set, read by `stepped` as the unit test reads it (the revisions
    after PR 14's reviews, `verification/plugin-probe.txt`). Where `to_preset`'s float32 is one
    the scale holds, as on most values at or below the floor, a set holds it and no row records
    it. Issue #15's fix is expected to change the three non-zero rows, on purpose; the unit test
    reads the same file.
    """
    record = parameter_map().find(ParameterId("volume"))
    for normalized, steps in volume_floor:
        host.load_state(initial)
        display = record.from_normalized(normalized)
        held = _held_after_a_set(host, record, display)
        assert held == record.scale.to_preset(record.to_normalized(display)), normalized
        assert held != record.curve.to_preset(display), normalized
        assert record.to_display(held) == stepped(display, steps, 64), (normalized, steps)


def test_a_held_power_of_two_set_through_the_host_lands_as_recorded(
    host: VitalHost,
    initial: bytes,
    power_of_two_presets: tuple[tuple[float, int], ...],
    stepped: Callable[[float, int, int], float],
) -> None:
    """A held power of two set through the host lands where each row says: issue #15 changes it.

    At each row of `tests/data/power-of-two-presets.txt`, on `env_1_delay` and `env_3_hold`, two
    of the 12 records sharing a scale and curve: the preset is a power of two, and set from
    `initial` through the map's normalized path Vital holds the scale's value at that path,
    exactly, the row's float32 steps from the power, one below, read by `stepped` as the unit test
    reads it (the revision after PR 14's second review, `verification/plugin-probe.txt`). Issue
    #15's fix is expected to change the rows to 0, on purpose, and this test then holds Vital at
    the power itself.
    """
    for name in ("env_1_delay", "env_3_hold"):
        record = parameter_map().find(ParameterId(name))
        for normalized, steps in power_of_two_presets:
            host.load_state(initial)
            preset = record.scale.to_preset(normalized)
            held = _held_after_a_set(host, record, record.to_display(preset))
            assert held == record.scale.to_preset(record.scale.to_normalized(preset)), (
                name,
                normalized,
            )
            assert held == stepped(preset, steps, 32), (name, normalized, steps)


def test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given(
    host: VitalHost, initial: bytes, volume_floor: tuple[tuple[float, int], ...]
) -> None:
    """A load of volume at a float32 its scale does not hold is held as the normalized path's.

    An observation no one has explained, held so that a Vital which changes it fails here by name.
    For each row of `tests/data/volume-floor.txt`, a load of `initial` and then, with no set
    between them, of `initial` holding `volume` at the curve's own float32 for the row's display
    (`curve.to_preset`), which the scale does not hold and issue #15 leaves as it is, is held at
    the normalized path's value for that float32; `chorus_feedback`'s off-grid initial value in the
    same load is held as given. The probe saw the same after each of the four histories it tried
    before the first of those loads: a fresh instance, the census's sets, a set of each of the
    two, and the measure's own sets (the revisions after PR 14's reviews,
    `verification/plugin-probe.txt`; first seen in issue #13's). This test does not rely on which
    of them precedes it in a run.
    """
    committed = parameter_map()
    assert (host.name, host.version) == (committed.instrument, committed.vital_version)
    volume = committed.find(ParameterId("volume"))
    chorus = committed.find(ParameterId("chorus_feedback"))
    document = json.loads(initial)
    given = document["settings"][chorus.preset_key]
    assert chorus.scale.to_preset(chorus.scale.to_normalized(given)) != given  # off the grid
    for normalized, _ in volume_floor:
        own = volume.curve.to_preset(volume.from_normalized(normalized))
        document["settings"][volume.preset_key] = own
        host.load_state(initial)
        host.load_state(json.dumps(document).encode())
        floats = _floats(host.state())
        held = volume.scale.to_preset(volume.scale.to_normalized(own))
        assert held != own, normalized
        assert floats[volume.preset_key] == held, normalized
        assert floats[chorus.preset_key] == given, normalized


def test_the_codec_reads_and_writes_the_plugin_s_own_bytes(host: VitalHost) -> None:
    """The VST3 preset the plugin gives is written back byte for byte, its text the state's."""
    data = host.preset_data()
    assert wrap(unwrap(data)) == data
    assert unwrap(data).text == host.state()


def _samples(text: bytes) -> np.ndarray:
    return np.frombuffer(base64.b64decode(json.loads(text)["settings"]["sample"]["samples"]), "<i2")


def test_the_fixture_as_state_reads_back_but_its_sample_delayed(
    host: VitalHost, pytestconfig: pytest.Config
) -> None:
    """A 1.6.4 save loads exactly: every setting, routing and section, but the sample and tuning.

    The containers around the text are the ones the plugin loaded with, so the host reads them once.
    """
    fixture = (pytestconfig.rootpath / _FIXTURE).read_bytes()
    containers = unwrap(host.preset_data())
    host.load_state(fixture)
    state = unwrap(host.preset_data())
    assert state.with_text(containers.text) == containers  # the text changes and no container
    back = state.text
    preset, loaded = loads(fixture.decode("utf-8")), loads(back.decode("utf-8"))
    assert loaded.settings == preset.settings
    assert loaded.modulations == preset.modulations
    assert {k: v for k, v in loaded.opaque.items() if k != "sample"} == {
        k: v for k, v in preset.opaque.items() if k != "sample"
    }
    assert loaded.tuning is not None
    before, after = _samples(fixture).astype(int), _samples(back).astype(int)
    assert np.abs(after[_SAMPLE_DELAY:] - before[:-_SAMPLE_DELAY]).max() <= _SAMPLE_STEPS
    assert not after[:_SAMPLE_DELAY].any()


def test_every_installed_preset_loads_as_state(
    host: VitalHost, pytestconfig: pytest.Config
) -> None:
    """Each manifest preset reads back as a preset: its routing and metadata kept, its keys too.

    Vital upgrades a preset older than 1.6.4 as it loads (every installed one is), so values and
    sections may move on the first load; the second load holds still but for the sample and a few
    float32 steps (probes: 68 of 75 exact, 7 within 7 steps).
    """
    lines = (pytestconfig.rootpath / _MANIFEST).read_text(encoding="utf-8").splitlines()
    manifest = [line for line in lines if not line.startswith("#")]
    assert len(manifest) == _MANIFEST_LENGTH
    if not _PRESETS.is_dir():
        pytest.skip(f"no installed Vital presets at {_PRESETS}")
    containers = unwrap(host.preset_data())
    for relative in manifest:
        text = (_PRESETS / relative).read_bytes()
        original = json.loads(text)
        host.load_state(text)
        state = unwrap(host.preset_data())
        assert state.with_text(containers.text) == containers, relative  # no container changed
        first = state.text
        loaded = loads(first.decode("utf-8"))
        routes = [(m["source"], m["destination"]) for m in original["settings"]["modulations"]]
        kept = [(m.source or "", m.destination or "") for m in loaded.modulations]
        assert kept == routes, relative
        for field in ("author", "comments", "macro1", "macro2", "macro3", "macro4", "preset_style"):
            assert getattr(loaded, field) == original[field], (relative, field)
        floats = _floats(first)
        missing = {k for k, v in original["settings"].items() if isinstance(v, float)} - set(floats)
        assert missing <= PRESET_ONLY_KEYS, relative
        host.load_state(first)
        again = _floats(host.state())
        moved = {k: _ulps(floats[k], again[k]) for k in floats if floats[k] != again[k]}
        assert all(steps <= _SECOND_LOAD_ULPS for steps in moved.values()), (relative, moved)


def _variation(audio: np.ndarray) -> float:
    """Return the coefficient of variation of 20 ms RMS over 0.2-1.4 s, the probes' measure."""
    mono = audio.mean(axis=0)[int(0.2 * _RATE) : int(1.4 * _RATE)]
    frames = mono[: len(mono) // 960 * 960].reshape(-1, 960)
    rms = np.sqrt((frames**2).mean(axis=1))
    return float(rms.std() / rms.mean())


def test_a_routing_only_in_the_preset_text_is_heard(host: VitalHost) -> None:
    """LFO 1 to oscillator 1's level, only in the JSON, moves the level; unrouted it does not."""
    note = [(bytes([0x90, 60, 100]), 0.0), (bytes([0x80, 60, 0]), 1.5)]
    state = json.loads(host.state())
    state["settings"]["modulation_1_amount"] = -1.0
    variations = {}
    for name, route in (("control", ("", "")), ("routed", ("lfo_1", "osc_1_level"))):
        state["settings"]["modulations"][0] = {"source": route[0], "destination": route[1]}
        host.load_state(json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        variations[name] = _variation(host.render(note, 2 * _RATE, _RATE))
    assert variations["routed"] > _JSON_ROUTE_VARIATION
    assert variations["control"] < _CONTROL_VARIATION


@pytest.mark.parametrize("rate", [44100, 48000])
def test_a_render_is_the_length_asked_for_and_finite(host: VitalHost, rate: int) -> None:
    """A render is as long as asked: the host makes up for pedalboard truncating a duration."""
    for samples in (7, 100003):  # each one short when asked for as samples / rate (host probes)
        audio = host.render([(bytes([0x90, 60, 100]), 0.0)], samples, rate)
        assert audio.shape == (2, samples)
        assert audio.dtype == np.float32
        assert np.isfinite(audio).all()


def test_a_note_sounds_from_its_time_and_not_before(host: VitalHost) -> None:
    """A MIDI time is seconds from the start: quiet up to the note, sounding just after it."""
    start = _RATE // 2
    note = [(bytes([0x90, 60, 100]), 0.5), (bytes([0x80, 60, 0]), 1.0)]
    peaks = np.abs(host.render(note, 2 * _RATE, _RATE)).max(axis=0)
    assert peaks[int(0.15 * _RATE) : start].max() < _QUIET  # the render's opening transient is over
    assert int(np.argmax(peaks[start:] > _ONSET)) < _ONSET_SAMPLES


def _subnormals() -> bool:
    """Say whether the process still has subnormal doubles: under flush-to-zero this is zero."""
    smallest = sys.float_info.min
    return smallest / 4 > 0.0 and smallest / 4 * 4 == smallest


def test_the_process_keeps_its_floating_point_environment(host: VitalHost) -> None:
    """Vital turns on flush-to-zero as it loads and renders; the host gives it back after each.

    Without the host's guard every subnormal result after a load is zero, in this process's Python
    and numpy alike (the spec's verification/float-environment.txt).
    """
    assert _subnormals()
    host.set(ParameterId("volume"), 0.5)
    host.load_state(host.state())
    host.render([(bytes([0x90, 60, 100]), 0.0)], 4800, _RATE)
    assert _subnormals()
    VitalHost()
    assert _subnormals()


def test_the_host_refuses_what_the_plugin_cannot_take(host: VitalHost) -> None:
    """An unknown id, a normalized value past 1, a render of no length: each the package's error."""
    with pytest.raises(UnknownParameterError):
        host.get(ParameterId("filter_1_cutofff"))
    with pytest.raises(ParameterRangeError):
        host.set(ParameterId("filter_1_cutoff"), 1.5)
    with pytest.raises(PluginRenderError):
        host.render([], 0, _RATE)
