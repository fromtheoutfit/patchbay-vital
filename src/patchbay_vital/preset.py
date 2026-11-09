"""The models of a Vital preset, each on patchbay's frozen, closed, finite, strict base.

A `.vital` file is JSON whose `settings` object holds float scalars and structured sections side by
side. `VitalSettings` holds the floats by key, `Modulation` a slot of the routing list joined with
that slot's own floats, and `VitalPreset.opaque` the sections this package does not interpret, each
as the text the file held, so it is written back byte for byte.

A key is *known* when Vital has ever been seen to write it, not when every file has it: Vital adds
keys as it grows (723 settings at 0.6.1, 909 at 1.6.4), so a key absent from a file is legal and a
key absent from `settings_keys.txt` is a change of format. That file is a plain sorted list; the
two-namespace map turns it into structured data.

A model built directly refuses as patchbay's `PatchbayValidationError`; reading a file through
`patchbay_vital.format` reports the same refusal as `MalformedPresetError`.
"""

import importlib.resources
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from patchbay import PatchbayModel, PresetKey
from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_serializer,
    field_validator,
    model_validator,
)

MODULATIONS_KEY = PresetKey("modulations")
"""The key of the routing list inside `settings`."""

MODULATION_SLOTS = 64
"""How many slots a preset has, used or not: every file seen holds exactly this many."""

SLOT_FIELDS = ("amount", "bipolar", "bypass", "power", "stereo")
"""The per-slot floats every file holds."""

NEWER_SLOT_FIELDS = ("ramp_down", "ramp_up")
"""The per-slot floats only newer files hold: 1.6.4 has them, 1.0.0 and earlier do not."""

SLOT_KEY = re.compile(
    r"modulation_(?P<slot>[1-9][0-9]*)_(?P<field>amount|bipolar|bypass|power|ramp_down|ramp_up|stereo)"
)
"""A per-slot float's key in `settings`; `Modulation` holds these, so `VitalSettings` does not."""

KNOWN_SETTINGS = frozenset(
    PresetKey(line)
    for line in importlib.resources.files("patchbay_vital")
    .joinpath("settings_keys.txt")
    .read_text(encoding="utf-8")
    .splitlines()
)
"""Every float key but the per-slot ones that Vital has been seen to write."""

type _Key = Annotated[PresetKey, Field(min_length=1)]


def _json_section(raw: bytes) -> bytes:
    """Return `raw` when it is the text of one JSON array or object, and refuse it otherwise."""
    if raw[:1] not in {b"[", b"{"}:
        msg = "a section is the text of a JSON array or object"
        raise ValueError(msg)
    try:
        json.loads(raw.decode("utf-8"))
    except RecursionError as error:
        msg = "a section nests too deeply to read"
        raise ValueError(msg) from error
    return raw


class Modulation(PatchbayModel, frozen=True):
    """One slot of the modulation matrix: what routes where, and the slot's own floats.

    An empty slot has neither a source nor a destination, where the file writes `""` for both, and
    keeps whatever floats it holds: Vital leaves a non-zero amount behind in some. `ramp_up` and
    `ramp_down` are None where the file lacks their keys. `line_mapping` is the file's own JSON.
    """

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    source: Annotated[str, Field(min_length=1)] | None
    destination: _Key | None
    amount: float
    bipolar: float
    bypass: float
    power: float
    stereo: float
    ramp_down: float | None = None
    ramp_up: float | None = None
    line_mapping: bytes | None = None

    @property
    def is_empty(self) -> bool:
        """Say whether nothing is routed through this slot."""
        return self.source is None

    @field_validator("line_mapping", mode="after")
    @classmethod
    def _line_mapping_is_json(cls, raw: bytes | None) -> bytes | None:
        return None if raw is None else _json_section(raw)

    @model_validator(mode="after")
    def _source_and_destination_go_together(self) -> Self:
        if (self.source is None) != (self.destination is None):
            msg = "a slot has both a source and a destination, or neither"
            raise ValueError(msg)
        return self


class VitalSettings(PatchbayModel, frozen=True):
    """A preset's float settings by key: every float but the per-slot ones `Modulation` holds.

    Sorted by key and read-only. Each key is one Vital is known to write; a key a file lacks is
    simply absent, older files lacking those Vital has added since.
    """

    values: Mapping[_Key, float]

    # Unhashable, said the way Python says it: pydantic's frozen hash would raise on a mapping.
    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    @field_validator("values", mode="after")
    @classmethod
    def _known_sorted_and_read_only(
        cls, values: Mapping[PresetKey, float]
    ) -> Mapping[PresetKey, float]:
        unknown = sorted(set(values) - KNOWN_SETTINGS)
        if unknown:
            msg = f"not keys Vital is known to write: {unknown!r}"
            raise ValueError(msg)
        return MappingProxyType(dict(sorted(values.items())))

    @field_serializer("values", mode="wrap")
    def _values_as_plain_dict(
        self, values: Mapping[PresetKey, float], handler: SerializerFunctionWrapHandler
    ) -> object:
        return handler(dict(values))


class VitalPreset(PatchbayModel, frozen=True):
    """A whole `.vital` file: its metadata, settings, modulations and the sections left unread.

    `modulations` is always every slot, its position the slot's number less one. `opaque` holds each
    section this package does not interpret, as the text of its JSON, the form `patchbay.Patch`
    carries unread sections in. `preset_name` is None where the file lacks the key, as files before
    1.6.4 do. `trailing_newline` says the file ended in one, as three of Vital's own presets do.
    """

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    author: str
    comments: str
    macro1: str
    macro2: str
    macro3: str
    macro4: str
    preset_name: str | None = None
    preset_style: str
    synth_version: str
    settings: VitalSettings
    modulations: tuple[Modulation, ...] = Field(
        min_length=MODULATION_SLOTS, max_length=MODULATION_SLOTS
    )
    opaque: Mapping[_Key, bytes]
    trailing_newline: bool = False

    # Unhashable, said the way Python says it: pydantic's frozen hash would raise on a mapping.
    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    @field_validator("opaque", mode="after")
    @classmethod
    def _sections_are_json_sorted_and_read_only(
        cls, opaque: Mapping[PresetKey, bytes]
    ) -> Mapping[PresetKey, bytes]:
        for key, raw in opaque.items():
            if key in KNOWN_SETTINGS or key == MODULATIONS_KEY or SLOT_KEY.fullmatch(key):
                msg = f"{key!r} is a key this package reads, so it is not an unread section"
                raise ValueError(msg)
            _json_section(raw)
        return MappingProxyType(dict(sorted(opaque.items())))

    @field_serializer("opaque", mode="wrap")
    def _opaque_as_plain_dict(
        self, opaque: Mapping[PresetKey, bytes], handler: SerializerFunctionWrapHandler
    ) -> object:
        return handler(dict(opaque))


class SettingChange(PatchbayModel, frozen=True):
    """A setting that differs between two presets; None on the side that lacks the key."""

    key: _Key
    old: float | None
    new: float | None


class ModulationChange(PatchbayModel, frozen=True):
    """A slot that differs: routed where it was empty, emptied, or changed in place."""

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    slot: int = Field(ge=1, le=MODULATION_SLOTS)
    kind: Literal["added", "removed", "changed"]
    old: Modulation
    new: Modulation


class MetadataChange(PatchbayModel, frozen=True):
    """A metadata field that differs; None on the side that lacks it."""

    field: str = Field(min_length=1)
    old: str | bool | None
    new: str | bool | None


class OpaqueChange(PatchbayModel, frozen=True):
    """An unread section that differs, by name and size only; None on the side that lacks it."""

    name: _Key
    old_size: int | None = Field(ge=0)
    new_size: int | None = Field(ge=0)


class PresetDiff(PatchbayModel, frozen=True):
    """What differs between two presets, each part in a fixed order."""

    settings: tuple[SettingChange, ...]
    modulations: tuple[ModulationChange, ...]
    metadata: tuple[MetadataChange, ...]
    opaque: tuple[OpaqueChange, ...]

    @property
    def is_empty(self) -> bool:
        """Say whether the two presets are the same."""
        return not (self.settings or self.modulations or self.metadata or self.opaque)
