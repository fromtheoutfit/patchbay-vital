# Revision after the Second Review of PR 14 — Shaping Notes

Shaped 2026-11-11 in plan mode with this repository's customized `/agent-os:shape-spec`. Each
claim of the review was checked against HEAD before any question. The owner then answered four
questions on the findings and one confirming steps 2 to 5.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The second review of PR 14, https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6811755893
(2026-11-12 01:34Z, "Review of `main...HEAD` (88d438d, 0568b32, 412b21a, c159446)"): a main
problem, two tests #15's fix would break, six requested checks and five smaller findings. In the
owner's words, "Let's read through the latest round of review on pr 14 and address the issues".
On the same branch, so PR 14 carries it; the first review's revision is `412b21a` and `c159446`,
committed and pushed by the owner. CHANGELOG entry, gate green, `verification/gate-run.txt`. No
behaviour change in `src/patchbay_vital/`, no gate file change. No stage, commit, push or pull
request edit by an agent.

## Shaping answers

- **Check 1, the floor's name lookup**, in the owner's words: "1 [a value predicate], with the
  condition #40's own rule sets: the sweep must show the predicate's set equals the failures, per
  group, not only contains them. If _shares_its_display excuses values where A3 and the set path
  do not fail, stop and present the counts before shipping it: either the predicate is tightened
  until the sets match, or shape.md says exactly which values are excused without failing and why
  that is accepted. A mutation shows a record with the same absorption under another name gets
  the allowance, and a record named volume without it does not."
- **Check 3 and Decision 8's "likewise":** an integration test of the power-of-two rows and rows
  for 0.5 and 2 ** -20. "The header marks the rows measured on the plugin and records the machine
  and Vital's version, as the base rule for measured data asks; the test skips by name on another
  machine. Decision 8's sentence is listed under Corrections with what the transcript now shows
  at 0.5 and 2 ** -20."
- **The step helper:** a fixture helper in `tests/conftest.py`.
- **The issues:** #15 and #40 revised in place, "with two points: #15: say exactly what is now
  counted on the 9 exponential groups (HELD, scale-only arithmetic, 0 failures on every float32
  normalized value) and what is still not (the claims that pass through the platform's pow/log2:
  the display coming back, A2 and the set path). If the issue already carries a paragraph
  scheduling the libm count, narrow it to those claims; if it does not, record them as open for
  the owner to schedule. The date: it is still 2026-11-11 for the owner (20:42 in New York). Use
  "Revised 2026-11-11" unless the repository's other dates are UTC, in which case say which
  convention the spec folders and CHANGELOG follow and use that one consistently." The spec
  folders are named from local time (EST) and the commits carry −0500, so the dates here are local:
  "Revised 2026-11-11".
- **Steps 2 to 5:** confirmed as listed. No visuals. References in `references.md`. The mission
  unchanged. Standards: the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`, `base/process/ownership`,
  `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and `vital/plugin-state`. Snapshot
  in `standards.md`, base at `e31f7db`.

## What was checked while shaping

- **The main problem, by reading the first revision's sweep:** `SET?` 1,512 and `above!` 1,512 on
  the 12 envelope records, which its `bound!` excused by `~short`. The four sentences stand where
  the review names them: `tests/unit/test_parameters.py:217`, `CHANGELOG.md:189` and `:197`,
  `agent-os/standards/vital/parameter-map.md:91` with `index.yml`'s entry. Its summary's `A2` is
  16,071,370, of which 1,512 are the envelope records'.
- **The two tests #15 would break, by running:** with the recorded candidate, `back` is
  `0.7071068286895752`, `above` `0.70710688829422`, and `to_preset(above)` 1.0000001192092896.
  The volume test's `back` unheld assertion fails at the 0-step row once `to_preset` returns a
  held preset.
- **Check 1:** `_ABSORBED.get(record.id, -math.inf)` keys the floor by name.
- **The smaller findings, by reading:** the hand-built `_VOLUME` equals the committed record today,
  scale, curve and parameter, so S2 is a re-census slipping past, not drift now; the other findings
  hold as written.
- **Found while implementing:** `35b504f4`, the hex the plan named for 2 ** -20, is 2 ** -19's
  normalized value; 2 ** -20's is `353504f4` (its float32 below, `353504f3`, is the map's
  normalized value and holds `9.536742595628311e-07`). The row carries `353504f4`. The load test,
  like the volume characterization, loaded `to_preset`'s value, which #15 makes a held preset, so
  it would have stopped measuring the move it holds; it now loads the curve's own float32.

## Decisions

1. **The floor's allowance is a value predicate,** `_shares_its_display(record, preset)`: the
   preset shows the display of the float32 just below or just above it, the curve's offset
   absorbing the skew. It replaces `_ABSORBED`, keyed by id.
   - **How an exception works, in plain sentences, as the owner asked:** `_assert_comes_back`
     makes each exact check first, on every value. Only where that check fails does it ask the
     exception's predicate, and the value passes then only if the predicate holds. So an
     exception excuses the failures where its predicate holds, and never a value whose exact
     check passed.
   - **The sweep's counts** (`verification/sweep.txt`, every float32 normalized value of 74
     counts): `_shares_its_display` holds on 589,224,972 of `volume`'s values and on no other
     record's. On 572,449,131 of them the display maps to another preset, the exact check of the
     display's preset fails, and the predicate excuses it; on 308,386 of those the set's display is
     off, each by one neighbouring double, excused too. On the other 16,775,841 (`SHARE0`) nothing
     fails, so the predicate is never asked there and excuses nothing. No failure anywhere is left
     without its exception: `HELDx`, `A3x` and `SETx` are 0 on every count, so the set each
     exception excuses is the failures exactly, the owner's condition, and nothing stopped the
     work.
   - **The mutation** (`verification/mutation.txt`):
     - M1: volume's record under another id passes at its rows, where HEAD's lookup by name fails
       it at `assert back == preset`.
     - M2: a record named `volume` without the absorption is never excused (the predicate asked 0
       times on 10,004 values), where HEAD's lookup took its floor branch on all 10,004.
     - M3: where the predicate holds but the set path is pushed several doubles off, the
       exception does not excuse it. Of 562 such values, the 232 landing further than one
       neighbouring double all fail, and none other.
     - M4: a held power of two pushed a second float32 below is not excused by
       `_lands_below_its_power_of_two`.
     - The A3 case cannot arise. A1 runs first on every value, so a value that passes A1 and fails
       A3 has its display shown by another preset, which is the shared display itself.
2. **The set path is asserted on every value:** exact, or the display or a neighbouring double
   where the preset shares its display, or anything where the held preset lands below its power
   of two. That replaces "above the floor it follows from A3 and HELD", the sentence the main
   problem rests on.
3. **Both characterization tests assert what #15 leaves alone** (R2, R3): the volume test, now on
   the committed record (R14), asserts the curve's own float32 is unheld and the preset shares its
   display; the power-of-two test drops `to_preset(above) == preset`, the row's own normalized
   value landing on the power by construction.
4. **Power-of-two rows** for 0.5 and 2 ** -20, read by a new integration test on `env_1_delay`
   and `env_3_hold` (R6, R13).
5. **`stepped` in `tests/conftest.py`** reads every row's step, as a fixture of the same name
   (R17); `_ulps` goes back to float32 alone.
6. **The sweep rerun** reads the rows through `recorded_rows` (R7), names #15 (R8) and counts HELD
   on the 9 exponential groups (R9).
7. **#15 and #40 revised in place,** "Revised 2026-11-11".

## The 17 findings

| # | Finding | Outcome |
|---|---|---|
| R1 | Exactness above the floor claimed in four places | Fixed: the property states two exceptions on every value; the test, CHANGELOG, `parameter-map.md` and `index.yml` say so; the count corrected |
| R2 | The volume test's unheld `back` fails under #15 | Fixed: the curve's own float32 (Decision 3) |
| R3 | `to_preset(above)` fails under #15 | Fixed: dropped; the row's value lands by construction (Decision 3) |
| R4 | The floor keyed by name (check 1) | Fixed: `_shares_its_display` (Decision 1); mutation M1 and M2 |
| R5 | The mutation reached only through rows (check 2) | Noted: the property's draws cannot be made to reach a value; the rows pin it, and M1/M2 test the predicate itself |
| R6 | No integration test of the power-of-two rows (check 3) | Fixed (Decision 4) |
| R7 | The sweep's literal rows (check 3) | Fixed (Decision 6) |
| R8 | `(issue #N)` in the sweep's legend (check 4) | Fixed |
| R9 | HELD countable on the exponential groups (check 4) | Fixed: counted (Decision 6) |
| R10 | Issue #13's `shape.md:136` and `:263` missing from the Corrections (check 5) | Corrected here |
| R11 | The standards repeat exactness (check 6) | Fixed in the retrospective, with R1 |
| R12 | "A load with no set before it" beside histories with sets (check 6) | Fixed: "with no set between them", in the test and the standard |
| R13 | Decision 8's "likewise at 0.5 and 2 ** -20" unrecorded | Measured now; corrected here |
| R14 | The rows checked against the hand-built `_VOLUME` | Fixed: the committed record |
| R15 | "every history this module can give the load" | Fixed: "each of the four histories it tried" |
| R16 | `env_1_delay` looked up twice | Fixed |
| R17 | Two spellings of a row's step | Fixed: `stepped` (Decision 5) |

## Corrections to issue #13's spec and to the revision after PR 14's review

Both folders stay their record; these sentences are corrected here.

`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/shape.md`:

- **`:135-138`, Decision 3's "What holds instead"** (R10). Old: "HELD on every value, the
  normalized path inverting the scale on the preset the parameter holds". New: HELD on every value
  but 1,512, the envelope records' held powers of two, where it lands one float32 below (the first
  review's revision, Decision 8).
- **`:262-263`, Docs** (R10). Old: "`NormalizedScale.to_normalized` ("For a value the scale holds,
  `to_preset` of the result is that value again", HELD failing on no value)", recorded as reading
  true. New: false at those 1,512; the docstring was corrected by the first review's revision.

`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/shape.md`:

- **`:132-134`, Decision 2** (R1). Old: "Above the floor the set path is exact, which follows from
  A3 and HELD". New: above the floor it is exact but at the 1,512 values where HELD is excused, and
  the display there is far more than a double off (`env_1_delay` at 1.0 s shows about 0.99999976 s
  after a set). This revision asserts the set path on every value with both exceptions named
  (Decision 2 here).
- **`:158-159`, Decision 8** (R13). Old: "and the float32 above the map's normalized value holds
  1.0; likewise at 0.5 and 2 ** -20", measured in an unrecorded run. New: recorded now in
  `verification/plugin-probe.txt`, section 3: at 1.0, 0.5 and 2 ** -20, on `env_1_delay` and `env_3_hold`
  both, a set through the map holds the float32 below (0.9999999403953552, 0.4999999701976776,
  9.536742595628311e-07) and the float32 above the map's normalized value holds the power
  itself.
- **`:280-288`, Open** (R9). Old: "so the sweep's arithmetic cannot count them … Decision 8's
  defect is one the count would look for there too: an exponential record's held power of two
  that the normalized path lands short of is not yet known to exist or not." New: HELD, which reads
  the scale alone, is counted there now and fails on no value (`verification/sweep.txt`), so
  Decision 8's defect does not reach them; what still passes through `pow`/`log2`, the display
  coming back, A2, A3 and the set path, stays open (below).
- **`:405-406`, Results** (R1). Old: "the property as stated breaks on none (`bound!: 0`)". New:
  true only because that sweep's `bound!` excused the set path at the power-of-two values (`~short`),
  which the property's docstring did not say; this revision's `bound!` has no such case.
- **`:549-553`, the retrospective's `parameter-map.md` entry** (R1, R11): "and a set of the display
  shows it again exactly, but where a curve's offset absorbs it" omits the power-of-two exception;
  corrected in this retrospective.

## Open

- **The 9 exponential groups' curve claims** (5 `exponential`, 4 `exponential_inverted`, 159
  records): A1 (the display coming back), A2, A3 and the set path pass through the platform's
  `pow` or `log2`, which numpy does not reproduce bit for bit. Counting them would call the
  platform libm value by value, hours of compute. HELD is counted there now (0 failures). For the
  owner to schedule or decline; not started here.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing on
  either side": the property now says, on every value, where it does not and why.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the property's exceptions, the one conftest and its fixtures.
- `base/process/verification-gate` — the gate unchanged; its transcript; the harness rerun.
- `base/process/standards-retrospective` — the last step; a base change proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request edit; issues edited without
  attribution.
- `vital/parameter-map` — the claims the property holds, corrected in the retrospective.
- `vital/measures` — the measures at the rows, `stepped`.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the load's wording and histories.

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

**Results (2026-11-11):** exit 0 on branch
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`
at `c159446` with the change uncommitted, `verification/gate-run.txt`, on the final tree after the
retrospective's edits: steps 1 to 6 passed, 495 tests (494 and the new power-of-two integration
test), the integration tests among them with Vital installed, none skipped. No gate file changed.

- **Not run by the gate:**
  - **The sweep**, `verification/sweep.txt`, 83 counts, each matching the shipped scalar methods
    and the tests' `_shares_its_display` on 200,007 values first, no fallback: as under Decision 1;
    HELD 0 on the 9 exponential groups; the rows read through `recorded_rows`.
  - **The probe**, `verification/plugin-probe.txt`, Vital 1.6.4 through pedalboard 0.9.26 on arm64:
    every row of both files as recorded, through the tests' own sequences and `stepped`; the four
    load histories. The blob hashes of the four files it reads are those of the tree the gate ran.
  - **The mutation**, `verification/mutation.txt`, as under Decision 1.
  - **The negative harness:** files under `tests/` changed under what every case copies, so this branch's
    harness (`scripts/gate-negative-tests.sh`, HEAD's blob) was rerun once, every test but j,
    `verification/gate-negative-tests.txt`: 141 runs, 0 unexpected. Case q copied
    `tests/conftest.py` and did what its header says ("495 passed, 1 deselected" with `--ignore`;
    the ignored `tests/unit/conftest.py` failing step 5 by name). Case j, the CI replay,
    `verification/ci-negative-test.txt`: 3 runs, 0 unexpected. Both ran on the final tree, after
    the gate.

**Docs (step 7):** every file changed, and every document and standard naming them, checked
against the shipped code:

- `tests/unit/test_parameters.py`:
  - the property's and `_assert_comes_back`'s docstrings state the two exceptions on every value,
    and that #15 removes the power of two's and the neighbouring double but not the shared
    display's excuse of the preset;
  - `_shares_its_display`'s docstring carries `_ABSORBED`'s measurement and says it is a value of
    the record's scale and curve, never its name;
  - both characterization tests' docstrings say what they hold and what #15 changes.
- `tests/integration/test_vital_plugin.py`:
  - the measure's docstring names `stepped`;
  - the new power-of-two test says what #15 changes;
  - the load test's says "with no set between them" and "each of the four histories it tried",
    and that it does not rely on which precedes it;
  - `_ulps` is back to float32 alone.
- `tests/conftest.py`'s docstring names `stepped`, and `stepped`'s says it is the one reading of a
  row's step.
- `tests/data/power-of-two-presets.txt`'s header: three rows, all measured on the plugin, with the
  machine, Vital and pedalboard, read by both tests. `tests/data/volume-floor.txt`'s header cites
  this revision's probe, and its "the committed map's own arithmetic" is true now that the unit
  test reads the committed record.
- `README.md`, the `tests/` paragraph. Old: "… read through the fixtures of `conftest.py`, the one
  module both trees share." New: "…, whose `stepped` reads a row's step." The rest checked and
  true.
- `src/patchbay_vital/parameters.py`: unchanged and true. The module docstring claims no exact set
  path; `to_normalized`'s states the power-of-two exception.
- `CLAUDE.md` and `agent-os/product/`: unchanged and true.
- `tests/unit/builders.py`'s "not a conftest" reason: still true.
- The standards naming a removed or renamed name are the retrospective's; after it, `git grep`
  finds `_ABSORBED`, `volume_floor_rows` and `_double_ulps` nowhere outside the spec folders.

**Version (step 8):** `CHANGELOG.md`'s `[Unreleased]` `### Fixed` entry for issue #13 is
corrected in place, since it describes what lands:

- both revision folders are named;
- "it fails on 16,069,858, all at or below 2 ** -43" becomes 16,069,858 of `volume`'s, all at or
  below, and 1,512 more above any floor;
- the HELD count on the exponential groups is added;
- "A set's display is exact above the floor" becomes the two exceptions stated over values,
  consulted only where a claim fails;
- the three power-of-two rows, `stepped`, the committed record and the new integration test are
  added.

No behaviour changes; the version stays 0.0.1.

**Issues (Decision 7):** read before each edit, compared with the body last read, and read back
after it; no attribution.

- **#15** gains a "Revised 2026-11-11 (after PR 14's second review)" paragraph:
  - what the tests hold now;
  - what its fix changes and leaves (not the shared display's excuse of the preset);
  - the new integration test, which section 2 asked for;
  - the exponential groups: HELD counted (0); the display, A2, A3 and the set path open for the
    owner to schedule, since the issue had no paragraph scheduling the libm count.

  Corrected where they stand: "the row … changed to 0" becomes "the rows"; the exponential sentence
  gains "(corrected 2026-11-11: HELD is counted there now …)"; the integration test and the set
  path's requirement each gain a "(revised 2026-11-11 …)".
- **fromtheoutfit/patchbay-standards#40** gains a "Revised 2026-11-11" paragraph:
  - proposal 2's second instance, `_shares_its_display`;
  - what "the predicate's set equals the failures" means once the predicate is consulted only
    where its claim fails (the excused set, not the bare predicate);
  - the mutation;
  - proposal 1's shared helper (below).
- **fromtheoutfit/patchbay-standards#39** gains a "Revised 2026-11-11" paragraph: a
  characterization test asserts nothing its issue's fix would change but the recorded rows
  (below).

## Standards Retrospective

Step 9, from the shipped diff. The four questions:

1. **A pattern no standard covers:** two.
   - A shared helper beside the shared reader, handed to tests as a fixture (`stepped`).
   - A characterization test asserting around its rows only what the named fix leaves (the curve's
     own float32; no `to_preset(above)`).
2. **A standard wrong or stale:** three.
   - `vital/parameter-map.md`'s round-trip bullet: "a set of the display shows it again exactly,
     but where a curve's offset absorbs it", false at the 1,512 power-of-two values.
   - Its counting rule: the exponential groups "rest on the property's draws" for HELD, which is
     countable.
   - `vital/measures.md`'s `_ulps` reading of a step, and `vital/plugin-state.md`'s "a load with no
     set before it" beside histories with sets, and its "every history the integration module can
     give".
3. **A deliberate deviation:** none.
4. **A pointer moved:** `_ABSORBED` replaced by `_shares_its_display`, `_ulps`' double use by
   `stepped`; every standard naming them updated.

The project edits, each approved by the owner on 2026-11-11 with AskUserQuestion, listed apart
from the feature's files. Each standard is its own change set with its entry of `index.yml`'s
`vital:` section; the `base:` section is untouched (`scripts/sync-standards.sh --check` passing).

- **`agent-os/standards/vital/parameter-map.md` with the `parameter-map` entry.**
  - The header gains this revision.
  - The round-trip bullet is restated as exact on every value but at two exceptions stated over
    values, never a name. In the owner's condition's words, it says in plain sentences how an
    exception works: the exact check first, the predicate asked only where it fails, so the
    excused set is the failures and not the predicate's wider set. It carries the power of two
    (12 records, the three rows, a unit and an integration test) and the shared display
    (589,224,972; 572,449,131 excused; 308,386 one neighbouring double; 16,775,841 never asked),
    and says #15 removes the neighbouring double and not the preset's excuse.
  - The counting rule gains HELD on the 9 exponential groups (0), the rest of their claims open,
    and that an exception is counted by the failures it leaves.
  - The entry follows.
  - Verified against `tests/unit/test_parameters.py` (`_assert_comes_back`,
    `_shares_its_display`, `_lands_below_its_power_of_two`, both characterization tests), both row
    files, `tests/conftest.py`, and `verification/sweep.txt` and `verification/mutation.txt`.
- **`agent-os/standards/vital/measures.md` with the `measures` entry.**
  - A row's step is read by `stepped`, the one spelling every test and the probe use, in double
    steps for volume's display and float32 steps for a power of two's held preset.
  - `_ulps` is no longer named there.
  - The entry gains "a row's step read by one helper".
  - Verified against `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`,
    `test_a_held_power_of_two_set_through_the_host_lands_as_recorded`, `tests/conftest.py`
    (`stepped`) and `verification/plugin-probe.txt`.
- **`agent-os/standards/vital/plugin-state.md` with the `plugin-state` entry.**
  - The load becomes "of the starting state and then, with no set between them, of a state holding
    `volume` … at a float32 the scale does not hold, the curve's own for the display".
  - The histories become "each of the four histories the probe tried before the first load", and
    the test "does not rely on which history precedes it". Still an observation claiming no cause.
  - The entry follows.
  - Verified against
    `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`
    (`volume.curve.to_preset`, the two loads) and `verification/plugin-probe.txt` section 2.

Proposals sent upstream: fromtheoutfit/patchbay-standards#40, revised in place; #39, revised in place

### Standards retrospective (proposed, base)

Each presented to the owner on 2026-11-11 with AskUserQuestion and approved. In the owner's words,
"(a) and (b), each revised into its issue in place. Word (a) without this project's terms".

- (a) `base/testing/tests.md`, #40's proposal 1 (shared recorded rows): a helper that tests in two
  directories share lives beside the shared reader in `tests/conftest.py`. It is handed to tests as
  a fixture and never imported from the conftest. Verified against `tests/conftest.py` (`stepped`)
  and the three row tests. Proposed, not applied; filed as fromtheoutfit/patchbay-standards#40,
  revised in place.
- (b) `base/testing/tests.md`, #39's rule: a characterization test asserts nothing that the fix it
  names would change but the recorded rows. Around them it asserts only quantities the fix leaves.
  Verified against `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded` and
  `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#39, revised in place.
- #40's proposal 2 (value predicates), its second instance and its sharpened sentence, as Decision
  7 approved before the retrospective: filed as fromtheoutfit/patchbay-standards#40, revised in
  place.
