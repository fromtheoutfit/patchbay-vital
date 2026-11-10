"""Vital hosted through pedalboard: the only module importing it, the seam another host replaces.

pedalboard is GPLv3 and this package MIT, so pedalboard comes only with the `host` extra
(`pip install patchbay-vital[host]`), the root package never imports this module, and nothing here
is copied from pedalboard (the host spec's shape.md, Decision 2).

`VitalHost` owns one plugin and speaks plain values, never patchbay's models: a parameter by its
`ParameterId`, which is its preset key, and its normalized value in `[0, 1]`; the plugin's state as
the preset text it holds; a render as an array. pedalboard knows a parameter by another key, the
map's `host_id`, which only this module reads. The plugin is found at the path given, or at
`DEFAULT_PATH`, Vital's macOS install, and nowhere else: there is no search.

What the probes found the plugin does (`verification/probes.txt` and `verification/host-probes.txt`
of the host spec): a state load upgrades an older preset, delays the embedded sample by 4 samples
and re-quantizes it, a 16-bit value moving by up to one step, and may snap a value off the host's
grid; a render that starts from a reset opens with a decaying transient (peak 0.022, under 1e-5 by
50 ms); a MIDI event's time is seconds from the render's start; and pedalboard returns
`int(duration * rate)` samples, so a render asks for half a sample more. pedalboard's own parameter
objects are reached through its public mapping on every access: one held across state loads
crashed the process (`verification/probes-first-attempt.txt`).

Loading Vital, and rendering it, turn on flush-to-zero for the whole process and leave it on, so
every subnormal result after them, in Python, numpy or `patchbay_vital.float32`, becomes zero
(`verification/float-environment.txt`). Every call into the plugin here saves the floating-point
environment before and restores it after, with the C library's `fegetenv` and `fesetenv`; the
plugin's own processing still runs under the environment it sets for itself.
"""

import ctypes
import ctypes.util
import importlib.metadata
import json
import math
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple, Protocol, cast

import numpy as np
import pedalboard
from numpy.typing import NDArray
from patchbay import ParameterId, PresetKey

from patchbay_vital.errors import (
    CensusError,
    ParameterRangeError,
    PluginLoadError,
    PluginRenderError,
    UnknownParameterError,
)
from patchbay_vital.parameters import ParameterMap, parameter_map
from patchbay_vital.state import unwrap, wrap

DEFAULT_PATH = Path("/Library/Audio/Plug-Ins/VST3/Vital.vst3")
"""Where Vital's installer puts the VST3 on macOS; the only place looked at without a path given."""

INSTRUMENT = "Vital"
"""The plugin's name, as it reports it; a plugin at the path by another name is refused."""

type Midi = Sequence[tuple[bytes, float]]
"""MIDI as pedalboard takes it: each message's bytes and its time in seconds from the start."""

_CHANNELS = 2

_ENVIRONMENT_BYTES = 512
"""Room for any platform's `fenv_t`, which is saved and restored whole, its layout never read."""


def _c_library() -> ctypes.CDLL | None:
    """Return the C library that holds `fegetenv` and `fesetenv`, or None where there is none."""
    for name in (ctypes.util.find_library("c"), "ucrtbase"):
        if name is None:
            continue
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    return None


_LIBC = _c_library()


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


class VitalHost:
    """One Vital through pedalboard: set and read in normalized values, rendered from MIDI."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Load the plugin at `path`, or at `DEFAULT_PATH` when none is given.

        PluginLoadError when there is nothing at the path, the host cannot load what is there, or
        what it loads is not Vital.
        """
        where = Path(DEFAULT_PATH if path is None else path)
        if not where.exists():
            raise PluginLoadError(str(where), "there is nothing at the path")
        if _LIBC is None:
            msg = "no C library to keep the floating-point environment the plugin changes"
            raise PluginLoadError(str(where), msg)
        try:
            with _environment_kept():
                plugin = cast("_HostedPlugin", pedalboard.VST3Plugin(str(where)))
                hosted = plugin.parameters
        except (ImportError, RuntimeError, ValueError, OSError) as error:
            raise PluginLoadError(str(where), str(error) or type(error).__name__) from error
        if plugin.name != INSTRUMENT:
            raise PluginLoadError(str(where), f"the plugin there is {plugin.name!r}")
        self._plugin = plugin
        self._hosted = hosted
        self._map: ParameterMap | None = None

    @property
    def name(self) -> str:
        """The plugin's name, as it reports it."""
        return self._plugin.name

    @property
    def version(self) -> str:
        """The plugin's version, as it reports it."""
        return self._plugin.version

    @property
    def host(self) -> str:
        """The host this is, by name and version: what a map measured through it records."""
        return f"pedalboard {importlib.metadata.version('pedalboard')}"

    def _parameter_map(self) -> ParameterMap:
        if self._map is None:
            self._map = parameter_map()
        return self._map

    def _hosted_parameter(self, parameter_id: ParameterId) -> _HostedParameter:
        """Return pedalboard's parameter for an id; UnknownParameterError for an id not hosted."""
        record = self._parameter_map().find(parameter_id)
        try:
            return self._hosted[record.host_id]
        except KeyError:
            raise UnknownParameterError(parameter_id, INSTRUMENT) from None

    def parameter_ids(self) -> tuple[ParameterId, ...]:
        """Every hosted parameter's id the map knows, in the host's order."""
        by_host = {record.host_id: record.id for record in self._parameter_map().parameters}
        return tuple(by_host[host_id] for host_id in self._hosted if host_id in by_host)

    def unmapped_parameters(self) -> tuple[str, ...]:
        """Return the labels of hosted parameters the map has no record of, in the host's order."""
        mapped = {record.host_id for record in self._parameter_map().parameters}
        return tuple(hosted.name for key, hosted in self._hosted.items() if key not in mapped)

    def get(self, parameter_id: ParameterId) -> float:
        """Return a parameter's normalized value; UnknownParameterError for an id not hosted."""
        return float(self._hosted_parameter(parameter_id).raw_value)

    def set(self, parameter_id: ParameterId, normalized: float) -> None:
        """Set a parameter's normalized value.

        UnknownParameterError for an id not hosted, ParameterRangeError for a value outside
        `[0, 1]`; neither changes anything.
        """
        hosted = self._hosted_parameter(parameter_id)
        if not (math.isfinite(normalized) and 0.0 <= normalized <= 1.0):
            raise ParameterRangeError(parameter_id, 0.0, 1.0, normalized)
        with _environment_kept():
            hosted.raw_value = normalized

    def preset_data(self) -> bytes:
        """Return the plugin's state as the VST3 preset bytes it gives the host, every container."""
        return self._plugin.preset_data

    def state(self) -> bytes:
        """Return the preset text the plugin holds: a `.vital` file's, with its `tuning`."""
        return unwrap(self._plugin.preset_data).text

    def load_state(self, text: bytes) -> None:
        """Load a preset's text into the plugin, every container around it the plugin's own.

        The text is a `.vital` file's or `state`'s: one JSON object, and the one newline a file may
        end in, which is not passed on. PluginStateError when it is anything else, which the plugin
        could not read; the plugin is then unchanged.
        """
        current = unwrap(self._plugin.preset_data)
        loaded = wrap(current.with_text(text.removesuffix(b"\n")))
        with _environment_kept():
            self._plugin.preset_data = loaded

    def render(self, midi: Midi, samples: int, sample_rate: int) -> NDArray[np.float32]:
        """Render `samples` samples of the plugin playing `midi`, as `(2, samples)` float32.

        The plugin is reset first. PluginRenderError when the length or the rate is not a
        positive whole number, or the host gives another length.
        """
        if samples < 1 or sample_rate < 1:
            msg = f"a render is a positive length at a positive rate: {samples} at {sample_rate}"
            raise PluginRenderError(msg)
        with _environment_kept():
            audio = self._plugin.process(list(midi), (samples + 0.5) / sample_rate, sample_rate)
        if audio.shape != (_CHANNELS, samples):
            msg = f"asked for {samples} samples in {_CHANNELS} channels, given {audio.shape}"
            raise PluginRenderError(msg)
        return audio

    def display_texts(self, host_id: str, points: Sequence[float]) -> tuple[str, ...]:
        """Return what the plugin shows for a parameter at each normalized value, for the census."""
        hosted = self._hosted[host_id]
        return tuple(hosted.get_text_for_raw_value(point) for point in points)

    def measure(self, grid: Sequence[float]) -> tuple[HostMeasurement, ...]:
        """Measure every hosted parameter at each normalized value of `grid`, for the census.

        Each parameter is set to each value and the state read: the one preset value that moves
        is the parameter's, by its key. The plugin's state is restored after each. CensusError
        names a parameter that moves no preset value, or more than one.
        """
        start = self._plugin.preset_data
        defaults = _floats(unwrap(start).text)
        measured = []
        for host_id, hosted in self._hosted.items():
            label = hosted.name
            rows = []
            with _environment_kept():
                for point in grid:
                    hosted.raw_value = point
                    rows.append(_floats(self.state()))
                self._plugin.preset_data = start
            moving = [key for key in defaults if len({row[key] for row in rows}) > 1]
            if len(moving) != 1:
                raise CensusError(label, f"moves {len(moving)} preset values: {moving[:4]}")
            (key,) = moving
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
        return tuple(measured)


def _floats(text: bytes) -> dict[str, float]:
    """Return the float settings of a preset's text, by key."""
    settings = json.loads(text)["settings"]
    return {key: value for key, value in settings.items() if isinstance(value, float)}
