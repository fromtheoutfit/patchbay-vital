# Spec A of issue #7 — the host and the parameter map

## Context

Issue #7 (https://github.com/fromtheoutfit/patchbay-vital/issues/7) makes `patchbay_vital` a real
`patchbay.Instrument` over Vital hosted by pedalboard. Discovery (appendix) answered its two
questions: a `.vital` preset *can* become the plugin's state (so `load_patch` can be complete), and
normalized → preset value is exactly linear or indexed in float32 for all 903 parameters, with
Vital's curve between the preset value and the display. The owner split the issue at its seam:
**Spec A** (this plan) builds the pedalboard extra, `VitalHost` with the state codec, the committed
parameter map and its generator, the scales, and the census and round-trip integration tests.
**Spec B** (filed as its own issue in Task 1) builds `VitalInstrument` on it. No instrument, no
contract tests, no mido, no CLI, no events here.

## Decisions (owner, 2026-11-09; shape.md records each with its evidence)

1. Scope: issue #7's host-and-map half, as the split and the answers below amend it.
2. **Licence:** stays MIT. pedalboard (GPLv3) is the optional extra `patchbay-vital[host]`
   (`pedalboard>=0.9.26,<1`); the format layer installs with no GPL code; `host.py` is the only
   module importing pedalboard; nothing copied from it. Recorded as an owner decision, not legal
   advice, revisited before any PyPI release.
3. **Gate route:** `pedalboard==0.9.26` (published 2026-10-07) also joins `[dependency-groups] dev`,
   a package entry, so the existing `uv sync --locked` installs it locally and in CI; no gate file
   changes. mido is Spec B's.
4. **Values:** the map's `Parameter`s speak the plugin's display units through Vital's curve kinds
   (multiply, offset); normalized ↔ preset is `linear` or `indexed`, exact float32.
5. **FMA:** no floor raise; `fma` with one rounding to float32, exact by `fractions.Fraction` and
   integer rounding (ties to even), proven by vectors measured on the 249 parameters where separate
   rounding differs; `math.fma` replaces it when the floor reaches 3.13.
6. **Identity:** `ParameterId` values are Vital's preset keys; pedalboard's key is `host_id` in the
   map, interpreted only in `host.py`. Recorded against the issue's wording (`parameter_id` = "the
   VST3 key pedalboard reports").
7. **Choices:** the six bad lists are disambiguated (`<label>_<index>` for a repeat,
   `option_<index>` for an empty name), the plugin's names kept in `choice_labels`.
8. **One source:** `parameters.json`; `settings_keys.txt` is derived from it plus
   `PRESET_ONLY_KEYS = {chorus_damping}` (written by 0.6.x, dropped on load by 1.6.4, no host
   parameter), checked by a unit test, and says so in `preset.py` and `vital/preset-file.md`.
9. **Measures, not samples:** every audio assertion is a measure with a named tolerance and a comment
   giving its source in the probes.
10. **Codec:** ours, from the probe; `wrap(unwrap(x)) == x`; `tuning` is an opaque section held like
    any other (`VitalPreset.tuning`).
11. **Sources:** every range, kind and key from plugin measurement; Vital's source (GPLv3, `636ca0e`)
    cited for corroboration only, no line written from it.
12. **Probe 4 → a quantization note upstream:** no tolerance field; propose to
    fromtheoutfit/patchbay that `Instrument.get`'s doc says it returns the nearest value the
    parameter holds. Presented to the owner and filed in the final task.
13. **Units** (the generator's suffix table, each recorded): `secs`/`s` → seconds; `ms` → seconds
    (multiply ÷1000); `dB` → db; `%` → percent (×100 or ×200 as shown); `semitones` → semitones;
    `c` → semitones (÷100); `Hz` → hz; `x`, `v`, `voices`, none → none; `Beats Per Minute` → bpm by
    its label. An unknown suffix fails the generator by name.
14. **Kinds:** `indexed` 0..1 → boolean; `indexed` with names → choice; numeric `indexed` (transposes,
    voices, `effect_chain_order`, `*_transpose_quantize`) → continuous on the indexed scale (whether
    a non-whole set is refused is Spec B's: core's `Parameter` has no step).
15. **Errors:** a new root `VitalError(PatchbayError)` above `VitalFormatError`; protocol failures
    derive from both the root and core's matching error so Spec B's contract tests catch them.
16. **Generator home:** `src/patchbay_vital/census.py` (scripts/ holds only shell scripts, gate step
    1; a top-level tools/ would escape mypy). Run as `python -m patchbay_vital.census`.

## Standards

Core five (Step 5a) plus `process/verification-gate`, `process/standards-retrospective`,
`process/standards-index`, `process/ownership`, `testing/tests`, `vital/preset-file`,
`vital/preset-tests` (owner's choice), snapshot at the pinned base commit in `standards.md`.

## Tasks (modules in import order, gate green after each)

### Task 1: Save spec documentation and file Spec B

- `agent-os/specs/{YYYY-MM-DD-HHMM}-the-host-and-the-parameter-map/`: `plan.md` (this plan),
  `shape.md` (first Decision cites #7; Decisions 1-16; the Vital-source citations and where each
  range, kind and key came from; out of scope: Hz/semitone/dB conversions beyond the plugin's own,
  CLI, semantics, agent code, wavetable authoring, performance tuning; the `integration` marker's
  description, a gate file, still says "presets" — recorded for the next gate spec),
  `standards.md`, `references.md` (below), `verification/discovery.md` (the appendix, with its
  transcripts as presented). Visuals: none.
- File **Spec B's issue** on fromtheoutfit/patchbay-vital (`gh issue create`, no attribution):
  VitalInstrument, Patch↔VitalPreset, mido builder, events, entry point, CONTRACT_TESTS, centroid
  test, the 0.1.0 issue; *Depends on* #7 and this spec folder; carrying decision 3 (the model is the
  truth, plugin state never read back as the patch, a diagnostic read for tests, its local
  standard), decisions 4, 6, 9, probe 4's numbers, the upgrade-on-load / 4-sample drift / off-grid
  snap caveats, the out-of-range preset values (`flanger_dry_wet` 0.7072 against 0..0.5 in ~25
  presets, kept by Vital; compressor ratios just above 1, clamped or kept; old `flanger_center`
  upgraded), render facts (78 ms per 2 s, 1-768 kHz, not sample-reproducible, centroid 302 → 2307
  Hz), open cost (~2.3 s with pedalboard's parameter wrappers), the dual-base errors, the
  numeric-indexed step question, mido 1.3.3 (MIT, 2024-10-25).

### Task 2: The dependency

`pyproject.toml`: `[project.optional-dependencies] host = ["pedalboard>=0.9.26,<1"]`; dev group
`"pedalboard==0.9.26"` with its date; header comment updated. `uv lock`; the diff into
`verification/lock-change.txt`. `tests/unit/test_package.py`: the extra is declared and its range
holds the installed version; `import patchbay_vital` in a subprocess with `pedalboard` blocked
succeeds and loads no pedalboard.

### Task 3: Re-run the probes in the locked environment

One consolidated probe script (scratchpad), run under `uv run --locked` (Python 3.12, pedalboard
0.9.26): state layout, census, fits, probe 4, fixture-as-state, render facts. Script and output into
`verification/probes.txt` as one run. The vectors for decision 5 (every grid point of the 249
FMA-discriminating parameters: r, span, min, the plugin's value) into `tests/data/fma-vectors.txt`.
**If any finding differs from the appendix, stop and report.**

### Task 4: `errors.py`

`VitalError(PatchbayError)` root; `VitalFormatError(VitalError)` and its three unchanged;
`VitalHostError(VitalError)` → `PluginLoadError(path, reason)`, `PluginStateError(reason)`;
`UnknownParameterError(VitalError, ParameterNotFoundError)` (parameter_id, instrument);
`ParameterRangeError(VitalError, ValueOutOfRangeError)` (parameter_id, minimum, maximum, given);
`CensusError(label, reason)`. Still the leaf (imports only patchbay). `tests/unit/test_errors.py`:
roots, dual bases, no narrower built-in, pickling and copy, messages.

### Task 5: `float32.py`

`round_to_float32(Fraction) -> float` (integer arithmetic, ties to even, subnormals, overflow
refused), `fma32(a, b, c) -> float`. `tests/unit/test_float32.py`: property against numpy's
double → float32 for every double; the recorded vectors, each also showing separate rounding
differs (so the vectors discriminate); ties pinned with `@example`.

### Task 6: `tuning` in the format

`VitalPreset.tuning: bytes | None = None` (the top-level object's text, `_json_section`-checked);
`format._parse` reads it by span, `dumps` writes it at its sorted place only when present,
`diff` reports it as `OpaqueChange("tuning")`; `_METADATA` excludes it. Tests in `test_preset.py`
/ `test_format.py`: a state-shaped text (the fixture plus a tuning object) round-trips byte for
byte; absent stays absent; a non-object tuning is malformed.

### Task 7: `state.py` — the codec (no pedalboard)

`PluginState` model holding every field read: `.vstpreset` (`VST3`, version, 32-byte class id,
`List` of `Comp` and empty `Cont`), `VstW` (8, 1, bypass), `CcnK`/`FBCh` (version, fx id, fx
version, programs, 128 future bytes), then `text` (the JSON object, found by `raw_decode`) and
`trailer`. `unwrap(bytes) -> PluginState`, `wrap(PluginState) -> bytes`; anything else is
`PluginStateError`, chained. `tests/unit/test_state.py`: `unwrap(wrap(s)) == s` and
`wrap(unwrap(x)) == x` over generated states; a state built from the committed fixture and the
measured header constants; each malformed layer refused by name.

### Task 8: `parameters.py` — the map's models and scales

`NormalizedScale` (`kind` linear|indexed, `minimum`/`maximum` float32-exact preset values;
`to_preset(normalized)` by `fma32`, rounded to a whole number for indexed; `to_normalized(preset)`
= float32((p − min)/span) exactly, which probe 4 P3 shows lands on p). `DisplayCurve` (`kind` from
the six measured — linear, quadratic, quartic, square_root, exponential, exponential_inverted —
`multiply`, `offset`; `to_display(preset)`, `to_preset(display)` rounded to float32).
`MappedParameter`: core's `Parameter` (id = preset key, label = the host's name, kind, unit,
display bounds, display default, disambiguated choices), `host_id`, `scale`, `curve`,
`preset_default`, `display_unit`, `choice_labels`; validators hold the bounds and default to what
the scale and curve compute, and kind to scale. `ParameterMap` (`instrument`, `vital_version`,
`parameters` sorted by id; ids and host ids distinct; `find(id)` → `UnknownParameterError`).
Conversions refuse outside the bounds with `ParameterRangeError`. `parameter_map()` loads
`data/parameters.json` once on first call (`importlib.resources`, `from_json_data`).
`PRESET_ONLY_KEYS`. `tests/unit/test_parameters.py`: models refuse an inconsistent record; per
scale and curve, hypothesis over normalized r: `to_normalized(to_preset(r))` lands on the same
preset value, and `curve.to_preset(curve.to_display(p)) == p` exactly; three literal anchors (min,
default, max) per kind from the probe transcript; refusals.

### Task 9: `host.py` — `VitalHost` (the only pedalboard import)

`DEFAULT_PATH = /Library/Audio/Plug-Ins/VST3/Vital.vst3` (documented; explicit path first; no
search). `VitalHost(path=None)`: missing path or a load pedalboard refuses or a plugin not named
Vital → `PluginLoadError`, chained. Public API in plain values: `name`, `version`,
`parameter_ids()`, `unmapped_parameters()` (labels), `get(id) -> float` / `set(id, normalized)`
normalized (unknown id, non-finite or outside [0, 1] refused), `state() -> bytes` /
`load_state(bytes)` (through `state.py`, the header kept from the plugin's own),
`render(midi: Sequence[tuple[bytes, float]], samples: int, sample_rate: int)` → `(2, samples)`
float32, and `measure(grid)` / `display_texts(host_id, points)` for the generator. Parameters go
through pedalboard's public `parameters` mapping (typed stubs; `_parameters` is private). The
render length rule and MIDI timestamp meaning are probed here and recorded.
`tests/unit/test_host.py`: a missing path is `PluginLoadError` (needs no plugin).

### Task 10: `census.py` — the generator

Pure fitting over `measure()`'s output: the moving key, linear vs indexed (exact match of the
grid through `fma32`, no tolerance), curve kind and constants (least squares, snapped to the
fewest significant digits that reproduce every display text at its printed precision), the unit
table, kinds, disambiguated choices; an unfit parameter is `CensusError` naming it.
`python -m patchbay_vital.census [--plugin PATH] --parameters FILE --settings-keys FILE` (both
outputs explicit). Run it: `data/parameters.json` (903 records) and `settings_keys.txt`
(unchanged, 456 lines, expected); counts by kind, curve and unit into
`verification/census-run.txt`. `tests/unit/test_census.py`: synthetic measurements per curve,
snapping, suffix table, classifier (`4/1` is a name), disambiguation, an unfit case; the derived
`settings_keys.txt` equals the file.

### Task 11: Integration tests — `tests/integration/test_vital_plugin.py`

Marker `integration`, skipped by name without the plugin at `DEFAULT_PATH`: the census regenerated
equals the committed map and the plugin's version equals its `vital_version`; every host parameter
mapped and every record hosted; a round trip per kind through the plugin (set normalized, the
state holds `scale.to_preset`); `wrap(unwrap(preset_data)) == preset_data`; the fixture as state
reads back equal but `sample`, which is delayed by exactly 4 samples; every manifest preset loaded
as state reads back as a `VitalPreset`, routing and metadata (but `synth_version`, `preset_name`)
preserved, stable on a second load but `sample` within 8 float32 ulps (probe: max 7); a routing
only in the JSON moves 20 ms RMS variation above 0.5 against a control below 0.1 (probe: 1.35 /
0.018); a render is `(2, samples)`, finite, and a note at 0.5 s is silent before it; an unknown
id and an out-of-range normalized value refused through the host.

### Task 12: `__init__.py`

Re-export the new errors and the map's public names (`ParameterMap`, `MappedParameter`,
`NormalizedScale`, `DisplayCurve`, `parameter_map`, `PRESET_ONLY_KEYS`); never `host` or `census`.
`test_package.py` holds the surface.

### Task 13: Docs

`README.md` (layout, install with `[host]`, the licence note), `CLAUDE.md` and the
`pyproject.toml` header (the dev group's package entries now include pedalboard),
`agent-os/product/tech-stack.md`, the `__init__` and `preset.py` docstrings.

### Task 14 (FINAL): Verification gate

1-6. `scripts/gate.sh` exits 0 with the integration tests run here, not skipped;
   `verification/gate-run.txt` with date and branch, the last act before hand-over. No gate file
   changes, but `src/`, `tests/`, `pyproject.toml` and `uv.lock` change under what the negative
   harness copies, so `scripts/gate-negative-tests.sh` and `j` rerun, one transcript each.
   `uv build` and the wheel's file list (`data/parameters.json` in; pedalboard only under the
   `host` extra) into `verification/wheel-contents.txt`.
7. **Docs**, recorded in `shape.md`.
8. **Version**: `[Unreleased]` in `CHANGELOG.md` (Added: the extra, host, codec, map, generator,
   `tuning`; Changed: the error root); the version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff: project standards under
   `agent-os/standards/vital/` (candidates: `parameter-map.md`, `plugin-state.md`, `measures.md`;
   `preset-file.md` for `tuning` and the derived keys; `preset-tests.md` for the plugin tests) with
   `index.yml`'s `vital:` section; base proposals only for what a second adapter needs (candidates:
   dual-base protocol errors, a GPL host as an extra the root never imports). Every proposal and the
   quantization note (Decision 12) presented to the owner with AskUserQuestion; approved base ones
   filed as one issue on fromtheoutfit/patchbay-standards, the note on fromtheoutfit/patchbay, no
   attribution; `Proposals sent upstream:` recorded.

Then stop and print `git status --short`. No stage, commit, push or PR.

## References

- `src/patchbay_vital/format.py` / `preset.py` — span reading, opaque sections, refusals as the
  package (tuning follows them).
- The format spec (`agent-os/specs/2026-11-09-1509-the-vital-format/`) — discovery-then-shape,
  manifest-driven integration tests, recorded vectors (`grisu2-vectors.txt`).
- patchbay-core at `dd2bcad`: `models.py` (`Parameter`, `Quantity`, `Unit`), `errors.py`,
  `testing/contract_tests.py` (what Spec B must pass, bounds only).
- `scripts/gate-negative-tests.sh` — what it copies, hence the rerun.

## Verification

- Gate exits 0 with the integration tests run (census, 75 presets as state, fixture, render).
- Census regenerates the committed map exactly; no parameter unfit.
- Exactness: vectors, the float32 property, and the per-curve round trips all exact.
- Negative suite and `j` end `0 unexpected`; Spec B's issue filed; the core note filed if approved.

The discovery this plan rests on is `verification/discovery.md`.
