"""What the host does with no plugin needed to show it, so CI, which has no Vital, holds it too.

A path that gives no Vital is refused as the package, by name. The floating-point guard every call
into the plugin goes through is found where the tests run, and gives the environment back however
the block changed it; a fake plugin that changes the rounding mode on every call shows each public
method gives it back and that each call is entered with the process's own. The same fake shows
what pedalboard raises, from any reach, is the package's error, that a measurement puts each
parameter back and loads the state once however it ends, that the containers are read once, that
a state, a value or an id the host cannot take is the package's error, and that the map is refused
on another machine or Vital version.

A state is written under a watch that answers Vital's alert. A stand-in for it shows the watch is
in place for the length of a write and at no other time, a write that raises included; that an
alert answered is the package's error with the alert's words; and that a load from a second thread
is refused before the plugin is called. The marker a load is checked with is worked out from
primitives, and the fake shows a load that leaves it is refused as ignored and the marker set
back. The watch itself, AppKit's, is run on a real alert in a child this module can kill. No test
here gives Vital anything. What the host does with a loaded Vital is
`tests/integration/test_vital_plugin.py`'s.

The real watch, built over a stand-in for the method it replaces, shows that an interrupt in its
install leaves the method its own, that an alert it could not note is still an error, and that
every alert of one write is in that error. The fake shows the same of an interrupt in the marker's
plant, that a marker value that is no number is refused before anything is set, and that the
count of writes begun is raised before the first change and by nothing refused before it.
"""

import ctypes
import ctypes.util
import json
import math
import platform
import subprocess
import sys
import threading
import types
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import ClassVar, NoReturn

import numpy as np
import pedalboard
import pytest
from builders import StandInWatch, first_depth_the_decoder_refuses, nested
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
    PluginThreadError,
    UnknownParameterError,
)
from patchbay_vital.host import (
    DEFAULT_PATH,
    Alert,
    VitalHost,
    _AppKitWatch,
    _c_library,
    _environment_kept,
    _floats,
    _planted,
    _settings,
)
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
# The fixture makes that one parameter the marker a load is checked with, and puts a stand-in
# watch in place of the one that answers Vital's alert.
_HOST_ID = "filter_1_cutoff"
_TWIN_ID = "filter_2_cutoff"
_START = 0.40625  # normalized, the plugin's default of 60 semitones
_ALERT = ("Error opening preset", "a stand-in's words")
_SECOND_ALERT = ("Error opening sample", "a stand-in's second words")
_LOAD = ["raw_value", "set_raw_value", "set_preset_data", "raw_value"]
"""The calls a checked load makes: the marker read and set, the state written, the marker read."""
_MAP = ["name", "version"]
"""What a host reads once, where it first needs the map: the plugin it was measured from."""
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
        cut, self._plugin.cutting = self._plugin.cutting, None
        if cut is not None and cut[0] == "before it sets":
            raise cut[1]
        self._plugin.value = value
        if cut is not None:
            raise cut[1]

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
    watch: ClassVar[StandInWatch]
    alerting = ""  # "after the floats", "before the floats", "then refused", "unreadable",
    # "twice", "twice, the second unread" or "unnoted"
    cutting: tuple[str, BaseException] | None = None  # an error the next set raises, and when
    ignoring = False  # whether a state write changes nothing and says nothing
    raising: BaseException | None = None  # an error from outside the package a state write raises
    refuse_after_write: frozenset[str] = frozenset()  # calls refused once a state write begins
    unread: BaseException = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "a stand-in's read")

    def __init__(self, path: str) -> None:
        self.path = path
        self.value = _START
        self.calls: list[str] = []
        self.entered: list[int] = []
        self.refusing: set[str] = set()
        self.watched: list[bool] = []  # whether the watch was in place at each state write
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
        self.watched.append(self.watch.in_place)
        self.refusing |= self.refuse_after_write
        self.touch("set_preset_data")
        if self.raising is not None:
            raise self.raising
        if self.ignoring:
            return
        if self.alerting in {"before the floats", "then refused"}:
            self.watch.alert(*_ALERT)
            if self.alerting == "then refused":
                msg = "the plugin refuses the state after its alert"
                raise RuntimeError(msg)
            return
        if self.alerting.startswith("twice"):
            self.watch.alert(*_ALERT)
            if self.alerting == "twice":
                self.watch.alert(*_SECOND_ALERT)
            else:
                self.watch.unreadable_alert(self.unread)
            return
        if self.alerting == "unnoted":
            self.watch.unnoted_alert()
            return
        settings = json.loads(unwrap(data).text)["settings"]
        self.value = (settings[_HOST_ID] - 8.0) / 128.0
        if self.alerting == "after the floats":
            self.watch.alert(*_ALERT)
        if self.alerting == "unreadable":
            self.watch.unreadable_alert(self.unread)

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
    watch = StandInWatch()
    monkeypatch.setattr(_FakePlugin, "library", library, raising=False)
    monkeypatch.setattr(_FakePlugin, "upward", upward, raising=False)
    monkeypatch.setattr(_FakePlugin, "watch", watch, raising=False)
    monkeypatch.setattr(host, "_ALERTS", watch)
    monkeypatch.setattr(host, "MARKER", ParameterId(_HOST_ID))
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
    made = len(plugin.calls)
    hosted.load_state(text)
    assert plugin.calls.count("preset_data") == before
    assert plugin.calls[made:] == [*_MAP, *_LOAD]
    hosted.load_state(text)
    assert plugin.calls[made:] == [*_MAP, *_LOAD, *_LOAD]


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


# --- a state write: the watch, the thread, the marker --------------------------------------------


def _text_holding(cutoff: float) -> bytes:
    """Return a state's text that holds the fake's one parameter at a preset value."""
    return json.dumps({"settings": {_HOST_ID: cutoff}}).encode("utf-8")


def test_the_watch_is_in_place_for_a_state_write_and_at_no_other_time(fake: _Maker) -> None:
    """Nothing is replaced outside a write, and it is put back when the write raises.

    The stand-in says when it is in place and the fake plugin notes that at each state write: a
    load's, a load's that pedalboard refuses, and the one a measurement ends on.
    """
    hosted, plugin = fake()
    watch = _FakePlugin.watch
    assert (watch.in_place, watch.entered) == (False, 0)  # loading the plugin watches nothing
    hosted.set(ParameterId(_HOST_ID), 0.5)
    hosted.state()
    hosted.render([], 10, 48000)
    assert (plugin.watched, watch.in_place, watch.entered) == ([], False, 0)
    hosted.load_state(hosted.state())
    assert (plugin.watched, watch.in_place, watch.entered) == ([True], False, 1)
    plugin.refusing = {"set_preset_data"}
    with pytest.raises(PluginStateError):
        hosted.load_state(hosted.state())
    assert (plugin.watched, watch.in_place, watch.entered) == ([True, True], False, 2)
    plugin.refusing = set()
    hosted.measure([0.0, 1.0])
    assert (plugin.watched, watch.in_place, watch.entered) == ([True, True, True], False, 3)


def test_a_state_the_plugin_answers_with_its_alert_is_the_package_s_error_with_its_words(
    fake: _Maker,
) -> None:
    """An alert answered during the write is PluginStateError; the plugin holds the text in part.

    Vital raises no error of its own for it, so there is no cause. The marker had moved to the
    text's value before the alert, so it is not set back: the last call is its read.
    """
    hosted, plugin = fake()
    plugin.alerting = "after the floats"
    made = len(plugin.calls)
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert all(words in caught.value.reason for words in _ALERT)
    assert caught.value.__cause__ is None
    assert plugin.value == (104.0 - 8.0) / 128.0
    assert plugin.calls[made:] == [*_MAP, *_LOAD]


@pytest.mark.parametrize("how", ["refused", "an alert before the floats"])
def test_a_marker_a_failed_write_left_is_set_back_to_the_value_it_had(
    fake: _Maker, how: str
) -> None:
    """A write that fails before it takes the text leaves the plugin holding what it held.

    The parameter held 0.25, and the text's 104 is in the upper half of 8 to 136, so the marker
    was planted at 0.0: the write left it there, and it is set to 0.25 again.
    """
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    if how == "refused":
        plugin.refusing = {"set_preset_data"}
    else:
        plugin.alerting = "before the floats"
    made = len(plugin.calls)
    with pytest.raises(PluginStateError):
        hosted.load_state(_text_holding(104.0))
    assert plugin.calls[made:] == [*_LOAD, "set_raw_value"]
    assert plugin.value == 0.25  # noqa: PLR2004 - the value it had


def test_a_load_the_plugin_ignores_is_refused_by_the_marker_it_left(fake: _Maker) -> None:
    """A write that changes nothing and says nothing is PluginStateError, and nothing is changed.

    The start's 60 is in the lower half, so the marker was planted at 1.0, where the write left
    it: the load was ignored. The same text loaded by a plugin that takes it moves the marker.
    """
    hosted, plugin = fake()
    text = hosted.state()
    plugin.ignoring = True
    made = len(plugin.calls)
    with pytest.raises(PluginStateError, match="ignored the state") as caught:
        hosted.load_state(text)
    assert _HOST_ID in caught.value.reason
    assert caught.value.__cause__ is None
    assert plugin.calls[made:] == [*_MAP, *_LOAD, "set_raw_value"]
    assert plugin.value == _START
    plugin.ignoring = False
    hosted.load_state(text)
    assert plugin.value == _START


_ABSENT = object()


@pytest.mark.parametrize(
    ("key", "held", "planted"),
    [
        # filter_1_on, the marker: a switch, 0 to 1, its midpoint 0.5 and its default 0
        ("filter_1_on", 0.0, 1.0),
        ("filter_1_on", 1.0, 0.0),
        ("filter_1_on", 0.5, 0.0),
        ("filter_1_on", 0.49, 1.0),
        ("filter_1_on", 1, 0.0),
        ("filter_1_on", 1e30, 0.0),
        ("filter_1_on", -1e30, 1.0),
        ("filter_1_on", _ABSENT, 1.0),
        # filter_1_cutoff: linear, 8 to 136, its midpoint 72 and its default 60
        ("filter_1_cutoff", 72.0, 0.0),
        ("filter_1_cutoff", 71.99, 1.0),
        ("filter_1_cutoff", _ABSENT, 1.0),
    ],
)
def test_the_marker_is_planted_at_the_end_of_its_range_the_text_does_not_hold(
    key: str, held: object, planted: float
) -> None:
    """The maximum, unless the text's value is in the upper half of the scale; then the minimum.

    Each expected value is worked out here from the scale's two ends and the default, written
    out: a text without the key holds the default. What is planted is an end, which the scale
    holds exactly, half the range or more from the text's.
    """
    record = parameter_map().find(ParameterId(key))
    ends = {"filter_1_on": (0.0, 1.0, 0.0), "filter_1_cutoff": (8.0, 136.0, 60.0)}[key]
    assert (record.scale.minimum, record.scale.maximum, record.preset_default) == ends
    settings = {} if held is _ABSENT else {key: held}
    text = json.dumps({"settings": settings}).encode("utf-8")
    assert _planted(record, text) == planted
    end = record.scale.to_preset(planted)
    assert end in ends[:2]
    assert record.scale.holds(end)
    its_own = ends[2] if held is _ABSENT else float(held)  # type: ignore[arg-type]
    clamped = min(max(its_own, ends[0]), ends[1])
    assert abs(end - clamped) >= (ends[1] - ends[0]) / 2


def test_a_text_with_no_settings_object_holds_the_marker_s_default() -> None:
    """A state whose settings is no object holds no value for the marker: its default decides."""
    record = parameter_map().find(host.MARKER)
    assert _planted(record, b'{"settings":[]}') == 1.0
    assert _planted(record, b"{}") == 1.0


def test_the_marker_is_a_switch_the_map_holds() -> None:
    """`MARKER` is a boolean on a scale from 0 to 1, so each end is a value it holds exactly."""
    record = parameter_map().find(host.MARKER)
    assert record.parameter.kind == "boolean"
    assert (record.scale.kind, record.scale.minimum, record.scale.maximum) == ("indexed", 0.0, 1.0)
    assert (record.scale.to_preset(0.0), record.scale.to_preset(1.0)) == (0.0, 1.0)


def test_a_load_from_a_second_thread_is_refused_before_the_plugin_is_called(fake: _Maker) -> None:
    """Where a load is the main thread's, another thread's is PluginThreadError, nothing touched.

    The error names the thread. The same load is then made from the main thread.
    """
    hosted, plugin = fake()
    text = hosted.state()
    made = len(plugin.calls)
    caught: list[PluginThreadError] = []

    def load() -> None:
        try:
            hosted.load_state(text)
        except PluginThreadError as error:
            caught.append(error)

    thread = threading.Thread(target=load, name="a second thread")
    thread.start()
    thread.join()
    (error,) = caught
    assert error.thread == "a second thread"
    assert "a second thread" in str(error)
    assert (plugin.calls[made:], _FakePlugin.watch.entered) == ([], 0)
    hosted.load_state(text)
    assert plugin.calls[made:] == [*_MAP, *_LOAD]


def test_where_no_alert_is_answered_a_load_is_made_from_any_thread(fake: _Maker) -> None:
    """Off macOS the host does what it did: a load from a second thread is made."""
    hosted, plugin = fake()
    _FakePlugin.watch.main_thread_only = False
    text = hosted.state()
    made = len(plugin.calls)
    thread = threading.Thread(target=lambda: hosted.load_state(text))
    thread.start()
    thread.join()
    assert plugin.calls[made:] == [*_MAP, *_LOAD]


def test_where_the_map_is_not_the_plugin_s_a_load_is_made_unchecked(fake: _Maker) -> None:
    """With a map measured from another Vital no marker is set, and an ignored load is not seen.

    The map is sought once, which reads the plugin's name and version; the second load reads
    neither.
    """
    hosted, plugin = fake()
    text = hosted.state()
    plugin.version_text = "1.7.0"
    plugin.ignoring = True
    made = len(plugin.calls)
    hosted.load_state(text)
    assert plugin.calls[made:] == ["name", "version", "set_preset_data"]
    hosted.load_state(text)
    assert plugin.calls[made:] == ["name", "version", "set_preset_data", "set_preset_data"]
    assert plugin.watched == [True, True]  # each write still under the watch


def test_without_the_runtime_the_host_refuses_to_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On macOS where the runtime or pthread_main_np cannot be reached the host is refused."""
    monkeypatch.setattr(host, "_ALERTS", None)
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(tmp_path)
    assert caught.value.path == str(tmp_path)
    assert "Objective-C runtime and AppKit" in caught.value.reason
    assert "pthread_main_np" in caught.value.reason


def test_off_macos_no_alert_is_watched(monkeypatch: pytest.MonkeyPatch) -> None:
    """On any other platform the watch does nothing, and a write is any thread's, as before."""
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    watch = host._alert_watch()  # noqa: SLF001 - the choice the module makes when it loads
    assert watch is not None
    elsewhere: list[bool] = []
    thread = threading.Thread(target=lambda: elsewhere.append(watch.may_write_here()))
    thread.start()
    thread.join()
    assert (watch.may_write_here(), elsewhere) == (True, [True])
    with watch.answered() as alerts:
        pass
    assert alerts == []


@pytest.mark.parametrize("missing", ["objc", "AppKit", "c"])
def test_on_macos_a_library_that_is_not_found_leaves_no_watch(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    """Where the runtime, AppKit or the C library is not found by name there is no watch.

    The C library is where `pthread_main_np` is looked up; without the watch the host refuses
    to load, saying why.
    """
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    found = ctypes.util.find_library
    monkeypatch.setattr(
        ctypes.util, "find_library", lambda name: None if name == missing else found(name)
    )
    assert host._alert_watch() is None  # noqa: SLF001 - the choice the module makes when it loads


# --- the revision after the review of PR 26 ------------------------------------------------------


def _from_a_second_thread(call: Callable[[], object]) -> PluginThreadError:
    """Run a call on a thread named "a second thread"; return the PluginThreadError it raised."""
    caught: list[PluginThreadError] = []

    def run() -> None:
        try:
            call()
        except PluginThreadError as error:
            caught.append(error)

    thread = threading.Thread(target=run, name="a second thread")
    thread.start()
    thread.join()
    (error,) = caught
    return error


def test_a_measurement_from_a_second_thread_is_refused_before_any_parameter_is_set(
    fake: _Maker,
) -> None:
    """Finding 4: `measure` ends on a state write, so it is the main thread's, asked first.

    Refused before the plugin is touched at all: no parameter is set, no state read or written.
    """
    hosted, plugin = fake()
    made, value, entered = len(plugin.calls), plugin.value, _FakePlugin.watch.entered
    error = _from_a_second_thread(lambda: hosted.measure([0.0, 1.0]))
    assert error.thread == "a second thread"
    assert (plugin.calls[made:], plugin.value, _FakePlugin.watch.entered) == ([], value, entered)


def test_a_state_write_from_a_second_thread_is_refused_by_the_write_itself(fake: _Maker) -> None:
    """Every caller asks first, and `_write` asks again: a caller that forgot still cannot write.

    `_write` is the one place the plugin's state is set; `load_state` and `measure` call it.
    """
    hosted, plugin = fake()
    data = hosted.preset_data()
    made, entered = len(plugin.calls), _FakePlugin.watch.entered
    error = _from_a_second_thread(lambda: hosted._write(data))  # noqa: SLF001 - the one writer
    assert error.thread == "a second thread"
    assert (plugin.calls[made:], _FakePlugin.watch.entered) == ([], entered)


class _StandInMethod:
    """`-[NSAlert runModal]`'s implementation, as `method_setImplementation` holds and sets it.

    `cutting` is an error the next install of anything but the method's own raises, once, before
    it sets the implementation or after it has: an interrupt in the install, or on the line
    after it.
    """

    own = 0x5EED
    """The method's own implementation, by a stand-in address."""

    def __init__(self) -> None:
        self.current: int | None = self.own
        self.installed: list[int | None] = []
        self.cutting: tuple[str, BaseException] | None = None

    def install(self, implementation: int | None) -> None:
        """Set the implementation, as the runtime does; what it replaced is not given back."""
        self.installed.append(implementation)
        cut = None
        if implementation != self.own:
            cut, self.cutting = self.cutting, None
        if cut is not None and cut[0] == "before it sets":
            raise cut[1]
        self.current = implementation
        if cut is not None:
            raise cut[1]


def _watch_over(
    method: _StandInMethod,
    texts: Callable[[int | None], tuple[str, str]] = lambda _alert: ("its message", "its words"),
    on_main: Callable[[], int] = lambda: 1,
) -> _AppKitWatch:
    """Return the real watch, what it takes from the runtime and the C library stood in."""
    return _AppKitWatch(method.install, method.own, texts, on_main)


def test_the_watch_refuses_to_be_entered_while_it_is_in_place_and_puts_the_method_back() -> None:
    """Finding 5: a nested entry is refused by name, before anything is replaced.

    So the callback is never saved as the method's own implementation: the method is the
    callback while the watch is entered and its own afterwards, a block that raised included, and
    the method was set twice for each entry, in and out.
    """
    method = _StandInMethod()
    watch = _watch_over(method)
    callback = ctypes.cast(watch._answer, ctypes.c_void_p).value  # noqa: SLF001 - its address
    with watch.answered():
        assert method.current == callback
        with (
            pytest.raises(PluginStateError, match="the alert watch is already in place"),
            watch.answered(),
        ):
            pass
        assert method.current == callback
    assert (method.current, method.installed) == (method.own, [callback, method.own])
    message = "a write that raises"
    with pytest.raises(KeyError, match=message), watch.answered():
        raise KeyError(message)
    assert method.current == method.own


def test_the_watch_lets_a_state_be_written_only_where_pthread_main_np_says_main() -> None:
    """Finding 6: the process's main thread, as AppKit needs, not the one that started Python.

    `pthread_main_np` gives 1 on the main thread and 0 on any other; the watch writes on 1 alone.
    """
    method = _StandInMethod()
    assert _watch_over(method, on_main=lambda: 1).may_write_here()
    assert not _watch_over(method, on_main=lambda: 0).may_write_here()


def test_on_macos_pthread_main_np_answers_the_main_thread_and_no_other() -> None:
    """The real check, through `ctypes`, with no plugin: true here, false on a second thread.

    The case it is chosen for, an interpreter embedded and started off the main thread, is
    reasoned from what `pthread_main_np` means and not measured.
    """
    if platform.system() != "Darwin":
        pytest.skip(f"pthread_main_np is asked on macOS alone; this is {platform.system()}")
    watch = host._alert_watch()  # noqa: SLF001 - the choice the module makes when it loads
    assert watch is not None
    elsewhere: list[bool] = []
    thread = threading.Thread(target=lambda: elsewhere.append(watch.may_write_here()))
    thread.start()
    thread.join()
    assert (watch.may_write_here(), elsewhere) == (True, [False])


def test_the_callback_notes_an_alert_whose_words_cannot_be_read_and_returns_the_first_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 7: nothing leaves the callback, which ctypes would print, returning 0.

    Called through its own C function, as Vital calls it, with a stand-in alert whose text read
    raises: the alert is noted with what the read raised, and the first button comes back. With
    texts it can read it notes them; with no watch in place it notes nothing. Whatever ctypes
    would print goes to `sys.unraisablehook`, which sees nothing.
    """
    leaked: list[object] = []
    monkeypatch.setattr(sys, "unraisablehook", leaked.append)
    unread = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "a stand-in alert's text")

    def texts(_alert: int | None) -> tuple[str, str]:
        raise unread

    method = _StandInMethod()
    watch = _watch_over(method, texts=texts)
    with watch.answered() as alerts:
        button = watch._answer(None, None)  # noqa: SLF001 - the C function the runtime is given
    assert (button, alerts, leaked) == (1000, [Alert("", "", unread)], [])
    assert alerts[0].unread is unread
    readable = _watch_over(method)
    with readable.answered() as alerts:
        assert readable._answer(None, None) == 1000  # noqa: SLF001, PLR2004 - its first button
    assert alerts == [Alert("its message", "its words")]
    assert (watch._answer(None, None), leaked) == (1000, [])  # noqa: SLF001 - no watch in place


class _NoRoom(list[Alert]):
    """A list no alert can be noted in: there is no memory for one more."""

    def append(self, _alert: Alert, /) -> None:
        msg = "a stand-in's memory"
        raise MemoryError(msg)


class _ThroughTheCallback:
    """In the fake plugin's hands in place of the stand-in watch: an alert is the real callback's.

    The fake raises an alert by calling `alert`, `unreadable_alert` or `unnoted_alert`; here
    each calls the real watch's C function, as Vital's `-[NSAlert runModal]` would, the last
    with nowhere to note the alert.
    """

    def __init__(self, watch: _AppKitWatch) -> None:
        self._watch = watch
        self.buttons: list[int] = []

    @property
    def in_place(self) -> bool:
        return self._watch._alerts is not None  # noqa: SLF001 - whether it is entered

    def alert(self, _message: str, _informative: str) -> None:
        self.buttons.append(self._watch._answer(None, None))  # noqa: SLF001 - as Vital calls it

    def unreadable_alert(self, _unread: BaseException) -> None:
        self.buttons.append(self._watch._answer(None, None))  # noqa: SLF001 - as Vital calls it

    def unnoted_alert(self) -> None:
        self._watch._alerts = _NoRoom()  # noqa: SLF001 - where the callback notes an alert
        self.buttons.append(self._watch._answer(None, None))  # noqa: SLF001 - as Vital calls it


def test_an_alert_whose_words_could_not_be_read_is_the_package_s_error_chained_from_the_read(
    fake: _Maker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Finding 7: still PluginStateError, saying an alert was answered and its words were not read.

    Chained from what the read raised. First on the stand-in watch, then through the real
    watch's callback, whose text read raises. The floats were taken before the alert, so the
    marker is not set back: the last call is its read.
    """
    hosted, plugin = fake()
    plugin.alerting = "unreadable"
    made = len(plugin.calls)
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value.reason == (
        "Vital answered the state with an alert, and its words could not be read "
        f"(UnicodeDecodeError: {plugin.unread})"
    )
    assert caught.value.__cause__ is plugin.unread
    assert plugin.calls[made:] == [*_MAP, *_LOAD]
    unread = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "a real callback's read")

    def texts(_alert: int | None) -> tuple[str, str]:
        raise unread

    real = _watch_over(_StandInMethod(), texts=texts)
    through = _ThroughTheCallback(real)
    monkeypatch.setattr(host, "_ALERTS", real)
    monkeypatch.setattr(_FakePlugin, "watch", through)
    again, plugin = fake()
    plugin.alerting = "unreadable"
    with pytest.raises(PluginStateError, match="its words could not be read") as caught:
        again.load_state(_text_holding(104.0))
    assert (caught.value.__cause__, through.buttons) == (unread, [1000])


def test_an_alert_and_a_pedalboard_refusal_are_one_error_carrying_both(fake: _Maker) -> None:
    """Finding 14: the alert's words are kept when pedalboard raises in the same write.

    One PluginStateError carrying the alert's two texts and pedalboard's, chained from
    pedalboard's own error. The write took nothing, so the marker is set back.
    """
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    plugin.alerting = "then refused"
    made = len(plugin.calls)
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value.reason == (
        f"Vital answered the state with its alert, {_ALERT[0]!r}: {_ALERT[1]!r}; pedalboard "
        "refused the state too: the plugin refuses the state after its alert"
    )
    assert type(caught.value.__cause__) is RuntimeError
    assert plugin.calls[made:] == [*_LOAD, "set_raw_value"]
    assert plugin.value == 0.25  # noqa: PLR2004 - the value it had


@pytest.mark.parametrize(
    "raised",
    [KeyboardInterrupt("a stand-in's interrupt"), MemoryError("a stand-in's memory")],
    ids=["KeyboardInterrupt", "MemoryError"],
)
def test_an_error_from_outside_the_package_in_a_write_leaves_as_itself_and_the_marker_is_set_back(
    fake: _Maker, raised: BaseException
) -> None:
    """Finding 1: the marker is set back on every way out of a write, not on a state error alone.

    Neither error is one `_reached` turns into the package's; each leaves as itself, the same
    object, and the marker the write left as planted is set to the value it had.
    """
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    plugin.raising = raised
    made = len(plugin.calls)
    with pytest.raises(type(raised)) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value is raised
    assert plugin.calls[made:] == [*_LOAD, "set_raw_value"]
    assert plugin.value == 0.25  # noqa: PLR2004 - the value it had


def test_a_marker_that_cannot_be_set_back_is_noted_on_the_write_s_own_error(fake: _Maker) -> None:
    """Finding 1: the write's error leaves, and the one raised setting the marker back is a note.

    pedalboard refuses the write, and then the set that would put the marker back.
    """
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    plugin.refusing = {"set_preset_data"}
    plugin.refuse_after_write = frozenset({"set_raw_value"})
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value.reason == "the plugin refuses set_preset_data"
    assert caught.value.__notes__ == [
        (
            "and the marker could not be set back: PluginStateError: plugin state: the plugin "
            "refuses set_raw_value"
        )
    ]


def test_a_marker_lookup_that_fails_is_sought_again_at_the_next_load(fake: _Maker) -> None:
    """Finding 2: a first lookup that meets another error leaves that load and settles nothing.

    The plugin refuses its version, read to check the map: the load is refused before anything
    is planted, and the next load looks the marker up again and is checked. MapMismatchError
    alone settles it unchecked (`test_where_the_map_is_not_the_plugin_s_a_load_is_made_unchecked`).
    """
    hosted, plugin = fake()
    text = hosted.state()
    plugin.refusing = {"version"}
    made = len(plugin.calls)
    with pytest.raises(PluginStateError, match="the plugin refuses version"):
        hosted.load_state(text)
    assert plugin.calls[made:] == _MAP
    plugin.refusing = set()
    made = len(plugin.calls)
    hosted.load_state(text)
    assert plugin.calls[made:] == [*_MAP, *_LOAD]


def test_the_settings_helper_refuses_a_text_one_level_past_the_decoder_s_limit() -> None:
    """Finding 13: `_planted` and `_floats` read through the one guarded decoder.

    At the decoder's own limit, bisected from it in this test, the text is the package's
    PluginStateError, chained from the guard's ValueError, chained from the RecursionError, and
    no RecursionError leaves.
    """
    text = nested(first_depth_the_decoder_refuses()).encode("utf-8")
    record = parameter_map().find(host.MARKER)
    for read in (_settings, lambda text: _planted(record, text), _floats):
        with pytest.raises(PluginStateError, match="nests too deeply to read") as caught:
            read(text)
        guard = caught.value.__cause__
        assert isinstance(guard, ValueError)
        assert isinstance(guard.__cause__, RecursionError)


def test_a_text_past_the_decoder_s_limit_is_refused_by_the_validator_before_the_marker(
    fake: _Maker,
) -> None:
    """The order alone: the state's validator reads every text first and refuses this one.

    So nothing is planted and the plugin is not called: not even its name and version, read
    when the marker is first sought. This does not exercise `_settings`, which the validator's
    lower limit leaves unreached here (`verification/costs.txt`: 9994 through the validator,
    9997 direct, on Python 3.12.16).
    """
    hosted, plugin = fake()
    made = len(plugin.calls)
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(nested(first_depth_the_decoder_refuses()).encode("utf-8"))
    assert isinstance(caught.value.__cause__, PatchbayValidationError)
    assert plugin.calls[made:] == []


_SWITCH_BETWEEN_ITS_ENDS = (
    # (the text's value, what Vital's parameter read held after the load, what its own text held),
    # each on Vital 1.6.4 (verification/midpoint-probe.txt of the revision after PR 26's review)
    (0.0, 0.0, 0.0),
    (1.401298464324817e-45, 1.401298464324817e-45, 0.0),  # the least float32 above 0
    (0.4999999701976776, 0.4999999701976776, 0.0),  # the float32 below the midpoint
    (0.5, 0.5, 1.0),
    (0.5000000596046448, 0.5000000596046448, 1.0),  # the float32 above it
    (0.9999999403953552, 0.9999999403953552, 1.0),  # the float32 below 1
    (1.0, 1.0, 1.0),
)


@pytest.mark.parametrize(("value", "read", "text"), _SWITCH_BETWEEN_ITS_ENDS)
def test_the_marker_is_never_planted_where_vital_holds_a_switch_s_value(
    value: float, read: float, text: float
) -> None:
    """Finding 10: on Vital, the parameter read holds a switch's value as given.

    Only Vital's own text rounds it, below the midpoint to 0 and from it to 1: the boundaries
    the probe located, each between two adjacent float32s, are written out above. The end
    planted is the other end from the one Vital's text holds, so never what the parameter reads
    after a load Vital took. Expected values from the scale's two ends and the transcript.
    """
    record = parameter_map().find(host.MARKER)
    low, high = record.scale.minimum, record.scale.maximum
    planted = _planted(record, json.dumps({"settings": {"filter_1_on": value}}).encode("utf-8"))
    assert planted == record.scale.to_normalized(high if text == low else low)
    assert record.scale.to_preset(planted) != read


# --- the revision after the second review of PR 26 ------------------------------------------------


def _callback_of(watch: _AppKitWatch) -> int | None:
    """Return the address the runtime is given for the watch's callback."""
    return ctypes.cast(watch._answer, ctypes.c_void_p).value  # noqa: SLF001 - its address


@pytest.mark.parametrize("when", ["before it sets", "after it has set"])
def test_an_interrupt_in_the_watch_s_install_leaves_the_method_its_own(when: str) -> None:
    """Finding 1: the state and the install are under one `try`, whose `finally` puts `own` back.

    An interrupt raised from the install before it sets the method, and one raised once it has,
    as on the line after it: the interrupt leaves as itself, the method is the one the watch has
    kept since it was made, the watch is not in place, and the next entry answers an alert and
    puts the method back as any other.
    """
    method = _StandInMethod()
    watch = _watch_over(method)
    interrupt = KeyboardInterrupt("a stand-in's interrupt")
    method.cutting = (when, interrupt)
    with pytest.raises(KeyboardInterrupt) as caught, watch.answered():
        pytest.fail("the watch was entered though its install was cut off")
    assert caught.value is interrupt
    assert (method.current, method.installed) == (method.own, [_callback_of(watch), method.own])
    assert watch._alerts is None  # noqa: SLF001 - whether it is in place
    with watch.answered() as alerts:
        assert method.current == _callback_of(watch)
        assert watch._answer(None, None) == 1000  # noqa: SLF001, PLR2004 - its first button
    assert (method.current, alerts) == (method.own, [Alert("its message", "its words")])


def test_putting_the_method_s_own_implementation_back_twice_changes_nothing() -> None:
    """Finding 1: the `finally` puts `own` back whether or not the install ran, so twice at times.

    The kept implementation installed over itself leaves the method its own, and the watch then
    replaces it and puts it back as before.
    """
    method = _StandInMethod()
    watch = _watch_over(method)
    with watch.answered():
        pass
    watch._install(watch._own)  # noqa: SLF001 - what the finally does
    watch._install(watch._own)  # noqa: SLF001 - and again
    assert (method.current, watch._own) == (method.own, method.own)  # noqa: SLF001 - the kept one
    with watch.answered():
        assert method.current == _callback_of(watch)
    assert method.current == method.own


def test_a_refused_nested_entry_leaves_the_first_entry_s_state_and_method_as_they_were() -> None:
    """Finding 1: the refusal comes before the `try`, so its `finally` never runs.

    The first entry is still in place after it: the method is still the callback, nothing was
    installed by the entry that was refused, and an alert answered then is noted in the first
    entry's list.
    """
    method = _StandInMethod()
    watch = _watch_over(method)
    with watch.answered() as alerts:
        with pytest.raises(PluginStateError, match="already in place"), watch.answered():
            pytest.fail("a nested entry was let in")
        assert (method.current, method.installed) == (_callback_of(watch), [_callback_of(watch)])
        assert watch._alerts is alerts  # noqa: SLF001 - the first entry's own list
        assert watch._answer(None, None) == 1000  # noqa: SLF001, PLR2004 - its first button
    assert (method.current, alerts) == (method.own, [Alert("its message", "its words")])


def test_the_callback_marks_an_alert_it_cannot_note_and_returns_the_first_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 8: the mark is made first, and everything after it is guarded.

    Called through its own C function with a list that has no room for one more alert: nothing
    leaves the callback, the first button comes back, nothing is noted, and the watch says an
    alert was answered, until it is entered again.
    """
    leaked: list[object] = []
    monkeypatch.setattr(sys, "unraisablehook", leaked.append)
    watch = _watch_over(_StandInMethod())
    with watch.answered() as alerts:
        assert not watch.alerted()
        watch._alerts = _NoRoom()  # noqa: SLF001 - where the callback notes an alert
        button = watch._answer(None, None)  # noqa: SLF001 - the C function the runtime is given
        assert watch.alerted()
    assert (button, alerts, leaked, watch.alerted()) == (1000, [], [], True)
    with watch.answered():
        assert not watch.alerted()


def test_an_alert_that_could_not_be_noted_is_still_the_package_s_error(
    fake: _Maker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Finding 8: a write in which an alert was answered is PluginStateError, noted or not.

    First on the stand-in watch, then through the real watch's callback with no room to note
    the alert. The write took nothing, so the marker is set back.
    """
    said = "Vital answered the state with an alert, which could not be noted"
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    plugin.alerting = "unnoted"
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert (caught.value.reason, caught.value.__cause__, plugin.value) == (said, None, 0.25)
    real = _watch_over(_StandInMethod())
    through = _ThroughTheCallback(real)
    monkeypatch.setattr(host, "_ALERTS", real)
    monkeypatch.setattr(_FakePlugin, "watch", through)
    again, plugin = fake()
    again.set(ParameterId(_HOST_ID), 0.25)
    plugin.alerting = "unnoted"
    with pytest.raises(PluginStateError) as caught:
        again.load_state(_text_holding(104.0))
    assert (caught.value.reason, caught.value.__cause__, plugin.value) == (said, None, 0.25)
    assert through.buttons == [1000]


def test_every_alert_of_one_write_is_in_the_error_in_the_order_answered(fake: _Maker) -> None:
    """Finding 10: two alerts in one write are both reported, in order, with how many.

    Held by the stand-in alone: no text was seen to make Vital raise two. Where the second's
    words could not be read the error says so in its place and is chained from that read.
    """
    hosted, plugin = fake()
    plugin.alerting = "twice"
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value.reason == (
        f"Vital answered the state with 2 alerts: 1, {_ALERT[0]!r}: {_ALERT[1]!r}; "
        f"2, {_SECOND_ALERT[0]!r}: {_SECOND_ALERT[1]!r}"
    )
    assert caught.value.__cause__ is None
    plugin.alerting = "twice, the second unread"
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value.reason == (
        f"Vital answered the state with 2 alerts: 1, {_ALERT[0]!r}: {_ALERT[1]!r}; "
        f"2, words that could not be read (UnicodeDecodeError: {plugin.unread})"
    )
    assert caught.value.__cause__ is plugin.unread


@pytest.mark.parametrize("when", ["before it sets", "after it has set"])
def test_an_interrupt_in_the_marker_s_plant_leaves_as_itself_and_the_marker_is_as_it_was(
    fake: _Maker, when: str
) -> None:
    """Finding 2: the plant is inside the `try` that sets the marker back.

    An interrupt raised from the setter that plants, before it sets the value and once it has,
    as on the line after it: the interrupt leaves as itself and the marker holds the value it
    had, set back where the plant had landed. The count of writes begun was raised before the
    setter was entered: it has moved though the setter set nothing.
    """
    hosted, plugin = fake()
    hosted.set(ParameterId(_HOST_ID), 0.25)
    interrupt = KeyboardInterrupt("a stand-in's interrupt")
    plugin.cutting = (when, interrupt)
    begun, made = hosted.writes_begun, len(plugin.calls)
    with pytest.raises(KeyboardInterrupt) as caught:
        hosted.load_state(_text_holding(104.0))
    assert caught.value is interrupt
    assert (plugin.value, hosted.writes_begun) == (0.25, begun + 1)
    set_back = ["set_raw_value"] if when == "after it has set" else []
    assert plugin.calls[made:] == ["raw_value", "set_raw_value", "raw_value", *set_back]


def test_the_count_of_writes_begun_is_raised_by_a_change_and_by_nothing_refused_before_one(
    fake: _Maker,
) -> None:
    """Findings 3 and 4: `writes_begun` moves when a load or a measurement begins to change.

    A checked load, an unchecked one and a measurement each raise it once. A load refused before
    any change leaves it: from a second thread, a text that is no object, a refused read of the
    marker. It has no setter.
    """
    hosted, plugin = fake()
    text = hosted.state()
    assert hosted.writes_begun == 0  # loading the plugin begins no state write
    hosted.load_state(text)
    hosted.measure([0.0, 1.0])
    assert hosted.writes_begun == 2  # noqa: PLR2004 - one load and one measurement
    _from_a_second_thread(lambda: hosted.load_state(text))
    with pytest.raises(PluginStateError):
        hosted.load_state(b"[]")
    plugin.refusing = {"raw_value"}
    with pytest.raises(PluginStateError, match="the plugin refuses raw_value"):
        hosted.load_state(text)
    assert hosted.writes_begun == 2  # noqa: PLR2004 - none of the three began a write
    with pytest.raises(AttributeError):
        hosted.writes_begun = 0  # type: ignore[misc]
    unchecked, other = fake()
    text = unchecked.state()
    other.version_text = "1.7.0"
    unchecked.load_state(text)
    assert unchecked.writes_begun == 1


@pytest.mark.parametrize(
    ("held", "kind"),
    [
        (True, "a boolean"),
        (False, "a boolean"),
        (None, "null"),
        ("on", "a string"),
        ([1.0], "an array"),
        ({"on": 1.0}, "an object"),
    ],
    ids=["true", "false", "null", "a string", "an array", "an object"],
)
def test_a_marker_value_that_is_no_number_is_refused_before_anything_is_set(
    fake: _Maker, held: object, kind: str
) -> None:
    """Finding 6: which end such a text holds is not known, so the load is refused.

    The order too: the state's validator passes the text, one JSON object, and the marker's
    check refuses it, naming the key and the value's kind. Only the map's two reads were made:
    the marker was not read or set, no state was written, and no write was counted as begun.
    The same refusal on the marker the package ships with.
    """
    hosted, plugin = fake()
    text = json.dumps({"settings": {_HOST_ID: held}}).encode("utf-8")
    assert PluginState.model_validate({**_CONTAINERS, "text": text}).text == text
    begun, made, value = hosted.writes_begun, len(plugin.calls), plugin.value
    with pytest.raises(PluginStateError) as caught:
        hosted.load_state(text)
    said = f"the state holds {kind} under {_HOST_ID}, where the marker reads a number"
    assert caught.value.reason == said
    assert (plugin.calls[made:], plugin.value, hosted.writes_begun) == (_MAP, value, begun)
    switch = parameter_map().find(ParameterId("filter_1_on"))
    shipped = json.dumps({"settings": {"filter_1_on": held}}).encode("utf-8")
    with pytest.raises(PluginStateError, match=f"holds {kind} under filter_1_on"):
        _planted(switch, shipped)


_REAL_ALERT = """
import ctypes
import ctypes.util

from patchbay_vital import host

runtime = ctypes.CDLL(ctypes.util.find_library("objc"))
pointer = ctypes.c_void_p
runtime.objc_getClass.restype = pointer
runtime.objc_getClass.argtypes = [ctypes.c_char_p]
runtime.sel_registerName.restype = pointer
runtime.sel_registerName.argtypes = [ctypes.c_char_p]
runtime.class_getInstanceMethod.restype = pointer
runtime.class_getInstanceMethod.argtypes = [pointer, pointer]
runtime.method_getImplementation.restype = pointer
runtime.method_getImplementation.argtypes = [pointer]


def send(receiver, selector, *arguments, result=pointer, kinds=()):
    call = ctypes.CFUNCTYPE(result, pointer, pointer, *kinds)(("objc_msgSend", runtime))
    return call(receiver, runtime.sel_registerName(selector), *arguments)


def words(text):
    string = runtime.objc_getClass(b"NSString")
    return send(string, b"stringWithUTF8String:", text, kinds=(ctypes.c_char_p,))


send(runtime.objc_getClass(b"NSApplication"), b"sharedApplication")
alert = send(send(runtime.objc_getClass(b"NSAlert"), b"alloc"), b"init")
send(alert, b"setMessageText:", words(b"a test's alert"), kinds=(pointer,))
send(alert, b"setInformativeText:", words(b"its words"), kinds=(pointer,))
method = runtime.class_getInstanceMethod(
    runtime.objc_getClass(b"NSAlert"), runtime.sel_registerName(b"runModal")
)
own = runtime.method_getImplementation(method)
watch = host._ALERTS
with watch.answered() as alerts:
    during = runtime.method_getImplementation(method)
    button = send(alert, b"runModal", result=ctypes.c_long)
after = runtime.method_getImplementation(method)
try:
    with watch.answered():
        raise KeyError("a write that raises")
except KeyError:
    pass
raised = runtime.method_getImplementation(method)
print((type(watch).__name__, button, alerts, during != own, after == own, raised == own))
"""
_REAL_ALERT_SECONDS = 10
"""What the real-alert child is given before this test kills it: answered, it ends at once."""

_REAL_ALERT_WATCHDOG_SECONDS = 30
"""What a child of this module gives itself, past its parent's limit: while the parent lives its
kill comes first; where the parent is gone, killed with no chance to kill its child, the child
ends itself here. Armed by `_armed` with faulthandler's watchdog, a C thread that needs no GIL,
which ended a child blocked in AppKit's alert, and one in Vital's, 0.052 to 0.070 s past a 3 s
limit (`verification/alarm-probe.txt` of the revision after the review of PR 26; `signal.alarm`
did too, and was not used, as it is not on every platform)."""

_STAND_IN_WATCHDOG_SECONDS = 1
_STAND_IN_PARENT_SECONDS = 20
"""For the stand-in no parent kills: its watchdog, short, and the parent's limit far past it, at
which the parent kills it and the test fails, saying the watchdog did not end it."""

_WATCHDOG_HEADER = "Timeout ("
"""How faulthandler's watchdog begins what it writes to stderr: `Timeout (0:00:01)!`. CPython's,
and not documented as a format; the stand-in watchdog test below is the one that fails if it
changes."""


def _armed(script: str, seconds: int) -> str:
    """Return a child's script with faulthandler's watchdog armed as its first statements.

    Before anything that could block is imported: the child exits with status 1 after `seconds`,
    every thread's stack on its stderr, whatever its main thread is doing.
    """
    return f"import faulthandler\nfaulthandler.dump_traceback_later({seconds}, exit=True)\n{script}"


def _ended_itself(returncode: int | None, stderr: str, *, killed: bool) -> bool:
    """Whether a child ended itself at its watchdog's limit: three things together.

    Exit status 1, a line of its stderr beginning `_WATCHDOG_HEADER`, and its parent not having
    killed it. Status 1 alone is also what an uncaught error gives. The same function, by the same
    name and with the same checks, is in tests/integration/test_vital_instrument.py, as no module
    can import from the other suite: a change to one is made to both.
    """
    timed_out = any(line.startswith(_WATCHDOG_HEADER) for line in stderr.splitlines())
    return not killed and returncode == 1 and timed_out


def _child_failed(why: str, stderr: str | bytes | None) -> NoReturn:
    """Fail the test saying why, with the child's stderr, where a watchdog's stack would be.

    The same function is in tests/integration/test_vital_instrument.py: a change to one is made
    to both.
    """
    said = stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else (stderr or "")
    pytest.fail(f"{why}; the child's stderr:\n{said}")


def test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back() -> None:
    """AppKit's own `-[NSAlert runModal]`, in a child this test can kill, on macOS.

    The child arms its watchdog first, then makes an alert and runs it modally under the watch.
    Answered, it returns the first button at once with the alert's two texts noted, and the
    method's implementation is the watch's while it is entered and AppKit's own afterwards, a
    block that raised included. Not answered, the alert would wait for a click: the child is
    then killed at the time limit and the test fails by name, or, where this test was itself
    killed, the child ends itself at its watchdog. It loads no plugin.
    """
    if platform.system() != "Darwin":
        pytest.skip(f"the watch that answers Vital's alert is macOS's; this is {platform.system()}")
    try:
        child = subprocess.run(  # noqa: S603 - this interpreter, and the script above
            [sys.executable, "-c", _armed(_REAL_ALERT, _REAL_ALERT_WATCHDOG_SECONDS)],
            capture_output=True,
            text=True,
            timeout=_REAL_ALERT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as expired:
        why = f"the alert was not answered: its child waited {_REAL_ALERT_SECONDS} s, killed"
        _child_failed(why, expired.stderr)
    if _ended_itself(child.returncode, child.stderr, killed=False):
        why = f"the child ended itself at its {_REAL_ALERT_WATCHDOG_SECONDS} s watchdog: it waited"
        _child_failed(why, child.stderr)
    if child.returncode != 0:
        _child_failed(f"the child ended with status {child.returncode}", child.stderr)
    alerts = [Alert("a test's alert", "its words")]
    answered = ("_AppKitWatch", 1000, alerts, True, True, True)
    assert child.stdout.strip() == repr(answered)


_SLEEPS = """
import time

time.sleep(600)
"""


def test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog() -> None:
    """The watchdog this module's child arms ends it where no parent does: three checks together.

    A stand-in that sleeps for ten minutes, armed for `_STAND_IN_WATCHDOG_SECONDS`, its parent
    killing it only at `_STAND_IN_PARENT_SECONDS`, which fails the test. It ended itself: status
    1, a stderr line beginning `_WATCHDOG_HEADER`, and no kill. That header is CPython's and not
    documented, so this is the test that fails if it changes. It needs no plugin and no macOS.
    """
    assert _STAND_IN_PARENT_SECONDS > _STAND_IN_WATCHDOG_SECONDS
    try:
        child = subprocess.run(  # noqa: S603 - this interpreter, and a script of this module
            [sys.executable, "-c", _armed(_SLEEPS, _STAND_IN_WATCHDOG_SECONDS)],
            capture_output=True,
            text=True,
            timeout=_STAND_IN_PARENT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as expired:
        why = (
            "the watchdog did not end the child: its parent killed it at "
            f"{_STAND_IN_PARENT_SECONDS} s"
        )
        _child_failed(why, expired.stderr)
    if not _ended_itself(child.returncode, child.stderr, killed=False):
        _child_failed(f"the child did not end itself: status {child.returncode}", child.stderr)


def test_the_real_alert_child_s_watchdog_is_past_its_parent_s_limit() -> None:
    """While the parent lives its kill comes first, and the test fails by the parent's name."""
    assert _REAL_ALERT_WATCHDOG_SECONDS > _REAL_ALERT_SECONDS


@pytest.mark.parametrize(
    ("returncode", "stderr", "killed", "ended_itself"),
    [
        (1, "Timeout (0:00:01)!\nThread 0x1 (most recent call first):\n", False, True),
        (1, "Traceback (most recent call last):\nKeyError: 'a'\n", False, False),
        (1, "Timeout (0:00:01)!\n", True, False),
        (-9, "Timeout (0:00:01)!\n", False, False),
        (0, "", False, False),
    ],
    ids=["the watchdog", "an uncaught error", "killed", "another status", "returned"],
)
def test_a_child_ended_itself_only_by_all_three_checks(
    returncode: int, stderr: str, *, killed: bool, ended_itself: bool
) -> None:
    """Status 1, the watchdog's header, and no kill by the parent: each check is needed."""
    assert _ended_itself(returncode, stderr, killed=killed) is ended_itself
