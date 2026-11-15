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

- Revision after the review of PR 12, `agent-os/specs/2026-11-11-1321-revision-after-pr-12-review/`:
  all 15 findings of the review at `8ebce15` addressed, a gate spec. The version stays 0.0.1.
  - Cases n and o, and case t's two edits of patchbay-core's rev in `[tool.uv.sources]` (through
    `setrev`), edit their pins through one helper, `setline`. Each such edit is held to its pin's
    table, and a case stops by name when the table already holds the value it sets, or does not
    hold it after the edit. So n refuses `ruff===…` and a pin with an environment marker rather
    than rewriting it. Case t's third edit, of patchbay-core's range, does not go through `setline`:
    it is a `sed` over the whole of the copy's `pyproject.toml`, checked only by a `grep` that the
    new range is there.
  - Case o requires `==0.0.0`, a uv no release carries. It reads the version word of
    `uv --version`, the word after `uv `, and stops by name unless that word is a plain X.Y.Z; what
    follows the word is not checked. It prints `uv --version`'s whole output in a note, not a second
    run, so the harness has 140 runs.
  - `test_the_manifest_holds_the_expected_count` is unmarked: it reads only the committed manifest.
    The `integration` marker reads "needs Vital's plugin or its presets installed", and the comment
    over it names the parameter map's machine as the plugin's tests' second skip.
  - The pin's entry below names core's merge #16 beside #19. Each guard is shown to fire, and its
    absence not to, by a pair of runs kept one run to a file, as is the rest of the revision's
    evidence (`verification/`).
  - The harness's rerun drew a Hypothesis failure that was already on `main`: volume's round trip
    below 2 ** -43, at normalized 5.857149595214349e-20, filed as #13. Its fix, PR 14, is merged
    into this branch (`main` at `9474506`), and the revision's harness and gate transcripts are
    runs of that merge.
- The `patchbay-core` pin and the `integration` marker, a gate spec, issue #11,
  `agent-os/specs/2026-11-11-1011-gate-core-pin-and-marker-needs/`. Landed before #8 resumes on top
  of it. The version stays 0.0.1.
  - `[tool.uv.sources]` takes `patchbay-core` at `eddba95`, the head of core's `main`, where it took
    `dd2bcad`. That brings in core's two merges since: fromtheoutfit/patchbay#19, for issue
    fromtheoutfit/patchbay#18 (`Instrument.get` says what an adapter relies on), and
    fromtheoutfit/patchbay#16 (core's gate and `Event.at` revised after the review of its PR 15).
    Core is still 0.0.1, so the range is unchanged. `uv.lock` re-locked: patchbay-core's source
    moved and nothing else. The gate passes against it with no other change: nothing here builds an
    event or implements `Instrument` yet, so `Event.at`'s wider refusal reaches nothing.
  - The `integration` marker says what its tests need: "needs Vital's plugin or its presets
    installed", where it named the presets alone and the plugin's tests carry it too.
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

### Fixed

- `MappedParameter.to_preset` always returns a preset the plugin holds, issue #16,
  `agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`, revised after the review of
  patchbay-vital's PR 19, `agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`. For a
  display no held preset shows, an arbitrary one, it kept the curve's float32, which the scale
  need not hold, so a model that stored it disagreed with Vital's state after a set. The version
  stays 0.0.1.
  - **One rule with one exception replaces the three branches.** `to_preset` returns what a set
    of the display's float32 holds: the scale's value at its normalized value, Vital's own
    rounding. The exception is issue #15's, the float32 on the other side, taken where what a set
    holds does not show the display, that float32 does, and the scale holds it.
  - **What changes for a caller.**
    - An arbitrary display gives the held preset a set of it holds, which shows another display.
      `beats_per_minute` at 216.85141355537831 gives 3.6141905784606934, shown as
      216.8514347076416, where it gave 3.6141903400421143, which the scale does not hold.
    - The normalized value `to_normalized` sends is the same, so Vital holds what it held. Only
      the preset the map reports changes.
    - A display a held preset shows gives the same preset and normalized value as before.
  - **Sampled on arbitrary displays, which cannot be enumerated**
    (`verification/arbitrary-displays.txt`), each through `main`'s shipped methods and this
    branch's:
    - 200,000 displays a continuous group, uniform over its bounds
      (`numpy.random.default_rng(16)`), 11,000,000 over 55 groups: 2,041,885 give another preset,
      on 31 groups. On every one `main`'s preset was not held, the new one is, and the normalized
      value is the same. On 1,361,005 the new preset is the float32 next to `main`'s.
    - Of 20,000 over `volume`'s range, 1,085 change with `random.Random(8)` and 1,108 with
      `numpy.random.default_rng(8)`, the two figures issue #16 gives.
    - The double below and above a held display, at 2,034 normalized values a group that reach
      every exponent (seed 14), 223,740 displays: 61,284 are past a bound and refused by both
      trees, and of the other 162,456, 7 change, all `volume`'s.
  - **Counted where the doubles can be enumerated.** Of the 23,726,567 doubles from -80 to
    `volume`'s display at 2 ** -43, 344,580 give another preset. `main`'s showed the display
    exactly and was not held; the new one is held and shows a display one double away.
  - **Counted directly against `main` on the displays held presets show**
    (`verification/direct-count.txt`): `main`'s shipped methods and this branch's, each imported
    from its own tree and called on every float32 normalized value, nothing reproduced.
    - On `volume`, 1,065,353,217 values, the held preset, the display, the display's preset, the
      normalized value a set sends and the held preset's normalized value are `main`'s on every
      one. 15,761,472 take what a set holds and 308,386 the exception, the fifth review's counts;
      on none does what a set holds fail to show the display.
    - On `env_1_delay`, counted for the 12 envelope records, the display, its preset and its
      normalized value are `main`'s on every one of the 1,065,353,217 values. Only those two
      methods are called there: of the 48 functions and module values of `parameters.py` and
      `float32.py`, 46 have `main`'s statements, and no other call of the count reaches the two
      that differ.
    - A control with the exception removed moves 99,796 values of binade -56, so the counts are
      read from the result.
  - **The reproduction's sweep, rerun** (`verification/sweep.txt`): over every float32 normalized
    value of all 69 groups, each group's table is the fourth review's, and no value takes what a
    set holds where that does not show the display. It is a reproduction's count, checked against
    the shipped methods on 200,010 values a group with no mismatch.
  - **An indexed scale goes through the same path.** The nearest whole number is asked of the
    scale like any float32. On every whole number of the map's 351 indexed records the result is
    the whole number, as on `main`: 398,563 calls counted in full, over 21 distinct scales
    holding 371,476 whole numbers (`verification/indexed-count.txt`). On a scale wider than its
    float32s, which the map has none of, it is the nearest whole number the scale holds: from -1
    to 2 ** 24, the bound's display gives 16777215, where `main` gave 16777216, which no
    normalized value in [0, 1] lands on.
  - **`NormalizedScale.holds` answers False for a value outside what the scale's ends land on,**
    `to_preset(0.0)` and `to_preset(1.0)`, where it raised `OverflowError` or `ValueError`.
    - That covers an infinity and a NaN (the final review's finding 6), and a finite value too
      large for its quotient to be a float32, such as 3.5e38 on a scale from 0 to 1 (the review
      of patchbay-vital's PR 19, finding 1).
    - The check is against what the ends land on, not the bounds. On a made-up scale from
      -16777216 to 1.0000001192092896 the span rounds up, normalized 1 lands on 2, past the
      maximum, and `holds(2.0)` stays True.
    - Within what the ends land on, `holds` no longer tests the landing's normalized value
      against [0, 1]: a preset the landing reaches there is reached from [0, 1], by the landing's
      own test of its step and, for the nearest quotient, by rounding (the revision's shape.md,
      Decision 10).
    - A made-up record whose `to_preset` raised at infinity now returns the float32 below its
      maximum.
    - The scale's `to_normalized` and `to_preset` still raise a built-in on a value outside what
      the scale can take, finite or not, and a scale whose span overflows still validates. Both
      are left as they are, in issue #18. The finite case was found in the revision and sits
      there.
  - **Vital.** After a set of 200 seeded arbitrary displays on each of the 46 linear-scale
    groups, 9,200 sets, Vital 1.6.4 holds the map's preset on every one, and `main`'s on none of
    the 2,085 that changed (`verification/plugin-probe.txt`).
  - **The tests' expected values come from primitives** (the final review's findings 2 and 3).
    - `_what_a_set_holds` and the load test's expected value called the scale's `to_normalized`,
      so a `_landing` that kept a missed step passed the property and moved the load test's
      expected value with it.
    - Both now work from the float32 nearest the exact quotient, the forward scale and
      `next_float32`. The mutant fails the unit tests by name, and the load test no longer
      follows it (`verification/mutation.txt`).
  - **The pinned values gain a set of displays,** `tempo_displays`, in
    `tests/data/pinned-values.txt`.
    - `test_an_arbitrary_display_takes_what_a_set_of_it_holds` reverses
      `test_an_arbitrary_display_keeps_the_curve_s_float32`, issue #16's characterization, on
      purpose.
    - Two property tests hold any display in range, on the hand-built records and the committed
      map.
    - Each module's reader fails by name on an empty set and on a normalized value outside
      [0, 1]: the integration module's since the final review's finding 5, the unit module's
      since the review of patchbay-vital's PR 19 (finding 3). The integration module reads the
      file once in the test that read it once a record (finding 9).
  - **Cost** (`verification/cost.txt`, an Apple M4 Pro under macOS 26.6.2): on an indexed record
    `to_preset` costs about 15 µs a call against `main`'s 3.5, and `to_normalized` about 27 µs
    against 15,
    since the whole number is landed like any float32. `volume` is unchanged, about 16 and 28 µs,
    and the 903 records at their defaults take 14.8 ms against 13.2. No fast path is added. The
    final review's finding 8, `_landing` calling `fma32` itself rather than narrowing a value
    that is already a float32, is declined by the owner: it changes no value.
  - **Revised after the review of patchbay-vital's PR 19,** seven findings on `f26e6bc`; the
    transcripts named here are in the revision's `verification/`.
    - **Finding 1, fixed:** `holds` on a huge finite value, above. `holds` answers as it did
      before on every committed record, at 13,397 presets around the pinned values and 798,179
      indexed whole numbers, halves and values past each end, and no committed scale runs
      against the normalized value (`holds-check.txt`).
    - **The direct count stands.** `NormalizedScale.holds` is the only function whose statements
      differ from the tree the count ran on, and `to_preset` calls it only from its exception.
      The three binades of `volume` where the exception is taken were recounted against `main`:
      25,165,824 values, no difference, and the same 308,386 taking the exception
      (`direct-count.txt`).
    - **Finding 2, fixed:** the property's helper checks the exception both ways, so a
      `to_preset` without its exception fails the pinned-display test by name. The two
      Hypothesis properties still pass it: a display drawn over a parameter's bounds is not one
      a held preset shows.
    - **Finding 3, fixed:** the unit reader, above.
    - **Finding 4, fixed:** "the double above" a display steps toward infinity. No value the test
      uses changes, since its displays are negative.
    - **Findings 5 and 6, declined by the owner,** as the fast path was in PR 14's sixth review:
      `to_normalized` landing the preset twice, and indexed records paying for a landing.
      `cost.txt` records the timings with the machine. `holds` itself now costs 21 to 23 µs a
      call against 12, for the two forward calls of its check.
    - **Finding 7, not changed, and held by a test.** An indexed scale takes the exception too,
      from 2 ** 23 up, where float32s are whole numbers; the map's widest indexed scale ends at
      362,879. On a made-up record, an indexed scale from -2 ** 24 to 2 ** 24 under a linear
      curve of multiply 3 and offset 2 ** 54, the held 8388610 comes back only through it.
      Limited to linear scales, `to_preset` would give 8388612 there, which fails
      `test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display` by name.
  - **Left open.** Which held preset an arbitrary display takes, Vital's rounding as here or the
    nearer held neighbour, and whether a set keeps a stored value, are issue #8's findings 1 and
    3.
- The parameter map's two inverses, issue #15,
  `agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`, revised after the fourth,
  fifth and sixth reviews of PR 14,
  `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`,
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/` and
  `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`. Each missed a preset a set
  should hold, and Vital held what the map gave. The version stays 0.0.1.
  - **`NormalizedScale.to_normalized` takes the float32 one step toward the preset** where the
    nearest quotient misses it and that step, inside [0, 1], lands on it.
    - On the 12 `env_N_delay` and `env_N_hold` records, at 126 powers of two each from 2 ** -125
      to 1, the nearest quotient multiplied back one float32 short. So a set of 1.0 s held
      0.9999999403953552 on Vital, and now holds 1.0.
    - A step past [0, 1] is never taken. On a span of 2 ** 24 from -1, only the float32 above 1,
      which the host cannot set, lands on the maximum, so the maximum is not one the scale holds.
  - **`MappedParameter.to_preset`** handles a display whose curve float32 the scale does not hold.
    It takes what a set of that float32 holds, Vital's own rounding of it, where that shows the
    display. Otherwise it takes the float32 on its other side, where the scale holds it and it
    shows the display. Otherwise it kept the curve's float32, as before, until issue #16's fix
    above.
    - At or below `volume`'s 2 ** -43, presets share a display, and a set of a display now shows
      it again exactly.
    - On 15,761,472 of `volume`'s values a set holds what it held before, now the value
      `to_preset` gives.
    - On the 308,386 where that showed a display one double off, a set holds the float32 on the
      other side.
    - The two are tried in that order: where both show the display, the first is taken.
    - The float32 on the other side is asked of `NormalizedScale.holds`, so one past an end the
      scale does not hold is never taken.
    - A display no preset shows exactly kept the curve's float32, which need not be one the
      scale holds. The sixth review found that a model storing it disagrees with what Vital holds
      after a set; that is issue #16, fixed above, which makes `to_preset` return what a set of
      the display's float32 holds. Whether a set keeps a stored value is left to issue #8
      (finding 3).
  - **Written plainer after the sixth review, no value changed.** `to_preset` holds the rule
    itself, its first branch taking what a set of the curve's float32 holds where that is the
    float32 or shows the display; `MappedParameter.to_normalized` is the scale's own normalized
    value for `to_preset`'s preset, `main`'s form, and the private `_resolve` is gone. The second
    branch compares displays before it asks `holds`. Both trees' shipped methods, `e852aac`'s and
    the new one's, give the same `to_preset` and `to_normalized` on every float32 normalized value
    of `volume` below 2 ** -54, 612,368,384 values, and at the envelope group's 143 held powers of
    two from 2 ** -149 to 2, the 126 above among them (`verification/floor-pass.txt`); no other value can differ, by reading (the spec's shape.md,
    Decision 5). A call costs more than on `main`, measured on an Apple M4 Pro under macOS 26.6.2
    (`verification/cost.txt`): on `volume`, `to_preset` about 15 µs against `main`'s 3.5, and
    `to_normalized` about 27 µs against `main`'s 8 and `e852aac`'s 15, since it lands the
    preset `to_preset` landed once more; the 903 records at their defaults, 13 ms against
    `main`'s 4.2 and `e852aac`'s 8.9. No fast path is added (the sixth review's finding 5).
  - **New:** `NormalizedScale.holds` says whether the plugin can hold a preset value.
    `float32.next_float32` steps to the next float32 as C's `nextafterf` does, both of its
    arguments narrowed to float32 first. It is the one way the package steps a float32, and its
    tests check it against numpy's `nextafter`.
  - **Counted over every float32 normalized value of all 69 of the map's scale and curve groups,**
    the 9 exponential ones through this machine's own libm (macOS 26.6.2 on arm64)
    (`verification/sweep.txt`):
    - the display, the held preset and the display's preset come back exactly, and a set shows
      the display again, on every value;
    - no value reaches the rule's third branch.

    That count is a reproduction's, of the fourth review's revision: numpy for 60 groups, checked
    against the shipped methods on 200,010 values a group, of which 2,989 take `volume`'s first
    branch and 69 its second. Its two columns for what changed against `main` where `main`'s
    value was held were 0 by how the reproduction was built, and are evidence of nothing.
  - **Counted directly against `main`**
    (the fifth review's revision, `verification/direct-count.txt`): `main`'s shipped methods and
    this branch's, each imported from its own tree and called on every float32 normalized value,
    1,065,353,217 a record, nothing reproduced.
    - On `volume` the display's preset differs from `main`'s on 16,069,858 values, every one at
      a held preset at or below 2 ** -43, split value by value. The branch each takes is read
      from the shipped result: 15,761,472 the first, 308,386 the second, none the third. The
      normalized value a set sends differs on the 308,386 alone. No value above 2 ** -43 differs
      or leaves the curve's float32.
    - On `env_1_delay`, counted for the 12 envelope records, which share every field the methods
      read, the normalized value differs from `main`'s at 126 held powers of two and nowhere
      else, and no display's preset differs.
    - The other 67 groups are not counted directly, by the owner's decision at about 2.5 hours
      wall a group. What holds there that a value `main`'s
      quotient lands on is returned unchanged is a unit test,
      `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it`, which fails
      when `to_normalized` prefers the step (M15 in the fifth review's
      `verification/mutation.txt`), and the reproduction's count above.
  - **Vital and the tests.** Vital 1.6.4 holds the map's value at each pinned value after a set
    (`verification/plugin-probe.txt`). The sixth review's `verification/mutation.txt` shows the
    tests fail with each branch, guard and order changed, but for one order shown equivalent.
  - **The pinned values** are written once, in `tests/data/pinned-values.txt`, which both test
    modules read through `pytestconfig.rootpath`, so `test_the_integration_module_pins_the_same_values`
    and its reading of the integration module's source are gone.
    `test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset` and
    `test_a_held_power_of_two_set_through_the_host_is_held` hold Vital at them, and
    `test_every_pinned_value_comes_back_on_every_record` runs them through the property on every
    hand-built record, where issue #13's value was an `@example`: a decorator cannot read from
    pytest's root.
  - **The property's excuse names what a set holds** (the sixth review's finding 1). Where the
    display's preset is not the held one, `_unnamed_by_its_display` passes it only if the curve's
    own float32 for the display is not the held preset and the display's preset is what a set of
    that float32 holds, worked out from the scale's and the curve's primitives. It replaces
    `_shares_its_display`, which on a monotone curve held wherever the display's preset showed
    the display, and so let a wrong held preset through.
    - Counted on every float32 normalized value of `volume` with the shipped methods
      (`verification/floor-pass.txt`): 570,997,534 values ask it, every one below 2 ** -54 at a
      held preset at or below 2 ** -43, and on each the display's preset is what a set holds. No
      value at or above 2 ** -54 asks it.
    - On none is it the float32 on the other side, which `to_preset` takes in its second branch,
      so that is not excused: a record that needed it would fail the property. The hand-built
      records are not counted.
- The parameter map's property at or below `volume`'s floor, issue #13,
  `agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`, revised after the two
  reviews of PR 14, `agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
  `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`, and closed by issue #15's
  fix above. At normalized `5.857149595214349e-20` the display maps to a float32 the scale does not
  hold, so the second assertion of `_assert_comes_back`, the display's preset back through the
  normalized path, failed whenever Hypothesis drew it: on 16,069,858 of `volume`'s values counted,
  all at or below 2 ** -43. The map was wrong there, not the property.
  - `_assert_comes_back` asserts on every value, exactly, the display back, the held preset back
    through the normalized path and the display's preset back through it. The preset the display
    maps to is the held one, but where the float32 next to the held one, toward the preset the
    display maps to, shows its display (`_shares_its_display`, which issue #15's entry above says
    the sixth review replaced by `_unnamed_by_its_display`).
    - That is a value predicate, in place of `_ABSORBED`, which was keyed by a record's id.
    - It is consulted only where the exact check fails: on 570,997,534 values, all of `volume`'s,
      each excused.
    - The issue's value is pinned, an `@example` until the sixth review moved it to
      `tests/data/pinned-values.txt`.
