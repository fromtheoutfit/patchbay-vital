# Revision after the review of PR 14

## Context

The review on https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6806758858
(2026-11-11 20:49Z, at `0568b32`) lists 16 findings against issue #13's spec
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`). None is a crash; most are
claims that say more than the tests hold. These were checked while shaping:

- **Finding 1 holds:** at r = 1.4144055385838898e-18 a set holds `to_preset`'s value exactly
  (P1 == P2, P1 held), so "never `to_preset`'s" is false below the floor generally.
- **Finding 7 holds:** at 1.53642479121845e-17 (the floor's own) P1 is unheld and the display
  lands −1 ulp off. `to_preset(1e-14)` is 7.4e-11, which is above the floor.
- **Finding 3's bound is true:** all 308,386 set failures (exponents −58..−56) are exactly one
  double ulp off: +1 on 154,100 and −1 on 154,286. The new sweep records this.
- **Finding 4 holds:** once `back == preset`, line 241 re-runs line 238.
- **Finding 10's scope:** the map has 69 scale/curve groups (54 linear, 9 exponential or
  exponential_inverted, 3 quadratic, 2 quartic, 1 square_root). Only 3 groups were swept.
- **Finding 14's constraint:** `tests/` has no `__init__.py` (base/testing/tests) and pytest's
  import path is per directory, so `tests/integration` cannot import a plain module from
  `tests/unit`. `tests/conftest.py` is covered by the existing `"tests/**"` ruff ignores, so no gate
  file changes.
- **Finding 8's history risk:** `test_the_census_regenerates_the_committed_map` sets every
  parameter, chorus_feedback included, before any later test runs.

The revision is a new spec folder on this branch, so PR 14 carries it. **No behaviour changes** and
no gate file changes. No stage, commit, push or PR edit by an agent.

## Decisions (owner, 2026-11-11, AskUserQuestion)

1. **#12, the altitude finding:** the map fix stays out of this PR, but is not left to #8.
   - shape.md answers finding 12 by agreeing the map is also wrong below the floor.
   - A new patchbay-vital issue is filed, no attribution, for the spec that runs before #8.
     - Scope: where `to_preset`'s float32 is not one the scale holds, it returns the held
       neighbour that shows the given display.
     - Evidence required:
       - the every-float32 sweep rerun, showing A2 and the set path hold on every value and that
         no arbitrary display's result changes;
       - the integration measure against Vital;
       - the characterization test replaced on purpose by the property holding everywhere.
     - Left to #8: whether `VitalInstrument.set` keeps the stored value when the display given is
       the one it already shows, and the nearer neighbour for arbitrary displays (finding 1).
   - #8 is revised in place: its finding 3 points at the new issue for the set path's display, #8
     depends on it, and the candidate fix recorded there moves to the new issue.
2. **#2–#4, the set path:** the bound is stated as what it is.
   - Exact above the floor; within one neighbouring double at or below it. The property's
     docstring says the new map issue removes the second half.
   - The three pinned values each name their direction.
   - The new sweep prints its tree first. It shows the bound holding on every float32 normalized
     value, with the count at each distance (0, +1, −1).
3. **#10, the counting rule:** the rule says exactly what was done.
   - Counted over every float32 normalized value for the 60 groups the sweep reproduces bit for
     bit (linear, quadratic, quartic, square_root), and for each of the six offset records
     directly.
   - The 9 exponential groups rest on the property's exponent-spread draws and pinned examples.
   - The sweep checks its arithmetic against the shipped implementation per group before
     counting, and its transcript shows that check.
   - The exponential groups' full count is recorded as open in shape.md, with what it would take
     (the platform libm, call by call, hours of compute). It is not started here.
4. **#8, the load observation:** an integration test holds it.
   - It records the machine and Vital's version the way its neighbours do, and skips by name on
     another machine.
   - `plugin-state.md` cites the test as what holds it, and the probe as where it was first seen.
5. **#14, the named values:** one recorded file, `tests/data/volume-floor.txt`.
   - It is read through one fixture in a new `tests/conftest.py`, which both modules take.
   - `_double_ulps` is removed in favour of `_ulps`.
   - Its header says what produced the values (the sweep, by spec folder) and that the new map
     issue is expected to change the three non-zero rows. It also says which rows were measured on
     the plugin, and for those the machine and Vital's version.
   - The negative harness is rerun: this branch's harness (main's), one run, its transcript whole.
     Case q must still do what its header says with `tests/conftest.py` beside the conftest it
     writes. shape.md notes for #11's revision that `tests/conftest.py` now exists, so its own
     harness rerun is the first to exercise case q against it.
6. **#1, #9, #16, earlier text:** issue #13's spec folder stays as written.
   - This spec's shape.md lists each corrected sentence with its file and line, old beside new,
     under a heading a reader of the earlier folder would look for, as the PR 12 revision did.
   - Issue #8's body is revised in the same edit as Decision 1's.
   - The PR body and 88d438d's message are left alone. The final report lists which of their
     sentences are now untrue and what is true.
7. **Steps 2–5:**
   - No visuals.
   - References as in Task 1.
   - Mission unchanged.
   - Standards: the core five plus base/testing/tests, process/verification-gate,
     standards-retrospective, standards-index, ownership, vital/parameter-map, vital/measures,
     vital/preset-tests and vital/plugin-state (base at `e31f7db`).

Decided in shaping, within those answers:

- **Finding 5:** the integration test asserts `held != record.curve.to_preset(display)`. That is
  the curve's raw float32, which the map fix leaves unchanged, so the test's code survives the fix
  and only the file's rows change.
- **Finding 6:** the integration test reloads `initial` before each set, as the probe does.
- **Finding 11:** the integration test calls `_held_after_a_set`.
- **Finding 13:** the probe prints the blob hash of each file it imports and the source of each
  helper it calls.
- **Finding 15:** the `plugin-state` index entry is updated in the retrospective.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`, modelled on
`2026-11-10-1438-revision-after-pr-9-third-review/`:

- **plan.md**: this plan.
- **shape.md**:
  - Scope, shaping answers in the owner's words, what was checked, and the decisions above.
  - A 16-row findings/outcome table.
  - **"Corrections to issue #13's spec"**: file:line, old beside new.
    - Its `shape.md`: :87 (the sweep "on each record with a curve offset") and :112 ("never
      `P1`", "never `to_preset`'s").
    - Its Decision 3: "above the floor line 221 itself" (finding 4).
    - Its Decision 6: `_BELOW_VOLUME_S_FLOOR` and `_double_ulps`.
    - Its Docs line :264 (finding 9: volume's −80 dB is preset 0, at the floor, held by chance).
    - Its retrospective: "re-quantizing … still covers its edit" (finding 15).
    - Its `sweep.txt` and `plugin-probe.txt`, superseded by this folder's.
  - The open item: the exponential groups' count.
  - The note for #11's revision.
  - Standards Applied, the Verification Gate and the Standards Retrospective (the last two filled
    in at the end).
- **standards.md**: the full text of each confirmed standard as it reads now.
- **references.md**:
  - issue #13's folder (`sweep.txt`'s `Vec`, `plugin-probe.txt`);
  - `tests/unit/test_parameters.py` and `tests/integration/test_vital_plugin.py`;
  - `tests/data/fma-vectors.txt` read by `tests/unit/test_float32.py:98`, the recorded-file
    precedent;
  - `tests/unit/builders.py`, why it is not a conftest;
  - base/testing/tests's one-conftest rule;
  - the PR 9 third-review folder (format);
  - `24b2b5d`'s shape.md Decision 2 (the corrections pattern);
  - the review comment.

## Task 2: Start the sweep (findings 2, 3, 10, 16) in the background

`verification/sweep.txt`:

- **Header:**
  - date, branch and HEAD;
  - `git status --short`, printed first;
  - the script, then its output.
- **Run:** `uv run --locked python <scratch>/sweep.py`, started before any code edit (the
  arithmetic is unchanged by this revision). About 63 counts of roughly 60 s each.
- **The script generalizes issue #13's `Vec`:**
  - any `multiply`;
  - the `linear`, `quadratic`, `quartic` and `square_root` skews;
  - indexed scales;
  - clamping as `MappedParameter.to_preset` clamps.
- **Groups:**
  - Every record is grouped by (parameter kind, scale kind/min/max, curve kind/multiply/offset,
    parameter min/max), and every group is printed with its ids.
  - The 9 exponential groups are listed as not counted, with the reason.
- **Per counted group,** and again for each of the six offset records directly:
  1. First, the check against the shipped scalar methods on 200,007 values: bit-uniform values
     plus named edges, the four rows among them. It prints mismatches and uncertified counts.
     A group with a mismatch is not counted and joins the open item.
  2. Any value whose sum it cannot certify exact falls back to the scalar method, counted.
  3. Then every float32 in [0, 1], by binade, counting:
     - A1, HELD, A2 and A3 (A3 above `_ABSORBED`'s floor, or everywhere without one);
     - the set path's display distance as a histogram (0, +1, −1, other);
     - any failure above the floor.
- **Expected:** volume's 308,386 split 154,100 / 154,286; "other" 0 everywhere; nothing above any
  floor.

## Task 3: File the map issue (finding 12)

- Draft the body in shape.md per Decision 1.
- Title: "The parameter map: at or below volume's floor, `to_preset` returns a preset the scale
  does not hold; return the held neighbour that shows the display".
- It names:
  - `tests/data/volume-floor.txt`'s three non-zero rows;
  - the renamed characterization test as what its fix replaces;
  - this spec's verification files.
- No attribution. `gh issue create --repo fromtheoutfit/patchbay-vital`. Record its number
  (called #N below) in shape.md.

## Task 4: The recorded file and its reader (finding 14)

- **`tests/data/volume-floor.txt`**, one row per value: normalized as float32 hex, the signed
  double steps, a note.
  - `1f8a4c4c 0` issue #13's value
  - `22800005 +1` the smallest of the 308,386
  - `2384caf4 -1` 1.439742266862027e-17
  - `238db5ce -1` the floor's own, 1.53642479121845e-17
  - The `#` header says:
    - what produced the values: this spec's `verification/sweep.txt`, by folder;
    - that #N is expected to change the three non-zero rows;
    - which rows the probe measured on the plugin, with the machine, Vital and pedalboard.
- **`tests/conftest.py`:**
  - A docstring.
  - `volume_floor_rows(path) -> tuple[tuple[float, int], ...]`, a plain parser that refuses a
    malformed row by name.
  - A function-scoped fixture `volume_floor` that reads the file through `pytestconfig.rootpath`.

## Task 5: The unit property and characterization (findings 2, 3, 4, 7)

In `tests/unit/test_parameters.py`:

- **`_assert_comes_back`:**
  - Drop line 241.
  - Keep A1 and HELD on every value, and A3 above `_ABSORBED`.
  - At or below the floor, assert the set path's display is the display or a neighbouring double
    (`math.nextafter` both ways).
  - Its docstring and the property's say: exact above the floor, where it follows from A3 and
    HELD; within one neighbouring double at or below it, which #N removes.
- **The `@example`s:** keep the issue's own (its counterexample) and remove `_ONE_ULP_OFF`'s and
  the constant itself.
- **The characterization test:** rename `test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off`
  to `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded`.
  - It takes `volume_floor`.
  - For each row it runs `_assert_comes_back(_VOLUME, r)` and asserts the display lands at the
    row's signed step. Assertion messages name the row.
  - Its docstring says this is today's map, that #N changes the non-zero rows on purpose, and that
    the integration test reads the same rows.
- **`_ABSORBED`'s docstring** and the summaries: "below" becomes "at or below". Units are said in
  presets, with the floor's normalized value (about 1.54e-17).

## Task 6: The integration tests (findings 1, 5, 6, 8, 11, 14)

In `tests/integration/test_vital_plugin.py`:

- **Helpers:**
  - Remove `_BELOW_VOLUME_S_FLOOR` and `_double_ulps`.
  - `_ulps(a, b, dtype=np.float32)` counts float32 or double steps.
  - `_held_after_a_set` moves above its first user.
- **Finding 11:** `test_a_value_set_through_the_host_is_the_one_the_state_holds` calls
  `_held_after_a_set`.
- **The measure:** rename it to
  `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value(host, initial, volume_floor)`.
  For each row it:
  1. runs `host.load_state(initial)`;
  2. sets the value with `_held_after_a_set`;
  3. asserts `held == scale.to_preset(to_normalized(display))`;
  4. asserts `held != record.curve.to_preset(display)`;
  5. asserts `_ulps(to_display(held), display, np.float64)` and the direction equal the row.

  Its docstring is scoped to "where `to_preset`'s float32 is not one the scale holds", and says #N
  changes the non-zero rows of the shared file on purpose.
- **New, for finding 8:** a test of a load with no set before it.
  - It asserts `(host.name, host.version) == (committed.instrument, committed.vital_version)`.
  - It loads `initial` with volume at each row's P1. In the same load, chorus_feedback has its
    off-grid initial value.
  - It asserts volume is held as P2 and chorus_feedback as given.
  - Its docstring calls this an observation no one has explained, and names the histories the
    probe measured.
  - If Task 8 shows histories that disagree, stop and ask the owner before keeping any assertion
    one history breaks.

## Task 7: Docstrings in `src/patchbay_vital/parameters.py` (finding 7)

- The module docstring (:14, :16) and `MappedParameter.to_preset` (:242): "below" becomes "at or
  below".
- `to_preset`'s summary is scoped as Decision 1 leaves it; #N is cited.
- Docstrings only.

## Task 8: The probe, rerun (findings 6, 8, 13)

`verification/plugin-probe.txt`, run after Tasks 4–7, from the repository root:

- **Header:** tree first; machine, Vital and pedalboard; `git hash-object` of
  `tests/integration/test_vital_plugin.py`, `tests/conftest.py` and `tests/data/volume-floor.txt`;
  `inspect.getsource` of each helper it imports.
- **Measures, on every row:**
  - the test's exact sequence: load `initial`, set, read;
  - the load observation under three histories: a fresh instance; after `build_map(host)` and a
    load of `initial`, which the census test leaves; and after a set of volume and a load of
    `initial`.
- Update the data file's "measured on the plugin" header from it.

## Task 9: Issue #8 and the CHANGELOG

- **Issue #8:** after Tasks 2 and 8, read its whole body, write the revised body to the scratchpad,
  and record old beside new in shape.md. Then `gh issue edit 8 --body-file`.
  - Finding 3 points at #N for the set path's display, #8 depends on #N, and the candidate fix
    moves to #N.
  - "never `to_preset`'s" is scoped.
  - "every record with a curve offset" says what was counted.
  - This spec's files are cited. Everything else, footer included, is left as it is.
- **CHANGELOG:** correct the issue #13 `### Fixed` entry in place, since it describes what lands:
  - the scoped Vital claim;
  - what the characterization test holds (four rows with directions, the bound on every value);
  - the renamed tests, the shared file and `tests/conftest.py`, and the load test;
  - "at or below";
  - #N, and both spec folders.

  The version stays 0.0.1.

## Task 10 (FINAL): Verification gate

1. `scripts/gate.sh` runs steps 1–6 (`bash -n`; `uv sync --locked` and ruff format; ruff check;
   mypy; pytest; `sync-standards.sh --check`). It must exit 0 with Vital installed and the
   integration tests run, not skipped. Saved to `verification/gate-run.txt`.
2. **Not covered by the gate:**
   - **Negative harness:** `scripts/gate-negative-tests.sh`, this branch's, one run, its whole
     transcript in `verification/gate-negative-tests.txt`, ending with 0 unexpected. Case q is read
     against its header with `tests/conftest.py` present.
   - **Mutation** (`verification/mutation.txt`), on a scratch copy, never the working tree: make
     `NormalizedScale.to_normalized` return the float32 above its result at or below the floor.
     Show the new bound and the characterization test fail where the PR 14 property passes.
3. **Docs (step 7)**, checked and recorded in shape.md:
   - `README.md` and `CLAUDE.md`;
   - both test modules' headers;
   - `builders.py`'s "not a conftest" reason, still true;
   - `conftest.py`'s docstring;
   - the docstrings changed;
   - every standard that names a renamed test or a removed constant.
4. **Version (step 8):** the corrected `[Unreleased]` entry; 0.0.1 kept.
5. **Standards retrospective (step 9),** from the shipped diff. Expected project edits, each
   approved by the owner, listed apart from the fixes:
   - `vital/parameter-map.md`: the round-trip bullet with "at or below", the bound, the rows file
     and #N; the counting rule scoped as in Decision 3, with "checked on 200,007 values per group",
     not "value for value".
   - `vital/measures.md`: the scoped claim, the shared file and fixture, `_ulps`, and the test and
     probe now running one sequence.
   - `vital/plugin-state.md`: the load bullet cites the new test, and the probe as first seen.
   - `index.yml`'s `vital:` descriptions for `plugin-state` (finding 15), `parameter-map` and
     `measures`.

   Possible base proposals (presented with AskUserQuestion, multi-select, before the spec is
   done; approved ones filed as one patchbay-standards issue, no attribution):
   - recorded rows that two test trees share are read through a fixture in `tests/conftest.py`;
   - a revision of #39 naming the rows file.

   Record `Proposals sent upstream:`.

Final report:

- the feature files and the retrospective files, listed apart;
- the #N link and the #8 edit;
- the open exponential count;
- the PR body's and 88d438d's sentences that are now untrue, with what is true.

If any step fails, fix the cause and rerun. The spec is not done until the gate is green and Docs,
Version and the retrospective are recorded.
