"""The models of a Vital preset, each on patchbay's frozen, closed, finite, strict base.

A `.vital` file is JSON whose `settings` object holds float scalars and structured sections side by
side. `VitalSettings` holds the floats by key, `Modulation` a slot of the routing list joined with
that slot's own floats, and `VitalPreset.opaque` the sections this package does not interpret, each
as the text the file held, so it is written back byte for byte. The plugin's own state is the same
text with one more top-level object, `tuning`, held as its text the same way.

A key is *known* when Vital has ever been seen to write it, not when every file has it: Vital adds
keys as it grows (723 settings at 0.6.1, 909 at 1.6.4), so a key absent from a file is legal and a
key absent from `settings_keys.txt` is a change of format. That file is a plain sorted list derived
from the parameter map, `data/parameters.json`: every key there but the per-slot ones, and the keys
only presets hold, `parameters.PRESET_ONLY_KEYS`. The generator writes both and a unit test holds
the one to the other.

A model built directly refuses as patchbay's `PatchbayValidationError`; reading a file through
`patchbay_vital.format` reports the same refusal as `MalformedPresetError`.
"""

import importlib.resources
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, Any, ClassVar, Literal, Self

from patchbay import PatchbayModel, PresetKey
from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    WrapSerializer,
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

SLOT_KEY = re.compile(f"modulation_[1-9][0-9]*_({'|'.join((*SLOT_FIELDS, *NEWER_SLOT_FIELDS))})")
"""A per-slot float's key in `settings`; `Modulation` holds these, so `VitalSettings` does not."""

KNOWN_SETTINGS = frozenset(
    PresetKey(line)
    for line in importlib.resources.files("patchbay_vital")
    .joinpath("settings_keys.txt")
    .read_text(encoding="utf-8")
    .splitlines()
)
"""Every float key but the per-slot ones that Vital has been seen to write."""


def _refuse_constant(name: str) -> object:
    """Refuse the NaN and Infinity tokens Python's JSON parser would otherwise accept."""
    msg = f"{name} is not a number a preset can hold"
    raise ValueError(msg)


DECODER = json.JSONDecoder(parse_constant=_refuse_constant)
"""How everything here reads JSON: a preset holds no NaN or Infinity, at any depth."""


def _utf_8(text: str) -> str:
    """Return `text` when UTF-8 can hold it, as a file must: a lone surrogate it cannot."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as error:
        msg = "text is written as UTF-8, which cannot hold a lone surrogate"
        raise ValueError(msg) from error
    return text


def _sorted_read_only[V](mapping: Mapping[PresetKey, V]) -> Mapping[PresetKey, V]:
    """Return a mapping sorted by key that cannot be changed under a frozen model."""
    return MappingProxyType(dict(sorted(mapping.items())))


def _as_plain_dict[V](
    mapping: Mapping[PresetKey, V], handler: SerializerFunctionWrapHandler
) -> object:
    """Hand pydantic a dict, since it cannot serialize a mapping proxy."""
    return handler(dict(mapping))


type _Key = Annotated[PresetKey, Field(min_length=1)]
type _Text = Annotated[str, AfterValidator(_utf_8)]
type _ReadOnly[V] = Annotated[
    Mapping[_Key, V], AfterValidator(_sorted_read_only), WrapSerializer(_as_plain_dict)
]


def decode_end(text: str, what: str) -> int:
    """Return where the JSON value that starts `text` ends, as the package reads JSON.

    ValueError, naming `what`, where the text nests too deeply for the decoder to read, so no
    `RecursionError` leaves a validator; any other refusal is the decoder's own `ValueError`.
    """
    try:
        _, end = DECODER.raw_decode(text)
    except RecursionError as error:
        msg = f"{what} nests too deeply to read"
        raise ValueError(msg) from error
    return end


def _json_section(raw: bytes) -> bytes:
    """Return `raw` when it is exactly the text of one JSON array or object, else refuse it."""
    if raw[:1] not in {b"[", b"{"}:
        msg = "a section is the text of a JSON array or object"
        raise ValueError(msg)
    text = raw.decode("utf-8")
    end = decode_end(text, "a section")
    if end != len(text):
        msg = "a section is one JSON array or object with nothing after it"
        raise ValueError(msg)
    return raw


class _PicklableMappings(PatchbayModel, frozen=True):
    """A model holding read-only mappings that can still be pickled and deep-copied.

    A mapping proxy can be neither, so the pickled state holds each as a plain dict, and a deep copy
    is a shallow one: everything such a model holds is immutable. pydantic deep-copies field by
    field when `model_copy` is given an update, so `deep` is dropped there too.
    """

    def __getstate__(self) -> dict[Any, Any]:
        """Return the state with each read-only mapping as a plain dict."""
        state = super().__getstate__()
        fields = state["__dict__"]
        state["__dict__"] = {
            name: dict(value) if isinstance(value, MappingProxyType) else value
            for name, value in fields.items()
        }
        return state

    def __setstate__(self, state: dict[Any, Any]) -> None:
        """Restore the state, each plain dict read-only again."""
        fields = {
            name: MappingProxyType(value) if isinstance(value, dict) else value
            for name, value in state["__dict__"].items()
        }
        super().__setstate__({**state, "__dict__": fields})

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        """Return a new model sharing what it holds, all of which is immutable."""
        return self.__copy__()

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
        """Return a copy with `update` applied; `deep` changes nothing, all being immutable."""
        del deep
        return super().model_copy(update=update)


class Modulation(PatchbayModel, frozen=True):
    """One slot of the modulation matrix: what routes where, and the slot's own floats.

    An empty slot has neither a source nor a destination, where the file writes `""` for both, and
    keeps whatever floats it holds: Vital leaves a non-zero amount behind in some. `ramp_up` and
    `ramp_down` are None where the file lacks their keys. `line_mapping` is the file's own JSON.
    """

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    source: Annotated[str, Field(min_length=1), AfterValidator(_utf_8)] | None
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


class VitalSettings(_PicklableMappings, frozen=True):
    """A preset's float settings by key: every float but the per-slot ones `Modulation` holds.

    Sorted by key and read-only. Each key is one Vital is known to write; a key a file lacks is
    simply absent, older files lacking those Vital has added since.
    """

    values: _ReadOnly[float]

    # Unhashable, said the way Python says it: pydantic's frozen hash would raise on a mapping.
    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    @field_validator("values", mode="after")
    @classmethod
    def _keys_are_known(cls, values: Mapping[PresetKey, float]) -> Mapping[PresetKey, float]:
        unknown = sorted(set(values) - KNOWN_SETTINGS)
        if unknown:
            msg = f"not keys Vital is known to write: {unknown!r}"
            raise ValueError(msg)
        return values


class VitalPreset(_PicklableMappings, frozen=True):
    """A whole `.vital` file: its metadata, settings, modulations and the sections left unread.

    `modulations` is always every slot, its position the slot's number less one. `opaque` holds each
    section this package does not interpret, as the text of its JSON, the form `patchbay.Patch`
    carries unread sections in. `preset_name` is None where the file lacks the key, as files before
    1.6.4 do. `tuning` is the top-level object the plugin's state adds, as its text, and None where
    the text has none, as every `.vital` file seen. `trailing_newline` says the file ended in one,
    as three of Vital's own presets do.
    """

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    author: _Text
    comments: _Text
    macro1: _Text
    macro2: _Text
    macro3: _Text
    macro4: _Text
    preset_name: _Text | None = None
    preset_style: _Text
    synth_version: _Text
    settings: VitalSettings
    modulations: tuple[Modulation, ...] = Field(
        min_length=MODULATION_SLOTS, max_length=MODULATION_SLOTS
    )
    opaque: _ReadOnly[bytes]
    tuning: bytes | None = None
    trailing_newline: bool = False

    # Unhashable, said the way Python says it: pydantic's frozen hash would raise on a mapping.
    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    @field_validator("tuning", mode="after")
    @classmethod
    def _tuning_is_an_object(cls, raw: bytes | None) -> bytes | None:
        if raw is not None and not _json_section(raw).startswith(b"{"):
            msg = "tuning is the text of a JSON object"
            raise ValueError(msg)
        return raw

    @field_validator("opaque", mode="after")
    @classmethod
    def _sections_are_json_under_their_own_keys(
        cls, opaque: Mapping[PresetKey, bytes]
    ) -> Mapping[PresetKey, bytes]:
        for key, raw in opaque.items():
            if key in KNOWN_SETTINGS or key == MODULATIONS_KEY or SLOT_KEY.fullmatch(key):
                msg = f"{key!r} is a key this package reads, so it is not an unread section"
                raise ValueError(msg)
            _json_section(raw)
        return opaque


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
    """An unread section that differs, by name and size only; None on the side that lacks it.

    `where` says which level holds it: `settings` for a section under `settings`, `preset` for the
    top-level `tuning`, so a section under `settings` named `tuning` is told from it.
    """

    name: _Key
    where: Literal["settings", "preset"]
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
        """Say whether the two presets write the same bytes."""
        return not (self.settings or self.modulations or self.metadata or self.opaque)
