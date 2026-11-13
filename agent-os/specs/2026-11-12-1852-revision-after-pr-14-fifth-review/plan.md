# Revision after PR 14's fifth review

Spec folder: `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/`

## Context

The fifth review of PR 14, "Review of the fourth-review revision (`3569cca`, `d21f160`)"
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6835661576, 2026-11-12
20:53Z). It finds no shipped value wrong. Its ten findings are about whether the evidence
supports what the docs say:

- CHANGEDx and NCHANGEDx are 0 by how the sweep's `N'` is built, yet the standard and the
  CHANGELOG cite them as evidence (findings 1, 2).
- The branch counts are the numpy reproduction's, and "at or below 2 ** -43" is read off a
  binade that straddles the floor (3, 6).
- Two conditions in `_resolve` are called always true (4); a 5.4% figure has no source (5); the
  duplicates check skips each table's closing line (7); the AST test has gaps (8); the module
  docstring hides that the rule is ordered (9); branch 1 lands twice (10).

Same branch, so PR 14 still closes #13 and #15. No gate file changes. No stage, commit, push or
pull request edit by an agent.

## What was checked while shaping (read-only, at `d21f160`)

- **Finding 1 holds by reading.** `Vec.Nf` tries `q` first and replaces it only with a strictly
  closer landing candidate; `q` is the nearest float32 to the exact quotient, so none is closer.
- **Finding 4 is half right.**
  - `settable`: `_landing`'s normalized value was inside [0, 1] for every preset tried on
    177,883 constructed scales (both ends and the float32 inside each).
  - The other-side check is reachable. 4,929 of those scales have an unheld end, and on 3,387
    the float32 past it is landed on by a normalized value above 1. On
    `NormalizedScale(linear, -1.0, 2 ** 24)`: the maximum is unheld, `other` is 16777218.0, and
    its normalized value is 1.000000238418579. So the review's "both ends are always held" is
    false. The sentence is written nowhere in the repository (`git grep`), only in the review.
- **Finding 10.** At issue #13's value and on 2,734 sampled branch-1 values of `volume`,
  `N(P1)` equals `N'(landed)` on every one.
- **Cost.** This branch's `from_normalized` + `to_preset` + `to_normalized` take about 45 µs a
  value; with `main`'s beside them, about 85 µs: roughly 25 CPU-hours a group over
  1,065,353,217 values, 2.5 hours wall on 10 processes.

## Decisions (owner, 2026-11-12, AskUserQuestion)

1. **CHANGEDx and NCHANGEDx are retired as evidence** in the standard and the CHANGELOG, with no
   negative control. In their place:
   - a unit test, with a mutant, that a value `main`'s quotient lands on is returned unchanged;
   - the standard's rule widened: a count the reproduction's definition forces to 0, in any
     form, is not evidence;
   - a direct count (Decision 2), which the standard cites where it cited the two 0s.
2. **A direct count, sharing nothing with the new code:** `main`'s shipped scalar methods against
   this branch's, value by value, over every float32 normalized value, on `volume` and on the
   envelope group.
   - Compared on each value: `to_preset(display)`, `to_normalized(display)` and
     `scale.to_normalized(held preset)`. Differences are counted by record and binade.
   - On `volume` the branch is read from this branch's shipped result (the curve's float32, what
     a set of it holds, or the other side), and every count is split at the floor exactly, by
     held preset ≤ 2 ** -43.
   - `volume`'s floor binades (-96 to -55) run and are reported first.
   - The envelope group is counted once, by `env_1_delay`. The transcript prints the 12 records'
     group key field by field and points at the shipped code to show the methods called read
     nothing else from a record.
   - Started unattended, re-timed on 200,000 values first. It stops and presents if the estimate
     passes 8 hours, or at once if any difference from `main` appears outside `volume`'s
     16,069,858 values and the envelope group's 126 powers of two.
   - The transcript prints both trees (`main`'s commit and this branch's) and the machine.
   - **The other 67 groups are not counted directly: declined by the owner** at about 2.5 hours
     wall a group. For them the standard and CHANGELOG name what holds the claim: the
     fourth-review sweep, labelled the reproduction's with the size of its check against the
     shipped methods, and the unit test with its mutant.
3. **`_resolve` drops `settable` and asks `scale.holds(other)`.**
   - `settable` is always true: the clamped preset's quotient rounds into [0, 1] and the step is
     kept only there. shape.md gives the reason; a transcript shows it over the committed map's
     scales and the constructed ones tried, with the count.
   - The other-side refusal is held by a unit test at one of the constructed cases, and a mutant
     dropping the `holds` check fails that test by name.
   - shape.md records the counterexample to "both ends are always held".
4. **Branch 1 keeps `(landed, None)`.** `_resolve`'s docstring states the invariant the `None`
   keeps, `to_normalized(display) == scale.to_normalized(to_preset(display))`, and a unit test
   holds it at the pinned floor values. Decision 8's "reuses" is an erratum. The `volume` pass
   counts where `N(P1)` differs from `N'(landed)` on branch-1 values, as information for a later
   spec; the code does not change on it.
5. **Steps 2 to 5:** "Confirmed as listed". No visuals; references below; mission unchanged;
   standards: the core five, `base/testing/tests`, `base/process/verification-gate`,
   `base/process/standards-retrospective`, `base/process/standards-index`,
   `base/process/ownership`, `vital/parameter-map`, `vital/measures`, `vital/preset-tests`,
   `vital/plugin-state`.

### Decided in shaping, within those answers

6. **Finding 5:** the 5.4% figure gets a script and transcript; the standard takes the figure the
   transcript prints.
7. **Finding 7:** the duplicates check is rerun over the fourth-review `sweep.txt`, comparing
   each table whole, closing line included with its run time stripped. The standard's "line for
   line" stands only if all 14 still match.
8. **Finding 8:** the AST test finds every binding of the name anywhere in the module and fails
   by name unless there is exactly one, a top-level plain assignment to a tuple of floats; it
   catches every error `ast.literal_eval` raises.
9. **Finding 9:** the module docstring says the rule is ordered, and "whichever".
10. **The negative harness is not rerun:** no gate file changes and no file is added, removed or
    renamed under `scripts`, `src`, `tests` or `agent-os/standards`.
11. **The earlier spec folders stay as recorded**, their errata listed in this shape.md.

## The findings

| # | Finding | Outcome |
|---|---|---|
| 1 | CHANGEDx, NCHANGEDx 0 by construction | Retired; unit test and mutant; direct count (Decisions 1, 2) |
| 2 | The standard and CHANGELOG cite the 0s | Both rewritten to cite the direct count; rule widened |
| 3 | Branch counts are the reproduction's | `volume`'s read from the shipped result; the rest labelled, with the check's size |
| 4 | Two conditions always true | `settable` removed, shown; the other-side check reachable, tested (Decision 3) |
| 5 | 5.4% has no source | Script and transcript (Decision 6) |
| 6 | "At or below 2 ** -43" not shown | Counts split at the floor exactly (Decision 2) |
| 7 | Duplicates check skips the closing line | Rerun whole (Decision 7) |
| 8 | AST test gaps | Every binding; every `literal_eval` error (Decision 8) |
| 9 | Docstring hides the order | Rewritten (Decision 9) |
| 10 | Branch 1 lands twice | Kept, invariant stated and tested (Decision 4) |

## Task 1: Save spec documentation

Create the spec folder with `plan.md` (this plan), `shape.md` (the template's sections, the
shaping checks, the owner's answers in their words, the findings table, the errata), 
`standards.md` (full text of the standards in Decision 5, base at the pinned commit) and
`references.md`. No `visuals/`.

## Task 2: `src/patchbay_vital/parameters.py`

- **Module docstring (finding 9):** below the floor `to_preset` gives, in this order, what a set
  of the curve's float32 holds where that shows the display, else the float32 on its other side
  where the scale holds it and it shows the display. Cite this revision's transcripts.
- **`_resolve` (finding 4):** remove `settable`; branch 2 becomes
  `scale.holds(other) and curve.to_display(other) == display`, returning `(other, None)`.
- **`_resolve`'s docstring (finding 10):** the `None` keeps
  `to_normalized(display) == scale.to_normalized(to_preset(display))`; `N(P1)` lands on the same
  preset but need not be `N'(landed)`.
- **`to_preset`'s docstring (findings 3, 6):** the floor claim cites the direct count, split at
  the floor; anything still from the fourth-review sweep is called the reproduction's.

## Task 3: `tests/unit/test_parameters.py`

- **A landing quotient is returned unchanged (Decision 1):** on a scale and preset where both the
  nearest quotient and a neighbour land, `to_normalized` is the nearest quotient. Found by a
  seeded search first; the pinned case goes in the test.
- **The other-side refusal (Decision 3):** a record built with `_record` on a scale whose maximum
  is unheld, at a display where the float32 past the maximum shows the display and a normalized
  value above 1 lands on it; `to_preset` keeps the curve's float32. If no valid record reaches
  it, stop and present; a scale-level test alone is not what was asked.
- **The invariant (Decision 4):** at `_VOLUME_FLOOR`,
  `to_normalized(display) == scale.to_normalized(to_preset(display))`.
- **`test_the_integration_module_pins_the_same_values` (finding 8):** `ast.walk` for every `Name`
  stored or deleted, import alias, and function or class of that name; exactly one, the sole
  target of a top-level `Assign` or `AnnAssign`; `literal_eval` under
  `(ValueError, TypeError, SyntaxError, MemoryError, RecursionError)`; the value a tuple of
  floats equal to this module's.
- Docstrings citing counts are updated to the direct count's.

## Task 4: The direct count (`verification/direct-count.txt`)

Scratchpad scripts, embedded in the transcript as before.

- **`main`'s tree:** `git archive 558b85b src | tar -x` into the scratchpad. Each worker is
  spawned with one side's `src` first on `sys.path`, and prints the `parameters.py` it imported
  with its blob. Each side reads its own `data/parameters.json`.
- **The header:** both commits, `git status --porcelain=v1`, the blob of every file read, the
  machine and Python; the tree printed again after the run and compared with `cmp`.
- **Timing first:** 200,000 values, the estimate printed; stop at more than 8 hours.
- **Stage A, `volume`, binades -96 to -55;** then **stage B, the rest of `volume`;** then
  **stage C, `env_1_delay`**, after the 12 records' group key, field by field, and the lines of
  `parameters.py` showing what each method called reads.
- **Columns per binade:** PRESET, NORM and HELDNORM (the three comparisons, differing from
  `main`); KEPT, PLUGIN, OTHER, UNHELD and UNKNOWN read from this branch's result; each split
  at and below, and above, a held preset of 2 ** -43; on branch-1 values, `N(P1) != N'(landed)`.
- **Stops:** a difference outside `volume`'s 16,069,858 values or the envelope's 126 powers, or
  any UNKNOWN or UNHELD.
- **A control:** the same pass on one floor binade with branches 1 and 2 swapped in a scratch
  copy (M7), showing the counts read from the shipped result move.
- **Then present to the owner** what the pass shows. If its branch counts differ from
  15,761,472 / 308,386 / 0, stop and present before any doc cites either.

## Task 5: The smaller transcripts

- **`verification/guards.txt` (Decision 3):** `_landing`'s normalized value inside [0, 1] over
  the committed map's 69 scales (ends, their neighbours and seeded float32 presets) and seeded
  constructed scales, with counts; the constructed scales with an unheld end, and those where a
  normalized value above 1 lands on the float32 past it.
- **`verification/arbitrary-displays.txt` (finding 5):** 20,000 displays uniform over `volume`'s
  range, seed 8, the share taking the third branch under the shipped code.
- **`verification/duplicates.txt` (finding 7):** the 14 records against their groups, each table
  whole.
- **`verification/sweep-check-size.txt` (finding 3):** of the fourth-review sweep's 200,010
  checked values, how many reach each branch on `volume`, recomputed from its `sample()`.

## Task 6: Mutation (`verification/mutation.txt`)

In a scratch copy, each mutant with its diff, the tests that fail, and the exit status:

- `_landing` preferring the step when the nearest lands: fails the new landing test by name.
- Branch 2 without `scale.holds(other)`: fails the other-side test by name.
- Branch 1 returning `N(P1)`: shown against the invariant test (expected to pass where the two
  are equal; the transcript says which).
- The AST test: an augmented assignment, a reassignment inside a module-level `if`, and a set
  holding an unhashable value, each failing by name.
- M0 and the fourth-review mutants M1 to M14 rerun, since `_resolve` changed.

## Task 7: The Vital probe (`verification/plugin-probe.txt`)

`_resolve` changed shape, so the fourth-review probe is rerun unchanged at the pinned values
with Vital 1.6.4: a set holds the map's value at each.

## Task 8: CHANGELOG and issues

- **`CHANGELOG.md` `[Unreleased]`, issue #15's entry:** "against `main`'s results, nothing
  changed where a set of `main`'s value held it" is replaced by the direct count on `volume` and
  the envelope group, and, for the other 67 groups, the reproduction's sweep with its check's
  size and the unit test. Branch counts are attributed to the pass they come from.
- **#15:** a "Revised 2026-11-12 (after PR 14's fifth review)" paragraph, read before and after
  the edit, no attribution. No pull request edit.

## Task 9 (FINAL): Verification gate

1. `scripts/gate.sh`, steps 1 to 6, on the final tree; `verification/gate-run.txt` with the tree
   printed before and after and compared with `cmp`.
7. **Docs:** every file changed and every standard naming them, read against the shipped code;
   `git grep` for `CHANGEDx`, `5.4%`, "line for line", `settable` and "reuses".
8. **Version:** the `[Unreleased]` entry above; 0.0.1 stays.
9. **Standards retrospective**, its own change set, each edit approved by the owner with
   AskUserQuestion, verified against shipped code and this spec's transcripts:
   - `vital/parameter-map.md`: the two 0s retired and the rule widened (finding 2); the 5.4%
     figure sourced (5); "at or below 2 ** -43" as the split count shows (6); the duplicates
     sentence (7); branch counts attributed; the other-side refusal and its test;
   - `vital/measures.md`: the AST test's wider reach;
   - `index.yml`'s `vital:` entries in step; `base:` untouched;
   - `Proposals sent upstream:` recorded, `none` unless the retrospective finds a base change,
     which is presented to the owner before the spec is done.

## Errata to record in shape.md (earlier folders stay as written)

In `2026-11-12-1319-revision-after-pr-14-fourth-review/`:
- `sweep.py`'s docstring, shape.md and the CHANGELOG say CHANGEDx and NCHANGEDx are not 0 by how
  the script is built. They are.
- Decision 8, "`to_normalized` reuses `to_preset`'s": only on the kept and other-side branches.
- "At or below 2 ** -43" stated as counted, where the transcript counts by binade.
- "Line for line": the comparison skipped each table's closing line.
- 5.4% of 20,000 displays had no recorded script.
- The branch counts given as counted of the shipped rule; they are the reproduction's.

## Critical files

- `src/patchbay_vital/parameters.py` (`_resolve`, `_landing`, the docstrings)
- `tests/unit/test_parameters.py` (three new tests, the AST test)
- `CHANGELOG.md`
- `agent-os/standards/vital/parameter-map.md`, `measures.md`, `index.yml` (retrospective only)
- Reused: `_record`, `_what_a_set_holds`, `_VOLUME_FLOOR` in the test module; `sample()`,
  `group_key`, `duplicates.py` and `mutate.sh` from the fourth-review transcripts.

## Verification

- `scripts/gate.sh` exits 0, all tests passing with Vital installed.
- `verification/direct-count.txt`: no difference from `main` outside the expected values, no
  UNKNOWN or UNHELD, both trees printed.
- `verification/mutation.txt`: each new mutant fails its named test.
- `verification/plugin-probe.txt`: Vital holds the map's value at each pinned value.
- Reported at the end: the feature's files and the retrospective's, listed apart, for the owner
  to commit.
