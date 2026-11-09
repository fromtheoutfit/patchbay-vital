"""A preset's models hold together, and refuse what a preset file could not have held."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from patchbay import PatchbayValidationError, PresetKey

from patchbay_vital.preset import (
    KNOWN_SETTINGS,
    MODULATION_SLOTS,
    SLOT_KEY,
    MetadataChange,
    Modulation,
    PresetDiff,
    VitalPreset,
    VitalSettings,
)

_KNOWN_COUNT = 456
_FLOATS = st.floats(allow_nan=False, allow_infinity=False, width=32)
_KEYS = st.sampled_from(sorted(KNOWN_SETTINGS))
_NAMES = st.text(min_size=1)
_EMPTY = Modulation(
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


def _preset(**changes: object) -> VitalPreset:
    """Return a valid preset of empty slots with `changes` applied."""
    fields = {
        **_METADATA,
        "settings": VitalSettings(values={}),
        "modulations": (_EMPTY,) * MODULATION_SLOTS,
        "opaque": {},
    }
    return VitalPreset.model_validate({**fields, **changes})


def test_the_known_keys_are_a_plain_sorted_list(pytestconfig: pytest.Config) -> None:
    """One key a line, sorted and unique, none of them a slot's: the seed of the parameter map."""
    path = pytestconfig.rootpath / "src" / "patchbay_vital" / "settings_keys.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == sorted(set(lines))
    assert len(lines) == _KNOWN_COUNT
    assert set(lines) == KNOWN_SETTINGS
    assert not [line for line in lines if SLOT_KEY.fullmatch(line)]


@given(st.dictionaries(_KEYS, _FLOATS))
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


@given(_NAMES, _KEYS, _FLOATS, _FLOATS, st.none() | _FLOATS)
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
    slot = _EMPTY.model_copy(update={"amount": 0.6680002212524414})
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


@pytest.mark.parametrize("raw", [b"", b"1.0", b'"text"', b"[", b"\xff"], ids=repr)
def test_a_line_mapping_is_a_json_section(raw: bytes) -> None:
    """Only the text of a JSON array or object can be written back into a file."""
    with pytest.raises(PatchbayValidationError):
        _EMPTY.model_validate({**_EMPTY.model_dump(), "line_mapping": raw})


@pytest.mark.parametrize("slots", [MODULATION_SLOTS - 1, MODULATION_SLOTS + 1])
def test_a_preset_has_exactly_its_slots(slots: int) -> None:
    """Every file seen has all of them, used or not."""
    with pytest.raises(PatchbayValidationError):
        _preset(modulations=(_EMPTY,) * slots)


@pytest.mark.parametrize("key", ["volume", "modulations", "modulation_1_amount", ""])
def test_a_section_cannot_take_a_key_the_package_reads(key: str) -> None:
    """A section under such a key would be written twice, or be read back as something else."""
    with pytest.raises(PatchbayValidationError):
        _preset(opaque={key: b"[]"})


@pytest.mark.parametrize("raw", [b"", b"1.0", b"[", b"\xff"], ids=repr)
def test_a_section_is_json(raw: bytes) -> None:
    """A section is written back into the file as it is, so it must be JSON."""
    with pytest.raises(PatchbayValidationError):
        _preset(opaque={"wavetables": raw})


def test_a_section_that_nests_too_deeply_is_refused_as_the_package() -> None:
    """A RecursionError from json is not one a caller of this package should meet."""
    with pytest.raises(PatchbayValidationError):
        _preset(opaque={"wavetables": b"[" * 200_000})


def test_sections_are_read_only_and_sorted() -> None:
    """The unread sections follow the same rule as any mapping on a model."""
    preset = _preset(opaque={"wavetables": b"[]", "lfos": b"[]"})
    assert list(preset.opaque) == ["lfos", "wavetables"]
    with pytest.raises(TypeError):
        preset.opaque[PresetKey("lfos")] = b"{}"  # type: ignore[index]


def test_a_preset_comes_back_from_its_json() -> None:
    """Its mappings and bytes survive pydantic's JSON form, the bytes as base64."""
    slot = _EMPTY.model_copy(update={"line_mapping": b'{"name":"L"}'})
    preset = _preset(
        settings=VitalSettings(values={PresetKey("volume"): 1.5}),
        modulations=(slot,) * MODULATION_SLOTS,
        opaque={"lfos": b"[1.0]"},
        preset_name="p",
        trailing_newline=True,
    )
    assert VitalPreset.model_validate_json(preset.model_dump_json()) == preset


def test_a_diff_with_a_change_is_not_empty() -> None:
    """Any part holding a change makes the diff non-empty."""
    empty = PresetDiff(settings=(), modulations=(), metadata=(), opaque=())
    change = MetadataChange(field="author", old="a", new="b")
    assert empty.is_empty
    assert not empty.model_copy(update={"metadata": (change,)}).is_empty
