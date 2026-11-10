# The Host and the Parameter Map — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`. Discovery
ran first and the owner saw its findings, with the probe transcripts, before any model or module
was proposed (`verification/discovery.md`). The owner then decided eleven points standing for this
spec and the next, judged the issue too large for one review and split it at its seam. This is
Spec A, the host and the map; Spec B, the instrument, is its own issue.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #7's host-and-map half: pedalboard as the optional extra `patchbay-vital[host]`; `VitalHost`
with the state codec; `src/patchbay_vital/data/parameters.json`, its generator and `parameters.py`
with the scales; the census and round-trip integration tests. No `VitalInstrument`, no
`Patch`↔`VitalPreset`, no mido, no events, no entry point and no contract tests: those are Spec B's.
CHANGELOG entry, gate green, `verification/gate-run.txt` with date and branch, present-and-file. No
stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** issue #7, split by the owner at its seam, as the Decisions below amend it.
- **Step 2, visuals:** none; nothing here has a screen.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission's second bullet, "the map between Vital's VST3 parameters
  and a preset's keys, and the unit conversions between them, so a value means the same thing on
  either side": the map is that, and Decision 5 is why its values are in the plugin's display units.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/preset-file` and `vital/preset-tests`, at the owner's choice. Snapshot in
  `standards.md`.

## Decisions

1. **The scope is issue #7**, https://github.com/fromtheoutfit/patchbay-vital/issues/7, its host and
   map half. The split is the owner's: the issue's "host + map data first; instrument + contract
   tests second" seam. Spec B is filed as
   https://github.com/fromtheoutfit/patchbay-vital/issues/8, depending on #7 and this folder.
2. **Licence: this repository stays MIT; pedalboard joins as the optional extra
   `patchbay-vital[host]`, `pedalboard>=0.9.26,<1`.** pedalboard is GPLv3 (its PyPI classifier and
   the license text in its wheel's metadata). The format layer installs with no GPL code;
   `host.py` is the only module that imports pedalboard and is the seam another host could replace;
   nothing is copied from pedalboard. The root package never imports `host.py`, and a test holds it.
   `numpy>=2.5.4,<3` is declared in the same extra: `host.py` imports it directly for its render
   arrays, and `base/python/toolchain.md` declares a direct import though patchbay-core and
   pedalboard bring it in (BSD-3-Clause; the lock adds no package, only this one's entry). The tests
   that import numpy take it from the package's own declaration.
   This is the owner's decision, not legal advice, and is revisited before any release to PyPI.
   What it does: hosts the VST3 and renders it. Why the standard library cannot: hosting a VST3 is
   native code. The floor is the version the gate ran, the latest on PyPI (2026-10-07).
3. **The gate installs pedalboard through the dev group, `pedalboard==0.9.26`** (published
   2026-10-07), at the owner's word. `scripts/gate.sh` and `.github/workflows/gate.yml` run
   `uv sync --locked` and are the gate's own files, changed only in a gate spec; a dev-group entry
   other than the gate's tool pins is the package's, so the existing sync installs it locally and in
   CI with no gate file changed. pedalboard ships `py.typed` and `pedalboard_native/__init__.pyi`, so
   `[tool.mypy]`, a gate file, needs no override; Linux cp312 wheels exist for CI.
4. **Identity: a `ParameterId` is Vital's preset key**, stable and canonical, one vocabulary for the
   file and the instrument. pedalboard's key, the snake-cased display name, is `host_id` in the map
   and is interpreted only in `host.py`. **This departs from the issue's wording**, which made
   `parameter_id` "the VST3 key pedalboard reports": 256 of the 903 differ from the preset key
   (`envelope_1_attack` against `env_1_attack`), and the preset key is the one a file, a diff and an
   agent already use.
5. **Values are the plugin's display units, through Vital's curve kinds.** A map record's `Parameter`
   has its bounds and default in the unit the plugin displays (seconds, dB, %, semitones, Hz);
   normalized ↔ preset is `linear` or `indexed` in exact float32, and preset ↔ display is one of the
   six measured curves with a multiply and an offset. Evidence: Q2 of the discovery (552 linear, 351
   indexed, every grid point exact; the curves fitted on every continuous parameter).
6. **Probe 4: values a parameter can hold come back exactly; arbitrary values do not, for any kind.**
   Bounds recovered exactly on all 552 continuous parameters; 1,104,000 values on their grids exact,
   every curve; 0 of 552,000 arbitrary display values exact, linear included, which is float32
   quantization and not the curves. So the owner dropped the tolerance field and chose **a
   quantization note upstream**: a proposal to fromtheoutfit/patchbay that `Instrument.get`'s
   documentation says it returns the nearest value the parameter holds. Presented and filed in the
   final task. **Correction, found by the map's property test (Task 8):** probe 4 drew normalized
   values uniformly and never came near `volume`'s floor. There, a preset value at or below 2 ** -43
   displays within 3.4e-7 dB of the curve's -80 dB offset, under a double's spacing at -80, so
   neighbouring presets share a display and the preset does not come back; every float32 above it
   does (checked over every 53rd float32 below 2 ** -43 and the 2,000,000 above it). The displayed
   value still comes back exactly everywhere (13,295,153 of 13,295,153 below the edge), so get after
   set in display units holds; what the instrument stores where two presets share a display is
   Spec B's.
7. **FMA without raising the floor.** The plugin's value is `r·span + min` rounded once to float32,
   a fused multiply-add: where that and separately rounded arithmetic differ, only the fused one
   matches, on 249 parameters over the discovery's 9-point grid and 252 over the census's 11 points
   (`verification/probes.txt`; separate rounding alone matches none). `float32.py` does it exactly
   with `fractions.Fraction` and integer rounding, ties to even, held by the 2772 vectors measured on
   those 252 (`tests/data/fma-vectors.txt`); `math.fma` (3.13) replaces it when the floor moves.
8. **Choices: the six bad lists are disambiguated in `parameters.json`**, `<label>_<index>` for a
   repeated name and `option_<index>` for an empty one, the plugin's own names kept beside in
   `choice_labels`, so core's rule (choices distinct and non-empty) stands. Evidence:
   `filter_{1,2,fx}_style` name indices 5 to 8 `''`; `osc_{1,2,3}_distortion_type` repeat
   `FM <- Osc` and `RM <- Osc`.
9. **One source of truth: `parameters.json`.** `settings_keys.txt` is derived from its non-slot ids
   plus `PRESET_ONLY_KEYS`, which holds `chorus_damping` (written by 0.6.x, dropped on load by 1.6.4,
   no host parameter); the generator writes both, a unit test holds the derivation, and `preset.py`
   and `vital/preset-file.md` say so.
10. **Measures, not samples.** Audio is not sample-reproducible (consecutive renders differ; two
    instances' centroids 4641 and 4652 Hz in discovery, 4657 and 4610 in `verification/probes.txt`),
    so every audio assertion is a measure with a named tolerance and a comment saying where its
    number came from.
11. **The codec is ours, written from the probe**, with `wrap(unwrap(x)) == x` as a property; the
    state's extra top-level `tuning` is an opaque section held like any other, as
    `VitalPreset.tuning`, the object's text.
12. **Sources.** Every range, scale kind and key name in the map comes from measuring the plugin
    (table below). Vital's source is GPLv3 and was read for facts only, cited for corroboration; no
    line of this repository is written from it.
13. **Units, the generator's suffix table:** `secs` and `s` → seconds; `ms` → seconds, the plugin's
    ×1000 dropped; `dB` → db; `%` → percent, its ×100 or ×200 kept as shown; `semitones` →
    semitones; `c` (cents) → semitones, its ×100 dropped; `Hz` → hz; `x`, `v`, `voices` and no
    suffix → none; and `Beats Per Minute`, displayed with no suffix, → bpm by its label. `ms` and
    `c` are scalings within a dimension, not the Hz/semitone/dB conversions the issue rules out;
    `patchbay.Unit` has no ms or cents. An unknown suffix fails the generator by name.
14. **Kinds:** an indexed parameter of two values shown as Off and On, or as numbers (`bypass`), is a
    boolean; an indexed one whose texts are other names is a choice; a numeric indexed one
    (transposes, voices, polyphony, `effect_chain_order`, `*_transpose_quantize`) is continuous on
    the indexed scale. A choice's value is its index, the preset value less the scale's minimum
    (`delay_tempo` and `delay_tempo_2` start at 4). Whether a non-whole value set on a numeric
    indexed one is refused is Spec B's: core's `Parameter` has no step. **Refined during the census
    (Task 10):** the plan's "indexed 0 to 1 is a boolean" would have dropped the names of five
    two-way choices (`eq_band_mode` Shelf/Notch, `eq_high_mode` Shelf/Low Pass, `eq_low_mode`
    Shelf/High Pass, `stereo_mode` SPREAD/ROTATE, `voice_override` Kill/Steal), so a pair of
    names other than Off and On stays a choice: 243 booleans, 79 choices, 581 continuous
    (`verification/census-run.txt`).
15. **Errors: a new root, `VitalError(PatchbayError)`, above `VitalFormatError`**, now that the
    package reports host and map failures too. A failure core's protocol names derives from both the
    root and core's matching error (`UnknownParameterError(VitalError, ParameterNotFoundError)`,
    `ParameterRangeError(VitalError, ValueOutOfRangeError)`), so `base/python/errors.md`'s one root
    holds and Spec B's contract tests catch core's types.
16. **The generator lives in the package, `src/patchbay_vital/census.py`**, run as
    `python -m patchbay_vital.census`: `scripts/` holds only shell scripts (gate step 1 fails any
    other file), and a top-level `tools/` would escape the gate's mypy, which reads `src/` and
    `tests/`. It needs the extra, measures through `host.py` and fits in pure Python.

## Found while building, beyond the plan

Each is recorded where it bears (Decisions 2, 6, 7 and 14, the standards, issue #8's comment), and
listed here so `plan.md` is not read as the whole of what shipped:

- **Vital leaves the process flushing subnormals to zero** after it loads or renders. Found when the
  unit tests ran after the plugin tests in one pytest process (hypothesis refused to draw
  subnormals); `host.py` now keeps the floating-point environment around every call into the plugin
  (`verification/float-environment.txt`, `test_the_process_keeps_its_floating_point_environment`).
- **A native parameter object held across state loads crashes the process** (the first probe run,
  `verification/probes-first-attempt.txt`), which settled reaching pedalboard's parameters through
  its public mapping.
- **`volume`'s floor** (Decision 6's correction) and **a load re-quantizing the sample** by up to one
  16-bit step (the fixture's -5000 reads back -4999).
- **A choice's index is its preset value less the scale's minimum** (`delay_tempo` starts at 4), and
  **two-name choices stay choices** (Decision 14's refinement).
- **pedalboard truncates a duration's samples**, so `render` takes its length in samples, and
  `PluginRenderError` joins the errors; `load_state` takes a `.vital` file's trailing newline.
- **numpy is declared in the extra** (Decision 2): `host.py` imports it.
- `VitalHost.preset_data()` and `VitalHost.host`: the plugin's own bytes, for the codec's
  integration test and as the diagnostic read, and the host's name and version for the map.

## Where each range, scale kind and key name came from

| Fact | Measured by | Corroborated in Vital's source (`636ca0e`) |
|---|---|---|
| Preset key of each parameter | setting each parameter's normalized value and reading which state float moves (census, `verification/probes.txt`) | `synth_parameters.cpp` 44-55, 535-602: id prefixes `env`/`osc`/`random`, names `Envelope`/`Oscillator`/`Random LFO` |
| Preset range (min, max) | the state's value at normalized 0 and 1 | `synth_parameters.cpp` table entries, e.g. `cutoff` 8..136 (421), `attack` 0..2.37842 (354) |
| `linear` / `indexed` | every grid point equal to `fma32(r, span, min)`, rounded for indexed | `value_bridge.h` 107-119 (`convertToEngineValue`, `std::round` for `kIndexed`) |
| Curve kind, multiply, offset | least squares on the plugin's display texts, snapped to the texts' precision | `value_bridge.h` 71-81 (`display_multiply * skewValue + post_offset`), 134-151 (the skews); `synth_parameters.h` 26-53 (`ValueScale`) |
| Unit | the display text's suffix | `ValueDetails::display_units` (`synth_parameters.h` 49) |
| Choices | the display text at each index | `string_lookup` (`value_bridge.h` 74-75) |
| Boolean | indexed with span 1 | `isBoolean` (`value_bridge.h` 102-104) |
| Default | the init state's value | `ValueDetails::default_value` |

The source is older than the 1.6.4 binary (2022-04-20; ramps and the third oscillator's later
parameters postdate it), so where they could differ the plugin decides.

## Out of scope

Hz/semitone or dB conversions beyond the plugin's own units; the CLI; sound-design semantics and
roles; any agent code; wavetable authoring; performance tuning beyond the recorded render and load
times; and all of Spec B.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** the mission's second bullet (Step 4 above).
- **A gate file's wording, for the next gate spec:** the `integration` marker's description in
  `[tool.pytest.ini_options]` says "needs an installed Vital's presets"; this spec's plugin tests
  carry the same marker and skip by name without the plugin. The description is a gate file, so it
  is not changed here.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — `src/`, `tests/`, `pyproject.toml` and `uv.lock` change under
  what the negative harness copies, so it reruns
- `base/process/standards-retrospective` — the map, the state and the measures rules, and which side
  each falls on
- `base/process/standards-index` — this repository's `vital:` section
- `base/process/ownership` — the owner commits; pedalboard is a project dependency, not a system tool
- `base/testing/tests` — the mirror, property tests with pinned examples, recorded vectors
- `vital/preset-file` — `tuning` and the derived key list change it
- `vital/preset-tests` — the plugin tests read installed presets and the committed fixture

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

**Results (2026-11-09):** exit 0 on branch
`feature/7-the-host-and-the-parameter-map-load-vital-through-pedalboard-map-all-903-parameters-to-preset-keys-and-pass-cores-contract-tests-as-a-real-instrument`,
`verification/gate-run.txt`, 411 tests, the plugin's integration tests among them and not skipped
(the census regenerating the committed map, the 75 presets as state, the fixture, the renders). No
gate file changed, but `src/`, `tests/`, `agent-os/standards/`, `pyproject.toml` and `uv.lock`
changed under what the negative harness copies, so it was rerun on the final tree:
`verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
`verification/ci-negative-test.txt` `3 runs, 0 unexpected`. The run before the last standards edits
and numpy's declaration ended the same and is not kept. The rest of `verification/`: the discovery
and its one-run re-probe (`discovery.md`, `probes.txt`, `probes-first-attempt.txt`), the host's two
facts (`host-probes.txt`), the float environment (`float-environment.txt`), the census
(`census-run.txt`), the lock's change and the wheel's contents. CI has no Vital, so the plugin
tests skip there; the hosted run of this branch exists only after the owner's push.

**Docs (step 7):** checked against the shipped files, and each reads true:
- `README.md`: what the package does now (the map and, with the extra, the host), two examples run
  as written against an installed preset (`diff ... .is_empty` True, `Unit.seconds`, a `(2, 48000)`
  float32 render); Layout names the new modules, `data/parameters.json`, the plugin tests and
  `fma-vectors.txt`; Install says `uv sync` installs pedalboard through the dev group, that a
  consumer installs `patchbay-vital[host]` to host, and the licence decision as the owner's.
- `CLAUDE.md`: the dev group's package entries now name pedalboard; nothing else it describes
  changed (no gate file did).
- `pyproject.toml`'s header and the comments over `[project.optional-dependencies]` and the dev
  group: the extra, numpy beside it, and the dev pin, with their reasons.
- `agent-os/product/tech-stack.md`: the pedalboard line. `mission.md`: its second bullet, the map
  and its unit conversions, is now true and needs no change.
- Module docstrings: `__init__.py` (what is re-exported, and that `host` and `census` are never
  imported by the package), `preset.py` (`tuning`, the derived key list), `format.py` (`tuning`),
  `errors.py` (the new root and branches), and each new module's.
- `agent-os/standards/vital/`: the standards this spec changed, in the retrospective below.

**Version (step 8):** `CHANGELOG.md`, `[Unreleased]`: under `### Added`, the host and the map with
the extra, the codec, the map and its generator, `tuning` and the plugin tests; under
`### Changed`, the error root. The version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff, each rule verified against the module and test
it names and against no text of this spec's plan.

1. **A pattern no standard covers:** several, the first spec about hosting. Sorted below.
2. **A standard wrong or stale:** `vital/preset-file.md` said the key list was "deliberately plain:
   the two-namespace map makes it structured"; the map now exists and the list is derived from it.
   Corrected. Probe 4's "every value comes back exactly" (Decision 6) was wrong at `volume`'s floor;
   corrected in Decision 6 and stated in `vital/parameter-map.md`.
3. **A deliberate deviation:** `host.py`'s private protocols hold settable properties, where
   `base/python/typing.md` makes a protocol's data members read-only properties: they describe
   pedalboard's runtime surface its stubs omit, not an API this package takes. Proposed upstream
   below rather than kept as a silent exception. Decision 4 departs from the issue's wording, and
   says so there.
4. **A pointer moved:** none; `settings_keys.txt` stays where `preset.py` reads it.

**Which side each rule fell on, and why.** The test: would a second adapter, for an instrument that
is not Vital, need this rule?

| Rule | Side | Why |
|---|---|---|
| The map measured by a census and committed as data; ids are preset keys | `vital/parameter-map` | Vital's parameters and keys; another plugin's census measures other things |
| Linear or indexed in exact float32 by a fused multiply-add; six curves; the suffix table | `vital/parameter-map` | What Vital's build and display do |
| Switches, choices by name, told apart by index; a choice's index from the scale's minimum | `vital/parameter-map` | Vital's parameter kinds |
| The state's three containers, our codec; `tuning` as an unread section | `vital/plugin-state`, `vital/preset-file` | Vital's (JUCE's) state layout |
| What a load does: upgrade, sample delay, re-quantize, snap; so never read back as the patch | `vital/plugin-state` | Vital's behaviour; the instrument's rule is issue #8's |
| pedalboard's parameters through its mapping; a render's half sample | `vital/plugin-state` | pedalboard with Vital |
| Measures with named tolerances from their probes | `vital/measures` | Vital's audio; the general rule may follow when a second adapter renders |
| Protocol failures on both the root and core's error | upstream, `base/python/errors` | Every adapter's errors meet core's contract tests |
| A dependency the licence cannot carry as an extra the root never imports | upstream, `base/python/toolchain` | Any adapter hosting through a GPL host |
| Native code in the test process keeps the floating-point environment | upstream, `base/testing/tests` | Any adapter that loads a plugin in-process |
| A private protocol for a third party's undeclared runtime surface | upstream, `base/python/typing` | Any adapter typing pedalboard, or a library with partial stubs |

Project standards changed, their own change set, listed apart when reported:

- `agent-os/standards/vital/parameter-map.md` — new: where the map comes from, the two
  conversions, units and kinds. Verified against `parameters.py`, `float32.py`, `census.py`,
  `tests/unit/test_parameters.py`, `test_census.py`, `test_float32.py` and
  `tests/integration/test_vital_plugin.py`.
- `agent-os/standards/vital/plugin-state.md` — new: the state, the process, a render. Verified
  against `state.py`, `host.py`, `tests/unit/test_state.py`, `test_host.py` and the integration
  tests.
- `agent-os/standards/vital/measures.md` — new: Decision 10 as a rule. Verified against the
  integration test's constants and `_variation`.
- `agent-os/standards/vital/preset-file.md` — the plugin state's `tuning`; the key list derived from
  the map. Verified against `preset.py`, `format.py`, `test_format.py` and `test_parameters.py`.
- `agent-os/standards/vital/preset-tests.md` — the hosted plugin's tests and what of the plugin is
  committed. Verified against `test_vital_plugin.py` and `data/parameters.json`.
- `agent-os/standards/index.yml` — the `vital:` section: three entries added, two descriptions
  changed; the `base:` section is the sync's and unchanged.

Proposals sent upstream: fromtheoutfit/patchbay-standards#34

### Standards retrospective (proposed, base)

- `base/python/errors.md` — a failure core's protocol names is raised as an adapter error deriving
  from both the adapter's root and core's matching error, so a caller holding core's types, its
  contract tests among them, catches it and the one-root rule holds. Verified against
  `src/patchbay_vital/errors.py` (`UnknownParameterError`, `ParameterRangeError`) and
  `tests/unit/test_errors.py` (`test_a_protocol_failure_is_core_s_error_too`). Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#34.
- `base/python/toolchain.md` ("Dependencies") — a dependency whose licence the package's cannot
  carry joins as an optional extra, imported by one module the root never imports, held by a test
  that a fresh interpreter with it blocked imports the package, and pinned at the extra's floor in
  the dev group so the gate installs it with no gate file changed. Verified against `pyproject.toml`
  and `tests/unit/test_package.py` (`test_pedalboard_is_declared_only_under_the_host_extra`,
  `test_importing_the_package_loads_no_pedalboard`). Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#34.
- `base/testing/tests.md` — an adapter that loads native code into the test process keeps the
  process's floating-point environment across each call into it, held by a test that subnormals
  survive a load and a render: a plugin built with fast-math leaves flush-to-zero on, and every
  later test in the process computes under it. Verified against `src/patchbay_vital/host.py`
  (`_environment_kept`), `test_the_process_keeps_its_floating_point_environment` and
  `verification/float-environment.txt`. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#34.
- `base/python/typing.md` — a private protocol may describe a third party's runtime surface its
  stubs omit, settable properties included, the object cast to it once where it is made; the
  read-only rule stays for protocols a package's API takes. Verified against
  `src/patchbay_vital/host.py` (`_HostedPlugin`, `_HostedParameter`) and the gate's mypy step.
  Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#34.

### Proposed to patchbay-core (Decision 12)

- `Instrument.get`'s documentation says it returns the nearest value the parameter holds, so a
  value set off the parameter's resolution comes back as that, not as given; the contract tests set
  bounds only, which hold exactly. Evidence: probe 4 (`verification/probes.txt`) and
  `tests/unit/test_parameters.py` (`test_a_value_the_parameter_holds_comes_back_exactly`). Approved
  by the owner, 2026-11-09; filed as fromtheoutfit/patchbay#18.
