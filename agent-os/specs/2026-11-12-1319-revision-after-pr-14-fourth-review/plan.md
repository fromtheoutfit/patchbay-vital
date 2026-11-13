# Revision after PR 14's fourth review: the plugin's own neighbour, a narrower excuse, checks that can fail

## Context

The review is "Review of f3625d1",
https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6831965378, posted
2026-11-12 18:12Z. It makes seven checks and three other findings. Two checks fail outright: the
tie rule is untested, and the `[0, 1]` guard is reachable. Two more are partly met.

Each finding was verified read-only against `f3625d1` while shaping:
- **next_float32's `toward`.** `next_float32(1.0, 1.0 + 1e-12)` gives 1.0000001192092896, where
  numpy's float32 `nextafter` gives 1.0. `tests/unit/test_float32.py:26` steps a float32 with
  numpy, so "the one way the package and its tests step a float32" is false.
- **The guard is reachable** on `NormalizedScale(linear, -1.0, 16777216.0)`. With the guard,
  `to_normalized(2**24)` is 1.0; without it, 1.0000001192092896.
- **The tie rule.** On sample 1 (60,000 floor values of `volume`, seed 15), both neighbours
  qualify on 1,631 values, and 757 of them are exact ties, decided only by the stable sort.
- **The sweep's zero counts.** CHANGEDx and NCHANGEDx are 0 by the sweep's construction:
  `Vec.fixed` rewrites only where `~held`, and `Vec.Nf` steps only where `S(q) != p`. The BOTH
  and NONE flags are never compared with the scalar methods. The script's docstring says 200,007,
  where `sample()` builds 200,010 values.
- **The reviewer's narrower excuse, `back in (below, above)`, would fail the property.** In
  sample 1, 57,459 values are excused under the shipped rule, and on 54,967 of them `back` is not
  a float32 neighbour of the preset.
- **The CHANGELOG's "Removed" bullet** names things that never existed on `main`.
- **The two constant copies** have no test that holds them equal.

No gate file changes. No stage, commit, push or pull-request edit by an agent.

## Decisions (owner, 2026-11-12, AskUserQuestion)

1. **`to_preset` takes the plugin's own value.**
   - **The rule.** Where the curve's float32 P1 is unheld, take what a set of P1 holds,
     `S(N'(P1))`, when it shows the display. Otherwise take the float32 on P1's other side, away
     from that value, when the scale holds it and it shows the display. Otherwise keep P1. The
     docstring states the rule in those terms.
   - **Why.** It needs no tie rule. On sample 2 (seed 16), `S(N'(P1))` is a neighbour of P1 on
     all 1,646 unheld values and shows the display on 1,622. On the other 24, exactly one
     neighbour qualifies. A1 and A2 fail nowhere. The pick differs from today's on 910 values,
     issue #13's own among them: 4.3339647768216114e-16 where today's is 4.3339653062172035e-16.
   - **The evidence is the full sweep, not the samples:**
     - A1, A2, HELD and the set path are 0 on every value of every group.
     - CHANGEDx and NCHANGEDx are 0 against `main`'s results, outside `main`'s unheld values.
     - Each of the rule's three branches has a count. A branch no value reaches is removed, or
       held by a unit test on a constructed record, and shape.md says which. **If any value
       reaches the third branch, stop and present.**
     - The Vital probe is rerun at the pinned values, issue #13's among them.
     - A mutation covers each branch's order.
   - **What it decides.** shape.md confirms it decides neither of #8's questions. It fixes what
     the model stores for a display. It does not decide whether `VitalInstrument.set` keeps a
     stored value (finding 3), nor the neighbour for an arbitrary display (finding 1).
2. **The excuse asks only the float32 on `back`'s side.**
   `_shares_its_display(record, preset, back)` holds where `next_float32(preset, back)` shows the
   preset's display. The reviewer's form is declined, with the sample figure above.
   - **Shown by count on the full sweep:** the excused set equals A3's failures on every group
     (A3x 0).
   - **Shown by mutation:** at `volume`'s 2 ** -43, the float32 below shares the display and the
     one above, toward `back`, does not. That value is not excused, and an either-side mutation
     fails the test.
   - **The docstring says plainly** that the predicate is consulted only where the exact check
     fails. It counts the values where a neighbour shares the display but the predicate is never
     asked, and says the predicate concerns float32 neighbours, not presets.
   - **shape.md names what each shaping figure counts:**
     - sample 1 (seed 15, 60,000 floor values): 57,459 excused under the shipped rule, 54,967 of
       them with `back` not a neighbour of the preset;
     - sample 3 (seed 17, 40,000 floor values): 38,337 excused under the shipped rule and 38,269
       under the plugin's own, the narrowed predicate failing on none.
3. **An AST equality test holds the two copies equal.** A unit test reads
   `tests/integration/test_vital_plugin.py`'s source and finds `_VOLUME_FLOOR` and
   `_POWERS_OF_TWO` as plain literals with `ast.literal_eval`. It asserts they equal the unit
   module's.
   - It fails by name if either tuple is missing, renamed or not a plain literal, and if the
     values differ. A mutation shows each case.
   - shape.md records that a single definition would need a shared `tests/support` module on
     pytest's `pythonpath`. That is a gate-file change, left as a note for the next gate spec, not
     a proposal.
4. **`test_an_arbitrary_display_keeps_the_curve_s_float32` is a characterization of #8.**
   - Its docstring names issue #8 and its finding 1, and says a decision there reverses the test
     on purpose.
   - It asserts only what that decision would change: `back` is the curve's float32 and is not
     held.
   - The mutation transcript shows the display check caught by the floor value with this test
     deselected.

### Decided in shaping, within those answers

- **`next_float32` rounds `toward` to float32 first**, as `nextafterf` receives it. The docstring
  says it is the one way the package steps a float32, and that its tests check it against numpy.
- **A unit test holds the `[0, 1]` guard** on the scale above, so M4 is now killed.
- **The sweep's reproduction shares no guard with the shipped code.**
  - N′ is the landing float32 nearest the exact quotient among q and its two neighbours in
    [0, 1], q kept on a tie and where none lands.
  - P1′ evaluates the rule's branches on every value, with no "held" shortcut.
  - CHANGEDx and NCHANGEDx compare these with `main`'s results (the curve's float32; the nearest
    quotient), outside `main`'s unheld values (`S(N(P1)) != P1`; `S(N(P0)) != P0`). So neither
    count can be 0 by the sweep's construction.
  - The branch flags, and the predicate, are checked against the scalar methods on the 200,010
    values first.
- **Repeated work goes.**
  - A private `NormalizedScale._landing(preset) -> (normalized, landed)` is shared by
    `to_normalized` and `holds`.
  - `MappedParameter.to_normalized` reuses `to_preset`'s landing where it is the value it needs.
  - `_inverse` goes, since the plugin's rule needs no unrounded inverse. `DisplayCurve.to_preset`
    is `main`'s again.
- **The gate record prints what it ran on** before and after the run: `git rev-parse HEAD`,
  `git status --porcelain=v1` verbatim with its line count, and `git hash-object` of every path
  that differs from HEAD or is untracked. No prose stands in for a printed check.
- **The CHANGELOG is written against `main`.** It names nothing that was added and removed
  inside this PR.
- **The earlier spec folders stay as recorded.** This spec's shape.md lists their errata:
  - Decision 7's "the one way";
  - CHANGEDx and NCHANGEDx given as evidence;
  - M4 called unreachable;
  - 200,007;
  - the gate record's prose.
- **The negative harness is not rerun.** `base/process/verification-gate.md` asks for a rerun
  when a gate file changes, or a file is added, removed or renamed under a directory the cases
  copy (`scripts`, `src`, `tests`, `agent-os/standards`). This revision only modifies files
  there. If the implementation adds or removes one, the harness is rerun.

## The findings

| # | Finding | Outcome |
|---|---|---|
| C1a | "the one way the package and its tests step" | Docstring and CHANGELOG corrected |
| C1b | `toward` not rounded as `nextafterf` | Rounded first; a pinned test and a property over double `toward` |
| C2 | Tie rule untested; exact tie silent; #8's question pinned | The plugin's own rule, with no tie (D1); the #8 test made a named characterization (D4) |
| C3 | The `[0, 1]` guard is reachable | Unit test on linear [-1, 2**24]; M4 killed |
| C4 | Zero counts by construction; flags unchecked; 200,007 | Guard-free reproduction against `main`'s results; flags checked; 200,010 |
| C5 | The excuse is wider than the code | The neighbour toward `back` (D2); `back in (below, above)` declined with the count |
| C6 | The gate record's identity is prose | Printed HEAD, status and blobs, before and after |
| C7 | CHANGELOG "Removed" bullet | Rewritten against `main` |
| O1 | Constants duplicated without a check | AST equality test (D3) |
| O2 | Repeated work on every set | `_landing`, reused landings, `_inverse` removed |
| O3 | Neighbour search's design | Adopted as D1 |

## Shaping steps 2 to 5 (owner: "Confirmed as listed")

- **Visuals:** none.
- **References:**
  - the previous spec's `sweep.py`, `sweep_exponential.py`, `plugin_probe.py` and `mutate.sh`,
    each embedded in its verification transcripts;
  - both test modules.
- **Product:** `mission.md` is unchanged ("so a value means the same thing on either side").
- **Standards:**
  - the core five;
  - from base: `base/testing/tests`, and `base/process/verification-gate`,
    `standards-retrospective`, `standards-index` and `ownership`;
  - from this repository: `vital/parameter-map`, `measures`, `preset-tests`, `plugin-state` and
    `float-writer`;
  - base pinned at `e31f7db`.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/` with:
- `plan.md`: this plan;
- `shape.md`: scope, the owner's answers in their words, the checks and samples above (each
  sample's seed, size and count named), the Decisions, the findings table and the errata;
- `standards.md`: a snapshot of the confirmed standards;
- `references.md`.

## Task 2: `src/patchbay_vital/float32.py`

- `next_float32` rounds `toward` with `to_float32` before comparing.
- The docstring says it behaves as `nextafterf` on the float32s it is given. The module docstring
  says it is "the one way the package steps a float32".

## Task 3: `src/patchbay_vital/parameters.py`

- **`NormalizedScale._landing(preset)`** returns `(normalized, landed)`: `to_normalized`'s result
  and `to_preset` of it.
  - `to_normalized` returns `[0]`.
  - `holds` reads both, so nothing is computed twice.
- **`MappedParameter.to_preset`**, on a linear scale, takes the clamped float32 P1 and
  `(n, landed) = scale._landing(P1)`:
  - `landed == P1`: return P1, which is held;
  - `curve.to_display(landed) == display`: return `landed`, what a set of P1 holds;
  - `other = next_float32(P1, copysign(inf, P1 - landed))`, held and showing the display: return
    `other`;
  - otherwise return P1, as `main` did (issue #8's finding 1).
- **The docstrings** state the rule in those terms and say it decides neither of #8's questions.
  The module docstring is updated to match.
- **`MappedParameter.to_normalized`** reuses the landing where it is the value it needs.
- **`_inverse` is removed**, and `DisplayCurve.to_preset` is restored to `main`'s text.

## Task 4: `tests/unit/test_float32.py`

- `next_float32(1.0, 1.0 + 1e-12) == 1.0`.
- The step property draws `toward` as any double and compares with numpy's float32 `nextafter`,
  under `errstate(over="ignore")` as `_numpy` does.

## Task 5: `tests/unit/test_parameters.py`

- **`_shares_its_display(record, preset, back)`** asks the float32 toward `back`, and its
  docstring follows D2. `_assert_comes_back` passes `back`.
- **The boundary test** pins the 2 ** -43 case from D2: not excused, while its far side shares
  the display.
- **The branch tests**, one per reachable branch, at pinned values: issue #13's value in branch
  1, as an exact literal, where swapping branches 1 and 2 changes the pick; a floor value in
  branch 2, expected to be 1.439742266862027e-17 and confirmed by the sweep's flags.
- **The #8 characterization**, as in D4.
- **The guard test** on linear [-1, 2**24].
- **The AST equality test**, as in D3.
- **`test_where_volume_s_offset_absorbs_a_preset`** moves to the new predicate's signature.

## Task 6: `tests/integration/test_vital_plugin.py`

- The pinned tuples are unchanged.
- The floor and power-of-two tests still assert that Vital holds `to_preset(display)` and the
  power.
- The docstrings cite this spec's probe.

## Task 7: The sweep, rerun (`verification/sweep.txt`)

**Both sections**, from the previous spec's `sweep.py` and `sweep_exponential.py`:
- the reproduction is guard-free, as above;
- the columns: A1, HELD, A2, SET, A3 and A3x (the new predicate), and SHARE (either side,
  for the never-asked count);
- the branches: KEPT, PLUGIN, OTHER and UNHELD;
- CHANGED, CHANGEDx, NCHANGED and NCHANGEDx against `main`;
- the check compares every column and flag with the scalar methods on 200,010 values;
- the docstrings say 200,010.

The last run took 2,567 s and 605 s. Expect about 1 to 1.5 hours unattended, since every branch
is computed on every value.

**Stop and present** if `bound!` is not 0 anywhere, if UNHELD is not 0, or if A3x is not 0.

## Task 8: The Vital probe, rerun (`verification/plugin-probe.txt`)

- At each pinned floor value it prints the branch taken. Vital holds `to_preset`'s value, held,
  showing the display; issue #13's value is the new one.
- The powers and the load are as before.
- The probe is written last, after every test edit.

## Task 9: Mutation (`verification/mutation.txt`)

On scratch copies, each mutant run against the unit tests:

| Mutant | Must fail |
|---|---|
| M0 the tree, unmutated | nothing: it passes |
| M1 `to_normalized` reverted | the powers of two |
| M2 the snap removed | the floor tests |
| M3 `holds` without its `[0, 1]` check | `test_a_scale_holds_its_values_and_none_past_its_ends` |
| M4 the step without its `[0, 1]` check | the new guard test |
| M5 branch 1 without its display check | the branch-2 floor value, shown again with the #8 test deselected |
| M6 branch 2 without its display check | the #8 test |
| M7 branches 1 and 2 swapped | issue #13's value |
| M8 the held branch after branch 1 | expected equivalent: `landed == P1` there, so the pick is the same. The transcript shows it, and shape.md says why |
| M9 branch 3 before branch 2 | the branch-2 value |
| M10 `_shares_its_display` either side | the boundary test |
| M11 to M14, the integration tuple missing, renamed, non-literal or changed | the AST test, by name, each |

## Task 10: CHANGELOG, issues, pull request

- **`CHANGELOG.md`:** the #15 entry is rewritten against `main`, with D1's rule, `holds` and
  `next_float32`, the evidence files, no PR-internal names, and no counts that are 0 by
  construction. The #13 entry follows D2.
- **Issues #15 and #8:** each body is read first. A "Revised 2026-11-12 (after PR 14's fourth
  review)" paragraph goes wherever a statement becomes false, such as #15's "nearer the inverse"
  and "no other result". Each is read back; no attribution.
- **PR 14:** the sentences now untrue are listed in the final report.

## Task 11 (FINAL): Verification gate

1. **`scripts/gate.sh`** exits 0 on the final tree, with Vital installed and nothing skipped,
   into `verification/gate-run.txt`. The printed identity blocks come before and after the run,
   compared with `cmp`.
2. **The negative harness** is not rerun, as above, and shape.md cites the rule.
3. **Docs:**
   - `README.md` and `CLAUDE.md`;
   - both source modules' docstrings and the three test modules';
   - every standard naming a changed name, `git grep` for `_inverse`, `nearer the curve`,
     `CHANGEDx`, `one way the package` and `200,007` outside spec folders.
4. **Version:** `[Unreleased]`; 0.0.1 kept.
5. **Standards retrospective,** from the shipped diff, each edit approved with AskUserQuestion:
   - **project:**
     - `vital/parameter-map.md`: D1's rule, D2's excuse, and the counting rule corrected so a
       count that a reproduction makes 0 by sharing the code's guard is not evidence;
     - `vital/measures.md`, if the probe's wording changes;
     - `index.yml`;
   - **base, presented before filing:**
     - #40's proposal 2, its instance now the narrowed predicate;
     - candidates on `verification-gate.md` (a run record prints its tree's identity) and on
       counting.
   - **Record `Proposals sent upstream:`.**

## Verification

- `scripts/gate.sh` exits 0 (507 tests plus the new ones).
- The sweep: `bound!` 0, UNHELD 0 and A3x 0 on all 69 groups.
- The probe at the pinned values.
- The mutation table: each mutant fails or is equivalent as listed.
- No stage, commit or push. The final report lists the feature files and the retrospective files
  apart, the issue edits, what remains open (#8's findings 1 and 3), and PR 14's untrue
  sentences.
