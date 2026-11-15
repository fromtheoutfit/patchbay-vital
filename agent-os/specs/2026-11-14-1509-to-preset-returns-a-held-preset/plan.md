# Issue #16: `MappedParameter.to_preset` always returns a held preset

- **Spec folder:** `agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`
- **Branch:** `refactor/16-…`, at `f533b1b`, which is `main`. The old tree is `main` at `f533b1b`.
- **Shaped** 2026-11-13 to 14 in plan mode with `/agent-os:shape-spec`; eight questions in two
  rounds.

## Context

`MappedParameter.to_preset` keeps the curve's float32 for a display no held preset shows (its
third branch). That float32 need not be one the scale holds, so a model that stores it disagrees
with what Vital holds after a set of `to_normalized(display)`. Issue #16 is the scope: the rule
returns what a set of the display's float32 holds, with the float32 on its other side only where
that alone shows the display. It runs before #8 and decides neither of #8's questions (the nearer
held neighbour; whether `VitalInstrument.set` keeps a stored value).

## Checked while shaping

Read-only, in memory, against `f533b1b`: the new rule compiled from the shipped source with the
lines below changed, nothing written.

- **The rule reproduces the issue's sample:** the same preset and normalized value on 207,000
  held displays (3,000 a group, seed 14); a different preset on 1,085 of `volume`'s 20,000
  (`random.uniform`, seed 8) and 1,108 with `numpy.random.default_rng(8)`, the normalized value
  unchanged.
- **Arbitrary displays, 20,000 a continuous group, `default_rng(16)`:** 204,233 of the 920,000
  on linear scales change (22%), on 31 of the 46 linear-scale groups, from 4.25%
  (`lfo_1_frequency`) to 75% (`lfo_1_smooth_time`). Every changed one was `main`'s unheld curve
  float32 and is now held; the normalized value is unchanged on all 1,100,000. The held preset is
  next to `main`'s on 136,355 and further on 67,878 (up to 922 float32 steps, `chorus_feedback`).
- **`volume`'s floor:** of 200,000 sampled doubles from -80 to the display at 2 ** -43
  (23,726,567 in all), 2,864 are shown by no held preset. `main` gave an unheld float32 that
  showed the display; the rule gives a held one that does not.
- **Indexed line through the set path:** `to_preset`, `to_normalized` and `from_normalized` of it
  equal `main`'s on every whole number of all 351 indexed records, 398,563 calls (371,476 whole
  numbers over the 21 distinct scales).
- **A made-up indexed scale, -1 to 2 ** 24:** `main` gives 16777216 for the bound's display,
  unheld; the rule gives 16777215, held, normalized 1.0.
- **Finding 6's reach:** scale 2 ** 103 to the largest float32, linear curve, display infinity:
  the record validates and `to_preset` raises `OverflowError` on `main`.
- **Finding 2's mutant** (a miss keeps the step's landing): passes the property with the helper
  as shipped, fails it and `test_every_pinned_value_comes_back_on_every_record` with the helper
  from primitives.
- **Timing, 200,000 values, one process:** `volume` 81.5 µs (`main`) and 80.6 (new);
  `env_1_delay` 79.4 and 78.6. Finding 8's form: 65.7 and 64.3, the same five values.
- **No caller in `src/`** calls `MappedParameter.to_preset` or `to_normalized`.

## Shaping answers, in the owner's words

- **The indexed line:** "2. Shown, not argued:
  - Every one of the 371,476 whole numbers on the 21 indexed scales gives the same value as
    main, by calling main's shipped method and this branch's directly; this is small enough to
    count in full, so it is counted, not sampled.
  - A unit test on a constructed indexed scale wider than 2 ** 24 holds the case the change is
    for, its expected value worked out from primitives, with a mutant that restores the old line
    failing it by name. shape.md says what the result means there: the nearest whole number the
    scale can hold, and what a caller sees when that is not the one asked for.
  - The choice labels and get/set of every committed indexed parameter are unchanged, as PR 14's
    final review checked for the indexed stepping."
- **Test findings:** "2, 3, 5 and 9. For 2 and 3: the _landing mutant that passes today is shown
  passing on main's tests and failing by name on this branch's, in one transcript. For 9:
  shape.md records the finding's second claim (unit tests reading the file more than once) as
  checked and not true."
- **Code findings:** "1 and 3. Finding 8 is declined by the owner: no value changes, the cost is
  not a concern (the fast path was declined in PR 14 for the same reason), and it would widen
  what the direct count has to stand behind; shape.md records the timing as information. For 6:
  the unit test's expected value is stated from the definition (no scale holds a non-finite
  value), with a mutant restoring the raise failing it by name. For the new issue: present its
  text before filing."
- **Long runs:** "1. When you stop, show the re-timing, the planned order (volume's floor binades
  first, then the rest of volume, then env_1_delay, then the sweep) and the stop conditions. Also
  say whether env_1_delay needs the direct count at all for this change: the rule being changed
  is to_preset's third branch, so state which methods can differ from main on the envelope group
  and count only those, or the whole record if you cannot rule a method out."
- **The sample:** "2, and one addition: the "double below and above a held display" draws, taken
  at float32 bit patterns so every exponent is reached, run on every continuous group, curved
  ones included, not only the linear ones. If a curved group cannot take them, say why and what
  stands in. The transcript labels each part a sample with its size, generator and seed, labels
  the floor's 23,726,567 doubles a count, and reports per group how many displays changed against
  main and that every changed one is now a held preset with the normalized value sent unchanged."
- **The indexed check:** "1. shape.md records that the citation was to an unposted review and
  what was checked instead. The count's transcript says why the two totals differ (398,563 calls
  across 351 records against 371,476 whole numbers on 21 distinct scales), so neither figure is
  mistaken for the other."
- **Finding 3:** "1. The transcript says in a sentence per run what a pass or a fail means there:
  main's load test failing because its expected value followed the mutant, this branch's passing
  because Vital's held value did not change, and this branch's unit tests failing by name because
  they own _landing. shape.md records that the form I asked for could not be shown and why."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. Standards beside the core five:
  `base/testing/tests`, `base/process/verification-gate`, `base/process/standards-retrospective`,
  `base/process/standards-index`, `base/process/ownership`, `vital/parameter-map`,
  `vital/measures`, `vital/preset-tests`, `vital/plugin-state`. Base at `e31f7db`.

## Decisions

1. **The scope is issue #16**
   (https://github.com/fromtheoutfit/patchbay-vital/issues/16), whole, with its six carried
   findings. The issue wins over the prompt. Neither of #8's questions is decided.
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

   - The condition is today's first branch negated, so on a linear scale only the last line's
     value changes, by reading.
   - The exception stays: it is the 308,386 `volume` values of issue #15.
   - Where neither candidate shows the display, the result is `held`, Vital's rounding.
   - **No valid scale returns an unheld preset.** `held` is the scale's value at `_landing`'s
     normalized value, which is in [0, 1] for a preset inside the scale; `other` is returned only
     where `scale.holds` says so.
3. **The indexed line goes through the set path** (the owner's answer). On the map no value
   changes, counted in full. On a scale wider than its float32s the result is what a set of the
   nearest whole number holds: at the unit test's value the nearest whole number the scale holds,
   16777215 for 16777216, so a caller who asks for the bound's display gets a preset displayed
   one below it. shape.md says so, and that the citation of PR 14's final review was to an
   unposted review, with what was checked instead.
4. **The pinned arbitrary displays are a third set of `tests/data/pinned-values.txt`,**
   `tempo_displays`, on `beats_per_minute`: 216.85141355537831 (the issue's example, held above
   the curve's float32) and 58.843714737570515 (held below). `vital/measures.md` already says a
   pinned value is written once. A display is a double, so each reader's float32 check stays on
   the two normalized sets. No file is added, so the negative harness is not rerun.
5. **Carried findings:**

   | # | On this tree | Outcome |
   |---|---|---|
   | 2 | True in its cause. Its last claim is false: both named scenarios already fail a test by name. | `_what_a_set_holds` from primitives |
   | 3 | True | The load test's value from the `Fraction` quotient and the forward scale. The form the owner asked for cannot be shown; shape.md says why |
   | 5 | True | The integration reader fails by name on an empty set or a normalized value outside [0, 1] |
   | 6 | True, and reached inside `to_preset` on a made-up record, not by the curve the reviewer names | `holds` answers False for a non-finite value |
   | 8 | True | Declined by the owner; the timing recorded as information |
   | 9 | True at `test_vital_plugin.py:194`. Not true of the unit module: no unit test reads the file twice | That read hoisted; no fixture |

6. **Found beside finding 6, not fixed here:** the scale's `to_normalized` and `to_preset` raise
   built-ins on a non-finite value, and a scale whose span overflows validates and then raises.
   One new issue, its text presented before filing.
7. **A test's expected value comes from primitives:** `Fraction`, `round_to_float32`, `fma32`
   or the forward `scale.to_preset`, `next_float32`, the curve. Never `MappedParameter.to_preset`
   or `to_normalized`, `NormalizedScale.to_normalized`, `holds` or `_landing`.
8. **Docstrings cite transcripts by path, not by number,** so `parameters.py` and the test
   modules are final before the long runs read them. Numbers go in shape.md, the CHANGELOG and
   the standard.
9. **No gate file changes.** No file is added, removed or renamed under `scripts`, `src`, `tests`
   or `agent-os/standards`, so the negative harness is not rerun.

## Task 1: Save spec documentation

Create the spec folder with:

- **plan.md**: this plan.
- **shape.md**: the command's template. Its first Decision cites issue #16. It holds "Checked
  while shaping" and the shaping answers above, in the owner's words.
- **standards.md**: the full text of the 14 standards as they read now.
- **references.md**: the fifth review's `direct-count.txt` and `arbitrary-displays.txt`, the
  fourth review's `sweep.txt`, the sixth review's `floor-pass.txt`, `mutation.txt` and
  `cost.txt` (each with its scripts embedded), and the unit tests' helpers.
- **verification/**: filled by Tasks 5, 6 and 9. No visuals.

## Task 2: The rule, `src/patchbay_vital/parameters.py`

- `MappedParameter.to_preset`: the body of Decision 2. Reuses `_landing`, `_round_half_away`,
  `next_float32`, `displayed_ends`; `_landing` itself is not touched.
- `NormalizedScale.holds`: `if not math.isfinite(preset): return False` before `_landing`.
- Docstrings: the module's rule sentence (lines 13 to 25), `to_preset`'s (the rule, its one
  exception, the indexed scale, what an arbitrary display takes, #8's finding 1 still open),
  `to_normalized`'s and `holds`'s.

## Task 3: Unit tests, `tests/unit/test_parameters.py`, and the data file

- `tests/data/pinned-values.txt`: the `tempo_displays` set and its header lines.
- `_pinned`: knows the third set; `test_the_pinned_values_file_holds_two_named_sets` becomes
  three sets (4, 3 and 2 values).
- **Finding 2:** `_what_a_set_holds` works out what a set holds from `_nearest_quotient`, the
  forward scale at it and at the float32 either side, and `next_float32`; it clamps the curve's
  float32 to the scale as the rule does.
- **The characterization reversed:** `test_an_arbitrary_display_keeps_the_curve_s_float32`
  becomes `test_an_arbitrary_display_takes_what_a_set_of_it_holds`. At each `tempo_displays`
  value on `_TEMPO`: the literal (3.6141905784606934, 0.9807285070419312), equal to the helper's
  value, not the curve's float32, and held by the normalized value the map sends. Its docstring
  names #8's finding 1 as still open.
- **The property that stands in for a count:** one helper, `_assert_a_set_holds_it`, run by a
  Hypothesis test over displays within each hand-built record's bounds, one over the committed
  map, and the pinned displays:
  - the normalized value is in [0, 1] and the forward scale lands it on `to_preset`'s value;
  - on a linear scale that value is the helper's `held`, or its `other` where `other` shows the
    display and `held` does not.
- `test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken`: the display now takes the
  float32 below the maximum, what a set holds; the normalized value stays 1.0.
- **New, the indexed case:** indexed -1 to 2 ** 24 at the bound's display gives 16777215, from
  the nearest quotient and `fma32`; the scale holds it and not 16777216.
- **New, finding 6:** a scale holds no infinity and no NaN, stated from the definition; and the
  made-up record whose `to_preset(inf)` raised gives the float32 below its maximum.

## Task 4: Integration tests, `tests/integration/test_vital_plugin.py`

- **Finding 5:** `_pinned` fails by name on a set with no value and on a normalized value outside
  [0, 1]; it knows the third set.
- **Finding 9:** the read moves above the per-record loop in
  `test_a_held_power_of_two_set_through_the_host_is_held`.
- **Finding 3:** the load test's `held` is the forward scale at the `Fraction` quotient's nearest
  float32.
- **The probe's assertion at arbitrary displays:** a new test sets each `tempo_displays` value
  on `beats_per_minute` from `initial` and holds the state's float to `to_preset`'s value, not
  the curve's float32; `test_a_value_set_through_the_host_is_the_one_the_state_holds` gains one
  arbitrary display a kind, scale and curve. Reuses `_held_after_a_set`, `_one_of_each`,
  `_floats`.

## Task 5: The short evidence

Each transcript: date, branch and machine; the trees before and after, by blob, compared with
`cmp`; its scripts embedded; scripts in the scratchpad, `main` extracted there with
`git archive f533b1b`; each pool importing its own tree; written outside the tree and copied in.

- **`indexed-count.txt`, a count.** Every whole number and every half of every one of the 351
  indexed records: `to_preset`, `to_normalized` and `from_normalized` of it, both trees.
  `parameters.json` at one blob. It says why 398,563 calls and 371,476 whole numbers differ.
- **`arbitrary-displays.txt`.** Each part labelled a sample, with size, generator and seed, or a
  count:
  - sample: 200,000 a continuous group, uniform over its bounds, `default_rng(16)`: 11,000,000
    over 55 groups;
  - sample: `volume`'s 20,000 at seed 8, `random.uniform` and `default_rng(8)`;
  - sample: the double below and above a held display, at 16 bit patterns in each exponent (the
    subnormals, every binade from -126 to -1) with 0.0 and 1.0, seed 14, on all 55 continuous
    groups, curved and indexed included: 223,740 displays. One past a bound is refused by both
    trees and counted so;
  - count: the 23,726,567 doubles from -80 to `volume`'s display at 2 ** -43.
  Per group: displays, changed against `main`, and of the changed: `main`'s unheld, now held
  (the forward scale lands the normalized value on it), normalized value unchanged.
- **`mutation.txt`.** Scratch copies, one mutant each, the tests that fail and the exit status:
  - the rule: the last line restored; the exception removed; `held != preset` dropped (an
    equivalent if it passes, said so); `holds(other)` dropped; the indexed line restored; `holds`
    without its guard. The sixth review's code mutants rerun on the rule as it reads.
  - findings 2 and 3, one section: the `_landing` mutant on `main`'s tests and on this branch's,
    unit and, with Vital, the load test, a sentence a run saying what its pass or fail means.
    The reviewer's two scenarios on `main`, each failing a test by name.
  - finding 5: the `volume_floor` lines deleted, and a value of 1.5, on both trees, with Vital.
- **`plugin-probe.txt`.** Vital 1.6.4: 200 seeded arbitrary displays a linear-scale group (9,200
  sets, `default_rng(16)`) and the `tempo_displays`, each from `initial` through the test
  module's `_held_after_a_set`: Vital holds `to_preset`'s value, counted a group.
- **`cost.txt`.** µs a call, `main` against this tree: `volume`, one indexed record, the 903
  records at their defaults. Information.

**Any difference from `main` outside the rule's change stops the work and is presented at once:**
a changed display where `main`'s preset was held, a new preset not held, a normalized value that
differs, a whole number that differs, or Vital holding another value.

## Task 6: Stop for the owner's word, then the long runs

**Stop and present with AskUserQuestion:**

- the run's own re-timing on its pools, 200,000 values a tree;
- the order: `volume`'s floor binades (-96 to -55), the rest of `volume`, `env_1_delay`, the
  sweep;
- the stop conditions below;
- **`env_1_delay`:** only `MappedParameter.to_preset` and, through it, `to_normalized` can differ
  from `main`. The transcript shows `scale.to_preset`, `from_normalized`, `scale.to_normalized`
  and `_landing` are the same source in both trees, and `float32.py` one blob. `to_preset` is not
  ruled out: the fifth review found every envelope value kept, but on its own tree. So the
  envelope count calls those two methods on every value, about 30 CPU-hours against 47. The same
  holds of `volume`; whether its count keeps the fifth review's five columns is asked here.

Estimate from shaping: `volume` 48 CPU-hours and about 4 hours wall with five columns;
`env_1_delay` about 30 and 2.6; the sweep about 14 and 1.4. The fifth review ran 20% over.

**At the owner's word, unattended, under `caffeinate -i`:**

- **`direct-count.txt`:** the fifth review's script, recovered from its transcript, with the
  branch read from this tree's result: kept, what a set holds and shows the display, the other
  side, or what a set holds and does not show it. A control on binade -56 with the exception
  removed in a scratch copy. The 12 envelope records' one group key.
- **`sweep.txt`:** the fourth review's two scripts, recovered from its transcript, with the last
  branch changed, the tests' predicate as it now reads and the pinned values from the file;
  labelled the reproduction's, checked on 200,010 values a group.
- **Stops:** an estimate past the budget the owner gives; any difference from `main` in any
  compared value; a value that takes what a set holds and does not show its display; a pool
  importing the wrong tree; a sweep group whose check fails or whose branch counts differ from
  the fourth review's.
- No tracked file is edited while a run is in flight.

## Task 7: Docs and Version

- `CHANGELOG.md`, `[Unreleased]`, `### Fixed`: issue #16, what changes for a caller with the
  transcripts' numbers, the indexed line, `holds`, the carried findings and finding 8 declined.
- `README.md`'s `tests/` paragraph names the third set.
- `git grep` outside `agent-os/specs/` for "third branch" and the renamed test.

## Task 8: The new issue and the standards retrospective

- **The issue of Decision 6:** its text presented, filed with `gh issue create` only on the
  owner's yes, no attribution.
- **The retrospective,** from the shipped diff and the transcripts, its own change set:
  - `vital/parameter-map.md` (the rule, the third branch's paragraph, the indexed line, what is
    counted and what is sampled), `vital/measures.md` (arbitrary displays, the third set, the
    reader's checks) and `index.yml`'s `vital:` entries: each edit presented and approved before
    it is made.
  - Base proposals under `### Standards retrospective (proposed, base)`, presented
    multi-select, their wording checked against the open upstream issues on `tests.md` (#39,
    #40, #42). Filed only after the gate is clean.

## Task 9 (final): Verification gate

1. `bash -n` on every shell script under `scripts/` as git lists them.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check`.
3. `uv run --locked ruff check --config pyproject.toml`.
4. `uv run --locked mypy --config-file pyproject.toml`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`.
6. `scripts/sync-standards.sh --check`.
7. **Docs**, recorded in shape.md.
8. **Version**, recorded in shape.md.
9. **Standards retrospective**, last, with `Proposals sent upstream:`.

`scripts/gate.sh` runs 1 to 6. `verification/gate-run.txt` opens with the date and the branch,
prints the tree before and after, and is the last thing done. Only the Results paragraph, the
upstream issue's number and the new issue's number are written after it. A step that fails is
fixed and the gate rerun from step 1.

Then print `git status --short`, list the feature's files and the retrospective's separately,
and stop. No stage, commit, push or pull request.

## Verification, end to end

- The unit suite and, with Vital at `/Library/Audio/Plug-Ins/VST3/Vital.vst3`, the integration
  module pass; each new test is failed by name by its mutant.
- `indexed-count.txt` and the floor's count show no value changed where none should; the samples
  show every changed display now held with its normalized value unchanged.
- `direct-count.txt` shows no difference from `main` on any held display; `sweep.txt` the same
  for all 69 groups, as the reproduction's.
- `plugin-probe.txt` shows Vital holding `to_preset`'s value at arbitrary displays.
- `scripts/gate.sh` exits 0, recorded in `gate-run.txt`.
