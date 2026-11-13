# Revision after PR 14's Sixth Review — Shaping Notes

Shaped 2026-11-13 in plan mode with this repository's customized `/agent-os:shape-spec`. Each
finding of the review was checked against HEAD (`e852aac`) before any question, read only, and the
owner then answered nine questions in three rounds.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The sixth review of PR 14, "Review of `e852aac`"
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6854235653, 2026-11-13
13:24Z). In the owner's words, "Let's address the last round of review on PR 14".

- It finds no wrong value or crash in the shipped arithmetic. Its nine findings are about test
  strength (1, 3), the third branch's unheld preset (2), cost (4, 5), simplification (6, 7, 8)
  and the rule's design (9).
- The revision is on the same branch, so PR 14 still closes #13 and #15. It changes
  `src/patchbay_vital/parameters.py`, both test modules that read the map, adds
  `tests/data/pinned-values.txt`, and changes no gate file. No stage, commit, push or pull request
  edit by an agent.

## What was checked while shaping

Read-only, against `e852aac`, with the shipped code, in memory (no file written).

- **Finding 1 holds.** Every curve the map uses is monotone in double arithmetic, so wherever
  `back` shows the display, every float32 between the preset and `back` shows it too.
  `_shares_its_display` asks only the float32 next to the preset toward `back`, so it holds
  wherever the first assert of `_assert_comes_back` does: it excused any `back` that shows the
  display, on any record.
- **The general rule (finding 9)**, `to_preset` returning what a set of the curve's float32 holds
  and falling back to the other side only where that alone shows the display:
  - the same value as the shipped rule on 207,000 held displays, 3,000 a group over all 69 of the
    map's groups, drawn uniformly over float32 bit patterns in [0, 1] (seed 14);
  - a different value on 1,085 of 20,000 displays drawn uniformly over `volume`'s range (seed 8,
    `random.uniform`), each a held preset where the shipped rule gives an unheld one;
  - the normalized value a set sends unchanged on all 1,085.
  A sample, labelled as one; moved to a new issue (Decision 1).
- **The candidate excuse (finding 1)** held on the 1,601 excused values of that 207,000-value
  sample. The owner set that aside as evidence: the floor pass counts it (Decision 2).
- **Where `back` differs from the preset.** About 93% of `volume`'s float32 normalized values
  below 2 ** -54, 612,368,384 in all, from the subnormals up; most of them below binade -96. So the
  fifth review's binades -96 to -55 would not hold them.
- **The committed map's 552 linear scales hold both their ends.**
- **Cost** on this machine (macOS 26.6.2, arm64, 14 cores, Python 3.12), µs a call on `volume`,
  `main`'s tree run in memory from `git show main:src/patchbay_vital/parameters.py`:

  | | `to_preset` | `to_normalized` | the whole map at its defaults |
  |---|---|---|---|
  | `main` | 3.7 | 8.3 | 4.3 ms |
  | `e852aac` | 15.8 | 15.9 | 9.1 ms |
  | derived, `scale.to_normalized(to_preset(display))` | — | 28.4 | 13.5 ms |

  Re-measured on the shipped tree in `verification/cost.txt` (Task 6).
- **The pass's cost** on 20,000 sampled values: finding 1's count over every value below
  2 ** -54 about 14 CPU-hours; the old-against-new comparison over the same range about 17. At the
  fifth review's measured throughput, about 8 times on 12 processes, roughly 3 hours wall for one
  pass.
- **The seeded regression the pins caught.** The revision after PR 14's review
  (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/verification/mutation.txt`) sent an
  unheld preset in (1e-13, 2 ** -43] eight float32 steps up in `NormalizedScale.to_normalized`;
  "The property's draws did not reach it; the rows did."
- **An earlier data file.** Issue #15's spec removed `tests/data/volume-floor.txt`,
  `tests/data/power-of-two-presets.txt` and the `tests/conftest.py` reading them (commit
  `2d2f7dc`), and pinned the values in each module (its Decision 8).

## Shaping answers

In the owner's words:

- **The rule (findings 9 and 2):** "Neither as offered: keep branch 3 in this PR and file the
  general rule as its own patchbay-vital issue, the spec that runs before #8.
  - This revision: finding 2 is answered in shape.md as agreed with and moved to the new issue,
    not declined as #8's. Finding 9's simplification of branch order and docstrings is done only
    where it changes no result; if it would change any shipped result, it moves too.
  - The new issue, no attribution: to_preset returns what a set of the display's float32 holds,
    falling back to the held float32 on its other side only when that alone shows the display, so
    it always returns a held preset. Evidence required: the direct old-against-new count on volume
    and the envelope group; the reproduction sweep on all 69 groups, labelled as such; a statement
    that arbitrary displays are doubles and cannot be enumerated, with the sample size and the
    property that stands in for a count; the normalized value a set sends shown unchanged; the
    Vital probe; #8's characterization test reversed on purpose.
  - Issue #8 is revised in place: it depends on the new issue, and its finding 1 narrows to
    "Vital's rounding or the nearer held neighbour"."
- **The excuse (finding 1):** "1. Two conditions:
  - The test works out the two candidates from the scale's and curve's own primitives
    (curve.to_preset, the scale's set path, the next float32), never by calling _resolve or
    to_preset, so a wrong rule in the code cannot agree with itself.
  - The 1,601 sampled values are not the evidence. Count it on volume's floor binades with the
    shipped methods (the 30-minute pass, not the overnight one): every value where back differs
    from the preset, with the number excused by each candidate and the number excused by neither,
    which must be 0. Mutants for both of the review's scenarios fail by name."
- **The pinned values (findings 3 and 7):** "1, with one question answered before building: the
  property's @example pins need these values at import time, and pytestconfig is a fixture,
  available only inside a test. Say how the @example decorators get them. If the answer is that
  each module reads the file at import through a path relative to its own __file__, do that for
  every use and drop pytestconfig, so there is one way in; the few-line reader may be written in
  each module, since it is the values, not the parsing, that must not be duplicated. If the
  @example pins are dropped instead, stop and present: the pins are what caught the seeded
  regression when Hypothesis's draws did not. The file's header says what each value is and which
  spec measured it. A missing or malformed file fails the tests by name, with a mutant for each.
  The harness rerun is one run, kept whole."
- **Cost and simplicity (findings 5 and 6):** "1. Show the derived to_normalized gives the same
  value as this branch's current one, so last night's direct count still describes the shipped
  code: compare the two on volume's floor binades and on the envelope group's held powers of two
  with the shipped methods (the short pass, not the overnight one), and say in shape.md why no
  other value can differ, citing the direct count's N(P1) == N'(landed) result on all 15,761,472
  first-branch values. Any difference: stop and present. The costs are recorded in shape.md with
  the machine they were measured on."
- **The pass**, told it is about 3 hours, not 30 minutes: "1. Start it unattended, under
  caffeinate, with the three stops as proposed. The transcript prints both trees and the machine
  before and after, and says why no value at or above 2 ** -54 can have back differ from the
  preset, shown by a check on those values or cited from last night's direct count, not asserted."
- **How the file is read**, told that `__file__` departs from `base/testing/tests.md`: "2. Shown,
  not assumed: the seeded regression that only the pinned rows caught in the earlier round is
  rerun as a mutant, and the new test over the file's values fails it by name with Hypothesis's
  draws unable to (derandomized, or the property deselected). The property keeps its literal
  @examples that are not in the file (0.0, 1.0 and any other value written only there). shape.md
  records that the @example form was dropped for the file's values and why: a decorator cannot
  read from pytest's root, and the base standard keeps one way to reach a repository file."
- **The quotient (finding 8):** "1. The helper's docstring says why it is not imported from
  parameters.py: the tests work the expected value out from Fraction primitives so the code
  cannot agree with its own mistake. Finding 8 is answered in shape.md as taken in that form, with
  the mutant on _landing's first step failing test_a_quotient_that_lands_... by name."
- **The data file**, told #15's spec had removed one: "1. shape.md records it as superseding issue
  #15's Decision 8, with both reasons in order: why the literals were chosen then, and what the
  fourth and sixth reviews showed the duplication costs. The reads go through
  pytestconfig.rootpath inside tests, as answered on the @example question."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`,
  `base/process/ownership`, `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and
  `vital/plugin-state`. Snapshot in `standards.md`, base at `e31f7db`.
- **The excuse after the floor pass**, told the second candidate excused none of the 570,997,534
  values and the first all of them, and that the unit tests pass with the excuse narrowed to the
  first: "1. As proposed, with the count as the recorded reason and the mutant that restores the
  second candidate failing by name. shape.md says the hand-built records were not counted, and
  that a record needing the second candidate would fail the property and not be excused.
  Decision 2 is listed as superseded, old beside new."

## Decisions

1. **Branch 3 stays; the general rule is its own issue**, the spec that runs before #8. Finding 2
   is agreed with and moved there. Finding 9 is taken here only where it changes no result: the
   first two branches merge, since where the scale holds the curve's float32 what a set of it
   holds is that float32. #8 is revised in place to depend on the new issue.
2. **The excuse names what a set holds.** Superseded once, after the floor pass, by the owner:

   | | The excuse passes `back != preset` only if |
   |---|---|
   | **Was** (shaping) | the curve's own float32 for the display is not the held preset, so the display does not name it, and `back` is what a set of that float32 holds **or the float32 on its other side** |
   | **Now** (after the floor pass) | the curve's own float32 for the display is not the held preset, and `back` is what a set of that float32 holds |

   - **Why:** the floor pass (`verification/floor-pass.txt`) counted the excuse as first written on
     every float32 normalized value of `volume`. It was asked on 570,997,534; what a set holds
     excused all 570,997,534, the other side none, and neither none. So the narrowed excuse
     refuses BY_OTHER plus NEITHER, 0 + 0: the pass is its count as it stands, and was not rerun.
     The pass sets BY_HELD where the excuse passed and `back == held`, which is the narrowed
     excuse exactly.
   - **What is not counted:** the hand-built records of `tests/unit/test_parameters.py`. No pass
     counts them. A record that needed the other side, there or in a later map, would fail the
     property and not be excused by it.
   - The test computes the candidate with `_what_a_set_holds` (`curve.to_preset`, the scale's
     `to_normalized` and `to_preset`, and `next_float32` for the other side it also returns, which
     the branch tests still read). MP4 in `verification/mutation.txt` puts the second candidate back
     and fails `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds` by name, at the
     held float32 above `_SHARED`'s own, which is the other side there and shows the display.
   - The first condition, `own != preset`, is now implied wherever `_assert_comes_back` asks.
     Where the curve's float32 is the preset, it is held, so a set of it holds it, and
     `back == held` would be `back == preset`, which is never asked. MP1, the excuse without it,
     is recorded as an expected equivalent. The condition stays, as the owner approved the
     excuse's wording.
3. **One data file, `tests/data/pinned-values.txt`**, read through `pytestconfig.rootpath` inside
   tests, a reader of a few lines in each module. It supersedes issue #15's Decision 8:
   - **Why the literals were chosen then:** the row files carried each value's step, and the
     conftest's reader, step helper, fixtures and format existed only for the steps, which the
     fix set to 0. "With the steps gone, a row is a value, and a value is clearest beside the
     assertion that reads it."
   - **What the duplication cost since:** the fourth review found the two copies could drift, and
     the AST test added to hold them equal grew to about 60 lines; the fifth review found gaps in
     it, and the sixth found more (`except ... as`, match captures, a mapping's `**rest`, PEP 695
     type parameters). A file of values alone needs no fixture, no conftest, no step format and no
     reading of another module's source.
4. **The `@example` form is dropped for the file's values.** A decorator is evaluated at import,
   before any fixture, so it cannot read from pytest's root, and `base/testing/tests.md` keeps one
   way to reach a repository file: `pytestconfig.rootpath`, "never a path counted up from the test
   file". The values run instead in `test_every_pinned_value_comes_back_on_every_record`, on every
   hand-built record through `_assert_comes_back`, the checks the `@example` ran. The property keeps
   its `@example`s written only there: 0.0, 1.0 and 5.2383727406426375e-33.
5. **`to_normalized` is derived**, `scale.to_normalized(to_preset(display))`, `main`'s form, and
   `_resolve` goes. **No value can differ from `e852aac`'s, by reading:** where `e852aac` returned
   a normalized value from `_resolve`, the curve's float32 was the preset returned (the kept and
   the third branches) and the value was `_landing(scale, preset)[0]`, which is
   `scale.to_normalized(preset)` itself; on the other two branches it already returned `None` and
   computed `scale.to_normalized` of the preset returned. The fifth review's direct count also
   found N(P1) equal to N'(landed) on all 15,761,472 first-branch values (PN 0), so not even the
   value it computed on the way differs there. The floor pass compares the two methods on every
   value below 2 ** -54 and at the envelope group's held powers of two, 143 from 2 ** -149 to 2,
   the fifth review's 126 from 2 ** -125 to 1 among them. The costs are measured again in
   `verification/cost.txt`; no fast path is added (finding 5). Finding 4's swap is taken.
6. **The floor pass**: every float32 normalized value of `volume` below 2 ** -54 with both trees,
   every one at or above it with the new tree, the envelope group's powers of two with both.
   Unattended under `caffeinate`, re-timed first; stops at an estimate past 4 hours, any difference
   from `e852aac`, or any value neither candidate excuses.
7. **Finding 8 is taken as a test-module helper**, `_nearest_quotient`, from `Fraction`
   primitives, never imported from `parameters.py`, so the code cannot agree with its own mistake.
   A mutant on `_landing`'s first step fails
   `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it` by name.
8. **The negative harness is rerun once**, its transcript kept whole: this revision adds a file
   under `tests/`, a directory the harness copies (`base/process/verification-gate.md`).
9. **The earlier spec folders stay as recorded**, with their errata listed below.

### Where the implementation departs from the plan

- **Issue #16 was filed first**, before Task 2, so the docstrings could cite its number. Its body is
  as Decision 1 words it, read back after posting.
- **The test module's docstrings cite the floor pass by path, not by number,** so
  `tests/unit/test_parameters.py`, which the pass imports for its predicate, was final before the
  pass began; the numbers are in this file, the CHANGELOG and the standard.
- **The floor pass asks the test module's own predicate**, `_unnamed_by_its_display`, imported
  from the working tree, not a copy of it: a one-entry cache in front of `_what_a_set_holds` hands
  the predicate the triple the pass already worked out, so the helper runs once a value.
- **Section C enumerates every power of two from 2 ** -149 to 2** and keeps those the scale holds,
  in each tree, rather than taking the 126 from the fifth review's transcript.
- **The mutation transcript's first run found two mutants that tested nothing:**
  - MF changed the last digit of a value's `repr`, which parsed to the same double, so the file
    was not malformed. It is replaced by a value that is no float32 (0.1), with MF2 beside it, a
    line of a set no reader knows.
  - MP1, the excuse without its first condition, passed: no test offered the excuse the one
    `back` only that condition refuses, the float32 just above a preset the display names, which
    is the other candidate there. The excuse was then narrowed (Decision 2, as superseded), under
    which MP1 is an expected equivalent. The held float32 above `_SHARED`'s own, the assertion
    planned for MP1, is offered instead with `_SHARED`'s preset, and refuses MP4.
  Both test edits waited for the floor pass to finish, since its section B pools import the test
  module afresh; the transcript kept is the second run, whole.
- **The floor pass's trees after the run differ from before in two lines of `git status`:**
  ` M CHANGELOG.md` and ` M README.md`, edited at 09:12 and 09:13, after the pass began at 09:08,
  so its `cmp` reports a difference at line 2. The pass reads neither. Every file it reads has the
  same blob before and after, in both trees, as the two listings show line for line.
- **The 2 ** -43 lines of `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`**
  asked the excuse where `back` is the preset, which `_assert_comes_back` never does. They now
  assert that the map takes the float32 on the other side there, 2 ** -43 itself, since what a set
  holds does not show the display.
- **Mutants retired with what they mutated:** M8, the held branch after branch 1, is now the
  shipped form itself (the merge of Decision 1), which the floor pass shows changes no value; M10,
  `_shares_its_display` asking either side, went with the predicate, and MP1 to MP3 take its place.

## What the transcripts show

- **`verification/floor-pass.txt`** ran from 09:08 to 12:10 EST, unattended under `caffeinate -i`,
  exit 0. The timing first estimated 2.71 hours wall, under the 4-hour stop. No stop was reached.
  - **Section A, every float32 normalized value of `volume` below 2 ** -54, 612,368,384, both
    trees (9,070 s):** `to_preset` and `to_normalized` the same as `e852aac`'s on every value, and
    the scale's and curve's forward values the same. `back` differs from the preset on 570,997,534,
    the reproduction's figure exactly, so no mismatch was presented. All of them are at a held
    preset at or below 2 ** -43. What a set holds excuses all 570,997,534, the other side none,
    and neither none.
  - **Section B, every value at or above 2 ** -54, 452,984,833, the new tree (1,850 s):** `back`
    differs from the preset on none. So nothing there asks the excuse, shown by a check, not
    argued.
  - **The 12 envelope records are one group:** one distinct key over every field the methods
    called read, the methods' attribute reads listed from the shipped source.
  - **Section C, `env_1_delay`:** 143 held powers of two from 2 ** -149 to 2, the fifth review's
    126 from 2 ** -125 to 1 among them. At each, the new `to_preset` and `to_normalized` of its
    display are `e852aac`'s, and are the power and its normalized value.
- **`verification/mutation.txt`**, its second run, whole (12:17 EST):
  - M0 passes, 89 tests.
  - M1 to M7, M9, M15 and M16 fail, each in the test its line names. M8b is equivalent, as
    before.
  - MA fails `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`, and passes all 102
    of `e852aac`'s tests. MB fails it and three others; on `e852aac`, only the pinned branch test
    caught it.
  - MC fails `test_every_pinned_value_comes_back_on_every_record` with the property deselected,
    and again with every test run, derandomized. The property's two Hypothesis tests alone,
    derandomized, pass it.
  - MD fails `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it`, among 8.
  - ME, MF and MF2 fail every unit test that reads the file, and, with Vital, the integration
    module's three. ME fails with the path, and MF and MF2 with `pinned-values.txt:25` and the line.
  - MP1 passes, an expected equivalent (Decision 2). MP2, MP3 and MP4 fail the excuse's test by name.
- **`verification/cost.txt`**, µs a call, the minimum of 7 repeats, measured twice. The machine is
  an Apple M4 Pro, arm64, 14 cores, macOS 26.6.2 (25G83), Python 3.12.16, with load averages about
  5 before and after. Pass 2:

  | | `to_preset`, 1,000 displays over [0, 1] | `to_normalized`, the same | `to_preset`, 1,000 at or below the floor | `to_normalized`, the same | the 903 records at their defaults |
  |---|---|---|---|---|---|
  | `main` | 3.6 | 7.9 | 4.0 | 8.9 | 4.2 ms |
  | `e852aac` | 15.6 | 15.6 | 18.2 | 19.3 | 9.0 ms |
  | this revision | 15.3 | 27.1 | 17.9 | 31.2 | 13.1 ms |

  The derived `to_normalized` lands the preset `to_preset` landed a second time, through
  `scale.to_normalized`. Pass 1 is within 0.7 µs and 0.2 ms of these. Shaping's figures,
  measured on a set of values not recorded, are within 1.3 µs and 0.4 ms of the [0, 1] columns.

## The review's findings

| # | Finding | Outcome |
|---|---|---|
| 1 | The excuse is looser than the guard it replaced | What a set holds, from primitives; counted on `volume`; the two scenarios' mutants and the second candidate's fail by name (Decision 2, as superseded) |
| 2 | The third branch returns a preset the plugin never holds | Agreed with; moved to the new issue (Decision 1) |
| 3 | `_bindings` misses some bindings | Removed with the AST test (Decision 3) |
| 4 | `holds(other)` runs before the cheap comparison | Swapped |
| 5 | `to_preset` always pays for `_landing` | Measured and recorded; no fast path (Decision 5) |
| 6 | `_resolve`'s optional value | Taken: `to_normalized` derived, equality counted and argued (Decision 5) |
| 7 | The pinned literals in two modules | One data file (Decisions 3, 4) |
| 8 | The quotient formula in two tests | A test-module helper (Decision 7) |
| 9 | The fix sits one level too shallow | The result-preserving part here; the rule to the new issue (Decision 1) |

## After the final review

The final review of PR 14, of `4095409` on 2026-11-13, has 13 findings and was not posted to the
pull request. Its reviewer verified none of them. By the owner's instruction, 12 and 13 are fixed
here once checked against the tree, six are carried to issue #16 unverified, and the rest are
already this revision's. No change to `src/` or `tests/`, and no new spec folder.

Checked on `4095409`, read only:

- **Finding 12 is true.** `git grep _VOLUME_FLOOR` outside `agent-os/specs/` found one line,
  `vital/plugin-state.md`'s "then the integration module's `_VOLUME_FLOOR`", meant as history and
  reading as a second, current source. `tests/integration/test_vital_plugin.py` has no such name:
  its load test loops the file's `volume_floor` set. Issue #15's probe transcript, which the
  standard cites, prints the same four values under that name.
- **Finding 13 is true.** `vital/parameter-map.md`'s counting rule cited "the `@example`s of
  `test_a_value_the_parameter_holds_comes_back_exactly`". That property keeps 0.0, 1.0 and
  5.2383727406426375e-33. Issue #13's value, an `@example` there at `e852aac`, is a line of
  `tests/data/pinned-values.txt`, run by `test_every_pinned_value_comes_back_on_every_record`.

| # | Finding | Where it went |
|---|---|---|
| 1 | The third branch returns a preset the scale does not hold | Issue #16's own subject (Decision 1) |
| 2 | `_what_a_set_holds` calls the shipped `NormalizedScale.to_normalized` | Carried to #16, unverified |
| 3 | The load test's expected value comes from `volume.scale.to_normalized` | Carried to #16, unverified |
| 4 | Without `_ABSORBED` the excuse applies to any record at any value | Already decided: Decision 2, as superseded. The excuse names what a set holds, counted on every float32 normalized value of `volume`; the hand-built records are recorded as not counted |
| 5 | An empty pinned set passes the integration loops | Carried to #16, unverified |
| 6 | `NormalizedScale.holds` raises a built-in on a non-finite value | Carried to #16, unverified |
| 7 | `to_normalized` lands the preset `to_preset` landed a second time | Already decided: Decision 5. Derived, the cost measured and recorded, no fast path |
| 8 | `_landing` runs `to_float32` on values already float32 | Carried to #16, unverified |
| 9 | `_pinned` is re-read inside the per-record loops | Carried to #16, unverified |
| 10 | Three ordered branches where one general rule would do | Issue #16's own subject (Decision 1) |
| 11 | `_pinned` is written in both test modules | Already decided: Decision 3. A reader of a few lines in each module; the values, not the parsing, are written once |
| 12 | `vital/plugin-state.md` names `_VOLUME_FLOOR` | True; corrected, standards change set |
| 13 | `vital/parameter-map.md` cites the moved `@example`s | True; corrected, standards change set |

- **The two standards edits** were approved by the owner on 2026-11-13, each wording shown before
  it was made, and are verified against `tests/unit/test_parameters.py`,
  `tests/integration/test_vital_plugin.py` and `tests/data/pinned-values.txt` as shipped:
  - `agent-os/standards/vital/plugin-state.md` names `_VOLUME_FLOOR` as what issue #15's probe
    transcript prints, the integration module's constant until this revision moved the values to
    the file;
  - `agent-os/standards/vital/parameter-map.md` cites the file, every value of which
    `test_every_pinned_value_comes_back_on_every_record` runs, and the three `@example`s the
    property keeps.
- **`agent-os/standards/index.yml` is unchanged:** neither description names what was corrected,
  and neither edit changes what its standard decides.
- **Issue #16 is revised in place,** "Revised 2026-11-13", with a section "Carried from PR 14's
  final review" holding findings 2, 3, 5, 6, 8 and 9 as the reviewer stated them, each marked
  unverified. Read back as posted.
- No gate file and no CHANGELOG entry changes, and there is no new base proposal: `Proposals sent
  upstream:` stands as written below.
- **`scripts/gate.sh` exits 0** on the working tree with both standards edits, on `4095409`, with
  Vital installed (2026-11-13, 13:43 EST): all six steps pass, step 5 with 507 passed. No
  transcript is kept, and `verification/gate-run.txt` stays as recorded; only this line is written
  after the run.

## Errata in the earlier spec folders, which stay as recorded

- **The fourth review's Decision 3**
  (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/shape.md`): "A single
  definition would need a shared `tests/support` module on pytest's `pythonpath`. That is a
  `[tool.pytest.ini_options]` change, so a gate file." A data file read through
  `pytestconfig.rootpath` needs no change to any gate file.
- **The fourth and fifth reviews' account of `_shares_its_display`**: that it "excuses a failure
  where it holds and never a value whose exact check passed", with its counts. True, but it held
  wherever `back` showed the display, the first assert's own condition, because the curves are
  monotone: it bounded nothing that assert did not.

## Open

- **The general rule**, issue #16, before #8. It inherits the narrowed excuse (Decision 2).
- **The hand-built records** are not counted by any pass (Decision 2).
- **#8's findings 1 and 3**, as before, finding 1 narrowed.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing on
  either side". No value the map gives changes in this revision.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — reading a repository file from pytest's root; the `@example` pins.
- `base/process/verification-gate` — the gate unchanged; its record; the harness rerun.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issues written without
  attribution.
- `vital/parameter-map` — the two inverses, the exception and what its counts cite.
- `vital/measures` — the pinned values, now one file.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load test, which reads the file now.

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

**Results (2026-11-13):** `scripts/gate.sh` exits 0 on this branch, the working tree on
`e852aac`, with Vital installed (`verification/gate-run.txt`, 12:53 EST). All six steps pass, and
step 5 reports 507 passed, none skipped. The tree before and after the run is the same by `cmp`,
every path's blob listed. The transcript is written outside the tree and copied in afterwards, and
only this Results paragraph is written after it.
- **507 against the fifth review's 520.** Collected from both trees, the difference is all in
  `tests/unit/test_parameters.py`:
  - the floor, branch and power-of-two tests ran once per pinned value and now loop over the
    file's, 14 items to 5;
  - `test_a_display_s_normalized_value_is_its_preset_s_own` (4) and
    `test_the_integration_module_pins_the_same_values` (2) are gone (Decisions 3 and 5), and
    `test_where_volume_s_offset_absorbs_a_preset` (1) is rewritten as
    `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`;
  - `test_every_pinned_value_comes_back_on_every_record` and
    `test_the_pinned_values_file_holds_two_named_sets` are new.
- **The negative harness was rerun once**, since a file is added under `tests/`, which every case
  copies (Decision 8). It ran on the final tree, before the gate:
  - `verification/gate-negative-tests.txt`, every test but j: 141 runs, 0 unexpected;
  - `verification/ci-negative-test.txt`, case j, the CI replay: 3 runs, 0 unexpected.
  Both are kept whole. The local paths in them, and the two in `gate-run.txt`, are the tools' own
  output (uv's `VIRTUAL_ENV` warning, its cache path, the sync script's upstream), as in the
  earlier specs' transcripts.
- No gate file changed.

**Docs (step 7):** checked against the shipped tree, and true after the change:
- `README.md`'s `tests/` paragraph names `pinned-values.txt` beside `fma-vectors.txt`.
- `CLAUDE.md` names nothing this revision changed.
- `src/patchbay_vital/parameters.py`: the module docstring states the rule in its order, the third
  branch as issue #16's. `to_preset`'s docstring numbers the branches as the code takes them and
  cites the fifth review's direct count and this revision's floor pass. `to_normalized`'s says
  what it is derived from.
- `tests/unit/test_parameters.py`: `_assert_comes_back`, `_unnamed_by_its_display`, `_SHARED` and
  `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds` describe the narrowed excuse
  and cite the floor pass by path. `_nearest_quotient` says why it is not imported. The
  characterization test names issue #16.
- `tests/integration/test_vital_plugin.py`'s three tests that read the file say so.
- `tests/data/pinned-values.txt`'s header names each set's spec, read against those folders.
- `git grep` outside `agent-os/specs/` for `_VOLUME_FLOOR`, `_POWERS_OF_TWO`,
  `_shares_its_display`, `_resolve`, `_bindings`, `pins_the_same_values`, `_INTEGRATION_MODULE`
  and the two removed tests finds them only as history:
  - the CHANGELOG saying what was replaced;
  - `_unnamed_by_its_display`'s docstring saying what it replaces;
  - after the retrospective, the standards saying the same.
  Before the retrospective, `vital/parameter-map.md`, `vital/measures.md` and
  `vital/plugin-state.md` named them as current; the retrospective below corrects them.
- Issues #8, #15 and #16 read back as posted.

**Version (step 8):** `CHANGELOG.md` `[Unreleased]`, `### Fixed`. Issue #15's entry names this
folder and adds:
- "Written plainer after the sixth review, no value changed", with the floor pass's counts and
  the costs with their machine;
- the pinned values in one file;
- "The property's excuse names what a set holds", with its count and what is not counted;
- #16 for the third branch.
Issue #13's entry says `_shares_its_display` was replaced and its `@example` moved to the file.
The version stays 0.0.1; no release is cut.

## Standards Retrospective

Step 9, from the shipped diff. Each edit was presented to the owner with AskUserQuestion on
2026-11-13 and approved. Each is verified against `tests/unit/test_parameters.py`,
`tests/integration/test_vital_plugin.py`, `tests/data/pinned-values.txt` and
`src/patchbay_vital/parameters.py` as shipped, and against this folder's
`verification/floor-pass.txt`, `verification/mutation.txt` and `verification/cost.txt`, never
against the plan. Its own change set:

- `agent-os/standards/vital/parameter-map.md`, approved with two changes of the owner's: the cost
  names the machine, and `floor-pass.txt` and `sweep.txt` are cited by their full paths.
  `sweep.txt` is the fourth review's, in
  `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/verification/`, since this
  folder holds none. What the edit says:
  - the floor pass finds the restructured `to_preset` and the derived `to_normalized` unchanged;
  - `to_normalized` is `scale.to_normalized(to_preset(display))`, about 27 µs against `main`'s 8;
  - the third branch's test is issue #16's characterization, before #8;
  - "The exception, in plain words" is rewritten for `_unnamed_by_its_display`, with its count,
    the second candidate's absence, the uncounted hand-built records, and the refusals its test
    offers, each held by a mutant;
  - the pinned values are one file;
  - "An exception" now reads: counted split by the value allowed; a value never found is not
    allowed; tested by what it refuses, and one the property's assertions imply bounds nothing;
  - the "Verified against" list follows the code.
- `agent-os/standards/vital/measures.md`, as drafted. The pinned values are one file, read through
  `pytestconfig.rootpath` by a few-line reader in each module, failing by name (ME, MF, MF2). The
  source-reading test is gone, and a probe reads the file. The "Verified against" list is
  `_pinned`, `test_the_pinned_values_file_holds_two_named_sets` and the file.
- `agent-os/standards/vital/plugin-state.md`, as drafted. The load observation's four values are
  named as the file's `volume_floor` set, then `_VOLUME_FLOOR`.
- `agent-os/standards/index.yml`, this repository's `vital:` section alone, kept in step:
  - `measures`: values written once in a data file both modules read from pytest's root;
  - `parameter-map`: #16's characterization, `to_normalized` derived, and the exception passing
    only what a set of the display's own float32 holds, tested by what it refuses.
  The `base:` section is untouched.

Proposals sent upstream: fromtheoutfit/patchbay-standards#42; fromtheoutfit/patchbay-standards#40, revised in place

### Standards retrospective (proposed, base)

Presented to the owner with AskUserQuestion on 2026-11-13, multi-select; both approved.

- `base/testing/tests.md`, "Inside a test": a property's known exception is a predicate worked
  out from the code's primitives, never from the method under test. It is asked only where the
  exact check fails, and tested by what it refuses, each refusal held by a mutant. One the
  property's own assertions imply bounds nothing. Verified against `tests/unit/test_parameters.py`
  (`_unnamed_by_its_display`, `_what_a_set_holds`, `_assert_comes_back`,
  `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`), `verification/floor-pass.txt`
  and `verification/mutation.txt` (MA, MB, MP2 to MP4). Proposed, not applied. By the owner's
  decision it is revised into fromtheoutfit/patchbay-standards#40's proposal 2 in place, not filed
  anew. A "Revised 2026-11-13" paragraph cites `_shares_its_display` as the instance the reviews
  found empty, and proposal 2's text is replaced by this form. Read back as posted.
- `base/testing/tests.md`, "Inside a test": a pinned value that lives in a repository file reaches
  a property through a test over the file, run through the property's own assertion helper, not as
  an `@example`, since a decorator runs at import, before pytest's root is known. Verified against
  `test_every_pinned_value_comes_back_on_every_record`, `_pinned` in both modules,
  `tests/data/pinned-values.txt` and MC, ME, MF and MF2 in `verification/mutation.txt`. Proposed,
  not applied; filed as fromtheoutfit/patchbay-standards#42. Read back as posted.
