# Issue #16: to_preset Returns a Held Preset — Shaping Notes

Shaped 2026-11-13 to 14 in plan mode with this repository's customized `/agent-os:shape-spec`. The
rule and each carried finding were checked against HEAD (`f533b1b`, which is `main`) before any
question, read only, and the owner then answered eight questions in two rounds.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #16, "The parameter map: to_preset returns a preset the plugin never holds for a display no
held preset shows" (https://github.com/fromtheoutfit/patchbay-vital/issues/16), whole: its rule,
the evidence it requires, its scope, and the six findings carried from PR 14's final review.

- `MappedParameter.to_preset` returns what a set of the display's float32 holds, and the float32
  on its other side only where that alone shows the display. So it always returns a held preset.
- It runs before #8 and decides neither of #8's questions: which held preset an arbitrary display
  takes, Vital's rounding or the nearer neighbour (finding 1), and whether `VitalInstrument.set`
  keeps a stored value (finding 3).
- No gate file changes. No stage, commit, push or pull request by an agent.

## What was checked while shaping

Read-only, in memory, against `f533b1b`: the new rule was compiled from the shipped source with
the changed lines replaced, and no file was written.

- **The rule reproduces the issue's sample.** The same preset and normalized value on 207,000
  held displays, 3,000 a group over all 69 groups (bit patterns uniform over [0, 1], seed 14). A
  different preset on 1,085 of `volume`'s 20,000 displays (`random.uniform`, seed 8), and on
  1,108 with `numpy.random.default_rng(8)`, the fifth review's figure; the normalized value
  unchanged on each.
- **Arbitrary displays, 20,000 a continuous group, `default_rng(16)`.** 204,233 of the 920,000 on
  linear scales change, 22%, on 31 of the 46 linear-scale groups, from 4.25% (`lfo_1_frequency`)
  to 75% (`lfo_1_smooth_time`). Every changed one was `main`'s unheld curve float32 and is now
  held, and the normalized value is unchanged on all 1,100,000. The held preset is the float32
  next to `main`'s on 136,355 and further away on 67,878, up to 922 float32 steps in 4,000 draws
  of `chorus_feedback`. The other 15 linear-scale groups and the 9 indexed continuous groups do
  not change.
- **`volume`'s floor.** There are 23,726,567 doubles from -80 to the display at 2 ** -43. Of
  200,000 sampled, 2,864 are shown by no held preset: `main` gave an unheld float32 that showed
  the display, and the rule gives a held one that does not.
- **The indexed line through the set path.** `to_preset`, `to_normalized` and `from_normalized`
  of it equal `main`'s on every whole number of all 351 indexed records, 398,563 calls. The 21
  distinct indexed scales hold 371,476 whole numbers between their ends, every one held. Halves
  and 180,000 arbitrary displays on the 9 continuous indexed groups: the same.
- **A made-up indexed scale, -1 to 2 ** 24.** `main` gives 16777216 for the bound's display,
  which the scale does not hold; the rule gives 16777215, held, the normalized value 1.0. From
  primitives: the nearest quotient is 1.0 and `fma32` there is 16777215.
- **A made-up linear scale whose maximum is unheld** (the test module's, -0.89999920129776 to
  1): at 2 ** 30 `main` gives 1.0 and the rule 0.9999999403953552, the normalized value 1.0 in
  both. The map's 39 distinct linear scales hold both their ends.
- **Finding 6's reach.** A scale from 2 ** 103 to the largest float32 does not hold its maximum.
  With a linear curve whose multiply is 5.28294562624475e+269, the record validates, and
  `to_preset(inf)` raises `OverflowError` on `main`. The reviewer's own scenario, an
  `exponential_inverted` curve at a display equal to its offset, is not reached: what a set
  holds shows the offset too.
- **Found beside finding 6.** `NormalizedScale.to_normalized` and `to_preset` raise the same
  built-ins on a non-finite value. A scale from the most negative float32 to the largest
  validates with an infinite span, and then every method raises `OverflowError`.
- **Finding 2's mutants of `_landing`.** The reviewer's two scenarios each fail a test by name
  on `main`: the step the wrong way fails
  `test_a_held_power_of_two_comes_back_through_the_normalized_path`, and no [0, 1] check fails
  `test_the_step_toward_a_preset_stays_where_the_host_can_set_it`. A third, a miss keeping the
  step's landing, passes the property on 78,000 values with the helper as shipped and fails
  three tests on their literals. With the helper from primitives it fails the property and
  `test_every_pinned_value_comes_back_on_every_record`.
- **Finding 9.** `tests/integration/test_vital_plugin.py:194` reads the file once per record. No
  unit test reads it more than once: six read it, once each.
- **Timing,** 200,000 values (4 ranges of 50,000, `default_rng(21)`), one process, the five
  calls of the fifth review's count: `volume` 81.5 µs on `main` and 80.6 with the rule;
  `env_1_delay` 79.4 and 78.6. So about 48 CPU-hours a record with both trees.
- **Finding 8's timing, as information.** `_landing` without its narrowing of values already
  float32 gives the same five values on those 200,000 values of each record, at 65.7 µs
  (`volume`) and 64.3 (`env_1_delay`).
- **Callers.** Nothing in `src/` calls `MappedParameter.to_preset` or `to_normalized`; the census
  calls the scale's `to_preset` and `to_normalized` only.

## Shaping answers

In the owner's words:

- **The indexed line**, told it returns the nearest whole number without asking the scale, that
  the map's are all held and a made-up scale wider than 2 ** 24 could return an unheld one:
  "2. Shown, not argued:
  - Every one of the 371,476 whole numbers on the 21 indexed scales gives the same value as
    main, by calling main's shipped method and this branch's directly; this is small enough to
    count in full, so it is counted, not sampled.
  - A unit test on a constructed indexed scale wider than 2 ** 24 holds the case the change is
    for, its expected value worked out from primitives, with a mutant that restores the old line
    failing it by name. shape.md says what the result means there: the nearest whole number the
    scale can hold, and what a caller sees when that is not the one asked for.
  - The choice labels and get/set of every committed indexed parameter are unchanged, as PR 14's
    final review checked for the indexed stepping."
- **The test findings:** "2, 3, 5 and 9. For 2 and 3: the _landing mutant that passes today is
  shown passing on main's tests and failing by name on this branch's, in one transcript. For 9:
  shape.md records the finding's second claim (unit tests reading the file more than once) as
  checked and not true."
- **The code findings:** "1 and 3. Finding 8 is declined by the owner: no value changes, the cost
  is not a concern (the fast path was declined in PR 14 for the same reason), and it would widen
  what the direct count has to stand behind; shape.md records the timing as information. For 6:
  the unit test's expected value is stated from the definition (no scale holds a non-finite
  value), with a mutant restoring the raise failing it by name. For the new issue: present its
  text before filing."
- **The long runs:** "1. When you stop, show the re-timing, the planned order (volume's floor
  binades first, then the rest of volume, then env_1_delay, then the sweep) and the stop
  conditions. Also say whether env_1_delay needs the direct count at all for this change: the
  rule being changed is to_preset's third branch, so state which methods can differ from main on
  the envelope group and count only those, or the whole record if you cannot rule a method out."
- **The sample:** "2, and one addition: the "double below and above a held display" draws, taken
  at float32 bit patterns so every exponent is reached, run on every continuous group, curved
  ones included, not only the linear ones. If a curved group cannot take them, say why and what
  stands in. The transcript labels each part a sample with its size, generator and seed, labels
  the floor's 23,726,567 doubles a count, and reports per group how many displays changed against
  main and that every changed one is now a held preset with the normalized value sent unchanged."
- **The indexed check**, told the final review was not posted and is not in the repository: "1.
  shape.md records that the citation was to an unposted review and what was checked instead. The
  count's transcript says why the two totals differ (398,563 calls across 351 records against
  371,476 whole numbers on 21 distinct scales), so neither figure is mistaken for the other."
- **Finding 3**, told the mutant cannot be shown passing on `main` and failing here: "1. The
  transcript says in a sentence per run what a pass or a fail means there: main's load test
  failing because its expected value followed the mutant, this branch's passing because Vital's
  held value did not change, and this branch's unit tests failing by name because they own
  _landing. shape.md records that the form I asked for could not be shown and why."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`,
  `base/process/ownership`, `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and
  `vital/plugin-state`. Snapshot in `standards.md`, base at `e31f7db`.

## Decisions

1. **The scope is issue #16**, whole
   (https://github.com/fromtheoutfit/patchbay-vital/issues/16), with its six carried findings.
   The issue wins over the prompt that started the spec. Neither of #8's questions is decided.
2. **One rule with one exception replaces the three branches** (the final review's finding 10):

   ```python
   preset = min(max(curve.to_preset(display), scale.minimum), scale.maximum)
   if scale.kind == "indexed":
       preset = _round_half_away(preset)
   held = _landing(scale, preset)[1]
   if held != preset and curve.to_display(held) != display:
       other = next_float32(preset, math.copysign(math.inf, preset - held))
       if curve.to_display(other) == display and scale.holds(other):
           return other
   return held
   ```

   - The condition is `main`'s first branch negated, so on a linear scale only the last line's
     value changes, by reading.
   - The exception stays. It is the 308,386 `volume` values of issue #15, where what a set holds
     shows a display a double off and the float32 on the other side shows it.
   - Where neither candidate shows the display, the result is `held`, Vital's own rounding.
   - **No valid scale returns an unheld preset.** `held` is the scale's value at `_landing`'s
     normalized value, which is in [0, 1] for a preset inside the scale (the fifth review's
     `verification/guards.txt`); `other` is returned only where `scale.holds` says so.
3. **The indexed line goes through the set path**, the owner's answer.
   - On the committed map no value changes, counted in full
     (`verification/indexed-count.txt`).
   - On a scale wider than its float32s the result is what a set of the nearest whole number
     holds. At the unit test's value that is the nearest whole number the scale holds, 16777215
     for 16777216. A caller who asks for the bound's display gets a preset displayed one below
     it, and `get` after the set shows that display, not the one asked for.
   - **The owner's third point cited what PR 14's final review checked for the indexed
     stepping. That review was not posted to the pull request and is not in the repository.**
     Checked instead, for all 351 indexed records: `parameters.json` at one blob in both trees,
     so the labels and choices are the same; and `to_preset`, `to_normalized` and
     `from_normalized` of it equal to `main`'s on every whole number, so the host is sent the
     same value and `get` shows the same display.
4. **The pinned arbitrary displays are a third set of `tests/data/pinned-values.txt`,**
   `tempo_displays`, on `beats_per_minute`: 216.85141355537831, the issue's example, where what a
   set holds is the float32 above the curve's, and 58.843714737570515, where it is the one
   below. `vital/measures.md` already says a pinned value is written once. A display is a double,
   so each reader's float32 check stays on the two normalized sets.
5. **The carried findings:**

   | # | On this tree | Outcome |
   |---|---|---|
   | 2 | True in its cause: `_what_a_set_holds` calls `_landing` through `scale.to_normalized`. Its last claim is false: both named scenarios already fail a test by name | `_what_a_set_holds` from primitives |
   | 3 | True | The load test's value from the `Fraction` quotient and the forward scale |
   | 5 | True | The integration reader fails by name on an empty set or a normalized value outside [0, 1] |
   | 6 | True, and reached inside `to_preset` on a made-up record, not by the curve the reviewer names | `holds` answers False for a non-finite value |
   | 8 | True | Declined by the owner; the timing recorded above as information |
   | 9 | True at `tests/integration/test_vital_plugin.py:194`. Its second claim, unit tests reading the file more than once, was checked and is not true | That read hoisted; no fixture |

   **Finding 3's transcript is not in the form the owner first asked for,** a mutant passing on
   `main`'s tests and failing by name on this branch's. The load test compares Vital with an
   expected value. On `main` that value is computed with the shipped `to_normalized`, so under a
   `_landing` mutant it follows the mutant and the test fails, though Vital holds what it held.
   On this branch the value comes from primitives, so the test passes: the observation does not
   depend on `_landing`. The mutant is failed by name by this branch's unit tests, which own
   `_landing`. The transcript says so, a sentence a run.
6. **Found beside finding 6 and not fixed here:** the scale's `to_normalized` and `to_preset`
   on a non-finite value, and a scale whose span overflows. One new issue, its text presented to
   the owner before it is filed. Presented on 2026-11-15 and approved as drafted ("File as
   drafted"): https://github.com/fromtheoutfit/patchbay-vital/issues/18.
7. **A test's expected value comes from primitives:** `Fraction`, `round_to_float32`, `fma32`
   or the forward `scale.to_preset`, `next_float32` and the curve. Never
   `MappedParameter.to_preset` or `to_normalized`, `NormalizedScale.to_normalized`, `holds` or
   `_landing`.
8. **Docstrings cite transcripts by path, not by number,** so `parameters.py` and the test
   modules are final before the long runs read them. The numbers are in this file, the CHANGELOG
   and the standard.
9. **No gate file changes, and the negative harness is not rerun.** No file is added, removed or
   renamed under `scripts`, `src`, `tests` or `agent-os/standards`: `pinned-values.txt` gains a
   set, and is not a new file (`base/process/verification-gate.md`).

### The owner's word for the long runs

Asked on 2026-11-14 with the re-timing on the run's own pools, the order, the stop conditions
and which of the envelope count's calls can differ. In the owner's words: "1. Start. Besides the
estimate stop: any difference from main outside the values the rule is meant to change stops the
run at once, as the prompt says. Report the floor binades as soon as they finish, in the
transcript, so the first result is readable before the rest completes. Each transcript prints its
tree and the machine before and after."

- **Chosen:** `volume` with the fifth review's five columns, `env_1_delay` on the two methods
  that can differ, then the sweep; a stop on an estimate past 5 hours a record.
- **Which calls can differ on the envelope group, shown and not argued**
  (`verification/direct-count.txt`, section 6). Both trees' `parameters.py` and `float32.py` are
  parsed, docstrings dropped, and each function's statements compared: of 48, 46 are the same,
  and the two that differ are `MappedParameter.to_preset` and `NormalizedScale.holds`. Each of
  the count's five calls is followed through the source to every function it can reach.
  `scale.to_preset(r)`, `record.from_normalized(r)` and `scale.to_normalized(P0)` reach only
  functions with `main`'s statements, so they cannot differ. `record.to_preset(D0)` and
  `record.to_normalized(D0)` reach the two changed ones. `to_preset` is not ruled out without
  calling `main`'s: the fifth review found every envelope value kept, but on its own tree. So the
  envelope record is counted on those two methods, every value, each tree making the display
  with its own `from_normalized`.

### Where the implementation departs from the plan

- **`_a_set_lands_on`, a second helper from primitives.** Decision 7 is applied to the tests'
  preconditions as well as their expected values: `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`,
  `test_a_display_takes_what_a_set_of_the_curve_s_float32_holds` and
  `test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset` asked `scale.holds` whether a
  float32 is held, and now ask the helper. `_what_a_set_holds` is built on it. The tests whose
  subject is `holds` or `to_normalized` still call them.
- **One test the plan did not name:**
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds` runs the
  property's assertions at each pinned `volume_floor` display and the double either side of it,
  on the hand-built record and the committed one. A uniform draw over `volume`'s bounds does not
  reach those displays.
- **`test_the_pinned_values_file_holds_two_named_sets` is renamed** for its three sets.
- **The mutation transcript kept is its second run, whole.** In the first, MN1 put `return
  preset` back as the method's last line, which also undid the rule where what a set holds shows
  the display, so it failed the floor's tests too and was not `main`'s third branch. It now puts
  `return preset` back inside the exception's block alone, and fails the arbitrary displays'
  tests and no test of a held display. Every run is derandomized (`--hypothesis-seed=0`).
- **The plugin probe takes `main`'s `to_preset` from `main`'s own tree,** through a pool of two
  processes, where the plan said only that Vital holds this branch's value.
- **The sample's third part is stratified:** 16 bit patterns among the subnormals and in each
  binade from -126 to -1, with 0.0 and 1.0, so every exponent is reached on every continuous
  group, the curved and the indexed ones included. No group had to be left out. Where a scale's
  minimum is not zero, every normalized value too small to move the sum holds the minimum, whose
  display is a bound: those values give one held display, and the double past the bound is
  refused by both trees. The transcript counts the distinct held displays a group, 47,798 in all.
- **The direct count's classes** are KEPT, PLUGIN and OTHER, the fifth review's names, and FELL,
  what a set holds where it does not show the display, in place of UNHELD.
- **The sweep counts 69 groups, not the fourth review's 83.** Its 14 duplicates, records counted
  beside their groups, are left out, as the standard says a later count does. The two scripts
  were recovered from the fourth review's transcript, at the blobs its header prints, and the
  transcript shows what changed from them. A third script compares each group's table with the
  fourth review's.
- **The five short transcripts were first run before the owner asked for the machine after a run
  as well as before.** They are rerun with it after the long runs; the first runs are not kept.

## What the transcripts show

Each transcript in `verification/` opens with its date, the branch and the machine: arm64, an
Apple M4 Pro of 14 cores, macOS 26.6.2 (25G83), Python 3.12.16. Each prints the two trees it
reads before and after the run, `main` at `f533b1b` extracted with `git archive` and this
branch's work tree, every file by blob, compared with `cmp`, and the machine again after the run.
Its scripts are embedded.

**No run found a difference from `main` outside what the rule is meant to change, so none
stopped.**

- **`direct-count.txt`, a count, nothing reproduced.** Run unattended under `caffeinate -i` from
  2026-11-14 18:41 to 2026-11-15 04:15 EST. `main`'s shipped methods and this branch's, each
  imported by its own pool of processes, are called on every float32 normalized value.
  - **`volume`, five calls a value in each tree, all 1,065,353,217 values:** the held preset,
    the display, the display's preset, the normalized value a set sends and the held preset's
    normalized value are `main`'s on every one.
  - **What the rule did, read from this branch's own results:**

    | Class | Values |
    |---|---|
    | KEPT, the curve's float32, which a set holds | 1,049,283,359 |
    | PLUGIN, what a set holds, which shows the display | 15,761,472 |
    | OTHER, the exception | 308,386 |
    | FELL, what a set holds, which does not show the display | 0 |
    | UNKNOWN | 0 |

    PLUGIN and OTHER are the fifth review's two counts. Split value by value at the floor, every
    value not kept is at a held preset at or below 2 ** -43.
  - **The floor binades ran first,** -96 to -55, 352,321,536 values, and hold every value not
    kept. Their table was readable in the transcript at 20:37, before the rest, and was reported
    to the owner then.
  - **A control:** binade -56 with the exception removed in a scratch copy. 99,796 values differ
    from `main` in the display's preset and the normalized value, each counted FELL. So the
    classes are read from the result and move when the rule is wrong.
  - **The envelope group** (section 6): the 12 records have one group key in both trees, and the
    statements of 46 of the 48 functions and module values are `main`'s, as "The owner's word for
    the long runs" says above.
  - **`env_1_delay`, the two methods that can differ, all 1,065,353,217 values:** the display,
    its preset and its normalized value are `main`'s on every one, and every value is KEPT.
  - **The time it took.** The run's own timing estimated 4.25 hours wall for `volume` and 3.19
    for `env_1_delay`; they took 5.25 (18,898 s over its four passes) and 4.30 (15,479 s). The
    owner's stop at 5 hours a record was checked on the estimate, before counting. `volume` ran
    15 minutes past it in wall time, which the owner was told while it ran. The timing ran 4
    processes at once and the count 13, on a machine of 10 performance cores and 4 efficiency
    ones, so the timing does not measure the pace of 13.
- **`sweep.txt`, the reproduction's count,** labelled so, run 2026-11-15 04:15 to 05:14 EST.
  The fourth review's two scripts, recovered from its transcript at the blobs its header prints,
  with the rule's last line changed, the tests' predicate as it now reads and the pinned values
  read from the file.
  - Over every float32 normalized value of all 69 groups, 73,509,371,973 values, each group's
    table equals the fourth review's: 69 of 69, on 16 columns, its UNHELD read as FELL.
  - On the 46 linear-scale groups every value is KEPT but `volume`'s 15,761,472 and 308,386.
    FELL is 0 on every group: on a display a held preset shows, what a set holds never fails to
    show it with nothing on the other side.
  - The exact checks fail on no value. The check that the display's preset is the held one
    fails on 570,997,534, all `volume`'s, each excused by `_unnamed_by_its_display` as it now
    reads, with `_what_a_set_holds` from primitives.
  - Each group's reproduction is checked against the shipped scalar methods on 200,010 values
    first: 78 checks, no mismatch.
- **`indexed-count.txt`, a count, in full.** Every whole number of every one of the 351 indexed
  records, and every half between them, through `to_preset`, `to_normalized` and
  `from_normalized` in both trees.
  - 398,563 whole numbers called and 398,212 halves, 807 of them refused by both trees: no value
    differs from `main`'s. This branch's `to_preset` is the whole number itself on every one.
  - **Why the two totals differ:** the 351 records lie on 21 distinct scales, which hold
    371,476 whole numbers between their ends. A scale several records share is called once for
    each of them, so the calls come to 398,563. The transcript lists each scale with its whole
    numbers, records and calls.
  - Both trees list the same 351 records, each with the same id, kind, group key, choices and
    choice labels.
- **`arbitrary-displays.txt`,** each part labelled a sample, with its size, generator and seed,
  or a count. Each display goes through both trees.
  - **A, a sample:** 200,000 displays a continuous group, uniform over its bounds,
    `numpy.random.default_rng(16)`, 11,000,000 over 55 groups. 2,041,885 give another preset
    than `main`'s, on 31 groups. On every one `main`'s preset was not held, this branch's is,
    and the normalized value is the same. On 1,361,005 the new preset is the float32 next to
    `main`'s. The other 24 groups change on no display.
  - **B, a sample:** `volume`, 20,000 displays over its range. 1,085 change with
    `random.Random(8)` and 1,108 with `numpy.random.default_rng(8)`, the issue's two figures.
  - **C, a sample:** the double below and above a held display, at 2,034 normalized values a
    group, 16 float32 bit patterns among the subnormals and in each binade from -126 to -1
    (`numpy.random.default_rng(14)`) with 0.0 and 1.0, on all 55 groups: 223,740 displays.
    61,284 are past a bound and refused by both trees. Of the other 162,456, 7 change, all
    `volume`'s, each as in A.
  - **D, a count:** every double from -80, `volume`'s display at preset 0, to its display at
    2 ** -43, 23,726,567 doubles. 344,580 give another preset than `main`'s: `main`'s was not
    held and showed the display exactly; this branch's is held, and shows a display one double
    away on every one. This is what the rule costs at the floor, and what issue #8's finding 1
    weighs.
  - No changed display anywhere had a held preset on `main`, a new preset not held, or another
    normalized value (the transcript's OUT column, 0 throughout).
- **`plugin-probe.txt`.** Vital 1.6.4 at `/Library/Audio/Plug-Ins/VST3/Vital.vst3`, through the
  integration module's own `_held_after_a_set`, each set after a load of the initial state.
  - A sample: 200 displays on each of the 46 linear-scale groups, `numpy.random.default_rng(16)`,
    9,200 sets. Vital holds this branch's `to_preset` on all 9,200, and the display the host
    gives back is that preset's display.
  - 2,085 of them changed from `main`'s `to_preset`, taken from `main`'s own tree. `main`'s was
    unheld on each, and Vital held it on none.
  - At the two pinned `tempo_displays`: `main` gave 3.6141903400421143 and 0.9807285666465759,
    this branch gives 3.6141905784606934 and 0.9807285070419312, and Vital holds those.
- **`mutation.txt`.** Scratch copies, one mutant each, derandomized, with the tests that fail
  and the exit status.
  - **The rule's own.** MN1, `main`'s third branch put back: 11 tests fail, each at a display no
    held preset shows, and no test of a display a held preset shows; the two Hypothesis
    properties alone catch it, on 6 of their cases. MN2, the indexed line as `main` has it: only
    `test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds` fails. MN3, `holds`
    without its guard: only `test_a_scale_holds_no_value_that_is_not_finite` fails.
  - **The sixth review's code mutants, rerun on the rule as it reads:** each fails but M8b, the
    exception tried where the curve's float32 is held too, which passes and is equivalent: a
    held float32 is what a set of it holds, so the exception's first condition already fails.
  - **Findings 2 and 3, one section.** ML3, a `_landing` that keeps the step's landing where no
    normalized value lands on a preset:
    - on `main`'s tree and tests it passes the property, and 3 tests of literals fail;
    - on this branch's it fails 11 tests by name, the property among them;
    - with Vital, `main`'s load test fails, because its expected value followed the mutant, and
      this branch's passes, because Vital's held value did not change and the expected value no
      longer comes from `_landing`.

    ML1 and ML2, the reviewer's two scenarios, each fail a test by name on `main` already, so
    the finding's last claim is not true.
  - **Finding 5.** MG1, the four `volume_floor` lines deleted: `main`'s three integration tests
    that read the file pass, their loops running nothing, and this branch's four fail by name,
    naming the file and the empty set. MG2, a normalized value of 1.5: on `main` one test fails
    downstream and two pass; this branch's four fail at the reader, naming the file and the line.
  - **The file's readers.** ME, MF, MF2 and MF3, a missing file, a value that is not a float32,
    an unknown set and a display that is not finite: every test reading the file fails by name,
    in both modules.
- **`cost.txt`,** information, not evidence: two passes, µs a call over 1,000 displays, `main`
  against this tree (the second pass's figures).
  - `volume` is unchanged: `to_preset` 15.5 and 15.6, `to_normalized` 27.4 and 27.7.
  - `polyphony`, an indexed record: `to_preset` 3.5 and 15.3, `to_normalized` 15.3 and 26.6,
    since the whole number is landed like any float32.
  - The 903 records at their defaults: 13.2 ms and 14.8.
  - Finding 8's form, `_landing` calling `fma32` itself rather than narrowing a value that is
    already a float32, is declined by the owner; its timing is under "What was checked while
    shaping".

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing
  on either side". After this spec the preset the map gives for a display is one the plugin
  holds after a set of it.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — a property's exception from primitives; a repository file read from
  pytest's root; the pinned values run through the property's own helper.
- `base/process/verification-gate` — the gate unchanged; its record; when the harness reruns.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request; issues written without
  attribution.
- `vital/parameter-map` — the rule, the fix-counting rule and what is counted or sampled.
- `vital/measures` — what Vital holds after a set; the pinned values' one file.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load test, whose expected value changes its source.

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
all six steps, 521 tests passed and none skipped, Vital installed. The record is
`verification/gate-run.txt`: the date and the branch on its first lines, the tree before and
after by blob, compared with `cmp`, and the machine before and after. It ran once, last, after
the retrospective's edits. Written after it: this paragraph, and the upstream issues' numbers
below. No gate file changed and no file was added, removed or renamed under `scripts`, `src`,
`tests` or `agent-os/standards`, so the negative harness was not rerun.

**Docs (step 7):** checked on 2026-11-15, each against the shipped code.
- `src/patchbay_vital/parameters.py`: the module docstring's rule sentence and the docstrings of
  `to_preset`, `to_normalized` and `NormalizedScale.holds` read as the code does. They cite this
  spec's transcripts by path, and each path exists in `verification/`.
- `tests/unit/test_parameters.py` and `tests/integration/test_vital_plugin.py`: the docstrings of
  the tests and helpers changed say what they now assert and where their expected value comes
  from.
- `tests/data/pinned-values.txt`: its header names the third set, says its values are displays,
  doubles, and where each came from.
- `README.md`: the `tests/` paragraph says `pinned-values.txt` holds the normalized values and
  the displays.
- `CHANGELOG.md`: issue #15's entry said a display no preset shows keeps the curve's float32, in
  two sentences. Both now say it kept it until issue #16's fix, the entry above it. That entry's
  counts of "the rule's third branch" are left: they are counts of that tree.
- `git grep` outside `agent-os/specs/` for "third branch", "two named sets" and the two renamed
  tests: what is left is in `agent-os/standards/vital/`, the retrospective's below, and one
  docstring that names the old test as history.
- `CLAUDE.md` and `agent-os/product/`: nothing there names what changed.

**Version (step 8):** recorded under `[Unreleased]` in `CHANGELOG.md`, the first entry of
`### Fixed`. No release is cut: the version in `pyproject.toml` stays 0.0.1.

## Standards Retrospective

Step 9, always last. Written on 2026-11-15 from the shipped diff and the transcripts, and its
own change set: `agent-os/standards/vital/parameter-map.md`, `agent-os/standards/vital/measures.md`
and `agent-os/standards/index.yml`. Every edit was drafted on a scratch copy, presented to the
owner on 2026-11-15 and approved before it was made: the owner chose all three,
"vital/parameter-map.md, vital/measures.md, index.yml, vital: entries".

**1. A pattern no standard covered.** Three, added to `vital/parameter-map.md`:
- **A claim over values that cannot be enumerated is sampled and called a sample,** with its
  size, generator and seed, and counted where a range's doubles can be enumerated. Verified
  against `verification/arbitrary-displays.txt`, whose parts A, B and C are labelled samples and
  whose part D, `volume`'s 23,726,567 doubles at its floor, a count.
- **A count calls only what can differ, and shows which,** by parsing both trees and following
  each call to every function it reaches. Verified against `verification/direct-count.txt`,
  section 6, and the script it embeds, `envelope_group.py`.
- **A count's cost is timed as the count will run,** and a stop on a budget is checked against
  the clock. Verified against `verification/direct-count.txt`: section 1 estimates 4.25 hours
  for `volume` from 4 processes, and its four passes took 18,898 s with 13.

**2. A standard that was wrong or stale.**
- `vital/parameter-map.md`:
  - The rule read as three branches, the third keeping the curve's float32. It now reads as the
    code does: what a set holds, with one exception. Verified against
    `MappedParameter.to_preset`.
  - "The third branch" said the branch was kept and held by a test. It is replaced by "An
    arbitrary display", with the tests, the sample, the floor's count and the probe that hold
    it. Verified against `test_an_arbitrary_display_takes_what_a_set_of_it_holds`,
    `test_any_display_in_range_maps_to_a_preset_a_set_of_it_holds`,
    `test_every_committed_record_maps_any_display_to_a_preset_a_set_of_it_holds`,
    `verification/arbitrary-displays.txt` and `verification/plugin-probe.txt`.
  - "An indexed scale takes no branch" is replaced by "An indexed scale", which goes through
    the set path. Verified against `to_preset`,
    `test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds` and
    `verification/indexed-count.txt`.
  - `_what_a_set_holds` was described as working from the scale's `to_normalized`. It works
    from primitives. Verified against the helper, `_a_set_lands_on`, `_nearest_quotient` and
    ML3 in `verification/mutation.txt`.
  - `holds` answering False for a value that is not finite is added beside the exception's
    `holds` check. Verified against `NormalizedScale.holds`,
    `test_a_scale_holds_no_value_that_is_not_finite` and MN3.
  - "A rule's branches are each counted" said the third branch is held by a test. It says the
    branch is gone.
  - Issue #16's direct count and the sweep's rerun are recorded beside the fifth and fourth
    reviews'. Verified against `verification/direct-count.txt` and `verification/sweep.txt`.
- `vital/measures.md`:
  - What Vital holds after a set of an arbitrary display is added. Verified against
    `test_an_arbitrary_display_set_through_the_host_holds_the_map_s_preset` and
    `test_a_value_set_through_the_host_is_the_one_the_state_holds`.
  - The expected value never comes from the method a test holds. Verified against the
    integration module's `_nearest_quotient` and its load test, and ML3.
  - The pinned file's line is `<set> <value> <name>`, a value a float32 normalized value or, in
    a set of displays, a finite double. Verified against `tests/data/pinned-values.txt` and both
    modules' `_pinned`.
  - The integration reader fails by name on an empty set and on a normalized value outside
    [0, 1]. Verified against its `_pinned`, and MG1 and MG2.

**3. A deliberate deviation.**
- **Deviation, not a standard change:** `base/process/standards-retrospective.md` says the
  approved proposals become one issue. By the owner's word each is revised into the open issue
  it refines, in place, as the retrospectives of 2026-11-11 to 13 did for #39 and #40, so a rule
  stays in one issue.
- **Deviation, not a standard change:** the owner's stop was 5 hours a record, and `volume`'s
  count took 5.25. The stop was checked on the estimate alone. The owner was told while it ran,
  and the standard now says to check the clock.

**4. Pointers that moved.**
- `test_an_arbitrary_display_keeps_the_curve_s_float32` is
  `test_an_arbitrary_display_takes_what_a_set_of_it_holds`, and
  `test_the_pinned_values_file_holds_two_named_sets` is
  `test_the_pinned_values_file_holds_three_named_sets`. Both standards name the new ones.
- The six new tests and `_nearest_quotient` are added to the standards' "Verified against"
  lists, with this spec's transcripts.

`agent-os/standards/index.yml`: the `vital:` descriptions of `parameter-map` and `measures` are
kept in step with the two edits. The `base:` section is the sync's and is not touched.

**Not proposed for base:** the counting, sampling and timing rules stay project standards. The
owner declined the counting rule as a base one on 2026-11-11, until a second package needs it
(fromtheoutfit/patchbay-standards#39).

Proposals sent upstream: #40, #42 and #38, revised in place.

Those are fromtheoutfit/patchbay-standards#40, #42 and #38, each revised on 2026-11-15 after the
gate's clean run, with a "Revised 2026-11-15" paragraph. No new issue was filed.

### Standards retrospective (proposed, base)

Presented to the owner on 2026-11-15, multi-select, and all three approved. In the owner's
words: "1, 2 and 3, each revised into its open issue in place with a "Revised 2026-11-15"
paragraph: the no-shared-code rule into #40's proposal 2, the empty-set rule into #42 with its
evidence updated, and the machine into #38. No new issue. Filed only after the gate is clean; if
it is not, stop and present. shape.md's line reads: Proposals sent upstream: #40, #42 and #38,
revised in place."

Their wording was checked against the open upstream issues #38, #39, #40 and #42 before they were
presented.

- `base/testing/tests.md`, "Inside a test" (no shared code) — a test's expected value shares no
  code with the method it holds: a sibling public method that runs the same private function is
  not a primitive. #40's proposal 2 says the value is worked out "from the primitives the code
  under test is built on", and `_what_a_set_holds` did so through the scale's `to_normalized`,
  which lands through `_landing` as `to_preset` does. A `_landing` that kept a missed step
  passed the property, and moved an integration test's expected value with it. Verified against
  `tests/unit/test_parameters.py` (`_what_a_set_holds`, `_a_set_lands_on`, `_nearest_quotient`),
  `tests/integration/test_vital_plugin.py` (`_nearest_quotient`,
  `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`) and
  ML3 in `verification/mutation.txt`. Proposed, not applied;
  revised into fromtheoutfit/patchbay-standards#40, its proposal 2, in place.
- `base/testing/tests.md`, "Inside a test" (an empty set fails) — a reader of a file of test
  values fails by name on a set with no value, and on a value outside the range the tests use
  it in, so a loop over the file's values cannot pass by running nothing. With it, #42's
  evidence is updated: the file holds nine values in three named sets, one of displays, which
  run through a test of their own. Verified against `tests/integration/test_vital_plugin.py`
  (`_pinned`), `tests/unit/test_parameters.py`
  (`test_the_pinned_values_file_holds_three_named_sets`,
  `test_every_pinned_value_comes_back_on_every_record`), `tests/data/pinned-values.txt` and MG1
  and MG2 in `verification/mutation.txt`. Proposed, not applied; revised
  into fromtheoutfit/patchbay-standards#42 in place.
- `base/process/verification-gate.md` (the machine) — a kept transcript prints the machine
  before and after the run as well as its tree, where its result is a time or depends on the
  machine. Verified against this spec's seven transcripts and its gate record, each with its two
  machine lines, `verification/direct-count.txt` and `verification/cost.txt` among them.
  Proposed, not applied; revised into fromtheoutfit/patchbay-standards#38, its proposal 2, in
  place.
