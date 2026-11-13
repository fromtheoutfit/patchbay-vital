# Revision after PR 14's sixth review

Spec folder: `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`

## Context

The sixth review of PR 14, "Review of `e852aac`"
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6854235653, 2026-11-13
13:24Z). It finds no wrong value or crash in the shipped arithmetic. Its nine findings:

- test strength: the excuse is looser than the guard it replaced (1); `_bindings` has gaps (3);
- the third branch returns a preset Vital never holds, the gap left to #8 (2);
- cost: `holds` is asked first (4); `to_preset` always lands (5);
- simplification: `_resolve`'s optional value (6); the duplicated pinned tuples (7); the
  duplicated quotient formula (8);
- design: one general rule would close 1 and 2 (9).

The revision stays on the same branch, so PR 14 still closes #13 and #15. No gate file changes.
No agent stages, commits, pushes or edits the pull request.

## What was checked while shaping (read-only, at `e852aac`)

- **Finding 1 holds.** Every curve is monotone, so wherever `back` shows the display, every
  float32 between the preset and `back` shows it too. `_shares_its_display` therefore holds
  wherever the first assert does: it excused any `back` that shows the display.
- **The general rule (finding 9),** tried in memory:
  - it gives the same value as the shipped rule on 207,000 held displays sampled over float32
    bits, across all 69 groups;
  - it differs on 1,085 of 20,000 uniform `volume` displays, always a held preset where the
    shipped rule gives an unheld one;
  - the normalized value a set sends is unchanged on all 1,085.
  Moved to a new issue (Decision 1).
- **The candidate excuse (finding 1)** held on 1,601 sampled excused values. That sample is not
  the evidence: the floor pass is (Task 6).
- **Where back differs from the preset:** about 93% of `volume`'s 612,368,384 float32 normalized
  values below 2 ** -54, from the subnormals up. Most lie below binade -96.
- **All 552 linear scales in the committed map hold both of their ends.**
- **Cost on this machine** (macOS 26.6.2, arm64, 14 cores), µs per call on `volume`:

  | | `to_preset` | `to_normalized` | Whole map at its defaults |
  |---|---|---|---|
  | `main` | 3.7 | 8.3 | 4.3 ms |
  | `e852aac` | 15.8 | 15.9 | 9.1 ms |
  | derived | — | 28.4 | 13.5 ms |

  "Derived" means `scale.to_normalized(to_preset(display))`. These are re-measured for shape.md
  (Task 6).
- **Issue #15's spec (Decision 8) removed `tests/data` row files and a `tests/conftest.py`
  reader.** It accepted the duplicated literals then; Decision 3 supersedes it.

## Decisions (owner, 2026-11-13, AskUserQuestion)

1. **Branch 3 stays in this PR. The general rule becomes its own issue, the spec that runs
   before #8.**
   - Finding 2 is answered as agreed with and moved to the new issue, not declined as #8's.
   - Finding 9's simplification is done only where it changes no result.
   - The new issue states the rule: `to_preset` returns what a set of the display's float32
     holds, falling back to the held float32 on its other side only when that alone shows the
     display. So it always returns a held preset.
   - The new issue lists the evidence the rule needs:
     - the direct old-against-new count on `volume` and the envelope group;
     - the reproduction's sweep on all 69 groups, labelled as such;
     - a statement that arbitrary displays are doubles and cannot be enumerated, with the
       sample size and the property that stands in for a count;
     - the normalized value a set sends, shown unchanged;
     - the Vital probe;
     - #8's characterization test, reversed on purpose.
   - #8 is revised in place: it depends on the new issue, and its finding 1 narrows to "Vital's
     rounding or the nearer held neighbour".
2. **Finding 1: the excuse names its candidates.**
   - `back != preset` passes only where the display's own float32 is not the held preset, and
     `back` is either what a set of that float32 holds or the float32 on its other side.
   - The test works the candidates out from primitives (`curve.to_preset`, the scale's set path,
     `next_float32`), never from `to_preset`.
   - It is counted on `volume` with the shipped methods: the values each candidate excuses, and
     the values neither excuses, which must be 0.
   - Mutants for both of the review's scenarios fail by name.
3. **Findings 3 and 7: one data file, `tests/data/pinned-values.txt`.**
   - Each module has a reader a few lines long, reading through `pytestconfig.rootpath` inside
     tests.
   - The AST test and `_bindings` go.
   - The file's header says what each value is and which spec measured it.
   - A missing or malformed file fails the tests by name, each with a mutant.
   - The negative harness reruns once, and its transcript is kept whole.
   - shape.md records that this supersedes #15's Decision 8, giving both reasons in order: why
     the literals were chosen then, and what the fourth and sixth reviews showed the
     duplication costs.
4. **The `@example` form is dropped for the file's values,** because a decorator cannot read
   from pytest's root, and the base standard keeps one way to reach a repository file.
   - A test over the file's values runs them on every hand-built record.
   - The first review's seeded regression, the one only the pinned rows caught, is rerun as a
     mutant. It must fail that test by name with Hypothesis unable to catch it (the property
     deselected, and a derandomized run).
   - The literal `@example`s that are not in the file stay: 0.0, 1.0 and 5.2383727406426375e-33.
5. **Findings 5 and 6: `to_normalized` is derived.**
   - `to_normalized(display)` is `scale.to_normalized(to_preset(display))`, and `_resolve` goes.
   - The derived method is compared with `e852aac`'s on the floor pass and at the envelope
     group's held powers of two. shape.md says why no other value can differ, citing the direct
     count's result N(P1) == N'(landed) on all 15,761,472 first-branch values.
   - Any difference: stop and present.
   - The costs are recorded with the machine they were measured on.
   - Finding 4's swap is taken.
6. **The floor pass runs unattended, under `caffeinate`,** over every value below 2 ** -54.
   - It stops in three cases: the estimate passes 4 hours, any difference from `e852aac`, or any
     value neither candidate excuses.
   - The transcript prints both trees and the machine before and after.
   - It shows, by a check, that no value at or above 2 ** -54 has `back` differing from the
     preset.
7. **Finding 8:** a `_nearest_quotient` helper in the test module, built from `Fraction`
   primitives.
   - Its docstring says why it is not imported from `parameters.py`.
   - A mutant on `_landing`'s first step fails `test_a_quotient_that_lands_...` by name.
8. **Steps 2 to 5 confirmed as listed.**
   - No visuals.
   - References: the fifth review's folder and its count scripts, `_record`, `_what_a_set_holds`,
     and the `tests/data` readers.
   - The mission is unchanged.
   - Standards: the core five, plus `base/testing/tests`, `base/process/verification-gate`,
     `base/process/standards-retrospective`, `base/process/standards-index`,
     `base/process/ownership`, `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and
     `vital/plugin-state`.

| # | Finding | Outcome |
|---|---|---|
| 1 | Excuse looser than the old guard | Candidates from primitives; counted; two mutants (D2) |
| 2 | Branch 3 returns an unheld preset | Agreed, moved to the new issue (D1) |
| 3 | `_bindings` gaps | Removed with the AST test (D3) |
| 4 | `holds` before the cheap check | Swapped |
| 5 | `to_preset` always lands | Costs recorded, no fast path (D5) |
| 6 | `_resolve`'s optional value | Derived; equality counted and argued (D5) |
| 7 | Pinned literals duplicated | One data file (D3, D4) |
| 8 | Quotient formula copied | Test-module helper (D7) |
| 9 | Fix one level too shallow | Result-preserving part here; the rule to the new issue (D1) |

## Task 1: Save spec documentation

Create the folder with:
- `plan.md`, this plan;
- `shape.md`, holding:
  - the template's sections;
  - the shaping checks;
  - the owner's answers, in their words;
  - the findings table;
  - the supersession of #15's Decision 8;
  - the errata;
- `standards.md`, the full text of the Decision 8 standards, base at `e31f7db`;
- `references.md`.

No `visuals/`.

## Task 2: `src/patchbay_vital/parameters.py`

- **`to_preset`** holds the rule directly, and `_resolve` is removed:
  ```python
  preset = min(max(curve.to_preset(display), scale.minimum), scale.maximum)
  if scale.kind == "indexed":
      return _round_half_away(preset)
  held = _landing(scale, preset)[1]
  if held == preset or curve.to_display(held) == display:
      return held
  other = next_float32(preset, math.copysign(math.inf, preset - held))
  if curve.to_display(other) == display and scale.holds(other):
      return other
  return preset
  ```
  Why no result changes:
  - branches 0 and 1 merge, and `held == preset` returns the same value;
  - the swap reorders a conjunction of calls that have no side effects.
- **`to_normalized`** becomes `self.scale.to_normalized(self.to_preset(display))`, `main`'s form.
- **Docstrings (module and `to_preset`):**
  - the rule in general terms, with its order;
  - where branches 2 and 3 occur, cited to this revision's floor pass and the fifth review's
    direct count;
  - the arbitrary display's unheld float32, as the new issue's question, before #8.

## Task 3: `tests/data/pinned-values.txt`

- **Header `#` lines** say what each set is, which spec measured it, and that both test modules
  read it through `pytestconfig.rootpath`.
- **Then one line per value:** `<set> <value> <name>`.
  - `volume_floor`: four values, each named as its comment is now.
  - `powers_of_two`: three values.
- **Values** are written as `repr` and read back with `float()`.

## Task 4: `tests/unit/test_parameters.py`

- **Removed:**
  - `_VOLUME_FLOOR`, `_POWERS_OF_TWO`, `_INTEGRATION_MODULE`, `_bindings` and
    `test_the_integration_module_pins_the_same_values`;
  - `test_a_display_s_normalized_value_is_its_preset_s_own`, now true by definition.
- **`_pinned(pytestconfig)`** returns `dict[str, tuple[float, ...]]`.
  - It refuses a line with the wrong field count, an unknown set, or a value `float()` refuses
    or that is not a float32, naming the file and the line.
  - A missing file raises an error naming the path.
  - `test_the_pinned_values_file_holds_two_named_sets` checks the sets, their sizes (4 and 3),
    and that each value is a float32 in [0, 1].
- **Tests now parametrized over the tuples loop over the file's values,** naming each one in
  their assertions:
  - the floor and power-of-two tests;
  - the two branch tests, their expected presets staying here, zipped strictly with the file's
    values.
- **`test_every_pinned_value_comes_back_on_every_record(pytestconfig)`** runs every file value on
  every hand-built record through `_assert_comes_back`. The property loses
  `@example(normalized=5.857149595214349e-20)` and keeps its other `@example`s.
- **Finding 1:** `_shares_its_display` is replaced by a predicate built on `_what_a_set_holds`:
  `own != preset and back in (held, other)`.
  - `_assert_comes_back`'s fourth assert asks it.
  - The docstrings cite the floor pass's counts for `volume`, and the reproduction's, labelled,
    for the other groups.
- **`test_where_volume_s_offset_absorbs_a_preset` is rewritten:**
  - at 2 ** -43 the display does not name its held preset, and `back` is a candidate;
  - at the float32 above, the display names its preset, so any other `back` is refused;
  - a `back` several float32s away is refused;
  - at a pinned `volume` value, found by a seeded search, the curve's float32 is the held
    preset and a held neighbour shares its display: that neighbour is refused (the review's
    scenario 1).
- **`_nearest_quotient(scale, preset)`** is used by both quotient tests (Decision 7).
- **Docstrings changed:**
  - `test_an_arbitrary_display_keeps_the_curve_s_float32` names the new issue, before #8;
  - the made-up record's test names branches as the restructured rule does.

## Task 5: `tests/integration/test_vital_plugin.py`

- `_VOLUME_FLOOR` and `_POWERS_OF_TWO` are removed.
- The floor, power-of-two and load tests take `pytestconfig` and read the file through this
  module's own reader, a few lines long.
- Their docstrings are updated. Nothing else changes.

## Task 6: The floor pass (`verification/floor-pass.txt`)

The scratchpad scripts are embedded in the transcript, adapted from the fifth review's
`direct-count.txt`.

- **Trees:**
  - `e852aac`'s `src`, taken with `git archive` into the scratchpad;
  - the working tree.
  Each worker pool imports one tree, and prints the `parameters.py` it imported, with its blob.
- **Header, printed before and after and compared with `cmp`:**
  - both trees;
  - `git status --porcelain=v1`;
  - the blob of every file read;
  - the machine and Python.
- **Timing first:** 200,000 values, with the estimate printed. Stop and present if it passes
  4 hours.
- **Section A, `volume` below 2 ** -54** (612,368,384 values). Per binade, each count split at a
  held preset ≤ 2 ** -43:
  - DIFF (`back != preset`), BY_HELD, BY_OTHER and NEITHER, with NEITHER a stop;
  - `to_preset` and `to_normalized`, new against `e852aac`, any difference a stop.
- **Section B, `volume` at or above 2 ** -54** (452,984,833 values), new tree: DIFF per binade.
  Any value it counts gets the candidate check, and NEITHER is a stop.
- **Section C, `env_1_delay`:**
  - the 12 records' group key, field by field;
  - at each of its 126 held powers of two, `to_preset` and `to_normalized`, new against
    `e852aac`, any difference a stop.
- **Totals:** DIFF is compared with the reproduction's 570,997,534. A mismatch is presented
  before any doc cites either figure.
- **How it runs:** under `caffeinate -i`, in the background, unattended.
- **`verification/cost.txt`:** per-call costs for `main`, `e852aac` and the new tree, with the
  machine.

## Task 7: Mutation (`verification/mutation.txt`)

Every mutant runs on a scratch copy, each with its diff, the tests that fail and the exit status.

- **M0**, unmutated: passes.
- **MA, scenario 1:** where the curve's float32 is held, `to_preset` returns a held float32
  beside it that shows the display. It fails by name. It is also run against `e852aac`'s tests
  to show they passed it.
- **MB, scenario 2:** `to_preset` returns a held float32 several steps from what a set holds,
  still showing the display. It fails by name, and is also run against `e852aac`'s tests.
- **MC, the first review's seeded regression:** an unheld preset in (1e-13, 2 ** -43] is sent 8
  float32 steps up in `_landing`. It must fail
  `test_every_pinned_value_comes_back_on_every_record` by name in two runs: with the property
  deselected, and derandomized.
- **MD:** `_landing`'s first step changed. It must fail
  `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it` by name.
- **ME, the file missing; MF, a malformed line:** the tests that read the file fail by name, in
  the unit module, and in the integration module with Vital.
- **Reruns:** the fifth review's code mutants, adapted to the new text: M1–M10, M15 and M16, M8
  and M8b as before.
- **Retired with their code:** M11–M14 and M19–M21 (the AST test), and M17–M18 (`_resolve`'s
  value).

## Task 8: Issues (no attribution; each read before and after)

- **The new issue,** worded as Decision 1:
  - the rule;
  - the required evidence;
  - the shaping sample, labelled as a sample;
  - `beats_per_minute` at 216.85141355537831;
  - #8 depending on it.
- **#8:** depends on the new issue, and finding 1 narrows. A "Revised 2026-11-13" paragraph says
  so.
- **#15:** a "Revised 2026-11-13 (after PR 14's sixth review)" paragraph.

## Task 9: `CHANGELOG.md` `[Unreleased]`, issue #15's entry

The entry's header names the sixth review's folder. Its bullets say:
- `to_preset` is restructured, with no result changed (the floor pass);
- `to_normalized` is derived, equal on every value (by reading and by the floor pass);
- an arbitrary display's float32 is now the new issue's question;
- the excuse names its candidates;
- the pinned values live in one file.

## Task 10 (FINAL): Verification gate

1–6. **`scripts/gate.sh`** on the final tree, with Vital installed. It writes
   `verification/gate-run.txt`, the tree printed before and after and compared with `cmp`.
   - **The negative harness reruns once,** since a file is added under `tests/`. Its transcript
     goes whole in `verification/gate-negative-tests.txt`, and case j's in
     `ci-negative-test.txt`, as the harness's own header says.
7. **Docs:**
   - every changed file, and every standard naming them;
   - `README.md`'s `tests/` paragraph;
   - `git grep` for `_VOLUME_FLOOR`, `_POWERS_OF_TWO`, `_shares_its_display`, `_resolve`,
     `_bindings` and `pins_the_same_values`.
8. **Version:** the `[Unreleased]` entry above. The version stays 0.0.1.
9. **Standards retrospective,** in its own change set, each edit approved by the owner with
   AskUserQuestion and verified against the shipped code and this spec's transcripts:
   - `vital/parameter-map.md`: the excuse and its counts, the third branch's issue, the derived
     `to_normalized`;
   - `vital/measures.md`: one file read through rootpath, the AST test gone;
   - `index.yml`'s `vital:` entries kept in step;
   - `Proposals sent upstream:` recorded, and any base proposal presented before the spec is
     done.

## Errata (earlier folders stay as recorded)

- **The fourth review's Decision 3:** "a single definition would need a shared `tests/support`
  module on pytest's `pythonpath`". A data file read through `pytestconfig.rootpath` needs no
  gate change.
- **The fourth and fifth reviews:** `_shares_its_display` was said to excuse "a failure where it
  holds". Because the curves are monotone, it held wherever `back` shows the display.

## Critical files

- `src/patchbay_vital/parameters.py`
- `tests/unit/test_parameters.py`
- `tests/integration/test_vital_plugin.py`
- `tests/data/pinned-values.txt` (new)
- `CHANGELOG.md`
- in the retrospective only: `agent-os/standards/vital/parameter-map.md`,
  `agent-os/standards/vital/measures.md` and `agent-os/standards/index.yml`

## Verification

- `scripts/gate.sh` exits 0, with Vital installed.
- The negative harness has no unexpected cases.
- `floor-pass.txt`: NEITHER 0, and no difference from `e852aac`.
- `mutation.txt`: each mutant fails its named test.
- Reported at the end, listed apart for the owner to commit:
  - the feature's files;
  - the retrospective's files;
  - the new issue's number.
