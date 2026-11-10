# Revision after the third review of PR 9

## Context

The latest review comment on https://github.com/fromtheoutfit/patchbay-vital/pull/9 (2026-11-10
19:26Z, "Review findings: `main...HEAD`", at `d4fe077`) lists 12 unverified findings. Each was
checked while shaping against the code at the PR head:

- **Hold as written:** 1 (`files.py:61`, a directory-sync failure after a successful rename is
  handled as a failed rename), 2 (`files.py:59`, every target read in full before its rename),
  4 (`ParameterMap.settings_keys` built from the current version alone), 5 (`host._floats`
  indexes `["settings"]` unguarded), 6 (`set` calls `math.isfinite` before any type check),
  7 (`display_texts` indexes `self._hosted[host_id]` directly), 10 (the integration test's
  `_floats` copies the host's, with `json.loads` where the host uses `DECODER`), 11 (1fb324f,
  eb95567, d4fe077 each carry `agent-os/standards/vital/*.md` and `index.yml` beside `src/`),
  12 (`CHANGELOG.md:66` blank line splits the list; line 65 runs past 100 columns).
- **3 holds, but the suggested fix is inexact. Probed on the installed Vital (read-only):**
  putting each parameter back by its raw value restores 881 of 903 exactly and leaves 22 a
  float32 step off (`env_1_decay_power` -2.0 → -2.0000005; `chorus_feedback`,
  `compressor_*_ratio` and others). Timing: today's `measure` takes 20.6 s. A raw-value put-back
  with one load at the end takes 14.4 s, with every float equal to the start's afterwards.
- **8** was declined in both earlier rounds and is listed "for completeness".
- **9's premise doesn't hold:** pedalboard's `parameters` is Python that does float work
  between its native calls (`.venv/.../pedalboard/_pedalboard.py:284-330`,
  `AudioProcessorParameter.__init__` steps `x / search_steps` and parses texts). One guard would
  start it under the flush-to-zero the load left.
  `test_every_call_into_the_plugin_is_entered_in_the_process_s_own_environment` holds all four of
  the load's calls.

This revision lands on PR 9's branch so PR 9 carries it. No gate file changes. No stage,
commit or push by an agent.

## Decisions (owner, 2026-11-10, AskUserQuestion)

1. **#3:** put each parameter back by its raw value after its grid, then load the starting
   state once at the end, however the loop ends. 903 loads become 1. That one load still delays
   the sample by 4 samples, and the docstring says so.
2. **#4:** the census refuses (`CensusError`) to write a key list that lacks a key the format
   knows now (`preset.KNOWN_SETTINGS`). The error names those keys and says to add them to
   `PRESET_ONLY_KEYS` in a spec. The list stays exactly derived, and its equality test stays.
3. **#8 declined again** (the validator's decode is `base/python/models`' "Refusing as the
   package"). **#9 declined** (the reason above; the one-guard-per-call rule and its test hold).
4. **#11:** history is left as it is. From here on, the owner commits standards edits on their
   own. This revision lists its retrospective edits separately.
5. **#1:** rename every file first, then sync each directory once. Every `OSError` from the sync
   is suppressed, so once the files are renamed nothing can fail. **An error outside the
   unsupported family (EINVAL, ENOTSUP/EOPNOTSUPP, EBADF) is logged as a warning through the
   module's logger, naming the directory and the errno.** In the owner's words, "Replaced, maybe
   not durable" is a degraded result, "reported, not raised and not silent". (ENOTSUP and
   EOPNOTSUPP are 45 and 102 on macOS but equal on Linux, so both are in the family.) This is
   a new pattern: the package logs nothing today and no standard covers logging. The
   retrospective writes it into `vital/preset-file` and likely proposes it to
   `base/python/errors`.
6. Steps 2–5: no visuals. References as below. The mission is unchanged. Standards: the core
   five, plus `process/verification-gate`, `process/standards-retrospective`,
   `process/standards-index`, `process/ownership`, `testing/tests`, `vital/plugin-state`,
   `vital/parameter-map`, `vital/preset-file` and `vital/preset-tests` (base at `e31f7db`).

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`. Use the previous
revision's folder (`2026-11-10-1307-revision-after-pr-9-second-review/`) as the model for each
file's shape.

- **plan.md**: this plan.
- **shape.md**: scope, shaping answers, what was checked, the decisions above, a 12-row table
  of findings and outcomes, then the Standards Applied, Verification Gate and Standards
  Retrospective sections, the last two filled at the end.
- **standards.md**: the full text of each confirmed standard as it reads now.
- **references.md**:
  - `files.py` with `tests/unit/test_files.py`;
  - the fake plugin and `fake` fixture in `tests/unit/test_host.py`;
  - `tests/unit/test_census.py` (`_FakeHost`, `_main`);
  - `host._whole`, the try/`TypeError` pattern #6 mirrors;
  - pedalboard's `AudioProcessorParameter.__init__`, #9's reason;
  - the previous revision's folder;
  - the review comment.
- **verification/restore-probe.txt**: rerun the two read-only probes from shaping and save the
  output with the scripts as header comments. The first sets each parameter over `census.GRID`,
  puts back its raw value and diffs the state's floats (22 inexact). The second times today's
  `measure` against the raw-value put-back plus one load.

## Task 2: `src/patchbay_vital/files.py` (findings 1, 2; Decision 5)

- **Read only what may need putting back.** Read the bytes of every target except the last,
  during staging, before any rename. A read that fails then leaves every file as it was. The
  last file can never be forced back, so `replace_file` and `dump` read nothing.
- **`_rename_each(staged, held)`** counts the renames done. On an `OSError`, put back
  `staged[:done]` from `held[:done]` (`zip(..., strict=True)`), then re-raise. Keep `_put_back`
  as it is.
- **Sync after every rename.** Once every rename is done, sync each distinct parent directory
  once, in order (`dict.fromkeys`), through `_sync_directory`. It becomes best effort: catch
  `OSError`, and when `error.errno` is not in `_UNSUPPORTED`, warn through
  `_LOG = logging.getLogger(__name__)` with %-style arguments (ruff `G`). The warning names the
  directory and the errno's name (`errno.errorcode`).
- Module and function docstrings say each of these, and that an earlier target must be readable
  to be put back.
- **Tests** (`tests/unit/test_files.py`):
  - A directory sync failing leaves every file replaced with no exception. Parametrize EINVAL
    (no log record) against EIO (one WARNING from `patchbay_vital.files` naming the directory and
    `EIO`, via `caplog`). Skip on `nt`.
  - Rewrite `test_the_directory_is_synced_after_the_rename` as "every directory is synced once,
    after every rename": record fsyncs and renames for two files in one directory; the order is
    file, file, rename, rename, directory.
  - Only a file that a later rename could force back is read. Monkeypatch `Path.read_bytes` to
    record: `replace_file` reads nothing; `replace_files` of three files reads the first two.
  - A write-only target (`0o200`) is replaced and keeps its mode. Skip on `nt` or as root.

## Task 3: `src/patchbay_vital/host.py` (findings 3, 5, 6, 7; 9 unchanged)

- **`measure`:**
  - Read `start` and `defaults` before an outer `try`. Its `finally` loads `start` once through
    `_reached(PluginStateError)`.
  - For each parameter, read `original = hosted.raw_value` (guarded) before its grid. The inner
    `finally` sets it back (guarded).
  - Rewrite the docstring to cover the put-back by normalized value, that this is a float32 step
    off on 22 of 903 at the census, which the one load at the end puts right, and that the load
    delays the embedded sample by 4 samples, as every load does.
- **`_floats`:** decode, then `PluginStateError("the state holds no settings object")` when
  `settings` is not a dict. The text is already one JSON object by `PluginState`'s validator, so
  the decode itself cannot fail (say so in the docstring). `census.main` then reports
  `census: plugin state: ...` and exits 1.
- **`set`:** refuse first, in the shape of `_whole`:
  - a bool is `ParameterRangeError`;
  - `math.isfinite` inside `try`, its `TypeError` turned into `ParameterRangeError(parameter_id,
    0.0, 1.0, normalized)`, chained;
  - then the range check, and pass `float(normalized)` to the plugin.
  - The docstring names a non-number and a bool.
- **`display_texts`:** a host id not hosted is `UnknownParameterError(host_id, INSTRUMENT)`
  `from None` (core's field is a plain `str`).
- **`__init__`'s four guards stay**, for #9's reason.
- **Tests** (`tests/unit/test_host.py`):
  - Add a `twinned` switch to `_FakePlugin`: a second host id bound to the same value.
    `test_a_measurement_puts_each_parameter_back_and_loads_the_state_once` checks that two
    parameters measured mean one `set_preset_data`, as the last call, and the value is `_START`.
  - Add `bare_at` and its text to the fake: a valid wrapper whose text is `{}` or
    `{"settings":[]}`. Parametrized, `measure` raises `PluginStateError` and the value is
    restored.
  - `set` with `"0.5"`, `None` and `True` raises `ParameterRangeError`, and `set_raw_value` is
    never called. `np.float32(0.5)` is set as `0.5`.
  - `display_texts("no_such_parameter", [0.0])` raises `UnknownParameterError` with that
    `parameter_id` and instrument `"Vital"`.
  - The existing restore, refusal and entry-mode tests must still pass unchanged.

## Task 4: the key list (finding 4; Decision 2)

- **`census.py`:** add `key_list(parameter_map) -> tuple[PresetKey, ...]`. It returns
  `parameter_map.settings_keys()`. When `KNOWN_SETTINGS` (imported from `preset`) holds a key
  that list lacks, it raises `CensusError("the key list", ...)` naming up to four of the
  missing keys and saying to add them to `PRESET_ONLY_KEYS` in a spec. Call it inside `main`'s
  `try`, beside `build_map`. Update the module docstring.
- **`parameters.py`:** `PRESET_ONLY_KEYS`' docstring adds that it holds any key a newer Vital
  drops, added when the census names it. The module docstring's line on deriving
  `settings_keys.txt` follows.
- **`preset.py`:** the module docstring on known keys follows.
- **Tests** (`tests/unit/test_census.py`):
  - With `census.KNOWN_SETTINGS` patched to include an extra key, `key_list(parameter_map())`
    raises `CensusError` naming it and `PRESET_ONLY_KEYS`, and `main` exits 1 with neither file
    written.
  - Unpatched, `key_list(parameter_map()) == parameter_map().settings_keys()`.
  - The existing `main` tests that use a one-parameter `_FakeHost` patch `census.KNOWN_SETTINGS`
    to that fake's keys (`chorus_damping`, `filter_1_cutoff`).

## Task 5: `tests/integration/test_vital_plugin.py` (finding 10)

Delete the local `_floats` and import `_floats` from `patchbay_vital.host`, as the unit tests
already import its private helpers. `json` stays for `_samples` and the routing test.

## Task 6: `CHANGELOG.md` (finding 12, and Version)

- Remove the blank line after the error-root item and rewrap lines 63–65 to 100 columns.
- Add this revision's entry at the top of `### Changed`: 12 findings at `d4fe077`, nine
  addressed, two declined with reasons (8, 9), and one acknowledged (11). The version stays
  0.0.1. Sub-items cover the files module, the host's `measure` and refusals, the census's
  key-list refusal, and the integration test using the host's helper.

## Task 7 (FINAL): Verification gate

1–6. Run `scripts/gate.sh` and save the output as `verification/gate-run.txt`. It must exit 0
     with the integration tests running, not skipped.

Then check what the gate does not:

- **Census regeneration:** run
  `uv run --locked python -m patchbay_vital.census --parameters <scratch>/parameters.json
  --settings-keys <scratch>/settings_keys.txt`, then `cmp` both outputs with the committed
  `src/patchbay_vital/data/parameters.json` and `settings_keys.txt`. They must match byte for
  byte, with no temporary left.
- **Old behaviour** (`verification/old-behaviour.txt`): run this revision's unit tests against
  `d4fe077` without touching the working tree. `git archive d4fe077 | tar -x` into the
  scratchpad, copy the new `tests/` over it, then run
  `PYTHONPATH=<scratch>/src .venv/bin/python -m pytest -c pyproject.toml -p no:doctest tests/unit
  -q --continue-on-collection-errors` from there. Name each failure's finding, and note the
  modules that don't collect (`key_list` is new).
- **Negative harness:** `src/` and `tests/` changed under what it copies, so rerun
  `scripts/gate-negative-tests.sh` (and the CI case) on the final tree. Save them as
  `verification/gate-negative-tests.txt` and `verification/ci-negative-test.txt`, each ending
  with 0 unexpected.

Then the three judgment steps, recorded in `shape.md`:

7. **Docs:** check that these read true:
   - `README.md` (the `files.py` line and the example);
   - the module, function and test docstrings changed;
   - the `files` and `host` docstrings' claims about restore, sync and errors;
   - `CLAUDE.md` and `agent-os/product/` (expected unchanged).
8. **Version:** the `[Unreleased]` entry; 0.0.1 kept.
9. **Standards retrospective,** from the shipped diff:
   - Expected project edits:
     - `vital/preset-file`: only earlier targets read; directories synced once after every
       rename, best effort, with a warning outside the unsupported family; the known-key rule
       for a dropped key.
     - `vital/plugin-state`: `measure`'s put-back and one load, with the probe's 22; a state with
       no settings object refused; `set` refusing a non-number or bool; `display_texts`' unknown
       id.
     - `vital/parameter-map`: the census refusing a list that forgets a known key, and
       `PRESET_ONLY_KEYS` holding dropped keys.
     - `index.yml`'s `vital:` descriptions follow.
   - Likely base proposals, presented with AskUserQuestion before the spec is done:
     - `base/python/errors`: "a degraded result is logged at WARNING through the module's logger,
       never raised and never silent; the library configures no handler";
     - possibly a generator refusing to shrink a derived list.
   - File the approved proposals as one `fromtheoutfit/patchbay-standards` issue with no
     attribution, and record `Proposals sent upstream:`.
   - List the retrospective's edits separately from the fixes, so the owner can commit them on
     their own (Decision 4).

If any step fails, fix the cause and rerun. The spec is not done until the gate is green and
Docs, Version and the retrospective are recorded.
