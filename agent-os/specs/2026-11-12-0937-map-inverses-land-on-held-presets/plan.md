# Issue #15 in PR 14: the parameter map's two inverses land on held presets

## Context

PR 14's third review, https://github.com/fromtheoutfit/patchbay-vital/pull/14 (comment "Review of
5e284ec", 2026-11-12 14:25Z), has 15 findings. Findings 1 and 2 say the PR records #15's two map
bugs as expected behaviour instead of fixing them:

- **Finding 1:** `NormalizedScale.to_normalized` lands one float32 below a held power of two, on
  12 envelope records at 126 powers each. A set of 1.0 s holds 0.9999999403953552.
- **Finding 2:** `MappedParameter.to_preset` returns a float32 the scale never holds at or below
  volume's 2 ** -43 floor.

The PR then pins both bugs in row files, characterization tests and test exceptions. The owner
**reversed the earlier decision to keep #15 separate**: two review rounds went on tests the fix
removes. So this revision is **issue #15's spec, with #13 beside it in scope**. It goes on the same
branch, so PR 14 carries it and closes both issues.

Checked while shaping (read-only, against HEAD 5e284ec):

- **Both candidate fixes work on the committed map.**
  - The `to_normalized` neighbour step fixes 1,512 of 1,512 power-of-two misses.
  - The `to_preset` snap leaves 0 of 12,004 sampled floor values off; today 143 are off.
  - A sample is not the evidence (Decision 2).
- **The fix restores main's property.** `main`'s `_assert_comes_back` asserted
  `scale.to_preset(record.to_normalized(display)) == back` on every value. That is issue #13's
  failing assertion, and the fix restores it, with `_shares_its_display` in place of `_ABSORBED`.
- **One existing assertion changes.** Under the fix, `to_preset(to_display(2 ** -43))` *is*
  2 ** -43, so `test_where_volume_s_offset_absorbs_a_preset`'s `!= last` becomes a claim about
  the curve's own float32.
- **Finding 7's boundary pin holds:** `not _shares_its_display(_VOLUME, first)`.
- **#8 finding 1's example is unchanged.** `_TEMPO` at 216.85141355537831 bpm keeps the same
  unheld float32, and no neighbour shows that display.
- **No negative-harness case depends on what this removes.** None reads `tests/conftest.py` or
  `tests/data/{volume-floor,power-of-two-presets}.txt`, and none pins a test count.
- **The census is unaffected.** `census.py:334` calls `to_normalized` on indexed whole steps,
  which already land.
- **The libm count is cheap.** The platform's `pow` and `log2` cost 18 ns a value each. Over the
  9 exponential groups the libm calls alone come to about 0.2 CPU-hours, against the "hours"
  assumed before. The last sweep ran 83 counts in 1,681 s on 10 processes.

No gate file changes. No stage, commit, push or PR edit by an agent.

## Decisions (owner, 2026-11-12, AskUserQuestion)

1. **Scope: #15 beside #13.** shape.md's first Decision cites both issues. It says the owner
   reversed the earlier decision to keep #15 separate, and why.
2. **Evidence is #15's in full, counted, not sampled.**
   - The every-float32 sweep reruns on every counted group. HELD, A2 and the set path must fail
     on no value.
   - No display's `to_preset` result may change, except where today's float32 is not one the
     scale holds.
   - The Vital probe and the integration tests rerun: Vital holds 1.0 after a set of 1.0 s, and
     the floor values land as the fix leaves them.
3. **What stays.**
   - The shared-display excuse of the preset coming back (A3) stays, with its count.
   - Open for #8: whether `VitalInstrument.set` keeps the stored value when the display is the
     one it already shows (#8's finding 3), and the nearer neighbour for an arbitrary display
     (#8's finding 1).
   - **If either fix would decide one of those, stop and present.**
4. **The 9 exponential groups.** `to_preset`'s change applies to every record. shape.md says what
   is counted there and what is not. Before the libm count of their curve-dependent claims runs,
   its cost goes to the owner, who starts it unattended or declines it (Task 7).
5. **Removed on purpose, each named in shape.md:**
   - the power-of-two exception (`_lands_below_its_power_of_two`);
   - the neighbouring-double tolerance;
   - the two characterization tests;
   - both row files, now empty of anything but steps the fix sets to 0;
   - `tests/conftest.py` with `recorded_rows`, `stepped` and the fixtures.

   The three Vital standards and CHANGELOG are corrected against the shipped code, the standards
   as their own change sets.
6. **Pinned values replace the row files.**
   - Each value is a constant with a comment naming what it is, written the same way in both test
     modules. shape.md says the duplicated inputs are accepted, and why the shared file went.
   - #40's proposal 1: revised in place, saying the fix removed its instance here and citing the
     commits where it existed, or withdrawn. **Present which before editing.**
   - #39 keeps its evidence the same way, by commit.
7. **Finding 15 is declined for this run.** The harness rerun is committed in full, as the base
   standard says, and shape.md gives that reason. The retrospective presents a base proposal for
   `base/process/verification-gate.md`:
   - a harness transcript may be committed as a mechanical extract: its header, each case's
     heading and exit lines, and the final count;
   - the extract carries the harness file's blob hash and the exact command that regenerates the
     whole;
   - the extract is produced by a stated command, never written by hand.

   Its evidence is the two transcripts on this branch: their sizes, and how few lines differ
   (count with `diff | wc -l`). If approved, it is filed with this revision's other new proposals.
   The earlier transcripts stay as recorded.
8. **Steps 2–5 confirmed.**
   - No visuals.
   - References: the previous revision's sweep and probe scripts, embedded in its `sweep.txt` and
     `plugin-probe.txt`, and both test modules.
   - The mission is unchanged.
   - Standards: the core five; `base/testing/tests`; the `base/process/` standards
     verification-gate, standards-retrospective, standards-index and ownership; and
     `vital/parameter-map`, `measures`, `preset-tests`, `plugin-state` and `float-writer`. Base
     at `e31f7db`.

Decided in shaping, within those answers:

- **`to_normalized`:** return the nearest float32 quotient `q`, unless `to_preset(q)` misses the
  preset. Then return the float32 one step toward the preset, if it lies in [0, 1] and lands on
  it; otherwise `q`.
  - The scale is monotone, since `span > 0`, so only that side can land.
  - A preset no float32 lands on keeps `q`, unchanged.
- **`NormalizedScale.holds(preset)`:** `to_normalized`'s result is in [0, 1] and `to_preset`
  of it is the preset. It is public, because tests and the snap both read it.
- **`MappedParameter.to_preset`:**
  - Compute today's clamped float32.
  - On an indexed scale, return the rounded whole number, as today.
  - Otherwise, if the scale holds it, return it unchanged. This guard makes "no change where today's
    float32 is held" structural.
  - Otherwise, of its two float32 neighbours, take those the scale holds and whose display is
    exactly the one given, and return the one nearer the curve's unrounded inverse. A private
    `DisplayCurve._inverse` provides that inverse, and `to_preset` rounds it.
  - If no neighbour qualifies, return today's float32 (an arbitrary display, #8's finding 1,
    unchanged).
  - #8 says #15 decides which preset a set of such a display stores, so the tie-break is this
    spec's. The sweep counts how often both neighbours qualify (`BOTH`) and records it.
- **`float32.next_float32(value, toward)`:** pure Python through the float32's bits, as the module
  is pure Python. It is the one way to step a float32, used by the fix and by the tests'
  `_shares_its_display` (finding 9).

## The 15 findings

| # | Finding | Outcome |
|---|---|---|
| F1 | `to_normalized` misses held powers of two | Fixed in `src/` |
| F2 | `to_preset` returns unheld float32 at the floor | Fixed in `src/` |
| F3 | Power-of-two exception leaves `shown` unbounded | Removed with the exception |
| F4 | Exact set-path check replaced by display-only | Restored: `scale.to_preset(record.to_normalized(display)) == back` on every value |
| F5 | `env_3_hold` given `env_1_delay`'s values unchecked | Assert scale and curve equal first |
| F6 | Load test reads and writes with `json` | `_floats(initial)` and the package's `loads`/`dumps`, asserting `dumps(loads(initial))` is `initial` first |
| F7 | Predicate's floor boundary not pinned | `assert not _shares_its_display(_VOLUME, first)` |
| F8 | Indented comment breaks `recorded_rows` | Removed with the conftest |
| F9 | Float stepping spelled four ways | `float32.next_float32`, the one spelling |
| F10 | Power-of-two check written twice | Removed with both uses |
| F11 | conftest's `noqa`, `dtype` order, `stepped` fixture | Removed with the conftest |
| F12 | conftest's import-mode reason inaccurate; README repeats it | Removed; README paragraph rewritten |
| F13 | `neighbours` built per example | Removed; the predicate is asked once, only where A3 fails |
| F14 | Function-scoped row fixtures | Removed with the conftest |
| F15 | 50k lines of transcripts | Declined for this run (Decision 7); base proposal |

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/` with:

- **`plan.md`:** this plan.
- **`shape.md`:**
  - scope, with the owner's answers in their words, and the checks above;
  - the Decisions, with Decision 1 citing #13 and #15 and the reversal;
  - the findings table;
  - the "Removed on purpose" list;
  - the open items (#8's two questions, the exponential count);
  - Standards Applied, the Verification Gate and the retrospective, filled in at the end.
- **`standards.md`:** a snapshot of the confirmed standards from HEAD.
- **`references.md`:** the previous revision's sweep and probe scripts (where each is embedded),
  `main`'s `_assert_comes_back`, both test modules and `tests/unit/test_float32.py`.

## Task 2: The fix in `src/patchbay_vital/`

- **`float32.py`:**
  - add `next_float32(value: float, toward: float) -> float`: the float32 adjacent to a float32
    `value` in `toward`'s direction, through `struct` bits;
  - zero steps to the smallest subnormal of `toward`'s sign;
  - `toward == value` returns `value`;
  - an infinity or a NaN returns as it is;
  - ValueError for a value that is not a float32;
  - the module docstring names it.
- **`parameters.py`:**
  - `NormalizedScale.to_normalized` and `holds`, as decided;
  - `DisplayCurve._inverse`, which `to_preset` rounds;
  - `MappedParameter.to_preset`'s snap;
  - `to_normalized`'s docstring and `to_preset`'s, rewritten to state the rules, with no "Issue
    #15 is to";
  - the module docstring: a value a parameter holds comes back exactly through display, preset
    and normalized path, but where presets share a display (the preset a display maps to is then
    a held one that shows it).

## Task 3: Unit tests

**`tests/unit/test_float32.py`:** `next_float32` at zero, across a binade, on a negative value, at
the largest float32 toward infinity, toward the same value, and refusing a non-float32.

**`tests/unit/test_parameters.py`:**

- **`_assert_comes_back`**, main's form, every check exact on every value:
  - A1: `to_display(back) == display`.
  - HELD: `scale.to_preset(scale.to_normalized(preset)) == preset`.
  - A2 and the set path: `scale.to_preset(record.to_normalized(display)) == back` (F4).
  - A3: `back == preset or _shares_its_display(record, preset)`, the predicate asked only there
    (F13).
  - The docstrings say A3 is the one excuse, and why it stays.
- **`_shares_its_display`** uses `next_float32` (F9). Its docstring keeps its measurement and drops
  "Issue #15 is to".
- **Removed:** `_lands_below_its_power_of_two`, both characterization tests, the `stepped` and row
  fixtures in signatures, and the `numpy` and `Callable` imports if they become unused.
- **Pinned values**, in the same form and with the same comments the integration module uses:
  ```python
  _VOLUME_FLOOR = (
      5.857149595214349e-20,  # issue #13's value
      3.4694490199051456e-18,  # the smallest of the former one-ulp landings
      1.439742266862027e-17,  # a former one-ulp landing below the display
      1.53642479121845e-17,  # the floor's own, preset 2 ** -43
  )
  _POWERS_OF_TWO = (
      0.7071068286895752,  # 1.0 on the envelope records
      0.3535534143447876,  # 0.5 on the envelope records
      6.74349621476722e-07,  # 2 ** -20 on the envelope records
  )
  ```
  - Held by `test_a_pinned_value_comes_back_exactly`, parametrized by record id over
    `volume × _VOLUME_FLOOR` and `env_1_delay, env_3_hold × _POWERS_OF_TWO` on the committed map.
  - This serves #15's "an `@example` pinning one such value", with one spelling in both modules.
  - The existing `@example`s on the hand-built property stay.
- **`test_where_volume_s_offset_absorbs_a_preset`**, restated:
  - the curve's own float32 for 2 ** -43's display is not 2 ** -43, and the scale does not hold
    it;
  - `to_preset` of that display is a held preset that shows it;
  - `_shares_its_display(last)` holds, and `not _shares_its_display(first)` (F7);
  - `first` comes back.
- **New, direct:**
  - `test_a_held_power_of_two_comes_back_through_the_normalized_path`, on the committed
    `env_1_delay` at 1.0: `to_normalized(1.0)` is `0x3f3504f4` and lands on 1.0;
  - `test_an_arbitrary_display_keeps_the_curve_s_float32`: `_TEMPO` at 216.85141355537831 is
    unchanged and unheld, left to #8 (finding 1).
  - It says so in its docstring.

## Task 4: Integration tests (`tests/integration/test_vital_plugin.py`)

- **The same two tuples**, with the same comments.
- **Floor test**, renamed, e.g. `test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`.
  For each value, from `initial`:
  - Vital holds `record.to_preset(display)` exactly;
  - the scale holds it;
  - it is not `record.curve.to_preset(display)`;
  - its display is the display set.
- **Power-of-two test**, renamed, e.g. `test_a_held_power_of_two_set_through_the_host_is_held`:
  - first assert `env_3_hold` has `env_1_delay`'s scale and curve (F5);
  - then on both records Vital holds the power: 1.0 after a set of 1.0 s.
- **Load test** (F6):
  - `given` is read with `_floats(initial)`;
  - `dumps(loads(initial.decode()))` is asserted to equal `initial`'s text first;
  - the loaded state is written with the package's `dumps`, `volume` set to the curve's own
    float32 for each floor value, through a `model_copy` of the settings' values;
  - the docstring is updated.
- **The module docstring** says states are written with the package's `dumps`.
- **Removed:** the `stepped` and row fixtures, and the `Callable` import.

## Task 5: Remove the row files and the conftest

- Delete `tests/conftest.py`, `tests/data/volume-floor.txt` and
  `tests/data/power-of-two-presets.txt`.
- **`README.md`'s `tests/` paragraph:** drop the conftest and row-file sentences, and say the
  pinned values live in each test module.
- `git grep` for `recorded_rows`, `stepped`, `volume_floor`, `power_of_two_presets`, `volume-floor`
  and `power-of-two-presets` finds nothing outside spec folders and the standards. The standards
  are the retrospective's.

## Task 6: The sweep, rerun (`verification/sweep.txt`)

Copy the previous revision's `sweep.py`, which is embedded in its `sweep.txt`, into the
scratchpad. Then:

- Reproduce the fixed `to_normalized` (N′) and `to_preset` (P1′) in numpy.
- Check them against the shipped scalar methods on 200,007 values per count first, with no
  fallback.
- Import `_shares_its_display` and the two tuples from `tests/unit/test_parameters.py`; drop
  `import conftest`.
- Counts per group, for the 60 reproduced groups, each of the six offset records and each of the
  12 envelope records:

  | Count | Fails on a value where | Must be |
  |---|---|---|
  | A1 | the display does not come back | 0 |
  | HELD | `S(N′(P0)) != P0` | 0 |
  | A2 | `S(N′(P1′)) != P1′` | 0 |
  | SET | `D(S(N′(P1′))) != D0` | 0 |
  | A3, A3x | `P1′ != P0`, and A3x where also not SHARE | A3x 0 |
  | SHARE, SHARE0 | as before | counted |
  | CHANGED, CHANGEDx | `P1′ != P1`, and CHANGEDx where also P1 held | CHANGEDx 0 |
  | NONE | P1 unheld and no neighbour qualifies | 0 |
  | BOTH | both neighbours qualify | counted |
  | NCHANGED | `N′(P0) != N(P0)` | 1,512 expected, only where `S(N(P0)) != P0` |

  - `bound! = A1 | HELD | A2 | SET | A3x | CHANGEDx | NONE` must be 0 on every count.
  - The pinned values are printed per row.
- HELD alone on the 9 exponential groups (scale arithmetic), as before.
- Print the tree first, then run.
- **Stop and present to the owner** if `bound!` is not 0 anywhere, or if the result would decide
  either of #8's questions.

## Task 7: The 9 exponential groups' curve claims, presented before they run

- Time the shipped arithmetic, Python's `math.pow`/`math.log2` (the platform libm the methods
  call) with numpy for the rest, on a 10M-value sample of one exponential group.
- Extrapolate to every float32 normalized value of the 9 groups (159 records) on 10 processes.
- **Present with AskUserQuestion:** wall time, method and counts (A1, A2, A3/A3x, SET,
  CHANGEDx, NONE, BOTH). The owner starts it unattended or declines.
- If started, its output joins `verification/sweep.txt` as its own section. If declined, shape.md
  says what is counted there (HELD) and what is not.

## Task 8: The Vital probe, rerun (`verification/plugin-probe.txt`)

Copy the previous `plugin_probe.py`, without `stepped` and `recorded_rows`. Then, on arm64,
Vital 1.6.4 through pedalboard 0.9.26, measure:

- each floor value set through the map: held, exactly `to_preset(display)`, shows the display;
- each power on `env_1_delay` and `env_3_hold`: Vital holds the power;
- the load of the curve's own float32, written through `dumps`, after the four histories.

Print the blob hashes of the files it reads. Write it last, after every test edit.

## Task 9: Mutation (`verification/mutation.txt`)

On scratch copies in the scratchpad:

- **M1:** `to_normalized` reverted to HEAD's. The unit tests fail at the power-of-two pins and
  the direct test, by name.
- **M2:** the snap removed. They fail at the floor pins (A2) and the restated absorption test.
- **M3:** `holds` without its [0, 1] check, if a value can show the difference; otherwise the
  transcript says why none can.

## Task 10: CHANGELOG, issues, PR text

- **`CHANGELOG.md` `[Unreleased]`:**
  - correct the #13 entry in place: no characterization tests, no row files, the property exact
    but A3;
  - add a `### Fixed` entry for #15: both inverses, `next_float32`, `holds`, and the evidence
    files;
  - the version stays 0.0.1.
- **Issues #15 and #8:** read each body first, record old beside new in shape.md, then
  `gh issue edit --body-file` with no attribution, and read it back.
  - **#15** gains a "Revised 2026-11-12" paragraph: the fix lands in PR 14, in this folder, with
    the evidence, what stays, and the exponential result.
  - **#8** gains one saying #15's fix is in PR 14 and its findings 1 and 3 remain open there.
- **PR 14's title and body:** list the sentences now untrue in the final report. The owner edits.

## Task 11 (FINAL): Verification gate

1. **`scripts/gate.sh`** (steps 1–6) exits 0, with Vital installed, the integration tests run
   and none skipped. Save it to `verification/gate-run.txt`, on the final tree after the
   retrospective's edits.
2. **The negative harness:** files are removed under `tests/`, so rerun
   `scripts/gate-negative-tests.sh` once whole, into `verification/gate-negative-tests.txt`, kept
   in full (Decision 7), and case j into `verification/ci-negative-test.txt`.
3. **Docs (step 7):** check, and record in shape.md:
   - `README.md` and `CLAUDE.md`;
   - the `parameters.py` and `float32.py` docstrings;
   - both test modules' docstrings;
   - `tests/unit/builders.py`'s "not a conftest" reason;
   - every standard naming a removed name.
4. **Version (step 8):** the `[Unreleased]` entries; 0.0.1 kept.
5. **Standards retrospective (step 9):** from the shipped diff, each edit approved with
   AskUserQuestion.
   - **Expected project edits,** each its own change set with its `index.yml` `vital:` entry:
     - `vital/parameter-map.md`: the round trip exact on every value but A3; the
       `to_normalized`/`to_preset` rules; the power-of-two and neighbouring-double text gone;
       the exponential count's state;
     - `vital/measures.md`: `stepped` and the row files gone, the pinned constants instead;
     - `vital/plugin-state.md`: the load written through `dumps`, the values inline.
   - **Base, presented before editing:**
     - #40: proposal 1 revised in place or withdrawn (the owner picks); proposal 2's
       `_lands_below_its_power_of_two` instance removed by commit;
     - #39's evidence, by commit;
     - the new `verification-gate.md` transcript-extract proposal (Decision 7). If approved, it
       is filed as one new issue with `gh issue create --repo fromtheoutfit/patchbay-standards`.
   - Record `Proposals sent upstream:`.

Final report:

- the feature files and the retrospective files, listed apart;
- the issue edits;
- what remains open (#8's two questions, and the exponential count if declined);
- PR 14's title and body sentences now untrue.
