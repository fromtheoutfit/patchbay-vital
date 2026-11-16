"""A preset is carried in a patch and comes back byte for byte, a float in exactly one place.

The carrying is held on built presets Hypothesis draws, on the start preset and on the fixture,
through JSON too; the installed presets are `tests/integration/test_factory_round_trip.py`'s. An
expected value here is written out or worked out from primitives, `struct`, `math` and the
curve's formula restated, never from `patch_of` or `preset_of` themselves.
"""

import json
import math
import struct
from pathlib import Path

import pytest
from builders import EMPTY_SLOT, FLOATS, KEYS, make_preset, what_a_set_holds
from hypothesis import given
from hypothesis import strategies as st
from patchbay import (
    ParameterId,
    Patch,
    PatchRejectedError,
    PresetKey,
    Quantity,
    Unit,
    UnitMismatchError,
    ValueOutOfRangeError,
)

from patchbay_vital import dumps, loads
from patchbay_vital.errors import (
    ParameterRangeError,
    ParameterUnitError,
    PatchRefusedError,
    UnknownParameterError,
    VitalError,
)
from patchbay_vital.format import split_modulations
from patchbay_vital.parameters import parameter_map
from patchbay_vital.patch import (
    LINE_MAPPING_PREFIX,
    PRESET_ENTRY,
    SECTION_PREFIX,
    TUNING_ENTRY,
    check_value,
    patch_of,
    preset_of,
)
from patchbay_vital.preset import MODULATION_SLOTS, VitalPreset, VitalSettings
from patchbay_vital.start import start_preset

_FIXTURE = Path("tests") / "data" / "init-media-replaced.vital"
_PARAMETERS = 903
_TWELVE_SEMITONES_UP = 72.0  # filter_1_cutoff shows its preset value less 60
_SECOND_STEP = 2.0
_PERCENT_BOUNDS = (0.0, 100.0)  # flanger_dry_wet's, in percent
_VOLUME_BOUNDS = (-80.0, 6.020000172561609)  # volume's, in dB

_SLOTS = st.builds(
    lambda source, amount, bipolar, ramp, line: EMPTY_SLOT.model_copy(
        update={
            "source": source,
            "destination": None if source is None else PresetKey("volume"),
            "amount": amount,
            "bipolar": bipolar,
            "ramp_up": ramp,
            "line_mapping": line,
        }
    ),
    st.sampled_from([None, "lfo_1", "macro_control_2"]),
    FLOATS,
    FLOATS,
    st.none() | FLOATS,
    st.sampled_from([None, b'{"points":[0.0,1.0]}']),
)
_SECTIONS = st.dictionaries(
    st.sampled_from(["wavetables", "lfos", "sample", "tuning", "a section Vital adds"]),
    st.sampled_from([b"[]", b'{"name":"x"}', b'[{"wave_data":"AAAA"}]']),
    max_size=4,
)
_PRESETS = st.builds(
    lambda values, slots, sections, name, tuning, newline: make_preset(
        settings=VitalSettings(values=values),
        modulations=(*slots, *(EMPTY_SLOT,) * (MODULATION_SLOTS - len(slots))),
        opaque=sections,
        preset_name=name,
        tuning=tuning,
        trailing_newline=newline,
    ),
    st.dictionaries(KEYS, FLOATS, max_size=30),
    st.lists(_SLOTS, max_size=4),
    _SECTIONS,
    st.none() | st.text(max_size=8),
    st.sampled_from([None, b'{"scale":[0.0,1.0]}']),
    st.booleans(),
)


def _float32(value: float) -> float:
    """Return the float32 nearest a double, by `struct`."""
    held: float = struct.unpack("<f", struct.pack("<f", value))[0]
    return held


def _entry(patch: Patch) -> dict[str, object]:
    """Return a patch's `preset` entry, parsed."""
    entry: dict[str, object] = json.loads(patch.opaque[PRESET_ENTRY])
    return entry


def _carried(patch: Patch) -> dict[str, float]:
    """Return the floats a patch's `preset` entry carries."""
    carried = _entry(patch)["settings"]
    assert isinstance(carried, dict)
    return carried


def _floats(preset: VitalPreset) -> dict[str, float]:
    """Return every float a preset holds, the slots' among them, by key."""
    _, slots = split_modulations(preset.modulations)
    return {str(key): held for key, held in (*preset.settings.values.items(), *slots.items())}


def _with(preset: VitalPreset, **floats: float) -> VitalPreset:
    """Return a preset with some settings floats replaced."""
    values = {**preset.settings.values, **{PresetKey(key): value for key, value in floats.items()}}
    return preset.model_copy(update={"settings": VitalSettings(values=values)})


def _through_json(patch: Patch) -> Patch:
    return Patch.model_validate_json(patch.model_dump_json())


@given(_PRESETS)
def test_a_built_preset_comes_back_byte_for_byte_through_a_patch_and_through_json(
    preset: VitalPreset,
) -> None:
    """Any float32 under any key, any slot, section, name, tuning and ending: the same bytes."""
    patch = patch_of(preset)
    assert dumps(preset_of(patch)) == dumps(preset)
    assert dumps(preset_of(_through_json(patch))) == dumps(preset)
    assert patch_of(preset_of(patch)) == patch


@given(_PRESETS)
def test_a_float_is_in_values_or_in_the_entry_and_never_in_both(preset: VitalPreset) -> None:
    """Every float the preset holds is carried once: as a value, or as itself in the entry."""
    patch = patch_of(preset)
    carried = _carried(patch)
    assert not set(patch.values) & set(carried)
    assert set(patch.values) | set(carried) == set(_floats(preset))
    found = parameter_map()
    for parameter_id, value in patch.values.items():
        found.find(parameter_id).parameter.check(value)


def test_the_start_preset_and_the_fixture_come_back_with_all_903_in_values(
    pytestconfig: pytest.Config,
) -> None:
    """A 1.6.4 preset at its defaults: every parameter a value, nothing left for the entry."""
    fixture = loads((pytestconfig.rootpath / _FIXTURE).read_text(encoding="utf-8"))
    for preset in (start_preset(), fixture):
        patch = patch_of(preset)
        assert patch.instrument == "Vital"
        assert len(patch.values) == _PARAMETERS
        assert _carried(patch) == {}
        assert dumps(preset_of(_through_json(patch))) == dumps(preset)


def test_what_opaque_holds_is_under_its_fixed_keys() -> None:
    """The entry, each section by its name, a slot's line mapping by its number, the tuning."""
    slots = list(start_preset().modulations)
    slots[2] = slots[2].model_copy(
        update={"source": "lfo_1", "destination": PresetKey("volume"), "line_mapping": b"[1.0]"}
    )
    sections = {**start_preset().opaque, PresetKey("tuning"): b"[2.0]"}
    preset = start_preset().model_copy(
        update={"modulations": tuple(slots), "opaque": sections, "tuning": b'{"a":3.0}'}
    )
    patch = patch_of(preset)
    assert sorted(patch.opaque) == [
        "line_mapping.3",
        "preset",
        "settings.custom_warps",
        "settings.lfos",
        "settings.random_values",
        "settings.sample",
        "settings.tuning",
        "settings.wavetables",
        "tuning",
    ]
    assert patch.opaque["line_mapping.3"] == b"[1.0]"
    assert patch.opaque["settings.tuning"] == b"[2.0]"  # a section of that name, under settings
    assert patch.opaque["tuning"] == b'{"a":3.0}'  # the plugin state's own, at the top
    assert patch.opaque["settings.wavetables"] == start_preset().opaque[PresetKey("wavetables")]
    entry = _entry(patch)
    assert sorted(entry) == [
        "author",
        "comments",
        "macro1",
        "macro2",
        "macro3",
        "macro4",
        "modulations",
        "preset_name",
        "preset_style",
        "settings",
        "synth_version",
        "trailing_newline",
    ]
    routing = entry["modulations"]
    assert isinstance(routing, list)
    assert len(routing) == MODULATION_SLOTS
    assert routing[2] == ["lfo_1", "volume"]
    assert routing[0] == ["", ""]
    assert dumps(preset_of(patch)) == dumps(preset)


def test_a_float_outside_its_bounds_rides_in_the_entry_as_itself() -> None:
    """`flanger_dry_wet` at 0.7072, as presets Vital ships hold it: 141.44 against 0 to 100."""
    held = _float32(0.7072)
    assert held * 200.0 > _PERCENT_BOUNDS[1]  # the display, by the curve's own multiply
    preset = _with(start_preset(), flanger_dry_wet=held)
    patch = patch_of(preset)
    assert ParameterId("flanger_dry_wet") not in patch.values
    assert _carried(patch) == {"flanger_dry_wet": held}
    assert len(patch.values) == _PARAMETERS - 1
    assert dumps(preset_of(_through_json(patch))) == dumps(preset)


def test_a_float_its_display_cannot_carry_rides_in_the_entry_though_it_is_in_range() -> None:
    """Below `volume`'s floor the curve does not give a float back, so the float itself is kept.

    `volume` shows `sqrt(preset) - 80` dB. At the float32 nearest 3e-19 the square root, about
    5.5e-10, loses its last digits beside 80, so the display, less its 80 and squared, is another
    float32: worked out here from `math`, not from the map. The display is in range, and still
    cannot name the float.
    """
    held = _float32(3e-19)
    display = math.sqrt(held) - 80.0
    assert _VOLUME_BOUNDS[0] <= display <= _VOLUME_BOUNDS[1]
    assert _float32((display + 80.0) ** 2) != held
    preset = _with(start_preset(), volume=held)
    patch = patch_of(preset)
    assert ParameterId("volume") not in patch.values
    assert _carried(patch) == {"volume": held}
    assert dumps(preset_of(_through_json(patch))) == dumps(preset)


def test_a_negative_zero_a_value_between_steps_and_a_key_that_is_no_parameter_are_kept() -> None:
    """Three more floats no display carries: each rides in the entry and comes back as written.

    -0.0 shows 0.0, which names 0.0; 1.5 on a transpose, a stepped scale, shows 1.5, which a
    preset holds as 2; `chorus_damping` is a key old presets hold and no parameter does.
    """
    preset = _with(start_preset(), osc_1_transpose=1.5, chorus_damping=0.5)
    slots = list(preset.modulations)
    slots[0] = slots[0].model_copy(update={"amount": -0.0})
    preset = preset.model_copy(update={"modulations": tuple(slots)})
    patch = patch_of(preset)
    carried = _carried(patch)
    assert sorted(carried) == ["chorus_damping", "modulation_1_amount", "osc_1_transpose"]
    assert math.copysign(1.0, carried["modulation_1_amount"]) == -1.0
    assert not {"osc_1_transpose", "chorus_damping", "modulation_1_amount"} & set(patch.values)
    back = preset_of(_through_json(patch))
    assert dumps(back) == dumps(preset)
    assert '"modulation_1_amount":-0.0' in dumps(back)


def test_a_key_the_preset_lacks_is_in_neither_place_and_stays_absent() -> None:
    """An older file's missing keys: no value, no entry float, and none after the round trip."""
    values = dict(start_preset().settings.values)
    del values[PresetKey("volume")]
    slots = tuple(
        slot.model_copy(update={"ramp_up": None, "ramp_down": None})
        for slot in start_preset().modulations
    )
    preset = start_preset().model_copy(
        update={"settings": VitalSettings(values=values), "modulations": slots, "preset_name": None}
    )
    patch = patch_of(preset)
    assert ParameterId("volume") not in patch.values
    assert ParameterId("modulation_1_ramp_up") not in patch.values
    assert len(patch.values) == _PARAMETERS - 1 - 2 * MODULATION_SLOTS
    assert _carried(patch) == {}
    assert "preset_name" not in _entry(patch)
    back = preset_of(patch)
    assert PresetKey("volume") not in back.settings.values
    assert back.modulations[0].ramp_up is None
    assert back.preset_name is None
    assert dumps(back) == dumps(preset)


def test_a_patch_of_values_alone_is_laid_over_the_start_preset() -> None:
    """Its sections, routing and metadata are the start's, and what it does not name is too."""
    cutoff = Quantity(value=12.0, unit=Unit.semitones)
    patch = Patch(instrument="Vital", values={ParameterId("filter_1_cutoff"): cutoff})
    preset = preset_of(patch)
    start = start_preset()
    assert preset.settings.values[PresetKey("filter_1_cutoff")] == _TWELVE_SEMITONES_UP
    assert _with(preset, filter_1_cutoff=60.0).settings == start.settings
    assert preset.modulations == start.modulations
    assert preset.opaque == start.opaque
    assert (preset.author, preset.preset_name) == (start.author, start.preset_name)
    assert preset_of(Patch(instrument="Vital", values={})) == start


def test_a_value_goes_to_the_float_a_set_of_it_holds_unless_it_names_a_float() -> None:
    """PR 23's findings 2 and 3: a value is taken as a set takes it, but for a float's own display.

    60 bpm is 1 in the preset, on a scale from the float32 of 1/3 to 5. 216.85141355537831 is no
    float's display: the float32 nearest it over 60 shows another, so it holds what a set of it
    holds, worked out from primitives. That float32's own display, 3.6141903400421143 times 60,
    names it, and it is held as itself, though no set lands on it. On a stepped scale a value
    always goes to the nearest step, a half away, as a set does.
    """
    given = 216.85141355537831
    own = _float32(given / 60.0)
    _, set_holds = what_a_set_holds(own, _float32(1 / 3), 5.0)
    assert (own, set_holds) == (3.6141903400421143, 3.6141905784606934)
    assert own * 60.0 != given
    values = {
        ParameterId("beats_per_minute"): Quantity(value=given, unit=Unit.bpm),
        ParameterId("chorus_voices"): Quantity(value=6.0, unit=Unit.none),
        ParameterId("oversampling"): Quantity(value=3.0, unit=Unit.none),
    }
    held = preset_of(Patch(instrument="Vital", values=values)).settings.values
    assert held[PresetKey("beats_per_minute")] == set_holds
    # 6 voices is 1.5 in fours, and a half goes up; log2(3) is 1.58, the step of 4 and not of 2.
    assert held[PresetKey("chorus_voices")] == _SECOND_STEP
    assert held[PresetKey("oversampling")] == _SECOND_STEP
    named = {ParameterId("beats_per_minute"): Quantity(value=own * 60.0, unit=Unit.bpm)}
    back = preset_of(Patch(instrument="Vital", values=named)).settings.values
    assert back[PresetKey("beats_per_minute")] == own != set_holds


def test_another_instrument_s_patch_is_refused_before_anything_else_is_read() -> None:
    """The name comes first: a patch for another instrument is refused though the rest is bad."""
    patch = Patch(
        instrument="Vital.other",
        values={ParameterId("nope"): Quantity(value=0.0, unit=Unit.none)},
        opaque={"nothing of ours": b"x"},
    )
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason == "the patch is for instrument 'Vital.other', not 'Vital'"
    assert caught.value.__cause__ is None
    assert isinstance(caught.value, PatchRejectedError)


@pytest.mark.parametrize(
    ("key", "reason"),
    [
        ("wavetables", "wavetables: no entry a Vital patch holds"),
        ("settings.", "settings.: no entry a Vital patch holds"),
        ("line_mapping.0", "line_mapping.0: a line mapping belongs to a slot from 1 to 64"),
        ("line_mapping.65", "line_mapping.65: a line mapping belongs to a slot from 1 to 64"),
        ("line_mapping.01", "line_mapping.01: a line mapping belongs to a slot from 1 to 64"),
        ("line_mapping.x", "line_mapping.x: a line mapping belongs to a slot from 1 to 64"),
    ],
)
def test_an_opaque_key_that_is_no_entry_of_a_vital_patch_is_refused_by_name(
    key: str, reason: str
) -> None:
    """A key outside the fixed ones is named, before any value is looked at."""
    whole = patch_of(start_preset())
    bad = {ParameterId("nope"): Quantity(value=0.0, unit=Unit.none)}
    patch = Patch(instrument="Vital", values=bad, opaque={**whole.opaque, key: b"[]"})
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason == reason


def test_the_first_opaque_key_to_refuse_is_the_first_in_order() -> None:
    """Two keys that are no entry: the one that sorts first is named, on every run."""
    whole = patch_of(start_preset())
    patch = Patch(instrument="Vital", values={}, opaque={**whole.opaque, "zz": b"", "aa": b""})
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason == "aa: no entry a Vital patch holds"


@pytest.mark.parametrize("key", ["settings.wavetables", "tuning", "line_mapping.1"])
def test_an_entry_without_the_preset_entry_it_belongs_to_is_refused(key: str) -> None:
    """Sections, a tuning or a line mapping with no `preset` entry are no part of anything."""
    patch = Patch(instrument="Vital", values={}, opaque={key: b"{}"})
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason == f"{key}: the patch has no 'preset' entry for it to belong to"


@pytest.mark.parametrize(
    "damage",
    [
        b"not JSON",
        b"{}",
        b'{"author":1}',
        json.dumps(
            {**json.loads(patch_of(start_preset()).opaque[PRESET_ENTRY]), "more": 1}
        ).encode(),
        json.dumps(
            {**json.loads(patch_of(start_preset()).opaque[PRESET_ENTRY]), "modulations": [["", ""]]}
        ).encode(),
    ],
    ids=["not JSON", "empty", "a number for a string", "a key too many", "one slot"],
)
def test_a_preset_entry_that_is_not_one_is_refused_by_its_key(damage: bytes) -> None:
    """The entry is read strictly: what it is not is said, chained from the model's refusal."""
    whole = patch_of(start_preset())
    patch = Patch(instrument="Vital", values={}, opaque={**whole.opaque, PRESET_ENTRY: damage})
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason.startswith("preset: ")
    assert caught.value.__cause__ is not None


def test_a_parameter_carried_in_both_places_is_refused_by_name() -> None:
    """A float as a value and in the entry too: which is meant cannot be said, so neither is."""
    held = _float32(0.7072)
    whole = patch_of(_with(start_preset(), flanger_dry_wet=held))
    both = {**whole.values, ParameterId("flanger_dry_wet"): Quantity(value=50.0, unit=Unit.percent)}
    patch = Patch(instrument="Vital", values=both, opaque=whole.opaque)
    with pytest.raises(PatchRefusedError) as caught:
        preset_of(patch)
    assert caught.value.reason == (
        "flanger_dry_wet: carried both as a value and in the 'preset' entry"
    )
    assert caught.value.__cause__ is None


def test_a_value_that_refuses_names_its_key_and_is_chained_from_what_refused_it() -> None:
    """An unknown id, another unit and a value past a bound: each named, each with its cause."""
    whole = patch_of(start_preset())
    cases: list[tuple[str, Quantity, type[VitalError]]] = [
        ("volume.unknown", Quantity(value=0.0, unit=Unit.db), UnknownParameterError),
        ("volume", Quantity(value=0.0, unit=Unit.percent), ParameterUnitError),
        (
            "volume",
            Quantity(value=math.nextafter(-80.0, -math.inf), unit=Unit.db),
            ParameterRangeError,
        ),
        ("filter_1_on", Quantity(value=0.5, unit=Unit.none), ParameterRangeError),
    ]
    for key, value, cause in cases:
        values = {**whole.values, ParameterId(key): value}
        for opaque in (whole.opaque, {}):
            with pytest.raises(PatchRefusedError) as caught:
                preset_of(Patch(instrument="Vital", values=values, opaque=opaque))
            assert caught.value.reason.startswith(f"{key}: ")
            assert type(caught.value.__cause__) is cause
            assert caught.value.reason == f"{key}: {caught.value.__cause__}"


def test_the_first_value_to_refuse_is_the_first_by_id() -> None:
    """Two values that refuse: the one whose id sorts first is named, whatever order they came."""
    late = {ParameterId("volume"): Quantity(value=0.0, unit=Unit.percent)}
    early = {ParameterId("bypass"): Quantity(value=0.5, unit=Unit.none)}
    for values in ({**late, **early}, {**early, **late}):
        with pytest.raises(PatchRefusedError) as caught:
            preset_of(Patch(instrument="Vital", values=values))
        assert caught.value.reason.startswith("bypass: ")


def test_a_patch_the_format_or_the_models_refuse_is_refused_as_the_package() -> None:
    """A section that is no JSON, a carried key Vital never wrote, a slot float past the slots."""
    whole = patch_of(start_preset())
    entry = json.loads(whole.opaque[PRESET_ENTRY])

    def carrying(**floats: float) -> bytes:
        return json.dumps({**entry, "settings": floats}).encode("utf-8")

    refused = [
        {**whole.opaque, f"{SECTION_PREFIX}wavetables": b"[1.0"},
        {**whole.opaque, TUNING_ENTRY: b"[1.0]"},
        {**whole.opaque, f"{LINE_MAPPING_PREFIX}1": b"1.0"},
        {**whole.opaque, PRESET_ENTRY: carrying(not_a_key_of_vital_s=1.0)},
        {**whole.opaque, PRESET_ENTRY: carrying(modulation_65_amount=1.0)},
    ]
    for opaque in refused:
        with pytest.raises(PatchRefusedError) as caught:
            preset_of(Patch(instrument="Vital", values=whole.values, opaque=opaque))
        assert isinstance(caught.value.__cause__, Exception)


@given(FLOATS)
def test_a_float_survives_the_entry_bit_for_bit(held: float) -> None:
    """Any float32, a zero of either sign and a subnormal among them, through the entry's JSON."""
    preset = _with(start_preset(), chorus_damping=held)
    back = preset_of(_through_json(patch_of(preset))).settings.values[PresetKey("chorus_damping")]
    assert struct.pack("<d", back) == struct.pack("<d", held)


def test_a_value_is_checked_by_core_s_rule_and_refused_as_the_package_with_core_s_fields() -> None:
    """`check_value` raises this package's errors, each core's too, core's own the cause."""
    volume = parameter_map().find(ParameterId("volume")).parameter
    check_value(volume, Quantity(value=volume.maximum, unit=Unit.db))
    with pytest.raises(ParameterUnitError) as wrong_unit:
        check_value(volume, Quantity(value=0.0, unit=Unit.percent))
    cause = wrong_unit.value.__cause__
    assert type(cause) is UnitMismatchError
    fields = (wrong_unit.value.parameter_id, wrong_unit.value.expected, wrong_unit.value.given)
    assert (
        fields
        == ("volume", Unit.db, Unit.percent)
        == (cause.parameter_id, cause.expected, cause.given)
    )
    past = math.nextafter(volume.maximum, math.inf)
    with pytest.raises(ParameterRangeError) as out_of_range:
        check_value(volume, Quantity(value=past, unit=Unit.db))
    error = out_of_range.value
    assert type(error.__cause__) is ValueOutOfRangeError
    assert (error.parameter_id, error.minimum, error.maximum, error.given) == (
        "volume",
        volume.minimum,
        volume.maximum,
        past,
    )
