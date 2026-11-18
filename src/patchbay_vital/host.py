"""Vital hosted through pedalboard: the only module importing it, the seam another host replaces.

pedalboard is GPLv3 and this package MIT, so pedalboard comes only with the `host` extra
(`pip install patchbay-vital[host]`), the root package never imports this module, and nothing here
is copied from pedalboard (the host spec's shape.md, Decision 2).

`VitalHost` owns one plugin and speaks plain values, never patchbay's models: a parameter by its
`ParameterId`, which is its preset key, and its normalized value in `[0, 1]`; the plugin's state as
the preset text it holds; a render as an array. pedalboard knows a parameter by another key, the
map's `host_id`, which only this module reads. The plugin is found at the path given, or at
`DEFAULT_PATH`, Vital's macOS install, and nowhere else: there is no search. The map is used only
on the machine it was measured on and with the plugin it was measured from, its scales being that
build's and its records that version's; another is `MapMismatchError`, naming what differs, where
the map is first needed, so the census, which needs no map, still runs there.

What the probes found the plugin does (`verification/probes.txt` and `verification/host-probes.txt`
of the host spec): a state load upgrades an older preset, delays the embedded sample by 4 samples
and re-quantizes it, a 16-bit value moving by up to one step, and may snap a value off the host's
grid; a render that starts from a reset opens with a decaying transient (peak 0.022, under 1e-5 by
50 ms); a MIDI event's time is seconds from the render's start; and pedalboard returns
`int(duration * rate)` samples, so a render asks for one sample more and returns the first
`samples`. The containers around the state's text are read once, when the plugin loads, and every
load reuses them: a load changes the text and no container, which the integration tests hold.
pedalboard's parameter objects: the Python wrappers its public mapping gives are held here, one
mapping per host, and each fetches the plugin's native parameter afresh on every attribute access,
which is what makes holding them safe; a native parameter object held across state loads crashed
the process (`verification/probes-first-attempt.txt`), and none is ever held. What pedalboard
raises is never let out: a read, a state or a value it refuses is `PluginStateError`, a render
`PluginRenderError`, each chained, from every method that reaches it.

Loading Vital, and rendering it, turn on flush-to-zero for the whole process and leave it on, so
every subnormal result after them, in Python, numpy or `patchbay_vital.float32`, becomes zero
(`verification/float-environment.txt`). Every call into the plugin here saves the floating-point
environment before and restores it after, with `fegetenv` and `fesetenv` from the first library
that holds both: the C library on macOS, the maths library on glibc, whose C library has neither
(the revision after PR 9's CI run). Each call is its own guard, so the Python work between two
calls, the JSON a measurement parses among it, runs in the process's own environment and never in
the one the plugin left. The plugin's own processing still runs under the environment it sets for
itself. A unit test with a plugin that changes the rounding mode on every call holds that each
public method gives the environment back and that each call is entered with it.

**A load.** Vital reports no state it cannot use (the spec of issue #20,
`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`, and the revision after the review of
PR 26, `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`, whose `verification/`
directories hold every count here; Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS
26.6.2). It answers a text it cannot read with a modal alert and its caller waits for ever,
nothing in Python running meanwhile; it ignores a text newer than itself without a word; and a
text can kill the process inside Vital's own reading of it. `load_state` does three things about
the first two:

- On macOS it answers the alert before it opens. For the length of each state write,
  `-[NSAlert runModal]` is replaced by a callback that notes the alert, then its two texts, and
  returns its first button at once, and is put back however the write ends, as the
  floating-point environment is. A write in which an alert was answered is `PluginStateError`,
  the alert's own words in it, or, where they could not be read, saying so; and the plugin is
  then part-loaded: of 249 texts that alert, the text's floats were already taken on 246. The
  Objective-C runtime is reached through `ctypes`, and the host refuses to load on macOS where it
  cannot be. The method is replaced for the whole process while a write runs, so any alert run
  on the main thread in that time is answered and counted as the write's; none but Vital's own
  was seen. The watch refuses to be entered while it is in place. Each answered alert leaves one
  window object in the application's list, never shown: 500 after 500 of them.
- On macOS it writes a state on the process's main thread or not at all, by `pthread_main_np`:
  `load_state` and `measure` raise `PluginThreadError` before the plugin is called, and the
  write itself asks again. From another thread AppKit refuses the alert's window, the load
  raises, the parameters are then read stale, and the process died at its next render, 11 of 11.
- It checks the load with a marker. Before the write `MARKER`, a switch, is set to the end of
  its range the text does not hold, and read after it: a write that left it there was ignored,
  and is `PluginStateError`. However the write ends, the marker it left as planted is set back,
  and the write's own error leaves as itself. The marker is the plugin's alone: no model holds
  it. It needs the map, so where the map is not the plugin's the load is made unchecked, as it
  was; any other error in seeking it leaves the load, and the next load seeks it again.

On any other platform a write is made as it always was, from any thread, and nothing was probed
off macOS, nor in a process with no screen: a text Vital cannot read may block there. Nothing here
helps with a text that kills the process, nor with one Vital loads in part: both are issue #25's.
"""

import ctypes
import ctypes.util
import importlib.metadata
import math
import operator
import platform
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import NamedTuple, Protocol, cast

import numpy as np
import pedalboard
from numpy.typing import NDArray
from patchbay import ParameterId, PresetKey

from patchbay_vital.errors import (
    CensusError,
    MapMismatchError,
    ParameterRangeError,
    PluginLoadError,
    PluginRenderError,
    PluginStateError,
    PluginThreadError,
    UnknownParameterError,
    VitalHostError,
)
from patchbay_vital.parameters import MappedParameter, ParameterMap, parameter_map
from patchbay_vital.preset import decoded
from patchbay_vital.state import unwrap, wrap

DEFAULT_PATH = Path("/Library/Audio/Plug-Ins/VST3/Vital.vst3")
"""Where Vital's installer puts the VST3 on macOS; the only place looked at without a path given."""

INSTRUMENT = "Vital"
"""The plugin's name, as it reports it; a plugin at the path by another name is refused."""

MARKER = ParameterId("filter_1_on")
"""The parameter a load is checked with: a switch, so each end of its range is a value it holds
exactly, and the two are the whole range apart."""

type Midi = Sequence[tuple[bytes, float]]
"""MIDI as pedalboard takes it: each message's bytes and its time in seconds from the start."""


class Alert(NamedTuple):
    """An alert as it was answered: its message, the text under it, and what reading them raised.

    `unread` is None where both texts were read; otherwise it is what the read raised, the two
    texts left empty, and the alert was answered all the same.
    """

    message: str
    informative: str
    unread: BaseException | None = None


_CHANNELS = 2

_AXES = 2
"""A render's dimensions: channels by samples."""

_ENVIRONMENT_BYTES = 512
"""Room for any platform's `fenv_t`, which is saved and restored whole, its layout never read."""

_ENVIRONMENT_FUNCTIONS = ("fegetenv", "fesetenv")

_PEDALBOARD_ERRORS = (RuntimeError, ValueError, TypeError)
"""What pedalboard raises when the plugin refuses a read, a state, a value or a render."""

_LIBRARY_NAMES: tuple[Callable[[], str | None], ...] = (
    lambda: ctypes.util.find_library("c"),
    lambda: ctypes.util.find_library("m"),
    lambda: "ucrtbase",
)
"""The libraries tried, in order, each looked up only when the one before it is passed over:
`find_library` runs a subprocess on Linux."""


def _c_library() -> ctypes.CDLL | None:
    """Return the first library that holds `fegetenv` and `fesetenv`, or None where none does.

    The C library first, then the maths library, then Windows' UCRT. A library that loads without
    both is passed over: glibc's C library has neither, and its maths library holds them.
    """
    for find in _LIBRARY_NAMES:
        name = find()
        if name is None:
            continue
        try:
            library = ctypes.CDLL(name)
        except OSError:
            continue
        if all(hasattr(library, function) for function in _ENVIRONMENT_FUNCTIONS):
            return library
    return None


_LIBC = _c_library()

_FIRST_BUTTON = 1000
"""`NSAlertFirstButtonReturn`: what a modal alert gives back when its first button is pressed."""

_RUNTIME_FUNCTIONS = (
    "objc_getClass",
    "sel_registerName",
    "class_getInstanceMethod",
    "method_setImplementation",
    "objc_msgSend",
)

_ANSWER = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)
"""`-[NSAlert runModal]` as a C function: the alert and the selector in, the button out."""


class _AlertWatch(Protocol):
    """What answers the alerts a state write raises, and says where a write may be made."""

    def may_write_here(self) -> bool: ...

    def answered(self) -> AbstractContextManager[list[Alert]]: ...


class _NoWatch:
    """Where no alert is answered, every platform but macOS: a write is made as it always was."""

    def may_write_here(self) -> bool:
        """Any thread may write: nothing here needs the main thread."""
        return True

    @contextmanager
    def answered(self) -> Iterator[list[Alert]]:
        """Watch nothing; the list stays empty."""
        yield []


class _AppKitWatch:
    """Vital's alert answered before it opens, on macOS, through the Objective-C runtime.

    Made from three calls `_alert_watch` builds from the runtime and the C library, so the class
    itself runs on any platform with those calls stood in: `install` sets the implementation of
    `-[NSAlert runModal]` and returns the one it replaced, `texts` reads an alert's message and
    informative text, and `on_main` is `pthread_main_np`, 1 on the process's main thread.

    While `answered` is entered, `-[NSAlert runModal]` is this object's callback, which notes the
    alert and returns the first button; on the way out the method's own implementation is put
    back. The callback is made once and kept, since the runtime holds only its address.

    The watch is one object for the whole process, and it refuses to be entered while it is in
    place, so a nested entry can never save the callback as the method's own implementation and
    put it back on the way out. No lock is needed beyond that: every state write is on the main
    thread here, which `may_write_here` checks first, and nothing runs inside a write but Vital and
    the callback, which writes nothing (the review of PR 26, finding 5).
    """

    def __init__(
        self,
        install: Callable[[int | None], int | None],
        texts: Callable[[int | None], tuple[str, str]],
        on_main: Callable[[], int],
    ) -> None:
        """Keep the three calls, and make the callback the runtime is given."""
        self._install = install
        self._texts = texts
        self._on_main = on_main
        self._answer = _ANSWER(self._answered_at_once)
        self._alerts: list[Alert] | None = None

    def may_write_here(self) -> bool:
        """Whether this is the process's main thread, by `pthread_main_np`, as AppKit needs."""
        return self._on_main() == 1

    def _answered_at_once(self, alert: int | None, _selector: int | None) -> int:
        """Stand in for `-[NSAlert runModal]`: note the alert, then its texts; the first button.

        The alert is noted, and the button to return fixed, before anything that can fail. What
        reading the texts raises is caught and kept in the note: nothing leaves the callback,
        whose error ctypes would print and drop, returning 0 and not the first button.
        """
        button = _FIRST_BUTTON
        noted = self._alerts
        if noted is not None:
            noted.append(Alert("", ""))
            try:
                noted[-1] = Alert(*self._texts(alert))
            except BaseException as error:  # noqa: BLE001 - nothing may leave a ctypes callback
                noted[-1] = Alert("", "", error)
        return button

    @contextmanager
    def answered(self) -> Iterator[list[Alert]]:
        """Answer every alert run while this is entered; yield the list they are noted in.

        PluginStateError, before anything is replaced, when the watch is already in place.
        """
        if self._alerts is not None:
            msg = "the alert watch is already in place: a state write was begun inside another"
            raise PluginStateError(msg)
        alerts: list[Alert] = []
        original = self._install(ctypes.cast(self._answer, ctypes.c_void_p).value)
        self._alerts = alerts
        try:
            yield alerts
        finally:
            self._install(original)
            self._alerts = None


def _alert_texts(runtime: ctypes.CDLL) -> Callable[[int | None], tuple[str, str]]:
    """Return the call that reads an alert's message and informative text, each empty if none."""
    pointer = ctypes.c_void_p
    send_object = ctypes.CFUNCTYPE(pointer, pointer, pointer)(("objc_msgSend", runtime))
    send_bytes = ctypes.CFUNCTYPE(ctypes.c_char_p, pointer, pointer)(("objc_msgSend", runtime))
    selectors = tuple(
        runtime.sel_registerName(name) for name in (b"messageText", b"informativeText")
    )
    utf8 = runtime.sel_registerName(b"UTF8String")

    def text(alert: int | None, selector: int | None) -> str:
        string = send_object(alert, selector)
        raw = send_bytes(string, utf8) if string else None
        return raw.decode("utf-8", "replace") if isinstance(raw, bytes) else ""

    def texts(alert: int | None) -> tuple[str, str]:
        message, informative = (text(alert, selector) for selector in selectors)
        return message, informative

    return texts


def _appkit_watch(runtime: ctypes.CDLL, libc: ctypes.CDLL) -> _AppKitWatch | None:
    """Return the watch made from the runtime and the C library, their types declared.

    None where the runtime lacks a function it calls, the C library `pthread_main_np`, or AppKit
    the method the watch replaces.
    """
    if not all(hasattr(runtime, function) for function in _RUNTIME_FUNCTIONS):
        return None
    if not hasattr(libc, "pthread_main_np"):
        return None
    pointer = ctypes.c_void_p
    runtime.objc_getClass.restype = pointer
    runtime.objc_getClass.argtypes = [ctypes.c_char_p]
    runtime.sel_registerName.restype = pointer
    runtime.sel_registerName.argtypes = [ctypes.c_char_p]
    runtime.class_getInstanceMethod.restype = pointer
    runtime.class_getInstanceMethod.argtypes = [pointer, pointer]
    runtime.method_setImplementation.restype = pointer
    runtime.method_setImplementation.argtypes = [pointer, pointer]
    libc.pthread_main_np.restype = ctypes.c_int
    libc.pthread_main_np.argtypes = []
    method = runtime.class_getInstanceMethod(
        runtime.objc_getClass(b"NSAlert"), runtime.sel_registerName(b"runModal")
    )
    if not method:
        return None

    def install(implementation: int | None) -> int | None:
        replaced: int | None = runtime.method_setImplementation(method, implementation)
        return replaced

    return _AppKitWatch(install, _alert_texts(runtime), libc.pthread_main_np)


def _alert_watch() -> _AlertWatch | None:
    """Return what answers Vital's alert on this platform; None on macOS where nothing can.

    Off macOS nothing is watched. On macOS the Objective-C runtime, AppKit and the C library are
    loaded by name, and the watch is made only where the runtime holds every function it calls,
    AppKit the method it replaces and the C library `pthread_main_np` (`_appkit_watch`).
    """
    if platform.system() != "Darwin":
        return _NoWatch()
    names = [ctypes.util.find_library(name) for name in ("objc", "AppKit", "c")]
    if None in names:
        return None
    try:
        runtime, _, libc = (ctypes.CDLL(name) for name in names)
    except OSError:
        return None
    return _appkit_watch(runtime, libc)


_ALERTS = _alert_watch()


@contextmanager
def _environment_kept() -> Iterator[None]:
    """Restore the floating-point environment after a call into the plugin, however it ends."""
    saved = ctypes.create_string_buffer(_ENVIRONMENT_BYTES)
    if _LIBC is not None:
        _LIBC.fegetenv(saved)
    try:
        yield
    finally:
        if _LIBC is not None:
            _LIBC.fesetenv(saved)


@contextmanager
def _reached(error: Callable[[str], VitalHostError]) -> Iterator[None]:
    """Keep the environment around one call into the plugin; what it refuses is `error`, chained."""
    with _environment_kept():
        try:
            yield
        except _PEDALBOARD_ERRORS as raised:
            raise error(str(raised) or type(raised).__name__) from raised


class _HostedParameter(Protocol):
    """What one of pedalboard's parameters answers: its own attributes and its native object's."""

    @property
    def name(self) -> str: ...

    @property
    def raw_value(self) -> float: ...

    @raw_value.setter
    def raw_value(self, value: float, /) -> None: ...

    def get_text_for_raw_value(self, raw_value: float, /) -> str: ...


class _HostedPlugin(Protocol):
    """What a VST3 pedalboard loaded answers, as this module uses it.

    pedalboard gives its native plugin class `parameters` at import, by adding a mixin to its bases,
    which its type stubs do not show; so the plugin it loads is cast to this, once, where it loads.
    """

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def parameters(self) -> Mapping[str, _HostedParameter]: ...

    @property
    def preset_data(self) -> bytes: ...

    @preset_data.setter
    def preset_data(self, data: bytes, /) -> None: ...

    def process(
        self, midi_messages: list[tuple[bytes, float]], duration: float, sample_rate: int, /
    ) -> NDArray[np.float32]: ...


class HostMeasurement(NamedTuple):
    """One hosted parameter as the census measures it: its values on a grid of normalized ones."""

    host_id: str
    label: str
    preset_key: PresetKey
    preset_default: float
    presets: tuple[float, ...]
    texts: tuple[str, ...]


def _whole(value: int, what: str) -> int:
    """Return `value` as the whole number it is; PluginRenderError when it is not one.

    A bool is not one: `operator.index` would take it as 0 or 1.
    """
    msg = f"a render's {what} is a positive whole number, given {value!r}"
    if isinstance(value, bool):
        raise PluginRenderError(msg)
    try:
        return operator.index(value)
    except TypeError as error:
        raise PluginRenderError(msg) from error


def _normalized(parameter_id: ParameterId, value: float) -> None:
    """Refuse a value that is not a normalized one as ParameterRangeError, before any is set.

    A bool is not one, though `math.isfinite` would take it as 0 or 1; a value that is no number
    is refused by name, `math.isfinite`'s `TypeError` chained.
    """
    if isinstance(value, bool):
        raise ParameterRangeError(parameter_id, 0.0, 1.0, value)
    try:
        finite = math.isfinite(value)
    except TypeError as error:
        raise ParameterRangeError(parameter_id, 0.0, 1.0, value) from error
    if not (finite and 0.0 <= value <= 1.0):
        raise ParameterRangeError(parameter_id, 0.0, 1.0, value)


def _name_of(hosted: _HostedParameter) -> str:
    """Return a hosted parameter's label, one guarded call."""
    with _reached(PluginStateError):
        return hosted.name


def _text_for(hosted: _HostedParameter, point: float) -> str:
    """Return what the plugin shows for a parameter at a normalized value, one guarded call."""
    with _reached(PluginStateError):
        return hosted.get_text_for_raw_value(point)


def _planted(record: MappedParameter, text: bytes) -> float:
    """Return the normalized value the marker is set to before a text is loaded.

    An end of its range, which the parameter holds exactly: the maximum, 1.0, unless the text's
    own value for it is in the upper half of its scale, at the midpoint or above, and then the
    minimum, 0.0. So what is planted is at least half the range from what the text holds, more
    than a set can blur. A text without the key holds the parameter's default, as Vital gives it
    one; a value there that is no number is read as absent. Read through `_settings`.

    For the marker, a switch, Vital's parameter read holds every value given as given, and only
    the state's own text rounds one between the ends, below the midpoint to the minimum and from
    it to the maximum: so what is planted is never what the parameter reads after a load Vital
    took (the review of PR 26, finding 10, `verification/midpoint-probe.txt`).
    """
    settings = _settings(text)
    held = settings.get(record.preset_key) if isinstance(settings, dict) else None
    if isinstance(held, bool) or not isinstance(held, int | float):
        held = record.preset_default
    return 0.0 if held >= (record.scale.minimum + record.scale.maximum) / 2 else 1.0


def _moving_key(
    label: str, defaults: Mapping[str, float], rows: Sequence[Mapping[str, float]]
) -> str:
    """Return the one preset key whose value differs across the rows; CensusError otherwise.

    Each row holds the same keys as the defaults, or the parameter changed what the preset holds,
    which no parameter does: a row with other keys is refused by name before any is indexed.
    """
    for row in rows:
        if row.keys() != defaults.keys():
            changed = sorted(row.keys() ^ defaults.keys())
            raise CensusError(label, f"changes the preset's keys at a grid point: {changed[:4]}")
    moving = [key for key in defaults if len({row[key] for row in rows}) > 1]
    if len(moving) != 1:
        raise CensusError(label, f"moves {len(moving)} preset values: {moving[:4]}")
    return moving[0]


class VitalHost:
    """One Vital through pedalboard: set and read in normalized values, rendered from MIDI."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Load the plugin at `path`, or at `DEFAULT_PATH` when none is given.

        PluginLoadError when there is nothing at the path, the host cannot load what is there, what
        it loads is not Vital, or the state it loads with is not one this package reads.
        """
        where = Path(DEFAULT_PATH if path is None else path)
        if not where.exists():
            raise PluginLoadError(str(where), "there is nothing at the path")
        if _LIBC is None:
            msg = "no library holds fegetenv and fesetenv to keep the floating-point environment"
            raise PluginLoadError(str(where), msg)
        if _ALERTS is None:
            msg = (
                "the Objective-C runtime and AppKit cannot be reached to answer Vital's alert, "
                "or pthread_main_np to find the main thread"
            )
            raise PluginLoadError(str(where), msg)
        try:
            with _environment_kept():
                plugin = cast("_HostedPlugin", pedalboard.VST3Plugin(str(where)))
            with _environment_kept():
                hosted = plugin.parameters
            with _environment_kept():
                name = plugin.name
            with _environment_kept():
                data = plugin.preset_data
        except (ImportError, OSError, *_PEDALBOARD_ERRORS) as error:
            raise PluginLoadError(str(where), str(error) or type(error).__name__) from error
        if name != INSTRUMENT:
            raise PluginLoadError(str(where), f"the plugin there is {name!r}")
        try:
            containers = unwrap(data)
        except PluginStateError as error:
            msg = f"its state is not one this package reads: {error.reason}"
            raise PluginLoadError(str(where), msg) from error
        self._plugin = plugin
        self._hosted = hosted
        self._containers = containers
        self._alerts = _ALERTS
        self._map: ParameterMap | None = None
        self._by_host: dict[str, ParameterId] = {}
        self._marker_sought = False
        self._marker_found: tuple[_HostedParameter, MappedParameter] | None = None

    @property
    def name(self) -> str:
        """The plugin's name, as it reports it."""
        with _reached(PluginStateError):
            return self._plugin.name

    @property
    def version(self) -> str:
        """The plugin's version, as it reports it."""
        with _reached(PluginStateError):
            return self._plugin.version

    @property
    def host(self) -> str:
        """The host this is, by name and version: what a map measured through it records."""
        return f"pedalboard {importlib.metadata.version('pedalboard')}"

    def _parameter_map(self) -> ParameterMap:
        """Return the committed map, and build the host-id lookup, on first use.

        MapMismatchError where the map was measured on another machine, from another instrument or
        from another version of it, naming the first that differs.
        """
        if self._map is None:
            found = parameter_map()
            provenance = (
                ("machine", found.machine, platform.machine()),
                ("instrument", found.instrument, self.name),
                ("vital_version", found.vital_version, self.version),
            )
            for what, measured, here in provenance:
                if measured != here:
                    raise MapMismatchError(what, measured, here)
            self._by_host = {record.host_id: record.id for record in found.parameters}
            self._map = found
        return self._map

    def _hosted_parameter(self, parameter_id: ParameterId) -> _HostedParameter:
        """Return pedalboard's parameter for an id; UnknownParameterError for an id not hosted."""
        record = self._parameter_map().find(parameter_id)
        try:
            return self._hosted[record.host_id]
        except KeyError:
            raise UnknownParameterError(parameter_id, INSTRUMENT) from None

    def parameter_ids(self) -> tuple[ParameterId, ...]:
        """Every hosted parameter's id the map knows, in the host's order.

        Read from the mapping held, its keys Python's: the plugin is not called.
        """
        self._parameter_map()
        return tuple(self._by_host[key] for key in self._hosted if key in self._by_host)

    def unmapped_parameters(self) -> tuple[str, ...]:
        """Return the labels of hosted parameters the map has no record of, in the host's order."""
        self._parameter_map()
        return tuple(
            _name_of(hosted) for key, hosted in self._hosted.items() if key not in self._by_host
        )

    def get(self, parameter_id: ParameterId) -> float:
        """Return a parameter's normalized value; UnknownParameterError for an id not hosted."""
        hosted = self._hosted_parameter(parameter_id)
        with _reached(PluginStateError):
            return float(hosted.raw_value)

    def set(self, parameter_id: ParameterId, normalized: float) -> None:
        """Set a parameter's normalized value.

        UnknownParameterError for an id not hosted; ParameterRangeError for a value outside
        `[0, 1]`, or one that is no number, a bool included, the built-in's refusal chained;
        PluginStateError, chained, for a value the plugin refuses. None changes anything.
        """
        hosted = self._hosted_parameter(parameter_id)
        _normalized(parameter_id, normalized)
        with _reached(PluginStateError):
            hosted.raw_value = float(normalized)

    def preset_data(self) -> bytes:
        """Return the plugin's state as the VST3 preset bytes it gives the host, every container."""
        with _reached(PluginStateError):
            return self._plugin.preset_data

    def state(self) -> bytes:
        """Return the preset text the plugin holds: a `.vital` file's, with its `tuning`."""
        return unwrap(self.preset_data()).text

    def _marker(self) -> tuple[_HostedParameter, MappedParameter] | None:
        """Return the marker's hosted parameter and its record, sought once.

        None where the map is not this plugin's, measured on another machine or from another
        Vital: the host cannot then tell which of the text's keys a hosted parameter is, and a
        load is made unchecked.

        Settled only by a lookup that found the marker or by MapMismatchError: any other error,
        a refused read of the plugin's name or version among them, leaves the load that met it,
        and the next load looks again (the review of PR 26, finding 2).
        """
        if not self._marker_sought:
            try:
                record = self._parameter_map().find(MARKER)
                found = (self._hosted_parameter(MARKER), record)
            except MapMismatchError:
                found = None
            self._marker_found, self._marker_sought = found, True
        return self._marker_found

    def _on_a_writing_thread(self) -> None:
        """Raise PluginThreadError, naming this thread, where a state may not be written from it.

        On macOS a state is written from the process's main thread alone (`may_write_here`);
        anywhere else from any thread. Every caller of `_write` asks this first, before the plugin
        is touched, and `_write` asks it again.
        """
        if not self._alerts.may_write_here():
            raise PluginThreadError(threading.current_thread().name)

    def _write(self, data: bytes) -> None:
        """Give the plugin a state, answering any alert it raises with it.

        PluginThreadError, the plugin not called, on a thread a state may not be written from.
        PluginStateError for a state pedalboard refuses, chained; for one the plugin answered
        with an alert, the alert's own two texts in the reason, or, where they could not be read,
        saying so, chained from what the read raised; and for both at once, one error carrying
        the alert's words and pedalboard's, chained from pedalboard's.
        """
        self._on_a_writing_thread()
        with self._alerts.answered() as alerts:
            try:
                with _reached(PluginStateError):
                    self._plugin.preset_data = data
            except PluginStateError as refused:
                if not alerts:
                    raise
                said = (
                    f"{_alert_said(alerts[0])}; pedalboard refused the state too: {refused.reason}"
                )
                raise PluginStateError(said) from refused.__cause__
        if alerts:
            raise PluginStateError(_alert_said(alerts[0])) from alerts[0].unread

    def _set_back(
        self, hosted: _HostedParameter, planted: float, before: float, error: BaseException
    ) -> None:
        """Set the marker back after a write that raised `error`; a failure is noted on `error`.

        The write's own error is the one that leaves: one raised while setting the marker back is
        attached to it as a note, and never takes its place.
        """
        try:
            self._unplanted(hosted, planted, before)
        except BaseException as second:  # noqa: BLE001 - noted on the write's error, which leaves
            error.add_note(
                f"and the marker could not be set back: {type(second).__name__}: {second}"
            )

    def _unplanted(self, hosted: _HostedParameter, planted: float, before: float) -> bool:
        """Set the marker back to what it was where a write left it as planted; say whether."""
        with _reached(PluginStateError):
            left = hosted.raw_value == planted
        if left:
            with _reached(PluginStateError):
                hosted.raw_value = before
        return left

    def load_state(self, text: bytes) -> None:
        """Load a preset's text into the plugin, inside the containers the plugin loaded with.

        The text is a `.vital` file's or `state`'s: one JSON object, and the one newline a file may
        end in, which is not passed on.

        PluginThreadError on macOS when this is not the process's main thread, before the plugin
        is called. PluginStateError when the text is anything but one JSON object, which the
        plugin could not read, the plugin not called; when pedalboard refuses the state, chained;
        when Vital answers it with its alert, the alert's words in the reason, the plugin then
        holding the text in part; and when Vital ignores it, which the marker shows, the plugin
        then as it was. On every platform but macOS no alert is answered, and a text Vital cannot
        read may not return: nothing was probed there.

        The marker (`MARKER`) is set before the write to an end of its range the text does not
        hold. However the write ends, an error from outside the package among the ways, where it
        left the marker as planted the marker is set back to the value it had, and the write's
        own error leaves as itself. Where the map is not this plugin's no marker is set and the
        load is not checked.
        """
        self._on_a_writing_thread()
        body = text.removesuffix(b"\n")
        loaded = wrap(self._containers.with_text(body))
        marker = self._marker()
        if marker is None:
            self._write(loaded)
            return
        hosted, record = marker
        planted = _planted(record, body)
        with _reached(PluginStateError):
            before = hosted.raw_value
        with _reached(PluginStateError):
            hosted.raw_value = planted
        try:
            self._write(loaded)
        except BaseException as error:
            self._set_back(hosted, planted, before, error)
            raise
        if self._unplanted(hosted, planted, before):
            msg = f"Vital ignored the state: {MARKER}, set before the load, was left as it was set"
            raise PluginStateError(msg)

    def render(self, midi: Midi, samples: int, sample_rate: int) -> NDArray[np.float32]:
        """Render `samples` samples of the plugin playing `midi`, as `(2, samples)` float32.

        The plugin is reset first. One sample more is asked for, pedalboard truncating a duration
        to whole samples, and the first `samples` are returned. PluginRenderError when the length
        or the rate is not a positive whole number, a bool included, when the plugin refuses the
        render, chained, or when the host gives fewer samples or another shape.
        """
        samples, sample_rate = _whole(samples, "length"), _whole(sample_rate, "rate")
        if samples < 1 or sample_rate < 1:
            msg = f"a render is a positive length at a positive rate: {samples} at {sample_rate}"
            raise PluginRenderError(msg)
        with _reached(PluginRenderError):
            audio = self._plugin.process(list(midi), (samples + 1) / sample_rate, sample_rate)
        if audio.ndim != _AXES or audio.shape[0] != _CHANNELS or audio.shape[1] < samples:
            msg = f"asked for {samples} samples in {_CHANNELS} channels, given {audio.shape}"
            raise PluginRenderError(msg)
        return np.ascontiguousarray(audio[:, :samples])

    def display_texts(self, host_id: str, points: Sequence[float]) -> tuple[str, ...]:
        """Return what the plugin shows for a parameter at each normalized value, for the census.

        The parameter is pedalboard's `host_id`, the map unused; UnknownParameterError, naming it,
        for one the plugin does not host.
        """
        try:
            hosted = self._hosted[host_id]
        except KeyError:
            raise UnknownParameterError(host_id, INSTRUMENT) from None
        return tuple(_text_for(hosted, point) for point in points)

    def measure(self, grid: Sequence[float]) -> tuple[HostMeasurement, ...]:
        """Measure every hosted parameter at each normalized value of `grid`, for the census.

        Each parameter is set to each value and the state read: the one preset value that moves
        is the parameter's, by its key. After its grid each parameter is set back to the
        normalized value it had, however its reads end, so the next is measured from the state
        measured from; that is exact but for a float32 step on 22 of Vital 1.6.4's 903 (the
        revision after PR 9's third review, `verification/restore-probe.txt`). Once every
        parameter is measured, or a read fails, the state measured from is loaded once, which
        puts those back exactly and, as every load does, delays the embedded sample by 4 samples.
        A put-back or a load the plugin refuses is PluginStateError, an earlier failure kept in
        its context chain. Each call into the plugin is its own guard, so the text is parsed
        between them in the process's own environment. CensusError names a parameter that moves
        no preset value, or more than one, or changes which keys the preset holds;
        PluginStateError a state holding no settings object. PluginThreadError on macOS when
        this is not the process's main thread, before any parameter is set: the measurement ends
        on a state write.
        """
        self._on_a_writing_thread()
        start = self.preset_data()
        defaults = _floats(unwrap(start).text)
        measured = []
        try:
            for host_id, hosted in self._hosted.items():
                label = _name_of(hosted)
                with _reached(PluginStateError):
                    original = hosted.raw_value
                rows: list[dict[str, float]] = []
                try:
                    for point in grid:
                        with _reached(PluginStateError):
                            hosted.raw_value = point
                        rows.append(_floats(self.state()))
                finally:
                    with _reached(PluginStateError):
                        hosted.raw_value = original
                key = _moving_key(label, defaults, rows)
                measured.append(
                    HostMeasurement(
                        host_id=host_id,
                        label=label,
                        preset_key=PresetKey(key),
                        preset_default=defaults[key],
                        presets=tuple(row[key] for row in rows),
                        texts=self.display_texts(host_id, grid),
                    )
                )
        finally:
            self._write(start)
        return tuple(measured)


def _settings(text: bytes) -> object:
    """Return what a preset's text holds under `settings`, None where it is no object holding it.

    Read through the package's one guarded decoder, `preset.decoded`: a text that nests too
    deeply is PluginStateError, chained, and no `RecursionError` leaves. It is guarded though the
    state's validator reads every text first today, because the preset-file standard has one
    decoder helper and the margin between the two decoders' limits is measured, not promised
    (the review of PR 26, finding 13, `verification/costs.txt`).
    """
    try:
        value, _ = decoded(text.decode("utf-8"), "the state's text")
    except ValueError as error:
        raise PluginStateError(str(error)) from error
    return value.get("settings") if isinstance(value, dict) else None


def _alert_said(alert: Alert) -> str:
    """Say what an answered alert was: its two texts, or that they could not be read."""
    if alert.unread is None:
        return f"Vital answered the state with its alert, {alert.message!r}: {alert.informative!r}"
    unread = f"{type(alert.unread).__name__}: {alert.unread}"
    return f"Vital answered the state with an alert, and its words could not be read ({unread})"


def _floats(text: bytes) -> dict[str, float]:
    """Return the float settings of a preset's text, by key, read through `_settings`.

    PluginStateError when the text holds no `settings` object, or nests too deeply to read.
    """
    settings = _settings(text)
    if not isinstance(settings, dict):
        msg = "the state holds no settings object"
        raise PluginStateError(msg)
    return {key: value for key, value in settings.items() if isinstance(value, float)}
