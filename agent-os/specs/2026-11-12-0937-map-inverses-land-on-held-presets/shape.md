# Issue #15 in PR 14: the Parameter Map's Two Inverses Land on Held Presets — Shaping Notes

Shaped 2026-11-12 in plan mode with this repository's customized `/agent-os:shape-spec`. Each
finding of the review was checked against HEAD (`5e284ec`) before any question, and both candidate
fixes were run against the committed map. The owner then answered four questions.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The third review of PR 14,
https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6826276826, "Review of
5e284ec" (2026-11-12 14:25Z): fifteen findings, of which the first two say the PR
records issue #15's two map defects as expected behaviour instead of fixing them. In the owner's
words, "Let's address the latest round of review on PR 14".

This spec is **issue #15's**, with issue #13 beside it in scope. It is on the same branch, so PR 14
carries it and closes both. It changes behaviour in `src/patchbay_vital/` and no gate file.
CHANGELOG entry, gate green, `verification/gate-run.txt`. No stage, commit, push or pull request
edit by an agent.

## Shaping answers

In the owner's words:

- **Scope:** "This revision is shaped as issue #15's spec: #15 is its scope beside #13, shape.md's
  first Decision cites both, and it says the owner reversed the earlier decision to keep #15
  separate and why (two review rounds spent on tests the fix removes).
  - Evidence is #15's in full, counted not sampled: the every-float32 sweep rerun on every counted
    group, showing HELD, A2 and the set path failing on no value, and that no display's to_preset
    result changes except where today's float32 is not one the scale holds. The 12,004 sample is
    not the evidence.
  - The Vital probe and integration tests rerun: Vital holds 1.0 after a set of 1.0 s, and the
    floor rows as the fix leaves them.
  - What stays: the shared-display excuse for the preset coming back, as #15 says, with its
    count. What stays open for #8: whether set keeps the stored value when the display is the one
    already shown, and the nearer neighbour for arbitrary displays. If either fix would decide
    those, stop and present.
  - The 9 exponential groups: to_preset's change applies to every record, so say what is counted
    there and what is not. Present, before running it, what the libm count of their
    curve-dependent claims would take, for the owner to start unattended or decline.
  - Removed on purpose, each named in shape.md: the power-of-two exception, the
    neighbouring-double tolerance, the two characterization tests and any row file left empty.
    The three vital standards and CHANGELOG are corrected against the shipped code, the standards
    as their own change sets."
- **The row files and the conftest:** removed, the values pinned in each test module. "Each pinned
  value carries a comment naming what it is (issue #13's value, the smallest of the former one-ulp
  landings, the floor's own, 1.0 / 0.5 / 2 ** -20 on the envelope records), written the same way
  in both modules, and shape.md says the duplication of those inputs is accepted and why the
  shared file went. For patchbay-standards#40: proposal 1 is revised in place, saying its instance
  here was removed by the fix and citing the commits on this branch where it existed, or withdrawn
  if the owner prefers; present which before editing. #39's characterization-test proposal keeps
  its evidence the same way, by commit."
- **Finding 15, the transcripts:** "3 for this run: commit the rerun in full, as the base standard
  says, and decline finding 15 here with that reason in shape.md. In the retrospective, present a
  base proposal for base/process/verification-gate.md: a harness transcript may be committed as a
  mechanical extract (its header, each case's heading and exit lines, the final count) with the
  harness file's blob hash and the exact command that regenerates the whole, where the extract is
  produced by a stated command and not written by hand. Evidence: the two transcripts on this
  branch, their sizes and how few lines differ. If approved it is filed with this revision's other
  proposals; the earlier transcripts stay as recorded until the standard changes."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`, `base/process/ownership`,
  `vital/parameter-map`, `vital/measures`, `vital/preset-tests`, `vital/plugin-state` and
  `vital/float-writer`. Snapshot in `standards.md`, base at `e31f7db`.

## What was checked while shaping

Read-only, against HEAD `5e284ec`:

- **Both candidate fixes, on the committed map.**
  - The `to_normalized` step toward the preset fixes 1,512 of the 1,512 power-of-two misses of
    the 12 envelope records, none left.
  - The `to_preset` snap to a held neighbour showing the display leaves 0 of 12,004 sampled
    volume-floor values off in the set path's display, where today's map is off on 143.
  - A sample, not the evidence (Decision 2).
- **`main`'s property** asserted `scale.to_preset(record.to_normalized(display)) == back` on every
  value: issue #13's failing assertion, which the fix makes true again.
- **`test_where_volume_s_offset_absorbs_a_preset`:** under the fix, `to_preset` of 2 ** -43's
  display is 2 ** -43 itself, so its `!= last` holds only of the curve's own float32.
- **Finding 7:** `_shares_its_display(_VOLUME, first)` is false at the float32 above 2 ** -43.
- **#8's finding 1:** `_TEMPO` at 216.85141355537831 bpm, its example, keeps the curve's unheld
  float32 under the fix, no neighbour showing that display.
- **The negative harness:** no case reads `tests/conftest.py` or the row files; case q writes its
  own `tests/unit/conftest.py`; no case pins a test count.
- **The census:** `census.py:334` calls `to_normalized` only on an indexed scale's whole steps.
- **The libm count's cost:** `math.pow` and `math.log2` take 18 ns a value each here, so the libm
  calls over every float32 normalized value of the 9 exponential groups are about 0.2 CPU-hours,
  against the "hours" earlier specs assumed. The last sweep ran 83 counts in 1,681 s on 10
  processes.

## Decisions

1. **This is issue #15's spec, beside issue #13's.**
   - #13 corrected the property below `volume`'s floor; #15 holds the map's two inverses, each
     missing a preset a set should hold. PR 14 closes both.
   - **The owner reversed the earlier decision to keep #15 separate.** The revision after PR 14's
     review moved the fix to #15, and the revision after its second review kept it there. Two
     review rounds were then spent on tests, rows and exceptions that the fix removes.
2. **The evidence is #15's in full, counted, not sampled:** the every-float32 sweep on every
   counted group, Vital's measure, and the integration tests.
3. **What stays and what stays open.**
   - The shared display's excuse of the preset coming back (A3) stays: where presets share a
     display, the display cannot say which was held.
   - Open for #8: whether `VitalInstrument.set` keeps the stored value when given the display it
     already shows (#8's finding 3), and the nearer neighbour for an arbitrary display (#8's
     finding 1). The fixes leave both: the snap fires only on a display a held neighbour shows
     exactly, and keeps today's float32 wherever the scale holds it.
4. **`to_normalized`:** the nearest float32 quotient `q`, unless `to_preset(q)` misses the preset;
   then the float32 one step toward the preset, if in [0, 1] and landing on it; else `q`. The
   scale is monotone in `r` (its span is positive), so only that side can land, and a preset no
   float32 lands on keeps `q`.
5. **`NormalizedScale.holds(preset)`:** `to_normalized`'s result is in [0, 1] and lands on it.
6. **`MappedParameter.to_preset`:** today's float32, clamped, rounded on an indexed scale; kept
   wherever the scale holds it; otherwise the float32 next to it, either side, that the scale
   holds and that shows the display exactly, the one nearer the curve's unrounded inverse where
   both do; otherwise today's float32. #8 says #15 decides which preset a set of such a display
   stores, so the tie-break is this spec's; the sweep counts how often both neighbours qualify.
7. **`float32.next_float32(value, toward)`:** the one way to step a float32, used by the fix and
   by the tests' `_shares_its_display`.
8. **The row files and `tests/conftest.py` go**, the values pinned in each test module as
   constants with a comment naming each, written the same way in both. **The duplicated inputs
   are accepted:** seven literals in two modules, each named, against a shared file whose reader,
   step helper, fixtures and format existed only to carry steps the fix sets to 0. With the steps
   gone, a row is a value, and a value is clearest beside the assertion that reads it.
9. **Finding 15 is declined for this run:** the negative harness's rerun is committed in full, as
   `base/process/verification-gate.md` says ("keeps the transcript"; "A kept transcript holds one
   run of the harness and ends on that run's count"). A base proposal for a mechanical extract is
   presented in the retrospective.

### Where the implementation departs from the plan

- **`next_float32` refuses nothing.** The plan had it raise ValueError for a value that is no
  float32; `base/python/errors.md` lets no built-in exception leave a public function, so it rounds
  such a value to the nearest float32 first, and from an infinity steps to the largest float32, as
  C's `nextafterf` does, where the plan said an infinity returns as it is. Held by
  `test_a_float32_steps_to_its_neighbour_as_numpy_steps_it` and
  `test_a_double_that_is_no_float32_steps_from_its_nearest`.
- **The curve's unrounded inverse is a module function, `_inverse(curve, display)`**, not a method
  `DisplayCurve._inverse`, so `MappedParameter.to_preset` reads it without reaching into another
  object's private member.
- **The pinned values are held by two named tests**, one per tuple, each asserting what makes its
  values the defect's (the curve's float32 unheld; the nearest quotient one float32 below the
  power), where the plan had one parametrized test; and a third direct test the plan did not name,
  `test_a_scale_holds_its_values_and_none_past_its_ends`, added so the mutation of `holds`'s
  `[0, 1]` check fails a test (Task 9).
- **`README.md` is `main`'s again.** The PR's only change to it was the sentence on the row files
  and the conftest, which went with them; `tests/data/` holds no pinned value, so the paragraph
  needs no new sentence.

## The 15 findings

| # | Finding | Outcome |
|---|---|---|
| F1 | `to_normalized` lands one float32 below a held power of two | Fixed (Decision 4) |
| F2 | `to_preset` returns a float32 the scale never holds at or below the floor | Fixed (Decision 6) |
| F3 | Under the power-of-two exception nothing bounds `shown` | The exception is removed |
| F4 | The exact set-path check replaced by a display-only one | Restored: `scale.to_preset(record.to_normalized(display)) == back` on every value |
| F5 | `env_1_delay`'s values applied to `env_3_hold` unchecked | The test asserts the two share a scale and curve first |
| F6 | The load test reads and writes with `json` | `_floats` reads; the package's `loads` and `dumps` write, `dumps(loads(initial))` asserted to be `initial` first |
| F7 | The predicate's boundary at the floor not pinned | `not _shares_its_display(_VOLUME, first)` |
| F8 | An indented comment breaks `recorded_rows` | Removed with the conftest |
| F9 | Float stepping spelled inline beside `stepped` | `float32.next_float32`, the one spelling |
| F10 | The power-of-two check written twice | Both uses removed |
| F11 | The conftest's `noqa`, `dtype` order and `stepped` fixture | Removed with the conftest |
| F12 | The conftest's import-mode reason is inaccurate, and the README repeats it | Removed; the README's `tests/` paragraph rewritten |
| F13 | `neighbours` computed on every example | Removed; the predicate is asked once, only where A3 fails |
| F14 | Function-scoped row fixtures | Removed with the conftest |
| F15 | About 50k lines of verification transcripts | Declined for this run (Decision 9); a base proposal |

## Removed on purpose

Each was there to hold today's map where #15 changes it, and goes because the fix lands:

- **The power-of-two exception**, `_lands_below_its_power_of_two`, from `_assert_comes_back`.
- **The neighbouring-double tolerance** of the set path's display.
- **The two characterization tests**,
  `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded` and
  `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`.
- **Both row files**, `tests/data/volume-floor.txt` and `tests/data/power-of-two-presets.txt`,
  whose step columns the fix sets to 0.
- **`tests/conftest.py`**, with `recorded_rows`, `stepped` and the `volume_floor`,
  `power_of_two_presets` and `stepped` fixtures, which existed to share those files.

## Open

- **#8's findings 1 and 3**, as under Decision 3.

The 9 exponential groups' curve claims, open since issue #13's spec, are counted now (below).

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing on
  either side": a set of a display the parameter shows now holds a preset that shows it, on Vital
  as in the model.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the property's one excuse, the pinned values and the removed conftest.
- `base/process/verification-gate` — the gate unchanged; its transcript; the harness rerun.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issues edited without
  attribution.
- `vital/parameter-map` — the two inverses and the round trip.
- `vital/measures` — what Vital holds after a set, compared exactly.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load test's wording and writer.
- `vital/float-writer` — the load test writes through the package's writer.

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

**Results (2026-11-12):** `verification/gate-run.txt`, three runs, on branch
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`:
the first two at `5e284ec` with the change uncommitted, on the final tree after the
retrospective's edits; the third at the owner's `f692287`, the change committed. No gate file
changed.

- **The tree's run fails at step 2**, exit 1, naming `tests/conftest.py`: "tracked but missing from
  the disk". The spec removes it and both row files, and git still tracks them, since an agent never
  stages (`base/process/ownership.md`).
- **The second run is green:** steps 1 to 6 pass, 507 tests, none skipped, the integration tests
  among them with Vital installed. As `base/process/verification-gate.md` says of a file a step
  refuses before the owner stages it, this run is on a scratch copy of the same tree, with the three
  removals staged in the copy's own index and a local clone of `../patchbay-standards` beside it.
- **The third run is the tree's own, green:** after the owner's `git rm tests/conftest.py
  tests/data/volume-floor.txt tests/data/power-of-two-presets.txt` and commits `2d2f7dc` (the
  removals), `b6a3fa4` (the feature and this folder) and `f692287` (the retrospective), steps 1 to 6
  pass at `f692287`, 507 tests, none skipped, the integration tests among them with Vital installed.
  The tree was clean, and HEAD `f692287`, before the run and after it.
- **The negative harness**, run on the same tree before the gate: `verification/gate-negative-tests.txt`,
  141 runs, 0 unexpected; case j, `verification/ci-negative-test.txt`, 3 runs, 0 unexpected.
- After the first two runs, only this file's results were written; after the third, only its
  section of `verification/gate-run.txt` and these results. No gate step reads either file.

- **Not run by the gate:**
  - **The sweep**, `verification/sweep.txt`, two sections, every float32 normalized value:
    - 83 counts, 60 groups reproduced in numpy, each of the six offset records, each of the 12
      envelope records, and HELD and NCHANGED on the 9 exponential groups, in 2,567 s on 10
      processes. Each was checked against the shipped scalar methods on 200,010 values first, with
      0 mismatches.
    - `bound!` 0 on every count. A1, HELD, A2 and SET are 0. A3 is 570,997,534, all on `volume`,
      with A3x 0. SHARE is 589,224,972, of which 18,227,438 are never consulted.
    - The fixes changed only what they should. CHANGED is 16,069,858, all on `volume`, with
      CHANGEDx 0; BOTH is 15,452,993; NONE is 0. NCHANGED is 1,512, 126 powers of two from
      2 ** -125 to 1 on each envelope record, with NCHANGEDx 0.
    - The second section, started by the owner after its cost was presented (Task 7): the 9
      exponential groups through this machine's own `pow` and `log2`. It ran on macOS 26.6.2
      (25G83) arm64, CPython 3.12.16 (uv's build, Clang 23.1.3), whose interpreter links libSystem
      1351; `pow` and `log2` resolve to one function each through libm, libSystem and the
      interpreter. 9 counts in 605 s on 9 processes. Each was checked against the shipped methods
      on 200,010 values, with 0 mismatches, and `bound!` is 0 on all 9.
    - So all 69 of the map's scale and curve groups are counted, the exponential ones on this
      machine's libm.
  - **The probe**, `verification/plugin-probe.txt`: Vital 1.6.4 through pedalboard 0.9.26 on arm64,
    through the tests' own sequences and the pinned values imported from the integration module.
    - At each floor value, Vital holds `to_preset`'s value, held by the scale, never the curve's
      float32, and its display is the one set.
    - At each power on `env_1_delay` and `env_3_hold`, Vital holds the power. The nearest
      quotient, the map's value before the fix, holds the float32 below.
    - `dumps(loads(initial))` is `initial`'s text. The load holds as observed after each of the
      four histories.
  - **The mutation**, `verification/mutation.txt`, on scratch copies:
    - M0, the tree unmutated, passes.
    - M1 (`to_normalized` reverted) fails the six power-of-two tests.
    - M2 (the snap removed) fails the hand-built property at issue #13's value, the absorption
      test and the four floor tests.
    - M3 (`holds` without [0, 1]) fails `test_a_scale_holds_its_values_and_none_past_its_ends`.
    - M5 (the snap without its display check) fails
      `test_an_arbitrary_display_keeps_the_curve_s_float32`.
    - M4 (the step in `to_normalized` without its [0, 1] check) survives, the one guard no test
      trips. On none of the map's 903 records, and on none of 200,000 constructed scales, does the
      step leave [0, 1] and land. It is kept so `to_normalized` never steps a value the host can
      set to one it refuses.
  - **The negative harness:** files are removed under `tests/`, which every case copies, so this
    branch's harness (`scripts/gate-negative-tests.sh`, HEAD's blob `578dd16`) is rerun once, every
    test but j, into `verification/gate-negative-tests.txt`, kept in full (Decision 9), and j into
    `verification/ci-negative-test.txt`. Their counts are under "The gate's run".
- **The sweep's blob of `tests/unit/test_parameters.py`:** the first section read `80aacb9`, the
  file before `test_a_scale_holds_its_values_and_none_past_its_ends` was added for mutation M3. The
  second section, the probe and the mutation read the shipped file. The added test touches neither
  `_shares_its_display` nor the pinned tuples, the only names the sweep imports.

**Issues** (read before each edit, compared with the body last read, read back after it; no
attribution):

- **#15** gains a "Revised 2026-11-12" paragraph, before its section 1: the fix lands in PR 14, its
  evidence, what was removed, what stays and what stays with #8.
- **#8** gains one before "Depends on": #15's fix is in PR 14; findings 1 and 3 stay there,
  undecided. The body's last line, an AI-attribution footer `CLAUDE.md` forbids in an issue body,
  was dropped with this edit rather than resubmitted.

**Docs (step 7):** every file changed, and every document and standard naming them, checked
against the shipped code:

- `src/patchbay_vital/parameters.py`:
  - the module docstring says a value a parameter holds comes back through display, preset and
    normalized path, the preset it came from but where presets share a display;
  - `to_normalized`, `holds` and `to_preset` state their rules, with no "issue #15 is to".
- `src/patchbay_vital/float32.py`: the module docstring names `next_float32`, and its docstring
  states its rounding of a non-float32 and its steps at zero and infinity.
- `tests/unit/test_parameters.py`:
  - the property's and `_assert_comes_back`'s docstrings state the one excuse and how it is
    consulted;
  - `_shares_its_display`'s says the preset may be another held one;
  - each new test's docstring says what it holds and what the map did before.
- `tests/unit/test_float32.py`: the module docstring names the step.
- `tests/integration/test_vital_plugin.py`:
  - the module docstring says a measured state is written with the package's `dumps`;
  - the two renamed tests and the load test say what they hold, citing this spec's probe.
- `README.md` is `main`'s, true now the row files and the conftest are gone. `CLAUDE.md` and
  `agent-os/product/` are unchanged and true.
- `tests/unit/builders.py`'s "not a conftest" reason, case q writing its own
  `tests/unit/conftest.py`, is still true.
- After the retrospective, `git grep` finds `recorded_rows`, `stepped`, `volume_floor`,
  `power_of_two_presets`, the two row files and `_lands_below_its_power_of_two` nowhere outside the
  spec folders but the CHANGELOG entry recording their removal.

**Version (step 8):** `CHANGELOG.md`'s `[Unreleased]` `### Fixed`:

- a new entry for issue #15: both inverses, `holds`, `next_float32`, the counts, the evidence
  files and what was removed;
- issue #13's entry corrected in place: the property exact on every value but the shared display,
  `_shares_its_display` in place of `_ABSORBED`, closed by #15's fix.

The behaviour changes, unreleased; the version stays 0.0.1 until a release is cut.

## Standards Retrospective

Step 9, from the shipped diff. The four questions:

1. **A pattern no standard covers:** two.
   - A fix counted by what it changed and by what it changed that it must not have (CHANGEDx,
     NCHANGEDx).
   - A count through the platform's own libm, scoped to the machine named.
2. **A standard wrong or stale:** three, each naming what the fix removed.
   - `vital/parameter-map.md`: the round trip's two exceptions, the rows and `stepped`, and the
     exponential groups called uncountable.
   - `vital/measures.md`: a row's step read by `stepped`, and a display landing off.
   - `vital/plugin-state.md`: the load at the rows of `tests/data/volume-floor.txt`.
3. **A deliberate deviation:** one, recorded under Decision 9: finding 15 declined for this run, the
   harness kept in full as the base standard says, with a proposal to change it.
4. **A pointer moved:**
   - the row files and `tests/conftest.py` are gone;
   - two integration tests are renamed;
   - the evidence is this spec's `verification/`.

   Every standard naming them is updated.

The project edits, approved by the owner on 2026-11-12 with AskUserQuestion, listed apart from the
feature's files. Each standard is its own change set with its entry of `index.yml`'s `vital:`
section. The `base:` section is untouched (`scripts/sync-standards.sh --check` passing).

- **`agent-os/standards/vital/parameter-map.md`, with the `parameter-map` entry.** In the owner's
  words: "the 570,997,534 excused is stated with the mechanism in plain words (the exact check runs
  first; the excuse is consulted only where it fails), and the libm claim is scoped to the machine
  named."
  - The header gains this spec.
  - The normalized bullet gains `to_normalized`'s step and `holds`.
  - The round-trip bullet is restated, in three parts:
    - every claim exact on every value but the display's preset where presets share a display;
    - `to_preset`'s held-neighbour rule;
    - the exception in plain words, with its counts and its never-consulted values on the
      exponential groups.
  - The counting rule covers all 69 groups, the exponential ones through this machine's libm,
    named, and a fix counted by what it changed and must not have.
  - Verified against `parameters.py`, `float32.py`, `tests/unit/test_parameters.py`,
    `tests/unit/test_float32.py`, both integration tests and `verification/sweep.txt`.
- **`agent-os/standards/vital/measures.md`, with the `measures` entry.**
  - The held value is compared exactly and its display with the display set.
  - The pinned constants are written alike in both modules.
  - The probe imports them and `_held_after_a_set`.
  - The header gains this spec.
  - Verified against `test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
    `test_a_held_power_of_two_set_through_the_host_is_held` and `verification/plugin-probe.txt`.
- **`agent-os/standards/vital/plugin-state.md`, with the `plugin-state` entry.** In the owner's
  words: "still an observation with its machine and Vital version, claiming no cause."
  - The load is observed at `_VOLUME_FLOOR`'s values.
  - Its state is written with `dumps`, which gives the starting state back byte for byte, and
    read with `_floats`.
  - Verified against
    `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given` and
    `verification/plugin-probe.txt` section 2.

Proposals sent upstream: fromtheoutfit/patchbay-standards#41; #39, revised in place; #40, revised in place, its proposal 1 withdrawn by owner, 2026-11-12

### Standards retrospective (proposed, base)

Each presented to the owner on 2026-11-12 with AskUserQuestion. (a), (b) and (c) approved; #40's
proposal 1 withdrawn.

- (a) `base/testing/tests.md`, #39's rule.
  - Its instances were removed by the fix as the rule intends, cited by commit (`88d438d`,
    `412b21a`, `10823c8`).
  - It gains a limit, in the owner's words: "a defect found in a spec, whose fix is known,
    checked, inside the files that spec may change and decides no other open issue's question, is
    fixed in that spec, with the owner widening the issue's scope in place; a characterization
    test is for a behaviour whose fix is not yet known or belongs to another issue's decision. A
    fix in a gate file still takes its own gate spec."
  - Evidence: PR 14's third review, findings 1 and 2, and Decision 1 here.
  - Proposed, not applied; filed as fromtheoutfit/patchbay-standards#39, revised in place.
- (b) `base/testing/tests.md`, #40's proposal 2.
  - Its first instance, `_lands_below_its_power_of_two`, was removed by the fix.
  - `_shares_its_display` stays as a permanent exception, so its docstring rule becomes "names
    the issue that removes it, or says why it stays".
  - Its counts after the fix: A3 570,997,534, A3x 0.
  - Verified against `tests/unit/test_parameters.py` and `verification/sweep.txt`.
  - Proposed, not applied; filed as fromtheoutfit/patchbay-standards#40, revised in place.
- #40's proposal 1, values two test directories share in one recorded file read through
  `tests/conftest.py`, with its shared helper.
  - Its only instance (`412b21a`, `10823c8`) was removed by the fix, and this repository now pins
    the values in each module on purpose.
  - Withdrawn by owner, 2026-11-12. The withdrawal is marked in #40 in place, with a "Revised
    2026-11-12" paragraph naming the commits and saying it may be filed again when a package holds
    recorded values two test directories share.
- (c) `base/process/verification-gate.md`: a harness transcript may be committed as a mechanical
  extract, with the harness blob and the exact command that regenerates the whole.
  - Evidence: the branch's three harness transcripts of blob `578dd16`, 16,790, 16,900 and 16,901
    lines. The first two differ on 4,398 lines and the second and this spec's on 6,655, chiefly
    ruff format's diff of the changed test files, uv's timings and pytest's progress. Their
    extracts, the 166 heading and exit lines and `141 runs, 0 unexpected`, are identical.
  - Proposed, not applied; filed as fromtheoutfit/patchbay-standards#41.
