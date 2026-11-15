# Revision after the Review of patchbay-vital's PR 19 — Shaping Notes

Shaped 2026-11-15 in plan mode with this repository's customized `/agent-os:shape-spec`. Each of
the review's seven findings was checked against HEAD (`f26e6bc`, the head the review read) before
any question, read only and in memory, and the owner then answered eight questions in two rounds.

Wherever this file names the pull request it writes "patchbay-vital's PR 19": issue #8 uses
"core's review of PR 19" for fromtheoutfit/patchbay#19, another pull request.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The seven findings of the owner's review of patchbay-vital's PR 19 at `f26e6bc`
(https://github.com/fromtheoutfit/patchbay-vital/pull/19#issuecomment-6894640094): one bug, three
test gaps, three efficiency and cleanup notes. The review found the pull request's main claim to
hold up.

- The bug and the three test gaps are fixed.
- The two efficiency notes are declined by the owner.
- The seventh finding is answered with a test, not a code change.
- Neither of #8's questions is decided, and none of #18's. No gate file changes. No stage,
  commit, push or pull request edit by an agent.

## What was checked while shaping

Read only, in memory, against `f26e6bc`; nothing was written.

| # | Finding | On this tree |
|---|---|---|
| 1 | `holds` raises on a huge finite value | True |
| 2 | The properties miss a `to_preset` without its exception | True |
| 3 | The unit reader checks less than the integration reader | True |
| 4 | "The double above" steps toward 0.0 | True and latent |
| 5 | `to_normalized` lands the preset twice | True |
| 6 | Indexed records pay for a landing | True |
| 7 | The exception cannot succeed on an indexed scale | False from 2 ** 23 up; true of the map |

- **Finding 1.** On `NormalizedScale(kind="linear", minimum=0.0, maximum=1.0)`, `holds(3.5e38)`,
  `holds(1e300)` and `holds(-1e300)` raise `OverflowError` ("cannot convert Infinity to integer
  ratio"), and so does `holds(1.0)` on a scale from 0 to 1.401298464324817e-45. `holds(2.0)`,
  `holds(-1.0)` and `holds(1e30)` answer False.
- **Finding 1's suggested fix is not exact.** The review suggests False outside
  `[minimum, maximum]`, since "a scale holds nothing past its ends". On
  `NormalizedScale(kind="linear", minimum=-16777216.0, maximum=1.0000001192092896)` the span is
  16777218, normalized 1.0 lands on 2.0, past the maximum, `holds(2.0)` is True and
  `holds(maximum)` False. On all 903 committed records `to_preset(0.0)` is the minimum and
  `to_preset(1.0)` the maximum, so the two forms agree there.
- **Finding 1 reaches #18's method.** `scale.to_normalized(3.5e38)` raises the same
  `OverflowError`. #18 names only a value that is not finite.
- **Finding 2.** M5 in #16's `verification/mutation.txt`, the exception removed, fails four
  tests: `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`,
  `test_every_pinned_value_comes_back_on_every_record`,
  `test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset` and
  `test_else_a_display_takes_the_float32_on_the_other_side`. Neither Hypothesis property is among
  them, nor `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds`.
- **What finding 2's `else` branch would catch,** with the exception removed, on `volume`:
  - 3 of the 4 pinned floor displays;
  - 0 of 20,000 displays drawn uniformly over its bounds (`random.Random(19)`);
  - 15 of 20,160 displays of held presets, 160 normalized values a binade
    (`numpy.random.default_rng(19)`).

  So the pinned-display test fails the mutant by name through the helper. The two Hypothesis
  properties draw arbitrary displays, which do not reach a display a held preset shows, and
  still pass it.
- **Finding 3.** By reading: the unit `_pinned` has neither check. With `volume_floor` emptied,
  `test_the_pinned_values_file_holds_three_named_sets` fails on the count, while
  `test_every_pinned_value_comes_back_on_every_record` and
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds` loop over
  nothing and pass.
- **Finding 4.** By reading: `math.nextafter(display, 0.0)`. Every display that test uses is
  `volume`'s at or below its floor, near -80, so the step toward 0.0 is the double above.
- **Finding 7's premise.** `next_float32` of a whole number is a whole number from 2 ** 23 up,
  where float32s are 1 apart: `next_float32(8388608.0, inf)` is 8388609.0, and
  `next_float32(8388607.0, inf)` is 8388607.5. The review says 2 ** 24. The map's largest indexed
  end is 362,879, below 2 ** 23, and no indexed value of the map enters the exception (#16's
  `verification/indexed-count.txt`: `to_preset` is the whole number itself on all 398,563).
- **Finding 7's record.** A made-up record validates:
  - scale: indexed, minimum -16777216.0, maximum 16777216.0, span 33554432.0;
  - curve: linear, multiply 3.0, offset 2 ** 54;
  - parameter: continuous, bounds 1.8014398459150336e16 to 1.801439855981363e16.

  At normalized 0.7500000596046448 the held preset is 8388610. Its display is
  1.8014398534647816e16, and the curve's value for that display is 8388611, which no normalized
  value lands on. A set of 8388611 holds 8388612, which shows another display. As shipped,
  `to_preset` takes the exception and returns 8388610, the held preset, which shows the display.
  Limited to linear scales it returns 8388612.

  On 8,100 sampled normalized values of that record (300 a binade, binades -27 to -1,
  `numpy.random.default_rng(7)`) the exception is taken on 86. The record fails the come-back
  property on 102 of them as shipped, and on 188 with the exception limited to linear scales. It
  is a record beyond what the map promises: its curve cannot tell neighbouring whole numbers
  apart.
- **Where a counted linear scale calls `holds`.** Only from `to_preset`'s exception. #16's direct
  count of 2026-11-14 puts that at `volume`'s 308,386 OTHER values, in binades -58, -57 and -56
  (31,879, 176,711 and 99,796). FELL is 0 on every binade, so no value entered the exception
  without returning the other side, and every value of `env_1_delay` is KEPT.

## Shaping answers

In the owner's words.

- **Finding 1:** "1. Shown by tests whose expected values come from primitives, each with a
  mutant failing by name: a huge finite value (3.5e38) answers False without raising; on the
  made-up scale whose top lands past its maximum, the value normalized 1.0 lands on answers True
  and the next float32 above it False. shape.md states the assumption the check rests on (the
  scale's value rises with the normalized value) and says whether any committed scale runs the
  other way; if one does, stop and present. holds gives the same answer as before this change on
  every committed record, checked over the pinned values and the indexed whole numbers."
- **The test gaps:** all three, "2: the else branch, 3: the unit reader, 4: toward math.inf".
- **The efficiency notes:** "1. Declined by the owner, citing the two earlier decisions (the fast
  path in PR 14's sixth review; finding 8 in this spec). shape.md records the timings with the
  machine, so a later spec that does need the speed starts from measured numbers."
- **Finding 7, the first answer, withdrawn:** "1. The indexed count is rerun in full (it is a
  minute) and shows no value differs from main. For linear scales, show from the diff that the
  statements a linear scale executes are the same as in the tree the direct count ran on, so that
  count stands; the short evidence (pinned values and the arbitrary-display sample) is rerun as a
  check. If the change cannot be made without altering what a linear scale executes, stop and
  present before touching it. shape.md corrects the premise to 2 ** 23 and names the mutant that
  puts the indexed exception back as an expected equivalent, or shows a test that fails it."
- **Finding 7, the second answer,** once the record above was found: "1. shape.md records that
  the earlier answer (limit to linear) was withdrawn once a record reaching the branch was found,
  with the record's fields. The reviewer's premise is corrected to 2 ** 23. The mutant limiting
  the exception to linear scales fails the new test by name."
- **The direct count:** "1. The transcript says how the three binades were identified as the only
  ones where the exception is taken (cited from the 2026-11-14 direct count's branch counts) and
  shows the recount's 308,386 matching that figure. Both trees and the machine are printed
  before and after. Any difference from main: stop and present."
- **Issue #18:** "Revise issue #18's body in place with a "Revised 2026-11-15" paragraph, no
  attribution, not a comment: the same defect reaches a huge finite value
  (scale.to_normalized(3.5e38) raises OverflowError), so the issue's scope reads "a value outside
  what the scale can take, finite or not", with the example added beside the others. Nothing in
  to_normalized or _landing changes here; shape.md and the CHANGELOG say the finite case was
  found in this revision and sits with #18. The text is short and factual, so file it without
  presenting first, and read it back."
- **Steps 2 to 5:** "1. Wherever this revision's shape.md, CHANGELOG entry or issue edits name
  the pull request, write "patchbay-vital's PR 19" (or its URL), since issue #8 uses "core's
  review of PR 19" for fromtheoutfit/patchbay#19. The drafted reply to the review stays a draft
  in shape.md for the owner to post."

### The owner's answers after the evidence

Asked on 2026-11-15, once the transcripts were in: what to do with a test in `holds` that the
mutation run showed no longer changes an answer, which standards edits to make, and which base
proposals to send.

- **The `[0, 1]` test in `holds`,** to the option "Remove it": "1. shape.md states why the check
  is implied, not only that sampling found no difference: the new bound (within what the ends
  land on) together with _landing keeping its step inside [0, 1] leaves no preset whose landing
  has a normalized value outside [0, 1]; if that argument has a gap, keep the check and say
  where the gap is. The 698,810 scales are recorded as a sample with its generator and seed. The
  reruns as proposed, stopping on any difference."
- **The project standards:** all three, "vital/parameter-map.md, vital/measures.md, index.yml,
  vital: entries".
- **The base proposals:** both, "tests.md: both ways, tests.md: both readers".

## Decisions

1. **The scope is the review's seven findings,**
   https://github.com/fromtheoutfit/patchbay-vital/pull/19#issuecomment-6894640094, and nothing
   beside them.
2. **Finding 1: `NormalizedScale.holds` answers False outside what the scale's ends land on,**
   `to_preset(0.0)` and `to_preset(1.0)`, before it lands the preset.
   - One check covers an infinity, a NaN and a huge finite value, so it replaces the `isfinite`
     guard #16 added.
   - **The assumption it rests on:** the scale's value rises with the normalized value, so
     nothing below what 0 lands on or above what 1 lands on is held. The span is positive, since
     the model refuses a minimum that is not below the maximum; `fma32` rounds an exact value
     that rises with the normalized value, once; and rounding, to a float32 or to a whole
     number, keeps order. `verification/holds-check.txt` says whether any committed scale runs
     the other way; one that does stops the work.
   - The review's form, False outside `[minimum, maximum]`, is not taken: it answers False for a
     value normalized 1.0 lands on, on the made-up scale above.
   - `_landing`, `to_normalized` and `MappedParameter.to_preset` are not touched.
3. **Findings 2, 3 and 4 are fixed** as the review asks, and this file says what each change
   does and does not catch: the two properties still pass without the exception, and finding 4
   changes no value the test uses.
4. **Findings 5 and 6 are declined by the owner,** as the fast path was in PR 14's sixth review
   and finding 8 in #16's spec. The timings are recorded below with the machine.
5. **Finding 7: the exception stays on an indexed scale, and a test holds it.** No statement of
   `to_preset` changes. The owner's first answer, to limit the exception to linear scales, was
   withdrawn once the record above was found to reach the branch and to get the right answer
   from it.
6. **#16's direct count stands but for the three binades where `holds` runs,** `volume`'s -58 to
   -56, which are recounted against `main`.
7. **The finite case of the scale's `to_normalized` sits with #18,** whose body is revised in
   place.
8. **A test's expected value comes from primitives,** as in #16's spec, Decision 7: `Fraction`,
   `fma32` or the forward `scale.to_preset`, `next_float32` and the curve. Never `holds`,
   `to_normalized`, `_landing` or `MappedParameter.to_preset`.
9. **No gate file changes, and the negative harness is not rerun.** No file is added, removed or
   renamed under `scripts`, `src`, `tests` or `agent-os/standards`.
10. **The `[0, 1]` test of the landing is removed from `holds`,** by the owner's answer after the
    evidence, since the check of the ends implies it. `holds` reads:

    ```python
    if not self.to_preset(0.0) <= preset <= self.to_preset(1.0):
        return False
    return _landing(self, preset)[1] == preset
    ```

    The argument is below, with the one place where the owner's wording of it needed more.

### Why the `[0, 1]` test is implied

After the check of the ends, the preset lies between what 0 lands on, B, and what 1 lands on, T.
`_landing` returns a normalized value in two ways, and each is inside [0, 1] for such a preset.

1. **Its step toward the preset.** `_landing` takes the step only where it is inside [0, 1], by
   its own test. This is the part the owner's wording names.
2. **The float32 nearest the quotient, `(preset - minimum) / span`.** No statement keeps this
   one inside [0, 1]: rounding does. This is the part the owner's wording leaves out, and it is
   where a gap would be. There is none:
   - Rounding to a float32 keeps order, and 0 and 1 are float32s. So it is enough that B's
     quotient is at least 0 and T's is at most 1 + 2 ** -24, a tie that rounds to 1.
   - **B is the minimum.** `fma32(0, span, minimum)` is the minimum, a float32 already, so its
     quotient is 0.
   - **T is at most `span * 2 ** -24` past `minimum + span`.** Write fl for rounding to the
     nearest float32, d for `maximum - minimum`, so that the span is fl(d) and T is
     fl(minimum + span).
     - If d is a float32, the span is d, `minimum + span` is the maximum, and T is the maximum:
       the quotient is 1.
     - Otherwise the span is d + e, where e is the rounding's error. With 2 ** k ≤ d < 2 ** (k + 1),
       |e| ≤ 2 ** (k - 24), and the span is at least 2 ** k, so |e| ≤ span * 2 ** -24. And
       `minimum + span` is `maximum + e`.
       - Where e < 0, T is at most the maximum, since rounding keeps order. So
         T - minimum ≤ d = span + |e| ≤ span * (1 + 2 ** -24).
       - Where e > 0, the rounding of `maximum + e` adds at most e. Next to the maximum it rounds
         up only when e is at least half the step, and then adds no more than e. Further up, a
         float32 step is at most twice the one below it, which lies between the maximum and
         `maximum + e`, so half the step is at most e. So T - minimum ≤ span + e ≤
         span * (1 + 2 ** -24).
   - **An indexed scale** is the same: its bounds are whole, so the span and `minimum + span`
     are whole, a whole number rounds to a whole float32, and the rounding to a whole number
     changes nothing.
   - A span that is not finite is outside this: every method of such a scale raises, issue #18.

So for a preset between B and T the quotient is between theirs, its nearest float32 is in
[0, 1], and every normalized value `_landing` returns is one the host can set. The test changed
no answer.

**Checked beside the argument,** each a sample and labelled so, in memory:
- 698,810 scales (`numpy.random.default_rng(23)`): bounds drawn as float32 bit patterns of any
  sign and exponent, as large values a few steps to a few thousand apart, and as whole numbers up
  to 2 ** 40. On none does `_landing` land on what an end lands on, or on the float32 inside it,
  from a normalized value outside [0, 1].
- 1,327,135 scales (`numpy.random.default_rng(29)`), a third of them built so that the
  difference of the bounds is a tie or beside one: T's exact quotient, worked out with
  `Fraction`, is above 1 + 2 ** -24 on none and exactly 1 + 2 ** -24 on 511, so the bound is met
  and not passed. The float32 nearest each end's quotient is in [0, 1] on all.
- `test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval` holds the same on bounds
  Hypothesis draws, on every run.

### Where the implementation departs from the plan

- **`holds` lost its `[0, 1]` test of the landing, which the plan's Decision 2 kept.** The first
  mutation run showed M3, `holds` without that test, passing every unit test, where it failed two
  in #16's transcript: the check of the ends now refuses what the test refused. The owner was
  asked and chose to remove it, on the argument under Decision 10.
  - M3 is now the test put back, an expected equivalent, and the transcript shows `holds`
    without the test failing two tests on the tree before, `f26e6bc`.
  - Every transcript was run again on the tree without the test, not only the four the owner
    was offered: each prints the blob it read, and they are one blob.
  - `test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval` is added for it.
- **`holds-check.txt` holds more than the plan listed:** a labelled sample of the forward value
  never falling, on each distinct scale, beside the count of the ends.
- **A property test the plan named only as "beside them"** is
  `test_a_scale_s_value_rises_with_the_normalized_value`, on every hand-built record.
- **`test_the_pinned_values_file_holds_three_named_sets` loses its range assertion.** That a
  normalized value is in [0, 1] is now the reader's check, which fails every test reading the
  file.
- **The recount's transcript parses both trees,** with the parser #16's count used, to show which
  functions' statements differ: `statements.py`, embedded in it.
- **`cost.txt` times three trees and `holds` too:** `main`, the tree before and this one.
- **Issue #18's title is unchanged.** The owner asked for its body to be revised; the title still
  reads "on a non-finite value".

## What the transcripts show

Each transcript in `verification/` opens with its date, the branch and the machine: arm64, an
Apple M4 Pro of 14 cores, macOS 26.6.2 (25G83), Python 3.12.16. Each prints the three trees
before and after its run, every file it reads by blob, compared with `cmp`: this tree, the tree
before the revision (`f26e6bc`, the pull request's head, extracted with `git archive`) and
`main`'s (`f533b1b`, extracted the same way). Each prints the machine again after the run, and
embeds its scripts.

**No run found a difference it was to stop on.**

- **`holds-check.txt`, counts, with one labelled sample.** `holds` in the tree before and in this
  one, each imported by its own pool of processes.
  - **No committed scale runs the other way.** The 903 records lie on 60 distinct scales, 39
    linear and 21 indexed. On every record the minimum is below the maximum, the span is
    positive and finite, 0 lands on the minimum and 1 on the maximum.
  - **A sample beside it:** on each of the 60 scales the forward value never falls over 5,674
    sorted float32 normalized values (`numpy.random.default_rng(19)`, 15 bit patterns a binade,
    with 0.0, 1.0 and the float32 beside each).
  - **The pinned values, on every record:** 13,397 presets asked of `holds` in both trees. True
    in both on 8,681, False in both on 4,716, and no answer differs. Neither tree raises.
  - **The indexed whole numbers:** every whole number and half of every one of the 351 indexed
    records, and past each end, 798,179 presets. True in both on 398,563, False in both on
    399,616, and no answer differs.
- **`direct-count.txt`, a count, on three binades.** `main`'s shipped methods against this
  tree's, five calls a value.
  - **Why three binades,** printed in the transcript: of the 48 functions and module values of
    `parameters.py` and `float32.py`, 47 have the statements of the tree #16's count ran on, and
    the one that differs is `NormalizedScale.holds`. `to_preset` calls it only from its
    exception. That count classed every value: the exception is taken on 308,386 values of
    `volume`, in binades -58, -57 and -56, no value enters it and falls through, and every value
    of `env_1_delay` is kept.
  - **The recount:** all 25,165,824 values of those binades. No value differs from `main` in any
    of the five calls. 24,150,585 keep the curve's float32, 706,853 take what a set holds, and
    308,386 take the exception: 31,879, 176,711 and 99,796 a binade, the earlier count's figures.
- **`indexed-count.txt`, a count, in full,** against `main`: 398,563 whole numbers called and
  398,212 halves, 807 of them refused by both trees. No value differs.
- **`arbitrary-displays.txt` and `plugin-probe.txt`, rerun as checks,** give #16's figures again.
  - Of 11,000,000 sampled displays 2,041,885 give another preset than `main`'s, each unheld
    there and held here, the normalized value the same.
  - Of `volume`'s 23,726,567 doubles at its floor, 344,580 change.
  - Vital 1.6.4 holds this tree's preset on all 9,200 sampled sets and at both pinned displays.
- **`mutation.txt`,** scratch copies, one mutant each, derandomized. This revision's own:

  | Mutant | What it changes | Result |
  |---|---|---|
  | MN3 | `holds` without its check of the ends | fails 4 tests, of a value past the ends or the scale |
  | MH1 | `holds` as `f26e6bc` has it, whole | fails `test_a_scale_holds_nothing_outside_what_its_ends_land_on` alone |
  | MH2 | the check made the review's, the bounds | fails `test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum` |
  | M5 | the exception removed | fails 6 tests, the pinned-display test among them |
  | M5 | the same, the two properties alone | passes, 10 cases |
  | M5 | the same, on `f26e6bc` and its tests | fails 4; the pinned-display test passes there |
  | MI1 | the exception limited to linear scales | fails the indexed test alone |
  | MD4 | the step toward 0.0 again | passes: an equivalent on the values the test uses |
  | MU1 | a set emptied, on `f26e6bc`'s unit tests | 3 fail; the two looping tests pass |
  | MU1 | the same, on this tree's | all 9 tests reading the file fail, naming the set |
  | MU2 | a value of 1.5, on `f26e6bc`'s unit tests | 4 fail, downstream |
  | MU2 | the same, on this tree's | all 9 fail at the reader, naming the line |
  | M3 | the `[0, 1]` test put back in `holds` | passes: an equivalent, by Decision 10 |
  | M3 | `holds` without that test, on `f26e6bc` | fails 2 tests of a value past the scale |

  The earlier mutants are rerun and read as in #16's transcript.

  **What finding 2's fix does and does not catch.** The helper now fails a `to_preset` without
  its exception, at the pinned displays, through
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds`. The two
  Hypothesis properties still pass it, as the review's suggested fix would leave them: a display
  drawn over a parameter's bounds is not one a held preset shows.

  **What finding 4's fix changes:** no value. Every display that test uses is negative.

## The timings, with the machine

Recorded so that a later spec that needs the speed starts from measured numbers; findings 5 and
6 are declined here. From `verification/cost.txt`, its second pass: the minimum of 7 repeats,
µs a call over 1,000 values, in each of three trees.

| Call | `main` | Before (`f26e6bc`) | This tree |
|---|---|---|---|
| `volume`, `to_preset`, uniform displays | 15.7 | 15.6 | 15.8 |
| `volume`, `to_normalized`, uniform displays | 27.8 | 28.1 | 28.0 |
| `volume`, `to_preset`, displays at the floor | 18.1 | 18.7 | 18.6 |
| `volume`, `to_normalized`, displays at the floor | 31.6 | 31.8 | 32.3 |
| `polyphony` (indexed), `to_preset` | 3.7 | 15.3 | 15.7 |
| `polyphony` (indexed), `to_normalized` | 15.5 | 27.3 | 27.0 |
| `volume`, `scale.holds`, held presets | 12.0 | 12.2 | 21.1 |
| `polyphony`, `scale.holds`, held presets | 11.6 | 11.5 | 23.2 |
| The 903 records at their defaults, `to_normalized`, ms | 13.3 | 14.8 | 14.7 |

- **The machine:** arm64, Apple M4 Pro, 14 cores (10 performance, 4 efficiency), macOS 26.6.2
  (25G83), Python 3.12.16, on 2026-11-15 at 09:23 EST. The load average was 3.70 before the run
  and 3.84 after it, with 20 over the five minutes before, the other transcripts having just run.
- **Finding 5's cost** is the second landing: `to_normalized` at about 27 µs against
  `to_preset`'s 15.
- **Finding 6's cost** is the indexed row: 3.7 µs on `main`, 15 since #16.
- **This revision's own cost** is in `holds` alone: 21 to 23 µs against 12, for the two forward
  calls of its check. `to_preset` calls `holds` only from its exception.

## The reply to the review, drafted

For the owner to post on patchbay-vital's PR 19; not posted by an agent.

> Revised in `agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`.
>
> 1. **Fixed, with another check than the one suggested.** `holds` answers False outside what
>    the scale's ends land on, `to_preset(0.0)` and `to_preset(1.0)`, not outside the bounds. On
>    a scale from -16777216 to 1.0000001192092896 the span rounds up and 1 lands on 2, past the
>    maximum: the bounds would refuse a value the plugin holds. The scale's `to_normalized`
>    raises the same error on 3.5e38, which is now in #18's scope.
> 2. **Fixed.** The helper checks the exception both ways, and a `to_preset` without it now
>    fails the pinned-display test by name. The two properties still pass it: a display drawn
>    over the bounds is not one a held preset shows.
> 3. **Fixed.** The unit reader has both checks.
> 4. **Fixed.** No value the test uses changes, since its displays are negative.
> 5. **Declined,** as the fast path was in PR 14's sixth review. The timings are in the spec's
>    shape.md with the machine.
> 6. **Declined,** on the same ground.
> 7. **Not changed, and held by a test.** The exception can be taken on an indexed scale from
>    2 ** 23 up, where float32s are whole numbers, not only from 2 ** 24. On a made-up record
>    (indexed, -2 ** 24 to 2 ** 24, linear curve of multiply 3 and offset 2 ** 54) it returns
>    8388610, the held preset that shows the display; limited to linear scales it would return
>    8388612, which does not. The map has no indexed scale that wide.
>
> `holds` answers as before on every committed record, and the three binades of `volume` where
> `to_preset` calls it were recounted against `main`: 25,165,824 values, no difference, the same
> 308,386 taking the exception.

**Lines of the pull request's body this revision makes stale,** for whoever next edits it:
- "`NormalizedScale.holds` answers False for a value that is not finite": now for a value outside
  what the scale's ends land on.
- "the file's reader fails by name on an empty set": now each module's reader.
- "Two defects found beside finding 6 are left to #18 ... on a value that is not finite": #18's
  scope is now a value outside what the scale can take, finite or not.
- The unit tests' list lacks this revision's five.
- "521 passed", the CI run at `f26e6bc`, "two commits", and the Limits line on what the gate's
  record covers.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing
  on either side". This revision keeps `holds` to its own definition on every scale.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — expected values from primitives; a repository file read from pytest's
  root; a reader that fails by name.
- `base/process/verification-gate` — the gate unchanged; its record; when the harness reruns.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issue edits without
  attribution.
- `vital/parameter-map` — the rule, what `holds` answers, and how a fix is counted.
- `vital/measures` — the pinned values' one file and its readers.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — read for the load test, which this revision does not change.

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script
under `scripts/` as git lists them, with no tracked file a `.gitignore` ignores;
`uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set and
`uv.lock`'s pins;
and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the commit in
`agent-os/standards/base/.version` — and the three judgment steps are recorded, in this order:
Docs, Version, then the standards retrospective below.

**Results (2026-11-15):** `scripts/gate.sh` exits 0 on branch
`refactor/16-the-parameter-map-to_preset-returns-a-preset-the-plugin-never-holds-for-a-display-no-held-preset-shows`,
all six steps, 534 tests passed and none skipped, Vital installed. The record is
`verification/gate-run.txt`: the date and the branch on its first lines, the tree before and
after by blob, compared with `cmp`, and the machine before and after. It ran once, last, after
the retrospective's edits. Written after it: this paragraph, and the upstream issues' numbers
below. No gate file changed and no file was added, removed or renamed under `scripts`, `src`,
`tests` or `agent-os/standards`, so the negative harness was not rerun.

**Docs (step 7):** checked on 2026-11-15, each against the shipped code.
- `src/patchbay_vital/parameters.py`: `NormalizedScale.holds`'s docstring says what it now
  answers, what the check rests on and why the landing's normalized value is not tested again; `MappedParameter.to_preset`'s says where an indexed scale
  can take the exception. No other docstring there names what changed.
- `tests/unit/test_parameters.py`: the docstrings of `_pinned`, `_assert_a_set_holds_it`,
  `test_the_pinned_values_file_holds_three_named_sets` and the five new tests say what each
  asserts and where its expected value comes from.
- `CHANGELOG.md`: #16's entry said `holds` answers False "for a value that is not finite" and
  that the integration reader alone fails on an empty set. Both read as the code does now.
- `README.md`, `CLAUDE.md` and `agent-os/product/`: nothing there names what changed.
- Issue #18, revised in place on 2026-11-15 and read back: its first defect reads "a value
  outside what the scale can take, finite or not", with `to_normalized(3.5e38)` beside the
  other examples. Its title was left as it reads.
- The body of patchbay-vital's PR 19 is not edited by an agent in this revision. The lines it
  makes stale are listed above, beside the drafted reply.
- The standards that name what changed, `vital/parameter-map.md` and `vital/measures.md` with
  `index.yml`, are the retrospective's, below.

**Version (step 8):** recorded under `[Unreleased]` in `CHANGELOG.md`, in #16's entry, the first
of `### Fixed`: its head names this revision, its `holds` and reader lines are revised, and a
sub-list gives each finding's outcome. No release is cut: the version stays 0.0.1.

## Standards Retrospective

Step 9, always last. Written on 2026-11-15 from the shipped diff and the transcripts, and its
own change set: `agent-os/standards/vital/parameter-map.md`, `agent-os/standards/vital/measures.md`
and `agent-os/standards/index.yml`. Every edit was drafted on a scratch copy, presented to the
owner on 2026-11-15 and approved before it was made: the owner chose all three,
"vital/parameter-map.md, vital/measures.md, index.yml, vital: entries".

**1. A pattern no standard covered.** One, added to `vital/parameter-map.md`:
- **A change inside one branch is recounted where that branch runs.** Parsing both trees shows
  which functions' statements differ; an earlier count's classes say where the branch that
  reaches the changed function is taken; those values are counted again. Verified against
  `verification/direct-count.txt`: `NormalizedScale.holds` the one function that differs from
  `f26e6bc`, the earlier count's 308,386 in three binades, and the recount's 25,165,824 values
  with the same 308,386.

**2. A standard that was wrong or stale.**
- `vital/parameter-map.md`:
  - It said `holds` answers False for a value that is not finite. It says what the code does:
    False outside what the ends land on, with the assumption that rests on, and that the
    landing's normalized value is not tested again. Verified against `NormalizedScale.holds`,
    `test_a_scale_holds_nothing_outside_what_its_ends_land_on`,
    `test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum`,
    `test_a_scale_s_value_rises_with_the_normalized_value`,
    `test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval`,
    `verification/holds-check.txt` and MN3, MH1, MH2 and M3 in `verification/mutation.txt`.
  - "An indexed scale" gains that the exception can be taken there from 2 ** 23 up, and the
    test that holds it. Verified against
    `test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display` and MI1.
  - The property tests' line gains that the helper checks the exception both ways, and that
    the pinned displays, not the draws, are what reach it. Verified against
    `_assert_a_set_holds_it` and M5, on this tree, on the properties alone and on `f26e6bc`.
- `vital/measures.md`: it said the integration module's reader alone fails on an empty set or a
  normalized value outside [0, 1]. Each reader does. Verified against the unit module's
  `_pinned`, and MU1 and MU2.

**3. A deliberate deviation.**
- **Deviation, not a standard change:** `vital/parameter-map.md` says a method is never ruled
  out by an earlier count of another tree. The recount here does lean on the count of
  2026-11-14 to say where `holds` runs. It may: that count's tree and this one differ in `holds`
  alone, shown by parsing, and `holds` is not on the path that decides whether the exception is
  entered. The standard's new rule states the condition.
- **Deviation, not a standard change:** `base/process/standards-retrospective.md` says the
  approved proposals become one issue. Each is revised into the open issue it refines, in
  place, as on 2026-11-15 for #16's spec, by the owner's word.

**4. Pointers that moved.** None was renamed or removed. The five new tests and this revision's
transcripts are added to `vital/parameter-map.md`'s "Verified against" lists.

`agent-os/standards/index.yml`: the `vital:` descriptions of `parameter-map` and `measures` are
kept in step with the two edits. The `base:` section is the sync's and is not touched.

Proposals sent upstream: #40 and #42, revised in place.

Those are fromtheoutfit/patchbay-standards#40 and #42, each revised on 2026-11-15 after the
gate's clean run, with a second "Revised 2026-11-15" paragraph. No new issue was filed.

### Standards retrospective (proposed, base)

Presented to the owner on 2026-11-15, multi-select, and both approved: "tests.md: both ways,
tests.md: both readers". Each refines a proposal already open upstream, so it is revised into
that issue in place. Their wording was checked against the open issues #40 and #42 as they read
after that morning's revisions.

- `base/testing/tests.md`, "Inside a test" (both ways) — an assertion about an exception in the
  code under test is made both ways: where the code takes the exception, that the rule allows
  it, and where the code does not, that the rule does not call for it. A helper that asserts
  only on the path the code took passes a code that never takes it. Verified against
  `tests/unit/test_parameters.py` (`_assert_a_set_holds_it`,
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds`) and M5 in
  `verification/mutation.txt`, which passes that test on `f26e6bc` and fails it by name on this
  tree. Proposed, not applied; revised into
  fromtheoutfit/patchbay-standards#40, its proposal 2, in place.
- `base/testing/tests.md`, "Inside a test" (both readers) — evidence for #42's rule that a
  reader of a file of test values fails by name on an empty set: the unit module's reader now
  does, where #42 said the unit module held only each set's count. No rule changes. Verified
  against `tests/unit/test_parameters.py` (`_pinned`) and MU1 and MU2 in
  `verification/mutation.txt`. Proposed, not applied; revised into
  fromtheoutfit/patchbay-standards#42 in place.
