"""MIDI for a render, built from a pattern: each note's on and its off, as bytes at a time.

`midi_of` gives what `VitalHost.render` takes: pairs of a message's bytes and its time in seconds
from the render's start. It needs no plugin and no MIDI library: a note-on and a note-off are
three bytes each.

**The bytes are core's `Note` as it is,** but for the channel of a note whose pitch already sounds
on its own. A note-on is `0x90 | channel`, the pitch, the velocity; a note-off is
`0x80 | channel`, the pitch, 0. Core's `Note` already holds MIDI's own integers, a pitch from 0 to
127, a velocity from 1 to 127 and a channel from 0 to 15, so nothing is scaled or rounded here,
every note has a channel, and no note-on carries velocity 0, which most receivers read as a
note-off. A unit test holds that core refuses a velocity of 0, so a change there is seen.

**Each note sounds for its own length, as core's reference instrument sums a sine per note.** On
one channel Vital voices two notes of one pitch, but the first note-off releases both: of two
overlapping, the later stops where the earlier ends, and of two struck on one sample both stop at
the first end, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2;
this revision's spec, `verification/overlap-probe.txt`). On another channel each note keeps its
own length and its own velocity, and a note alone sounds the same on any channel, with Vital's
MPE setting off and on (`overlap-probe-2.txt`). So a note keeps its own channel unless its pitch
is already sounding there; then it goes out, its note-on and its note-off, on the lowest channel
where that pitch is not sounding. Of two notes of one pitch struck on one sample, the first in the
pattern keeps its channel and the second moves. A pitch is sounding on a channel from its note-on
to its note-off, so one released on the sample another is struck on is free again. Sixteen notes
of one pitch can sound at once; a seventeenth is RenderRefusedError, naming the pitch and the
sample, since Vital has no channel left to give it its own length.

**The samples are core's.** A note starts on `RenderRequest.sample_at(pattern, start_beats)` and
ends on `sample_at(pattern, start_beats + duration_beats)`, the sum as core's reference instrument
computes it, in a render of `RenderRequest.samples(pattern)` samples. As that reference does at
the render's end: a note that starts at or past the render's length is left out whole, and a
note-off at or past the length is left out, the render ending before it. The host resets the
plugin before each render, so a note left sounding is not heard in the next (the instrument
spec's `verification/probes.txt`).

**A time is half a sample past its sample.** pedalboard places an event by its time in seconds,
and the time of sample n itself, n over the rate, lands one sample early on some n: at 100,003,
1,000,003 and 4,000,001 at 48 kHz, and on 4 of 120 drawn. Half a sample past, `(n + 0.5) / rate`,
landed on n at every value tried, those and three past 12 million among them, as the host asks a
render for one sample more than it wants. A sample, not a count: no rule for where pedalboard
rounds was found that the measurements bear out (the same transcript).

**On one sample the order is fixed:** the note-offs of notes that began earlier, then the
note-ons, then the note-off of a note that begins and ends on that sample, each group in the
pattern's order. So a pitch repeated without a gap is released before it is struck again, on its
own channel, and a note too short to last a sample is still released after it is struck.
"""

import math

from patchbay import Pattern, RenderRequest

from patchbay_vital.errors import RenderRefusedError

NOTE_ON = 0x90
"""A note-on's status byte, less its channel."""

NOTE_OFF = 0x80
"""A note-off's status byte, less its channel."""

CHANNELS = 16
"""How many MIDI channels there are, and so how many notes of one pitch can sound at once."""

_BEFORE, _ON, _AFTER = 0, 1, 2
"""On one sample: the offs of earlier notes, the ons, the off of a note that also began there."""


def midi_of(pattern: Pattern, request: RenderRequest) -> tuple[tuple[bytes, float], ...]:
    """Return the pattern's notes as MIDI for a render the request asks for, in time order.

    Each pair is a message's three bytes and its time in seconds from the render's start, half a
    sample past the sample it belongs on. A note that starts at or past the render's length gives
    nothing, and one that ends there gives its note-on alone. A note whose pitch is already
    sounding on its channel goes out on the lowest channel where it is not; RenderRefusedError,
    naming the pitch and the sample, for a note of a pitch sounding on all sixteen.
    """
    length = request.samples(pattern)
    struck: list[tuple[int, int, int, int]] = []
    for index, note in enumerate(pattern.notes):
        start = request.sample_at(pattern, note.start_beats)
        end = request.sample_at(pattern, note.start_beats + note.duration_beats)
        if start < length:
            struck.append((start, index, end, note.pitch))
    struck.sort()
    sounding: list[tuple[int, float, int, int]] = []  # start, end (inf with no off), pitch, channel
    events: list[tuple[int, int, int, bytes]] = []
    for start, index, end, pitch in struck:
        note = pattern.notes[index]
        sounding = [held for held in sounding if not (held[1] <= start and held[0] < start)]
        busy = {channel for _, _, held_pitch, channel in sounding if held_pitch == pitch}
        channel = _free_channel(note.channel, busy, pitch, start)
        sounding.append((start, end if end < length else math.inf, pitch, channel))
        events.append((start, _ON, index, bytes([NOTE_ON | channel, pitch, note.velocity])))
        if end < length:
            rank = _BEFORE if end > start else _AFTER
            events.append((end, rank, index, bytes([NOTE_OFF | channel, pitch, 0])))
    events.sort(key=lambda event: event[:3])
    doubled = 2 * request.sample_rate
    return tuple((message, (2 * sample + 1) / doubled) for sample, _, _, message in events)


def _free_channel(own: int, busy: set[int], pitch: int, sample: int) -> int:
    """Return a note's own channel if its pitch is not sounding there, else the lowest it is not."""
    if own not in busy:
        return own
    free = [channel for channel in range(CHANNELS) if channel not in busy]
    if not free:
        msg = (
            f"pitch {pitch} is already sounding on all {CHANNELS} MIDI channels at sample "
            f"{sample}, so a note struck there cannot sound for its own length"
        )
        raise RenderRefusedError(msg)
    return free[0]
