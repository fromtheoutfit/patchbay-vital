# Revision after PR 14's Fourth Review — Shaping Notes

Shaped 2026-11-12 in plan mode with this repository's customized `/agent-os:shape-spec`. Each
check and finding of the review was verified against HEAD (`f3625d1`) before any question, read
only, and the owner then answered five questions.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The fourth review of PR 14, "Review of f3625d1"
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6831965378, 2026-11-12
18:12Z). In the owner's words, "Let's read through the latest round of review on PR 14 and address
the issues".
- It makes seven checks. Two fail outright: the tie rule is untested, and the `[0, 1]` guard is
  reachable. Two more are partly met.
- It adds three other findings.

The revision is on the same branch, so PR 14 still closes #13 and #15. It changes behaviour in
`src/patchbay_vital/` and no gate file. CHANGELOG entry, gate green, `verification/gate-run.txt`.
No stage, commit, push or pull request edit by an agent.

## What was checked while shaping

Read-only, against `f3625d1`, with the shipped code. The samples are for shaping only; the
evidence is the full sweep (Decisions 1 and 2).

- **`next_float32`'s `toward` (check 1).** `next_float32(1.0, 1.0 + 1e-12)` is
  1.0000001192092896, where numpy's float32 `nextafter` gives 1.0.
  - `tests/unit/test_float32.py:26` steps a float32 with numpy (`_next_up`), so "the one way the
    package and its tests step a float32" is false.
- **The guard (check 3).** It is reachable on `NormalizedScale(linear, -1.0, 16777216.0)`:
  - the span is 2 ** 24, and `to_preset(1.0)` is 16777215.0;
  - the float32 above 1 lands on 16777216.0;
  - with the guard, `to_normalized(16777216.0)` is 1.0, and `holds(16777216.0)` is false;
  - without it, `to_normalized` returns 1.0000001192092896.
- **The sweep (check 4).** `Vec.fixed` rewrites P1 only where `~held`, and `Vec.Nf` steps only
  where `S(q) != p`, so CHANGEDx and NCHANGEDx are 0 by the sweep's construction. Its `check`
  never compares the BOTH and NONE flags, and its docstring says 200,007 values where `sample()`
  builds 200,010.
- **Sample 1:** seed 15, 60,000 float32 normalized values of `volume` at or below 2 ** -43, drawn
  uniformly over their bit patterns.
  - **Excused values:** 57,459 under the shipped rule (`back != preset`). On 54,967 of them,
    `back` is not a float32 neighbour of the preset, so the review's form of the excuse,
    `back in (below, above)`, would fail the property on them.
  - **A narrower excuse fails too:** requiring a *held* neighbour to show the display fails on
    4,487 of the 57,459.
  - **Ties:** the curve's float32 is unheld with both neighbours qualifying on 1,631 values, 757
    of them exact ties, where only the stable sort decides. The plugin's own value differs from
    the shipped pick on 877 of the 1,631.
- **Sample 2:** seed 16, 60,000 values drawn the same way, 1,646 of them with the curve's float32
  unheld.
  - **What a set of it holds** (`S(N'(P1))`) is a float32 neighbour of it on all 1,646, and shows
    the display on 1,622.
  - **On the other 24,** exactly one neighbour qualifies, and none has two or none.
  - **The plugin's own rule** gives a held preset that shows the display on every value, and
    differs from the shipped pick on 910 of the 1,646.
- **Sample 3:** seed 17, values drawn the same way. The shaping script carried one random stream
  on from the first rule to the second, so the two figures are of different draws (corrected
  while implementing):
  - the first 40,000 draws, under the rule shipped at `f3625d1`: 38,337 excused;
  - the next 40,000, under the plugin's own rule as simulated while shaping: 38,269 excused;
  - recounted on the first 40,000 under the shipped plugin's own rule: 38,338 excused.

  Each of those holds at its own totals:
  - the narrowed excuse (the float32 next to the preset toward `back` shows its display) fails on
    none of the excused values;
  - the either-side form fails on none either;
  - A1 and A2 fail on none.

  So sample 1's 54,967 is read against its 57,459 excused, and sample 3's narrowed-form figure
  against its own 38,337 and 38,269.
- **At the four pinned floor values:** the plugin's own rule changes only issue #13's,
  5.857149595214349e-20, from 4.3339653062172035e-16 to 4.3339647768216114e-16.
- **The negative harness** copies `scripts`, `src`, `tests` and `agent-os/standards`
  (`scripts/gate-negative-tests.sh`, `mk`).

## Shaping answers

In the owner's words:

- **The neighbour rule:** the plugin's own, with: "1. Evidence is the full sweep, not the sample:
  - Every float32 normalized value of every group, with A1, A2, HELD and the set path failing on
    no value, and CHANGEDx / NCHANGEDx at 0 against main's results outside the unheld values.
  - The count of values that reach each of the rule's three branches (what a set of the curve's
    float32 holds; the float32 on its other side; the curve's float32 itself). A branch no value
    reaches is either removed or held by a unit test on a constructed scale, and shape.md says
    which; the third branch returns an unheld preset, so if any value reaches it, stop and
    present.
  - The Vital probe rerun at the pinned values, issue #13's own among them since its result
    changes.
  - A mutation for each branch's order, so no pick rests on evaluation order unnoticed.
  The docstring states the rule in those terms. Confirm in shape.md that it decides neither of
  issue #8's questions: it fixes what the model stores for a display, not whether
  VitalInstrument.set keeps a stored value, nor the neighbour for an arbitrary display."
- **The excuse:** toward `back`, with: "1. Shown by count on the full sweep, not the sample: the
  narrowed predicate's excused set equals A3's failures on every group (A3x 0), and a mutation
  shows a value whose float32 neighbour on the far side shares its display, but not the one on
  back's side, is not excused. Two sample figures were given for the excused values (57,459 and
  38,337): say in shape.md what each counts, so the declined form's 54,967 and the narrowed form's
  38,337 are read against the right totals. The docstring says plainly that the predicate is
  consulted only where the exact check fails, with the count of values where it holds and is
  never asked."
- **The constants:** an AST equality test, with: "1. The test fails by name if either tuple is
  missing, renamed or not a plain literal in the integration module, not only if the values
  differ; a mutation shows each. shape.md records that a single definition would need a shared
  tests/support module on pytest's pythonpath, a gate-file change, and leaves that as a note for
  the next gate spec, not a proposal here."
- **The #8 test:** kept as #8's characterization, with: "1. The docstring names issue #8 and its
  finding 1, and says a decision there reverses this test on purpose. The test asserts only what
  that decision would change (the unheld float32 kept at this value), nothing #8 would leave
  alone. The mutation transcript shows the display check caught by the floor value with this test
  deselected."
- **Steps 2 to 5:** "Confirmed as listed". No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`, `base/process/ownership`,
  `vital/parameter-map`, `vital/measures`, `vital/preset-tests`, `vital/plugin-state` and
  `vital/float-writer`. Snapshot in `standards.md`, base at `e31f7db`.

## Decisions

1. **`MappedParameter.to_preset` takes the plugin's own value.**
   - On a linear scale, the curve's float32 P1 (clamped) is kept where the scale holds it.
   - Otherwise the value is, in order:
     - what a set of P1 holds, `S(N'(P1))`, where it shows the display;
     - else the float32 on P1's other side, away from that value, where the scale holds it and
       it shows the display;
     - else P1, unheld, as on `main`.
   - **The rule needs no tie-break.** It is Vital's own rounding of the value the map gave before
     the fix, so a set holds what it held on `main` wherever that shows the display. It replaces
     the previous spec's rule (Decision 6 there), the neighbour nearer the curve's unrounded
     inverse, whose exact ties the stable sort decided.
   - **It decides neither of #8's questions.** It fixes what the model stores for a display. It
     does not decide whether `VitalInstrument.set` keeps a stored value given the display it
     already shows (#8's finding 3), nor the neighbour for an arbitrary display, which keeps the
     curve's float32 as on `main` (#8's finding 1).
   - #8 said #15 decides which preset a set of a shared display stores. That is the first two
     branches.
2. **`_shares_its_display(record, preset, back)` asks only the float32 next to the preset toward
   `back`.** It holds where that float32 shows the preset's display. The review's
   `back in (below, above)` is declined: by sample 1, it would fail on 54,967 of 57,459 excused
   values.
3. **The two copies of the pinned tuples are held equal by an AST test**, which finds both in the
   integration module's source as plain literals and fails by name otherwise.
   - A single definition would need a shared `tests/support` module on pytest's `pythonpath`.
     That is a `[tool.pytest.ini_options]` change, so a gate file. It is left as a note for the
     next gate spec, not proposed here.
4. **`test_an_arbitrary_display_keeps_the_curve_s_float32` is issue #8's characterization**, as
   patchbay-standards#39's rule asks. It asserts only that the unheld float32 is kept at its
   value, and a decision of #8's finding 1 reverses it on purpose.
5. **`next_float32` rounds `toward` to float32 first**, as C's `nextafterf` receives it.
   - It is the one way the package steps a float32.
   - The tests check it against numpy's `nextafter`, an independent oracle, and keep `_next_up`.
6. **The `[0, 1]` guard on `to_normalized`'s step is kept and tested** on
   `NormalizedScale(linear, -1.0, 16777216.0)`.
7. **The sweep's reproduction shares no guard with the shipped code.**
   - N′ is the landing float32 nearest the exact quotient among q and its two neighbours in
     [0, 1], q on a tie and where none lands.
   - P1′ evaluates the rule's branches on every value.
   - CHANGEDx and NCHANGEDx compare them with `main`'s results (the curve's float32; the nearest
     quotient) outside `main`'s unheld values. The branch flags are checked against the scalar
     methods first.
8. **The repeated work goes.**
   - `NormalizedScale._landing` returns the normalized value and where it lands, once, for
     `to_normalized` and `holds`.
   - `MappedParameter.to_normalized` reuses `to_preset`'s.
   - `_inverse` goes, the rule needing no unrounded inverse.
9. **The gate record prints the tree it ran on**, before and after the run, and the two are
   compared with `cmp`. No prose stands in for a printed check.
10. **The CHANGELOG is written against `main`.**
11. **The earlier spec folders stay as recorded**, with their errata listed below.
12. **The negative harness is not rerun.** `base/process/verification-gate.md` asks for a rerun
    "whenever the gate's files change, and whenever a spec adds, removes or renames a file under a
    directory the tests copy". This revision changes no gate file and adds, removes or renames no
    file under `scripts`, `src`, `tests` or `agent-os/standards`.

### Decided while implementing

13. **Each scale and curve group is counted once, by its first record, from the next count on.**
    - While the sweep ran, the owner asked how it came to take an hour. The answer:
      - each round widened its scope;
      - this one also reproduces every branch;
      - 14 of its 74 full counts repeat a group already counted: the three records with a curve
        offset and the 11 envelope delay and hold records that are not their group's first.
    - In the owner's words: "Yeah - let's do 1 for sure."
    - This run was left to finish rather than restarted, since its output is the evidence:
      `verification/sweep-afterwards.txt` compares each of the 14 with its group's first record,
      every binade and the total, 14 of 14 identical.
    - The counting rule in `vital/parameter-map.md` now says each group is counted once (the
      retrospective, below).

### Where the implementation departs from the plan

- **`_landing` is a module function, `_landing(scale, preset)`, not a method.** So
  `MappedParameter` reads it without reaching into another class's private member, as the
  previous spec's `_inverse` did. `to_preset` and `to_normalized` share a private
  `MappedParameter._resolve`, which returns the preset and, where it has been computed on the way,
  its normalized value.
- **The sweep's P1′ computes the rule's first condition from N′ on every value.** It never copies
  P1 where P1 is held, and it computes the later branches where the earlier fail, in the rule's
  order. The plan said every branch on every value, which would double the cost without changing
  a count. Its docstring says exactly what it computes.
- **The branch tests are two:**
  - `test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`, at issue #13's value;
  - `test_else_a_display_takes_the_float32_on_the_other_side`, at the other three floor values,
    which all take the second branch.
- **The `toward` cases of `next_float32` are four `@example`s on its property**, with no separate
  test: 1.0 + 1e-12, 1.0 - 1e-12, 1e300 and 1e-50. With the old `next_float32`, three of them fail
  the property.
- **M8b is added.** It moves the held branch after the second, beside M8's move after the first,
  so each branch's order has a mutant.
- **Two docstrings of `tests/unit/test_parameters.py` changed after the sweep read it (blob
  `05e3fd9`):**
  - `_shares_its_display`'s, whose counts are the sweep's own;
  - `_assert_comes_back`'s, which now cites this revision.

  `verification/sweep-afterwards.txt` puts both back in a scratch copy, finds the copy's blob is
  `05e3fd9`, and finds the two modules' syntax trees identical with every docstring removed. The
  mutation and the probe ran after the last edit.
- **The shaping script for sample 3 carried one random stream across two rules**, as corrected
  above.

## The review's findings

| # | Finding | Outcome |
|---|---|---|
| C1a | `next_float32` "the one way the package and its tests step a float32" | Docstring and CHANGELOG corrected (Decision 5) |
| C1b | `toward` compared as a double, not as `nextafterf` | Rounded first; a pinned test and a property over double `toward` |
| C2 | The tie rule is untested and an exact tie silent; the #8 test pins #8's question | The plugin's own rule, with no tie (Decision 1); the #8 test a named characterization (Decision 4) |
| C3 | The `[0, 1]` guard is reachable | Kept and tested; M4 killed (Decision 6) |
| C4 | Zero counts by construction; BOTH and NONE unchecked; 200,007 | Guard-free reproduction against `main`'s results; flags checked; 200,010 (Decision 7) |
| C5 | The excuse is wider than the code it excuses | The neighbour toward `back` (Decision 2); `back in (below, above)` declined with its count |
| C6 | The gate record's identity is prose | Printed before and after, compared (Decision 9) |
| C7 | The CHANGELOG's "Removed" bullet names what never was on `main` | Rewritten against `main` (Decision 10) |
| O1 | The pinned tuples copied with nothing checking them | The AST test (Decision 3) |
| O2 | Repeated work on every set | `_landing`; the landing reused; `_inverse` removed (Decision 8) |
| O3 | Prefer what a set of P1 holds | Adopted (Decision 1) |

## Errata in the earlier spec folders, which stay as recorded

In `agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`:
- **Decision 7 and the CHANGELOG** call `next_float32` "the one way" the package *and its tests*
  step a float32. `tests/unit/test_float32.py` steps with numpy on purpose.
- **CHANGEDx and NCHANGEDx** are given as evidence that the fix changed nothing it must not.
  They were 0 by the sweep's construction.
- **The sweep's BOTH and NONE** were counts of the reproduction alone, never checked against the
  shipped methods.
- **`sweep.py` and `sweep_exponential.py`** say 200,007 values. Both checked 200,010.
- **`mutation.txt` and the shape.md** call the step's `[0, 1]` guard one no test trips, searched on
  200,000 constructed scales. It is reachable on a span of 2 ** 24.
- **`gate-run.txt`** shows the scratch copy's identity only by `git status --short`. Its third run
  describes the clean tree in prose rather than printing it.

## Open

- **#8's findings 1 and 3** (Decision 1).
- **A single definition of the pinned tuples**, for the next gate spec (Decision 3).

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing on
  either side". The value the model stores for a display is now the one Vital's own set holds.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the property's one excuse, the characterization test and the AST test.
- `base/process/verification-gate` — the gate unchanged; its record; when the harness reruns.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issues edited without
  attribution.
- `vital/parameter-map` — the two inverses, the round trip and the counting rule.
- `vital/measures` — what Vital holds after a set, compared exactly.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load test, unchanged.
- `vital/float-writer` — the load test's writer, unchanged.

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

**Results (2026-11-12):** `verification/gate-run.txt`, one run, 15:31 EST, on branch
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`
at `f3625d1`, with the change uncommitted, on the final tree after the retrospective's edits. No
gate file changed.

- **Steps 1 to 6 pass, exit 0:** 514 tests, none skipped, the integration tests among them with
  Vital installed.
- **The tree is printed before the run and after it:**
  - HEAD;
  - `git status --porcelain=v1 --untracked-files=all` in full;
  - the blob of every path that differs from HEAD or is untracked.

  `cmp` finds the two the same, line for line.
- **The same blobs in every record:** `parameters.py`, `float32.py` and the three test modules
  have the blobs that `verification/mutation.txt` and `verification/plugin-probe.txt` print, each
  for the files it reads. The sweep's `parameters.py`, `float32.py` and `data/parameters.json` are
  these too; its test module differs only in two docstrings (`verification/sweep-afterwards.txt`).
- **Written after the run:** only this file's results and `verification/gate-run.txt` itself,
  copied in from outside the tree. No gate step reads either.

- **Not run by the gate:**
  - **The sweep**, `verification/sweep.txt`, two sections, every float32 normalized value. Each
    section prints its tree before and after the run, and `cmp` finds them the same.
    - **The first section:** 83 counts in 4,236 s on 10 processes.
      - **What it counts:** the 60 groups reproduced in numpy, the six records with a curve
        offset, the 12 envelope records, and HELD, NCHANGED and NCHANGEDx on the 9 exponential
        groups.
      - **The checks:** each count is checked against the shipped scalar methods on 200,010
        values first, with 0 mismatches and no fallback, the branch and both predicates among
        what it compares.
      - **`bound!` 0 on every count.** A1, HELD, A2 and SET are 0.
      - **The excuse:** A3 is 570,997,534, all of `volume`, A3x 0. UNASKED is 18,227,438, of
        SHARE 589,224,972.
      - **The branches:** PLUGIN 15,761,472, OTHER 308,386 and UNHELD 0, all of `volume`; every
        other linear value is KEPT.
      - **Against `main`:** CHANGED 16,069,858, CHANGEDx 0; NCHANGED 126 on each of the 12
        envelope records, at the powers of two from 2 ** -125 to 1, NCHANGEDx 0.
      - **Where `volume` changed:** CHANGED falls in its normalized binades -95 to -56, at or
        below 2 ** -43, and OTHER in -58 to -56.
    - **The second section:** the 9 exponential groups through this machine's own `pow` and
      `log2`, 9 counts in 989 s on 9 processes.
      - **The machine:** macOS 26.6.2 (25G83) arm64. The interpreter links libSystem 1351, and
        `pow` and `log2` resolve to one address each.
      - **The checks:** each count is checked on 200,010 values, with 0 mismatches.
      - **The counts:** `bound!` 0; KEPT on every linear value; UNASKED 1,042,983,597, of which
        `oversampling`'s whole numbers are 1,042,983,595, its indexed values taking no branch.
    - **The 14 records counted beside their groups** match them line for line
      (`verification/sweep-afterwards.txt`, with the docstring-only check of the test module).
  - **The probe**, `verification/plugin-probe.txt`: Vital 1.6.4 through pedalboard 0.9.26 on arm64.
    - **The floor values:** at each, a set holds the map's value, held, showing the display. At
      issue #13's value that is 4.3339647768216114e-16, what a set of the curve's float32 holds.
      At the other three it is the float32 on the other side.
    - **The powers:** Vital holds the power at each.
    - **The load:** a load of the curve's own float32 is held as what a set of it holds, after
      each of the four histories.
  - **The mutation**, `verification/mutation.txt`:
    - each mutant fails the tests its heading names;
    - M5 does so again with issue #8's characterization deselected;
    - M8 and M8b pass, equivalent as their headings say, M8b's equivalence resting on A1 being 0
      on every value;
    - M11 to M14 each fail the AST test by name, with its message.
  - **The negative harness** is not rerun (Decision 12). The revision changes no gate file and
    adds, removes or renames no file under `scripts`, `src`, `tests` or `agent-os/standards`.

**Issues** (each body read before the edit, compared with the body last read, read back after
it; no attribution; lines added, none removed):

- **#15** gains a "Revised 2026-11-12 (after PR 14's fourth review)" paragraph, before its section
  1:
  - the plugin's own rule replaces the nearer neighbour;
  - its counts;
  - the correction of "and no other result";
  - the narrowed excuse;
  - Vital's set and load;
  - #8's two questions unchanged.
- **#8** gains one before "Depends on": the rule changed, the 15,452,993 the old rule's, and
  findings 1 and 3 undecided.

**Docs (step 7):** every file changed, and every document and standard naming them, checked
against the shipped code:

- **`src/patchbay_vital/parameters.py`:**
  - the module docstring states the rule and cites this revision's sweep and probe;
  - `to_preset`'s states its three branches in order and that it decides neither of #8's
    questions;
  - `_landing`'s states the guard and the scale that reaches it.
- **`src/patchbay_vital/float32.py`:** the module docstring says `next_float32` is the one way the
  package steps a float32, checked against numpy's. `next_float32`'s says both arguments are
  narrowed first.
- **`tests/unit/test_parameters.py`:**
  - `_assert_comes_back`'s and `_shares_its_display`'s docstrings state the excuse, the side it
    asks, and its counts;
  - each new test's docstring says what it holds;
  - the #8 test's says it is issue #8's characterization.
- **`tests/unit/test_float32.py`:** the property's docstring says the direction is narrowed.
- **`tests/integration/test_vital_plugin.py`:** the three docstrings cite this revision's probe.
  The module docstring is unchanged and true.
- **Unchanged and true:** `README.md`, `CLAUDE.md` and `agent-os/product/` name nothing that
  changed.
- **`git grep` outside the spec folders** finds no `_inverse`, "one way the package and its tests",
  200,007, "no test trips", 15,452,993 or 5.7%. "Nearer the curve" is found only in
  `vital/parameter-map.md`'s note that the rule replaced it.

**Version (step 8):** `CHANGELOG.md`'s `[Unreleased]` `### Fixed`:
- **issue #15's entry is rewritten against `main`:**
  - both inverses, the guard and the plugin's own rule, with its counts;
  - `holds` and `next_float32`;
  - the evidence files;
  - no name that was added and removed inside the PR, and no count that is 0 by construction;
- **issue #13's entry:** the excuse asks the side toward the preset the display maps to, with its
  count.

The behaviour changes, unreleased; the version stays 0.0.1 until a release is cut.

## Standards Retrospective

Step 9, from the shipped diff. The four questions:

1. **A pattern no standard covers:** four.
   - Each group is counted once, by its first record (Decision 13).
   - A fix is counted against the old code's results by a reproduction sharing none of the new
     code's guards.
   - A rule's branches are each counted, a branch no counted value reaches removed or held by a
     unit test.
   - A kept transcript prints its tree before and after the run and compares them with `cmp`.
     That one is a base proposal, below.
2. **A standard wrong or stale:** two.
   - `vital/parameter-map.md`:
     - the nearer-inverse rule;
     - the either-side excuse;
     - "a fix by what it changed and must not have", counted by a reproduction that shared the
       code's guard;
     - the step's guard called unreachable nowhere, but untested;
     - 5.7%, measured another way and now 5.4% under the shipped rule.
   - `vital/measures.md`: the two copies of the pinned values held equal by convention alone.
3. **A deliberate deviation:** one. This run counted the 14 records beside their groups once more
   (Decision 13). The declined proposal is held as a project rule.
4. **A pointer moved:**
   - `_inverse` removed, `_landing` and `_resolve` added;
   - four new test functions, seven tests (the two branch tests, the guard test and the AST
     test), and the #8 test made a characterization;
   - the evidence in this revision's `verification/`.

   Every standard naming them is updated.

The project edits, approved by the owner on 2026-11-12 with AskUserQuestion, are listed apart from
the feature's files. Each standard is its own change set with its entry of `index.yml`'s `vital:`
section. The `base:` section is untouched (`scripts/sync-standards.sh --check` passing), and
`vital/plugin-state.md` needs no change: its load observation reads true.

- **`agent-os/standards/vital/parameter-map.md`, with the `parameter-map` entry.** In the owner's
  words: "write the five points as plain sentences a reader new to the spec can follow, each with
  its count and the file that holds it. The third branch counted UNHELD 0: the standard says
  whether it was removed or is held by a unit test on a constructed scale, matching what shipped."
  - **The rule:** in plain sentences, its three branches in order, with PLUGIN 15,761,472, OTHER
    308,386 and UNHELD 0 from `verification/sweep.txt`, and Vital's load from
    `verification/plugin-probe.txt`.
  - **The third branch:** kept and held by `test_an_arbitrary_display_keeps_the_curve_s_float32`,
    on `beats_per_minute`'s scale and curve as the test module builds them (`_TEMPO`). It is #8's
    characterization, and 5.4% of 20,000 uniform displays of `volume` (seed 8) reach it.
  - **The excuse:** asked toward `back`, on 570,997,534 values, and never asked on 1,061,211,035
    where a neighbour shares the display, with the far-side case at 2 ** -43.
  - **The guard:** reachable on a span of 2 ** 24, and `next_float32` narrowing both arguments.
  - **The counting rule:**
    - each group once, the 14 duplicates matching (`verification/sweep-afterwards.txt`);
    - the check covering every value and flag;
    - branches counted;
    - a fix counted against the old results by a reproduction sharing no guard, and a count 0 by a
      copied guard not evidence.
  - **Verified against:** `parameters.py`, `float32.py`, both test modules,
    `verification/sweep.txt`, `verification/sweep-afterwards.txt`, `verification/mutation.txt` and
    `verification/plugin-probe.txt`.
- **`agent-os/standards/vital/measures.md`, with the `measures` entry.**
  - At issue #13's value Vital holds what a set of the curve's float32 holds, and at the other
    three the other side.
  - The pinned copies are held equal by `test_the_integration_module_pins_the_same_values`, which
    fails by name (M11 to M14).
  - The header gains this revision.
  - Verified against the AST test, `verification/mutation.txt` and `verification/plugin-probe.txt`.

**A note for the next gate spec, not a proposal (Decision 3):** a single definition of the pinned
tuples would need a shared `tests/support` module on pytest's `pythonpath`, which is a gate file.

Proposals sent upstream: #40 and #38, revised in place.

### Standards retrospective (proposed, base)

Each presented to the owner on 2026-11-12 with AskUserQuestion. The owner's answer: "Proposal 2 is
revised into fromtheoutfit/patchbay-standards#38's proposal 2 in place, with a "Revised
2026-11-12" paragraph, since it refines a proposal already filed and still open; no new issue is
filed. Proposal 3 is marked "declined by owner, 2026-11-12: held as a project standard in
vital/parameter-map.md until a second package needs it"."

- **`base/testing/tests.md`, #40's proposal 2: a known exception's predicate is as narrow as the
  code it excuses.**
  - Where the excused value has a side, the predicate asks only that side, and its docstring says
    it is asked only where the claim fails and counts where it holds unasked.
  - Evidence: the review of `f3625d1`, check 5; `_shares_its_display`; `verification/sweep.txt`
    (A3x 0); `verification/mutation.txt` M10. The review's narrower form is declined there with
    sample 1's count.
  - Proposed, not applied; filed as fromtheoutfit/patchbay-standards#40, revised in place.
- **`base/process/verification-gate.md`, #38's proposal 2: a kept transcript prints its tree before
  and after the run and compares the two with `cmp`.**
  - The tree is printed as HEAD, `git status --porcelain=v1` in full, and the blob of each file
    read that differs from HEAD, or for a gate run every such path and every untracked one. No
    prose stands in for a printed check.
  - Evidence: the review of `f3625d1`, check 6; this revision's `verification/gate-run.txt`,
    `sweep.txt`, `plugin-probe.txt` and `mutation.txt`.
  - Proposed, not applied; filed as fromtheoutfit/patchbay-standards#38, revised in place.
- **`base/testing/tests.md`: no count 0 by construction.** A count of what a fix changed compares,
  against the old code's results, a reproduction sharing none of the new code's guards.
  - Evidence: the review of `f3625d1`, check 4; the previous spec's `Vec.fixed` and `Vec.Nf`; this
    revision's CHANGEDx and NCHANGEDx.
  - Declined by owner, 2026-11-12: held as a project standard in vital/parameter-map.md until a
    second package needs it.
