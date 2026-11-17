"""A preset carried in a core `Patch`, and back, byte for byte.

`patch_of` turns a `VitalPreset` into the `Patch` an instrument gives, and `preset_of` turns a
patch into the preset an instrument loads. For any preset, `preset_of(patch_of(preset))` writes
the bytes the preset writes, through JSON too. Neither touches the plugin.

**A float is carried in exactly one place.** `values` holds a parameter's value in the unit Vital
displays, and it holds one only where that display can carry the preset's own float: the display
is one the parameter takes (`Parameter.check`), and it converts back to the very float, the sign
of a zero included, by the rule below. That is checked for each float as the patch is built,
never assumed. A float the display cannot carry rides in `opaque` as itself and is not in
`values`: one outside its parameter's bounds, as `flanger_dry_wet` 0.7072 is in presets Vital
ships; one the curve does not give back, as at or below `volume`'s floor; one between an indexed
scale's steps; one whose display another float shows; and a key that is no parameter, as
`chorus_damping`. A key the preset lacks, which an older file may, is in neither
and reads as its parameter's default. So a patch an instrument gives restores every float it
carried, and `values` names each parameter the preset holds a float for, but those.

**A value is taken one way, by `load_patch` and by the check above alike.** On a linear scale, the
curve's inverse rounded to float32 and kept within the scale's ends, where that float's display
is exactly the one given: the display names it, and it is stored. Any other value is taken as
`set` takes it, the float a set of the display holds (`MappedParameter.to_preset`), and on an
indexed scale always so: the nearest step, a half away from zero. So an arbitrary display in a
patch holds what a set of it holds. The one difference is a display that is exactly the display
of a float no set lands on, which a load restores and a set does not: the case of
fromtheoutfit/patchbay#20, `Instrument.get`'s clause.

**What `opaque` holds**, under fixed keys, any other key refused by name:

- `preset`: one small JSON object, keys sorted and no whitespace: the metadata strings the preset
  has, `modulations`, the 64 slots' sources and destinations as pairs, `""` for an empty slot,
  `settings`, the floats `values` does not carry, and `trailing_newline`;
- `settings.<name>`: each section this package does not read, the text the file held;
- `line_mapping.<slot>`: a slot's `line_mapping`, the text the file held;
- `tuning`: the top-level object the plugin's state adds, where the preset has one.

**A patch of values alone is laid over the start preset** (`patchbay_vital.start`): its sections,
routing and metadata, with every parameter the patch does not name at the start's value. A patch
with a `preset` entry is whole as given: what it does not name is absent. Entries without the
`preset` entry they belong to are refused.

**A patch is taken whole or refused**, as `PatchRefusedError`, core's `PatchRejectedError` too,
chained from what refused it. Its reason names the first entry to refuse, in the order a patch is
checked, so it is the same on every run: the instrument's name; then each `opaque` key, sorted;
then each of `values`, sorted by id, for an id that is no parameter, a parameter carried in both
places, its unit and its range; then the preset the entries make. A value in range is never
refused for its resolution: it is taken to a float as above.

`check_loadable` is here too, beside `preset_of`: what the plugin was seen not to load whole,
judged from a preset and the map alone, so it needs no plugin.
"""

import json
import math
import re
from collections.abc import Mapping

from patchbay import (
    Parameter,
    ParameterId,
    Patch,
    PatchbayModel,
    PatchbayValidationError,
    PresetKey,
    Quantity,
    UnitMismatchError,
    ValueOutOfRangeError,
)
from pydantic import Field

from patchbay_vital.errors import (
    ParameterRangeError,
    ParameterUnitError,
    PatchRefusedError,
    UnknownParameterError,
    VitalError,
)
from patchbay_vital.format import (
    METADATA,
    ModulationEntry,
    join_modulations,
    split_modulations,
    writes_same,
)
from patchbay_vital.parameters import MappedParameter, ParameterMap, parameter_map
from patchbay_vital.preset import DECODER, MODULATION_SLOTS, SLOT_KEY, VitalPreset, VitalSettings
from patchbay_vital.start import LFOS, OSCILLATORS, RANDOMS, WARPS, start_preset

PRESET_ENTRY = "preset"
"""The `opaque` key of the entry that makes a patch a whole preset."""

SECTION_PREFIX = "settings."
"""What an unread section's `opaque` key starts with; the rest is the section's name."""

LINE_MAPPING_PREFIX = "line_mapping."
"""What a slot's `line_mapping` key starts with; the rest is the slot's number, from 1."""

TUNING_ENTRY = "tuning"
"""The `opaque` key of the plugin state's top-level `tuning`."""

_SLOT_NUMBER = re.compile("[1-9][0-9]*")
_VERSION = re.compile("[0-9]+([.][0-9]+)*")
_SAMPLE_KEYS = frozenset({"length", "name", "sample_rate", "samples"})
_SECTION_COUNTS = {"wavetables": OSCILLATORS, "lfos": LFOS}
_HELD_COUNTS = {"custom_warps": WARPS, "random_values": RANDOMS}
"""The sections a preset need not hold, and how many entries one that holds them has."""


class _Entry(PatchbayModel, frozen=True):
    """The `preset` entry as read: what a preset holds that neither `values` nor a section does."""

    author: str
    comments: str
    macro1: str
    macro2: str
    macro3: str
    macro4: str
    preset_name: str | None = None
    preset_style: str
    synth_version: str
    modulations: tuple[tuple[str, str], ...] = Field(
        min_length=MODULATION_SLOTS, max_length=MODULATION_SLOTS
    )
    settings: Mapping[str, float]
    trailing_newline: bool = False


def check_value(parameter: Parameter, value: Quantity) -> None:
    """Raise unless `value` is one the parameter takes, as the package's errors.

    Core's own check, `Parameter.check`, and core's own fields: ParameterUnitError for another
    unit than the parameter's, ParameterRangeError for a value outside its bounds or, for a choice
    or a boolean, not a whole number, each chained from the error core raised.
    """
    try:
        parameter.check(value)
    except UnitMismatchError as error:
        raise ParameterUnitError(error.parameter_id, error.expected, error.given) from error
    except ValueOutOfRangeError as error:
        raise ParameterRangeError(
            error.parameter_id, error.minimum, error.maximum, error.given
        ) from error


def _float_of(record: MappedParameter, display: float) -> float:
    """Return the float a preset holds for a display the parameter takes.

    On a linear scale, the curve's inverse rounded to float32 and kept within the scale's ends,
    where that float's own display is exactly the one given: the display names it, as every
    display a patch carries does. Otherwise, as on every indexed scale, the float a set of the
    display holds, `MappedParameter.to_preset`: on an indexed scale the nearest step, a half away
    from zero, which a value between steps shows too and so does not name.
    """
    if record.scale.kind == "indexed":
        return record.to_preset(display)
    named = min(max(record.curve.to_preset(display), record.scale.minimum), record.scale.maximum)
    return named if record.to_display(named) == display else record.to_preset(display)


def _carried_as_a_value(found: ParameterMap, key: str, held: float) -> Quantity | None:
    """Return the display that carries a preset's float, or None where no display can.

    None for a key that is no parameter, a display that is no number a quantity holds, one the
    parameter does not take, and one that does not convert back to the float itself.
    """
    try:
        record = found.find(ParameterId(key))
        value = Quantity(value=record.to_display(held), unit=record.parameter.unit)
        check_value(record.parameter, value)
        back = _float_of(record, value.value)
    except (VitalError, PatchbayValidationError):
        return None
    return value if writes_same(back, held) else None


def _entry_text(
    preset: VitalPreset, entries: tuple[ModulationEntry, ...], carried: Mapping[str, float]
) -> bytes:
    """Write the `preset` entry: sorted keys, no whitespace, each float as its shortest repr."""
    entry: dict[str, object] = {
        name: getattr(preset, name) for name in METADATA if getattr(preset, name) is not None
    }
    entry["modulations"] = [[source, destination] for source, destination, _ in entries]
    entry["settings"] = dict(carried)
    entry["trailing_newline"] = preset.trailing_newline
    text = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def patch_of(preset: VitalPreset) -> Patch:
    """Return the patch that carries a preset: its values, and everything else in `opaque`.

    Every float is in `values` or in the `preset` entry, never both, by the check this module's
    docstring gives, made for each float. `preset_of` gives the preset back.
    """
    found = parameter_map()
    entries, slot_floats = split_modulations(preset.modulations)
    values: dict[ParameterId, Quantity] = {}
    carried: dict[str, float] = {}
    for key, held in {**preset.settings.values, **slot_floats}.items():
        value = _carried_as_a_value(found, key, held)
        if value is None:
            carried[key] = held
        else:
            values[ParameterId(key)] = value
    opaque: dict[str, bytes] = {PRESET_ENTRY: _entry_text(preset, entries, carried)}
    opaque |= {f"{SECTION_PREFIX}{name}": raw for name, raw in preset.opaque.items()}
    for slot, (_, _, line_mapping) in enumerate(entries, 1):
        if line_mapping is not None:
            opaque[f"{LINE_MAPPING_PREFIX}{slot}"] = line_mapping
    if preset.tuning is not None:
        opaque[TUNING_ENTRY] = preset.tuning
    return Patch(instrument=found.instrument, values=values, opaque=opaque)


def _slot_of(key: str) -> int:
    """Return the slot a `line_mapping` key names; PatchRefusedError for a key that names none."""
    number = key.removeprefix(LINE_MAPPING_PREFIX)
    if not _SLOT_NUMBER.fullmatch(number) or int(number) > MODULATION_SLOTS:
        msg = f"{key}: a line mapping belongs to a slot from 1 to {MODULATION_SLOTS}"
        raise PatchRefusedError(msg)
    return int(number)


def _read_opaque(patch: Patch) -> tuple[_Entry | None, dict[str, bytes], dict[int, bytes]]:
    """Sort a patch's `opaque` into the entry, the sections by name and the line mappings by slot.

    Each key is checked in sorted order, the first that is no entry of a Vital patch refused by
    name; then, with no `preset` entry, the first of the others, which belong to none.
    """
    entry: _Entry | None = None
    sections: dict[str, bytes] = {}
    line_mappings: dict[int, bytes] = {}
    for key, raw in patch.opaque.items():
        if key == PRESET_ENTRY:
            try:
                entry = _Entry.model_validate_json(raw)
            except PatchbayValidationError as error:
                msg = f"{key}: {error}"
                raise PatchRefusedError(msg) from error
        elif key == TUNING_ENTRY:
            continue
        elif key.startswith(LINE_MAPPING_PREFIX):
            line_mappings[_slot_of(key)] = raw
        elif key.startswith(SECTION_PREFIX) and key != SECTION_PREFIX:
            sections[key.removeprefix(SECTION_PREFIX)] = raw
        else:
            msg = f"{key}: no entry a Vital patch holds"
            raise PatchRefusedError(msg)
    if entry is None and patch.opaque:
        key = next(iter(patch.opaque))
        msg = f"{key}: the patch has no {PRESET_ENTRY!r} entry for it to belong to"
        raise PatchRefusedError(msg)
    return entry, sections, line_mappings


def _take_values(
    patch: Patch, found: ParameterMap, floats: dict[str, float], carried: Mapping[str, float]
) -> None:
    """Put each of a patch's values into `floats` as the float a preset holds for it.

    In the order of the ids, the first that is no parameter, is carried in the `preset` entry too,
    or is a value its parameter does not take refused by name, chained from the error that says
    which.
    """
    for parameter_id, value in patch.values.items():
        try:
            record = found.find(parameter_id)
            if parameter_id in carried:
                msg = f"{parameter_id}: carried both as a value and in the {PRESET_ENTRY!r} entry"
                raise PatchRefusedError(msg)
            check_value(record.parameter, value)
        except (UnknownParameterError, ParameterUnitError, ParameterRangeError) as error:
            msg = f"{parameter_id}: {error}"
            raise PatchRefusedError(msg) from error
        floats[parameter_id] = _float_of(record, value.value)


def _whole(patch: Patch, found: ParameterMap) -> VitalPreset:
    """Build the preset a patch carries; the format's and the models' refusals go to the caller."""
    entry, sections, line_mappings = _read_opaque(patch)
    if entry is None:
        start = start_preset()
        entries, slot_floats = split_modulations(start.modulations)
        held = (*start.settings.values.items(), *slot_floats.items())
        floats: dict[str, float] = {str(key): value for key, value in held}
        _take_values(patch, found, floats, {})
        fields: dict[str, object] = {name: getattr(start, name) for name in METADATA}
        fields |= {"opaque": start.opaque, "tuning": start.tuning}
        fields["trailing_newline"] = start.trailing_newline
    else:
        entries = tuple(
            (source, destination, line_mappings.get(slot))
            for slot, (source, destination) in enumerate(entry.modulations, 1)
        )
        floats = dict(entry.settings)
        _take_values(patch, found, floats, entry.settings)
        fields = {name: getattr(entry, name) for name in METADATA}
        fields |= {"opaque": sections, "tuning": patch.opaque.get(TUNING_ENTRY)}
        fields["trailing_newline"] = entry.trailing_newline
    slots = {PresetKey(key): value for key, value in floats.items() if SLOT_KEY.fullmatch(key)}
    settings = {PresetKey(key): value for key, value in floats.items() if key not in slots}
    fields["settings"] = VitalSettings(values=settings)
    fields["modulations"] = join_modulations(entries, slots)
    return VitalPreset.model_validate(fields)


def preset_of(patch: Patch) -> VitalPreset:
    """Return the preset a patch carries, whole; PatchRefusedError, by name, when it carries none.

    A patch of values alone is the start preset with those values. Nothing is taken in part: the
    whole patch is checked, in the order this module's docstring gives, before a preset exists.
    """
    found = parameter_map()
    if patch.instrument != found.instrument:
        msg = f"the patch is for instrument {patch.instrument!r}, not {found.instrument!r}"
        raise PatchRefusedError(msg)
    try:
        return _whole(patch, found)
    except PatchRefusedError:
        raise
    except (VitalError, PatchbayValidationError) as error:
        raise PatchRefusedError(str(error)) from error


def _version(text: str) -> tuple[int, ...] | None:
    """Return a version's numbers less its trailing zeros, or None for one not digits and dots.

    So `1.6.4.0` is `1.6.4`, and `1.6.10` is past `1.6.4`.
    """
    if not _VERSION.fullmatch(text):
        return None
    numbers = [int(part) for part in text.split(".")]
    while len(numbers) > 1 and numbers[-1] == 0:
        numbers.pop()
    return tuple(numbers)


def check_loadable(preset: VitalPreset, found: ParameterMap) -> None:
    """Raise PatchRefusedError unless a preset is one the plugin was seen to load whole.

    Vital reports no load it cannot use. It blocks its caller on a modal alert, ignores the whole
    text without a word, loads the floats and keeps the sections it had, or dies of a signal
    inside its own reading of the text (the instrument spec's `verification/probes.txt`, and the
    spec of issue #20's `verification/probes-4-counts.txt` and `arrays-seen.txt`), so what was
    seen to do so is refused here, before the plugin is called, in this order:

    - a `synth_version` that is not digits and dots, which blocks, or is newer than the plugin's,
      `found.vital_version`, which is ignored whole; versions compared by their numbers, trailing
      zeros dropped. A plugin version that is not digits and dots refuses every preset, since
      none can then be shown not to be newer;
    - `wavetables` and `lfos` that are not arrays of three and of eight objects, and a `sample`
      that is not an object holding `length`, `name`, `sample_rate` and `samples`: every preset
      Vital installs, of any version, holds them so, a text without them blocks, and an empty
      array keeps the sections of the preset before it;
    - `custom_warps` and `random_values`, where the preset holds them, that are not arrays of
      three objects. None of the 75 presets Vital installs holds either, and its own saves hold
      three. One entry more killed the process, every time: with `custom_warps` in the first
      load, with `random_values` in the second, the first having returned. One entry fewer, or
      none, loaded without a word and was not held as the text gives it;
    - a parameter's float whose display is no finite number, which `get` could not return.

    It judges a section's shape and not its inside, which this package does not read. A section
    Vital cannot read inside is answered with Vital's alert, which the host answers on macOS and
    which blocks elsewhere (`patchbay_vital.host`). Only the shapes found are refused: a text
    not tried that Vital dies on kills the calling process, and one it loads in part is not
    detected (issue #25). It needs no plugin, so a preset `preset_of` builds can be checked
    where no Vital is installed.
    """
    version, plugin = _version(preset.synth_version), _version(found.vital_version)
    if version is None:
        msg = f"synth_version {preset.synth_version!r} is not a version, digits and dots"
        raise PatchRefusedError(msg)
    if plugin is None:
        msg = (
            f"the plugin's version {found.vital_version!r} is not digits and dots, so no "
            "preset's can be compared with it"
        )
        raise PatchRefusedError(msg)
    if version > plugin:
        msg = (
            f"synth_version {preset.synth_version} is newer than the plugin's {found.vital_version}"
        )
        raise PatchRefusedError(msg)
    _check_sections(preset)
    _, slots = split_modulations(preset.modulations)
    floats = {**preset.settings.values, **slots}
    for record in found.parameters:
        held = floats.get(record.preset_key)
        if held is not None and not math.isfinite(record.to_display(held)):
            msg = f"{record.id}: {held!r} has no display that is a finite number"
            raise PatchRefusedError(msg)


def _check_sections(preset: VitalPreset) -> None:
    """Refuse the first section whose shape is not one `check_loadable` passes, by name."""
    for name, count in _SECTION_COUNTS.items():
        if not _objects(_section(preset, name), count):
            msg = f"settings.{name}: a preset holds an array of {count} objects there"
            raise PatchRefusedError(msg)
    sample = _section(preset, "sample")
    if not (isinstance(sample, dict) and sample.keys() >= _SAMPLE_KEYS):
        msg = f"settings.sample: a preset holds an object there with {sorted(_SAMPLE_KEYS)}"
        raise PatchRefusedError(msg)
    for name, count in _HELD_COUNTS.items():
        section = _section(preset, name)
        if section is not None and not _objects(section, count):
            msg = f"settings.{name}: a preset that holds it holds an array of {count} objects there"
            raise PatchRefusedError(msg)


def _objects(section: object, count: int) -> bool:
    """Whether a section is an array of exactly `count` objects."""
    return (
        isinstance(section, list)
        and len(section) == count
        and all(isinstance(entry, dict) for entry in section)
    )


def _section(preset: VitalPreset, name: str) -> object:
    """Return one of a preset's unread sections, parsed, or None where it has none."""
    raw = preset.opaque.get(PresetKey(name))
    return None if raw is None else DECODER.decode(raw.decode("utf-8"))
