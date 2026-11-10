"""The plugin's state is read and written exactly as its containers hold it, layer by layer."""

import json
import struct
from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st
from patchbay import PatchbayValidationError

from patchbay_vital.errors import PluginStateError
from patchbay_vital.state import PluginState, unwrap, wrap

# What Vital 1.6.4 wrote around its text (the host spec's verification/probes.txt).
_MEASURED: dict[str, object] = {
    "class_id": b"56535456697461766974616C00000000",
    "container_version": 1,
    "wrapper_version": 1,
    "bypass": 0,
    "bank_version": 2,
    "plugin_id": b"Vita",
    "plugin_version": 0x00010604,
    "programs": 0,
    "reserved": bytes(128),
    "trailer": bytes(17) + b"JUCEPrivateData",
    "controller": b"",
}
_INT32 = st.integers(min_value=-(2**31), max_value=2**31 - 1)
_JSON = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(st.text(), inner, max_size=3),
    max_leaves=10,
)
_TEXTS = st.dictionaries(st.text(), _JSON, max_size=4).map(
    lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8")
)
_STATES = st.builds(
    PluginState,
    class_id=st.binary(min_size=32, max_size=32),
    container_version=_INT32,
    wrapper_version=_INT32,
    bypass=_INT32,
    bank_version=_INT32,
    plugin_id=st.binary(min_size=4, max_size=4),
    plugin_version=_INT32,
    programs=_INT32,
    reserved=st.binary(min_size=128, max_size=128),
    text=_TEXTS,
    trailer=st.binary(max_size=40),
    controller=st.binary(max_size=40),
)


@pytest.fixture
def fixture_state(pytestconfig: pytest.Config) -> PluginState:
    """Return the committed fixture's text as the plugin's state, in the containers it measured."""
    path = pytestconfig.rootpath / "tests" / "data" / "init-media-replaced.vital"
    return PluginState.model_validate({**_MEASURED, "text": path.read_bytes()})


@given(_STATES)
def test_unwrap_reverses_wrap(state: PluginState) -> None:
    """Every field comes back as it was written."""
    assert unwrap(wrap(state)) == state


@given(_STATES)
def test_wrap_reverses_unwrap(state: PluginState) -> None:
    """Bytes read and written again are the same bytes."""
    data = wrap(state)
    assert wrap(unwrap(data)) == data


def test_the_layers_are_where_the_plugin_put_them(fixture_state: PluginState) -> None:
    """The container, the wrapper, the bank and the text sit at the offsets read from Vital."""
    data = wrap(fixture_state)
    text, trailer = fixture_state.text, fixture_state.trailer
    chunk = len(text) + len(trailer)
    component = 16 + 160 + chunk
    assert data[:4] == b"VST3"
    assert struct.unpack_from("<i32sq", data, 4) == (1, _MEASURED["class_id"], 48 + component)
    assert struct.unpack_from(">4siii", data, 48) == (b"VstW", 8, 1, 0)
    assert struct.unpack_from(">4si4si4si", data, 64) == (
        b"CcnK",
        chunk + 152,
        b"FBCh",
        2,
        b"Vita",
        0x00010604,
    )
    assert struct.unpack_from(">i", data, 64 + 156) == (chunk,)
    assert data[224 : 224 + len(text)] == text
    assert data[224 + len(text) : 224 + chunk] == trailer
    assert data[48 + component :] == (
        b"List"
        + struct.pack("<i", 2)
        + b"Comp"
        + struct.pack("<qq", 48, component)
        + b"Cont"
        + struct.pack("<qq", 48 + component, 0)
    )


def test_another_text_keeps_every_other_field(fixture_state: PluginState) -> None:
    """The host swaps the preset and keeps the containers the plugin wrote."""
    swapped = fixture_state.with_text(b'{"a":1}')
    assert swapped.text == b'{"a":1}'
    assert swapped.model_dump(exclude={"text"}) == fixture_state.model_dump(exclude={"text"})


_NOT_ONE_OBJECT = [b"", b"[]", b"1.0", b'{"a":1} ', b'{"a":1}{}', b"{", b'{"\xff":1}']


@pytest.mark.parametrize("text", _NOT_ONE_OBJECT)
def test_a_text_that_is_not_one_object_is_refused(fixture_state: PluginState, text: bytes) -> None:
    """Only an object's text goes to the plugin: anything else could take the process down."""
    with pytest.raises(PluginStateError) as caught:
        fixture_state.with_text(text)
    assert isinstance(caught.value.__cause__, PatchbayValidationError)


def _replace(data: bytes, offset: int, new: bytes) -> bytes:
    """Return the data with the bytes at `offset` replaced."""
    return data[:offset] + new + data[offset + len(new) :]


def _damages(data: bytes) -> dict[str, Callable[[], bytes]]:
    """Each way the bytes can be wrong, layer by layer, and the reason it is refused with."""
    chunk_end = len(data) - 48
    return {
        "the container's header needs 48 bytes": lambda: data[:20],
        "the container's magic": lambda: _replace(data, 0, b"VST2"),
        "the chunk list's magic": lambda: _replace(data, chunk_end, b"Lizt"),
        "the chunk count": lambda: _replace(data, chunk_end + 4, struct.pack("<i", 3)),
        "the chunks": lambda: _replace(data, chunk_end + 8, b"Cmop"),
        "the component's offset": lambda: _replace(data, chunk_end + 12, struct.pack("<q", 47)),
        "the data's length": lambda: data + b"\0",
        "the wrapper's magic": lambda: _replace(data, 48, b"VstX"),
        "the wrapper's header size": lambda: _replace(data, 52, struct.pack(">i", 9)),
        "the bank's magic": lambda: _replace(data, 64, b"CcnX"),
        "the bank's count": lambda: _replace(data, 68, struct.pack(">i", 1)),
        "the bank's kind": lambda: _replace(data, 72, b"FxCk"),
        "the chunk's size": lambda: _replace(data, 220, struct.pack(">i", 1)),
        "does not start with a JSON object": lambda: _replace(data, 224, b"["),
    }


@pytest.mark.parametrize("damage", list(_damages(b"")))
def test_each_layer_is_refused_by_name(fixture_state: PluginState, damage: str) -> None:
    """Bytes that are not the plugin's state are the package's error, naming what is wrong."""
    damaged = _damages(wrap(fixture_state))[damage]()
    with pytest.raises(PluginStateError) as caught:
        unwrap(damaged)
    assert damage in str(caught.value)


def test_a_text_the_decoder_refuses_is_chained(fixture_state: PluginState) -> None:
    """A JSON error under the containers is the package's, from json's."""
    data = wrap(fixture_state.with_text(b'{"a":[1]}'))
    with pytest.raises(PluginStateError) as caught:
        unwrap(data.replace(b'{"a":[1]}', b'{"a":[1}}'))
    assert isinstance(caught.value.__cause__, ValueError)
