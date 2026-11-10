# Revision after the Third Review of PR 9 — Shaping Notes

Shaped 2026-11-10 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered four questions on the findings, then one on finding 1's directory sync and one
confirming steps 2 to 5 together.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The review of PR 9 at `d4fe077` (the fifth comment on
https://github.com/fromtheoutfit/patchbay-vital/pull/9, 2026-11-10 19:26Z, "Review findings:
`main...HEAD`"): 12 findings, unverified when posted, four behaviour, three errors escaping, three
cleanups, two process and docs. Each was checked while shaping against the code at the PR head.
On the same branch, so PR 9 carries it. CHANGELOG entry, gate green, `verification/gate-run.txt`.
No stage, commit or push by an agent. No gate file changes.

## Shaping answers

- **Step 1, scope:** the 12 findings, in the owner's words "address the issues in the latest round
  of review".
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file` and
  `vital/preset-tests`. Snapshot in `standards.md`, base at `e31f7db`.

## What was checked while shaping

- **Findings 1, 2, 5, 6, 7, 10, 12, by reading:** each holds as written. `_rename_each` syncs the
  directory inside the rename's `try`, so a sync failure puts every earlier file back and leaves
  this one replaced; it reads every existing target before its rename; `_floats` indexes
  `["settings"]` unguarded; `set` calls `math.isfinite` first; `display_texts` indexes
  `self._hosted` directly; the integration test's `_floats` decodes with `json.loads`, the host's
  with `DECODER`; `CHANGELOG.md` line 66 is blank inside the list and line 65 runs past 100
  columns.
- **Finding 4, by reading:** `ParameterMap.settings_keys` is the current map's keys and
  `PRESET_ONLY_KEYS`, so a census on a Vital that dropped a parameter would write a list without
  its key, and `load()` of a preset holding it would raise `UnknownSettingError`.
- **Finding 3, by running** (`verification/restore-probe.txt`, read-only, on the installed Vital):
  the reviewer's fix, each parameter put back by its raw value, restores 881 of 903 exactly and
  leaves 22 a float32 step off (`env_1_decay_power` -2.0 read back -2.0000005,
  `chorus_feedback`, `compressor_*_lower_ratio`, `osc_*_detune_power`, `reverb_high_shelf_gain`
  among them). `measure` as reviewed takes 20.9 s; the raw-value put-back with one load of the
  start at the end 14.4 s, every float the start's afterwards.
- **Finding 8** was declined by both earlier revisions and is listed again "for completeness".
- **Finding 9, by reading pedalboard:** `plugin.parameters` is Python
  (`pedalboard/_pedalboard.py`, `AudioProcessorParameter.__init__`, lines 284-330) that steps
  `x / search_steps` and parses texts between its native calls, so there is Python work inside the
  second of the four calls; `test_every_call_into_the_plugin_is_entered_in_the_process_s_own_environment`
  holds all four of the load's calls entered in the process's own environment.
- **Finding 11, by `git show --stat`:** `1fb324f`, `eb95567` and `d4fe077` each carry
  `agent-os/standards/vital/*.md` and `index.yml` beside `src/patchbay_vital/*.py`; `0fc8152`
  carries the standards alone.

## Decisions

1. **#3: put back by raw value, then one load.** Each parameter is set back to the normalized
   value it had after its grid, and the state measured from is loaded once at the end, however the
   loop ends: 903 loads become 1, every float comes back exact, and the one load still delays the
   embedded sample by 4 samples, which the docstring says. (Owner: "Raw value, then one load".)
2. **#4: the census refuses to forget a known key.** `census.key_list` is `CensusError`, naming
   the keys, when the map's list lacks a key `preset.KNOWN_SETTINGS` holds, and says to add them to
   `PRESET_ONLY_KEYS` in a spec; the list stays exactly derived and its equality test stays.
   (Owner: "Refuse, naming keys".) The reviewer's union was not taken: the list would stop being
   derivable from the map and a wrong key could never leave.
3. **#8 declined a third time, #9 declined.** 8: the validator's decode is
   `base/python/models`' "Refusing as the package", and the census runs once per Vital version.
   9: one guard around the load's four calls would enter pedalboard's Python `parameters` in the
   flush-to-zero `VST3Plugin` left; every call stays its own guard. (Owner: "Decline both".)
4. **#11: history left as it is.** Owner: "It's fine - leave it. I'll start splitting them going
   forward." This revision lists its retrospective edits apart from the fixes.
5. **#1: renamed first, then each directory synced once, best effort.** Owner: "Suppress all
   OSErrors there (the contract holds: once renamed, nothing can fail), but log a warning through
   the module's logger naming the directory and errno for any error other than the unsupported
   family (EINVAL, ENOTSUP, EBADF). "Replaced, maybe not durable" is a degraded result, and
   degraded is reported, not raised and not silent." ENOTSUP and EOPNOTSUPP are 45 and 102 on
   macOS and one value on Linux, so the family holds both. The package logged nothing before: a
   new pattern, for the retrospective.
6. **#2: only a file a later rename could force back is read,** during staging, before any
   rename: `replace_file`, and so `dump`, reads nothing.
7. **#5, #6, #7:** a state with no `settings` object is `PluginStateError`; a normalized value
   that is no number, or a bool, is `ParameterRangeError`, the `TypeError` chained, in the shape
   of `_whole`; a host id not hosted is `UnknownParameterError`, core's field a plain `str`.
8. **Steps 2–5:** no visuals; references, product and standards as above.

## The 12 findings

| # | Finding | Outcome |
|---|---|---|
| 1 | A directory sync failing after a rename is handled as a failed rename | Fixed: renames first, each directory synced once after, best effort, a warning outside the unsupported family (Decision 5) |
| 2 | `dump` needs read permission; every target read whole | Fixed: only a file a later rename could force back is read (Decision 6) |
| 3 | `measure` reloads the whole state after every parameter | Fixed: put back by raw value, one load at the end (Decision 1) |
| 4 | `settings_keys()` rebuilt from the current version only | Fixed: the census refuses to forget a known key (Decision 2) |
| 5 | `_floats` lets `KeyError` escape | Fixed: `PluginStateError` (Decision 7) |
| 6 | `set` lets `TypeError` escape | Fixed: `ParameterRangeError`, a bool refused too (Decision 7) |
| 7 | `display_texts` lets `KeyError` escape | Fixed: `UnknownParameterError` (Decision 7) |
| 8 | The state's JSON decoded three times per read | Declined a third time (Decision 3) |
| 9 | Four guards back to back in `__init__` | Declined (Decision 3) |
| 10 | The integration test copies `_floats` | Fixed: the host's imported |
| 11 | Standards edits mixed into feature commits | Acknowledged; history left (Decision 4) |
| 12 | A blank line and a long line in `CHANGELOG.md` | Fixed |

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a; `errors` names findings 5, 6 and 7 (a built-in escaping a public
  method), `models` keeps the validator finding 8 would have dropped

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `src/` and `tests/` changing under what
  it copies
- `base/process/standards-retrospective` and `base/process/standards-index` — project standards
  rewritten, base proposals presented
- `base/process/ownership` — the owner commits (finding 11); nothing filed carries attribution
- `base/testing/tests` — the fake plugin's twin and bare state are unit tests'; the probe is a
  measured third party's record
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
`verification/gate-run.txt`, 490 tests in 33 s, the plugin's integration tests among them and not
skipped (477 in 39 s before this revision, the census's `measure` now 14.4 s where it was 20.9).
- **The census regenerates the committed map** and the key list byte for byte, with no temporary
  left beside them: run to a scratch directory (`--parameters` and `--settings-keys` there, 18 s)
  and compared with `cmp` before the gate.
- **The old behaviour:** `verification/old-behaviour.txt`, this revision's unit tests against
  `src/` at `d4fe077`, from a `git archive` in the scratchpad with this revision's `tests/` over it,
  the working tree untouched: 12 failed, 355 passed, 1 error. Each failure is a finding's test,
  named in the file's header (findings 1, 2, 3, 5, 6, 7); `tests/unit/test_census.py` imports
  `key_list`, new here, and does not collect, so finding 4's tests run only on the new code.
- **The negative harness:** no gate file changed, but `src/`, `tests/` and the standards changed
  under what it copies, so it was rerun on the final tree, after the retrospective's edits.
  `verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
  `verification/ci-negative-test.txt` `3 runs, 0 unexpected`.
- **CI's own run** of this revision exists only after the owner's push.

**Docs (step 7):** checked against the shipped files, and each reads true:
- `README.md`: `settings_keys.txt` "lists every float key Vital has been seen to write, derived
  from the map", and `files.py` "replaces files whole or not at all": both still true; the example
  uses nothing this revision changed.
- `src/patchbay_vital/files.py`: the module docstring says only an earlier target is read, an
  earlier one must be readable to be put back, and each directory is flushed once after every
  rename as a best effort, a failure outside `_UNSUPPORTED` logged as a warning and never raised;
  `replace_file`, `_held`, `_rename_each` and `_sync_directory` say what they do.
- `src/patchbay_vital/host.py`: `measure` says each parameter is put back by its normalized value,
  that this is a float32 step off on 22 of 903, and that one load at the end puts those right and
  delays the sample; `_floats`, `set`, `_normalized` and `display_texts` name what they refuse
  and as what. The module docstring's claims (each call its own guard, nothing pedalboard raises
  let out, the state's load delaying the sample) still hold.
- `src/patchbay_vital/census.py` (the module docstring, `key_list`), `parameters.py` (the module
  docstring, `PRESET_ONLY_KEYS`), `preset.py` (the module docstring on known keys) and `errors.py`
  (`UnknownParameterError`, which now names a host id not hosted): each says what this revision
  made it do.
- `tests/unit/test_files.py`, `test_host.py`, `test_census.py` and
  `tests/integration/test_vital_plugin.py`: their module docstrings say what the new tests and the
  fake's additions hold.
- `CHANGELOG.md` (finding 12): the blank line inside `### Changed` is gone and the error-root item
  is wrapped to 100 columns. Four older lines at 101 columns sit in entries already on `main` and
  were left.
- `CLAUDE.md` and `agent-os/product/`: unchanged; none names what changed.
- The three project standards: rewritten in the retrospective below.

**Version (step 8):** this spec's entry at the top of `### Changed` in `[Unreleased]`,
`CHANGELOG.md`. The version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** a degraded result, the files replaced but a directory not
   flushed, logged as a warning through the module's logger, neither raised nor silent, the
   package's first logging (`vital/preset-file`, and the base proposal below); a generator that
   refuses to forget an entry older inputs hold rather than keep a union (`vital/parameter-map`,
   `vital/preset-file`, and the base proposal below); a measurement that puts each parameter back
   by its value and restores the whole state once (`vital/plugin-state`).
2. **A standard wrong or stale:** `vital/plugin-state` said a measurement puts the starting state
   back after each parameter's grid, and is rewritten for the put-back and the one load;
   `vital/preset-file` said `replace_files` flushes the directory after each rename, which made a
   flush's failure a failed rename, and now says each directory is flushed once after every
   rename, as a best effort, and that only an earlier target is read.
3. **A deliberate deviation:** none. Findings 8 and 9 are declined, not deviations:
   `base/python/models` is kept, and `vital/plugin-state` now gives the load's four guards their
   reason.
4. **A pointer moved:** `test_the_directory_is_synced_after_the_rename` is
   `test_every_directory_is_synced_once_after_every_rename`; `vital/preset-file` follows.

The retrospective's own change set, to commit apart from the fixes (Decision 4):

- `agent-os/standards/vital/plugin-state.md` — the header names this revision's evidence; the
  load's four calls are four guards, with pedalboard's Python `parameters` the reason; no
  built-in's error leaves the host, a non-number, an id not hosted and a state with no settings
  object each named; a measurement puts each parameter back and loads the starting state once,
  with the probe's 22 and its timing. Verified against `host.py` (`__init__`, `_normalized`,
  `display_texts`, `_floats`, `measure`), pedalboard 0.9.26's `AudioProcessorParameter.__init__`,
  `verification/restore-probe.txt` and the tests named in each rule.
- `agent-os/standards/vital/parameter-map.md` — the header names this revision; the key list is
  derived and the census never forgets a key, refusing by name, a spec keeping the key in
  `PRESET_ONLY_KEYS`. Verified against `census.py` (`key_list`, `main`), `parameters.py` and the
  three tests named.
- `agent-os/standards/vital/preset-file.md` — the header names this revision; a key a newer Vital
  drops stays known; `replace_files` reads only an earlier target and flushes each directory once
  after every rename, as a best effort that warns outside the unsupported family. Verified against
  `files.py`, `format.py` (`dump`) and `tests/unit/test_files.py`, the tests named.
- `agent-os/standards/index.yml` — the `vital:` section's `parameter-map`, `plugin-state` and
  `preset-file` descriptions follow; the `base:` section is the sync's and unchanged (gate step 6).

**Which side each rule fell on, and why.** What Vital's files, map and host do stayed in `vital/`.
Two rules read true of any package: a degraded result logged and never raised or silent, and a
regeneration of measured data never forgetting an entry that inputs in the wild still hold. Both
went upstream.

Proposals sent upstream: fromtheoutfit/patchbay-standards#36

### Standards retrospective (proposed, base)

Both approved by the owner, 2026-11-10, with AskUserQuestion.

- `base/python/errors.md`, "What escapes" — a degraded result is logged at `WARNING` through the
  module's `logging.getLogger(__name__)`, naming what and why, never raised and never silent, the
  library configuring no handler, and a failure that only means the platform cannot do the step
  passed over. Verified against `src/patchbay_vital/files.py` (`_sync_directory`, `_UNSUPPORTED`)
  and `test_a_directory_that_cannot_be_synced_leaves_every_file_replaced`. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#36.
- `base/testing/tests.md`, "Measured third parties" (or `base/python/models.md`) — a regeneration
  of measured data never forgets an entry inputs in the wild hold: the generator refuses, naming
  the entries, and a spec keeps them in a hand-held list, the data staying derived. Verified
  against `src/patchbay_vital/census.py` (`key_list`) and
  `test_a_key_list_that_would_forget_a_known_key_is_refused_and_nothing_written`. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#36.
