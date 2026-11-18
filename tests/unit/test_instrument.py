"""The instrument over a fake plugin: every rule that needs no Vital to show it, so CI holds it.

`VitalInstrument` is built here over a real `VitalHost` on a stand-in for pedalboard's plugin,
`_FakeVital`, which hosts all 903 parameters, keeps the text it was last given and the floats set
since, and records every call. So the instrument reaches its plugin only through the host here
too, and core's thirteen contract tests run against it on any machine. A pass here is a pass over
the fake plugin: what Vital itself does is `tests/integration/test_vital_instrument.py`'s.

The fake can answer a load as Vital was seen to: take it, have pedalboard refuse it, raise its
alert with the text taken or not, or ignore it. A stand-in watch (`builders.StandInWatch`) is in
place of the one that answers the alert, so these run alike on macOS and without AppKit. The
host's marker shows among the fake's sets and nowhere else; `_sets` leaves it out.

An expected value is written out or worked out from primitives, `Fraction`, `struct` and the
scale's and the curve's formulas restated, never from the map's `to_preset` or `to_normalized`
and never from the instrument.
"""

import json
import math
import platform
import struct
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pedalboard
import pytest
from builders import StandInWatch, what_a_set_holds
from numpy.typing import NDArray
from patchbay import (
    Event,
    EventBus,
    Instrument,
    Note,
    ParameterChanged,
    ParameterId,
    ParameterNotFoundError,
    Patch,
    PatchLoaded,
    PatchRejectedError,
    Pattern,
    PresetKey,
    Quantity,
    RenderCompleted,
    RenderFailedError,
    RenderRequest,
    SubscriberFailedError,
    Unit,
    UnitMismatchError,
    ValueOutOfRangeError,
)
from patchbay.testing import CONTRACT_TESTS, RecordingSubscriber
from patchbay.testing.contract_tests import ContractTest

from patchbay_vital import dumps, loads
from patchbay_vital import host as host_module
from patchbay_vital.errors import (
    MapMismatchError,
    ParameterRangeError,
    ParameterUnitError,
    PatchRefusedError,
    PluginRenderError,
    PluginStateError,
    PluginThreadError,
    RenderRefusedError,
    UnknownParameterError,
    VitalError,
)
from patchbay_vital.format import split_modulations
from patchbay_vital.host import MARKER, VitalHost, _floats
from patchbay_vital.instrument import (
    FULL_SCALE,
    LOADS,
    MAX_SAMPLE_RATE,
    MAX_SAMPLES,
    MIN_SAMPLE_RATE,
    VitalInstrument,
)
from patchbay_vital.parameters import MappedParameter, parameter_map
from patchbay_vital.patch import PRESET_ENTRY, check_loadable, patch_of
from patchbay_vital.preset import VitalPreset, VitalSettings
from patchbay_vital.start import start_preset
from patchbay_vital.state import PluginState, unwrap, wrap

_PARAMETERS = 903
_BOUNDS = 2 * _PARAMETERS
_OFF_GRID_DEFAULTS = 22
_STEPS_FROM_ITS_START = 2  # float32 steps from chorus_feedback's 0.4 to what a set of it holds
_RATE = 48000
_CONTAINERS: dict[str, object] = {  # Vital 1.6.4's, as tests/unit/test_state.py measured them
    "class_id": b"56535456697461766974616C00000000",
    "container_version": 1,
    "wrapper_version": 1,
    "bypass": 0,
    "bank_version": 2,
    "plugin_id": b"Vita",
    "plugin_version": 0x00010604,
    "programs": 0,
    "reserved": bytes(128),
    "trailer": bytes(17) + b"JUCEPrivateData",
}
_ALERT = ("Error opening preset", "a stand-in's words")
_PATTERN = Pattern(
    tempo_bpm=120.0,
    bars=1,
    beats_per_bar=4,
    notes=(Note(pitch=60, velocity=100, start_beats=0.0, duration_beats=1.0, channel=0),),
)
_REQUEST = RenderRequest(sample_rate=_RATE, tail_seconds=0.25)
_SAMPLES = 108000  # one bar at 120 bpm and a quarter second, at 48 kHz


class _FakeParameter:
    """One of pedalboard's parameter wrappers over the fake plugin."""

    def __init__(self, plugin: "_FakeVital", record: MappedParameter) -> None:
        self._plugin = plugin
        self._record = record

    @property
    def name(self) -> str:
        return self._record.parameter.label

    @property
    def raw_value(self) -> float:
        return self._plugin.read(self._record)

    @raw_value.setter
    def raw_value(self, value: float) -> None:
        self._plugin.write(self._record, value)

    def get_text_for_raw_value(self, _raw_value: float) -> str:
        return ""


class _FakeVital:
    """pedalboard's plugin as the host sees it: 903 parameters, and a preset's text as its state.

    A set holds the scale's own value for the normalized value sent, as Vital does. A load keeps
    the text and forgets the sets before it, and a parameter then reads as the text holds it, or
    at its default where the text lacks it. `refusing` names the calls it raises on;
    `load_script`, while it has entries, says load by load what becomes of it: False, taken;
    True, refused by pedalboard; "alert", taken and then answered with the alert; "alert first",
    answered with the alert and not taken; "ignore", nothing at all; an error from outside the
    package, raised as itself, nothing taken. `raising_at_read`, a count and an error, raises the
    error at that read of the marker, counted by `marker_reads`. `audio` makes what a render
    gives.
    """

    name, version = "Vital", "1.6.4"

    def __init__(self, _path: str) -> None:
        self.watch = StandInWatch()
        self.text = b'{"settings":{}}'
        self.floats: dict[str, float] = {}
        self.normalized: dict[str, float] = {}
        self.loads: list[bytes] = []
        self.sets: list[tuple[str, float]] = []
        self.renders: list[tuple[list[tuple[bytes, float]], float, int]] = []
        self.refusing: set[str] = set()
        self.load_script: list[bool | str | BaseException] = []
        self.marker_reads = 0
        self.raising_at_read: tuple[int, BaseException] | None = None
        self.audio: Callable[[int], NDArray[np.float32]] | None = None
        self._hosted = {
            record.host_id: _FakeParameter(self, record) for record in parameter_map().parameters
        }

    @property
    def parameters(self) -> dict[str, _FakeParameter]:
        return self._hosted

    def read(self, record: MappedParameter) -> float:
        """Return a parameter's normalized value: what was set, or what the text holds for it."""
        if record.id == MARKER:
            self.marker_reads += 1
            if self.raising_at_read is not None and self.raising_at_read[0] == self.marker_reads:
                raise self.raising_at_read[1]
        if record.id in self.normalized:
            return self.normalized[record.id]
        held = json.loads(self.text)["settings"].get(record.preset_key, record.preset_default)
        return record.scale.to_normalized(held)

    def write(self, record: MappedParameter, value: float) -> None:
        if "set" in self.refusing:
            msg = "the plugin refuses the value"
            raise RuntimeError(msg)
        self.sets.append((record.id, value))
        self.normalized[record.id] = value
        self.floats[record.preset_key] = record.scale.to_preset(value)

    @property
    def preset_data(self) -> bytes:
        state = json.loads(self.text)
        state["settings"].update(self.floats)
        text = json.dumps(state).encode("utf-8")
        return wrap(PluginState.model_validate({**_CONTAINERS, "text": text}))

    @preset_data.setter
    def preset_data(self, data: bytes) -> None:
        how = self.load_script.pop(0) if self.load_script else "load" in self.refusing
        if isinstance(how, BaseException):
            raise how
        if how is True:
            msg = "the plugin refuses the state"
            raise RuntimeError(msg)
        if how == "ignore":
            return
        if how == "alert first":
            self.watch.alert(*_ALERT)
            return
        self.text = unwrap(data).text
        self.floats = {}
        self.normalized = {}
        self.loads.append(self.text)
        if how == "alert":
            self.watch.alert(*_ALERT)

    def process(
        self, midi: list[tuple[bytes, float]], duration: float, sample_rate: int
    ) -> NDArray[np.float32]:
        if "render" in self.refusing:
            msg = "the plugin refuses the render"
            raise RuntimeError(msg)
        self.renders.append((midi, duration, sample_rate))
        samples = int(duration * sample_rate)
        if self.audio is not None:
            return self.audio(samples)
        return np.zeros((2, samples), dtype=np.float32)


@pytest.fixture
def plugin(monkeypatch: pytest.MonkeyPatch) -> _FakeVital:
    """Return the fake plugin the test's host loads, on the machine the map was measured on."""
    fake = _FakeVital("")
    monkeypatch.setattr(platform, "machine", lambda: parameter_map().machine)
    monkeypatch.setattr(pedalboard, "VST3Plugin", lambda _path: fake)
    monkeypatch.setattr(host_module, "_ALERTS", fake.watch)
    return fake


@pytest.fixture
def host(plugin: _FakeVital, tmp_path: Path) -> VitalHost:
    """Return a real host over the fake plugin, found at a path that exists."""
    del plugin  # asked for so that pedalboard is replaced before the host loads
    return VitalHost(tmp_path)


@pytest.fixture
def bus() -> EventBus:
    """Give each test a bus no other test has published on."""
    return EventBus()


@pytest.fixture
def instrument(bus: EventBus, host: VitalHost) -> VitalInstrument:
    """Give each test a new instrument over the fake plugin, publishing on its bus."""
    return VitalInstrument(bus, host)


def _recorder(bus: EventBus) -> RecordingSubscriber:
    recorder = RecordingSubscriber()
    bus.subscribe(None, recorder)
    return recorder


def _float32(value: float) -> float:
    """Return the float32 nearest a double, by `struct`."""
    held: float = struct.unpack("<f", struct.pack("<f", value))[0]
    return held


def _float32_toward_zero(value: float) -> float:
    """Return the float32 next to a float32 that is not zero, toward zero, by its bits.

    One less in the float32's own bits. `math.nextafter` steps a double, and the double next to a
    float32 rounds back to that float32.
    """
    (bits,) = struct.unpack("<I", struct.pack("<f", value))
    stepped: float = struct.unpack("<f", struct.pack("<I", bits - 1))[0]
    return stepped


def _sets(plugin: _FakeVital) -> list[tuple[str, float]]:
    """Return the sets the plugin was sent, less the host's marker, which no model knows of."""
    return [made for made in plugin.sets if made[0] != MARKER]


def _state_floats(instrument: VitalInstrument) -> dict[str, float]:
    """Return the plugin's own floats, through the diagnostic read."""
    return _floats(instrument.host.state())


def _model_floats(preset: VitalPreset) -> dict[str, float]:
    _, slots = split_modulations(preset.modulations)
    return {str(key): held for key, held in (*preset.settings.values.items(), *slots.items())}


def _holding(**floats: float) -> VitalPreset:
    """Return the start preset with some settings floats replaced."""
    start = start_preset()
    values = {**start.settings.values, **{PresetKey(key): held for key, held in floats.items()}}
    return start.model_copy(update={"settings": VitalSettings(values=values)})


def _quantity(value: float, unit: Unit = Unit.none) -> Quantity:
    return Quantity(value=value, unit=unit)


# --- the contract --------------------------------------------------------------------------------


@pytest.mark.parametrize("contract_test", CONTRACT_TESTS, ids=lambda test: test.__name__)
def test_contract_against_a_fake_plugin(
    contract_test: ContractTest, instrument: Instrument, bus: EventBus
) -> None:
    """Each of core's contract tests passes over the fake plugin; this is not a pass on Vital."""
    contract_test(instrument, bus)


# --- how it starts -------------------------------------------------------------------------------


def test_it_starts_on_the_start_preset_loaded_into_the_plugin_twice(
    bus: EventBus, host: VitalHost, plugin: _FakeVital
) -> None:
    """The model is the package's preset, never the plugin's state, and nothing is published."""
    plugin.text = b'{"settings":{"volume":1.0}}'  # whatever the plugin held is replaced, not read
    recorder = _recorder(bus)
    instrument = VitalInstrument(bus, host)
    checked: Instrument = instrument
    assert isinstance(checked, Instrument)
    assert instrument.name == "Vital"
    assert instrument.preset is start_preset()
    assert instrument.host is host
    start_text = dumps(start_preset()).encode("utf-8")
    assert plugin.loads == [start_text] * LOADS
    assert LOADS == 2  # noqa: PLR2004 - the measured workaround, by its own number
    assert recorder.events == ()
    assert _state_floats(instrument) == _model_floats(start_preset())


def test_its_parameters_are_the_map_s_903_in_the_map_s_order(instrument: VitalInstrument) -> None:
    """Every hosted parameter, sorted by id, each the map's own `Parameter`."""
    parameters = instrument.parameters()
    assert len(parameters) == _PARAMETERS
    assert [parameter.id for parameter in parameters] == sorted(p.id for p in parameters)
    assert parameters == tuple(record.parameter for record in parameter_map().parameters)
    assert (parameters[0].id, parameters[-1].id) == ("beats_per_minute", "volume")


def test_the_map_is_refused_where_the_instrument_is_built_on_another_machine(
    bus: EventBus, host: VitalHost, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The map is the machine's it was measured on: another is named before anything is loaded."""
    monkeypatch.setattr(platform, "machine", lambda: "a machine the map was not measured on")
    with pytest.raises(MapMismatchError) as caught:
        VitalInstrument(bus, host)
    assert caught.value.what == "machine"


# --- get and set ---------------------------------------------------------------------------------


def test_get_is_the_display_of_the_model_s_float_and_a_default_where_the_key_is_absent(
    instrument: VitalInstrument,
) -> None:
    """A new instrument shows every default; a key the preset lacks reads as its default."""
    for parameter in instrument.parameters():
        assert instrument.get(parameter.id) == parameter.default
    values = dict(start_preset().settings.values)
    del values[PresetKey("volume")]
    slots = tuple(slot.model_copy(update={"ramp_up": None}) for slot in start_preset().modulations)
    older = start_preset().model_copy(
        update={"settings": VitalSettings(values=values), "modulations": slots}
    )
    instrument.load_patch(patch_of(older))
    by_id = {parameter.id: parameter for parameter in instrument.parameters()}
    for name in ("volume", "modulation_1_ramp_up", "modulation_64_ramp_up"):
        assert instrument.get(ParameterId(name)) == by_id[ParameterId(name)].default
    assert PresetKey("volume") not in instrument.preset.settings.values


def test_every_bound_of_every_parameter_comes_back_exactly(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Core's clause at a bound, counted: all 1,806, and the plugin was sent 0 or 1 for each."""
    counted = 0
    for parameter in instrument.parameters():
        for bound, normalized in ((parameter.maximum, 1.0), (parameter.minimum, 0.0)):
            value = _quantity(bound, parameter.unit)
            if instrument.get(parameter.id) != value:
                instrument.set(parameter.id, value)
                assert plugin.sets[-1] in (
                    (parameter.id, normalized),
                    (parameter.id, 1 - normalized),
                )
            assert instrument.get(parameter.id) == value
            counted += 1
    assert counted == _BOUNDS


def test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Finding 1 of core's review of its PR 19, decided: `beats_per_minute` at 216.85141355537831.

    60 bpm is 1 in the preset, on a scale from the float32 of 1/3 to 5. The float32 nearest the
    display over 60 is 3.6141903400421143, which no normalized value lands on; the normalized
    value nearest it lands on 3.6141905784606934, the float32 above it, shown as
    216.8514347076416, where the float32 below it, 3.614190101623535, shown as 216.8514060974121,
    is one a set lands on and is nearer the display given. All worked out here.
    """
    given = 216.85141355537831
    own = _float32(given / 60.0)
    normalized, held = what_a_set_holds(own, _float32(1 / 3), 5.0)
    assert (own, held) == (3.6141903400421143, 3.6141905784606934)
    below = _float32_toward_zero(own)
    assert (below, below * 60.0) == (3.614190101623535, 216.8514060974121)
    assert what_a_set_holds(below, _float32(1 / 3), 5.0)[1] == below  # a set of it lands on it
    assert abs(below * 60.0 - given) < abs(held * 60.0 - given)
    recorder = _recorder(bus)
    old = instrument.get(ParameterId("beats_per_minute"))
    instrument.set(ParameterId("beats_per_minute"), _quantity(given, Unit.bpm))
    shown = _quantity(216.8514347076416, Unit.bpm)
    assert shown.value == held * 60.0
    assert instrument.get(ParameterId("beats_per_minute")) == shown
    assert instrument.preset.settings.values[PresetKey("beats_per_minute")] == held
    assert _sets(plugin) == [("beats_per_minute", normalized)]
    assert _state_floats(instrument)["beats_per_minute"] == held
    (changed,) = recorder.of_type(ParameterChanged)
    assert (changed.id, changed.old, changed.new) == ("beats_per_minute", old, shown)
    instrument.set(ParameterId("beats_per_minute"), shown)  # a value a set left it holding
    assert instrument.get(ParameterId("beats_per_minute")) == shown


@pytest.mark.parametrize(
    "case",
    [
        ("chorus_voices", 6.0, 8.0, 2.0),  # 1.5 in fours: a tie, away from zero
        ("chorus_voices", 5.0, 4.0, 1.0),  # 1.25 in fours
        ("oversampling", 3.0, 4.0, 2.0),  # log2(3) is 1.58, the step of 4
    ],
    ids=["chorus_voices 6", "chorus_voices 5", "oversampling 3"],
)
def test_a_value_between_steps_is_taken_and_the_nearest_step_held(
    bus: EventBus, instrument: VitalInstrument, case: tuple[str, float, float, float]
) -> None:
    """Finding 4, decided: `get` and the event's `new` carry the step's display.

    Each case is the parameter, the value given, the display then shown and the preset held.
    """
    name, given, shown, held = case
    recorder = _recorder(bus)
    instrument.set(ParameterId(name), _quantity(given))
    assert instrument.get(ParameterId(name)) == _quantity(shown)
    assert recorder.of_type(ParameterChanged)[0].new == _quantity(shown)
    assert instrument.preset.settings.values[PresetKey(name)] == held
    assert _state_floats(instrument)[name] == held


def test_a_set_of_the_value_already_shown_keeps_what_is_held(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The keep rule, on the 22 defaults the scale does not hold, counted.

    Each is a float no normalized value lands on, so a set of its own display would hold a
    neighbour. It keeps the float, in the model and the plugin, and is published all the same.
    The rule's other side is the next test's.
    """
    off_grid = [r for r in parameter_map().parameters if not r.scale.holds(r.preset_default)]
    assert len(off_grid) == _OFF_GRID_DEFAULTS
    recorder = _recorder(bus)
    before = instrument.preset
    for record in off_grid:
        shown = instrument.get(record.id)
        instrument.set(record.id, shown)
        assert instrument.get(record.id) == shown
    assert instrument.preset is before
    assert _sets(plugin) == []
    events = recorder.of_type(ParameterChanged)
    assert len(recorder.events) == len(events) == _OFF_GRID_DEFAULTS
    assert all(event.old == event.new for event in events)


def test_a_set_of_the_value_already_shown_on_a_float_a_set_lands_on_reaches_the_plugin(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """PR 23's finding 1: the plugin holds another float than the model's, and a set mends it.

    As Vital upgrades a preset older than it (issue #22), the model holds `osc_1_stack_style` 9
    where the plugin holds 10. 9 is a step of the scale, 0 to 12, so a set of the value shown
    reaches the plugin, sent 9 / 12 = 0.75, and the plugin holds 9 again. Published once, `old`
    equal to `new`.
    """
    stack = ParameterId("osc_1_stack_style")
    instrument.load_patch(Patch(instrument="Vital", values={stack: _quantity(9.0)}))
    plugin.floats["osc_1_stack_style"] = 10.0  # the plugin's own upgrade, which the model keeps
    assert _state_floats(instrument)["osc_1_stack_style"] == 10.0  # noqa: PLR2004 - Vital's
    recorder = _recorder(bus)
    instrument.set(stack, _quantity(9.0))
    assert _sets(plugin) == [("osc_1_stack_style", 0.75)]
    assert _state_floats(instrument)["osc_1_stack_style"] == 9.0  # noqa: PLR2004 - the model's
    assert instrument.preset.settings.values[PresetKey("osc_1_stack_style")] == 9.0  # noqa: PLR2004
    (changed,) = recorder.events
    assert isinstance(changed, ParameterChanged)
    assert changed.old == changed.new == _quantity(9.0)


def test_a_set_of_the_value_shown_on_an_upgraded_float_no_set_lands_on_leaves_the_plugin_upgraded(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Finding A of PR 23's second review: the one upgraded float a set of its value cannot mend.

    On Oolacile Evil Dubstep Bass the model holds `modulation_10_amount` at 0.19999998807907104
    where Vital plays 0.07499999552965164 (issue #22; `tests/data/upgraded-floats.txt`, line 49).
    The model's float is one no normalized value lands on, worked out here from primitives: on
    the scale from -1 to 1 a set of it would hold 0.20000004768371582, two float32 steps up. So
    the keep rule keeps it. The plugin is not called and goes on holding its upgraded float, the
    model is the same object, and the set is published all the same, `old` equal to `new`.
    Nothing the host can set puts the plugin on the model's float: what the model should hold
    for such a preset is issue #22's to decide.
    """
    amount = ParameterId("modulation_10_amount")
    in_file, upgraded = 0.19999998807907104, 0.07499999552965164
    assert (_float32(in_file), _float32(upgraded)) == (in_file, upgraded)
    _, a_set_holds = what_a_set_holds(in_file, -1.0, 1.0)
    assert a_set_holds == 0.20000004768371582 != in_file  # noqa: PLR2004 - its neighbour
    start = start_preset()
    slots = list(start.modulations)
    slots[9] = slots[9].model_copy(update={"amount": in_file})
    instrument.load_patch(patch_of(start.model_copy(update={"modulations": tuple(slots)})))
    assert instrument.preset.modulations[9].amount == in_file
    plugin.floats["modulation_10_amount"] = upgraded  # the plugin's own upgrade, the model's kept
    recorder = _recorder(bus)
    before = instrument.preset
    shown = instrument.get(amount)
    assert shown == _quantity(in_file)
    instrument.set(amount, shown)
    assert _sets(plugin) == []
    assert _state_floats(instrument)["modulation_10_amount"] == upgraded
    assert instrument.preset is before
    assert instrument.get(amount) == shown
    (changed,) = recorder.events
    assert isinstance(changed, ParameterChanged)
    assert changed.old == changed.new == shown


def test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour(
    instrument: VitalInstrument,
) -> None:
    """The case the keep rule leaves, held as it is today, for core's wording to decide.

    The issue drafted for fromtheoutfit/patchbay in this spec's shape.md, "Instrument.get: a value
    `get` has returned is not always one `set` lands on", asks what "at any value `get` has
    returned for it that `set` takes" promises here. `chorus_feedback` starts on 0.4 as a float32,
    0.4000000059604645, which no normalized value lands on. `get` returns its display; another
    value is set; that display is set back. The parameter then holds the float32 a set of 0.4
    lands on, worked out here from primitives, two float32 steps from the float it started on,
    and `get` returns that one's display, not the value given. A change to the rule changes this
    test.
    """
    feedback = ParameterId("chorus_feedback")
    started = _float32(0.4)
    assert instrument.preset.settings.values[PresetKey("chorus_feedback")] == started
    first = instrument.get(feedback)
    assert first == _quantity(started * 100.0, Unit.percent)
    instrument.set(feedback, _quantity(10.0, Unit.percent))
    instrument.set(feedback, first)
    _, held = what_a_set_holds(started, _float32(-0.95), _float32(0.95))
    steps = abs(
        struct.unpack("<i", struct.pack("<f", held))[0]
        - struct.unpack("<i", struct.pack("<f", started))[0]
    )
    assert steps == _STEPS_FROM_ITS_START
    assert instrument.preset.settings.values[PresetKey("chorus_feedback")] == held
    assert instrument.get(feedback) == _quantity(held * 100.0, Unit.percent) != first


def test_a_set_reaches_a_slot_s_float_and_the_model_stays_a_preset_that_reads_back(
    instrument: VitalInstrument,
) -> None:
    """A slot float, one an older file lacks among them, is set in its slot and nowhere else."""
    instrument.set(ParameterId("modulation_3_amount"), _quantity(-1.0))
    ramp = parameter_map().find(ParameterId("modulation_64_ramp_up"))
    instrument.set(ramp.id, _quantity(ramp.parameter.maximum, Unit.seconds))
    instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    preset = instrument.preset
    assert preset.modulations[2].amount == -1.0
    assert preset.modulations[63].ramp_up == ramp.scale.maximum != ramp.preset_default
    assert preset.settings.values[PresetKey("volume")] == 0.0
    assert preset.modulations[0] == start_preset().modulations[0]
    assert loads(dumps(preset)) == preset


# --- what it refuses -----------------------------------------------------------------------------


def test_a_set_it_refuses_is_the_package_s_error_with_core_s_fields_and_core_s_error_its_cause(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The fields the contract tests compare, met one for one, and the unit and bounds the map's."""
    recorder = _recorder(bus)
    volume = next(p for p in instrument.parameters() if p.id == "volume")
    with pytest.raises(ParameterUnitError) as wrong_unit:
        instrument.set(volume.id, _quantity(0.0, Unit.percent))
    unit = wrong_unit.value
    assert isinstance(unit, UnitMismatchError)
    assert isinstance(unit, VitalError)
    assert (unit.parameter_id, unit.expected, unit.given) == ("volume", Unit.db, Unit.percent)
    assert type(unit.__cause__) is UnitMismatchError
    past = math.nextafter(volume.maximum, math.inf)
    with pytest.raises(ParameterRangeError) as out_of_range:
        instrument.set(volume.id, _quantity(past, Unit.db))
    error = out_of_range.value
    assert isinstance(error, ValueOutOfRangeError)
    assert (error.parameter_id, error.minimum, error.maximum, error.given) == (
        "volume",
        -80.0,
        volume.maximum,
        past,
    )
    assert (error.minimum, error.maximum) != (0.0, 1.0)  # never the host's normalized range
    assert type(error.__cause__) is ValueOutOfRangeError
    with pytest.raises(ParameterRangeError):
        instrument.set(ParameterId("filter_1_on"), _quantity(0.5))
    for call in (
        lambda: instrument.get(ParameterId("volume.unknown")),
        lambda: instrument.set(ParameterId("volume.unknown"), _quantity(0.0, Unit.db)),
    ):
        with pytest.raises(UnknownParameterError) as unknown:
            call()
        assert isinstance(unknown.value, ParameterNotFoundError)
        assert (unknown.value.parameter_id, unknown.value.instrument) == ("volume.unknown", "Vital")
    assert recorder.events == ()
    assert instrument.preset is start_preset()
    assert _sets(plugin) == []


def test_a_set_the_plugin_refuses_leaves_the_model_the_plugin_and_the_bus_as_they_were(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The checks pass and the plugin refuses: the host's error leaves the call, a VitalError."""
    recorder = _recorder(bus)
    before = _state_floats(instrument)
    plugin.refusing.add("set")
    with pytest.raises(PluginStateError) as caught:
        instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db))
    assert isinstance(caught.value, VitalError)
    assert instrument.preset is start_preset()
    assert _state_floats(instrument) == before
    assert recorder.events == ()


def test_a_subscriber_that_raises_leaves_the_set_made_and_published(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """The bus raises after every subscriber ran; the change was made before it was published."""
    seen: list[Quantity] = []

    def failing(event: Event) -> None:
        seen.append(instrument.get(ParameterId("volume")))
        raise RuntimeError(event.name)

    bus.subscribe(None, failing)
    with pytest.raises(SubscriberFailedError):
        instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    assert seen == [_quantity(-80.0, Unit.db)]  # the handler already reads the new value
    assert instrument.get(ParameterId("volume")) == _quantity(-80.0, Unit.db)


# --- patches -------------------------------------------------------------------------------------


def test_a_preset_holding_a_float_outside_its_bounds_is_shown_refused_on_set_and_carried(
    instrument: VitalInstrument,
) -> None:
    """`flanger_dry_wet` at 0.7072, as presets Vital ships hold it, through the whole instrument.

    `get` returns its true display, 141.44 against 0 to 100; a set of that display is refused;
    `patch()` leaves it out of `values` and `load_patch` gives the same model back; and a set of
    50 % brings it into `values`, gone from `opaque`.
    """
    dry_wet = ParameterId("flanger_dry_wet")
    held = _float32(0.7072)
    preset = _holding(flanger_dry_wet=held)
    instrument.load_patch(patch_of(preset))
    shown = instrument.get(dry_wet)
    assert shown == _quantity(held * 200.0, Unit.percent)
    assert round(shown.value, 2) == 141.44  # noqa: PLR2004 - the figure the issue gives
    with pytest.raises(ParameterRangeError) as caught:
        instrument.set(dry_wet, shown)
    assert (caught.value.minimum, caught.value.maximum, caught.value.given) == (
        0.0,
        100.0,
        shown.value,
    )
    patch = instrument.patch()
    assert dry_wet not in patch.values
    assert json.loads(patch.opaque[PRESET_ENTRY])["settings"] == {"flanger_dry_wet": held}
    instrument.load_patch(Patch.model_validate_json(patch.model_dump_json()))
    assert dumps(instrument.preset) == dumps(preset)
    assert instrument.patch() == patch
    instrument.set(dry_wet, _quantity(50.0, Unit.percent))
    after = instrument.patch()
    assert after.values[dry_wet] == _quantity(50.0, Unit.percent)
    assert json.loads(after.opaque[PRESET_ENTRY])["settings"] == {}
    assert len(after.values) == _PARAMETERS


def test_a_patch_of_values_alone_loads_as_the_start_preset_with_those_values(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The short form: whatever the instrument held, what the patch does not name is the start's."""
    instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    recorder = _recorder(bus)
    values = {
        ParameterId("filter_1_on"): _quantity(1.0),
        ParameterId("filter_1_cutoff"): _quantity(12.0, Unit.semitones),
    }
    instrument.load_patch(Patch(instrument="Vital", values=values))
    expected = _holding(filter_1_on=1.0, filter_1_cutoff=72.0)
    assert dumps(instrument.preset) == dumps(expected)
    assert instrument.get(ParameterId("volume")) == _quantity(
        start_preset().settings.values[PresetKey("volume")] ** 0.5 - 80.0, Unit.db
    )
    assert plugin.loads[-LOADS:] == [dumps(expected).encode("utf-8")] * LOADS
    assert _state_floats(instrument) == _model_floats(expected)
    (loaded,) = recorder.events
    assert isinstance(loaded, PatchLoaded)
    assert (loaded.instrument, loaded.parameter_count) == ("Vital", len(values))


_SAMPLE_SEED = 23
_SAMPLE_ROUNDS = 25
_BOUND_ROUNDS = 2  # every group's minimum, then every group's maximum
_SAMPLE_GROUPS = 55


def test_an_arbitrary_display_in_a_patch_holds_what_a_set_of_it_holds(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """PR 23's findings 2 and 3, on a labelled sample: a load and a set leave the same float.

    One record of each of the map's 55 continuous groups, a scale and a curve. 25 displays each
    are drawn by `numpy.random.default_rng(23).uniform` over the parameter's bounds, and each
    bound is taken too: 27 rounds of 55, 1,485 displays. Each display in a patch of values alone
    holds the very float a set of it holds, the sign of a zero included.

    The set is made from another value, on the start preset and before the load, and each is
    counted at the plugin (finding B of PR 23's second review). Made after the load, a set of a
    display the loaded float shows is the keep rule's no-op, and the load then agrees with it
    whatever float it took. That takes a display two floats show, which is why the bounds are in
    the sample: `volume`'s minimum is one, shown by 0 and by the float32 next above it, and a
    uniform draw never lands there. A sample, not a count; the one display that differs, one
    that is exactly an off-grid float's own, is the next test's.
    """
    groups: dict[str, MappedParameter] = {}
    for record in parameter_map().parameters:
        if record.parameter.kind == "continuous":
            key = record.scale.model_dump_json() + record.curve.model_dump_json()
            groups.setdefault(key, record)
    assert len(groups) == _SAMPLE_GROUPS
    rng = np.random.default_rng(_SAMPLE_SEED)
    rounds = [
        {
            record.id: float(rng.uniform(record.parameter.minimum, record.parameter.maximum))
            for record in groups.values()
        }
        for _ in range(_SAMPLE_ROUNDS)
    ]
    rounds.append({record.id: record.parameter.minimum for record in groups.values()})
    rounds.append({record.id: record.parameter.maximum for record in groups.values()})
    units = {record.id: record.parameter.unit for record in groups.values()}
    compared = 0
    for displays in rounds:
        values = {
            parameter_id: _quantity(display, units[parameter_id])
            for parameter_id, display in displays.items()
        }
        instrument.load_patch(Patch(instrument="Vital", values={}))
        sent = len(plugin.sets)
        for parameter_id, value in values.items():
            instrument.set(parameter_id, value)
        assert len(plugin.sets) - sent == len(values)  # each reached the plugin: none was kept
        set_holds = _model_floats(instrument.preset)
        instrument.load_patch(Patch(instrument="Vital", values=values))
        loaded = _model_floats(instrument.preset)
        for parameter_id, value in values.items():
            taken, held = loaded[parameter_id], set_holds[parameter_id]
            assert struct.pack("<d", taken) == struct.pack("<d", held), (parameter_id, value)
            compared += 1
    assert compared == (_SAMPLE_ROUNDS + _BOUND_ROUNDS) * _SAMPLE_GROUPS


def test_a_display_that_is_an_off_grid_float_s_own_is_restored_by_a_load_and_not_by_a_set(
    instrument: VitalInstrument,
) -> None:
    """The one case where a load and a set differ, fromtheoutfit/patchbay#20's.

    `chorus_feedback` starts on the float32 of 0.4, which no normalized value lands on. Its
    display names it: a patch carrying that display restores it, as a patch the instrument gave
    restores every float it carried. A set of the same display holds the float32 a set of 0.4
    lands on, worked out here from primitives, which "Instrument.get: a value `get` has returned
    is not always one `set` lands on" asks core's clause about.
    """
    feedback = ParameterId("chorus_feedback")
    started = _float32(0.4)
    first = instrument.get(feedback)
    instrument.set(feedback, _quantity(10.0, Unit.percent))
    instrument.load_patch(Patch(instrument="Vital", values={feedback: first}))
    assert instrument.preset.settings.values[PresetKey("chorus_feedback")] == started
    assert instrument.get(feedback) == first
    instrument.set(feedback, _quantity(10.0, Unit.percent))
    instrument.set(feedback, first)
    _, held = what_a_set_holds(started, _float32(-0.95), _float32(0.95))
    assert held != started
    assert instrument.preset.settings.values[PresetKey("chorus_feedback")] == held


def test_a_patch_is_built_once_for_each_model(instrument: VitalInstrument) -> None:
    """PR 23's finding 8: the same object until a set or a load replaces the model."""
    first = instrument.patch()
    assert instrument.patch() is first
    instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    after_set = instrument.patch()
    assert after_set is not first
    assert after_set.values[ParameterId("volume")] == _quantity(-80.0, Unit.db)
    assert instrument.patch() is after_set
    instrument.load_patch(first)
    after_load = instrument.patch()
    assert after_load is not after_set
    assert after_load == first


def test_parameter_count_is_the_number_of_values_in_the_patch_given(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """For a whole patch, a patch of values alone, and one whose float rides in `opaque`."""
    recorder = _recorder(bus)
    whole = instrument.patch()
    instrument.load_patch(whole)
    instrument.load_patch(Patch(instrument="Vital", values={}))
    instrument.load_patch(patch_of(_holding(flanger_dry_wet=_float32(0.7072))))
    counts = [event.parameter_count for event in recorder.of_type(PatchLoaded)]
    assert counts == [_PARAMETERS, 0, _PARAMETERS - 1]
    assert len(recorder.events) == len(counts)  # no ParameterChanged for a load


def test_a_patch_refused_part_way_leaves_the_model_the_plugin_and_the_bus_as_they_were(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """A whole patch, every value moved, bad only at its last entry: nothing of it is taken.

    Unlike the contract test's patch of values alone, this one carries its `preset` entry and
    its sections, so nothing but the last value refuses it.
    """
    instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db))
    before, state, loads_made = instrument.preset, _state_floats(instrument), len(plugin.loads)
    recorder = _recorder(bus)
    whole = instrument.patch()
    moved = {
        parameter.id: _quantity(
            parameter.maximum
            if whole.values[parameter.id].value != parameter.maximum
            else parameter.minimum,
            parameter.unit,
        )
        for parameter in instrument.parameters()
    }
    last = max(moved)
    bad = [
        {**moved, last: _quantity(0.0, Unit.percent)},
        {**moved, last: _quantity(math.nextafter(-80.0, -math.inf), Unit.db)},
        {**moved, ParameterId(f"{last}.unknown"): _quantity(0.0, Unit.db)},
    ]
    for values in bad:
        with pytest.raises(PatchRefusedError) as caught:
            instrument.load_patch(Patch(instrument="Vital", values=values, opaque=whole.opaque))
        assert isinstance(caught.value, PatchRejectedError)
        assert caught.value.reason.startswith("volume")
        assert instrument.preset is before
        assert _state_floats(instrument) == state
    assert len(plugin.loads) == loads_made
    assert recorder.events == ()


def test_a_load_the_plugin_refuses_puts_the_model_s_text_back_and_is_refused_as_a_patch(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The first of the two loads is taken and the second refused: the plugin is put back.

    The package's patch error leaves the call, chained from the host's, and the plugin, read
    through the diagnostic read, holds the model's floats again, not the refused patch's.
    """
    instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db))
    before, state = instrument.preset, _state_floats(instrument)
    recorder = _recorder(bus)
    plugin.load_script = [False, True, False, False]  # the patch once, refused, the model back
    patch = Patch(instrument="Vital", values={ParameterId("volume"): _quantity(-80.0, Unit.db)})
    with pytest.raises(PatchRefusedError) as caught:
        instrument.load_patch(patch)
    assert isinstance(caught.value, VitalError)
    assert type(caught.value.__cause__) is PluginStateError
    assert caught.value.reason.startswith("the plugin refused the preset: ")
    assert instrument.preset is before
    assert _state_floats(instrument) == state
    assert plugin.loads[-LOADS:] == [dumps(before).encode("utf-8")] * LOADS
    assert recorder.events == ()


_LOST = (
    "the plugin refused a preset (the plugin refuses the state) and then the model's own text "
    "(the plugin refuses the state), so its state is unknown while the model holds the preset "
    "before"
)


def _lose_step(instrument: VitalInstrument, plugin: _FakeVital) -> None:
    """Have the plugin refuse a load and the model's own text after it, then take loads again."""
    plugin.refusing.add("load")
    with pytest.raises(PluginStateError):
        instrument.load_patch(Patch(instrument="Vital", values={}))
    plugin.refusing.clear()


def test_a_plugin_that_refuses_the_model_s_own_text_too_leaves_the_instrument_out_of_step(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """PR 23's finding 4: the package's PluginStateError, not core's PatchRejectedError.

    It names both refusals and says to build a new instrument, chained from the host's error for
    the second refusal: that is chained from what the plugin raised, raised while the first
    refusal was being handled. The model holds the preset before; nothing is published.
    """
    before = instrument.preset
    recorder = _recorder(bus)
    plugin.refusing.add("load")
    with pytest.raises(PluginStateError) as caught:
        instrument.load_patch(Patch(instrument="Vital", values={}))
    assert not isinstance(caught.value, PatchRejectedError)
    assert caught.value.reason == f"{_LOST}: build a new VitalInstrument"
    second = caught.value.__cause__
    assert isinstance(second, PluginStateError)
    raised = second.__cause__
    assert isinstance(raised, RuntimeError)
    first = raised.__context__
    assert isinstance(first, PluginStateError)  # the first refusal, kept
    assert first is not second
    assert instrument.preset is before
    assert recorder.events == ()


@pytest.mark.parametrize(
    "call",
    [
        lambda instrument: instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db)),
        lambda instrument: instrument.set(ParameterId("volume.unknown"), _quantity(0.0, Unit.db)),
        lambda instrument: instrument.load_patch(Patch(instrument="Vital", values={})),
        lambda instrument: instrument.load_patch(Patch(instrument="another", values={})),
        lambda instrument: instrument.render(_PATTERN, _REQUEST),
    ],
    ids=["set", "a set it would refuse", "load_patch", "a patch it would refuse", "render"],
)
def test_once_out_of_step_every_call_that_reaches_the_plugin_is_refused_before_anything_else(
    bus: EventBus,
    instrument: VitalInstrument,
    plugin: _FakeVital,
    call: Callable[[VitalInstrument], object],
) -> None:
    """Refused naming the earlier failure, even where its own checks would refuse it first.

    The plugin is not called, the model is not changed and nothing is published.
    """
    _lose_step(instrument, plugin)
    before, reached = instrument.preset, (len(plugin.loads), len(plugin.sets), len(plugin.renders))
    recorder = _recorder(bus)
    with pytest.raises(PluginStateError) as caught:
        call(instrument)
    assert caught.value.reason == (
        f"the instrument lost step with the plugin: {_LOST}; build a new one"
    )
    assert (len(plugin.loads), len(plugin.sets), len(plugin.renders)) == reached
    assert instrument.preset is before
    assert recorder.events == ()


def test_once_out_of_step_get_and_patch_answer_from_the_model(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """They read the model, the preset before, which the plugin may no longer match.

    The fake plugin keeps its state through a refused load, so what Vital is left holding is
    not shown here: the instrument does not read it either way.
    """
    instrument.set(ParameterId("volume"), _quantity(-80.0, Unit.db))
    shown, patch = instrument.get(ParameterId("volume")), instrument.patch()
    _lose_step(instrument, plugin)
    assert instrument.get(ParameterId("volume")) == shown == _quantity(-80.0, Unit.db)
    assert instrument.patch() == patch
    assert instrument.parameters() == tuple(r.parameter for r in parameter_map().parameters)


# --- a load Vital answers with its alert, or ignores ----------------------------------------------


def _answered(how: str) -> str:
    """Return the host's reason for a load the fake answered `how`."""
    if how == "ignore":
        return f"Vital ignored the state: {MARKER}, set before the load, was left as it was set"
    return f"Vital answered the state with its alert, {_ALERT[0]!r}: {_ALERT[1]!r}"


@pytest.mark.parametrize("how", ["alert", "alert first", "ignore"])
def test_a_load_vital_answers_with_its_alert_or_ignores_is_refused_and_the_model_s_text_put_back(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital, how: str
) -> None:
    """The host's error is met by the rollback that was there: refused as a patch, nothing kept.

    The plugin takes the alerting text in part, or not at all, or ignores the load; each way the
    model's own text is then loaded twice, and the plugin, through the diagnostic read, holds
    the model's floats, not the refused patch's. Nothing is published.
    """
    instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db))
    before, state = instrument.preset, _state_floats(instrument)
    recorder = _recorder(bus)
    plugin.load_script = [how, False, False]
    patch = Patch(instrument="Vital", values={ParameterId("volume"): _quantity(-80.0, Unit.db)})
    with pytest.raises(PatchRefusedError) as caught:
        instrument.load_patch(patch)
    assert isinstance(caught.value, PatchRejectedError)
    cause = caught.value.__cause__
    assert type(cause) is PluginStateError
    assert cause.reason == _answered(how)
    assert caught.value.reason == f"the plugin refused the preset: {_answered(how)}"
    assert instrument.preset is before
    assert _state_floats(instrument) == state
    assert plugin.loads[-LOADS:] == [dumps(before).encode("utf-8")] * LOADS
    assert plugin.load_script == []
    assert recorder.events == ()
    assert not plugin.watch.in_place


@pytest.mark.parametrize("how", ["alert", "alert first", "ignore"])
def test_a_rollback_vital_answers_the_same_way_leaves_the_instrument_out_of_step(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital, how: str
) -> None:
    """The model's own text alerting too, or ignored too: lost step, as for a refusal.

    `PluginStateError`, not core's `PatchRejectedError`, names both failures; the model holds
    the preset before, nothing is published, and every later load is refused before the plugin.
    """
    before = instrument.preset
    recorder = _recorder(bus)
    plugin.load_script = [how, how]
    with pytest.raises(PluginStateError) as caught:
        instrument.load_patch(Patch(instrument="Vital", values={}))
    assert not isinstance(caught.value, PatchRejectedError)
    assert caught.value.reason == (
        f"the plugin refused a preset ({_answered(how)}) and then the model's own text "
        f"({_answered(how)}), so its state is unknown while the model holds the preset before: "
        "build a new VitalInstrument"
    )
    assert type(caught.value.__cause__) is PluginStateError
    assert instrument.preset is before
    assert recorder.events == ()
    reached = (len(plugin.loads), len(plugin.sets))
    with pytest.raises(PluginStateError, match="lost step"):
        instrument.load_patch(Patch(instrument="Vital", values={}))
    assert (len(plugin.loads), len(plugin.sets)) == reached


def test_the_marker_is_the_plugin_s_alone_on_a_load_that_succeeds_and_on_one_that_fails(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The host sets it on the plugin; the model, `get`, `patch` and the bus never see it.

    The start preset holds the marker's parameter at 0, so each of its two loads planted 1. A
    preset holding it at 1 plants 0, and the model then holds the preset's own 1. A load that
    is then ignored plants and sets back at the plugin, and the model, the patch object and the
    bus are as they were.
    """
    assert MARKER == "filter_1_on"
    planted = [made for made in plugin.sets if made[0] == MARKER]
    assert planted == [(MARKER, 1.0)] * LOADS
    assert instrument.get(MARKER) == _quantity(0.0)
    recorder = _recorder(bus)

    instrument.load_patch(patch_of(_holding(filter_1_on=1.0)))
    planted = [made for made in plugin.sets if made[0] == MARKER]
    assert planted == [(MARKER, 1.0)] * LOADS + [(MARKER, 0.0)] * LOADS
    assert instrument.get(MARKER) == _quantity(1.0)
    assert instrument.preset.settings.values[PresetKey("filter_1_on")] == 1.0
    assert instrument.patch().values[MARKER] == _quantity(1.0)
    assert _state_floats(instrument)["filter_1_on"] == 1.0
    (loaded,) = recorder.events
    assert isinstance(loaded, PatchLoaded)

    held, patch, state = instrument.preset, instrument.patch(), _state_floats(instrument)
    plugin.load_script = ["ignore", False, False]
    with pytest.raises(PatchRefusedError):
        instrument.load_patch(patch_of(_holding(filter_1_on=0.0)))
    assert [made for made in plugin.sets if made[0] == MARKER][2 * LOADS :] == [
        (MARKER, 1.0),  # planted for a text that holds 0: where the plugin stood already
        (MARKER, 1.0),  # the load left it there, so it is set back to what it was
        (MARKER, 0.0),  # the model's own text, which holds 1, put back: its first load
        (MARKER, 0.0),  # and its second
    ]
    assert instrument.preset is held
    assert instrument.patch() is patch
    assert instrument.get(MARKER) == _quantity(1.0)
    assert _state_floats(instrument) == state
    assert recorder.events == (loaded,)
    assert not any(isinstance(event, ParameterChanged) for event in recorder.events)


def _on_a_second_thread(call: Callable[[], object]) -> VitalError:
    """Run a call on a thread named "a second thread"; return the VitalError it raised."""
    caught: list[VitalError] = []

    def run() -> None:
        try:
            call()
        except VitalError as error:
            caught.append(error)

    thread = threading.Thread(target=run, name="a second thread")
    thread.start()
    thread.join()
    (error,) = caught
    return error


def test_a_load_from_a_second_thread_changes_nothing_and_is_refused_as_a_patch(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The review of PR 26, finding 3: core's PatchRejectedError, chained from PluginThreadError.

    It says, in this order, that the call came from a thread the plugin cannot be loaded from
    on macOS, naming it; that the patch passed the package's own checks; and that it was not
    given to Vital, so whether Vital takes it is unknown. It is no state error, so no rollback
    answers it: nothing is changed or published, and the instrument has not lost step, so the
    same patch then loads from the main thread.
    """
    before, state = instrument.preset, _state_floats(instrument)
    reached = (len(plugin.loads), len(plugin.sets))
    recorder = _recorder(bus)
    patch = Patch(instrument="Vital", values={ParameterId("volume"): _quantity(-80.0, Unit.db)})
    error = _on_a_second_thread(lambda: instrument.load_patch(patch))
    assert type(error) is PatchRefusedError
    assert isinstance(error, PatchRejectedError)
    cause = error.__cause__
    assert type(cause) is PluginThreadError
    assert cause.thread == "a second thread"
    said = [
        (
            "the call came from the thread 'a second thread', which the plugin cannot be loaded "
            "from on macOS"
        ),
        "the patch passed the package's own checks",
        "it was not given to Vital, so whether Vital takes it is unknown",
    ]
    assert all(statement in error.reason for statement in said)
    assert sorted(said, key=error.reason.index) == said
    assert instrument.preset is before
    assert _state_floats(instrument) == state
    assert (len(plugin.loads), len(plugin.sets)) == reached
    assert recorder.events == ()
    instrument.load_patch(patch)
    assert instrument.get(ParameterId("volume")) == _quantity(-80.0, Unit.db)
    assert len(recorder.of_type(PatchLoaded)) == 1


def test_a_patch_the_guard_refuses_is_refused_for_the_guard_s_reason_from_any_thread(
    instrument: VitalInstrument, plugin: _FakeVital, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard comes first: from a second thread its refusal is the one raised.

    The thread is never asked, and the plugin is not called.
    """
    asked: list[str] = []
    asks = plugin.watch.may_write_here

    def may_write_here() -> bool:
        asked.append("asked")
        return asks()

    monkeypatch.setattr(plugin.watch, "may_write_here", may_write_here)
    loads_made = len(plugin.loads)
    error = _on_a_second_thread(
        lambda: instrument.load_patch(patch_of(_reshaped(custom_warps=[_LINE] * 4)))
    )
    assert type(error) is PatchRefusedError
    assert error.reason == _NO_WARPS
    assert not isinstance(error.__cause__, PluginThreadError)
    assert (asked, len(plugin.loads)) == ([], loads_made)


_OUTSIDE = (KeyboardInterrupt("a stand-in's interrupt"), MemoryError("a stand-in's memory"))
_MID_LOAD = (
    "in the first write",
    "when the second load first reaches the plugin",
    "in the second write",
)


@pytest.mark.parametrize("where", _MID_LOAD)
@pytest.mark.parametrize("raised", _OUTSIDE, ids=["KeyboardInterrupt", "MemoryError"])
def test_an_error_from_outside_the_package_mid_load_leaves_as_itself_and_the_step_is_lost(
    bus: EventBus,
    instrument: VitalInstrument,
    plugin: _FakeVital,
    raised: BaseException,
    where: str,
) -> None:
    """The review of PR 26, finding 1: the plugin may hold part of a text the model does not.

    The error leaves `load_patch` as itself, the same object, and no rollback is tried. The
    marker is not left planted: the start preset and the patch both hold it at 0, so it was
    planted at 1, and it reads 0. The instrument has lost step: `set`, `load_patch` and `render`
    are refused naming the error, `get` and `patch` answer from the model, the preset before,
    and nothing is published.
    """
    before, shown = instrument.preset, instrument.get(ParameterId("volume"))
    patch_before = instrument.patch()
    recorder = _recorder(bus)
    if where == "in the first write":
        plugin.load_script = [raised]
    elif where == "in the second write":
        plugin.load_script = [False, raised]
    else:
        plugin.raising_at_read = (
            plugin.marker_reads + 3,
            raised,
        )  # its marker read, before the plant
    patch = Patch(instrument="Vital", values={ParameterId("volume"): _quantity(-80.0, Unit.db)})
    with pytest.raises(type(raised)) as caught:
        instrument.load_patch(patch)
    assert caught.value is raised
    assert instrument.host.get(MARKER) == 0.0
    reason = f"a load was cut off by {type(raised).__name__}"
    calls: list[Callable[[], object]] = [
        lambda: instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db)),
        lambda: instrument.load_patch(patch),
        lambda: instrument.render(_PATTERN, _REQUEST),
    ]
    for call in calls:
        with pytest.raises(PluginStateError, match=reason):
            call()
    assert instrument.preset is before
    assert instrument.patch() == patch_before
    assert instrument.get(ParameterId("volume")) == shown
    assert recorder.events == ()


# --- the guard -----------------------------------------------------------------------------------


def _reshaped(**sections: object) -> VitalPreset:
    """Return the start preset with some sections replaced by other JSON, or removed for None."""
    opaque = dict(start_preset().opaque)
    for name, value in sections.items():
        if value is None:
            del opaque[PresetKey(name)]
        else:
            opaque[PresetKey(name)] = json.dumps(value).encode("utf-8")
    return start_preset().model_copy(update={"opaque": opaque})


_WAVETABLE: dict[str, object] = {"groups": []}
_SAMPLE: dict[str, object] = {"length": 0, "name": "x", "sample_rate": 44100, "samples": ""}
_NO_SAMPLE = (
    "settings.sample: a preset holds an object there with "
    "['length', 'name', 'sample_rate', 'samples']"
)
_LINE: dict[str, object] = {
    "name": "Line 1",
    "num_points": 2,
    "points": [0.0, 1.0, 1.0, 0.0],
    "powers": [0.0, 0.0],
    "smooth": False,
}
_NO_WARPS = "settings.custom_warps: a preset that holds it holds an array of 3 objects there"
_NO_RANDOMS = "settings.random_values: a preset that holds it holds an array of 3 objects there"
_REFUSED: dict[str, tuple[Callable[[], VitalPreset], str]] = {
    "a version that is no version": (
        lambda: start_preset().model_copy(update={"synth_version": "abc"}),
        "synth_version 'abc' is not a version, digits and dots",
    ),
    "a version with a letter in it": (
        lambda: start_preset().model_copy(update={"synth_version": "1.6.4b"}),
        "synth_version '1.6.4b' is not a version, digits and dots",
    ),
    "a newer version": (
        lambda: start_preset().model_copy(update={"synth_version": "1.6.5"}),
        "synth_version 1.6.5 is newer than the plugin's 1.6.4",
    ),
    "a much newer version": (
        lambda: start_preset().model_copy(update={"synth_version": "99.0.0"}),
        "synth_version 99.0.0 is newer than the plugin's 1.6.4",
    ),
    "no wavetables": (
        lambda: _reshaped(wavetables=None),
        "settings.wavetables: a preset holds an array of 3 objects there",
    ),
    "wavetables an object": (
        lambda: _reshaped(wavetables={"x": 1}),
        "settings.wavetables: a preset holds an array of 3 objects there",
    ),
    "wavetables empty": (
        lambda: _reshaped(wavetables=[]),
        "settings.wavetables: a preset holds an array of 3 objects there",
    ),
    "two wavetables": (
        lambda: _reshaped(wavetables=[_WAVETABLE] * 2),
        "settings.wavetables: a preset holds an array of 3 objects there",
    ),
    "wavetables that are not objects": (
        lambda: _reshaped(wavetables=[1.0, 2.0, 3.0]),
        "settings.wavetables: a preset holds an array of 3 objects there",
    ),
    "no lfos": (
        lambda: _reshaped(lfos=None),
        "settings.lfos: a preset holds an array of 8 objects there",
    ),
    "lfos empty": (
        lambda: _reshaped(lfos=[]),
        "settings.lfos: a preset holds an array of 8 objects there",
    ),
    "no sample": (
        lambda: _reshaped(sample=None),
        _NO_SAMPLE,
    ),
    "a sample lacking a key": (
        lambda: _reshaped(sample={"length": 0, "name": "x", "sample_rate": 44100}),
        _NO_SAMPLE,
    ),
    "a sample that is an array": (
        lambda: _reshaped(sample=[_SAMPLE]),
        _NO_SAMPLE,
    ),
    "four custom warps": (
        lambda: _reshaped(custom_warps=[_LINE] * 4),
        _NO_WARPS,
    ),
    "two custom warps": (
        lambda: _reshaped(custom_warps=[_LINE] * 2),
        _NO_WARPS,
    ),
    "custom warps empty": (
        lambda: _reshaped(custom_warps=[]),
        _NO_WARPS,
    ),
    "custom warps an object": (
        lambda: _reshaped(custom_warps={}),
        _NO_WARPS,
    ),
    "custom warps that are not objects": (
        lambda: _reshaped(custom_warps=[_LINE, _LINE, 5]),
        _NO_WARPS,
    ),
    "four random values": (
        lambda: _reshaped(random_values=[{"seed": 4}] * 4),
        _NO_RANDOMS,
    ),
    "two random values": (
        lambda: _reshaped(random_values=[{"seed": 4}] * 2),
        _NO_RANDOMS,
    ),
    "random values empty": (
        lambda: _reshaped(random_values=[]),
        _NO_RANDOMS,
    ),
    "random values an object": (
        lambda: _reshaped(random_values={}),
        _NO_RANDOMS,
    ),
    "random values that are not objects": (
        lambda: _reshaped(random_values=[{"seed": 4}, {"seed": 4}, "x"]),
        _NO_RANDOMS,
    ),
    "a float whose display is no finite number": (
        lambda: _holding(chorus_delay_1=1e30),  # shown as two to that power, in seconds
        "chorus_delay_1: 1e+30 has no display that is a finite number",
    ),
}


@pytest.mark.parametrize("case", _REFUSED.values(), ids=_REFUSED.keys())
def test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called(
    bus: EventBus,
    instrument: VitalInstrument,
    plugin: _FakeVital,
    case: tuple[Callable[[], VitalPreset], str],
) -> None:
    """Each shape the probes saw block, be ignored, keep old sections or kill the process.

    Refused by its reason, before the plugin is called. `custom_warps` and `random_values` one
    entry longer killed the process on Vital, and shorter or empty were not held as given (the
    spec of issue #20's `verification/arrays-seen.txt`): no test sends Vital either.
    """
    build, reason = case
    preset = build()
    with pytest.raises(PatchRefusedError) as caught:
        check_loadable(preset, parameter_map())
    assert caught.value.reason == reason
    recorder = _recorder(bus)
    loads_made = len(plugin.loads)
    with pytest.raises(PatchRefusedError):
        instrument.load_patch(patch_of(preset))
    assert len(plugin.loads) == loads_made
    assert instrument.preset is start_preset()
    assert recorder.events == ()


def test_the_guard_passes_what_vital_was_seen_to_load(pytestconfig: pytest.Config) -> None:
    """The start preset, the fixture, an older version and a sample with a fifth key all pass."""
    found = parameter_map()
    fixture = pytestconfig.rootpath / "tests" / "data" / "init-media-replaced.vital"
    check_loadable(start_preset(), found)
    check_loadable(loads(fixture.read_text(encoding="utf-8")), found)
    check_loadable(start_preset().model_copy(update={"synth_version": "0.6.1"}), found)
    check_loadable(_reshaped(sample={**_SAMPLE, "samples_stereo": ""}), found)
    check_loadable(_reshaped(custom_warps=None, random_values=None), found)
    check_loadable(_reshaped(custom_warps=[_LINE] * 3, random_values=[{"seed": 9}] * 3), found)
    check_loadable(_holding(flanger_dry_wet=_float32(0.7072)), found)


def test_the_sections_are_judged_in_the_order_the_guard_gives() -> None:
    """Of two sections that would each refuse, the earlier in the guard's order is named.

    Wavetables and lfos, then the sample, then the two a preset need not hold.
    """
    found = parameter_map()
    both = _reshaped(sample=[_SAMPLE], custom_warps=[], random_values=[])
    with pytest.raises(PatchRefusedError) as caught:
        check_loadable(both, found)
    assert caught.value.reason == _NO_SAMPLE
    with pytest.raises(PatchRefusedError) as caught:
        check_loadable(_reshaped(custom_warps=[], random_values=[]), found)
    assert caught.value.reason == _NO_WARPS


def test_a_version_is_compared_by_its_numbers_less_trailing_zeros() -> None:
    """PR 23's finding 6: `1.6.4.0` is the plugin's 1.6.4, and `1.6.10` is newer than it."""
    found = parameter_map()
    check_loadable(start_preset().model_copy(update={"synth_version": "1.6.4.0"}), found)
    check_loadable(start_preset().model_copy(update={"synth_version": "1.6.4.0.0"}), found)
    check_loadable(start_preset().model_copy(update={"synth_version": "1.6"}), found)
    with pytest.raises(PatchRefusedError) as caught:
        check_loadable(start_preset().model_copy(update={"synth_version": "1.6.10"}), found)
    assert caught.value.reason == "synth_version 1.6.10 is newer than the plugin's 1.6.4"


def test_a_plugin_version_that_is_not_digits_and_dots_refuses_every_preset_by_name() -> None:
    """PR 23's finding 6: no preset can be shown not to be newer, so none is taken."""
    found = parameter_map().model_copy(update={"vital_version": "1.6.4b"})
    with pytest.raises(PatchRefusedError) as caught:
        check_loadable(start_preset().model_copy(update={"synth_version": "0.6.1"}), found)
    assert caught.value.reason == (
        "the plugin's version '1.6.4b' is not digits and dots, so no preset's can be compared "
        "with it"
    )


def test_the_guard_does_not_read_inside_a_section() -> None:
    """Three wavetables whose inside Vital cannot read pass: the limit the docstring states.

    Vital answers this text with its alert (the instrument spec's `verification/probes.txt`).
    Since issue #20 the host answers that alert on macOS and the load is refused; anywhere else
    it still never returns, which is why no test sends it to Vital in the test's own process.
    The guard judges a section's shape alone.
    """
    check_loadable(_reshaped(wavetables=[{"groups": 5}] * 3), parameter_map())


# --- renders -------------------------------------------------------------------------------------


def test_a_render_sends_the_pattern_s_midi_and_gives_the_length_asked_for(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The host is asked for the samples core's rule gives, with each note half a sample past."""
    recorder = _recorder(bus)
    result = instrument.render(_PATTERN, _REQUEST)
    assert _REQUEST.samples(_PATTERN) == _SAMPLES
    assert result.audio.shape == (2, _SAMPLES)
    assert result.audio.dtype == np.float32
    assert (result.sample_rate, result.warnings) == (_RATE, ())
    assert result.elapsed_seconds > 0.0
    ((midi, duration, rate),) = plugin.renders
    assert midi == [(b"\x90\x3c\x64", 0.5 / _RATE), (b"\x80\x3c\x00", 24000.5 / _RATE)]
    assert (duration, rate) == ((_SAMPLES + 1) / _RATE, _RATE)
    (completed,) = recorder.events
    assert isinstance(completed, RenderCompleted)
    assert (completed.source, completed.instrument) == ("Vital", "Vital")
    assert (completed.elapsed_seconds, completed.audio_seconds, completed.warnings) == (
        result.elapsed_seconds,
        _SAMPLES / _RATE,
        (),
    )
    assert instrument.preset is start_preset()
    assert _sets(plugin) == []


def test_a_render_of_no_samples_is_an_empty_result_and_the_plugin_is_not_called(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """As core's reference instrument gives it: two channels of nothing, and one event.

    Four beats at 23,040,000 bpm with no tail round to no sample. The model, the plugin and the
    bus, but for the one `RenderCompleted`, are as they were.
    """
    instant = Pattern(tempo_bpm=23_040_000.0, bars=1, beats_per_bar=4, notes=_PATTERN.notes)
    request = RenderRequest(sample_rate=_RATE, tail_seconds=0.0)
    assert request.samples(instant) == 0
    state, loads_made = _state_floats(instrument), len(plugin.loads)
    recorder = _recorder(bus)
    result = instrument.render(instant, request)
    assert result.audio.shape == (2, 0)
    assert result.audio.dtype == np.float32
    assert (result.audio_seconds, result.warnings) == (0.0, ())
    assert plugin.renders == []
    (completed,) = recorder.events
    assert isinstance(completed, RenderCompleted)
    assert (completed.audio_seconds, completed.elapsed_seconds) == (0.0, result.elapsed_seconds)
    assert instrument.preset is start_preset()
    assert (_state_floats(instrument), len(plugin.loads), _sets(plugin)) == (state, loads_made, [])


_RATES = "MIN_SAMPLE_RATE, 1000 Hz, to MAX_SAMPLE_RATE, 768000 Hz"
_PAST_A_LIMIT: dict[str, tuple[Pattern, RenderRequest, str]] = {
    "too long": (
        Pattern(tempo_bpm=60.0, bars=1, beats_per_bar=350, notes=()),
        _REQUEST,
        f"a render of 16812000 samples is past MAX_SAMPLES, {2**24}",
    ),
    "too slow a rate": (
        _PATTERN,
        RenderRequest(sample_rate=999, tail_seconds=0.0),
        f"a rate of 999 Hz is outside {_RATES}",
    ),
    "too fast a rate": (
        _PATTERN,
        RenderRequest(sample_rate=768001, tail_seconds=0.0),
        f"a rate of 768001 Hz is outside {_RATES}",
    ),
}


@pytest.mark.parametrize("case", _PAST_A_LIMIT.values(), ids=_PAST_A_LIMIT.keys())
def test_a_render_past_a_limit_is_refused_naming_the_limit_and_its_value(
    bus: EventBus,
    instrument: VitalInstrument,
    plugin: _FakeVital,
    case: tuple[Pattern, RenderRequest, str],
) -> None:
    """Refused before the plugin is called: nothing rendered, changed or published."""
    pattern, request_, reason = case
    assert (MAX_SAMPLES, MIN_SAMPLE_RATE, MAX_SAMPLE_RATE) == (2**24, 1_000, 768_000)
    state = _state_floats(instrument)
    recorder = _recorder(bus)
    with pytest.raises(RenderRefusedError) as caught:
        instrument.render(pattern, request_)
    assert isinstance(caught.value, RenderFailedError)
    assert isinstance(caught.value, VitalError)
    assert caught.value.reason == reason
    assert plugin.renders == []
    assert recorder.events == ()
    assert instrument.preset is start_preset()
    assert _state_floats(instrument) == state


def test_a_render_with_a_note_no_channel_can_voice_is_refused_and_the_plugin_not_called(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Seventeen notes of one pitch at once: refused by the MIDI's reason, publishing nothing."""
    notes = tuple(
        Note(pitch=60, velocity=100, start_beats=0.0, duration_beats=1.0, channel=0)
        for _ in range(17)
    )
    crowded = _PATTERN.model_copy(update={"notes": notes})
    recorder = _recorder(bus)
    with pytest.raises(RenderRefusedError) as caught:
        instrument.render(crowded, _REQUEST)
    assert caught.value.reason.startswith("pitch 60 is already sounding on all 16 MIDI channels")
    assert plugin.renders == []
    assert recorder.events == ()


def test_the_limits_themselves_are_rendered(instrument: VitalInstrument) -> None:
    """A render at each rate's end and of exactly `MAX_SAMPLES` is asked of the plugin."""
    for rate in (MIN_SAMPLE_RATE, MAX_SAMPLE_RATE):
        request = RenderRequest(sample_rate=rate, tail_seconds=0.0)
        assert instrument.render(_PATTERN, request).audio.shape == (2, 2 * rate)
    longest = Pattern(tempo_bpm=60.0, bars=1, beats_per_bar=1024, notes=())
    request = RenderRequest(sample_rate=2**14, tail_seconds=0.0)
    assert request.samples(longest) == MAX_SAMPLES
    assert instrument.render(longest, request).audio.shape == (2, MAX_SAMPLES)


def test_a_render_the_plugin_does_not_give_is_refused_chained_from_the_host_s_error(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """A plugin that raises, and one that gives a sample that is no number: the render error."""
    recorder = _recorder(bus)
    plugin.refusing.add("render")
    with pytest.raises(RenderRefusedError) as refused:
        instrument.render(_PATTERN, _REQUEST)
    assert type(refused.value.__cause__) is PluginRenderError
    assert refused.value.reason.startswith("the plugin gave no render: ")
    plugin.refusing.clear()

    def not_finite(samples: int) -> NDArray[np.float32]:
        audio = np.zeros((2, samples), dtype=np.float32)
        audio[1, 7] = np.inf
        return audio

    plugin.audio = not_finite
    with pytest.raises(RenderRefusedError) as infinite:
        instrument.render(_PATTERN, _REQUEST)
    assert infinite.value.reason == "the plugin gave a sample that is no finite number"
    assert recorder.events == ()


def test_a_render_that_reaches_full_scale_carries_one_warning_saying_the_peak_and_where(
    bus: EventBus, instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Three samples at or past full scale, the largest 1.5 on the second channel: one warning.

    The audio is returned as the plugin gave it, the sample past full scale still past it, and
    the `RenderCompleted` carries the same warning.
    """

    def clipping(samples: int) -> NDArray[np.float32]:
        audio = np.zeros((2, samples), dtype=np.float32)
        audio[0, 4800] = FULL_SCALE
        audio[1, 9600] = -1.5
        audio[0, 9601] = 1.25
        return audio

    plugin.audio = clipping
    recorder = _recorder(bus)
    result = instrument.render(_PATTERN, _REQUEST)
    warning = (
        "clipped: the render peaks at 1.500 of full scale; 3 of its 108000 samples are at or "
        "past it, the first at sample 4800 (0.100 s)"
    )
    assert result.warnings == (warning,)
    assert float(result.audio[1, 9600]) == -1.5  # noqa: PLR2004 - as given, not clipped
    (completed,) = recorder.of_type(RenderCompleted)
    assert completed.warnings == result.warnings
    assert len(recorder.events) == 1


def test_a_render_whose_largest_sample_is_exactly_full_scale_carries_the_warning(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """At full scale counts, not only past it: one sample of exactly -1.0 is a clipped render."""

    def at_full_scale(samples: int) -> NDArray[np.float32]:
        audio = np.zeros((2, samples), dtype=np.float32)
        audio[1, 0] = -FULL_SCALE
        return audio

    plugin.audio = at_full_scale
    warning = (
        "clipped: the render peaks at 1.000 of full scale; 1 of its 108000 samples are at or "
        "past it, the first at sample 0 (0.000 s)"
    )
    assert instrument.render(_PATTERN, _REQUEST).warnings == (warning,)


def test_a_render_just_under_full_scale_carries_no_warning(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """The float32 below 1.0 on every sample: the threshold is full scale itself, not near it."""
    under = float(np.nextafter(np.float32(FULL_SCALE), np.float32(0.0)))
    assert under < FULL_SCALE == 1.0
    plugin.audio = lambda samples: np.full((2, samples), under, dtype=np.float32)
    assert instrument.render(_PATTERN, _REQUEST).warnings == ()


# --- what it publishes ---------------------------------------------------------------------------


def test_each_call_carried_out_publishes_its_one_event_from_vital_under_its_own_id(
    bus: EventBus, instrument: VitalInstrument
) -> None:
    """A set, a load and a render: three events, each sourced "Vital", no two of one call."""
    recorder = _recorder(bus)
    instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db))
    instrument.load_patch(instrument.patch())
    instrument.render(_PATTERN, _REQUEST)
    kinds = [type(event) for event in recorder.events]
    assert kinds == [ParameterChanged, PatchLoaded, RenderCompleted]
    assert [event.source for event in recorder.events] == ["Vital"] * 3
    assert len({event.correlation_id for event in recorder.events}) == len(recorder.events)


def test_every_refusal_is_the_package_s_error_and_core_s(
    instrument: VitalInstrument, plugin: _FakeVital
) -> None:
    """Each path a call can be refused on, driven once: nothing but a VitalError leaves it.

    errors.md's rule, that no error but the package's leaves a public method, held over the
    instrument's five methods that can refuse.
    """
    whole = instrument.patch()
    far = Pattern(tempo_bpm=1e-300, bars=1, beats_per_bar=1, notes=())
    refusals: list[tuple[Callable[[], object], type[Exception]]] = [
        (lambda: instrument.get(ParameterId("nope")), ParameterNotFoundError),
        (lambda: instrument.set(ParameterId("nope"), _quantity(0.0)), ParameterNotFoundError),
        (lambda: instrument.set(ParameterId("volume"), _quantity(0.0)), UnitMismatchError),
        (
            lambda: instrument.set(ParameterId("volume"), _quantity(7.0, Unit.db)),
            ValueOutOfRangeError,
        ),
        (lambda: instrument.set(ParameterId("bypass"), _quantity(0.5)), ValueOutOfRangeError),
        (lambda: instrument.load_patch(Patch(instrument="Other", values={})), PatchRejectedError),
        (
            lambda: instrument.load_patch(
                Patch(instrument="Vital", values={ParameterId("nope"): _quantity(0.0)})
            ),
            PatchRejectedError,
        ),
        (
            lambda: instrument.load_patch(
                Patch(instrument="Vital", values=whole.values, opaque={"nope": b""})
            ),
            PatchRejectedError,
        ),
        (
            lambda: instrument.load_patch(
                Patch(
                    instrument="Vital",
                    values=whole.values,
                    opaque={**whole.opaque, "settings.wavetables": b"[]"},
                )
            ),
            PatchRejectedError,
        ),
        (lambda: instrument.render(far, _REQUEST), RenderFailedError),
        (
            lambda: instrument.render(_PATTERN, RenderRequest(sample_rate=1, tail_seconds=0.0)),
            RenderFailedError,
        ),
    ]
    for call, core_s in refusals:
        with pytest.raises(VitalError) as caught:
            call()
        assert isinstance(caught.value, core_s)
    plugin.refusing.update({"set", "render", "load"})
    after: list[Callable[[], object]] = [
        lambda: instrument.set(ParameterId("volume"), _quantity(0.0, Unit.db)),
        lambda: instrument.load_patch(whole),
        lambda: instrument.render(_PATTERN, _REQUEST),
    ]
    for call in after:
        with pytest.raises(VitalError):
            call()
