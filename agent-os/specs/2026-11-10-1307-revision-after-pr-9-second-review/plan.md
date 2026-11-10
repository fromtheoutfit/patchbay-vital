# Revision after the second review of PR 9

## Context

The owner's second review of PR 9, at `0fc8152` (the third comment on
https://github.com/fromtheoutfit/patchbay-vital/pull/9, 2026-11-10 18:02Z), lists 17 findings: four most serious, seven correctness, six speed and
duplication. Each was checked against the code at the PR head; all hold, two by running:

- #6: `NormalizedScale(...).model_copy(update={"maximum": 3.0}).span` is still the old span,
  `cached_property` living in `__dict__`, which `model_copy` copies.
- #10: on every boolean the grid's 0.5 is exactly `fma32(0.5, 1, 0) = 0.5`, a half; the plugin
  gives 1 there (the committed map fits every grid point exactly) and `round()` would give 0. The
  docstring's "the grid never lands on a half" is false.
- #1, #3: `measure` sets `raw_value` and the `finally` restore with no wrapping, under one outer
  guard, so Python's JSON parsing runs in the plugin's environment and a refusal escapes as
  pedalboard's error; `get`, `preset_data`, `display_texts`, `name`, `version` are unwrapped too.
- #12 was declined by the last revision and is listed again "for completeness".

This revision closes them on PR 9's branch so PR 9 carries it. No gate file changes.

## Decisions (owner, 2026-11-10)

1. **#2, one `MapMismatchError`** with fields `what` (`"machine"`, `"instrument"` or
   `"vital_version"`), `measured`, `found`, replacing `MachineMismatchError`, which no release
   shipped: "fields, not a class per case" (`base/python/errors`). The map's `host` is provenance
   and not checked: the scales are the plugin's, not pedalboard's. The host compares machine, then
   instrument, then version, where the map is first used.
2. **#12 declined again, #13 fixed.** 12: the validator's decode is the model holding its own
   invariant; the census runs once per Vital version. 13: the host reads the plugin's state once
   when it loads and holds its containers; an integration test holds that a load changes the text
   and no container.
3. **#4: the integration module skips whole** in the module-scoped `vital` fixture, naming both
   machines, before the plugin loads.
4. **#5: `files.replace_files`** stages every temporary first, then renames each over, putting an
   earlier file back from the bytes read at the start when a later rename fails; #11's directory
   sync lands beside it.
5. **#3:** every reach into the plugin is its own guarded call; Python work in `measure` runs
   between them in the process's own environment. The fake plugin records the rounding mode it is
   entered with, and a test holds that every entry was the original.
6. **#6, #17:** `span` and a record's displayed ends are computed by module functions under
   `functools.lru_cache`, keyed by the bounds and the curve's constants, so a copy with another
   bound computes afresh and the committed records compute once; the host builds its host-id
   lookup once where the map is resolved.
7. **#16:** `fit_scale` builds the linear scale once and takes its `span`; `parameters.displayed_ends`
   is the one place a record's displayed ends are computed, used by `to_preset` and the census.
8. **#15:** `preset.decode_end` holds the `raw_decode` and the `RecursionError` turn, used by
   `_json_section` and `state._object_end`; `host._floats` decodes with the package's `DECODER`.
9. Steps 2–5: no visuals; references, product and standards as Task 1.

## Tasks

### Task 1: Save spec documentation

`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`:
- `plan.md`: this plan.
- `shape.md`: scope (the 17 findings, the probes above), Decisions 1–9, a table of the 17 findings
  and each outcome (as the last revision's), standards applied, the gate section, retrospective
  with this revision's edits listed apart.
- `standards.md`: snapshot of the core five plus `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file`,
  `vital/preset-tests`; base at `e31f7db`, project standards at `0fc8152`.
- `references.md`: the last revision's folder (`2026-11-10-1027-revision-after-pr-9-review/`:
  the shape of a review revision, `old-behaviour.txt`); `preset._json_section` and
  `state._object_end`; `files.replace_file`; `tests/unit/test_host.py`'s `_FakePlugin`.

### Task 2: `errors.py` and the package root (#2, #7)

- `MapMismatchError(VitalHostError)`: `__init__(what: str, measured: str, found: str)`, the three
  kept as attributes, `__str__` `f"the map's {what} is {measured!r}, here {found!r}"`. Docstring:
  the map is the plugin's build's and version's. `MachineMismatchError` is gone (never released).
- `__init__.py`: import and list `MapMismatchError` in `__all__`; `tests/unit/test_package.py`'s
  surface tuple gains it; `test_errors.py`'s `_ERRORS` holds `MapMismatchError("machine", "arm64",
  "x86_64")` in `MachineMismatchError`'s slot, its message and fields tested.

### Task 3: `host.py` (#1, #2, #3, #8, #9, #13, #14, #15, #17)

- `_reached(error)`: a context manager over `_environment_kept()` that raises
  `error(str(raised) or type(raised).__name__)` from any of `_PEDALBOARD_ERRORS`. Every reach
  into the plugin after the load goes through it: `name`, `version`, `get`, `set`, `preset_data`,
  `load_state`'s write, `display_texts`, `unmapped_parameters`, and in `measure` the `name` read,
  each `raw_value` write and the restore, all `PluginStateError`; `render` `PluginRenderError`.
  `PluginStateError`'s docstring: "or the plugin refused a read or a write".
- `measure`: no outer guard. Per parameter: guarded name read; `try:` for each point a guarded
  write, then `rows.append(_floats(self.state()))` outside any guard; `finally:` a guarded restore.
  A row whose float keys are not `defaults`' is `CensusError(label, "changes the preset's keys at a
  grid point: <symmetric difference, first four>")` before `moving` is computed (#8).
- `__init__` reads `preset_data` inside the load's guard and holds `self._containers =
  unwrap(data)`; a state the codec cannot read is `PluginLoadError(path, "its state is not one this
  package reads: <reason>")`, chained. `load_state` wraps `self._containers.with_text(...)` and
  reads nothing first (#13). Docstring: the containers are read once; a test holds they never
  change.
- `_parameter_map`: compares `(machine, found.machine, platform.machine())`, `(instrument,
  found.instrument, self.name)`, `(vital_version, found.vital_version, self.version)` in that
  order, raising `MapMismatchError` on the first difference; on success also builds
  `self._by_host: dict[str, ParameterId]` once. `parameter_ids` and `unmapped_parameters` use it
  (#17).
- `_whole` refuses `bool` by name before `operator.index` (#9).
- `_AXES = 2` ("a render is channels by samples"); the shape check is `audio.ndim != _AXES or
  audio.shape[0] != _CHANNELS or audio.shape[1] < samples` (#14).
- `_floats` decodes with `preset.DECODER` (#15).
- Module docstring: errors from every reach, the containers read once, the map refused on another
  machine or Vital version, each call its own guard so Python work runs in the process's
  environment.

### Task 4: `parameters.py` and `census.py` (#6, #10, #16, #17)

- `_span(minimum, maximum)` and `_displayed_ends(kind, multiply, offset, minimum, maximum)` are
  module functions under `functools.lru_cache(maxsize=4096)`; `NormalizedScale.span` is a plain
  property over the first, `displayed_ends(curve, scale) -> tuple[float, float]` (public, sorted)
  over the second. `to_preset` uses `displayed_ends(self.curve, self.scale)`.
- `_round_half_away` docstring: the grid lands on a half, 0.5 on every boolean and 0.25 on a scale
  of two steps; the plugin takes it away from zero, which the committed map's exact fit shows;
  `round`, a half to even, would give 0.
- `census.fit_scale`: builds the linear scale once (`PatchbayValidationError` is
  `CensusError(label, "its ends make no scale: ...")`, chained), the indexed one only when both
  ends are whole; the refusal's `plain` is `linear.to_preset(point)`, no second span. `_record`'s
  `ends` is `displayed_ends(curve, scale)`.

### Task 5: `files.py`, `preset.py`, `state.py` (#5, #11, #15)

- `files.replace_files(files: Mapping[Path, bytes]) -> None`: for each, resolve, write the
  temporary beside it, flush, fsync, copy the mode; then for each, read the target's bytes if it
  exists, rename the temporary over it, fsync the directory (`os.open(parent, O_RDONLY)` +
  `os.fsync`, skipped on Windows, which cannot open a directory); a rename failing after an earlier
  one succeeded writes each earlier file back from its bytes (a temporary and rename again) and
  re-raises; every temporary is unlinked in `finally`. `replace_file(path, raw)` is
  `replace_files({path: raw})`. Docstring updated. `census.main` calls `replace_files` with both.
- `preset.decode_end(text: str, what: str) -> int`: `DECODER.raw_decode`, `RecursionError` turned
  into `ValueError(f"{what} nests too deeply to read")`. `_json_section` and `state._object_end`
  call it, keeping their own first-byte and end checks and messages.

### Task 6: `tests/integration/test_vital_plugin.py` (#4, #13)

- `vital` fixture: after the path check, `parameter_map().machine != platform.machine()` skips
  with "the map was measured on 'arm64', this is 'x86_64'".
- `test_every_installed_preset_loads_as_state` and
  `test_the_fixture_as_state_reads_back_but_its_sample_delayed`: `first =
  unwrap(host.preset_data())` before the load, and after it
  `unwrap(host.preset_data()).with_text(first.text) == first`: a load changes the text and no
  container (Decision 2's proof).
- `test_the_census_regenerates_the_committed_map` keeps asserting name and version; the map's
  `machine` is now the fixture's precondition.

### Task 7: Unit tests

- `test_host.py`: `_FakePlugin.touch` records `self.entered.append(self.library.fegetround())`
  before setting upward; fake gains `missing_at: float | None` (preset_data omits the key there)
  and `version_text` (default "1.6.4"). New tests: every reach refusing is `PluginStateError`
  chained (parametrized over `name`, `version`, `raw_value`, `preset_data`, `text`,
  `set_raw_value` in `measure`); a restore refused in `measure` is `PluginStateError` with the
  grid's failure as its `__context__` and `calls[-1] == "set_preset_data"`; every plugin call is
  entered in the process's own environment across `measure` (entered all `== original`);
  a key missing from a grid row is `CensusError` naming the parameter; `render([], True, True)`
  refused, `process` not called; the map refused on another Vital version from `get`, not from
  `VitalHost()` nor `measure`, `what == "vital_version"`; the machine test asserts `what ==
  "machine"`; `load_state` reads `preset_data` no more than at load (`"preset_data"` count in
  `calls` unchanged by a load); a load whose state the codec cannot read is `PluginLoadError`
  naming the path.
- `test_parameters.py`: `test_a_scale_s_span_is_computed_once` becomes: a copy with another
  maximum has the new span, and `_span.cache_info().hits` grows on a second read; a half on an
  indexed scale goes away from zero (boolean at 0.5 → 1.0, a -1..0 scale at 0.5 → -1.0);
  `displayed_ends` is sorted and equals what `to_preset` bounds by; `MapMismatchError` where the
  committed map is read elsewhere is the host's, not here.
- `test_census.py`: ends that make no scale are named (presets decreasing); a second rename
  failing leaves both files as they were (`_main` with `Path.replace` failing on its second call).
- `test_files.py`: `replace_files` stages both before renaming either (a write failure of the
  second leaves the first untouched); a rename failing after one succeeded puts the first back;
  the directory is synced (`os.fsync` recorded, one fd a directory by `os.fstat`), skipped on
  Windows by name.
- `test_state.py`: deep nesting stays `PluginStateError`; `test_preset.py` (or `test_format.py`)
  holds `decode_end` naming what nests.
- `verification/old-behaviour.txt`: this revision's unit tests against `0fc8152`'s `src/`, each
  failure a finding's (the two modules importing `MapMismatchError` cannot collect there; said).

### Task 8: Docs and CHANGELOG

- `README.md`'s module list: `files.py` "replaces files whole or not at all".
- `CHANGELOG.md`: a `### Changed` entry under `[Unreleased]` for this revision, 17 findings at
  `0fc8152`, 16 addressed and #12 declined with its reason; `MachineMismatchError` becomes
  `MapMismatchError`. The version stays 0.0.1.

### Task 9 (FINAL): Verification gate

1–6. `scripts/gate.sh` exit 0, `verification/gate-run.txt`; `src/` and `tests/` change under
what the harness copies, so `scripts/gate-negative-tests.sh` and the CI replay rerun, one
transcript each. The plugin tests run, not skipped.
7. **Docs**: README, the docstrings of `host.py`, `parameters.py`, `files.py`, `preset.py`,
   `state.py`, `census.py`, `errors.py`; `CLAUDE.md` and `agent-os/product/` unchanged.
8. **Version**: the CHANGELOG entry; 0.0.1.
9. **Standards retrospective**, from the shipped diff, edits listed apart:
   - `vital/plugin-state.md`: errors from every reach; each call its own guard, held by the entry
     check; the containers read once; the map refused on another machine or Vital version by one
     error naming what differs; a render refuses a bool.
   - `vital/parameter-map.md`: the span and the displayed ends computed by bounds, a copy never
     stale; the grid's halves and why the rounding is away from zero; `fit_scale`'s one scale.
   - `vital/preset-file.md`: both census files staged then renamed, put back on failure; the
     directory synced.
   - `vital/preset-tests.md`: a plugin test skips by name where the map was measured elsewhere.
   - `index.yml`: the `vital:` descriptions follow; `base:` untouched.
   - Base proposal, to present to the owner: amend `fromtheoutfit/patchbay-standards#35` in
     place (measured data records its machine *and the plugin's version*; tests of the installed
     plugin skip by name where the data was measured elsewhere), or mark declined.
     `Proposals sent upstream:` recorded either way.

Then stop and print `git status --short`. No stage, commit or push.

## Verification

- Gate exit 0 with the plugin tests run; harness and CI replay `0 unexpected`.
- `old-behaviour.txt`: each finding's test fails at `0fc8152` and passes now.
- The census regenerates `parameters.json` byte for byte and `settings_keys.txt` unchanged (no
  field changes this time).
- The README example runs as written.
