"""Vital as a `patchbay.Instrument`: parameters in the units it displays, patches, renders, events.

`VitalInstrument` implements core's protocol over `VitalHost`, the one way it reaches the plugin,
and needs the `host` extra. It is built from the bus it publishes on, as core's reference
instrument is, and registered under `vital` in the `patchbay.instruments` entry-point group, which
is provisional until core says what that group holds.

**The model is the source of truth.** The instrument holds a `VitalPreset` and every answer comes
from it: `get` reads it, `patch` carries it (`patchbay_vital.patch`), `set` writes through to it
and to the plugin, `load_patch` replaces it and sends its text to the plugin. The plugin's state
never becomes the model, not even at the start: the instrument starts on the preset the package
ships (`patchbay_vital.start`), loaded into the plugin as it is built, so it does not start on
Vital's own initial sound. What the plugin holds is read only to check it, through `host`.

**What a set holds.** A value its parameter takes (`Parameter.check`, the bounds the map's) is
taken to the preset value Vital holds for it, the map's `MappedParameter.to_preset`, and that is
what `get` then returns and `ParameterChanged.new` carries: the value given itself at a bound and
at any value a set has left the parameter holding, and otherwise a value near it that need not be
the nearest one held. A value between the steps of a stepped parameter is taken and the nearest
step held, a half away from zero: `chorus_voices` given 6 holds 8. A set of the value the
parameter already shows, where the model holds a float no set lands on, changes nothing, in the
model or the plugin, and is still published: a set of that float's own display would otherwise
move it. Any other set reaches the plugin, one of the value shown on a float a set does land on
among them, so the plugin is set to what the model holds.

**When the plugin does not take a load and then does not take the model's own text either,**
refusing it, answering it with its alert or ignoring it, its state is unknown and the model
still holds the preset before: the instrument has lost step with it.
`load_patch` raises `PluginStateError` saying so, and from then on `set`, `load_patch` and
`render` are refused with that error, the plugin not called and nothing published, while `get`,
`patch` and `parameters` answer from a model the plugin no longer matches. Build a new
instrument. **The same is so when a load is cut off by an error from outside the package,** a
`KeyboardInterrupt` or a `MemoryError` among them, once a text is being sent: the plugin may hold
part of it, the error leaves as itself, and no rollback is tried (the review of PR 26, finding 1).

**A patch Vital cannot use** (issue #20 and the revision after the review of PR 26; their
specs' `verification/` hold the counts). Each was measured on Vital 1.6.4 through pedalboard
0.9.26 on arm64, macOS 26.6.2, and nothing was probed on any other platform, nor in a process with
no screen. Vital reports none. Given a text it cannot read it puts up a modal alert and never
returns to its caller; a text newer than itself it ignores without a word; and some texts kill
the process inside Vital's own reading of them. What the instrument does about each:

- **The alert.** On macOS the host answers it before it opens, and `load_patch` refuses the
  patch: `PatchRefusedError`, with Vital's own words, the model's text loaded again. The patch
  was taken in part by then, so the plugin is put back, not left alone. On any other platform
  nothing answers the alert, so such a patch may block the calling process there.
- **A load from a thread that is not the process's main one,** on macOS: `PatchRefusedError`,
  core's `PatchRejectedError`, chained from the host's `PluginThreadError`, the plugin not called
  and nothing changed. The alert cannot open there, and the process was seen to die at its next
  render.
- **A load Vital ignores.** A preset newer than the plugin, the one kind seen ignored whole,
  `check_loadable` refuses before Vital is given it. Behind that the host sets a marker on the
  plugin before each load and reads it after; one that was left is refused the same way as an
  alert. The marker is the plugin's alone: `get`, `patch` and the bus never show it.
- **A text Vital dies on kills the calling process** (issue #25). Three shapes were found, each
  a section one entry longer than Vital holds, and `check_loadable` refuses those. Only the
  shapes found are refused: no text was tried with two faults, or with a fault past an array's
  first entry.
- **A text Vital loads in part is not detected** (issue #25). Where it keeps a wavetable or a
  sample it had, or makes something else of the one given, nothing read back from the plugin
  tells.

**Known limits, each measured** on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (the
instrument spec's `verification/probes.txt` and `probes-2.txt`), each the hosted plugin's. The
first two each wait on an issue of their own, which come before the first experiment that puts
an agent in front of the instrument, in this order; the third is a workaround no issue owns:

- Issue #21. A render of most presets opens with the preset sounding though no note was played.
  On the start preset that is a transient of about 0.02 of full scale, over in about 100 ms; on
  presets Vital installs it reaches full scale and can last seconds. The clipping warning counts
  it.
- Issue #22. On a preset older than the plugin, a few parameters can be reported by `get` with
  the file's value where Vital plays its upgraded one, and for a choice that can be a different
  setting by name. Vital upgrades such a preset as it loads: of the 75 presets it installs, 11
  hold 46 such floats, `osc_1_stack_style` 9 played as 10 and `filter_1_style` 1 played as 0
  among them. The model keeps the file's floats. A set of the value `get` shows puts Vital on
  the model's float for 42 of the 46, counted on Vital (the `verification/upgraded-set-count.txt`
  of the revision after PR 23's second review). It is refused for 3, `flanger_center` on Touch
  Tone, Memory Leak and Oolacile Evil Dubstep Bass, whose file value shows a display outside the
  parameter's bounds. It is kept for 1, `modulation_10_amount` on Oolacile Evil Dubstep Bass,
  a float no set lands on: Vital goes on playing 0.07499999552965164 where `get` shows
  0.19999998807907104, and no set can put it on the model's float.
- A load is made twice, a measured workaround with no known cause and no issue of its own. One
  load leaves 17 to 53 of a preset's 903 floats off the text's; a second load of the same text
  holds them, all but what the upgrade above changes, and a third changes nothing more.
"""

import time
import uuid
from typing import NoReturn

import numpy as np
from numpy.typing import NDArray
from patchbay import (
    EventBus,
    Parameter,
    ParameterChanged,
    ParameterId,
    Patch,
    PatchLoaded,
    Pattern,
    Quantity,
    RenderCompleted,
    RenderRequest,
    RenderResult,
)

from patchbay_vital.errors import (
    PatchRefusedError,
    PluginRenderError,
    PluginStateError,
    PluginThreadError,
    RenderRefusedError,
    VitalError,
)
from patchbay_vital.format import dumps, writes_same
from patchbay_vital.host import VitalHost
from patchbay_vital.midi import midi_of
from patchbay_vital.parameters import MappedParameter, parameter_map
from patchbay_vital.patch import check_loadable, check_value, patch_of, preset_of
from patchbay_vital.preset import VitalPreset, VitalSettings, slot_place
from patchbay_vital.start import start_preset

MAX_SAMPLES = 2**24
"""The longest render the instrument makes, in samples: 5.8 minutes at 48 kHz, 128 MiB of stereo
float32. Vital 1.6.4 gave exactly this many, every sample finite, in 1.3 s (the instrument spec's
`verification/probes.txt`); core's reference instrument declares the same figure."""

MIN_SAMPLE_RATE = 1_000
MAX_SAMPLE_RATE = 768_000
"""The sample rates the instrument renders at, in Hz: the range the host spec measured, every
rate in it giving the length asked for, finite (its `verification/probes.txt`). A rate outside it
has not been rendered, so it is refused."""

FULL_SCALE = 1.0
"""The magnitude a sample reaches when the render clips. Vital gives samples past it, up to 2.1,
and none held at it (the instrument spec's `verification/probes.txt`), so the audio returned is
never clipped here: a render that reaches it carries a warning."""

LOADS = 2
"""How many times a text is sent to the plugin for one load: a measured workaround, no cause
known. On Vital 1.6.4 through pedalboard 0.9.26 on arm64, after a set, one load leaves floats the
scale does not hold a float32 step or two from the text's, and a second load of the same text
holds them as given (the instrument spec's `verification/probes.txt`)."""

_CHANNELS = 2


def _text_of(preset: VitalPreset) -> bytes:
    """Return the text the plugin is sent for a preset, as the package writes it."""
    return dumps(preset).encode("utf-8")


def _clipping(audio: NDArray[np.float32], sample_rate: int) -> tuple[str, ...]:
    """Return the one warning a render that reaches full scale carries, or none.

    The warning says what was measured: the peak, as a multiple of full scale, the first sample
    at or past full scale and its time, and how many samples are.
    """
    if audio.shape[1] == 0:
        return ()
    peaks = np.maximum(audio.max(axis=0), -audio.min(axis=0))
    peak = float(peaks.max())
    if peak < FULL_SCALE:
        return ()
    past = np.nonzero(peaks >= FULL_SCALE)[0]
    first = int(past[0])
    warning = (
        f"clipped: the render peaks at {peak:.3f} of full scale; {past.size} of its "
        f"{audio.shape[1]} samples are at or past it, the first at sample {first} "
        f"({first / sample_rate:.3f} s)"
    )
    return (warning,)


class VitalInstrument:
    """Vital, driven through core's `Instrument` protocol and publishing on the bus it is given."""

    def __init__(self, bus: EventBus, host: VitalHost | None = None) -> None:
        """Start on the package's start preset, loaded into the plugin; nothing is published.

        `host` is a loaded Vital to drive, for a plugin somewhere other than the host's default
        path; without one the instrument loads Vital there itself. Whatever the plugin held is
        replaced. PluginLoadError when no Vital loads, MapMismatchError when the parameter map was
        measured on another machine or from another Vital, PluginStateError when the plugin
        refuses the start preset, PluginThreadError on macOS when this is not the process's main
        thread.
        """
        self._bus = bus
        self._host = VitalHost() if host is None else host
        self._host.parameter_ids()
        self._map = parameter_map()
        self._parameters = tuple(record.parameter for record in self._map.parameters)
        self._preset = start_preset()
        self._patch: Patch | None = None
        self._lost: str | None = None
        self._sent(_text_of(self._preset))

    @property
    def name(self) -> str:
        """Always "Vital", the plugin's own name and the one a patch names."""
        return self._map.instrument

    @property
    def host(self) -> VitalHost:
        """The hosted plugin, for the diagnostic read: what the plugin itself holds.

        `host.state()` is the plugin's own view, which its loads and its own rounding move away
        from what it was given. Nothing here reads it as the instrument's state; tests read it to
        hold the plugin to the model.
        """
        return self._host

    @property
    def preset(self) -> VitalPreset:
        """The model: the preset the instrument holds, which `patch` carries."""
        return self._preset

    def parameters(self) -> tuple[Parameter, ...]:
        """Return all 903 parameters the plugin hosts, in the map's order, sorted by id."""
        return self._parameters

    def get(self, parameter_id: ParameterId, /) -> Quantity:
        """Return the value the parameter holds, in the unit Vital displays.

        The display of the model's float, or of the parameter's default where the preset lacks
        its key. A loaded preset can hold a float outside the parameter's bounds, and its true
        display is returned, though `set` would refuse it. UnknownParameterError, core's
        ParameterNotFoundError too, when there is no such id. After the instrument has lost step
        with the plugin (`load_patch`), it still answers from the model, which the plugin no
        longer matches.
        """
        record = self._map.find(parameter_id)
        return Quantity(value=record.to_display(self._held(record)), unit=record.parameter.unit)

    def set(self, parameter_id: ParameterId, value: Quantity, /) -> None:
        """Set the parameter in the model and the plugin, then publish ParameterChanged.

        The parameter then holds the value Vital holds for the display given, which `get`
        returns and the event's `new` carries, and which need not be the held value nearest it.
        A bound is held exactly. A value between the steps of a stepped parameter is taken and
        the nearest step held. A set of the value the parameter already shows, where it holds a
        float no set lands on, keeps that float, in the model and the plugin, and is published
        all the same, `old` equal to `new`; a set of the value shown on any other float sets the
        plugin to it. So where Vital upgraded a preset's float as it loaded (issue #22), a set
        of the value shown puts Vital on the model's float only where that is one a set lands
        on: a kept float leaves Vital on its upgraded one.

        UnknownParameterError for an id the instrument does not have, ParameterUnitError for a
        value in another unit, ParameterRangeError for one outside the parameter's bounds or, on
        a choice or a boolean, not a whole number: core's ParameterNotFoundError,
        UnitMismatchError and ValueOutOfRangeError too, each changing nothing and publishing
        nothing. When the plugin refuses the value after those checks pass, the host's
        PluginStateError, a VitalError, leaves the call with the model unchanged and nothing
        published. Once the instrument has lost step with the plugin (`load_patch`), every set
        is refused with PluginStateError before anything else, naming the earlier failure: build
        a new instrument.
        """
        self._refuse_once_lost()
        record = self._map.find(parameter_id)
        check_value(record.parameter, value)
        old = self.get(parameter_id)
        held = record.to_preset(value.value)
        if value.value != old.value or writes_same(held, self._held(record)):
            self._host.set(parameter_id, record.scale.to_normalized(held))
            self._hold(self._holding(record, held))
        self._bus.publish(
            ParameterChanged(
                source=self.name,
                correlation_id=uuid.uuid4().hex,
                id=parameter_id,
                old=old,
                new=self.get(parameter_id),
            )
        )

    def load_patch(self, patch: Patch, /) -> None:
        """Load the patch whole into the model and the plugin, then publish PatchLoaded.

        A patch with a `preset` entry is a whole preset, as `patch` gives one. A patch of values
        alone, its `opaque` empty, is the start preset with those values: its sections, routing
        and metadata, and every parameter the patch does not name at the start's value. Each
        value is taken to a float one way (`patchbay_vital.patch`): the float its display names,
        where the curve's float32 for it shows exactly that display, and otherwise the float a
        set of it holds, on a stepped parameter the nearest step. So the patch `patch` then
        returns can differ from the one given, where a value named no float, and loads back
        unchanged.

        `PatchLoaded.parameter_count` is the number of entries in the patch's `values` as given:
        every parameter the preset holds for a whole patch, less any whose float rides in
        `opaque`, and only the values named for a patch of values alone.

        PatchRefusedError, core's PatchRejectedError too, for a patch the instrument does not
        load, naming the first entry to refuse and chained from what refused it
        (`patchbay_vital.patch`), and for a preset the plugin was seen not to load whole
        (`check_loadable`); nothing is then changed or published. When the plugin refuses the
        text after those checks pass, the model's own text is sent to it again and the same
        error leaves the call, chained from the host's. That is so when pedalboard refuses it,
        when Vital answers it with its alert, which the host answers on macOS, the reason then
        carrying the alert's words, and when Vital ignores it, which the host's marker shows.
        After an alert the plugin had taken the patch in part, and the model's text puts it back.

        Each of these was measured on macOS 26.6.2 alone. On any other platform no alert is
        answered, and nothing was probed there: a patch with a section Vital cannot read inside
        may block the calling process there. A patch Vital dies on was seen to kill the calling
        process, but for the shapes `check_loadable` refuses. A patch Vital loads in part,
        keeping sections it had, is not detected. Both are issue #25's.

        PatchRefusedError, core's PatchRejectedError too, chained from the host's
        PluginThreadError, on macOS when this is not the process's main thread. Its reason says,
        in this order, that the call came from a thread the plugin cannot be loaded from,
        naming it; that the patch passed the package's own checks, which come first, so a patch
        they refuse is refused for their reason from any thread; and that it was not given to
        Vital, so whether Vital takes it is unknown. The plugin is not called, nothing is changed
        or published, and the instrument has not lost step (the review of PR 26, finding 3).

        Should the plugin refuse the model's own text too, its state is unknown and the model
        holds the preset before: the instrument has lost step with the plugin. PluginStateError,
        a VitalError and not core's PatchRejectedError, leaves the call naming both refusals,
        chained from the second, and nothing is published. From then on `set`, `load_patch` and
        `render` are refused with PluginStateError naming that failure, the plugin not called
        and nothing published, and `get` and `patch` answer from the model: build a new
        instrument. So too when an error from outside the package, a KeyboardInterrupt or a
        MemoryError among them, leaves while the text is being sent, or while the model's own
        text is sent again: the plugin may hold part of a text, so the instrument loses step,
        no rollback is tried, and that error leaves as itself, the same object. An error raised
        before the text is sent, by the checks or the host's thread rule, changes nothing and
        loses no step.

        A preset older than the plugin loads, and Vital upgrades it as it does: the model keeps
        the file's floats, so `get` can then report the file's value for a few parameters where
        Vital plays another, which for a choice is another setting by name. A set of the value
        `get` shows then puts Vital on the model's float, but where that value is outside the
        parameter's bounds, which is refused, or the float is one no set lands on, which is
        kept: 42, 3 and 1 of the 46 such floats on the presets Vital installs (the module's
        known limits).
        """
        self._refuse_once_lost()
        preset = preset_of(patch)
        check_loadable(preset, self._map)
        text = _text_of(preset)
        try:
            self._sent(text)
        except PluginThreadError as error:
            msg = (
                f"the call came from the thread {error.thread!r}, which the plugin cannot be "
                "loaded from on macOS; the patch passed the package's own checks; it was not "
                "given to Vital, so whether Vital takes it is unknown"
            )
            raise PatchRefusedError(msg) from error
        except PluginStateError as error:
            self._rolled_back(error)
        except VitalError:
            raise
        except BaseException as error:
            self._lose_step(error)
            raise
        self._hold(preset)
        self._bus.publish(
            PatchLoaded(
                source=self.name,
                correlation_id=uuid.uuid4().hex,
                instrument=self.name,
                parameter_count=len(patch.values),
            )
        )

    def patch(self) -> Patch:
        """Return the model as a patch, which `load_patch` takes back unchanged.

        `values` holds each parameter the preset has a float for, as the display that carries
        that float. A parameter whose stored value is outside its bounds, or one no display
        carries exactly, is absent from `values` and its float rides in `opaque`; `get` still
        returns its true display, and a set of a value in range brings it into `values` from
        then on. Every entry of `values` is one `set` takes, and names the float it carries
        (`patchbay_vital.patch`). The patch is built once for each model and the same object is
        returned until the model changes. After the instrument has lost step with the plugin
        (`load_patch`), it still carries the model, which the plugin no longer matches.
        """
        if self._patch is None:
            self._patch = patch_of(self._preset)
        return self._patch

    def render(self, pattern: Pattern, request: RenderRequest, /) -> RenderResult:
        """Render the pattern as the request asks, two channels, then publish RenderCompleted.

        The result is `request.samples(pattern)` samples long, each note sent as MIDI
        (`patchbay_vital.midi`), and `elapsed_seconds` is the wall-clock time of the whole call.
        A render of no samples is an empty result, the plugin not called. A render in which any
        sample is at or past full scale carries one warning saying the peak and where; the audio
        is as Vital gave it, never clipped here. Neither the model nor the plugin's settings
        change. Until the host's own spec lands, a render of most presets opens with the preset
        sounding though no note was played, and the warning counts that sound with the rest.

        RenderRefusedError, core's RenderFailedError too, publishing nothing: for a rate outside
        `MIN_SAMPLE_RATE` to `MAX_SAMPLE_RATE`, a render longer than `MAX_SAMPLES`, each naming
        the limit and its value; for a pattern with a note no MIDI channel can voice, naming its
        pitch and sample (`patchbay_vital.midi`); and for a render the plugin does not give or
        gives with a sample that is no finite number, chained from the host's error. Once the
        instrument has lost step with the plugin (`load_patch`), every render is refused with
        PluginStateError before anything else, naming the earlier failure: build a new
        instrument.
        """
        self._refuse_once_lost()
        started = time.perf_counter()
        rate = request.sample_rate
        if not MIN_SAMPLE_RATE <= rate <= MAX_SAMPLE_RATE:
            msg = (
                f"a rate of {rate} Hz is outside MIN_SAMPLE_RATE, {MIN_SAMPLE_RATE} Hz, to "
                f"MAX_SAMPLE_RATE, {MAX_SAMPLE_RATE} Hz"
            )
            raise RenderRefusedError(msg)
        samples = request.samples(pattern)
        if samples > MAX_SAMPLES:
            msg = f"a render of {samples} samples is past MAX_SAMPLES, {MAX_SAMPLES}"
            raise RenderRefusedError(msg)
        audio = self._rendered(pattern, request, samples)
        result = RenderResult(
            audio=audio,
            sample_rate=rate,
            elapsed_seconds=time.perf_counter() - started,
            warnings=_clipping(audio, rate),
        )
        self._bus.publish(
            RenderCompleted(
                source=self.name,
                correlation_id=uuid.uuid4().hex,
                instrument=self.name,
                elapsed_seconds=result.elapsed_seconds,
                audio_seconds=result.audio_seconds,
                warnings=result.warnings,
            )
        )
        return result

    def _rendered(
        self, pattern: Pattern, request: RenderRequest, samples: int
    ) -> NDArray[np.float32]:
        """Return the plugin's audio for a render within the limits, empty for no samples."""
        if samples == 0:
            return np.zeros((_CHANNELS, 0), dtype=np.float32)
        try:
            audio = self._host.render(midi_of(pattern, request), samples, request.sample_rate)
        except PluginRenderError as error:
            msg = f"the plugin gave no render: {error.reason}"
            raise RenderRefusedError(msg) from error
        if not np.isfinite(audio).all():
            msg = "the plugin gave a sample that is no finite number"
            raise RenderRefusedError(msg)
        return audio

    def _sent(self, text: bytes) -> None:
        """Send a preset's text to the plugin, `LOADS` times."""
        for _ in range(LOADS):
            self._host.load_state(text)

    def _rolled_back(self, error: PluginStateError) -> NoReturn:
        """Send the model's own text again after the plugin refused a load, then refuse the patch.

        PatchRefusedError, chained from `error`, when the plugin takes the model's text. When it
        refuses that too, or the rollback is cut off by any other error, the instrument has lost
        step: PluginStateError naming both refusals, chained from the second, or that other
        error as itself.
        """
        try:
            self._sent(_text_of(self._preset))
        except PluginStateError as again:
            self._lost = (
                f"the plugin refused a preset ({error.reason}) and then the model's own text "
                f"({again.reason}), so its state is unknown while the model holds the preset "
                "before"
            )
            msg = f"{self._lost}: build a new VitalInstrument"
            raise PluginStateError(msg) from again
        except BaseException as cut:
            self._lose_step(cut, f"while the model's own text was sent after: {error.reason}")
            raise
        msg = f"the plugin refused the preset: {error.reason}"
        raise PatchRefusedError(msg) from error

    def _lose_step(self, error: BaseException, during: str = "") -> None:
        """Mark the instrument out of step: an error from outside the package cut a load off.

        The plugin may then hold part of a text while the model holds the preset before; no
        rollback is tried, and the caller re-raises the error as itself (the review of PR 26,
        finding 1).
        """
        where = f" {during}" if during else ""
        self._lost = (
            f"a load was cut off by {type(error).__name__} ({error}){where}, so the plugin's "
            "state is unknown while the model holds the preset before"
        )

    def _refuse_once_lost(self) -> None:
        """Raise PluginStateError, naming the failure, once the instrument has lost step."""
        if self._lost is not None:
            msg = f"the instrument lost step with the plugin: {self._lost}; build a new one"
            raise PluginStateError(msg)

    def _hold(self, preset: VitalPreset) -> None:
        """Make a preset the model, dropping the patch built from the one before."""
        self._preset = preset
        self._patch = None

    def _held(self, record: MappedParameter) -> float:
        """Return the float the model holds for a parameter, its default where the key is absent."""
        place = slot_place(record.preset_key)
        if place is None:
            held = self._preset.settings.values.get(record.preset_key)
        else:
            slot, field = place
            held = getattr(self._preset.modulations[slot - 1], field)
        return record.preset_default if held is None else held

    def _holding(self, record: MappedParameter, held: float) -> VitalPreset:
        """Return the model with one parameter's float replaced, everything else the same object."""
        place = slot_place(record.preset_key)
        if place is None:
            values = {**self._preset.settings.values, record.preset_key: held}
            return self._preset.model_copy(update={"settings": VitalSettings(values=values)})
        slot, field = place
        modulations = list(self._preset.modulations)
        modulations[slot - 1] = modulations[slot - 1].model_copy(update={field: held})
        return self._preset.model_copy(update={"modulations": tuple(modulations)})
