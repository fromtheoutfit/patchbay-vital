# Revision after the Second Review of PR 9 — Shaping Notes

Shaped 2026-11-10 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered four questions on the findings and confirmed steps 2 to 5 together.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The owner's second review of PR 9, at `0fc8152` (the third comment on
https://github.com/fromtheoutfit/patchbay-vital/pull/9, 2026-11-10 18:02Z): 17 findings, four most
serious, seven correctness, six speed and duplication. Each was checked while shaping against the
code at the PR head; all hold. On the same branch, so PR 9 carries it. CHANGELOG entry, gate green,
`verification/gate-run.txt`. No stage, commit or push by an agent. No gate file changes.

## Shaping answers

- **Step 1, scope:** the 17 findings, in the owner's words "read through the latest round of
  review and address the issues".
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file` and
  `vital/preset-tests`. Snapshot in `standards.md`, base at `e31f7db`.

## What was checked while shaping

- **Finding 6, by running:** `NormalizedScale(kind="linear", minimum=0.0, maximum=1.0)` read once,
  then `.model_copy(update={"maximum": 3.0}).span` is still `1.0`, the `cached_property` living in
  `__dict__`, which `model_copy` copies.
- **Finding 10, by running:** on a boolean's scale `fma32(0.5, 1, 0)` is exactly `0.5`, a half, and
  on a scale of two steps `fma32(0.25, 2, 0)` is too; `_round_half_away` gives 1 and `round()` 0.
  The committed map fits every grid point exactly, so the plugin gives 1 there: the docstring's
  "the grid never lands on a half" was false and the rounding's direction matters.
- **Findings 1 and 3, by reading `host.py`:** `measure` writes `raw_value` and runs its `finally`
  restore with no wrapping, under one outer guard, so `_floats(self.state())` parses JSON in the
  environment the plugin left and a refusal escapes as pedalboard's error; `get`, `preset_data`,
  `display_texts`, `name` and `version` are unwrapped too.
- **Finding 9:** `operator.index(True)` is `1`.
- **Finding 12** was declined by the last revision (its Decision 7) and is listed again "for
  completeness".

## Decisions

1. **#2, one `MapMismatchError`** with fields `what` (`"machine"`, `"instrument"` or
   `"vital_version"`), `measured` and `found`, replacing `MachineMismatchError`, which no release
   shipped. Owner: "One error with a what field is the errors standard's shape — fields, not a
   class per case — and it scales to the next provenance check without another class." The map's
   `host` is provenance and not checked: the scales are the plugin's, not pedalboard's. The host
   compares machine, then instrument, then version, where the map is first used.
2. **#12 declined again, #13 fixed.** Owner: "Thirteen is a real redundancy with a test that
   proves the assumption; twelve is still the model holding its invariant." 12: the validator's
   decode is `base/python/models`' "Refusing as the package", and the census runs once per Vital
   version. 13: the host reads the plugin's state once when it loads and holds its containers; an
   integration test holds that a load changes the text and no container.
3. **#4: the integration module skips whole**, in the module-scoped `vital` fixture, naming both
   machines, before the plugin loads. (Owner: "The module skips whole".)
4. **#5: `files.replace_files`** stages every temporary first, then renames each over, putting an
   earlier file back from the bytes read at the start when a later rename fails. Owner: "The
   derived file disagreeing with its source is the one state the generator must never leave, and
   the fix is a few lines in the module that already owns the concern." #11's directory sync
   lands beside it.
5. **#3:** every reach into the plugin is its own guarded call; the Python work in `measure` runs
   between them in the process's own environment. The fake plugin records the rounding mode it is
   entered with, and a test holds that every entry was the original: with one outer guard the
   second entry in a grid sees the mode the first left.
6. **#6, #17:** `span` and a record's displayed ends are computed by module functions under
   `functools.lru_cache`, keyed by the bounds and the curve's constants, so a copy with another
   bound computes afresh and the committed records compute once; the host builds its host-id
   lookup once where the map is resolved.
7. **#16:** `fit_scale` builds the linear scale once and takes its `span`;
   `parameters.displayed_ends` is the one place a record's displayed ends are computed, used by
   `to_preset` and the census.
8. **#15:** `preset.decode_end` holds the `raw_decode` and the `RecursionError` turn, used by
   `_json_section` and `state._object_end`; `host._floats` decodes with the package's `DECODER`.
9. **Steps 2–5:** no visuals; references, product and standards as above.

## The 17 findings

| # | Finding | Outcome |
|---|---|---|
| 1 | pedalboard errors get out of the host unwrapped | Fixed: every reach through `_reached`, the restore too |
| 2 | No Vital version check | Fixed: `MapMismatchError` naming what differs (Decision 1) |
| 3 | Python's float work under the plugin's environment in `measure` | Fixed: each call its own guard (Decision 5) |
| 4 | Integration tests fail instead of skipping off arm64 | Fixed: the module skips by name (Decision 3) |
| 5 | Two files replaced as two steps | Fixed: `replace_files` (Decision 4) |
| 6 | `span` cached in `__dict__` survives `model_copy` | Fixed: computed by bounds (Decision 6) |
| 7 | `MachineMismatchError` not exported | Fixed: `MapMismatchError` is, in its place |
| 8 | `row[key]` can raise `KeyError` in `measure` | Fixed: a row with other keys is `CensusError` |
| 9 | `_whole` accepts `bool` | Fixed: refused by name |
| 10 | `_round_half_away`'s docstring says the grid never lands on a half | Fixed: the docstring, and a test pins the half |
| 11 | `replace_file` never syncs the directory | Fixed, with Decision 4 |
| 12 | The state's JSON decoded more than once | Declined (Decision 2) |
| 13 | `load_state` reads the state on every call | Fixed: the containers read once (Decision 2) |
| 14 | `audio.ndim` compared with `_CHANNELS` | Fixed: `_AXES` |
| 15 | `_object_end` copies `_json_section`; `_floats` uses `json.loads` | Fixed (Decision 8) |
| 16 | `fit_scale` and `_record` copy `span` and the bounds logic | Fixed (Decision 7) |
| 17 | Lookups rebuilt per call, ends recomputed per conversion | Fixed (Decision 6) |

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a; `errors` names findings 1, 8 and 9 (a built-in or a third
  party's error escaping a public method) and shapes finding 2's error, `models` keeps the
  validator finding 12 would have dropped

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `src/` and `tests/` changing under what
  it copies
- `base/process/standards-retrospective` and `base/process/standards-index` — four project
  standards rewritten, one base proposal presented
- `base/process/ownership` — the owner commits; nothing filed carries attribution
- `base/testing/tests` — the fake plugin's entry check is a unit test's; the integration skip is
  by name
- `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file`, `vital/preset-tests` — the
  rules the findings touch

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script under
`scripts/` as git lists them, with no tracked file a `.gitignore` ignores; `uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml` and
`uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set
and `uv.lock`'s pins; and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the
commit in `agent-os/standards/base/.version` — and the three judgment steps are recorded, in this
order: Docs, Version, then the standards retrospective below.

**Results (2026-11-10):** exit 0 on branch
`feature/7-the-host-and-the-parameter-map-load-vital-through-pedalboard-map-all-903-parameters-to-preset-keys-and-pass-cores-contract-tests-as-a-real-instrument`,
`verification/gate-run.txt`, 477 tests in 39 s, the plugin's integration tests among them and not
skipped (451 before this revision).
- **The census regenerates the committed map** byte for byte, and the key list unchanged, with no
  temporary left beside them: run to a scratch directory and compared with `cmp` before the gate.
- **The old behaviour:** `verification/old-behaviour.txt`, this revision's unit tests against `src/`
  at `0fc8152`. Five modules import names new here (`MapMismatchError`, `replace_files`, `_span`
  and `displayed_ends`, `decode_end`) and do not collect against the old code, so their findings'
  tests run only on the new; the three failures that do collect are findings 16, 5 and 7's.
- **The negative harness:** no gate file changed, but `src/` and `tests/` changed under what it
  copies, so it was rerun on the final tree. `verification/gate-negative-tests.txt` ends
  `141 runs, 0 unexpected` and `verification/ci-negative-test.txt` `3 runs, 0 unexpected`.
- **CI's own run** of this revision exists only after the owner's push.

**Docs (step 7):** checked against the shipped files, and each reads true:
- `README.md`: the module list says `files.py` replaces files whole or not at all; the example
  runs as written (checked against an installed preset: the diff empty, `env_1_attack` in
  seconds, a `(2, 48000)` float32 render).
- `src/patchbay_vital/host.py`: the module docstring says the map is refused on another machine or
  plugin, naming what differs; that the containers are read once; that nothing pedalboard raises
  leaves any method; and that each call is its own guard so the Python work between calls runs in
  the process's environment. `__init__`, `_parameter_map`, `load_state`, `render`, `measure`,
  `_whole` and `_moving_key` name what they do and raise.
- `src/patchbay_vital/parameters.py`: `_round_half_away` says the grid lands on a half and why
  the direction matters; `span` and `displayed_ends` say they are kept by their values.
- `src/patchbay_vital/files.py`, `preset.py` (`decode_end`), `state.py` (`_object_end`),
  `census.py` (the module docstring, `fit_scale`) and `errors.py` (the module docstring,
  `MapMismatchError`, `PluginStateError`): each says what this revision made it do.
- `tests/unit/test_host.py` and `tests/integration/test_vital_plugin.py`: their module and
  fixture docstrings say what the fake records and why the module skips.
- `CLAUDE.md` and `agent-os/product/`: unchanged; none names what changed.
- The four project standards: rewritten in the retrospective below.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`,
naming the rename of `MachineMismatchError`. The version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** measured data checked against the native code's version as
   well as the machine, by one error naming what differs (`vital/plugin-state`,
   `vital/parameter-map`, and the base proposal below); each call into native code its own guard,
   held by a fake that records the mode each call found (`vital/plugin-state`); the containers
   read once (`vital/plugin-state`); several files staged, then renamed, an earlier put back
   (`vital/preset-file`); a plugin test skipping where the data was measured elsewhere
   (`vital/preset-tests`, and the base proposal below).
2. **A standard wrong or stale:** `vital/parameter-map` said the map is used on no other machine,
   which left the version unchecked, and described the two outputs as written in order; both
   corrected. The `_round_half_away` docstring, which `vital/parameter-map` did not repeat, said
   the grid never lands on a half; the standard now says it does and why the direction matters.
3. **A deliberate deviation:** none. Finding 12 is declined, not a deviation: `base/python/models`
   is kept.
4. **A pointer moved:** `MachineMismatchError` is `MapMismatchError`; `vital/plugin-state`,
   `CHANGELOG.md` and the base proposal follow. `replace_file` is now `replace_files` of one.

The retrospective's own change set, to commit apart from the fixes:

- `agent-os/standards/vital/plugin-state.md` — the codec's one decoder helper; the containers
  read once; each call its own guard and entered with the process's environment; nothing
  pedalboard raises leaving any reach, a refused restore included; the map refused on another
  machine, instrument or version by one error; a row with other keys refused; a render refusing a
  bool; the module skipping on another machine. Verified against `host.py`, `state.py`,
  `preset.py`, `errors.py`, `tests/unit/test_host.py` and
  `tests/integration/test_vital_plugin.py`, the tests named in each rule.
- `agent-os/standards/vital/parameter-map.md` — the map recording the plugin it measured and used
  with no other; both outputs staged then renamed, the key list put back; `fit_scale`'s one scale
  and ends that make none named; the span kept by its bounds; the grid's half rounded away from
  zero; the displayed ends computed in one place. Verified against `parameters.py`, `census.py`,
  `host.py`, `tests/unit/test_parameters.py` and `tests/unit/test_census.py`, the tests named in
  each rule.
- `agent-os/standards/vital/preset-file.md` — `replace_files`: staged before any rename, the
  directory synced, an earlier file put back; a section nesting too deeply refused through
  `decode_end`. Verified against `files.py`, `preset.py`, `tests/unit/test_files.py` and
  `tests/unit/test_preset.py`.
- `agent-os/standards/vital/preset-tests.md` — a plugin test skips by name where the map was
  measured on another machine. Verified against `tests/integration/test_vital_plugin.py` (the
  `vital` fixture).
- `agent-os/standards/index.yml` — the `vital:` section's four descriptions follow; the `base:`
  section is the sync's and unchanged (gate step 6).

**Which side each rule fell on, and why.** What Vital's plugin, map, file and tests do stayed in
`vital/`. Two rules read true of any adapter with data measured from native code and went
upstream as a revision of the proposal that already covers the machine: the version checked by
the same error, and the installed-code tests skipping where the data was measured elsewhere.

Proposals sent upstream: fromtheoutfit/patchbay-standards#35

### Standards retrospective (proposed, base)

Both approved by the owner, 2026-11-10, with AskUserQuestion.

- `base/python/models.md` or `base/testing/tests.md` — a revision of
  `fromtheoutfit/patchbay-standards#35`: the measured data records the native code's version as
  well as the machine, the host library's version as provenance only, and the adapter refuses the
  data with one error naming the first field that differs, its value in the data and the one
  found. Verified against `src/patchbay_vital/host.py` (`_parameter_map`), `errors.py`
  (`MapMismatchError`), `parameters.py` (`ParameterMap`) and
  `test_the_map_is_refused_on_another_vital_version_where_it_is_first_used`. Proposed, not
  applied; filed by editing #35's body in place with a "Revised 2026-11-10" paragraph and its
  proposal 1 rewritten.
- The same file — #35's new proposal 2: a test of the installed native code skips by name where
  the data was measured elsewhere, a differing version left to fail the regeneration test.
  Verified against `tests/integration/test_vital_plugin.py` (`vital`). Proposed, not applied;
  filed in the same revision of #35.
