"""What the host does with no plugin needed to show it, so CI, which has no Vital, holds it too.

A path that gives no Vital is refused as the package, by name. The floating-point guard every call
into the plugin goes through is found where the tests run, and gives the environment back however
the block changed it; a fake plugin that changes the rounding mode on every call shows each public
method gives it back and that each call is entered with the process's own. The same fake shows
what pedalboard raises, from any reach, is the package's error, that a measurement puts each
parameter back and loads the state once however it ends, that the containers are read once, that
a state, a value or an id the host cannot take is the package's error, and that the map is refused
on another machine or Vital version. What the host does with a loaded Vital is
`tests/integration/test_vital_plugin.py`'s.
"""

import ctypes
import ctypes.util
import json
import math
import platform
import types
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import ClassVar

import numpy as np
import pedalboard
import pytest
from numpy.typing import NDArray
from patchbay import ParameterId, PatchbayValidationError

from patchbay_vital import host
from patchbay_vital.errors import (
    CensusError,
    MapMismatchError,
    ParameterRangeError,
    PluginLoadError,
    PluginRenderError,
    PluginStateError,
    UnknownParameterError,
)
from patchbay_vital.host import DEFAULT_PATH, VitalHost, _c_library, _environment_kept
from patchbay_vital.parameters import parameter_map
from patchbay_vital.state import PluginState, unwrap, wrap

_FE_UPWARD = {"x86_64": 0x800, "arm64": 0x400000, "aarch64": 0x400000}
"""`FE_UPWARD` from `<fenv.h>` by machine: x86's rounding-control bits, arm64's FPCR RMode bits."""

_UCRT_UPWARD = {"AMD64": 0x200}
"""`FE_UPWARD` on Windows, where the UCRT's `<fenv.h>` defines it as `_RC_UP`."""


def _upward_or_skip() -> tuple[ctypes.CDLL, int]:
    """Return the guard's library and this machine's `FE_UPWARD`, or skip where it is not known."""
    machine = platform.machine()
    known = _UCRT_UPWARD if platform.system() == "Windows" else _FE_UPWARD
    upward = known.get(machine)
    if upward is None:
        pytest.skip(f"no FE_UPWARD known for {platform.system()} on {machine!r}")
    library = _c_library()
    assert library is not None
    return library, upward


def _added(one: float, tiny: float) -> float:
    """Add at run time, under whatever rounding the process has, where the compiler cannot fold."""
    return one + tiny


def test_the_default_is_vital_s_own_install_path() -> None:
    """Without a path the host looks where Vital's installer puts it on macOS, and nowhere else."""
    assert Path("/Library/Audio/Plug-Ins/VST3/Vital.vst3") == DEFAULT_PATH


def test_a_path_with_nothing_there_is_named(tmp_path: Path) -> None:
    """Nothing is searched for: a path with nothing at it is refused, saying so."""
    absent = tmp_path / "Vital.vst3"
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(absent)
    assert caught.value.path == str(absent)
    assert "nothing at the path" in caught.value.reason


@pytest.mark.parametrize("make", ["directory", "file"])
def test_a_path_the_host_cannot_load_is_named(tmp_path: Path, make: str) -> None:
    """A bundle with no plugin in it, or a file that is none, is the host's refusal, chained."""
    path = tmp_path / "Nothing.vst3"
    if make == "directory":
        path.mkdir()
    else:
        path.write_text("not a plugin", encoding="utf-8")
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(path)
    assert caught.value.path == str(path)
    assert isinstance(caught.value.__cause__, ImportError)


def test_the_two_functions_are_found_where_the_tests_run() -> None:
    """The guard has a library holding `fegetenv` and `fesetenv` here, whatever the platform.

    On glibc that is the maths library; the C library, which loads, has neither.
    """
    library = _c_library()
    assert library is not None
    assert hasattr(library, "fegetenv")
    assert hasattr(library, "fesetenv")


_BOTH = types.SimpleNamespace(fegetenv=None, fesetenv=None)
_NEITHER = types.SimpleNamespace()


@pytest.mark.parametrize(
    ("found", "libraries", "chosen"),
    [
        # glibc: the C library loads without them, the maths library holds them.
        ({"c": "libc", "m": "libm"}, {"libc": _NEITHER, "libm": _BOTH}, _BOTH),
        # A name that does not load is passed over too, and the UCRT is tried last.
        ({"c": "libc", "m": "libm"}, {"libm": _NEITHER, "ucrtbase": _BOTH}, _BOTH),
        # No library holding both: the host then refuses to load.
        ({"c": "libc"}, {"libc": _NEITHER}, None),
    ],
)
def test_a_library_without_the_two_functions_is_passed_over(
    monkeypatch: pytest.MonkeyPatch,
    found: dict[str, str],
    libraries: dict[str, object],
    chosen: object,
) -> None:
    """The first library that loads and holds both is the one, so the choice shows on any host."""

    def load(name: str) -> object:
        if name not in libraries:
            raise OSError(name)
        return libraries[name]

    monkeypatch.setattr(ctypes.util, "find_library", found.get)
    monkeypatch.setattr(ctypes, "CDLL", load)
    assert _c_library() is chosen


def test_a_library_is_looked_up_only_once_the_one_before_it_is_passed_over(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With both in the C library, the maths library, a subprocess on Linux, is never looked up."""
    asked: list[str] = []

    def find(name: str) -> str:
        asked.append(name)
        return f"lib{name}"

    monkeypatch.setattr(ctypes.util, "find_library", find)
    both: object = _BOTH
    monkeypatch.setattr(ctypes, "CDLL", lambda _name: both)
    assert _c_library() is both
    assert asked == ["c"]


def test_the_environment_comes_back_however_the_block_changed_it() -> None:
    """Upward rounding set inside the guard holds there, and is gone once the guard closes.

    The library is the guard's own, so this saves and restores the real environment once, with no
    plugin to change it.
    """
    library, upward = _upward_or_skip()
    original = library.fegetround()
    one, tiny = 1.0, 2.0**-60
    try:
        with _environment_kept():
            assert library.fesetround(upward) == 0
            assert _added(one, tiny) == math.nextafter(1.0, 2.0)
        assert library.fegetround() == original
        assert _added(one, tiny) == 1.0
    finally:
        library.fesetround(original)


def test_without_the_two_functions_the_host_refuses_to_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where no library holds them, the host is refused before the plugin is loaded, saying why."""
    monkeypatch.setattr(host, "_LIBC", None)
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(tmp_path)
    assert caught.value.path == str(tmp_path)
    assert "fegetenv and fesetenv" in caught.value.reason


# A plugin as pedalboard hands it to the host, with one parameter, filter_1_cutoff, whose preset
# key is its host id and whose preset value is 8 + 128 r (the committed map). Every call into it
# turns upward rounding on, as Vital turns flush-to-zero on, so the guard has something to undo.
_HOST_ID = "filter_1_cutoff"
_TWIN_ID = "filter_2_cutoff"
_START = 0.40625  # normalized, the plugin's default of 60 semitones
_CONTAINERS: dict[str, object] = {  # Vital 1.6.4's, as tests/unit/test_state.py measured them
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
}


def _preset_value(normalized: float) -> float:
    return 8.0 + 128.0 * normalized


class _FakeParameter:
    """One of pedalboard's parameter wrappers, each access a call into the plugin."""

    def __init__(self, plugin: "_FakePlugin") -> None:
        self._plugin = plugin

    @property
    def name(self) -> str:
        self._plugin.touch("name")
        return "Filter 1 Cutoff"

    @property
    def raw_value(self) -> float:
        self._plugin.touch("raw_value")
        return self._plugin.value

    @raw_value.setter
    def raw_value(self, value: float) -> None:
        self._plugin.touch("set_raw_value")
        self._plugin.value = value

    def get_text_for_raw_value(self, raw_value: float) -> str:
        self._plugin.touch("text")
        return f"{_preset_value(raw_value) - 60:.6g} semitones"


class _FakePlugin:
    """pedalboard's plugin as the host sees it, turning upward rounding on at every call.

    `entered` records the rounding mode each call found: the process's own when the host guards
    each call, the one the last call left when one guard spans two.
    """

    library: ClassVar[ctypes.CDLL]
    upward: ClassVar[int]
    broken_at: float | None = None  # the value at which the state read is not a state
    missing_at: float | None = None  # the value at which the state lacks the parameter's key
    bare_at: float | None = None  # the value at which the state's text is `bare_text`
    bare_text = b"{}"
    twinned = False  # whether a second host id, filter_2_cutoff, moves the same value
    short = False  # whether a render gives three samples whatever was asked
    version_text = "1.6.4"

    def __init__(self, path: str) -> None:
        self.path = path
        self.value = _START
        self.calls: list[str] = []
        self.entered: list[int] = []
        self.refusing: set[str] = set()
        self.touch("load")

    def touch(self, what: str) -> None:
        """Count a call, turn upward rounding on, and refuse where the test asked for it."""
        self.calls.append(what)
        self.entered.append(self.library.fegetround())
        assert self.library.fesetround(self.upward) == 0
        assert _added(1.0, 2.0**-60) == math.nextafter(1.0, 2.0)
        if what in self.refusing:
            msg = f"the plugin refuses {what}"
            raise RuntimeError(msg)

    @property
    def name(self) -> str:
        self.touch("name")
        return "Vital"

    @property
    def version(self) -> str:
        self.touch("version")
        return self.version_text

    @property
    def parameters(self) -> dict[str, _FakeParameter]:
        self.touch("parameters")
        hosted = {_HOST_ID: _FakeParameter(self)}
        if self.twinned:
            hosted[_TWIN_ID] = _FakeParameter(self)
        return hosted

    @property
    def preset_data(self) -> bytes:
        self.touch("preset_data")
        if self.value == self.broken_at:
            return b"not a state"
        settings = {} if self.value == self.missing_at else {_HOST_ID: _preset_value(self.value)}
        text = json.dumps({"settings": settings}).encode("utf-8")
        if self.value == self.bare_at:
            text = self.bare_text
        return wrap(PluginState.model_validate({**_CONTAINERS, "text": text}))

    @preset_data.setter
    def preset_data(self, data: bytes) -> None:
        self.touch("set_preset_data")
        settings = json.loads(unwrap(data).text)["settings"]
        self.value = (settings[_HOST_ID] - 8.0) / 128.0

    def process(
        self, _midi: list[tuple[bytes, float]], duration: float, sample_rate: int
    ) -> NDArray[np.float32]:
        self.touch("process")
        samples = 3 if self.short else int(duration * sample_rate)
        return np.zeros((2, samples), dtype=np.float32)


@pytest.fixture
def fake(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[[], tuple[VitalHost, _FakePlugin]]]:
    """Return a maker of a host over the fake plugin, the environment restored after the test."""
    library, upward = _upward_or_skip()
    original = library.fegetround()
    monkeypatch.setattr(_FakePlugin, "library", library, raising=False)
    monkeypatch.setattr(_FakePlugin, "upward", upward, raising=False)
    monkeypatch.setattr(platform, "machine", lambda: parameter_map().machine)
    made: list[_FakePlugin] = []

    def load(path: str) -> _FakePlugin:
        plugin = _FakePlugin(path)
        made.append(plugin)
        return plugin

    monkeypatch.setattr(pedalboard, "VST3Plugin", load)

    def make() -> tuple[VitalHost, _FakePlugin]:
        return VitalHost(tmp_path), made[-1]

    yield make
    library.fesetround(original)


_Maker = Callable[[], tuple[VitalHost, _FakePlugin]]


def test_every_public_method_gives_the_environment_back(fake: _Maker) -> None:
    """Each call into the plugin turns upward rounding on; after each public method it is off."""
    library = _FakePlugin.library
    original = library.fegetround()
    hosted, plugin = fake()
    cutoff = ParameterId(_HOST_ID)
    calls: list[Callable[[], object]] = [
        lambda: hosted.name,
        lambda: hosted.version,
        lambda: hosted.get(cutoff),
        lambda: hosted.set(cutoff, 0.5),
        hosted.preset_data,
        hosted.state,
        lambda: hosted.load_state(hosted.state()),
        lambda: hosted.render([], 10, 48000),
        lambda: hosted.display_texts(_HOST_ID, [0.0, 1.0]),
        lambda: hosted.measure([0.0, 1.0]),
    ]
    assert library.fegetround() == original  # the load itself
    before = len(plugin.calls)
    for call in calls:
        call()
        assert library.fegetround() == original, plugin.calls[-1]
        assert _added(1.0, 2.0**-60) == 1.0
        assert len(plugin.calls) > before  # the plugin was reached
        before = len(plugin.calls)
    # These two read the mapping held and reach the plugin only for a parameter the map lacks.
    assert hosted.parameter_ids() == (cutoff,)
    assert hosted.unmapped_parameters() == ()
    assert len(plugin.calls) == before


def test_what_pedalboard_raises_is_the_package_s_error(fake: _Maker) -> None:
    """A value, a state or a render the plugin refuses is the host's error, chained from its."""
    hosted, plugin = fake()
    plugin.refusing = {"set_raw_value", "set_preset_data", "process"}
    with pytest.raises(PluginStateError) as state:
        hosted.set(ParameterId(_HOST_ID), 0.5)
    assert isinstance(state.value.__cause__, RuntimeError)
    with pytest.raises(PluginStateError) as loaded:
        hosted.load_state(hosted.state())
    assert isinstance(loaded.value.__cause__, RuntimeError)
    with pytest.raises(PluginRenderError) as render:
        hosted.render([], 10, 48000)
    assert isinstance(render.value.__cause__, RuntimeError)
    assert plugin.value == _START


def test_a_measurement_restores_the_state_however_it_ends(fake: _Maker) -> None:
    """A read that fails mid-grid leaves the plugin where the measurement found it."""
    hosted, plugin = fake()
    plugin.broken_at = 0.5
    with pytest.raises(PluginStateError):
        hosted.measure([0.0, 0.5, 1.0])
    assert plugin.value == _START
    assert plugin.calls[-1] == "set_preset_data"


def test_a_measurement_is_the_values_the_state_held(fake: _Maker) -> None:
    """Each grid point's preset value and text, the state restored after."""
    hosted, plugin = fake()
    (measured,) = hosted.measure([0.0, 0.5, 1.0])
    assert (measured.host_id, measured.preset_key, measured.preset_default) == (
        _HOST_ID,
        _HOST_ID,
        60.0,
    )
    assert measured.presets == (8.0, 72.0, 136.0)
    assert measured.texts == ("-52 semitones", "12 semitones", "76 semitones")
    assert plugin.value == _START


def test_the_map_is_refused_on_another_machine_where_it_is_first_used(
    fake: _Maker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The host loads and measures on any machine; the map's scales are used only on its own."""
    hosted, _ = fake()
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    hosted.measure([0.0, 1.0])
    with pytest.raises(MapMismatchError) as caught:
        hosted.get(ParameterId(_HOST_ID))
    assert (caught.value.what, caught.value.measured, caught.value.found) == (
        "machine",
        "arm64",
        "x86_64",
    )
    assert str(caught.value) == "the map's machine is 'arm64', here 'x86_64'"


def test_a_render_is_the_first_samples_asked_for_in_one_block(fake: _Maker) -> None:
    """One sample more is asked for and the first `samples` returned, contiguous."""
    hosted, plugin = fake()
    audio = hosted.render([], 7, 44100)
    assert audio.shape == (2, 7)
    assert audio.flags["C_CONTIGUOUS"]
    plugin.short = True
    with pytest.raises(PluginRenderError, match="given"):
        hosted.render([], 7, 44100)


@pytest.mark.parametrize(
    ("samples", "rate"),
    [(10.5, 48000), (100, 44100.7), (0, 48000), (True, 48000), (100, True)],
)
def test_a_render_length_or_rate_that_is_not_a_positive_whole_number_is_refused(
    fake: _Maker, samples: float, rate: float
) -> None:
    """A fraction of a sample, a fractional rate, no length or a bool is refused, unrendered."""
    hosted, plugin = fake()
    with pytest.raises(PluginRenderError, match="positive"):
        hosted.render([], samples, rate)  # type: ignore[arg-type]
    assert "process" not in plugin.calls


def test_a_state_that_nests_too_deeply_is_refused_as_the_package(fake: _Maker) -> None:
    """A text the decoder cannot read for its depth is the host's error, the plugin unchanged."""
    hosted, plugin = fake()
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(b'{"a":' + b"[" * 200000)
    assert isinstance(caught.value.__cause__, PatchbayValidationError)
    assert "set_preset_data" not in plugin.calls


@pytest.mark.parametrize(
    ("refused", "reach"),
    [
        ("name", lambda hosted: hosted.name),
        ("version", lambda hosted: hosted.version),
        ("raw_value", lambda hosted: hosted.get(ParameterId(_HOST_ID))),
        ("preset_data", lambda hosted: hosted.preset_data()),
        ("preset_data", lambda hosted: hosted.state()),
        ("text", lambda hosted: hosted.display_texts(_HOST_ID, [0.0])),
        ("set_raw_value", lambda hosted: hosted.measure([0.0, 1.0])),
    ],
)
def test_every_reach_the_plugin_refuses_is_the_package_s_error(
    fake: _Maker, refused: str, reach: Callable[[VitalHost], object]
) -> None:
    """A reach the plugin refuses, from any method, is the host's error, chained from its."""
    hosted, plugin = fake()
    hosted.get(ParameterId(_HOST_ID))  # the map resolved, so the refusal is the reach's own
    plugin.refusing = {refused}
    with pytest.raises(PluginStateError) as caught:
        reach(hosted)
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert f"refuses {refused}" in caught.value.reason
    assert plugin.value == _START


def test_a_restore_the_plugin_refuses_is_the_package_s_error_after_the_read_s(fake: _Maker) -> None:
    """A refused restore is the host's error, chained, the read's failure kept in its chain."""
    hosted, plugin = fake()
    plugin.refusing = {"set_preset_data"}
    with pytest.raises(PluginStateError) as alone:
        hosted.measure([0.0, 1.0])
    assert isinstance(alone.value.__cause__, RuntimeError)
    assert plugin.calls[-1] == "set_preset_data"
    plugin.broken_at = 0.5
    with pytest.raises(PluginStateError) as after:
        hosted.measure([0.0, 0.5, 1.0])
    assert isinstance(after.value.__cause__, RuntimeError)
    assert isinstance(after.value.__cause__.__context__, PluginStateError)
    assert "not a state" not in after.value.reason


def test_every_call_into_the_plugin_is_entered_in_the_process_s_own_environment(
    fake: _Maker,
) -> None:
    """Each call is its own guard: no call finds the rounding mode the one before it left.

    One guard around a measurement's grid would hand the second call the first's upward mode, and
    the JSON parsed between them would run under it.
    """
    library = _FakePlugin.library
    original = library.fegetround()
    hosted, plugin = fake()
    hosted.measure([0.0, 0.5, 1.0])
    hosted.load_state(hosted.state())
    hosted.set(ParameterId(_HOST_ID), 0.25)
    hosted.render([], 4, 48000)
    assert len(plugin.calls) > len([0.0, 0.5, 1.0]) * 2
    assert plugin.entered == [original] * len(plugin.calls)


def test_a_parameter_that_changes_the_preset_s_keys_is_named(fake: _Maker) -> None:
    """A grid row holding other keys than the state's is the census's error, by label, restored."""
    hosted, plugin = fake()
    plugin.missing_at = 0.5
    with pytest.raises(CensusError) as caught:
        hosted.measure([0.0, 0.5, 1.0])
    assert caught.value.label == "Filter 1 Cutoff"
    assert "changes the preset's keys" in caught.value.reason
    assert _HOST_ID in caught.value.reason
    assert plugin.value == _START


def test_the_map_is_refused_on_another_vital_version_where_it_is_first_used(fake: _Maker) -> None:
    """A map measured from another version is refused where first needed, after measuring."""
    hosted, plugin = fake()
    plugin.version_text = "1.7.0"
    hosted.measure([0.0, 1.0])
    with pytest.raises(MapMismatchError) as caught:
        hosted.get(ParameterId(_HOST_ID))
    assert (caught.value.what, caught.value.measured, caught.value.found) == (
        "vital_version",
        "1.6.4",
        "1.7.0",
    )


def test_a_load_reuses_the_containers_read_when_the_plugin_loaded(fake: _Maker) -> None:
    """A state load reads nothing from the plugin first: the containers were read once, at load."""
    hosted, plugin = fake()
    assert plugin.calls.count("preset_data") == 1
    text = hosted.state()
    before = plugin.calls.count("preset_data")
    hosted.load_state(text)
    assert plugin.calls.count("preset_data") == before
    assert plugin.calls[-1] == "set_preset_data"


def test_a_plugin_whose_state_the_codec_cannot_read_is_refused_at_load(
    fake: _Maker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A state that is not one this package reads is refused by path, where the plugin loads."""
    monkeypatch.setattr(_FakePlugin, "broken_at", _START)
    with pytest.raises(PluginLoadError) as caught:
        fake()
    assert "its state is not one this package reads" in caught.value.reason
    assert isinstance(caught.value.__cause__, PluginStateError)


def test_a_measurement_puts_each_parameter_back_and_loads_the_state_once(
    fake: _Maker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two parameters measured: each set back by its normalized value, the state loaded once, last.

    A load after each parameter would load twice; one parameter alone could not tell them apart.
    """
    monkeypatch.setattr(_FakePlugin, "twinned", True)
    hosted, plugin = fake()
    measured = hosted.measure([0.0, 0.5, 1.0])
    assert [measurement.host_id for measurement in measured] == [_HOST_ID, _TWIN_ID]
    assert plugin.calls.count("set_preset_data") == 1
    assert plugin.calls[-1] == "set_preset_data"
    grid_and_back = len([0.0, 0.5, 1.0]) + 1
    assert plugin.calls.count("set_raw_value") == 2 * grid_and_back
    assert plugin.value == _START


@pytest.mark.parametrize("text", [b"{}", b'{"settings":[]}'], ids=["no settings", "a list"])
def test_a_state_holding_no_settings_object_is_the_package_s_error(
    fake: _Maker, text: bytes
) -> None:
    """A state whose text has no settings object is PluginStateError, by name, and restored."""
    hosted, plugin = fake()
    plugin.bare_at, plugin.bare_text = 0.5, text
    with pytest.raises(PluginStateError, match="no settings object"):
        hosted.measure([0.0, 0.5, 1.0])
    assert plugin.value == _START
    assert plugin.calls[-1] == "set_preset_data"


@pytest.mark.parametrize("value", ["0.5", None, True], ids=["text", "None", "a bool"])
def test_a_normalized_value_that_is_no_number_is_refused_as_the_package(
    fake: _Maker, value: object
) -> None:
    """A value that is no number, or a bool, is ParameterRangeError, and nothing is set."""
    hosted, plugin = fake()
    with pytest.raises(ParameterRangeError) as caught:
        hosted.set(ParameterId(_HOST_ID), value)  # type: ignore[arg-type]
    assert caught.value.given is value
    assert "set_raw_value" not in plugin.calls
    hosted.set(ParameterId(_HOST_ID), np.float32(0.5))  # type: ignore[arg-type]
    assert plugin.value == 0.5  # noqa: PLR2004 - the value just set
    assert type(plugin.value) is float


def test_display_texts_for_a_host_id_not_hosted_is_named(fake: _Maker) -> None:
    """A host id the plugin does not host is UnknownParameterError, naming it, nothing reached."""
    hosted, plugin = fake()
    before = len(plugin.calls)
    with pytest.raises(UnknownParameterError) as caught:
        hosted.display_texts("no_such_parameter", [0.0])
    assert (caught.value.parameter_id, caught.value.instrument) == ("no_such_parameter", "Vital")
    assert len(plugin.calls) == before
