# Revision after PR 14's Fifth Review — Shaping Notes

Shaped 2026-11-12 in plan mode with this repository's customized `/agent-os:shape-spec`. Each
finding of the review was checked against HEAD (`d21f160`) before any question, read only, and the
owner then answered seven questions.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The fifth review of PR 14, "Review of the fourth-review revision (`3569cca`, `d21f160`)"
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6835661576, 2026-11-12
20:53Z). In the owner's words, "Let's address the latest round of review on pr 14".

- It finds no shipped value wrong. Its six checks and ten findings are about whether the evidence
  supports what the docs say.
- The revision is on the same branch, so PR 14 still closes #13 and #15. It changes
  `src/patchbay_vital/parameters.py`, its unit tests, and no gate file. No stage, commit, push or
  pull request edit by an agent.

## What was checked while shaping

Read-only, against `d21f160`, with the shipped code.

- **Finding 1 holds by reading.** The fourth-review `Vec.Nf` tries the nearest quotient `q` first
  and replaces it only with a strictly closer landing candidate. `q` is the float32 nearest the
  exact quotient, so none is closer: wherever `q` lands, `N'` is `q`, and CHANGEDx and NCHANGEDx
  are 0 whatever the shipped code does.
- **Finding 4 is half right.** A seeded search of 177,883 constructed linear scales (now
  `verification/guards.txt`):
  - **`settable` is always true.** `_landing`'s normalized value is inside [0, 1] for every preset
    tried, 711,532 of them.
  - **The other-side check is reachable.** 4,929 of those presets are an end the scale does not
    hold. On 3,387 the float32 on the other side is landed on by a normalized value above 1. So
    the review's "both ends are always held" is false: a maximum need not be held. On
    `NormalizedScale(linear, -1.0, 2 ** 24)`, the fourth-review revision's own guard test, the
    maximum is unheld and the float32 past it has the normalized value 1.000000238418579.
  - The sentence is written nowhere in the repository (`git grep`), only in the review.
- **Finding 10.** At issue #13's value and on 2,734 sampled first-branch values of `volume`, the
  normalized value computed on the way, `N(P1)`, equals the scale's own for the preset returned.
- **Cost.** This branch's `from_normalized`, `to_preset` and `to_normalized` took about 45 µs a
  value, so both trees about 85 µs: roughly 25 CPU-hours a group. (Measured again before the run,
  with the branch read from each result: 37 and 83 µs, 36 CPU-hours, 3.1 hours wall a record.)

## Shaping answers

In the owner's words:

- **The two zero counts:** "1, and add evidence that shares nothing with the new code:
  - Retire CHANGEDx and NCHANGEDx as evidence in the standard and CHANGELOG, add the unit test
    and its mutant, and widen the rule as proposed.
  - Then count directly: main's shipped to_normalized and to_preset against this branch's, the
    scalar methods themselves, value by value over every float32 normalized value, with the
    outputs compared and the differences counted by record. Start with the 13 records the fix is
    known to touch (volume and the 12 envelope records) and say what it shows. Before running
    the rest, present what all 69 groups would take in CPU-hours and wall time, for the owner to
    start unattended or decline.
  - The transcript prints both trees (main's commit and this branch's) and the machine, and the
    standard cites this count where it cited the two 0s.
  No negative control is needed for columns that are no longer cited."
- **The branch counts:** "1, combined with the direct main-against-branch count already asked
  for: on volume, one pass calls the shipped to_preset (this branch's and main's) on every float32
  normalized value in those binades, reads the branch from the shipped result, splits at the
  floor exactly, and records the differences from main. The 12 envelope records get the same
  direct comparison for to_normalized. Outside the binades run, say in the transcript why no value
  there can leave KEPT, with the check that shows it, not by assertion. Everything still cited
  from the fourth-review sweep is labelled the reproduction's, with the size of its check against
  the shipped methods."
- **The two conditions:** "1. Two things shown, not argued:
  - settable being always true: shape.md gives the reason (the clamped preset's quotient rounds
    into [0, 1], and the step is kept only there) and the transcript shows it over the committed
    map's scales and the constructed ones tried, with the count.
  - The other-side refusal is reachable on a constructed scale whose maximum is unheld, so a
    unit test holds it at one of the 3,387 cases found, with a mutant that drops the holds check
    failing that test by name. shape.md records the counterexample to "both ends are always
    held" and corrects the sentence wherever it was written."
- **Branch 1:** "2. _resolve's docstring states the invariant the None keeps, and a unit test
  holds it at the pinned floor values: to_normalized(display) ==
  scale.to_normalized(to_preset(display)). Decision 8's "reuses" is corrected as an erratum. If
  the volume run already being made can count, at no extra cost, the values where N(P1) differs
  from N'(landed), record the count in shape.md as information for a later spec; do not change the
  code on it."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`,
  `base/process/ownership`, `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and
  `vital/plugin-state`. Snapshot in `standards.md`, base at `e31f7db`.
- **The envelope group:** "1. The transcript prints the 12 records' group key field by field, and
  also shows that the methods called read nothing from a record but those fields (so identical
  keys mean identical results), by pointing at the shipped code. Run the full paths, not
  to_normalized alone: 2.5 hours unattended is fine."
- **The pass's scope:** "1. Start it unattended, floor binades first, with the stop at 8 hours as
  proposed. If any difference from main appears outside the 16,069,858 volume values and the
  envelope group's 126 powers of two, stop and present at once instead of finishing.
  The other 67 groups are not counted directly: declined by the owner at about 2.5 hours wall
  a group. For them the standard and CHANGELOG say what holds the claim: the fourth-review
  sweep, labelled the reproduction's with the size of its check against the shipped methods, and
  the unit test with its mutant that a value main's quotient lands on is returned unchanged."

## Decisions

1. **CHANGEDx and NCHANGEDx are retired as evidence**, in the standard and the CHANGELOG, with no
   negative control. What holds the claim instead:
   - `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it`, with mutant
     M15;
   - the direct count (Decision 2), on `volume` and the envelope group;
   - for the other 67 groups, the fourth-review sweep, labelled the reproduction's.
2. **The direct count shares nothing with the new code.** Two pools of processes each import
   `patchbay_vital` from one tree, `main`'s (`558b85b`, extracted with `git archive`) or this
   branch's, and call that tree's scalar methods on every float32 normalized value.
   - **Compared on each value:** the held preset and its display (forward, unchanged since
     `main`), `to_preset(display)`, `to_normalized(display)` and `scale.to_normalized(held
     preset)`.
   - **The branch is read from this branch's result**, which is the curve's float32, what a set
     of it holds, or the float32 on its other side. The three are distinct, so the result names
     its branch, and a reordering inside `_resolve` moves the counts. A control shows that
     (Decision 2's last point).
   - **Every count is split at the floor exactly**, by held preset ≤ 2 ** -43, value by value.
   - **Every value of `volume` is run**, the floor binades first, so nothing lies outside the run
     and no argument stands in for a check.
   - **The envelope group is counted once**, by `env_1_delay`, after the 12 records' group key is
     printed field by field with what each method called reads, from the shipped source.
   - **It stops at once** on a difference from `main` outside `volume`'s moved values and the
     envelope group's powers of two.
   - **The other 67 groups are not counted directly: declined by the owner.**
   - **A control:** the same pass over one floor binade with branches 1 and 2 swapped in a
     scratch copy.
3. **`_resolve` drops `settable` and asks `scale.holds(other)`.**
   - **`settable` is always true.** The preset is clamped to the scale, so its exact quotient is
     at most `(maximum - minimum) / span`. `span` is that difference rounded to float32, so the
     quotient is no more than half a float32 step past 1, and its nearest float32 is at most 1. It
     is at least 0, the minimum's quotient. `_landing` keeps its step only inside [0, 1].
     `verification/guards.txt` shows it on the committed map's scales and the constructed ones.
   - **The other-side check is real**, and now reads as the docstring's rule: "where the scale
     holds it". `holds` carries the range check, which M3 already kills.
   - `test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken` holds it on a valid
     record, and M16 fails that test by name.
4. **Branch 1 keeps `(landed, None)`.** `_resolve`'s docstring states the invariant, and
   `test_a_display_s_normalized_value_is_its_preset_s_own` holds it at the pinned floor values.
   The direct count records where the value computed on the way differs (PN). It differs on none of
   `volume`'s 15,761,472 first-branch values (PN 0, `verification/direct-count.txt`, section 2):
   information for a later spec, and the code does not change on it.
5. **The 5.4% figure is recorded with its script**, and the standard takes what it prints.
6. **The duplicates check compares each table whole**, the closing line with its run time removed.
7. **The AST test reads every binding of the name**, at any depth: a name stored or deleted, an
   import alias, a function or class, a `global` or `nonlocal`, an argument. It passes only on one
   binding, a top-level assignment to a plain literal that is a tuple of floats, and catches every
   error `ast.literal_eval` documents.
8. **The module docstring says the rule is ordered.**
9. **The negative harness is not rerun.** `base/process/verification-gate.md` asks for a rerun
   "whenever the gate's files change, and whenever a spec adds, removes or renames a file under a
   directory the tests copy". This revision changes no gate file and adds, removes or renames no
   file under `scripts`, `src`, `tests` or `agent-os/standards`.
10. **The earlier spec folders stay as recorded**, with their errata listed below.

### Where the implementation departs from the plan

- **`verification/sweep-check-size.txt` is the second section of
  `verification/arbitrary-displays.txt`.** One script reads the branch from the shipped result for
  both samples.
- **The second branch returns `(other, None)`**, as planned, so `to_normalized` lands once more on
  its 308,386 values. `holds` gives no normalized value back, and the invariant of Decision 4
  holds there by the same line as on the first branch. M18 shows the test catches the other
  choice.
- **The pinned record for the other-side refusal is made up, not one of the 3,387.** The search's
  cases are scales alone. `to_preset` reaches the second branch past the maximum only where the
  curve shows the maximum's display at the float32 past it and another at what a set holds, on a
  record that validates. That takes a curve built for it:
  `NormalizedScale(linear, -0.89999920129776, 1.0)` with
  `DisplayCurve(linear, multiply=0.9999999478459358, offset=1073741823.0)`, at the display
  2 ** 30. It is a case of the same kind: the maximum unheld, and the normalized value
  1.0000001192092896 landing on the float32 past it (`verification/guards.txt`, section 3).
- **M17 and M18 are added** beside the planned mutants: the normalized value computed on the way
  returned from the first branch, and from the second.

## The review's findings

| # | Finding | Outcome |
|---|---|---|
| 1 | CHANGEDx and NCHANGEDx are 0 by construction | Retired; a unit test and M15; the direct count (Decisions 1, 2) |
| 2 | The standard and the CHANGELOG cite the 0s | Both cite the direct count; the rule widened (the retrospective) |
| 3 | The branch counts are the reproduction's | `volume`'s read from the shipped result; the rest labelled, with the check's size |
| 4 | Two conditions always true | `settable` removed and shown; the other is reachable, tested, M16 (Decision 3) |
| 5 | 5.4% has no recorded source | `verification/arbitrary-displays.txt` (Decision 5) |
| 6 | "At or below 2 ** -43" not shown | Every count split at the floor exactly (Decision 2) |
| 7 | The duplicates check skips the closing line | `verification/duplicates.txt` (Decision 6) |
| 8 | The AST test's gaps | Every binding, every error; M19 to M21 (Decision 7) |
| 9 | The docstring hides the order | Rewritten (Decision 8) |
| 10 | Branch 1 lands twice | Kept; the invariant stated and tested, M17 and M18 (Decision 4) |

## Errata in the earlier spec folders, which stay as recorded

In `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`:

- **`sweep.py`'s docstring** says "Neither CHANGEDx nor NCHANGEDx is 0 by how this script is
  built". Both are: its `N'` keeps `main`'s quotient wherever it lands.
- **shape.md, the CHANGELOG and the standard** give the two 0s as evidence that nothing changed
  where `main`'s value held.
- **Decision 8**, "`MappedParameter.to_normalized` reuses `to_preset`'s": only where `to_preset`
  kept the curve's float32. On the first and second branches `to_normalized` lands again.
- **"At or below 2 ** -43"** is stated as counted. The sweep counts by normalized binade, and
  binade -56 straddles the floor.
- **"Line for line"** (`sweep-afterwards.txt`, shape.md, the standard): the comparison skipped
  each table's closing line.
- **5.4% of 20,000 displays** had no recorded script.
- **PLUGIN 15,761,472, OTHER 308,386 and UNHELD 0** are given as counts of the shipped rule. They
  are the numpy reproduction's, checked against the shipped methods on 200,010 values a group.

In the fifth review itself: "both ends are always held" (finding 4). A scale's maximum need not be
held; `verification/guards.txt` counts 4,929 unheld ends among 177,883 constructed scales.

## Open

- **#8's findings 1 and 3**, as before.
- **A single definition of the pinned tuples**, for the next gate spec, as before.

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
- `base/testing/tests` — the three new tests on pinned and constructed values, and the AST test.
- `base/process/verification-gate` — the gate unchanged; its record; when the harness reruns.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issues edited without
  attribution.
- `vital/parameter-map` — the two inverses, the counting rule and what it cites.
- `vital/measures` — the pinned values held equal by the AST test.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load test, unchanged.

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

**Results (2026-11-13):** `scripts/gate.sh` exits 0 on the final tree, the retrospective's edits
in it: steps 1 to 6 pass, 520 tests, Vital installed, the tree the same before and after
(`verification/gate-run.txt`). This file's Results line and the transcript itself were written
after the run; the gate reads neither. No gate file changed, so the negative harness was not
rerun.

**The direct count (2026-11-12 to 13, `verification/direct-count.txt`).** `main`'s shipped
methods (commit `558b85b`) against this branch's, on every float32 normalized value:

- `volume`, 1,065,353,217 values in three sections. The display's preset differs from `main`'s on
  16,069,858, every one at a held preset at or below 2 ** -43: 15,761,472 on the first branch and
  308,386 on the second, read from the shipped result, none on the third. The normalized value
  differs on the 308,386 alone. Above 2 ** -43, and in every binade outside -95 to -56, every
  value is kept and nothing differs. The counts equal the fourth-review reproduction's.
- The control, branches 1 and 2 swapped on binade -56: 99,636 and 99,796, so the counts are read
  from the result.
- The 12 envelope records have one group key, and the methods read nothing else of a record.
- `env_1_delay`, 1,065,353,217 values: the normalized value differs at 126 held powers of two,
  one in each binade from -126 to -1, and nothing else differs.
- No stop was reached. Measured cost: 39 and 83 µs a value, about 36 CPU-hours and 3.1 hours wall
  a record on 12 processes; the run took 1.4 + 2.3 + 3.9 hours.
- Section A's listings of the tree before and after differ in `git status` alone, the spec's own
  files and the test module having been written meanwhile; the blobs of the files the count reads
  are the same. The wrapper changed between the sections, to stop at a failed count and write
  each line as it comes. Both are shown in the transcript.

**The smaller transcripts.** `verification/guards.txt`, `duplicates.txt` (14 of 14 whole tables
the same), `arbitrary-displays.txt` (1,108 of 20,000, 5.54%; and the fourth-review sample's
196,952 / 2,989 / 69), `mutation.txt` (M0 passes; M1 to M7, M9 to M16 and M18 to M21 fail as
headed; M8, M8b and M17 pass, M17 equivalent at the pinned values) and `plugin-probe.txt` (Vital
1.6.4 holds the map's value at each pinned value). `src/patchbay_vital/parameters.py` and
`tests/unit/test_parameters.py` are at the blobs those ran on, `e49d5e9` and `7e39546`.

**Docs (step 7):** read against the shipped code after the change:

- `src/patchbay_vital/parameters.py`: the module docstring (the rule's order), `to_preset`'s and
  `_resolve`'s docstrings (the floor claim's source, the invariant, why no [0, 1] check is asked).
- `tests/unit/test_parameters.py`: the docstrings citing counts.
- `CHANGELOG.md`, issue #15's entry; issue #15 itself, its paragraph of 2026-11-12 read back.
- `agent-os/standards/vital/parameter-map.md`, `vital/measures.md` and `index.yml`'s `vital:`
  entry, in the retrospective below.
- `git grep` outside `agent-os/specs`: `CHANGEDx` only where the standard retires it; `5.4%`,
  "line for line" and `settable` nowhere; "reuses" only of the host's containers.
- `README.md` and `CLAUDE.md` name nothing this changes.

**Version (step 8):** issue #15's entry under `[Unreleased]` `### Fixed` in `CHANGELOG.md` names
this spec, the direct count and what holds the other 67 groups. The version stays 0.0.1.

## Standards Retrospective

Approved by the owner on 2026-11-13, each edit by AskUserQuestion, with two changes asked for: D
says plainly that the other 67 groups were not counted directly and names what holds the claim,
and A cites the transcript by path with its machine and both trees' commits. Their own change
set, verified against the shipped code and this spec's transcripts.

- `vital/parameter-map.md`:
  - the branch counts are the direct count's, split at the floor value by value, and the
    fourth-review sweep's are a reproduction's (`verification/direct-count.txt`);
  - the rule's order, and the second branch asking `NormalizedScale.holds`
    (`MappedParameter._resolve`; `test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken`,
    M16; `test_a_display_s_normalized_value_is_its_preset_s_own`);
  - 5.4% is 5.54%, 1,108 of 20,000 (`verification/arbitrary-displays.txt`);
  - "line for line" is each table whole (`verification/duplicates.txt`);
  - `CHANGEDx` and `NCHANGEDx` retired, and the rule widened: a count a reproduction's definition
    forces to 0 is not evidence in any form, and a fix is counted by the old tree's and the new
    tree's shipped methods called directly;
  - the other 67 groups not counted directly, by the owner's decision, held by
    `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it` (M15) and the
    reproduction with its 200,010-value check.
- `vital/measures.md`: `test_the_integration_module_pins_the_same_values` fails unless the name
  is bound once, at the top level, to a tuple of floats (M19 to M21).
- `agent-os/standards/index.yml`: the `vital:` `parameter-map` entry in step with the widened
  rule. The `base:` section is untouched.
- No base standard is taught anything: `base/process/verification-gate` already says an
  assertion no mutation trips is not known to assert anything.

Proposals sent upstream: none
