"""Reading, writing and comparing a `.vital` file, byte for byte.

`loads` walks the top level and `settings` by span, so every section it does not interpret is kept
as the very text the file held. `dumps` writes what Vital writes: keys sorted at every depth, no
whitespace, raw UTF-8 and floats through `grisu2`, so `dumps(loads(text)) == text` for a file Vital
saved.

An unknown float setting or top-level key is `UnknownSettingError`, so a change of format is
noticed; an unknown section under `settings` is kept with the unread ones. Anything else wrong with
a file is `MalformedPresetError`, and neither pydantic's error nor `json`'s leaves this module.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from patchbay import PatchbayValidationError, PresetKey

from patchbay_vital.errors import MalformedPresetError, PresetFileError, UnknownSettingError
from patchbay_vital.grisu2 import format_float
from patchbay_vital.preset import (
    KNOWN_SETTINGS,
    MODULATION_SLOTS,
    MODULATIONS_KEY,
    NEWER_SLOT_FIELDS,
    SLOT_FIELDS,
    SLOT_KEY,
    MetadataChange,
    Modulation,
    ModulationChange,
    OpaqueChange,
    PresetDiff,
    SettingChange,
    VitalPreset,
    VitalSettings,
)

type ModulationEntry = tuple[str, str, bytes | None]
"""One entry of the file's routing list: source, destination, `line_mapping`; `""` when empty."""

type _Member = tuple[str, int, int, object]
"""An object's member: its key, where its value starts and ends, and the value parsed."""

_SETTINGS_KEY = "settings"
_SOURCE, _DESTINATION, _LINE_MAPPING = "source", "destination", "line_mapping"
_METADATA = (
    "author",
    "comments",
    "macro1",
    "macro2",
    "macro3",
    "macro4",
    "preset_name",
    "preset_style",
    "synth_version",
)
_WHITESPACE = " \t\n\r"


def _refuse_constant(name: str) -> object:
    """Refuse the NaN and Infinity tokens Python's JSON parser would otherwise accept."""
    msg = f"{name} is not a number a preset can hold"
    raise ValueError(msg)


_DECODER = json.JSONDecoder(parse_constant=_refuse_constant)


def _skip_space(text: str, index: int) -> int:
    """Return the index of the next character that is not JSON whitespace."""
    while index < len(text) and text[index] in _WHITESPACE:
        index += 1
    return index


def _expect(text: str, index: int, character: str) -> int:
    """Return the index past `character`, which must be the next thing in the text."""
    index = _skip_space(text, index)
    if not text.startswith(character, index):
        msg = f"expected {character!r} at offset {index}"
        raise MalformedPresetError(msg)
    return index + 1


def _members(text: str, start: int) -> tuple[list[_Member], int]:
    """Return the members of the object at `start`, and the index past it."""
    index = _skip_space(text, _expect(text, start, "{"))
    members: list[_Member] = []
    if text.startswith("}", index):
        return members, index + 1
    seen: set[str] = set()
    while True:
        key, index = _DECODER.raw_decode(text, index)
        if not isinstance(key, str) or key in seen:
            msg = f"a key is missing or repeated before offset {index}: {key!r}"
            raise MalformedPresetError(msg)
        seen.add(key)
        first = _skip_space(text, _expect(text, index, ":"))
        value, end = _DECODER.raw_decode(text, first)
        members.append((key, first, end, value))
        index = _skip_space(text, end)
        if text.startswith("}", index):
            return members, index + 1
        index = _skip_space(text, _expect(text, index, ","))


def _modulation_entry(text: str, members: list[_Member]) -> ModulationEntry:
    """Return one entry of the routing list from its members."""
    by_key = {key: (first, end, value) for key, first, end, value in members}
    unknown = sorted(set(by_key) - {_SOURCE, _DESTINATION, _LINE_MAPPING})
    if unknown:
        msg = f"a modulation has keys this package does not know: {unknown!r}"
        raise MalformedPresetError(msg)
    source = by_key.get(_SOURCE, (0, 0, None))[2]
    destination = by_key.get(_DESTINATION, (0, 0, None))[2]
    if not isinstance(source, str) or not isinstance(destination, str):
        msg = "a modulation has a source and a destination, each a string"
        raise MalformedPresetError(msg)
    if _LINE_MAPPING not in by_key:
        return source, destination, None
    first, end, _ = by_key[_LINE_MAPPING]
    return source, destination, text[first:end].encode("utf-8")


def _modulation_entries(text: str, start: int) -> tuple[ModulationEntry, ...]:
    """Return the entries of the routing list at `start`."""
    index = _skip_space(text, _expect(text, start, "["))
    entries: list[ModulationEntry] = []
    if text.startswith("]", index):
        return ()
    while True:
        members, index = _members(text, index)
        entries.append(_modulation_entry(text, members))
        index = _skip_space(text, index)
        if text.startswith("]", index):
            return tuple(entries)
        index = _skip_space(text, _expect(text, index, ","))


def _slot_key(slot: int, field: str) -> PresetKey:
    """Return the `settings` key of a slot's float."""
    return PresetKey(f"modulation_{slot}_{field}")


def _join_slot(slot: int, entry: ModulationEntry, floats: dict[PresetKey, float]) -> Modulation:
    """Build one slot, taking its floats out of `floats`."""
    source, destination, line_mapping = entry
    fields: dict[str, float | None] = {}
    for field in SLOT_FIELDS:
        key = _slot_key(slot, field)
        if key not in floats:
            msg = f"slot {slot} has no {key!r}"
            raise MalformedPresetError(msg)
        fields[field] = floats.pop(key)
    for field in NEWER_SLOT_FIELDS:
        fields[field] = floats.pop(_slot_key(slot, field), None)
    return Modulation.model_validate(
        {
            _SOURCE: source or None,
            _DESTINATION: destination or None,
            _LINE_MAPPING: line_mapping,
            **fields,
        }
    )


def join_modulations(
    entries: Sequence[ModulationEntry], floats: Mapping[PresetKey, float]
) -> tuple[Modulation, ...]:
    """Join the file's routing list with its per-slot floats, the reverse of `split_modulations`.

    MalformedPresetError when a slot lacks a float every file holds, UnknownSettingError for a
    per-slot float beyond the slots there are.
    """
    remaining = dict(floats)
    joined = tuple(_join_slot(slot, entry, remaining) for slot, entry in enumerate(entries, 1))
    if remaining:
        raise UnknownSettingError(min(remaining))
    return joined


def split_modulations(
    modulations: Sequence[Modulation],
) -> tuple[tuple[ModulationEntry, ...], dict[PresetKey, float]]:
    """Split slots into the file's routing list and its per-slot floats, keeping what each holds.

    A newer field that is None is left out, as the file that lacked it did.
    """
    entries: list[ModulationEntry] = []
    floats: dict[PresetKey, float] = {}
    for slot, modulation in enumerate(modulations, 1):
        entries.append(
            (modulation.source or "", modulation.destination or "", modulation.line_mapping)
        )
        for field in (*SLOT_FIELDS, *NEWER_SLOT_FIELDS):
            value: float | None = getattr(modulation, field)
            if value is not None:
                floats[_slot_key(slot, field)] = value
    return tuple(entries), floats


def _read_settings(
    text: str, start: int
) -> tuple[
    dict[PresetKey, float],
    dict[PresetKey, float],
    dict[PresetKey, bytes],
    tuple[ModulationEntry, ...],
]:
    """Sort `settings` into floats, per-slot floats, unread sections and the routing list."""
    values: dict[PresetKey, float] = {}
    floats: dict[PresetKey, float] = {}
    opaque: dict[PresetKey, bytes] = {}
    entries: tuple[ModulationEntry, ...] | None = None
    for name, first, end, value in _members(text, start)[0]:
        key = PresetKey(name)
        if key == MODULATIONS_KEY:
            entries = _modulation_entries(text, first)
        elif isinstance(value, list | dict):
            opaque[key] = text[first:end].encode("utf-8")
        elif not isinstance(value, float):
            msg = f"{name!r} holds {value!r}, where a setting is a float"
            raise MalformedPresetError(msg)
        elif SLOT_KEY.fullmatch(name):
            floats[key] = value
        elif key in KNOWN_SETTINGS:
            values[key] = value
        else:
            raise UnknownSettingError(name)
    if entries is None:
        msg = f"{_SETTINGS_KEY} has no {MODULATIONS_KEY!r}"
        raise MalformedPresetError(msg)
    if len(entries) != MODULATION_SLOTS:
        msg = f"a preset has {MODULATION_SLOTS} modulation slots, this one {len(entries)}"
        raise MalformedPresetError(msg)
    return values, floats, opaque, entries


def _parse(text: str) -> VitalPreset:
    """Read a preset, leaving the errors of json and pydantic for `loads` to report."""
    body = text.removesuffix("\n")
    members, end = _members(body, 0)
    if _skip_space(body, end) != len(body):
        msg = f"text follows the preset at offset {end}"
        raise MalformedPresetError(msg)
    fields: dict[str, object] = {"trailing_newline": text.endswith("\n")}
    settings_start: int | None = None
    for name, first, _, value in members:
        if name == _SETTINGS_KEY:
            settings_start = first
        elif name in _METADATA:
            fields[name] = value
        else:
            raise UnknownSettingError(name)
    if settings_start is None:
        msg = f"a preset has {_SETTINGS_KEY!r}"
        raise MalformedPresetError(msg)
    values, floats, opaque, entries = _read_settings(body, settings_start)
    return VitalPreset.model_validate(
        {
            **fields,
            _SETTINGS_KEY: VitalSettings(values=values),
            "modulations": join_modulations(entries, floats),
            "opaque": opaque,
        }
    )


def loads(text: str) -> VitalPreset:
    """Read a preset from the text of a `.vital` file.

    UnknownSettingError for a float setting or top-level key Vital is not known to write,
    MalformedPresetError for anything else this package cannot read.
    """
    try:
        return _parse(text)
    except PatchbayValidationError as error:
        raise MalformedPresetError(str(error)) from error
    except (ValueError, RecursionError) as error:
        raise MalformedPresetError(str(error) or type(error).__name__) from error


def load(path: Path | str) -> VitalPreset:
    """Read a preset from a file: `loads`, and PresetFileError when it cannot be read."""
    try:
        raw = Path(path).read_bytes()
    except OSError as error:
        raise PresetFileError(str(path), str(error)) from error
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MalformedPresetError(str(error)) from error
    return loads(text)


def _string(value: str) -> str:
    """Write a JSON string as Vital does: UTF-8 left raw, only what JSON requires escaped."""
    return json.dumps(value, ensure_ascii=False)


def _object(members: Mapping[str, str]) -> str:
    """Write a JSON object from its members' written values, its keys sorted."""
    return "{" + ",".join(f"{_string(key)}:{members[key]}" for key in sorted(members)) + "}"


def _entry(entry: ModulationEntry) -> str:
    """Write one entry of the routing list."""
    source, destination, line_mapping = entry
    members = {_SOURCE: _string(source), _DESTINATION: _string(destination)}
    if line_mapping is not None:
        members[_LINE_MAPPING] = line_mapping.decode("utf-8")
    return _object(members)


def dumps(preset: VitalPreset) -> str:
    """Return the text of a `.vital` file holding `preset`, as Vital writes it."""
    entries, floats = split_modulations(preset.modulations)
    settings: dict[str, str] = {key: format_float(v) for key, v in preset.settings.values.items()}
    settings |= {key: format_float(value) for key, value in floats.items()}
    settings |= {key: raw.decode("utf-8") for key, raw in preset.opaque.items()}
    settings[MODULATIONS_KEY] = "[" + ",".join(_entry(entry) for entry in entries) + "]"
    members = {_SETTINGS_KEY: _object(settings)}
    for name in _METADATA:
        value: str | None = getattr(preset, name)
        if value is not None:
            members[name] = _string(value)
    return _object(members) + ("\n" if preset.trailing_newline else "")


def dump(preset: VitalPreset, path: Path | str) -> None:
    """Write a preset to a file, and PresetFileError when it cannot be written."""
    try:
        raw = dumps(preset).encode("utf-8")
    except UnicodeEncodeError as error:
        raise MalformedPresetError(str(error)) from error
    try:
        Path(path).write_bytes(raw)
    except OSError as error:
        raise PresetFileError(str(path), str(error)) from error


def _setting_changes(a: VitalPreset, b: VitalPreset) -> tuple[SettingChange, ...]:
    """Return every setting that differs, by key."""
    old, new = a.settings.values, b.settings.values
    return tuple(
        SettingChange(key=key, old=old.get(key), new=new.get(key))
        for key in sorted(set(old) | set(new))
        if old.get(key) != new.get(key)
    )


def _modulation_change(slot: int, old: Modulation, new: Modulation) -> ModulationChange:
    """Say how one differing slot changed."""
    kind = "added" if old.is_empty and not new.is_empty else "changed"
    if new.is_empty and not old.is_empty:
        kind = "removed"
    return ModulationChange.model_validate({"slot": slot, "kind": kind, "old": old, "new": new})


def _metadata_changes(a: VitalPreset, b: VitalPreset) -> tuple[MetadataChange, ...]:
    """Return every metadata field that differs, by name."""
    changes: list[MetadataChange] = []
    for name in sorted((*_METADATA, "trailing_newline")):
        old: str | bool | None = getattr(a, name)
        new: str | bool | None = getattr(b, name)
        if old != new:
            changes.append(MetadataChange(field=name, old=old, new=new))
    return tuple(changes)


def _opaque_changes(a: VitalPreset, b: VitalPreset) -> tuple[OpaqueChange, ...]:
    """Return every unread section that differs, by name, saying only its size."""
    old, new = a.opaque, b.opaque
    changes: list[OpaqueChange] = []
    for name in sorted(set(old) | set(new)):
        before, after = old.get(name), new.get(name)
        if before != after:
            changes.append(
                OpaqueChange(
                    name=name,
                    old_size=None if before is None else len(before),
                    new_size=None if after is None else len(after),
                )
            )
    return tuple(changes)


def diff(a: VitalPreset, b: VitalPreset) -> PresetDiff:
    """Return what differs from `a` to `b`, each part in a fixed order."""
    return PresetDiff(
        settings=_setting_changes(a, b),
        modulations=tuple(
            _modulation_change(slot, old, new)
            for slot, (old, new) in enumerate(zip(a.modulations, b.modulations, strict=True), 1)
            if old != new
        ),
        metadata=_metadata_changes(a, b),
        opaque=_opaque_changes(a, b),
    )
