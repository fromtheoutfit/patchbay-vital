# Issue #8 — the instrument: `VitalInstrument` over `VitalHost`

Shaped 2026-11-15 in plan mode with this repository's `/agent-os:shape-spec`. The owner answered
the Step 2 to 5 questions and twenty decisions in six rounds; every answer is in the appendix,
in the owner's words, for `shape.md`.

## Context

Issue #8 (Spec B of #7, https://github.com/fromtheoutfit/patchbay-vital/issues/8) makes
`patchbay_vital` a real `patchbay.Instrument`: `VitalInstrument` over `VitalHost` and the
parameter map, a `VitalPreset` carried in a core `Patch`, MIDI built as bytes, core's three
events on an injected bus, the `patchbay.instruments` entry point, and core's thirteen
`CONTRACT_TESTS` passing against a real Vital. Then drafts go to the owner for
fromtheoutfit/patchbay: a patchbay-core 0.1.0 proposal citing the local gate run and core's
`eddba95`, and three things the build found core does not say.

The issue's "Revised" paragraphs are history. Where they differ from the tree (`e3e6017`), the
tree and the standards are the present, and `shape.md` says so each time: `to_preset` always
returns a held preset (#16); `to_normalized(display)` is `scale.to_normalized(to_preset(display))`
(#13, #15); 344,580 of `volume`'s 23,726,567 doubles at its floor map one double off; core is
pinned at `eddba95`; mido is not used.

Branch: `feature/8-the-instrument-...` (current, clean). No stage, commit, push or pull request
by an agent. No gate file changes: if anything in `[tool.*]`, the harness or CI would have to
change, stop, that is a gate spec first.

## What was checked while shaping (read only, in memory, nothing written)

- **Core at `eddba95` reads no entry point**; adapter discovery is in its contracts spec's
  "Deferred". It shows an instrument built one way: `FakeInstrument(bus)`.
- **Bounds come back exactly, 1,806 of 1,806**, on all 903 records, through the set path and
  through the curve alone; every record's default display is its `parameter.default`. No record
  has one bound; none has unit `ratio`. Kinds 581, 243, 79; 448 slot ids.
- **`parameters()[0]` is `beats_per_minute`; the last id sorted is `volume`.**
- **The 29 indexed continuous records:** 27 whole numbers; `chorus_voices` 4 to 16 in fours
  (multiply 4); `oversampling` 1, 2, 4, 8 (exponential).
- **The fixture** (`tests/data/init-media-replaced.vital`): its 903 floats are exactly the map's
  `preset_default`, 903 of 903; 22 are floats the scale does not hold, and on all 22 a set of the
  display shown holds a preset that shows another. Its media are this repository's own: a sine
  wavetable three times, two-point LFO and warp lines, a 16-sample ramp.
- **The 75 installed presets, 57,671 floats:** 2,201 off the host's grid, in all 75, each moving
  on a set of its own display; 32 outside the scale in 26 presets (`flanger_dry_wet` 26,
  `flanger_center` 3, three `compressor_*_upper_ratio` 1 each); `chorus_damping`, no parameter,
  in 3; 10,057 parameter keys absent. On every float inside its scale the curve's inverse gives
  the float back, 0 failures. Sections: `lfos`, `sample`, `wavetables` only.
- **Core's fake renders zero samples:** at 23,040,000 bpm, 4 beats, 48 kHz, no tail it returns
  shape `(1, 0)`, `audio_seconds` 0.0 and one `RenderCompleted`; a `(2, 0)` `RenderResult`
  validates. No contract test covers it. A note-on can fall on the render's length (96,000 of
  96,000).
- **The negative harness** copies `src/` and `tests/`, so it is rerun. No case rests on a count
  of files. Case q writes `tests/unit/conftest.py`: this spec adds no `conftest.py` anywhere.
  Its last transcript holds 33 pytest runs summing 1,036 s and 118 syncs.
- **On file from the host spec:** 2 s at 48 kHz renders in about 80 ms; a load 1.20 s plus
  1.12 s for pedalboard's mapping; the transient peaks at 0.022 (0.0225 on a second render), last
  non-zero sample 4,869; `chorus_feedback`'s off-grid default, loaded once after a host set, is
  held two float32 steps off and loaded twice as given; "a fresh instance differs from the first
  at: ['sample']". The gate today: 534 tests, 33 s.

## Decisions

1. **Scope is issue #8, body and comment**, and nothing beside it. Its owner's Decisions 1 to 5
   (2026-11-09) stand. Each stale sentence is named in `shape.md` with what the tree says.
2. **The starting preset is one the package ships**, `src/patchbay_vital/data/start.vital`,
   loaded into the plugin at construction. The plugin's state never becomes the model.
   - Floats: the map's 903 `preset_default`. Slots: 64 empty. `synth_version`: the map's.
   - Media of the package's own, each rebuilt from its formula in a test: a 2,048-sample ramp
     `i / 1024 - 1` as each oscillator's wavetable (exact in float32, no libm), two-point lines
     for the LFO and warp shapes, a 16-sample ramp as the sample.
   - The census writes it as its third file, beside the map and the key list, all renamed
     together or none; one test checks all three so they cannot drift.
   - The licence call is the owner's, dated 2026-11-15, not legal advice, revisited before any
     PyPI release, recorded beside the pedalboard decision: the file holds Vital's default values
     (already shipped in `data/parameters.json`) and media generated by this package, none of
     Vital's presets, wavetables, samples or LFO shapes.
   - README says the instrument starts on this preset and not on Vital's own Init, and why.
3. **Patch layout: all 903 in `values`, a float in exactly one place.**
   - `values[id]` is the display of the preset's own float, for every parameter the preset holds
     a float for, slot floats included. A key the preset lacks is left out and reads as its
     default.
   - A float goes to `values` only if, checked for that float when `patch()` is built, its
     display passes `Parameter.check` and converts back to the same float, sign of zero included.
     Back means: on a linear scale the curve's inverse kept within the scale's ends; on an
     indexed scale `record.to_preset`. Any other float rides in `opaque["preset"]` as itself:
     the 32 out-of-range floats, `chorus_damping`, and any float the check fails.
   - `opaque` keys: `preset` (small JSON: metadata strings, 64 sources and destinations,
     `trailing_newline`, the carried floats), `settings.<name>` (each unread section's text),
     `line_mapping.<slot>`, `tuning`. Any other key is refused, naming it.
   - `load_patch` refuses a patch carrying one parameter in both places, naming the key.
4. **A values-only patch is laid over the start preset**: its sections, routing and metadata,
   every parameter left out at the start's value. Section entries without a `preset` entry are
   refused. Documented on `load_patch`; held by our own tests.
5. **Out-of-range floats are kept out of `values`** (Decision 3's rule). `get` returns the true
   display; `set` refuses it; a set of an in-range value brings the parameter into `values`.
   `patch()`'s docstring says so.
6. **Finding 1: Vital's rounding.** `set` stores `record.to_preset(display)` and sends
   `scale.to_normalized` of it. The nearer held neighbour is declined: a second rule beside the
   map's, or a recount of the map. Issue #8's body is revised in place to say so.
7. **Finding 3: a set of the display already shown keeps the stored preset.** Model and plugin
   untouched; one `ParameterChanged`, old equal to new. One case is left and is held, counted and
   put to core (Task 9): a loaded off-grid float, set back after another value was set, holds the
   neighbour.
8. **Finding 4: a value between steps is taken and the nearest step held**, a half away from
   zero, on `set` and on `load_patch`. A note for the semantics-data spec, not a change here: the
   29 parameters and their steps are not visible in core's `Parameter`; a step field upstream
   waits for a second adapter.
9. **Names and registration.** `name` is `"Vital"`. `VitalInstrument(bus, host=None)`.
   `[project.entry-points."patchbay.instruments"] vital = "patchbay_vital.instrument:VitalInstrument"`.
   CHANGELOG and README call the entry point provisional until core states the group's contract.
10. **Errors, in `errors.py`:** `ParameterUnitError(VitalError, UnitMismatchError)`,
    `PatchRefusedError(VitalError, PatchRejectedError)`,
    `RenderRefusedError(VitalError, RenderFailedError)`. Core's `Parameter.check` errors are
    re-raised as the package's with core's exact fields, the original as `__cause__`.
    A refused patch names the first key that refused it, in this order: the instrument's name;
    `opaque` keys sorted; `values` sorted by id (unknown id, in both places, unit, range); the
    preset's own validation.
11. **Events.** Checks, then the plugin, then the model, then one event. `ParameterChanged` after
    a set; `PatchLoaded` after a load, `parameter_count` the number of values in the patch given;
    `RenderCompleted` carrying the result's own three values. Source `"Vital"`, a fresh
    correlation id. A refused call publishes nothing and leaves model and plugin as they were.
    Construction publishes nothing.
12. **Render.**
    - Limits, named constants with their source: `MAX_SAMPLES = 2**24` (this spec's probe),
      rate 1,000 to 768,000 Hz (the host spec's probes). The error names the limit and its value.
    - Zero samples: an empty `(2, 0)` result, one `RenderCompleted`, the host not called.
    - Clipping: one warning when any sample is at or past `FULL_SCALE = 1.0`, the whole render,
      its text giving the peak and where. The audio is never clipped here. The rule rests on
      the probe (Task 3) and is not relied on before the owner has seen it.
    - MIDI (`midi.py`): core's `Note` already carries MIDI integers (pitch 0 to 127, velocity 1
      to 127, channel 0 to 15), so no byte is scaled and no velocity can be 0. Note-on
      `0x90 | channel, pitch, velocity`; note-off `0x80 | channel, pitch, 0`. Times from
      `sample_at`. Order on one sample: offs of notes begun earlier, ons, the off of a note that
      begins and ends there. Core's fake is the reference at the edges: a note whose on falls at
      or past the render's length is left out whole; an off at or past it is left out. Whether
      the time sent is `n / rate` or half a sample past is the probe's to decide.
    - `elapsed_seconds`: `time.perf_counter()` around the whole call.
13. **The contract tests run twice, each named for what it runs against:**
    `test_contract_against_vital` (integration, one Vital a module) and
    `test_contract_against_a_fake_plugin` (unit, a real `VitalHost` on a fake plugin, so CI runs
    them). All thirteen are expected to pass as written. One more transcript runs them with a
    fresh `VitalHost` per test.
14. **The centroid test**: Decision in Task 7.
15. **One new project standard, `vital/instrument.md`**, written in the retrospective from the
    shipped code; four existing ones corrected; rules that are any adapter's presented as base
    proposals.
16. **Modules.** New: `midi.py`, `patch.py`, `start.py` (pure) and `instrument.py` (host extra).
    Changed: `errors.py`, `census.py`, `__init__.py`. Not touched: `host.py`, `format.py`,
    `preset.py`, `parameters.py`, so no count of the map is owed again.
    Import direction: `errors` ← `preset` ← `parameters`, `format` ← `start` ← `patch`;
    `midi` imports core alone; `host` ← `census` (which now imports `start`); `instrument`
    imports `host`, `patch`, `midi`, `start`. The root imports neither `host`, `census` nor
    `instrument`.
17. **No dependency is added.** `instrument.py` imports numpy, already in the `host` extra.
18. **Evidence.** A claim over values that can be enumerated is counted; one that cannot is a
    labelled sample. A test's expected value shares no code with the method it holds. Every
    audio assertion is a measure with a named tolerance and its probe. Each transcript prints its
    tree and the machine before and after and embeds its script.

## Tasks

### Task 1: Save the spec documentation

`agent-os/specs/2026-11-15-<HHMM>-the-instrument/`: `plan.md` (this plan), `shape.md` (first
Decision cites issue #8; the answers in the owner's words; each stale sentence of the issue),
`standards.md` (the core five; `base/testing/tests`, `base/python/events`,
`base/process/verification-gate`, `standards-retrospective`, `standards-index`, `ownership`;
`vital/plugin-state`, `measures`, `parameter-map`, `preset-file`, `preset-tests`),
`references.md` (core's fake and conftest; `test_vital_plugin.py`; `test_host.py`'s fake plugin;
the last spec folder; the host spec's probes). No visuals.

Then revise issue #8's body in place with a "Revised 2026-11-15" paragraph, no attribution:
finding 1 is decided as Vital's rounding, the nearer neighbour declined and why, and findings 2
to 4 are decided in this spec's `shape.md`. Read it back.

### Task 2: Errors, the start preset, the census (gate green after each module)

- `errors.py`: the three errors; `tests/unit/test_errors.py` gains their fields, args, pickling
  and bases.
- `start.py`: `build_start(map)` and `start_preset()`; `data/start.vital` written from it.
  `tests/unit/test_start.py`: 903 floats equal the map's defaults; each media section rebuilt
  from its formula in the test; byte-for-byte through `loads` and `dumps`.
- `census.py`: `main` writes three files through `replace_files`; `tests/unit/test_census.py`
  follows. `test_vital_plugin.py`'s census test checks all three in one test.

### Task 3: Probes on Vital, then stop and present

`verification/probes.txt`, recording the machine and pedalboard's and Vital's versions:

- the sample a MIDI time lands on, `n / rate` against half a sample either side, by the first
  non-zero sample after the transient, at 7, 100,003 and others;
- one render of exactly 2**24 samples: time taken, every sample finite;
- what Vital gives past full scale;
- the transient's peak with `volume` at its maximum and on each of the 75 installed presets;
- what a load the plugin refuses, or cannot use, leaves in the plugin;
- single against double load after host sets, on all 22 off-grid defaults;
- centroids at the two cutoffs, ten renders each on two instances, each with its RMS and peak.

**Stop:** present the results before the clipping rule, the refused-load rule and the MIDI time
rest on them. A transient reaching full scale on any preset, a 2**24 render Vital does not give,
or a refused load that leaves the plugin partly changed with no way back: stop and present.
If a refused load can leave the plugin changed, the instrument reloads the model's text before
raising, and the docstring says so.

### Task 4: The carrying and the MIDI builder

- `patch.py`: `patch_of(preset)`, `preset_of(patch)`. `tests/unit/test_patch.py`: the two rules
  of Decision 3; a float inside its scale that fails the check (found from primitives, at
  `volume`'s floor) goes to `opaque`; `-0.0`; a key in both refused by name; each refusal's
  first key; a values-only patch; `dumps(preset_of(patch_of(x)))` equal to `x`'s text over
  built presets and through JSON.
- `tests/integration/test_factory_round_trip.py`: each manifest preset comes back byte for byte
  through a patch.
- `midi.py`: `midi_of(pattern, request)`. `tests/unit/test_midi.py`: expected bytes written out;
  channel and velocity; the order on one sample; a note on, and a note off, at or past the
  length; times from `Fraction`.

### Task 5: The instrument

`instrument.py`: `VitalInstrument` with `name`, `host` (the diagnostic read), `preset` (the
model), `parameters`, `get`, `set`, `load_patch`, `patch`, `render`, and the constants of
Decision 12. Docstrings carry what the owner asked for on `set`, `load_patch`, `patch` and the
errors that leave each call.

`tests/unit/test_instrument.py`, over a real `VitalHost` on a fake plugin hosting all 903:

- `test_contract_against_a_fake_plugin`, thirteen cases;
- every refusal path raises under `VitalError`, with core's fields field for field and the
  original as `__cause__`;
- finding 1 at `beats_per_minute` 216.85141355537831, expected from primitives;
- the keep rule on the 22 off-grid defaults; the characterization test of the case it leaves,
  naming the drafted core issue;
- steps: `chorus_voices` 6 holds 8 and 5 holds 4; `oversampling` 3 holds 4;
- `flanger_dry_wet` at 0.7072: `get` 141.44, `set` of it refused, `patch()` then `load_patch`
  the same model, after `set(50 %)` in `values` and gone from `opaque`;
- a patch refused part way, and a plugin that refuses after the checks pass: model, plugin
  (through the diagnostic read) and events as they were;
- `PatchLoaded.parameter_count` for a full patch, a values-only one and one with floats in
  `opaque`;
- each render refusal publishing nothing; zero samples; a render that clips gives exactly one
  warning and a `RenderCompleted` carrying it; a render of no notes gives none.

### Task 6: Registration and the package surface

`pyproject.toml` `[project.entry-points]` (the package's section; `uv.lock` checked unchanged,
else stop). `__init__.py` re-exports the three errors, `patch_of`, `preset_of`, `start_preset`.
`tests/unit/test_package.py`: the installed entry point is that string and loads the class; the
root import still loads no pedalboard, extended to `midi`, `patch` and `start`; the re-exported
names in the public-surface test. `verification/wheel-contents.txt`: the wheel's
`entry_points.txt` and `data/start.vital`.

### Task 7: Against the installed Vital

`tests/integration/test_vital_instrument.py`, its own module-scoped Vital, skipping by name with
no Vital or on another machine; a new bus and instrument per test, the start text loaded once
before the constructor loads it again.

- `test_contract_against_vital`, thirteen cases.
- The next instrument starts clean: after a test that sets all 903 and renders, the plugin's 903
  floats through the diagnostic read, and the model, are the start's.
- After a set at each bound of all 903, the plugin's float is the model's: 1,806 counted.
- Finding 1, the keep rule, the characterization and the steps, on Vital, plugin float included.
- For each installed preset: `dumps` of the model after `load_patch(patch())` equals the text
  loaded.
- A values-only patch that loads; a patch refused part way; the render's refusals, zero
  samples, the warning, a note left sounding not heard in the next render.
- **The centroid test.** `filter_1_on` 1, `filter_1_cutoff` at the displays of normalized 0.3
  and 0.8, one C4 held 1.5 s in a 2 s bar at 48 kHz. First each render is audible: RMS over the
  held note above a named floor. Then the high centroid over the low exceeds one named
  tolerance, half the smallest ratio the probe saw, its comment giving that ratio and the number
  of renders. The measure is the probe's computation, written once in the test module, guarding
  its own division. Nothing is shipped, which `shape.md` says of the mission's "No audio
  analysis".

`verification/contract-run.txt`: the thirteen on the shared instance with their times, and once
with a fresh `VitalHost` per test by a throwaway invocation embedded in the transcript; both
give the same thirteen passes.

### Task 8: Counts and mutants

- `verification/carrying-count.txt`: the fixture and the 75 presets, which floats took the
  `opaque` route, by key, and every preset byte for byte.
- `verification/off-grid-count.txt`: the 22 and the 2,201, with how far each display moves.
- `verification/mutation.txt`: scratch copies outside the tree, one mutant per decided rule,
  each failing a test by name.

### Task 9: Docs, Version, the drafts for core

- `README.md`: the instrument, its start preset and why, the provisional entry point, the
  layout. `agent-os/product/mission.md`: the one bullet the owner approved, third of four,
  nothing else under `agent-os/product/`. Docstrings and headers of the files changed.
- `CHANGELOG.md` `[Unreleased]`, `### Added`. The version stays 0.0.1.
- Drafted in `shape.md`, for fromtheoutfit/patchbay, presented together after the gate, filed
  only at the owner's word:
  1. `Instrument.get`'s "has returned": the clause, the case, the counts, candidate wordings
     with what each asks of `FakeInstrument` and the contract tests, and whether any contract
     test's meaning changes.
  2. The `patchbay.instruments` group: core defines nothing at `eddba95`; what this adapter
     registers; state it before 0.1.0 or mark it provisional.
  3. A render of zero samples: the docstring does not say, the fake does; say so in
     `Instrument.render` or add a contract test.
  4. The 0.1.0 proposal: thirteen contract tests pass against Vital 1.6.4 on this machine, the
     local gate run in `gate-run.txt` (CI has no Vital), core at `eddba95`, and one clause of
     `get`'s docstring met except in the case of draft 1.

### Task 10 (final): Verification gate

1. Standards retrospective drafted on a scratch copy and **presented** before it is made:
   `vital/instrument.md` (rules, each with the test that holds it, not the code restated),
   corrections to `vital/plugin-state`, `parameter-map`, `preset-tests`, `measures`, and
   `index.yml`'s `vital:` entries. Its own change set.
2. Base proposals **presented**, multi-select: the rules that are any adapter's, with this spec
   as evidence, checked against the open issues on `patchbay-standards` first.
3. `shape.md` records beforehand roughly how long the harness takes on this tree: 33 pytest runs
   at the measured step-5 time, plus about 8 minutes.
4. `scripts/gate-negative-tests.sh`, started without a further question once the tree is
   otherwise final: `verification/gate-negative-tests.txt`.
5. `scripts/gate.sh`, once, last: `verification/gate-run.txt` with date and branch.
   **If either is not clean: stop and present. No rerun to green; no saved Hypothesis example
   cleared.**
6. Docs, Version and the retrospective recorded in `shape.md`, in that order.
7. Present the four drafts for core together; file what the owner approves, and the approved
   base proposals, after the clean run; write the numbers into `shape.md`.
8. Stop and print `git status --short`, the retrospective's files listed apart from the
   feature's.

## Verification

- `scripts/gate.sh` exits 0, Vital installed, no test skipped; `gate-run.txt` shows the tree and
  the machine before and after.
- `uv run --locked pytest -c pyproject.toml -p no:doctest tests/integration/test_vital_instrument.py -v`
  shows the thirteen `test_contract_against_vital` cases passing.
- The harness transcript ends with its count and 0 unexpected.
- `git status --short` lists only this spec's files; nothing staged.

## Appendix: the owner's answers, verbatim

**Visuals:** "None (Recommended)".

**References:** all four: core's fake and conftest; `test_vital_plugin.py`; `test_host.py`'s
fake plugin; the last spec and the host probes.

**Product:** "2. The mission is the owner's text: present the changed sentence in "What the
adapter is", old beside new, before writing it, and change nothing else in agent-os/product/.
"No agent code" and "No audio analysis" stay as they read; shape.md says how the centroid test
keeps to the second (a measure computed inside a test, nothing shipped)."

**Standards:** "Include these (Recommended)".

**Patch layout:** "1. Two rules stated and tested:
- A float is carried in exactly one place. One that values can carry (inside its scale, and
  coming back exactly through the curve's inverse) is in values and not in opaque; one that
  cannot is in opaque["preset"] and not in values. load_patch refuses, by the package's
  PatchRejected error naming the key, a patch that carries the same parameter in both, and
  shape.md says which floats took the opaque route on the 75 presets, with the count.
- "Comes back exactly" is checked per float when patch() is built, not assumed from the count:
  the count covers the floats those presets hold, not every float a preset could hold. A
  float that fails the check goes to opaque, and a unit test holds one such value.
Also show, as a measure of the whole: for the fixture and each installed preset,
dumps(model after load_patch(patch())) equals the text loaded, byte for byte."

**Empty opaque:** "1, with one point presented before building: where the starting preset comes
from. "Read once at construction" from the plugin is the one place plugin state would become the
model, which Decision 1 otherwise forbids, and it makes a values-only patch mean whatever that
machine's Vital starts with. Say what the alternatives are (the plugin's own start read once and
stated as the single exception; or a preset the package ships and loads at construction, the
same on every machine) with what each costs, and recommend one. Whichever it is: the values-only
form is documented on load_patch, a values-only patch that loads is held by our own tests (the
contract tests never load a valid one), and a patch refused part way leaves model, plugin and
events exactly as they were."

**Out of range:** "1. Documented where a caller will look: patch()'s docstring says a parameter
whose stored value is outside its bounds is absent from values and carried in opaque, that get
still returns its true display, and that a set of an in-range value brings it into values from
then on. Tests hold each: on a preset with flanger_dry_wet at 0.7072, get returns 141.44, set of
141.44 is refused with the package's range error, patch() then load_patch gives the same model
back, and after set(50 %) the parameter is in values and gone from opaque. The 32 floats in
26 presets are recorded in shape.md as counted, with the transcript."

**Set rounding (finding 1):** "1. set's docstring says it in a sentence a caller can use: the
parameter then holds the value Vital holds for the display given, which get returns, and which
need not be the held value nearest it. The beats_per_minute example is held by a test, expected
value from primitives. shape.md records finding 1 as decided, with the nearer-neighbour option
declined and why, and issue #8's body is revised in place to say so."

**Start preset:** "1. Recorded and held:
- shape.md records the licence call as the owner's, dated, not legal advice, to revisit before
  any PyPI release, beside the pedalboard decision: the file holds Vital's default values
  (already shipped in data/parameters.json) and media generated by this package, none of
  Vital's presets, wavetables, samples or LFO shapes.
- Tests hold: all 903 floats equal the map's preset_default; every media section is
  reproduced from its formula in the test, so the committed file cannot drift from what the
  package says it is; and the file round-trips byte for byte through loads/dumps.
- The census regenerates or checks it, so a new Vital version cannot leave it stale silently,
  and the README says the instrument starts on this preset and not on Vital's own Init, and
  why."

**Keep on same (finding 3):** "1. And for the case it leaves:
- Hold it with a characterization test naming the core issue, per the standard: load an
  off-grid float, get, set another value, set the first back, and assert what is held, the
  expected value worked out from primitives.
- Count it on what can be counted: the 22 defaults and the 2,201 preset floats, with how far
  the display moves (one float32 step), in a transcript.
- Draft the fromtheoutfit/patchbay issue and present it, do not file: the clause as worded,
  the case, the counts, and the candidate wordings (for example "at the value get returns
  now, and at any value a set has left it holding") with what each would require of
  FakeInstrument and the contract tests. Say whether any contract test's meaning changes.
- The 0.1.0 proposal, when drafted, states this openly: the thirteen contract tests pass, and
  one clause of Instrument.get's docstring is met except in this case, with the issue's
  number. Do not file the 0.1.0 proposal until the owner has seen both drafts together."

**Between steps (finding 4):** "1. Held by tests at the uneven ones, expected values from
primitives: chorus_voices given 6 holds 8 (a tie, away from zero) and given 5 holds 4;
oversampling given 3 holds 4. get and ParameterChanged.new carry the step's display. set's and
load_patch's docstrings say a value between steps is taken and the nearest step held.
shape.md records, as a note for the semantics-data spec and not a change here: the 29 indexed
continuous parameters and their steps (27 whole numbers, chorus_voices in fours, oversampling
in powers of two) are not visible in core's Parameter; describing them belongs with the
per-parameter semantics, and a step field upstream is proposed only when a second adapter
needs one."

**Contract run:** "1, plus one transcript for the 0.1.0 evidence: the thirteen contract tests run
once with a fresh VitalHost per test, by a flag or a throwaway invocation, not as the gate's way,
kept in verification/ beside the shared-instance run, with both giving the same thirteen passes.
The test showing the next instrument starts clean compares the plugin's 903 floats read through
the diagnostic read, not the model alone. The two parametrizations are named for what they
run against, so nobody reads CI's pass over the fake plugin as a pass against Vital, and the
0.1.0 draft cites the local run with Vital's version and the machine."

**Render limit:** "1. The limits are named constants with a comment giving their source (the host
spec's probes for the rates, this spec's probe for the length), and the render error names which
limit was passed and its value. Tests hold each refusal publishing nothing and leaving the model
and plugin as they were. The 2 ** 24 probe's transcript records the machine, Vital's version, the
time taken and that every sample is finite. A render of zero samples being refused is checked
against core's contract first: say which contract test or docstring covers an empty pattern,
and if core expects an empty render to succeed, stop and present."

**Clipping:** "1. The probe's results decide whether the reasoning holds beyond the start preset,
so present them before relying on it: the transient's peak with volume at its maximum and on
each of the 75 installed presets, as a measure with the machine and Vital's version. If any
reaches full scale, stop, as proposed. The warning's text says what was measured (the peak and
where), the threshold is a named constant, and a test holds a render that does clip producing
exactly one warning and a RenderCompleted that carries it."

**MIDI:** "1. Two things said and tested in midi.py:
- Where the channel and the velocity byte come from: what core's Note carries for each, how a
  core velocity becomes 1..127 (and what a velocity that would round to 0 does, since a
  note-on of velocity 0 is a note-off to most receivers), and which channel is used if Note
  has none. Expected bytes in the unit tests are written out, not computed by the builder.
- A note whose start or end falls outside the render (before sample 0 or at or past the
  render's length): sent, clamped or left out, with core's fake as the reference, and a test
  for each.
The probe's transcript records the machine, pedalboard's and Vital's versions, and the sample
counts tried; the decision it leads to (exact time or half a sample past) is a Decision in
shape.md with the measurement cited."

**Registration:** "1, and the convention is put to core, not assumed: add to the drafts presented
with the 0.1.0 proposal a short section (or its own draft issue, whichever reads better) saying
core defines nothing for the "patchbay.instruments" group at eddba95, and what this adapter
registers: the key (lower-case, here "vital"), the object (a callable taking an EventBus and
returning an Instrument), and that loading it may need an optional extra. It asks core either to
state that as the group's contract before 0.1.0 or to mark the group provisional. Here, the
CHANGELOG and README call the entry point provisional until core says so. Present, do not
file."

**Zero samples:** "1. The empty result is built without calling the host, and a test holds that
the model, the plugin and the event stream apart from the one RenderCompleted are untouched. The
note for core in the drafts says what the docstring does not state and the fake does, and asks
core to either say so in Instrument.render or add a contract test for it, so the next adapter
does not have to read the fake to find out."

**Errors:** "1. The comparisons the contract tests make are met field for field, shown by the
tests: the re-raised error carries exactly core's fields and values (the parameter's own unit and
bounds, not the map's normalized ones), and the original is its __cause__. A refused patch names
the first key that refused it, and "first" is defined (the order values are checked in) so the
message is the same on every run. errors.md's rule that nothing but the package's errors
leaves a public method is held by a test that drives each refusal path and checks the type
raised is under VitalError."

**Events:** "1. Two points made explicit and tested:
- When the plugin refuses after the checks pass, the docstring says which error leaves the
  call and that it is under VitalError; and the test shows the plugin itself, read through the
  diagnostic read, is as it was, not only the model. If a refused load can leave the plugin
  partly changed, say so and what the instrument does about it (reload the model's text), or
  stop and present.
- PatchLoaded.parameter_count is defined in load_patch's docstring for each form: a full
  patch, a values-only patch laid over the start, and a patch whose out-of-range floats ride
  in opaque, each with a test."

**Centroid:** "1. Before comparing centroids, the test asserts each render is audible: its RMS
over the held note is above a named floor taken from the same probe, so a silent render fails by
name as silence and not as a centroid. The measure function guards its own division. The probe's
transcript records, beside every centroid, each render's RMS and peak, and the tolerance's
comment gives the smallest ratio seen and the number of renders it came from."

**Standard:** "1. Two requests for when it is drafted:
- It states rules, each with the test that holds it, and does not restate the code: a reader
  should be able to tell from it what a second Vital feature must not break.
- In the same retrospective, say which of its rules are not Vital's but any adapter's (for
  example: the model, not the device, is the source of truth; a contract run is named for what
  it runs against; a patch is refused whole) and present those as base proposals with this
  spec as the evidence, for the owner to approve or hold until a second adapter needs them."

**Mission:** "Add that bullet (Recommended)": "The instrument: Vital hosted and driven through
patchbay-core's Instrument contract. Its parameters are read and set in the units Vital
displays, a preset is loaded and given back as a patch, and a pattern is rendered to audio."

**Modules:** "1. Held by tests: the root import still loads no pedalboard, extended to midi,
patch and start; the public names the root re-exports are listed in the public-surface test; and
the census still regenerates the committed parameters.json and key list byte for byte, with
start.vital now the third file it writes, all three checked in one test so they cannot drift
apart. shape.md shows the import direction among the four new modules and the existing ones."

**Runs:** "2. The harness starts without a further question once the tree is otherwise final. If
it or the gate is not clean: stop and present; do not rerun to green and do not clear any saved
Hypothesis example. Say beforehand in shape.md roughly how long the harness takes on this
tree, so a run that goes far past it is noticed."
