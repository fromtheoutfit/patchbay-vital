"""A pattern's notes become note-ons and note-offs, each three bytes at a time in seconds.

Every expected byte here is written out, and every expected time is worked out with `Fraction`
from the sample core's own `sample_at` rule gives, restated in the test: none comes from the
builder.
"""

from fractions import Fraction

import pytest
from patchbay import Note, PatchbayValidationError, Pattern, RenderRequest

from patchbay_vital.midi import midi_of

_RATE = 48000
_BAR = 96000  # one bar of four beats at 120 bpm, at 48 kHz


def _pattern(*notes: Note, tempo: float = 120.0) -> Pattern:
    return Pattern(tempo_bpm=tempo, bars=1, beats_per_bar=4, notes=notes)


def _note(pitch: int, start: float, duration: float, velocity: int = 100, channel: int = 0) -> Note:
    return Note(
        pitch=pitch,
        velocity=velocity,
        start_beats=start,
        duration_beats=duration,
        channel=channel,
    )


def _at(sample: int, rate: int = _RATE) -> float:
    """Return the time half a sample past a sample, in seconds, exactly rounded."""
    return float(Fraction(2 * sample + 1, 2 * rate))


def _request(rate: int = _RATE, tail: float = 0.25) -> RenderRequest:
    return RenderRequest(sample_rate=rate, tail_seconds=tail)


def test_a_note_is_a_note_on_and_a_note_off_of_three_bytes_each() -> None:
    """Middle C at velocity 100 on the first channel, one beat at 120 bpm: 0.5 s, 24,000 samples."""
    midi = midi_of(_pattern(_note(60, 0.0, 1.0)), _request())
    assert midi == ((b"\x90\x3c\x64", _at(0)), (b"\x80\x3c\x00", _at(24000)))
    assert midi[0][1] == 0.5 / _RATE


def test_the_bytes_are_the_note_s_own_pitch_velocity_and_channel() -> None:
    """Core's `Note` holds MIDI's integers, so each goes into its byte as it is, at either end."""
    highest = midi_of(_pattern(_note(127, 0.0, 1.0, velocity=127, channel=15)), _request())
    assert [message for message, _ in highest] == [b"\x9f\x7f\x7f", b"\x8f\x7f\x00"]
    lowest = midi_of(_pattern(_note(0, 0.0, 1.0, velocity=1, channel=0)), _request())
    assert [message for message, _ in lowest] == [b"\x90\x00\x01", b"\x80\x00\x00"]
    tenth = midi_of(_pattern(_note(36, 0.0, 1.0, velocity=64, channel=9)), _request())
    assert [message for message, _ in tenth] == [b"\x99\x24\x40", b"\x89\x24\x00"]


@pytest.mark.parametrize(
    "fields",
    [
        {"velocity": 0},
        {"velocity": 128},
        {"channel": 16},
        {"channel": -1},
        {"pitch": 128},
    ],
)
def test_core_refuses_a_note_whose_bytes_would_not_be_midi_s(fields: dict[str, int]) -> None:
    """No note-on of velocity 0 can be built, nor a byte out of range: the builder leans on it.

    A note-on of velocity 0 is a note-off to most receivers, and the builder has no guard for
    one, since core's `Note` cannot hold it. Should core widen `Note`, this fails first.
    """
    whole = {"pitch": 60, "velocity": 100, "start_beats": 0.0, "duration_beats": 1.0, "channel": 0}
    with pytest.raises(PatchbayValidationError):
        Note.model_validate({**whole, **fields})


def test_a_time_is_half_a_sample_past_the_sample_core_s_rule_gives() -> None:
    """Each event sits at `(2 n + 1) / (2 rate)` seconds, n the sample its beat rounds to.

    At 137 bpm and 44.1 kHz, beats 1.25 and 3.0 fall on samples 24,142 and 57,942: `round(beat *
    60 / tempo * rate)`, half to even, worked out here with `Fraction`.
    """
    tempo, rate = 137.0, 44100
    on = round(Fraction(5, 4) * 60 / Fraction(tempo) * rate)
    off = round(Fraction(3) * 60 / Fraction(tempo) * rate)
    assert (on, off) == (24142, 57942)
    midi = midi_of(_pattern(_note(60, 1.25, 1.75), tempo=tempo), _request(rate))
    assert [when for _, when in midi] == [_at(on, rate), _at(off, rate)]
    for (_, when), sample in zip(midi, (on, off), strict=True):
        assert sample < Fraction(when) * rate < sample + 1


def test_events_come_in_time_order_whatever_order_the_notes_are_in() -> None:
    """The pattern lists a later note first; its events still follow the earlier note's."""
    midi = midi_of(_pattern(_note(64, 2.0, 1.0), _note(60, 0.0, 1.0)), _request())
    assert midi == (
        (b"\x90\x3c\x64", _at(0)),
        (b"\x80\x3c\x00", _at(24000)),
        (b"\x90\x40\x64", _at(48000)),
        (b"\x80\x40\x00", _at(72000)),
    )


def test_a_pitch_repeated_without_a_gap_is_released_before_it_is_struck_again() -> None:
    """On one sample the off of the note that began earlier comes before the next note's on."""
    midi = midi_of(_pattern(_note(60, 1.0, 1.0), _note(60, 0.0, 1.0)), _request())
    assert midi == (
        (b"\x90\x3c\x64", _at(0)),
        (b"\x80\x3c\x00", _at(24000)),
        (b"\x90\x3c\x64", _at(24000)),
        (b"\x80\x3c\x00", _at(48000)),
    )


def test_a_note_too_short_to_last_a_sample_is_struck_and_then_released() -> None:
    """At 100 Hz a note of a thousandth of a beat begins and ends on one sample: on, then off.

    Beside it on that sample, a note that began earlier ends first and a longer one begins
    before the short one is released, each group in the pattern's order.
    """
    rate = 100
    earlier = _note(48, 0.0, 2.0)
    short = _note(60, 2.0, 0.001)
    longer = _note(72, 2.0, 1.0)
    midi = midi_of(_pattern(short, longer, earlier), _request(rate))
    assert midi == (
        (b"\x90\x30\x64", _at(0, rate)),
        (b"\x80\x30\x00", _at(100, rate)),
        (b"\x90\x3c\x64", _at(100, rate)),
        (b"\x90\x48\x64", _at(100, rate)),
        (b"\x80\x3c\x00", _at(100, rate)),
        (b"\x80\x48\x00", _at(150, rate)),
    )


def test_a_note_that_starts_at_the_render_s_length_is_left_out_whole() -> None:
    """With no tail the bar is 96,000 samples, and a note at its very end starts on sample 96,000.

    Core's reference instrument mixes such a note into no sample; here it gives no event.
    """
    request = _request(tail=0.0)
    late = _note(72, 3.99999, 0.00001)
    assert request.samples(_pattern(late)) == _BAR
    assert request.sample_at(_pattern(late), 3.99999) == _BAR
    assert midi_of(_pattern(late), request) == ()
    assert midi_of(_pattern(_note(60, 0.0, 1.0), late), request) == (
        (b"\x90\x3c\x64", _at(0)),
        (b"\x80\x3c\x00", _at(24000)),
    )


def test_a_note_off_at_the_render_s_length_is_left_out_and_the_note_on_kept() -> None:
    """A note held to the end of the bar, no tail: its off would fall on the sample past the last.

    The render ends before it, as core's reference clamps a note's end to the length; with a
    tail the same off is inside the render and is sent.
    """
    held = _pattern(_note(60, 2.0, 2.0))
    assert midi_of(held, _request(tail=0.0)) == ((b"\x90\x3c\x64", _at(48000)),)
    assert midi_of(held, _request(tail=0.25)) == (
        (b"\x90\x3c\x64", _at(48000)),
        (b"\x80\x3c\x00", _at(_BAR)),
    )


def test_no_note_starts_before_the_render() -> None:
    """Core's `Note` takes no start before beat 0, so the first sample an event can have is 0."""
    with pytest.raises(PatchbayValidationError):
        _note(60, -0.001, 1.0)
    assert midi_of(_pattern(_note(60, 0.0, 4.0)), _request())[0][1] > 0.0


def test_a_pattern_of_no_notes_and_a_render_of_no_samples_give_no_midi() -> None:
    """Nothing to play, and nowhere to play it: a tempo so fast the bar rounds to no sample."""
    assert midi_of(_pattern(), _request()) == ()
    instant = _pattern(_note(60, 0.0, 4.0), tempo=23_040_000.0)
    assert _request(tail=0.0).samples(instant) == 0
    assert midi_of(instant, _request(tail=0.0)) == ()
