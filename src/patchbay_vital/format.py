"""Reading, writing and comparing a `.vital` file, byte for byte.

`loads` walks the top level and `settings` by span, so every section it does not interpret is kept
as the very text the file held, the plugin state's top-level `tuning` among them. `dumps` writes
what Vital writes: keys sorted at every depth, no whitespace, raw UTF-8 and floats through `grisu2`,
so `dumps(loads(text)) == text` for a file Vital saved.

A key Vital is not known to write is `UnknownSettingError`, so a change of format is noticed, except
that an unknown section under `settings` is kept with the unread ones. Anything else wrong with a
file is `MalformedPresetError`, and neither pydantic's error nor `json`'s leaves this module. What
may follow the object is one newline and nothing else. Whitespace inside it is read, carrying no
data, and is not written back.
"""

import json
import math
import os
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

from patchbay import PatchbayValidationError, PresetKey

from patchbay_vital.errors import MalformedPresetError, PresetFileError, UnknownSettingError
from patchbay_vital.grisu2 import format_float
from patchbay_vital.preset import (
    DECODER,
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

type _Reader = Callable[[str, int], tuple[object, int]]
"""Reads the value at an offset, returning it and the offset past it."""

_SETTINGS_KEY = "settings"
_SOURCE, _DESTINATION, _LINE_MAPPING = "source", "destination", "line_mapping"
_TRAILING_NEWLINE = "trailing_newline"
_TUNING = "tuning"
_METADATA = tuple(
    sorted(
        set(VitalPreset.model_fields)
        - {_SETTINGS_KEY, MODULATIONS_KEY, "opaque", _TUNING, _TRAILING_NEWLINE}
    )
)
_SLOT_FLOATS = (*SLOT_FIELDS, *NEWER_SLOT_FIELDS)
_WHITESPACE = " \t\n\r"


class _Settings(NamedTuple):
    """What `settings` holds, sorted by what becomes of it."""

    values: dict[PresetKey, float]
    floats: dict[PresetKey, float]
    opaque: dict[PresetKey, bytes]
    entries: tuple[ModulationEntry, ...]


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


def _decode(text: str, start: int) -> tuple[object, int]:
    """Decode the JSON value at `start`, returning it and the index past it."""
    value, end = DECODER.raw_decode(text, start)
    return value, end


def _members(
    text: str, start: int, readers: Mapping[str, _Reader] | None = None
) -> tuple[list[_Member], int]:
    """Return the members of the object at `start`, and the index past it.

    `readers` names the keys whose value is walked by its own reader, so it is decoded only once.
    """
    index = _skip_space(text, _expect(text, start, "{"))
    members: list[_Member] = []
    if text.startswith("}", index):
        return members, index + 1
    seen: set[str] = set()
    while True:
        key, index = DECODER.raw_decode(text, index)
        if not isinstance(key, str) or key in seen:
            msg = f"a key is missing or repeated before offset {index}: {key!r}"
            raise MalformedPresetError(msg)
        seen.add(key)
        first = _skip_space(text, _expect(text, index, ":"))
        read = (readers or {}).get(key, _decode)
        value, end = read(text, first)
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
        raise UnknownSettingError(unknown[0])
    source = by_key.get(_SOURCE, (0, 0, None))[2]
    destination = by_key.get(_DESTINATION, (0, 0, None))[2]
    if not isinstance(source, str) or not isinstance(destination, str):
        msg = "a modulation has a source and a destination, each a string"
        raise MalformedPresetError(msg)
    if _LINE_MAPPING not in by_key:
        return source, destination, None
    first, end, _ = by_key[_LINE_MAPPING]
    return source, destination, text[first:end].encode("utf-8")


def _modulation_entries(text: str, start: int) -> tuple[tuple[ModulationEntry, ...], int]:
    """Return the entries of the routing list at `start`, and the index past it."""
    index = _skip_space(text, _expect(text, start, "["))
    entries: list[ModulationEntry] = []
    if text.startswith("]", index):
        return (), index + 1
    while True:
        members, index = _members(text, index)
        entries.append(_modulation_entry(text, members))
        index = _skip_space(text, index)
        if text.startswith("]", index):
            return tuple(entries), index + 1
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
    try:
        return Modulation.model_validate(
            {
                _SOURCE: source or None,
                _DESTINATION: destination or None,
                _LINE_MAPPING: line_mapping,
                **fields,
            }
        )
    except PatchbayValidationError as error:
        raise MalformedPresetError(str(error)) from error


def join_modulations(
    entries: Sequence[ModulationEntry], floats: Mapping[PresetKey, float]
) -> tuple[Modulation, ...]:
    """Join the file's routing list with its per-slot floats, the reverse of `split_modulations`.

    MalformedPresetError when a slot lacks a float every file holds or cannot be a slot,
    UnknownSettingError for a per-slot float beyond the slots there are.
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
        for field in _SLOT_FLOATS:
            value: float | None = getattr(modulation, field)
            if value is not None:
                floats[_slot_key(slot, field)] = value
    return tuple(entries), floats


def _read_settings(text: str, start: int) -> tuple[_Settings, int]:
    """Sort `settings` into floats, per-slot floats, unread sections and the routing list."""
    values: dict[PresetKey, float] = {}
    floats: dict[PresetKey, float] = {}
    opaque: dict[PresetKey, bytes] = {}
    entries: tuple[ModulationEntry, ...] | None = None
    members, past = _members(text, start, {MODULATIONS_KEY: _modulation_entries})
    for name, first, end, value in members:
        key = PresetKey(name)
        if isinstance(value, tuple):
            entries = value
        elif isinstance(value, list | dict):
            opaque[key] = text[first:end].encode("utf-8")
        elif not (SLOT_KEY.fullmatch(name) or key in KNOWN_SETTINGS):
            raise UnknownSettingError(name)
        elif not isinstance(value, float):
            msg = f"{name!r} holds {value!r}, where a setting is a float"
            raise MalformedPresetError(msg)
        elif SLOT_KEY.fullmatch(name):
            floats[key] = value
        else:
            values[key] = value
    if entries is None:
        msg = f"{_SETTINGS_KEY} has no {MODULATIONS_KEY!r}"
        raise MalformedPresetError(msg)
    if len(entries) != MODULATION_SLOTS:
        msg = f"a preset has {MODULATION_SLOTS} modulation slots, this one {len(entries)}"
        raise MalformedPresetError(msg)
    return _Settings(values, floats, opaque, entries), past


def _parse(text: str) -> VitalPreset:
    """Read a preset, leaving the errors of json and pydantic for `loads` to report."""
    body = text.removesuffix("\n")
    members, end = _members(body, 0, {_SETTINGS_KEY: _read_settings})
    if end != len(body):
        msg = f"text follows the preset at offset {end}"
        raise MalformedPresetError(msg)
    fields: dict[str, object] = {_TRAILING_NEWLINE: text.endswith("\n")}
    settings: _Settings | None = None
    for name, first, end, value in members:
        if isinstance(value, _Settings):
            settings = value
        elif name == _TUNING:
            if not isinstance(value, dict):
                msg = f"{_TUNING!r} is an object, here {value!r}"
                raise MalformedPresetError(msg)
            fields[_TUNING] = body[first:end].encode("utf-8")
        elif name not in _METADATA:
            raise UnknownSettingError(name)
        elif value is None:
            msg = f"{name!r} is null, and a file that lacks it omits the key"
            raise MalformedPresetError(msg)
        else:
            fields[name] = value
    if settings is None:
        msg = f"a preset has {_SETTINGS_KEY!r}"
        raise MalformedPresetError(msg)
    return VitalPreset.model_validate(
        {
            **fields,
            _SETTINGS_KEY: VitalSettings(values=settings.values),
            MODULATIONS_KEY: join_modulations(settings.entries, settings.floats),
            "opaque": settings.opaque,
        }
    )


def loads(text: str) -> VitalPreset:
    """Read a preset from the text of a `.vital` file.

    UnknownSettingError for a key Vital is not known to write, an unknown section under `settings`
    aside, and MalformedPresetError for anything else this package cannot read.
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
    except (OSError, ValueError) as error:
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
    if preset.tuning is not None:
        members[_TUNING] = preset.tuning.decode("utf-8")
    return _object(members) + ("\n" if preset.trailing_newline else "")


def _replace_file(path: Path, raw: bytes) -> None:
    """Write `raw` beside the file and rename it over, so a failure leaves the file as it was."""
    target = path.resolve()
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as file:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        if target.exists():
            shutil.copymode(target, temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def dump(preset: VitalPreset, path: Path | str) -> None:
    """Write a preset to a file, whole or not at all.

    PresetFileError when it cannot be written, MalformedPresetError for text UTF-8 cannot hold,
    which only a model changed past its validation can carry.
    """
    try:
        raw = dumps(preset).encode("utf-8")
    except UnicodeEncodeError as error:
        raise MalformedPresetError(str(error)) from error
    try:
        _replace_file(Path(path), raw)
    except (OSError, ValueError) as error:
        raise PresetFileError(str(path), str(error)) from error


def _same(old: float | None, new: float | None) -> bool:
    """Say whether two floats write the same, as `0.0` and `-0.0` do not though they are equal."""
    if old is None or new is None:
        return old is new
    return old == new and math.copysign(1.0, old) == math.copysign(1.0, new)


def _same_slot(old: Modulation, new: Modulation) -> bool:
    """Say whether two slots write the same."""
    return old == new and all(_same(getattr(old, f), getattr(new, f)) for f in _SLOT_FLOATS)


def _setting_changes(a: VitalPreset, b: VitalPreset) -> tuple[SettingChange, ...]:
    """Return every setting that differs, by key."""
    old, new = a.settings.values, b.settings.values
    return tuple(
        SettingChange(key=key, old=old.get(key), new=new.get(key))
        for key in sorted(set(old) | set(new))
        if not _same(old.get(key), new.get(key))
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
    for name in sorted((*_METADATA, _TRAILING_NEWLINE)):
        old: str | bool | None = getattr(a, name)
        new: str | bool | None = getattr(b, name)
        if old != new:
            changes.append(MetadataChange(field=name, old=old, new=new))
    return tuple(changes)


def _opaque_change(name: str, before: bytes | None, after: bytes | None) -> OpaqueChange:
    """Say that an unread section differs, by its name and sizes."""
    return OpaqueChange(
        name=PresetKey(name),
        old_size=None if before is None else len(before),
        new_size=None if after is None else len(after),
    )


def _opaque_changes(a: VitalPreset, b: VitalPreset) -> tuple[OpaqueChange, ...]:
    """Return every unread section that differs, by name, saying only its size.

    The sections under `settings` come by name, then the top-level `tuning`, which is unread too.
    """
    old, new = a.opaque, b.opaque
    changes = [
        _opaque_change(name, old.get(name), new.get(name))
        for name in sorted(set(old) | set(new))
        if old.get(name) != new.get(name)
    ]
    if a.tuning != b.tuning:
        changes.append(_opaque_change(_TUNING, a.tuning, b.tuning))
    return tuple(changes)


def diff(a: VitalPreset, b: VitalPreset) -> PresetDiff:
    """Return what differs from `a` to `b`, each part in a fixed order."""
    return PresetDiff(
        settings=_setting_changes(a, b),
        modulations=tuple(
            _modulation_change(slot, old, new)
            for slot, (old, new) in enumerate(zip(a.modulations, b.modulations, strict=True), 1)
            if not _same_slot(old, new)
        ),
        metadata=_metadata_changes(a, b),
        opaque=_opaque_changes(a, b),
    )
