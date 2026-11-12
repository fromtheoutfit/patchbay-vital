# Revision after the second review of PR 14

## Context

The second review on PR 14 is https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6811755893
(2026-11-12 01:34Z), covering `88d438d`, `0568b32`, `412b21a` and `c159446`. Its main problem is
that four places still claim a set's display is exact above volume's floor. On the 12 envelope
records, 1,512 power-of-two values above the floor don't come back exactly.

The rest:
- Two characterization tests that #15's fix would break for the wrong reason.
- A floor allowance keyed by the record's name, not by values.
- No integration test for the power-of-two rows.
- The sweep hard-codes its rows and leaves an `(issue #N)` placeholder.
- HELD on the 9 exponential groups is countable but called uncountable.
- Missing corrections, wording that overstates, and three small cleanups.

Every claim was checked against HEAD while shaping:
- The hand-built `_VOLUME` equals the committed record today.
- #15's candidate fix gives `to_preset(above)` = 1.0000001.
- The four sentences are where the review says.

The revision is a new spec folder on this branch. There is no behaviour change in
`src/patchbay_vital/` (docstrings only) and no gate file change. No stage, commit, push or PR
edit by an agent.

## Decisions (owner, 2026-11-11, AskUserQuestion)

1. **The floor allowance becomes a value predicate**, `_shares_its_display(record, preset)`: the
   preset and an adjacent float32 show one display. It replaces `_ABSORBED.get(record.id)`.
   - The owner's condition: the sweep shows per group that the predicate's set **equals** the
     failures. If it excuses values where A3 and the set path don't fail, stop and present the
     counts: either the predicate is tightened until the sets match, or shape.md says exactly
     which values are excused without failing and why that is accepted.
   - A mutation shows two things: a record with the same absorption under another name gets the
     allowance, and a record named volume without it does not.
2. **Power-of-two rows get an integration test and two more rows** (0.5, `3eb504f4`; 2 ** -20,
   `35b504f4`).
   - The header marks the rows measured on the plugin, with the machine and Vital's version.
   - The test skips by name on another machine (the `vital` fixture).
   - Decision 8's "likewise at 0.5 and 2 ** -20" goes under Corrections, with what the
     transcript now shows.
3. **One step helper:** a plain `stepped(value, steps, width)` in `tests/conftest.py` returns the
   float32 (width 32) or double (width 64) that many steps away. A fixture `stepped` hands it to
   tests. All three row tests compare `== stepped(...)`. `_ulps` stays for `_SECOND_LOAD_ULPS`.
4. **#15 and patchbay-standards#40 are revised in place**, no attribution, each with a
   "Revised 2026-11-11" paragraph. Dates follow the repository's local (EST) convention, as the
   spec folders and commits do.
   - #15 says what is now counted on the 9 exponential groups: HELD, scale-only arithmetic, 0
     failures on every float32 normalized value. It also says what is still not: the claims that
     pass through `pow`/`log2`, namely the display coming back, A2 and the set path. If the issue
     has a paragraph scheduling the libm count, it is narrowed to those claims; if not, they are
     recorded as open for the owner to schedule.
   - #40's proposal (c) gains the floor's lookup as a second instance of its rule.
5. **Steps 2–5:**
   - No visuals.
   - References: the previous revision's folder (sweep script, probe, mutation), `tests/conftest.py`,
     both test modules and both row files.
   - Mission unchanged.
   - Standards: the core five plus base/testing/tests, process/verification-gate,
     standards-retrospective, standards-index, ownership, vital/parameter-map, vital/measures,
     vital/preset-tests and vital/plugin-state (base at `e31f7db`).

Decided in shaping, within those answers:

- **Each exception is consulted only where its claim fails**, as `_lands_below_its_power_of_two`
  is: `claim or predicate`. So an excuse can never cover a value that doesn't fail, and "sets
  equal" means every failure satisfies its predicate. The sweep checks exactly that, and also
  prints how many values satisfy `_shares_its_display` alone, which is wider.
- **The set path is asserted on every value**, `shown == display` or one of two excuses:
  `_shares_its_display` with `shown` a neighbouring double, or `_lands_below_its_power_of_two`.
  That replaces "follows from A3 and HELD above the floor". It fixes the exactness wording at its
  root: exact but at those two stated exceptions.
- **The second mutation shows the branch taken, not a failure.** With monotone curves, a record
  named volume without absorption cannot have an A1-holding A3 failure, nor a set path one double
  off, that the old rule excused. So that half of the mutation counts which branch each version
  takes on such a record, and the transcript says why.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`, modelled on
`2026-11-11-1555-revision-after-pr-14-review/`:

- **plan.md** (this plan) and **standards.md** (snapshot from HEAD).
- **references.md**.
- **shape.md**:
  - scope, the shaping answers in the owner's words, what was checked, the decisions above;
  - a findings table, 17 rows (R1–R17 below);
  - **"Corrections to issue #13's spec and to the revision after PR 14's review"**: file:line,
    old beside new;
  - the open item; Standards Applied; Verification Gate; the retrospective, filled in at the end.

Corrections to list:
- Issue #13's `shape.md:136` ("HELD on every value") and `:263` (`to_normalized`, "HELD failing
  on no value").
- The previous revision's `shape.md`:
  - Decision 8's "likewise at 0.5 and 2 ** -20";
  - its "Open" item on the exponential groups;
  - its Results' "the property as stated breaks on none", which held only under the sweep's
    `~short` excuse of the set path;
  - every sentence claiming exactness above the floor.

## Task 2: Tests and fixtures

**`tests/conftest.py`:**
- Add `stepped(value, steps, width)`, a plain function, and a `stepped` fixture that returns it.
- `recorded_rows` and the two row fixtures are unchanged.

**`tests/unit/test_parameters.py`:**
- `_shares_its_display(record, preset)`: `record.to_display(preset)` equals the display of the
  float32 just below or just above it. Its docstring names the absorption and #15.
- `_assert_comes_back`:
  - A1 on every value.
  - `held == preset or _lands_below_its_power_of_two(preset, held)`.
  - `back == preset or _shares_its_display(record, preset)`.
  - `shown == display or (_shares_its_display(record, preset) and shown == stepped(display, ±1, 64)) or _lands_below_its_power_of_two(preset, held)`.
  - `_ABSORBED` is removed, and its measurement's history moves into `_shares_its_display`'s
    docstring.
- The property's docstring states exactness but at the two named exceptions (R1).
- **The volume characterization (R2, R14)** uses the committed `parameter_map().find("volume")`,
  not `_VOLUME`.
  - It asserts that the curve's own float32 (`record.curve.to_preset(display)`) is not held, which
    #15 leaves true, instead of asserting it of `to_preset`'s value.
  - It asserts the preset shares its display (not `<= _ABSORBED["volume"]`).
  - It asserts `to_display(held) == stepped(display, steps, 64)`.
- **The power-of-two characterization (R3, R16):**
  - Bind `env_1_delay` once.
  - Drop the `to_preset(above) == preset` assertion. The docstring says the row's own normalized
    value lands on the power by construction, so a landing float32 exists without assuming
    today's `to_normalized`.
  - `held == stepped(preset, steps, 32)`.

**`tests/integration/test_vital_plugin.py`:**
- The volume measure compares `record.to_display(held) == stepped(display, steps, 64)` (R17).
- New, for R6: `test_a_held_power_of_two_set_through_the_host_lands_as_recorded(host, initial, power_of_two_presets, stepped)`.
  - For each row and each of `env_1_delay` and `env_3_hold`: load `initial`; set through the map;
    assert `held == scale.to_preset(scale.to_normalized(preset))` and
    `held == stepped(preset, steps, 32)`.
  - Its docstring says #15 changes the rows to 0, and that this test then holds Vital at 1.0.
- The load test's docstring (R15): "after each of the four histories the probe tried", and that
  the module's order is not one the test relies on.

**`tests/data/power-of-two-presets.txt`:**
- Rows for 0.5 (`3eb504f4`) and 2 ** -20 (`35b504f4`).
- The header marks every row measured on the plugin, with machine, Vital and pedalboard.
- The steps are taken from the probe (Task 4).

**`tests/data/volume-floor.txt`:** its header's "the committed map's own arithmetic" becomes true
through the committed record.

## Task 3: The sweep, rerun (R7, R8, R9, Decision 1's counts)

Copy the previous revision's `sweep.py`, then:
- read both row files through `tests/conftest.py`'s `recorded_rows`;
- name #15 in the legend;
- per counted group, add `SHARE` (the predicate alone), `A3x` (A3 failures the predicate does
  not cover) and `SETx` (set-path failures neither excuse covers);
- `bound!` becomes `A1 | HELDx | A3x | SETx`, with no `~short` special case;
- add a HELD-only section for the 9 exponential groups: `S` and `N`, checked against the scalar
  methods on 200,007 values first, then every float32. The display, A2, A3 and the set path stay
  uncounted there and are named as such.

Run it with the tree printed first, into `verification/sweep.txt`. **Stop and ask the owner** if
any `A3x`/`SETx`/`HELDx` is non-zero in any group, before shipping. Report `SHARE`'s width either
way.

## Task 4: The probe, rerun

Copy the previous `plugin_probe.py`, then:
- read the new power-of-two rows;
- measure 0.5 and 2 ** -20 on `env_1_delay` and `env_3_hold`, through the map and through the
  float32 above;
- print blobs and helper sources, including `stepped`.

Write `verification/plugin-probe.txt` last, after all test edits, so the hashes match the shipped
files. Fill the rows' steps from it.

## Task 5: Docstrings and docs (R1, R12, R13)

- **`src/patchbay_vital/parameters.py`:** the module docstring says exactness but at the two
  exceptions.
- **`CHANGELOG.md`'s issue #13 entry**, corrected in place:
  - "exact above the floor" becomes exact but at the envelope powers of two;
  - "fails on 16,069,858, all at or below" becomes 16,069,858 on volume, all at or below, and
    1,512 more on the envelope powers of two, above any floor;
  - the new integration test and rows;
  - `_shares_its_display` in place of `_ABSORBED`;
  - the HELD count on the exponential groups.

## Task 6: Mutation (Decision 1)

`verification/mutation.txt`, on scratch copies:
- **M1:** volume's record copied under another id. This revision's property passes at the floor
  rows; HEAD's `_assert_comes_back` fails (no allowance by name).
- **M2:** a record named `volume` whose curve has no absorption (volume's scale, offset 0).
  Instrumented to count branches over the rows and over 10,000 presets at or below 2 ** -43: HEAD's
  takes the allowance branch on every one, this revision's takes none and asserts A3 and the set
  path exactly. The transcript says why no test-failure form of M2 exists.

## Task 7: Issues (Decision 4)

Read each body first and record old beside new in shape.md; then use `gh issue edit --body-file`.
- **#15:** the HELD count on the exponential groups, and what stays open; the 0-step row stays
  unchanged under the fix; the new integration test; `_shares_its_display`; the corrected test
  names. Narrow the open libm item as directed.
- **#40:** proposal (c)'s evidence gains `_shares_its_display` and its count.

## Task 8 (FINAL): Verification gate

1. `scripts/gate.sh` (steps 1–6): exit 0, Vital installed, integration tests run, none skipped.
   Saved to `verification/gate-run.txt`, on the final tree after the retrospective's edits.
2. **Negative harness:** files under `tests/` change, so rerun `scripts/gate-negative-tests.sh`
   once whole (`verification/gate-negative-tests.txt`) and j (`verification/ci-negative-test.txt`).
3. **Docs (step 7):**
   - `README.md` (the `tests/` paragraph, `stepped`) and `CLAUDE.md`;
   - every changed docstring and header;
   - `builders.py`'s reason, still true;
   - every standard naming a removed or renamed name (`_ABSORBED`, `_lands_below_its_power_of_two`'s
     siblings).
4. **Version (step 8):** the corrected `[Unreleased]` entry; 0.0.1 kept.
5. **Standards retrospective (step 9):** each project edit approved by the owner with
   AskUserQuestion, and each standard its own change set with its `index.yml` entry.
   - Expected project edits:
     - `vital/parameter-map.md`: the round-trip bullet's exactness, `_shares_its_display`, the
       exponential HELD count, and the open item narrowed;
     - `vital/measures.md`: `stepped`;
     - `vital/plugin-state.md`: "no set before it" reworded for the histories (R12), and the
       power-of-two integration test;
     - `index.yml`'s parameter-map entry (R1).
   - Possible base proposals: the step helper beside shared rows, which fits #40's (a). Present
     them with AskUserQuestion, file the approved ones (or revise #40), and record
     `Proposals sent upstream:`.

Final report:
- the feature files and the retrospective files, listed apart;
- the issue edits;
- what remains open;
- any PR-body sentence now untrue.

Findings, R1–R17:
- **R1:** the exactness claims (`test_parameters.py:217`, `CHANGELOG.md:189,197`,
  `parameter-map.md:91`, `index.yml`).
- **R2:** the 0-row assertion.
- **R3:** `to_preset(above)`.
- **R4:** the name lookup.
- **R5:** the mutation reached only through rows (noted).
- **R6:** the power-of-two integration test.
- **R7:** the sweep's literal `ROWS`.
- **R8:** the `(issue #N)` placeholder.
- **R9:** the exponential HELD count.
- **R10:** issue #13's lines 136 and 263.
- **R11:** the standards' exactness claim (= R1).
- **R12:** "no set before it".
- **R13:** Decision 8's "likewise".
- **R14:** `_VOLUME` versus the committed record.
- **R15:** "every history".
- **R16:** the double lookup.
- **R17:** the step helper.
