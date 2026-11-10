# Revision after the review of PR 9

## Context

The owner's review of PR 9 at `eb95567`
(https://github.com/fromtheoutfit/patchbay-vital/pull/9#issuecomment-6770350222) lists 24
findings: 2 reproduced by running, then errors escaping `VitalError`, robustness, portability,
docs that don't match the code, design, efficiency, simplification and one convention. Each was
checked while shaping against the code, pedalboard 0.9.26's source and the plugin; all hold, with
these refinements:

- #13: pedalboard caches its Python wrappers itself (`_get_parameters`, `__python_parameter_cache__`)
  and each wrapper re-fetches the native parameter on every attribute access (`__getattr__`,
  `__setattr__`); the first probe's crash came from holding the *native* `_parameters` objects.
  Reading `plugin.parameters` afresh costs ~3 ms (re-walks 903). So the docs change, not the code.
- #3: pedalboard 0.9.26 accepts empty and odd MIDI bytes without error here; its `preset_data`
  setter raises a bare `RuntimeError` ("Failed to set preset data"), which `load_state` lets out.
- #19: a Vital load is ~2.2 s; the gate's pytest is 65 s for 417 tests, ~14 loads.
- #17: `functools.cached_property` on a frozen `PatchbayModel` works under pydantic 2.14.3, equality
  and JSON round trip intact (probed).

This revision makes the host, the codec, the map and the census keep the promises their docstrings
and the errors standard make, on PR 9's branch so PR 9 carries it. No gate file changes.

## Decisions (owner, 2026-11-10)

1. **Scope:** all 24 findings; 16 declined with its reason; 24 is the owner's at commit time.
2. **#13:** keep `self._hosted`; correct `host.py`'s docstring and `vital/plugin-state.md`: the
   Python wrappers are held and are safe because each re-fetches the native parameter per access;
   the native objects are never held.
3. **#11:** `MappedParameter`'s validator checks the round trip in float32: the curve's `to_preset`
   of each bound lands on the scale's ends and of the default's display on `preset_default`. The
   census still computes the bounds exactly; the integration test still regenerates the map equal.
4. **#12:** `ParameterMap` gains `machine` (`platform.machine()`, `"arm64"`); the census writes it;
   `VitalHost` refuses a map measured on another machine, where the map is first used (not in
   `__init__`, so the census can run on a new machine with no map of its own).
5. **#19:** one module-scoped `VitalHost` per integration module; a function-scoped fixture loads
   the initial state's text before each test.
6. **#8:** `OpaqueChange` gains `where: Literal["settings", "preset"]`, `"preset"` for the top-level
   `tuning`.
7. **#16: declined.** The validator's decode is the model holding its own invariant
   (`base/python/models`); the census runs once per Vital version and its ~10k `state()` calls are
   ~2.5 ms each. Recorded in `shape.md`.
8. **#20:** a new module `src/patchbay_vital/files.py` holding `replace_file`: "replace a file whole
   or not at all" is a file-system concern, one concern per module (`base/python/layout`), and two
   importers make it a module rather than a private helper. `format.py` and `census.py` import it.
9. **Steps 2-5:** no visuals; references and standards as in Task 1.

## Tasks

### Task 1: Save spec documentation

`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`:
- `plan.md`: this plan.
- `shape.md`: shaping answers; Decisions 1-9; a table of the 24 findings and each outcome
  (as the PR 6 revision's); the probes above (pedalboard's cache and `__getattr__`, load timing,
  `preset_data`'s `RuntimeError`, the `cached_property` probe). Finding 24 noted as the owner's at
  commit time, this revision's retrospective edits listed apart.
- `standards.md`: snapshot of the core five plus `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file`, base at
  `e31f7db`, project standards at the branch head.
- `references.md`: the PR 6 revision folder (the shape of a review revision, `old-behaviour.txt`);
  the host spec's `shape.md` and `verification/probes-first-attempt.txt` (#13's evidence);
  `format._replace_file` and `preset._json_section` (patterns reused); pedalboard 0.9.26's
  `_pedalboard.py` (`_get_parameters`, `AudioProcessorParameter.__getattr__`), read for the fact.

### Task 2: `src/patchbay_vital/files.py` (new) and `format.py` (#20, #8)

- `files.py`: `replace_file(path: Path, raw: bytes) -> None`, the body of `format._replace_file`
  moved whole (temporary beside the target, mode kept, rename over, temporary removed on failure).
  Imports nothing from the package. Module docstring: the preset-file standard's "whole or not at
  all" and who uses it.
- `format.py`: `dump` calls `files.replace_file`; `_replace_file` is gone.
- `preset.py`: `OpaqueChange.where: Literal["settings", "preset"]`.
- `format.py`: `_opaque_change` takes `where`; sections under `settings` are `"settings"`, the
  top-level tuning `"preset"`. Docstring of `_opaque_changes` says so.
- README's module list names `files.py` (Docs step).

### Task 3: `src/patchbay_vital/state.py` (#2, #7)

- `_object_end` turns `RecursionError` into `ValueError` ("the text nests too deeply to read"),
  as `preset._json_section` does, so `with_text` reports `PluginStateError` and `unwrap`'s except
  tuple drops `RecursionError`.
- `_container` refuses a negative component or controller size before the offset checks:
  `_expect`-style message "a chunk's size is not negative".

### Task 4: `src/patchbay_vital/errors.py` (#21, #12)

- A private `_ReasonError(VitalError)` base: `__init__(reason)`, `self.reason`, `__str__` from a
  class attribute prefix. `MalformedPresetError(VitalFormatError, _ReasonError)`,
  `PluginStateError(VitalHostError, _ReasonError)`, `PluginRenderError(VitalHostError, _ReasonError)`
  keep their names, fields, `args` order and messages.
- New `MachineMismatchError(VitalHostError)` with fields `measured: str`, `running: str`: "the map
  was measured on 'arm64' and this process runs on 'x86_64'". Module docstring updated.

### Task 5: `src/patchbay_vital/parameters.py` (#1, #11, #12, #17)

- `MappedParameter.to_preset`: after the curve and the clamp, an indexed scale rounds with
  `_round_half_away`; a choice or boolean refuses a non-whole display value with
  `ParameterRangeError` (core's whole-number rule, as `Parameter.check` applies it). Docstring:
  "the nearest value the parameter holds; a choice or boolean takes a whole index".
- `_the_parameter_is_what_the_scales_compute` (#11): `{curve.to_preset(parameter.minimum),
  curve.to_preset(parameter.maximum)} == {scale.minimum, scale.maximum}` (unclamped, so a wrong
  bound is not hidden), `curve.to_preset(parameter.default.value) == preset_default`, and the
  default a float32 in the scale's range. Module docstring says the bounds are held in float32,
  so a libm an ulp apart still loads the map.
- `ParameterMap.machine: str = Field(min_length=1)` (#12).
- `NormalizedScale.span` becomes `functools.cached_property` (#17).
- `data/parameters.json`: `"machine":"arm64"` added to the header by rerunning the census
  (Task 7 verifies the rest regenerates byte for byte).

### Task 6: `src/patchbay_vital/host.py` (#3, #5, #6, #12, #13, #14, #15, #18)

- `_c_library` looks each name up lazily: iterate over `(lambda: find_library("c"),
  lambda: find_library("m"), lambda: "ucrtbase")` (#18).
- Every plugin access sits inside `with _environment_kept()`: `name`, `version`, `get`,
  `preset_data`, `state`, `load_state`'s read, `display_texts`, `measure`'s first read,
  `unmapped_parameters`, `parameter_ids` (#14). Module docstring: "every call into the plugin"
  stays true; Task 8's fake-plugin test holds it.
- pedalboard's errors are wrapped, chained (#3): a raw value the plugin refuses in `set` and the
  `preset_data` setter's refusal in `load_state` are the plugin's state, so `PluginStateError`;
  `process`'s refusal in `render` is `PluginRenderError`. Caught: `(RuntimeError, ValueError,
  TypeError)`, the types pedalboard raises.
- `render` (#5, #15): `samples` and `sample_rate` go through `operator.index` (a `TypeError` is
  `PluginRenderError` "a positive whole number"), then `< 1` as now; asks for `(samples + 1) /
  sample_rate`, refuses fewer than `samples`, returns `np.ascontiguousarray(audio[:, :samples])`.
  Docstring and module docstring: "one sample more, the first `samples` returned"; the
  "half a sample" sentence goes.
- `measure` (#6): `try/finally` restores `self._plugin.preset_data = start` per parameter.
- `_parameter_map` (#12): on first use, `MachineMismatchError(map.machine, platform.machine())`
  when they differ.
- Module docstring (#13): the wrappers pedalboard's mapping gives are held in `self._hosted`;
  each fetches the native parameter on every access; a native object held across loads crashed.

### Task 7: `src/patchbay_vital/census.py` (#4, #9, #12, #20, #22, #23)

- `_record`: `Quantity(...)` inside the `try` (#4).
- `build_map`: duplicate preset keys across hosted parameters are `CensusError` naming the second
  label ("its preset key X is also <label>'s"); `ParameterMap(...)` wrapped, a refusal
  `CensusError("the map", reason)` chained (#4). `machine=platform.machine()` (#12).
- `_choices` (#9): names unique and non-empty are kept and pre-seed `taken`; every other gets
  `option_<i>` / `<name>_<i>`, lengthened by `_<i>` while taken. Terminates; never collides.
- `_BOOLEAN` stays for the switch; `_fit_curve` uses `_TWO_POINTS = 2` with its own docstring (#22).
- `fit_scale`'s message computes "against" with the float32 span
  (`round_to_float32(Fraction(maximum) - Fraction(minimum))`) (#23).
- `main` writes through `files.replace_file`, the key list first, then the map (#20).
- Rerun: `uv run --locked python -m patchbay_vital.census --parameters
  src/patchbay_vital/data/parameters.json --settings-keys src/patchbay_vital/settings_keys.txt`;
  the diff is the one header field; `settings_keys.txt` unchanged.

### Task 8: Tests

- `tests/unit/test_files.py` (new, mirrors `files.py`): a failed write leaves the file as it was and
  no temporary; mode kept; written through a symlink. `test_format.py` keeps its `dump` tests.
- `tests/unit/test_host.py`: a fake plugin (`monkeypatch.setattr(pedalboard, "VST3Plugin", ...)`,
  name `"Vital"`, parameters keyed by real `host_id`s, `preset_data` from `wrap(PluginState(...))`)
  that sets upward rounding on every call: after each public method the rounding mode is back
  (#14); the fake raising `RuntimeError` from the setter, `raw_value` and `process` is the
  package's error, chained (#3); `measure` restores the state when a read fails mid-grid (#6);
  a map whose `machine` differs is `MachineMismatchError` from `get`, not from `VitalHost()`
  (#12); `render(midi, 10.5, r)` and `(midi, n, 44100.7)` refused by name (#5); `load_state` of
  200,000 `[` is `PluginStateError` (#2); `_FE_UPWARD` is `0x200` on Windows AMD64, skipping
  elsewhere on Windows (#10); `find_library("m")` not called when the C library holds both (#18).
- `tests/unit/test_state.py`: `with_text` of deep nesting is `PluginStateError` chained from the
  validation error (#2); a negative chunk size in `_damages` (#7); the hypothesis strategies
  unchanged.
- `tests/unit/test_parameters.py`: `oversampling`-like record `to_preset(4.5)` is a whole preset
  value and `to_normalized` lands the plugin on it; a choice's and a boolean's non-whole display
  is `ParameterRangeError` (#1); a record whose bound is a libm ulp off still validates, one a
  float32 step off is refused (#11); `_map(...)` builders gain `machine="arm64"`; the committed
  map's `machine` is `"arm64"` (#12); `span` computed once (`cached_property` in `__dict__`) (#17).
- `tests/unit/test_census.py`: `('A', 'A', 'A_1')` and `('', 'option_0')` told apart (#9); a
  non-finite default display and two measurements sharing a preset key are `CensusError` naming
  the label, and `main` exits 1 saying so (#4); a failed key-list write leaves both files as they
  were (#20); `fit_scale`'s message quotes float32 values (#23).
- `tests/unit/test_format.py`: a preset differing in a settings-level `tuning` section and the
  top-level one gives two `OpaqueChange`s told apart by `where` (#8); existing tuning diff test
  asserts `where == "preset"`.
- `tests/unit/test_errors.py`: the three reason errors rebuild from `args`, messages unchanged;
  `MachineMismatchError` fields and message (#21, #12).
- `tests/integration/test_vital_plugin.py` (#19): module-scoped `vital` fixture; function-scoped
  `host` loads the initial state's text; `test_a_render_is_the_length_asked_for_and_finite` keeps
  7 and 100003; a new assertion that `set` of a non-whole choice display through `to_normalized`
  is refused before the plugin is touched (#1).
- `verification/old-behaviour.txt`: this revision's tests against `eb95567`'s `src/`, each failure
  a finding.

### Task 9 (FINAL): Verification gate

1-6. `scripts/gate.sh`: shell scripts parse; `uv sync --locked` then ruff format; ruff check; mypy;
pytest; `scripts/sync-standards.sh --check`. Exit 0, `verification/gate-run.txt` with date and
branch, the last act before hand-over. `src/` and `tests/` change under what the harness copies, so
`scripts/gate-negative-tests.sh` and the CI replay rerun, one transcript each. The integration
tests run (Vital installed), not skipped.
7. **Docs**, recorded in `shape.md`: `README.md`'s module list (`files.py`), `host.py`,
   `parameters.py`, `state.py`, `census.py`, `errors.py` docstrings; `CLAUDE.md` and
   `agent-os/product/` unchanged.
8. **Version**: `[Unreleased]` `### Changed` entry in `CHANGELOG.md`; the version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff, its edits listed apart:
   - `vital/plugin-state.md`: wrappers held, native objects never (#13); every plugin call guarded
     and held by the fake-plugin test (#14); a render asks one sample more and returns the first
     `samples` (#15); the map's machine refused on mismatch (#12); pedalboard's errors wrapped (#3).
   - `vital/parameter-map.md`: an indexed scale's `to_preset` rounds, a choice takes a whole index
     (#1); the record held in float32 (#11); `machine` recorded and the arm64 FMA assumption named
     (#12); choice names made unique by lengthening (#9).
   - `vital/preset-file.md`: `OpaqueChange.where` (#8); `replace_file` in `files.py` (#20).
   - `agent-os/standards/index.yml`: the `vital:` descriptions follow; `base:` untouched.
   - Base proposals: expected none; if the fake-plugin guard test or the machine check reads as a
     rule for any adapter hosting native code, present it to the owner and file on
     `patchbay-standards` (no attribution) or mark declined. `Proposals sent upstream:` recorded
     either way.

Then stop and print `git status --short`. No stage, commit or push.

## Verification

- `scripts/gate.sh` exits 0 with the integration tests run; the negative suite and the CI replay
  each end `0 unexpected`.
- `verification/old-behaviour.txt`: each reproduced finding's test fails at `eb95567` and passes now.
- The census regenerates `parameters.json` byte for byte but the `machine` field;
  `settings_keys.txt` unchanged.
- The README example still runs as written.
