# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The base standards under `agent-os/standards/base/` are pinned to the commit in `base/.version`;
a sync forward is recorded here by the sync's own commit, one entry naming the old commit and the
new as the sync's report gives them. The script writes no `CHANGELOG.md`: the person who syncs
writes the entry, in that commit
(`agent-os/standards/base/process/standards-sync.md`, "Pinned, not tracking").

## [Unreleased]

### Changed

- The `patchbay-core` pin and the `integration` marker, a gate spec, issue #11,
  `agent-os/specs/2026-11-11-1011-gate-core-pin-and-marker-needs/`. Landed before #8 resumes on top
  of it. The version stays 0.0.1.
  - `[tool.uv.sources]` takes `patchbay-core` at `eddba95`, the head of core's `main` carrying
    fromtheoutfit/patchbay#18 (`Instrument.get` says what an adapter relies on), where it took
    `dd2bcad`. Core is still 0.0.1, so the range is unchanged. `uv.lock` re-locked: patchbay-core's
    source moved and nothing else. The gate passes against it with no other change: nothing here
    builds an event or implements `Instrument` yet.
  - The `integration` marker says what its tests need: "an installed Vital, its plugin or its
    presets", where it named the presets alone and the plugin's tests carry it too.
  - Negative tests n and o match their pins whatever the value, as t already did, and o names the
    running uv as `uv --version` prints it. The work fromtheoutfit/patchbay-standards#31 left to
    this repository's next gate spec; `verification/guard-mutations.txt` shows both discriminate,
    and `verification/pin-moves.txt` shows both follow a moved pin.
- Revision after the third review of PR 9,
  `agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`: 12 findings at `d4fe077`,
  nine addressed, two declined with their reasons (the state's JSON decoded more than once, a third
  time; one guard around the load's four calls) and one acknowledged (standards edits in feature
  commits, the history left). The version stays 0.0.1.
  - `files.replace_files` reads only a file a later rename could force back, before any rename,
    so `dump` needs no read permission and reads nothing; each directory is flushed once, after
    every rename, as a best effort, never undoing or failing a replacement, and a flush that fails
    for a reason other than the file system's not supporting it is logged as a warning through
    the `patchbay_vital.files` logger.
  - `VitalHost.measure` puts each parameter back by its normalized value after its grid and loads
    the state measured from once, at the end, where it loaded it after every parameter. A state
    holding no settings object is `PluginStateError`, a normalized value that is no number or a
    bool `ParameterRangeError`, and a host id `display_texts` does not host
    `UnknownParameterError`.
  - The census refuses a key list that would forget a key the format knows, naming the keys to
    add to `PRESET_ONLY_KEYS`; the integration tests read a state's floats with the host's own
    helper.
- Revision after the second review of PR 9,
  `agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`: 17 findings at `0fc8152`,
  16 addressed and one, the state's JSON decoded more than once, declined again with its reason.
  The version stays 0.0.1.
  - `MachineMismatchError` is `MapMismatchError`, with `what`, `measured` and `found`: the host
    refuses the map on another machine, instrument or Vital version, naming the first that
    differs, where the map is first used; the package root exports it.
  - Every reach into the plugin is its own guarded call, nothing pedalboard raises leaving any of
    them, a refused restore in `measure` included; the Python work between calls runs in the
    process's own environment. The containers around the state are read once, at load, and every
    `load_state` reuses them; a render refuses a bool; a grid row with other keys is `CensusError`.
  - `NormalizedScale.span` and a record's displayed ends are computed by their values, so a copy
    with another bound is never stale; `_round_half_away`'s docstring says the grid lands on a
    half; `fit_scale` builds one scale; `preset.decode_end` is the one place deep nesting is
    turned into `ValueError`.
  - `files.replace_files` stages every file, then renames each over, putting an earlier one back
    when a later rename fails, and syncs the directory; the census writes both outputs through it.
  - The plugin's integration tests skip by name where the map was measured on another machine,
    and hold that a load changes no container.
- Revision after the review of PR 9, `agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`:
  24 findings at `eb95567`, 23 addressed and one, the state's JSON decoded more than once, declined
  with its reason. The version stays 0.0.1.
  - `MappedParameter.to_preset` rounds to a whole number on an indexed scale and refuses a
    non-whole value for a choice or a boolean; a record holds together in float32, so a libm an
    ulp apart still reads the map; `ParameterMap.machine` records where the census ran, and the
    host refuses the map on another machine with `MachineMismatchError`, where the map is first
    used.
  - The host keeps the floating-point environment around every call into the plugin, held by a
    unit test with a fake plugin; what pedalboard raises is `PluginStateError` or
    `PluginRenderError`, chained; `render` refuses a length or rate that is no whole number, asks
    one sample more and returns the first `samples`; `measure` restores the state however a read
    ends; the libraries are looked up lazily.
  - The state codec refuses a negative chunk size and a text nesting too deeply, as
    `PluginStateError`; `OpaqueChange.where` tells a section under `settings` named `tuning` from
    the top-level one.
  - The census refuses two parameters moving one preset value and a record the map's models
    refuse, by name; choice names made from an index never collide; both outputs are written
    whole or not at all, the key list first, through the new `files.replace_file`, which `dump`
    uses too.
  - Tests: the host's integration module loads Vital once; `tests/unit/test_files.py` is new.
- Revision after PR 9's CI run, `agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`: the host
  keeps the floating-point environment with `fegetenv` and `fesetenv` from the first library that
  holds both, glibc keeping them in its maths library. It had taken the C library, so on Linux a
  built-in `AttributeError` left `VitalHost()` and CI's unit suite failed. Unit tests that need no
  plugin hold the lookup and a save and restore of the environment, so CI runs them. The version
  stays 0.0.1.
- The package's error root is `VitalError`, with `VitalFormatError` under it beside the host's
  `VitalHostError` and the map's `UnknownParameterError` and `ParameterRangeError`, each of those
  two also core's matching error. The host spec,
  `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`.
- Revision after the review of PR 6, `agent-os/specs/2026-11-09-1610-revision-after-pr-6-review/`:
  sixteen findings at `6d7f747`, fifteen addressed and one, `json.decoder.WHITESPACE`, declined with
  its reason. The version stays 0.0.1.
  - `dump` writes a temporary file and renames it over the target, so a failure leaves the file as
    it was; a path `pathlib` refuses is `PresetFileError`.
  - `diff` compares floats as written, so `is_empty` means the two presets write the same bytes.
  - A preset can be pickled and deep-copied.
  - A lone surrogate is refused where it comes in; a section holding `NaN` or stray whitespace, a
    `null` name and text after the object are refused too.
  - A new key in a routing entry, and a non-float under an unknown name, are `UnknownSettingError`,
    naming the key, not `MalformedPresetError`.
- Revision after the review of PR 5, `agent-os/specs/2026-11-09-1433-revision-after-pr-5-review/`:
  all eleven findings of the review at `d638b39` addressed. The version stays 0.0.1.
  - `tests/unit/test_package.py` holds the pinned `patchbay-core` to the declared range, which uv
    does not check against a git source, and the names the adapter builds on to the pinned commit.
    `packaging==26.3` joins the dev group for it.
  - `scripts/gate.sh` step 2's reason names a locked package that could not be fetched.
  - Case t survives a pin move and covers a failed fetch and an unmet range; case y's marked test
    fails on purpose, so step 5 shows it ran. `verification/guard-mutations.txt` shows both
    discriminate.
  - The hosted run of the git source is recorded, and `CLAUDE.md` and `README.md` say what the gate
    owns, that `uv sync` calls git, and that the wheel installs only where `patchbay-core` resolves.
- Revision after the review of PR 3, `agent-os/specs/2026-11-09-1311-revision-after-pr-3-review/`:
  findings 1 to 8 and 15 of the review at `5dff391` fixed, 9's wording corrected, 9 proposed upstream
  (`fromtheoutfit/patchbay-standards#29`), 10 declined by the owner, 11 to 14 left. Findings that
  hold in patchbay too are `fromtheoutfit/patchbay#17`. The version stays 0.0.1.
  - `scripts/gate.sh` step 5 runs `pytest -c pyproject.toml -p no:doctest`, so a root `pytest.ini`,
    `.pytest.ini`, `pytest.toml` or `.pytest.toml`, tracked or ignored, cannot replace the test
    rules; the four filename refusals are gone, the `uv.toml` refusal stays.
  - `[tool.uv] python-preference = "only-managed"`: a local run and CI both use uv's own build of
    the interpreter, CPython 3.12.16 at this uv pin, where CI had taken the runner's 3.12.3.
  - Step 2 fails by name when uv warns it cannot use a key or value in `[tool.uv]`, where uv goes on
    without it and the gate passed.
  - `scripts/gate.sh` and the harness empty `CDPATH` for the `cd` to the repository root.
  - The pre-commit hooks read `pyproject.toml` alone (`--config`), as the gate does.
  - `tests/unit/test_package.py` exempts only the package's own submodules from the public surface.
  - The harness: q holds each of the four files, ignored and tracked; new cases w (`CDPATH`) and x
    (`python-preference`); j pins pyyaml. `verification/guard-mutations.txt`: each guard's mutation
    caught.
  - Docs: where uv puts the interpreter, what CI runs besides the gate, and that `CLAUDE.md` opens
    with `## Git`. The bootstrap spec records its hosted run, 42668230570.

### Added

- The host and the parameter map, the first half of issue #7,
  `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`; the instrument is issue #8.
  - `patchbay-vital[host]`: pedalboard (GPLv3) as an optional extra, `>=0.9.26,<1`, so the package
    stays MIT and installs without it; pinned `==0.9.26` in the dev group so the gate hosts Vital.
    `numpy>=2.5.4,<3` is declared in the extra beside it, `host.py` importing it.
  - `host.VitalHost`: loads Vital from a path or `/Library/Audio/Plug-Ins/VST3/Vital.vst3`, sets and
    reads parameters by preset key in normalized values, loads and reads the plugin's state as a
    preset's text, and renders MIDI to `(2, samples)` float32. It keeps the process's
    floating-point environment, which Vital otherwise leaves flushing subnormals to zero.
  - `state`: the VST3 preset, `VstW` and `CcnK` containers around the state's text, read and written
    byte for byte.
  - `parameters` and `data/parameters.json`: all 903 parameters by preset key, each with its
    normalized ↔ preset scale (linear or indexed, exact float32 with a fused multiply-add,
    `float32`) and its preset ↔ display curve in the plugin's own units, measured from the plugin.
    `census` is the generator that wrote it; `settings_keys.txt` is now derived from the map.
  - `VitalPreset.tuning`: the plugin state's top-level object, kept as its text like any unread
    section.
  - Integration tests against the installed plugin: the census regenerates the committed map, every
    installed preset loads as its state, and renders are measured.
- The `.vital` format, issue #2, `agent-os/specs/2026-11-09-1509-the-vital-format/`: `load`, `loads`,
  `dump`, `dumps` and `diff` over typed models on `PatchbayModel`, every section the package does not
  interpret kept as the file held it. `dumps(loads(text)) == text` on every one of the 75 presets
  Vital installs, held by an integration test against a committed manifest, floats written through
  a port of nlohmann::json's Grisu2 that matches the library on 1,286,646 compared values. `pydantic`
  joins the runtime dependencies. The first project standards, `agent-os/standards/vital/`. The
  version stays 0.0.1.
- `patchbay-core>=0.0.1,<1` as the first runtime dependency, taken from its public repository at
  `dd2bcad` by `[tool.uv.sources]`, and the `integration` pytest marker, for issue #2 to build on. A
  gate spec, issue #4, `agent-os/specs/2026-11-09-1405-gate-patchbay-core-source-and-marker/`;
  negative tests t and y. `uv.lock` adds six packages and moves no existing pin. The version stays
  0.0.1.
- sync base standards: e31f7dbfb474752339a43fe08a37ab26c7956f5c, the first sync. Written by the spec
  after it (`agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/`), since the sync's commit
  `fe84938` came before this file existed.

- First spec, `agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/` (issue #1): this repository
  becomes a patchbay repository, its second consuming project. Every departure from the issue's text
  and from patchbay is a Decision in the spec's `shape.md`. The version is 0.0.1.
  - `scripts/gate.sh`, `scripts/gate-negative-tests.sh` and `.github/workflows/gate.yml` from
    patchbay at `dd2bcad`, with this repository's paths. On top of that skeleton, as the issue
    names them: ruff and mypy told by flag to read `pyproject.toml` alone, a root `uv.toml` refused
    by name at step 2, and `-p no:doctest` on the pytest step.
  - The harness rebuilt for this repository: every step with its case and every guard with its
    mutation (`verification/guard-mutations.txt`), the CI replay, and case `v` for the guards that
    had no case. Its runs of the gate from patchbay's history are gone.
  - `pyproject.toml`: the toolchain standard applied, the ruff ignore list being what this tree's
    own first run gave. `.pre-commit-config.yaml`, registration only.
  - `src/patchbay_vital/__init__.py` holds `__version__` from the installed metadata and `__all__`;
    `tests/unit/test_version.py` and `test_package.py` hold them.
  - `.claude/commands/agent-os/shape-spec.md` customized for this repository's gate, `CLAUDE.md`,
    `README.md`, `agent-os/product/mission.md` and `tech-stack.md`.
  - `patchbay-core` is not a dependency yet: this spec ships no adapter code.
