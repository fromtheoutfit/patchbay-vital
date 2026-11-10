"""The hosted plugin's state as bytes: the containers around a preset's text, read and written.

The host hands the plugin's state over as a VST3 preset (pedalboard's `preset_data`), and each
layer of it was read from the plugin itself (the host spec's `verification/probes.txt`), not from
any other program's source:

- the `.vstpreset` container: `VST3`, a version (little-endian, as every number in this layer), the
  32-byte class id and the offset of the chunk list; the component's data at offset 48, the
  controller's after it, then `List`, the count, and per chunk its id, offset and size, `Comp` and
  `Cont` in that order, ending the data;
- the component: `VstW`, then three big-endian numbers, the header's size (8), a version and a
  bypass flag; then a VST2 bank of one opaque chunk: `CcnK`, the count of the bytes after it,
  `FBCh`, a version, the plugin's id (`Vita`) and version (0x00010604 at 1.6.4), a program count,
  128 reserved bytes and the chunk's size;
- the chunk: the preset's JSON text, written exactly as a `.vital` file writes it with one more
  top-level key, `tuning`, then what the plugin's framework appends (17 NUL bytes and
  `JUCEPrivateData` at 1.6.4).

`PluginState` holds every field as read, so `wrap(unwrap(data)) == data` and
`unwrap(wrap(state)) == state`. Bytes that are not this, layer by layer, are `PluginStateError`,
chained from what refused them. The text is read only as far as finding where its object ends:
reading the preset is `patchbay_vital.format`'s.
"""

import struct
from typing import Annotated, Any, Self

from patchbay import PatchbayModel, PatchbayValidationError
from pydantic import ConfigDict, Field, field_validator

from patchbay_vital.errors import PluginStateError
from patchbay_vital.preset import DECODER

_PRESET_MAGIC, _LIST_MAGIC = b"VST3", b"List"
_COMPONENT_ID, _CONTROLLER_ID = b"Comp", b"Cont"
_WRAPPER_MAGIC, _BANK_MAGIC, _OPAQUE_BANK = b"VstW", b"CcnK", b"FBCh"

_PRESET_HEADER = struct.Struct("<4si32sq")
"""`VST3`, the container's version, the class id and the chunk list's offset: 48 bytes."""

_LIST_HEADER = struct.Struct("<4si")
_ENTRY = struct.Struct("<4sqq")
_CHUNKS = 2
"""The chunk list's length: the component's and the controller's."""

_WRAPPER = struct.Struct(">4siii")
"""`VstW`, the size of the header after it (8), its version and the bypass flag."""

_WRAPPER_SIZE = 8
_BANK = struct.Struct(">4si4si4sii128si")
"""`CcnK`, the count after it, `FBCh`, the version, the plugin's id and version, the program count,
the reserved bytes and the chunk's size: 160 bytes."""

_COUNTED_FROM = 8
"""`CcnK`'s count leaves out itself and its magic."""

type _Int32 = Annotated[int, Field(ge=-(2**31), le=2**31 - 1)]


def _object_end(chunk: bytes) -> int:
    """Return where the JSON object that starts `chunk` ends, as a byte offset.

    Read as Latin-1 every byte is one character, so the decoder's index is a byte offset; the
    object's structure is ASCII, and the text it spans must still be UTF-8, which is checked after.
    """
    if not chunk.startswith(b"{"):
        msg = "the chunk does not start with a JSON object"
        raise ValueError(msg)
    _, end = DECODER.raw_decode(chunk.decode("latin-1"))
    chunk[:end].decode("utf-8")
    return int(end)


class PluginState(PatchbayModel, frozen=True):
    """The plugin's state: every field its containers held, as read, and the preset's text."""

    model_config = ConfigDict(ser_json_bytes="base64", val_json_bytes="base64")

    class_id: bytes = Field(min_length=32, max_length=32)
    container_version: _Int32
    wrapper_version: _Int32
    bypass: _Int32
    bank_version: _Int32
    plugin_id: bytes = Field(min_length=4, max_length=4)
    plugin_version: _Int32
    programs: _Int32
    reserved: bytes = Field(min_length=128, max_length=128)
    text: bytes
    trailer: bytes = b""
    controller: bytes = b""

    @field_validator("text", mode="after")
    @classmethod
    def _text_is_one_object(cls, text: bytes) -> bytes:
        if _object_end(text) != len(text):
            msg = "the text is one JSON object with nothing after it"
            raise ValueError(msg)
        return text

    def with_text(self, text: bytes) -> Self:
        """Return this state holding another preset's text, every other field kept.

        PluginStateError when the text is not one JSON object, which the plugin could not read.
        """
        try:
            return self.model_validate({**dict(self), "text": text})
        except PatchbayValidationError as error:
            raise PluginStateError(str(error)) from error


def _read(layout: struct.Struct, data: bytes, offset: int, what: str) -> tuple[Any, ...]:
    """Unpack `layout` at `offset`, refusing data too short to hold it."""
    if offset < 0 or len(data) < offset + layout.size:
        msg = f"{what} needs {layout.size} bytes at offset {offset} of {len(data)}"
        raise PluginStateError(msg)
    return layout.unpack_from(data, offset)


def _expect(found: object, wanted: object, what: str) -> None:
    """Refuse a field that is not what this layout holds there."""
    if found != wanted:
        msg = f"{what} is {wanted!r}, here {found!r}"
        raise PluginStateError(msg)


def _container(data: bytes) -> tuple[dict[str, object], bytes]:
    """Read the `.vstpreset` container: its fields, its controller's bytes, and its component."""
    magic, version, class_id, list_at = _read(_PRESET_HEADER, data, 0, "the container's header")
    _expect(magic, _PRESET_MAGIC, "the container's magic")
    list_magic, count = _read(_LIST_HEADER, data, list_at, "the chunk list")
    _expect(list_magic, _LIST_MAGIC, "the chunk list's magic")
    _expect(count, _CHUNKS, "the chunk count")
    first = list_at + _LIST_HEADER.size
    (component_id, component_at, component_size), (controller_id, controller_at, size) = (
        _read(_ENTRY, data, first + i * _ENTRY.size, "a chunk entry") for i in range(_CHUNKS)
    )
    _expect((component_id, controller_id), (_COMPONENT_ID, _CONTROLLER_ID), "the chunks")
    _expect(component_at, _PRESET_HEADER.size, "the component's offset")
    _expect(controller_at, component_at + component_size, "the controller's offset")
    _expect(list_at, controller_at + size, "the chunk list's offset")
    _expect(len(data), first + _CHUNKS * _ENTRY.size, "the data's length")
    fields: dict[str, object] = {
        "class_id": class_id,
        "container_version": version,
        "controller": data[controller_at:list_at],
    }
    return fields, data[component_at:controller_at]


def _component(component: bytes) -> dict[str, object]:
    """Read the component: the wrapper, the bank, and the chunk's text and what follows it."""
    magic, size, wrapper_version, bypass = _read(_WRAPPER, component, 0, "the wrapper")
    _expect(magic, _WRAPPER_MAGIC, "the wrapper's magic")
    _expect(size, _WRAPPER_SIZE, "the wrapper's header size")
    at = _WRAPPER.size
    bank, count, kind, version, plugin, plugin_version, programs, reserved, chunk_size = _read(
        _BANK, component, at, "the bank"
    )
    _expect(bank, _BANK_MAGIC, "the bank's magic")
    _expect(count, len(component) - at - _COUNTED_FROM, "the bank's count")
    _expect(kind, _OPAQUE_BANK, "the bank's kind")
    chunk = component[at + _BANK.size :]
    _expect(chunk_size, len(chunk), "the chunk's size")
    end = _object_end(chunk)
    return {
        "wrapper_version": wrapper_version,
        "bypass": bypass,
        "bank_version": version,
        "plugin_id": plugin,
        "plugin_version": plugin_version,
        "programs": programs,
        "reserved": reserved,
        "text": chunk[:end],
        "trailer": chunk[end:],
    }


def unwrap(data: bytes) -> PluginState:
    """Read the plugin's state from its VST3 preset bytes.

    PluginStateError, chained from what refused them, for bytes that are not that state.
    """
    try:
        fields, component = _container(data)
        return PluginState.model_validate({**fields, **_component(component)})
    except (struct.error, ValueError, RecursionError, PatchbayValidationError) as error:
        raise PluginStateError(str(error) or type(error).__name__) from error


def wrap(state: PluginState) -> bytes:
    """Write the plugin's state as the VST3 preset bytes it is loaded from."""
    chunk = state.text + state.trailer
    bank = _BANK.pack(
        _BANK_MAGIC,
        _BANK.size - _COUNTED_FROM + len(chunk),
        _OPAQUE_BANK,
        state.bank_version,
        state.plugin_id,
        state.plugin_version,
        state.programs,
        state.reserved,
        len(chunk),
    )
    wrapper = _WRAPPER.pack(_WRAPPER_MAGIC, _WRAPPER_SIZE, state.wrapper_version, state.bypass)
    component = wrapper + bank + chunk
    controller_at = _PRESET_HEADER.size + len(component)
    list_at = controller_at + len(state.controller)
    header = _PRESET_HEADER.pack(_PRESET_MAGIC, state.container_version, state.class_id, list_at)
    entries = _ENTRY.pack(_COMPONENT_ID, _PRESET_HEADER.size, len(component)) + _ENTRY.pack(
        _CONTROLLER_ID, controller_at, len(state.controller)
    )
    chunk_list = _LIST_HEADER.pack(_LIST_MAGIC, _CHUNKS) + entries
    return header + component + state.controller + chunk_list
