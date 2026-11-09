"""A preset file comes back byte for byte, its faults are named, and a diff says what differs."""

import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from patchbay import PatchbayValidationError, PresetKey

from patchbay_vital.errors import MalformedPresetError, PresetFileError, UnknownSettingError
from patchbay_vital.format import (
    ModulationEntry,
    diff,
    dump,
    dumps,
    join_modulations,
    load,
    loads,
    split_modulations,
)
from patchbay_vital.preset import (
    KNOWN_SETTINGS,
    MODULATION_SLOTS,
    NEWER_SLOT_FIELDS,
    SLOT_FIELDS,
    Modulation,
    VitalPreset,
    VitalSettings,
)

_EMPTY_ENTRY = '{"destination":"","source":""}'
_FLOATS = st.floats(allow_nan=False, allow_infinity=False, width=32)
_KEYS = st.sampled_from(sorted(KNOWN_SETTINGS))
_SETTINGS = st.dictionaries(_KEYS, _FLOATS, max_size=20)
_EMPTY = Modulation(
    source=None, destination=None, amount=0.0, bipolar=0.0, bypass=0.0, power=0.0, stereo=0.0
)
_ROUTED = _EMPTY.model_copy(update={"source": "lfo_1", "destination": PresetKey("volume")})
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


def _preset(**changes: object) -> VitalPreset:
    """Return a valid preset of empty slots with `changes` applied."""
    fields = {
        **_METADATA,
        "settings": VitalSettings(values={}),
        "modulations": (_EMPTY,) * MODULATION_SLOTS,
        "opaque": {},
    }
    return VitalPreset.model_validate({**fields, **changes})


@pytest.fixture
def fixture_text(pytestconfig: pytest.Config) -> str:
    """Return a real 1.6.4 preset's text, with its media replaced by values written for the test."""
    path = pytestconfig.rootpath / "tests" / "data" / "init-media-replaced.vital"
    return path.read_bytes().decode("utf-8")


def _set_value(text: str, key: str, written: str) -> str:
    """Return the text with one setting's written value replaced, which must take effect."""
    changed, count = re.subn(rf'"{key}":[^,}}]+', f'"{key}":{written}', text, count=1)
    assert count == 1
    return changed


def _insert_setting(text: str, member: str) -> str:
    """Return the text with a member added at the start of `settings`."""
    assert '"settings":{' in text
    return text.replace('"settings":{', f'"settings":{{{member},', 1)


def test_a_preset_comes_back_byte_for_byte(fixture_text: str) -> None:
    """The claim of this format, on the one real file the suite carries."""
    assert dumps(loads(fixture_text)) == fixture_text


def test_a_1_6_4_preset_reads_as_its_models(fixture_text: str) -> None:
    """Its metadata, floats, slots and sections each land where they belong."""
    preset = loads(fixture_text)
    assert (preset.synth_version, preset.preset_name) == ("1.6.4", "fixture")
    assert len(preset.modulations) == MODULATION_SLOTS
    assert all(slot.is_empty and slot.ramp_up == -10.0 for slot in preset.modulations)  # noqa: PLR2004 - Vital's default
    assert sorted(preset.opaque) == [
        "custom_warps",
        "lfos",
        "random_values",
        "sample",
        "wavetables",
    ]
    assert not [key for key in preset.settings.values if key.startswith("modulation_")]


def test_a_file_without_the_newer_keys_comes_back_without_them(fixture_text: str) -> None:
    """Files before 1.6.4 lack the ramps and the name, and writing must not invent them."""
    older = re.sub(r'"modulation_[0-9]+_ramp_(up|down)":[^,}]+,', "", fixture_text)
    older = re.sub(r'"preset_name":"[^"]*",', "", older)
    preset = loads(older)
    assert preset.preset_name is None
    assert all(slot.ramp_up is None and slot.ramp_down is None for slot in preset.modulations)
    assert dumps(preset) == older


def test_a_value_left_on_an_empty_slot_survives(fixture_text: str) -> None:
    """Vital leaves amounts on empty slots: 19 in the files shipped, and they must round trip."""
    text = _set_value(fixture_text, "modulation_3_amount", "0.6680002212524414")
    preset = loads(text)
    assert preset.modulations[2].is_empty
    assert preset.modulations[2].amount == 0.6680002212524414  # noqa: PLR2004 - a shipped value
    assert dumps(preset) == text


def test_a_trailing_newline_survives(fixture_text: str) -> None:
    """Three of Vital's own presets end in one."""
    text = fixture_text + "\n"
    preset = loads(text)
    assert preset.trailing_newline
    assert dumps(preset) == text


def test_strings_are_written_as_vital_writes_them() -> None:
    """UTF-8 stays raw and only what JSON requires is escaped, as nlohmann::json does."""
    text = dumps(_preset(comments='a\n"\\/é\x01'))
    assert '"comments":"a\\n\\"\\\\/é\\u0001"' in text
    assert loads(text).comments == 'a\n"\\/é\x01'


_MALFORMED: dict[str, Callable[[str], str]] = {
    "not json": lambda _: "nope",
    "empty": lambda _: "",
    "an array": lambda _: "[]",
    "text after": lambda t: t + "x",
    "byte order mark": lambda t: "﻿" + t,
    "repeated key": lambda t: _insert_setting(t, '"volume":1.0'),
    "NaN": lambda t: _set_value(t, "volume", "NaN"),
    "Infinity": lambda t: _set_value(t, "volume", "Infinity"),
    "int setting": lambda t: _set_value(t, "volume", "1"),
    "string setting": lambda t: _set_value(t, "volume", '"x"'),
    "null setting": lambda t: _set_value(t, "volume", "null"),
    "bool setting": lambda t: _set_value(t, "volume", "true"),
    "a section under a setting's key": lambda t: _set_value(t, "volume", "[1.0]"),
    "no settings": lambda _: '{"author":""}',
    "no modulations": lambda t: t.replace('"modulations":[', '"modulationz":[', 1),
    "metadata missing": lambda t: t.replace('"author":"",', "", 1),
    "metadata a number": lambda t: t.replace('"author":""', '"author":1', 1),
    "too few slots": lambda t: t.replace(f'"modulations":[{_EMPTY_ENTRY},', '"modulations":[', 1),
    "half-routed slot": lambda t: t.replace(
        _EMPTY_ENTRY, '{"destination":"volume","source":""}', 1
    ),
    "slot float missing": lambda t: re.sub(r'"modulation_1_amount":[^,]+,', "", t, count=1),
    "unknown slot key": lambda t: t.replace(
        _EMPTY_ENTRY, '{"destination":"","source":"","x":1}', 1
    ),
    "source a number": lambda t: t.replace(_EMPTY_ENTRY, '{"destination":"","source":1}', 1),
    "nesting too deep": lambda t: _insert_setting(t, '"deep":' + "[" * 200_000 + "]" * 200_000),
    "lone surrogate": lambda t: _insert_setting(t, '"s":["\ud800"]'),
}


@pytest.mark.parametrize("damage", _MALFORMED.values(), ids=_MALFORMED.keys())
def test_a_malformed_preset_is_refused_as_the_package(
    fixture_text: str, damage: Callable[[str], str]
) -> None:
    """Nothing from json or pydantic leaves `loads`."""
    with pytest.raises(MalformedPresetError):
        loads(damage(fixture_text))


@pytest.mark.parametrize(
    ("member", "key"),
    [
        ('"brand_new_setting":1.0', "brand_new_setting"),
        ('"modulation_65_amount":0.0', "modulation_65_amount"),
        ('"modulation_1_new_field":0.0', "modulation_1_new_field"),
    ],
)
def test_an_unknown_float_is_named(fixture_text: str, member: str, key: str) -> None:
    """A float Vital is not known to write is a change of format, and says which key."""
    with pytest.raises(UnknownSettingError) as caught:
        loads(_insert_setting(fixture_text, member))
    assert caught.value.key == key


def test_an_unknown_top_level_key_is_named(fixture_text: str) -> None:
    """The envelope is typed and closed."""
    text = fixture_text.replace('"author":', '"authors":', 1)
    with pytest.raises(UnknownSettingError) as caught:
        loads(text)
    assert caught.value.key == "authors"


def test_an_unknown_section_is_kept_and_written_back(fixture_text: str) -> None:
    """A section this package has never seen still round trips, byte for byte."""
    text = _insert_setting(fixture_text, '"aaa_section":{"a":[1.50, 2]}')
    preset = loads(text)
    assert preset.opaque[PresetKey("aaa_section")] == b'{"a":[1.50, 2]}'
    assert dumps(preset) == text


def test_a_refusal_is_chained_from_what_it_stands_in_for(fixture_text: str) -> None:
    """The cause stays on `__cause__`, for json and for a model alike."""
    with pytest.raises(MalformedPresetError) as from_json:
        loads("{nope")
    assert isinstance(from_json.value.__cause__, json.JSONDecodeError)
    with pytest.raises(MalformedPresetError) as from_model:
        loads(fixture_text.replace('"author":"",', "", 1))
    assert isinstance(from_model.value.__cause__, PatchbayValidationError)


def test_a_preset_is_written_to_a_file_and_read_back(fixture_text: str, tmp_path: Path) -> None:
    """`dump` writes the bytes `dumps` returns, with no newline translation."""
    preset = loads(fixture_text)
    path = tmp_path / "a.vital"
    dump(preset, path)
    assert path.read_bytes() == fixture_text.encode("utf-8")
    assert load(path) == preset


def test_a_missing_file_is_named(tmp_path: Path) -> None:
    """No OSError leaves `load`."""
    path = tmp_path / "absent.vital"
    with pytest.raises(PresetFileError) as caught:
        load(path)
    assert caught.value.path == str(path)
    assert isinstance(caught.value.__cause__, OSError)


def test_a_file_that_cannot_be_written_is_named(tmp_path: Path) -> None:
    """No OSError leaves `dump`."""
    with pytest.raises(PresetFileError) as caught:
        dump(_preset(), tmp_path)
    assert caught.value.path == str(tmp_path)


def test_bytes_that_are_not_utf_8_are_malformed(tmp_path: Path) -> None:
    """`load` decodes strictly, as Vital writes UTF-8."""
    path = tmp_path / "a.vital"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(MalformedPresetError):
        load(path)


def test_a_string_utf_8_cannot_hold_is_malformed_on_writing(tmp_path: Path) -> None:
    """A lone surrogate reaches `dump` only through a model built directly."""
    with pytest.raises(MalformedPresetError):
        dump(_preset(comments="\ud800"), tmp_path / "a.vital")


_ENTRY_NAMES = st.just(("", "")) | st.tuples(
    st.text(min_size=1), st.sampled_from(sorted(KNOWN_SETTINGS))
)
_SLOT = st.tuples(
    _ENTRY_NAMES,
    st.none() | st.just(b'{"name":"Linear","points":[0.0,1.0]}'),
    st.fixed_dictionaries(dict.fromkeys(SLOT_FIELDS, _FLOATS)),
    st.fixed_dictionaries(
        {},
        optional=dict.fromkeys(NEWER_SLOT_FIELDS, _FLOATS),
    ),
)
_SLOTS = st.lists(_SLOT, min_size=1, max_size=8)


def _flatten(
    slots: list[tuple[tuple[str, str], bytes | None, dict[str, float], dict[str, float]]],
) -> tuple[tuple[ModulationEntry, ...], dict[PresetKey, float]]:
    """Return generated slots as the file holds them: the routing list and the per-slot floats."""
    entries = tuple((names[0], names[1], mapping) for names, mapping, _, _ in slots)
    floats = {
        PresetKey(f"modulation_{slot}_{field}"): value
        for slot, (_, _, required, newer) in enumerate(slots, 1)
        for field, value in (required | newer).items()
    }
    return entries, floats


@given(_SLOTS)
def test_split_reverses_join_over_arbitrary_slot_contents(
    slots: list[tuple[tuple[str, str], bytes | None, dict[str, float], dict[str, float]]],
) -> None:
    """Whatever a slot holds, empty or routed, with or without the newer fields, none is lost."""
    entries, floats = _flatten(slots)
    assert split_modulations(join_modulations(entries, floats)) == (entries, floats)


@given(_SLOTS)
def test_join_reverses_split(
    slots: list[tuple[tuple[str, str], bytes | None, dict[str, float], dict[str, float]]],
) -> None:
    """The models come back equal from the file's form."""
    joined = join_modulations(*_flatten(slots))
    assert join_modulations(*split_modulations(joined)) == joined


def test_join_needs_every_slot_s_required_floats() -> None:
    """A float every file holds is not optional."""
    with pytest.raises(MalformedPresetError, match="modulation_1_bipolar"):
        join_modulations([("", "", None)], {PresetKey("modulation_1_amount"): 0.0})


def test_join_names_a_float_beyond_the_slots() -> None:
    """A float for a slot that does not exist is a change of format."""
    floats = {PresetKey(f"modulation_1_{field}"): 0.0 for field in SLOT_FIELDS}
    floats[PresetKey("modulation_2_amount")] = 0.0
    with pytest.raises(UnknownSettingError, match="modulation_2_amount"):
        join_modulations([("", "", None)], floats)


@given(_SETTINGS)
def test_a_preset_does_not_differ_from_itself(values: dict[PresetKey, float]) -> None:
    """The diff of a preset against itself says nothing."""
    preset = _preset(settings=VitalSettings(values=values))
    assert diff(preset, preset).is_empty


@given(_SETTINGS, _SETTINGS)
def test_a_diff_applied_gives_the_other_settings(
    old: dict[PresetKey, float], new: dict[PresetKey, float]
) -> None:
    """Setting each changed key to its new value, or dropping it, turns `a` into `b`."""
    a, b = (_preset(settings=VitalSettings(values=values)) for values in (old, new))
    changes = diff(a, b).settings
    assert [change.key for change in changes] == sorted(change.key for change in changes)
    applied = dict(old)
    for change in changes:
        if change.new is None:
            del applied[change.key]
        else:
            applied[change.key] = change.new
    assert applied == new


def test_a_diff_says_how_each_slot_changed() -> None:
    """Routed where it was empty is added, emptied is removed, anything else changed; by slot."""
    louder = _ROUTED.model_copy(update={"amount": 0.5})
    stale = _EMPTY.model_copy(update={"amount": 0.25})
    a = list((_EMPTY,) * MODULATION_SLOTS)
    b = list(a)
    a[4], b[4] = _ROUTED, louder
    b[0] = _ROUTED
    a[2] = _ROUTED
    b[9] = stale
    changes = diff(_preset(modulations=tuple(a)), _preset(modulations=tuple(b))).modulations
    assert [(change.slot, change.kind) for change in changes] == [
        (1, "added"),
        (3, "removed"),
        (5, "changed"),
        (10, "changed"),
    ]


def test_a_diff_reports_metadata_by_field() -> None:
    """Each field that differs, in name order, a field one side lacks as None."""
    a = _preset(author="a", preset_name="p")
    b = _preset(author="b", trailing_newline=True)
    assert [(c.field, c.old, c.new) for c in diff(a, b).metadata] == [
        ("author", "a", "b"),
        ("preset_name", "p", None),
        ("trailing_newline", False, True),
    ]


def test_a_diff_reports_sections_by_name_and_size_only() -> None:
    """A section is not read, so a change is a name and two sizes."""
    a = _preset(opaque={"lfos": b"[1.0]", "sample": b"{}", "wavetables": b"[]"})
    b = _preset(opaque={"lfos": b"[2.0]", "wavetables": b"[]", "zeta": b"[1]"})
    assert [(c.name, c.old_size, c.new_size) for c in diff(a, b).opaque] == [
        ("lfos", 5, 5),
        ("sample", 2, None),
        ("zeta", None, 3),
    ]
