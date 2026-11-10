"""A preset's models hold together, and refuse what a preset file could not have held."""

import copy
import pickle
from types import MappingProxyType

import pytest
from builders import EMPTY_SLOT, FLOATS, KEYS, make_preset
from hypothesis import given
from hypothesis import strategies as st
from patchbay import PatchbayValidationError, PresetKey

from patchbay_vital.preset import (
    KNOWN_SETTINGS,
    MODULATION_SLOTS,
    NEWER_SLOT_FIELDS,
    SLOT_FIELDS,
    SLOT_KEY,
    MetadataChange,
    Modulation,
    PresetDiff,
    VitalPreset,
    VitalSettings,
    decode_end,
)

_KNOWN_COUNT = 456
_NAMES = st.text(min_size=1)


def test_the_known_keys_are_a_plain_sorted_list(pytestconfig: pytest.Config) -> None:
    """One key a line, sorted and unique, none of them a slot's: the seed of the parameter map."""
    path = pytestconfig.rootpath / "src" / "patchbay_vital" / "settings_keys.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == sorted(set(lines))
    assert len(lines) == _KNOWN_COUNT
    assert set(lines) == KNOWN_SETTINGS
    assert not [line for line in lines if SLOT_KEY.fullmatch(line)]


@given(st.dictionaries(KEYS, FLOATS))
def test_settings_take_any_known_keys_and_are_sorted(values: dict[PresetKey, float]) -> None:
    """A key a file lacks is simply absent, and the mapping keeps its keys in order."""
    settings = VitalSettings(values=values)
    assert dict(settings.values) == values
    assert list(settings.values) == sorted(values)


def test_a_key_vital_never_wrote_is_refused() -> None:
    """A key outside the known list is a change of format."""
    with pytest.raises(PatchbayValidationError, match="nope"):
        VitalSettings(values={PresetKey("nope"): 0.0})


def test_a_slot_s_float_is_not_a_setting() -> None:
    """`Modulation` holds these, so they cannot be held twice."""
    with pytest.raises(PatchbayValidationError, match="modulation_1_amount"):
        VitalSettings(values={PresetKey("modulation_1_amount"): 0.0})


def test_a_setting_is_finite() -> None:
    """The base refuses NaN."""
    with pytest.raises(PatchbayValidationError):
        VitalSettings(values={PresetKey("volume"): float("nan")})


def test_settings_are_read_only_and_unhashable() -> None:
    """A frozen model's mapping cannot be changed under it, and has no hash."""
    settings = VitalSettings(values={PresetKey("volume"): 1.0})
    with pytest.raises(TypeError):
        settings.values[PresetKey("volume")] = 2.0  # type: ignore[index]
    with pytest.raises(TypeError):
        hash(settings)


@given(_NAMES, KEYS, FLOATS, FLOATS, st.none() | FLOATS)
def test_a_routed_slot_holds_what_it_is_given(
    source: str, destination: PresetKey, amount: float, power: float, ramp: float | None
) -> None:
    """A slot with a source and a destination is routed, whatever its floats."""
    slot = Modulation(
        source=source,
        destination=destination,
        amount=amount,
        bipolar=0.0,
        bypass=0.0,
        power=power,
        stereo=0.0,
        ramp_up=ramp,
    )
    assert not slot.is_empty
    assert (slot.amount, slot.power, slot.ramp_up, slot.ramp_down) == (amount, power, ramp, None)


def test_an_empty_slot_keeps_a_value_vital_left_behind() -> None:
    """Vital leaves a non-zero amount on some empty slots, so it is not dropped."""
    slot = EMPTY_SLOT.model_copy(update={"amount": 0.6680002212524414})
    assert slot.is_empty
    assert slot.amount == 0.6680002212524414  # noqa: PLR2004 - the value from a shipped preset


@pytest.mark.parametrize(
    ("source", "destination"),
    [("lfo_1", None), (None, PresetKey("volume"))],
    ids=["no destination", "no source"],
)
def test_a_half_routed_slot_is_refused(source: str | None, destination: PresetKey | None) -> None:
    """A source and a destination go together, as in every file seen."""
    with pytest.raises(PatchbayValidationError, match="neither"):
        Modulation(
            source=source,
            destination=destination,
            amount=0.0,
            bipolar=0.0,
            bypass=0.0,
            power=0.0,
            stereo=0.0,
        )


@pytest.mark.parametrize(
    ("source", "destination"), [("", PresetKey("volume")), ("lfo_1", PresetKey(""))]
)
def test_an_empty_name_is_refused(source: str, destination: PresetKey) -> None:
    """An empty slot is None; an empty string is what the file writes, not what a model holds."""
    with pytest.raises(PatchbayValidationError):
        Modulation(
            source=source,
            destination=destination,
            amount=0.0,
            bipolar=0.0,
            bypass=0.0,
            power=0.0,
            stereo=0.0,
        )


@pytest.mark.parametrize("raw", [b"", b"1.0", b'"text"', b"[", b"\xff", b"[NaN]", b"{} "], ids=repr)
def test_a_line_mapping_is_a_json_section(raw: bytes) -> None:
    """Only the text of a JSON array or object can be written back into a file."""
    with pytest.raises(PatchbayValidationError):
        EMPTY_SLOT.model_validate({**EMPTY_SLOT.model_dump(), "line_mapping": raw})


@pytest.mark.parametrize("slots", [MODULATION_SLOTS - 1, MODULATION_SLOTS + 1])
def test_a_preset_has_exactly_its_slots(slots: int) -> None:
    """Every file seen has all of them, used or not."""
    with pytest.raises(PatchbayValidationError):
        make_preset(modulations=(EMPTY_SLOT,) * slots)


@pytest.mark.parametrize("key", ["volume", "modulations", "modulation_1_amount", ""])
def test_a_section_cannot_take_a_key_the_package_reads(key: str) -> None:
    """A section under such a key would be written twice, or be read back as something else."""
    with pytest.raises(PatchbayValidationError):
        make_preset(opaque={key: b"[]"})


@pytest.mark.parametrize("raw", [b"", b"1.0", b"[", b"\xff", b"[NaN]", b"[1] ", b" [1]"], ids=repr)
def test_a_section_is_json(raw: bytes) -> None:
    """A section is written back into the file as it is, so it must be JSON."""
    with pytest.raises(PatchbayValidationError):
        make_preset(opaque={"wavetables": raw})


def test_a_section_that_nests_too_deeply_is_refused_as_the_package() -> None:
    """A RecursionError from json is not one a caller of this package should meet."""
    with pytest.raises(PatchbayValidationError):
        make_preset(opaque={"wavetables": b"[" * 200_000})


def test_the_decoder_s_end_names_what_nests_too_deeply() -> None:
    """One function turns the decoder's RecursionError into a ValueError naming the text's part."""
    assert decode_end('{"a":1} and more', "a section") == 7  # noqa: PLR2004 - the object's end
    with pytest.raises(ValueError, match="the text nests too deeply to read") as caught:
        decode_end("[" * 200_000, "the text")
    assert isinstance(caught.value.__cause__, RecursionError)


@pytest.mark.parametrize("raw", [b"[]", b"1.0", b"", b"{", b"{} "], ids=repr)
def test_a_tuning_is_the_text_of_an_object(raw: bytes) -> None:
    """The plugin's tuning is a JSON object, written back into its state as it is."""
    with pytest.raises(PatchbayValidationError):
        make_preset(tuning=raw)


def test_a_tuning_is_kept_as_given() -> None:
    """An object's text is held as it is, unread, and a preset without one holds None."""
    assert make_preset(tuning=b'{"default":true}').tuning == b'{"default":true}'
    assert make_preset().tuning is None


def test_sections_are_read_only_and_sorted() -> None:
    """The unread sections follow the same rule as any mapping on a model."""
    preset = make_preset(opaque={"wavetables": b"[]", "lfos": b"[]"})
    assert list(preset.opaque) == ["lfos", "wavetables"]
    with pytest.raises(TypeError):
        preset.opaque[PresetKey("lfos")] = b"{}"  # type: ignore[index]


def test_a_preset_comes_back_from_its_json() -> None:
    """Its mappings and bytes survive pydantic's JSON form, the bytes as base64."""
    slot = EMPTY_SLOT.model_copy(update={"line_mapping": b'{"name":"L"}'})
    preset = make_preset(
        settings=VitalSettings(values={PresetKey("volume"): 1.5}),
        modulations=(slot,) * MODULATION_SLOTS,
        opaque={"lfos": b"[1.0]"},
        preset_name="p",
        tuning=b'{"default":true}',
        trailing_newline=True,
    )
    assert VitalPreset.model_validate_json(preset.model_dump_json()) == preset


def test_a_diff_with_a_change_is_not_empty() -> None:
    """Any part holding a change makes the diff non-empty."""
    empty = PresetDiff(settings=(), modulations=(), metadata=(), opaque=())
    change = MetadataChange(field="author", old="a", new="b")
    assert empty.is_empty
    assert not empty.model_copy(update={"metadata": (change,)}).is_empty


@pytest.mark.parametrize("field", ["amount", *SLOT_FIELDS, *NEWER_SLOT_FIELDS])
def test_the_slot_key_matches_every_slot_field(field: str) -> None:
    """A field added to the tuples is matched without touching the pattern."""
    assert SLOT_KEY.fullmatch(f"modulation_64_{field}")


@pytest.mark.parametrize("key", ["modulation_0_amount", "modulation_1_nope", "modulations"])
def test_the_slot_key_matches_nothing_else(key: str) -> None:
    """Slots count from one, and a field outside the tuples is not a slot's."""
    assert not SLOT_KEY.fullmatch(key)


@pytest.mark.parametrize(
    "field",
    ["author", "comments", "macro1", "macro2", "macro3", "macro4", "preset_name", "preset_style"],
)
def test_metadata_is_text_utf_8_can_hold(field: str) -> None:
    """A lone surrogate could never be written, so it is refused where it comes in."""
    with pytest.raises(PatchbayValidationError):
        make_preset(**{field: "\ud800"})


@pytest.mark.parametrize(
    ("source", "destination"), [("\ud800", PresetKey("volume")), ("lfo_1", PresetKey("\ud800"))]
)
def test_a_slot_s_names_are_text_utf_8_can_hold(source: str, destination: PresetKey) -> None:
    """The same holds of what a slot routes."""
    with pytest.raises(PatchbayValidationError):
        EMPTY_SLOT.model_validate(
            {**EMPTY_SLOT.model_dump(), "source": source, "destination": destination}
        )


def _full_preset() -> VitalPreset:
    """Return a preset with something in each of its mappings."""
    return make_preset(
        settings=VitalSettings(values={PresetKey("volume"): 1.5}), opaque={"lfos": b"[1.0]"}
    )


def _assert_same_and_read_only(copied: VitalPreset, original: VitalPreset) -> None:
    """Assert a copy equals its original, with mappings that still cannot be changed."""
    assert copied == original
    assert copied is not original
    assert isinstance(copied.settings.values, MappingProxyType)
    assert isinstance(copied.opaque, MappingProxyType)


def test_a_preset_can_be_pickled() -> None:
    """Batch work across processes pickles every preset it hands over."""
    preset = _full_preset()
    _assert_same_and_read_only(pickle.loads(pickle.dumps(preset)), preset)  # noqa: S301 - our own bytes


def test_a_preset_can_be_deep_copied() -> None:
    """A deep copy of a frozen preset is an equal one."""
    preset = _full_preset()
    _assert_same_and_read_only(copy.deepcopy(preset), preset)
    _assert_same_and_read_only(preset.model_copy(deep=True), preset)


def test_updating_a_deep_copy_leaves_the_original_alone() -> None:
    """A deep copy shares only what cannot change, never the model's own fields."""
    preset = _full_preset()
    preset.model_copy(deep=True, update={"author": "someone"})
    assert preset.author == ""
