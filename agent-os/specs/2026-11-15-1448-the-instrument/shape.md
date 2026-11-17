# The Instrument: VitalInstrument over VitalHost (issue #8) — Shaping Notes

Shaped 2026-11-15 in plan mode with this repository's customized `/agent-os:shape-spec`, on
branch `feature/8-the-instrument-...` at `e3e6017`. The issue, the standards, the package and
core at its pinned commit were read whole before any question; what could be counted without the
plugin was counted, read only and in memory. The owner then answered the Step 2 to 5 questions
and twenty decisions in six rounds.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #8, https://github.com/fromtheoutfit/patchbay-vital/issues/8, body and comment: make
`patchbay_vital` a real `patchbay.Instrument`.

- `VitalInstrument` over `VitalHost` and the parameter map, reaching the plugin only through
  the host.
- A `VitalPreset` carried in a core `Patch` and back.
- The MIDI builder, bytes and seconds.
- Core's three events on an injected bus.
- The entry point in the `patchbay.instruments` group.
- Core's thirteen `CONTRACT_TESTS` against a real Vital, and a render whose spectral centroid
  moves with the cutoff.
- Drafts for fromtheoutfit/patchbay, presented to the owner: the patchbay-core 0.1.0 proposal
  and what the build found core does not say.

No gate file changes. No stage, commit, push or pull request by an agent.

## What was checked while shaping

Read only, in memory, against `e3e6017`; nothing was written.

- **Core at `eddba95` reads no entry point.** Adapter discovery is in its contracts spec's
  "Deferred". It shows an instrument built one way: `FakeInstrument(bus)`.
- **Bounds come back exactly, 1,806 of 1,806,** on all 903 records, through the set path
  (`to_display(to_preset(bound)) == bound`) and through the curve alone. Every record's default
  display is its `parameter.default`. No record has one bound, and none has unit `ratio`.
- **The map:** 581 continuous, 243 booleans, 79 choices; 552 linear scales and 351 indexed; 448
  slot ids, 64 of each of seven fields. `parameters()[0]` is `beats_per_minute`
  (20.000000596046448 to 300, default 120) and the last id sorted is `volume`.
- **The 29 indexed continuous records** are not all whole numbers: `chorus_voices` runs 4 to 16
  in fours (a linear curve of multiply 4), `oversampling` is 1, 2, 4, 8 (exponential), and the
  other 27 are whole.
- **The fixture, `tests/data/init-media-replaced.vital`, 903 floats:**
  - each is exactly the map's `preset_default`, 903 of 903;
  - 22 are floats the scale does not hold, off the host's grid;
  - on all 22 a set of the display the parameter shows holds a preset that shows another;
  - its media are this repository's own: one sine wavetable three times, two-point LFO and
    warp lines, a 16-sample ramp.
- **The 75 installed presets, 57,671 floats:**
  - 2,201 off the host's grid, in all 75 presets, each moving on a set of its own display;
  - 32 outside the scale, in 26 presets: `flanger_dry_wet` 26, `flanger_center` 3, and
    `compressor_band_upper_ratio`, `compressor_low_upper_ratio` and
    `compressor_high_upper_ratio` once each;
  - `chorus_damping`, which is no parameter, in 3;
  - 10,057 parameter keys absent, every file being 1.0.0 or older;
  - on every float inside its scale the curve's own inverse gives the float back,
    `curve.to_preset(to_display(p)) == p`, with 0 failures;
  - the sections are `lfos`, `sample` and `wavetables` and no other.
- **Core's fake renders zero samples.** Given 4 beats at 23,040,000 bpm and 48 kHz with no
  tail, `samples()` is 0 and `FakeInstrument` returns audio of shape `(1, 0)`, `audio_seconds`
  0.0, no warning, and one `RenderCompleted`. A `(2, 0)` `RenderResult` validates. No contract
  test covers it. A note-on can fall on the render's length: 96,000 of 96,000.
- **The negative harness** copies `src/` and `tests/`, so it is rerun. No case rests on a count
  of files. Case q writes `tests/unit/conftest.py`, so this spec adds no `conftest.py`: a second
  one is a duplicate module to mypy and would fail q before the step it expects.
- **On file from the host spec** (`verification/probes.txt` and `host-probes.txt`):
  - 2 s at 48 kHz renders in about 80 ms; a load takes 1.20 s and pedalboard's mapping 1.12 s;
  - the opening transient peaks at 0.022, 0.0225 on a second render, its last non-zero sample
    4,869;
  - `chorus_feedback`'s off-grid 0.4000000059604645, loaded once after a host set, is held as
    0.40000006556510925, and loaded twice as given;
  - "a fresh instance differs from the first at: ['sample']";
  - centroids 368 Hz and 2,298 Hz at cutoff 46.4 and 110.4 with filter 1 on.
- **The gate before this spec:** 534 tests in 33 s, Vital installed.

## Where the issue is stale

The issue's "Revised" paragraphs are a history. Where one differs from the tree, the merged tree
and the standards are the present.

| The issue says | The tree says |
|---|---|
| Below `volume`'s floor `to_preset`'s value is not one the scale holds, on 16,069,858 values | `to_preset` always returns a preset the scale holds (#15, #16) |
| A set of such a display comes back one double off on 308,386 values | A set of any display a parameter shows holds a preset that shows it, on all 69 groups (#15) |
| An arbitrary display keeps the curve's float32, held or not | It takes what a set of the display's float32 holds (#16); 344,580 of `volume`'s 23,726,567 doubles at its floor map one double off |
| "552 of 552 continuous" bounds exact | 581 records are continuous; all 1,806 bounds of the 903 come back exactly |
| `flanger_dry_wet` 0.7072 "in about 25 installed presets"; the ratios "clamped to 1.0 in two, kept in one" | 26 presets; one preset each, as the issue's own comment counts |
| Finding 3: at 2 ** -43 and 2 ** -45 the display comes back one double away | It comes back exactly since #15; what is left is the stored preset moving, and the wider case found here |
| "the centroid is 302 Hz at cutoff 46.4 and 2307 Hz at 110.4" | Those are Vital's own Init; the instrument starts on the package's preset, measured anew |
| "When they pass, file the issue on fromtheoutfit/patchbay" | The owner's answer of 2026-11-15: the drafts are presented together and filed at the owner's word |

Against the shaping prompt the issue wins, and they do not differ on the entry point's key or
the instrument's name.

## Shaping answers

In the owner's words.

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

## Decisions

1. **The scope is issue #8,** https://github.com/fromtheoutfit/patchbay-vital/issues/8, body
   and comment, and nothing beside it. Its owner's Decisions 1 to 5 of 2026-11-09 stand: the
   loaded `VitalPreset` is the source of truth; values are the plugin's display units; a
   `ParameterId` is Vital's preset key; measures, not samples; MIT, with pedalboard only through
   the `host` extra.
2. **The starting preset is one the package ships,** `src/patchbay_vital/data/start.vital`,
   loaded into the plugin at construction. The plugin's state never becomes the model, so
   Decision 1 of the issue has no exception.
   - Its floats are the map's 903 `preset_default`, its 64 slots are empty and its
     `synth_version` is the map's.
   - Its media are the package's own, each rebuilt from its formula in a test: a 2,048-sample
     ramp, `i / 1024 - 1`, as each oscillator's wavetable, exact in float32 with no libm;
     two-point lines for the LFO and warp shapes; a 16-sample ramp as the sample.
   - The census writes it as its third file, beside the map and the key list, all three renamed
     together or none, and one test checks all three.
   - The alternative, the plugin's own start read once, was declined: it is the one place
     plugin state would become the model, it makes a values-only patch mean whatever that
     Vital starts with, and two fresh instances already differ in `sample`.
3. **The licence call is the owner's,** made 2026-11-15, not legal advice, and revisited before
   any release to PyPI, beside the pedalboard decision of the host spec. `start.vital` holds
   Vital's default values, which `data/parameters.json` already ships, and media generated by
   this package. It holds none of Vital's presets, wavetables, samples or LFO shapes.
4. **Patch layout: all 903 in `values`, and a float in exactly one place.**
   - `values[id]` is the display of the preset's own float, for every parameter the preset
     holds a float for, the 448 slot floats included. A key the preset lacks is left out and
     reads as its default.
   - A float is in `values` only if, checked for that float when the patch is built, its
     display passes `Parameter.check` and converts back to the same float, the sign of a zero
     included. Back is the curve's inverse kept within the scale's ends on a linear scale, and
     `record.to_preset` on an indexed one.
   - Any other float rides in `opaque["preset"]` as the float itself and is not in `values`.
   - `opaque` holds `preset`, a small JSON entry of the metadata strings, the 64 sources and
     destinations, `trailing_newline` and the carried floats; `settings.<name>` for each unread
     section, the text the file held; `line_mapping.<slot>`; and `tuning`. Any other key is
     refused, naming it.
   - `load_patch` refuses a patch that carries one parameter in both places, naming the key.
5. **A values-only patch is laid over the start preset:** its sections, routing and metadata,
   with every parameter the patch leaves out at the start's value. Section entries without a
   `preset` entry are refused. Core's two contract tests that load a values-only patch are then
   refused for their bad entry alone.
6. **Out-of-range floats are kept out of `values`,** by Decision 4's rule. `get` returns the
   true display, `set` refuses it, and a set of an in-range value brings the parameter into
   `values` from then on.
7. **Finding 1: Vital's rounding.** `set` stores `record.to_preset(display)`, what a set of the
   display's float32 holds, and sends `scale.to_normalized` of it. The nearer held neighbour is
   declined: it would be a second rule beside the map's `to_preset`, so either the instrument
   and the map disagree on what a display maps to, or `to_preset` changes and its direct counts
   are owed again.
8. **Finding 3: a set of the display a parameter already shows keeps the stored preset.** Model
   and plugin are untouched, and one `ParameterChanged` is published with old equal to new. It
   is needed beyond `volume`'s floor: on the 22 off-grid defaults a set of the display shown
   would otherwise hold a neighbour. One case is left: a loaded off-grid float, set back after
   another value was set in between, holds the neighbour. It is held by a characterization
   test, counted, and put to core in a drafted issue.
9. **Finding 4: a value between steps is taken and the nearest step held,** a half away from
   zero, on `set` and on `load_patch`. Core says a continuous parameter takes any value in its
   bounds, and its whole-number fake rounds and passes all thirteen contract tests.
10. **The name is `"Vital"`,** the host's and the map's. `VitalInstrument(bus, host=None)`
    takes the bus as its one required argument, as core's fake does. The entry point is
    `vital = "patchbay_vital.instrument:VitalInstrument"` in
    `[project.entry-points."patchbay.instruments"]`. It is called provisional in the CHANGELOG
    and the README until core states the group's contract.
11. **Three dual-base errors:** `ParameterUnitError(VitalError, UnitMismatchError)`,
    `PatchRefusedError(VitalError, PatchRejectedError)` and
    `RenderRefusedError(VitalError, RenderFailedError)`. What `Parameter.check` raises is
    re-raised as the package's with core's exact fields, the original its `__cause__`.
12. **A refused patch names the first key that refused it,** in the order the patch is checked:
    the instrument's name; the `opaque` keys, sorted; the `values`, sorted by id, each for an
    unknown id, a key in both places, its unit and its range; then the preset's own validation.
13. **Events.** Everything is checked, then the plugin is called, then the model is replaced,
    then one event is published. A refused call publishes nothing and leaves model and plugin as
    they were. `PatchLoaded.parameter_count` is the number of values in the patch given.
    Construction publishes nothing.
14. **Render limits** are named constants with their source: `MAX_SAMPLES = 2**24`, from this
    spec's probe, and a rate from 1,000 to 768,000 Hz, the range the host spec measured.
15. **A render of zero samples returns an empty `(2, 0)` result** and one `RenderCompleted`, the
    host not called, as core's fake does.
16. **The clipping warning** is one warning when any sample is at or past `FULL_SCALE`, over
    the whole render, the transient included. The audio is never clipped by the instrument. The
    rule rests on the probe's results, which the owner sees before it is relied on.
17. **The MIDI builder** takes its bytes from core's `Note` as they are: pitch 0 to 127,
    velocity 1 to 127, channel 0 to 15, so no byte is scaled, no velocity is 0 and every note
    has a channel. Core's fake is the reference at the render's end: a note whose start falls
    at or past the render's length is left out whole, and an off at or past it is left out.
18. **The contract tests run twice, each named for what it runs against:**
    `test_contract_against_vital`, one Vital a module, and
    `test_contract_against_a_fake_plugin`, a real `VitalHost` on a fake plugin, which CI runs.
    A pass over the fake plugin is not a pass against Vital.
19. **One new project standard, `vital/instrument.md`,** written in the retrospective from the
    shipped code. The pattern is decided here, with the owner, and written then.
20. **Four new modules:** `midi.py`, `patch.py` and `start.py`, which need no plugin, and
    `instrument.py`, which needs the `host` extra. `host.py`, `format.py`, `preset.py` and
    `parameters.py` are not touched, so no count of the map is owed again.
21. **No dependency is added.** `instrument.py` imports numpy, which the `host` extra declares.
22. **No gate file changes, and no `conftest.py` is added.** The negative harness is rerun,
    since files are added under `src/` and `tests/`.
23. **A claim over values that can be enumerated is counted; one that cannot is a labelled
    sample.** A test's expected value shares no code with the method it holds. Every audio
    assertion is a measure with a named tolerance and the probe its number came from.

## What the probes showed

`verification/probes.txt` and `verification/probes-2.txt`, run 2026-11-15 on Vital 1.6.4 through
pedalboard 0.9.26 on arm64. A first run stalled at the first load Vital could not use and was
stopped; a second was made while a file was being added to the tree, and its own check said so;
the run kept is the third, on a still tree, each load Vital might not return from in a process of
its own.

- **A MIDI time is sent half a sample past its sample.** `(n + 0.5) / rate` lands on n at every
  value tried: 17 chosen, 5 of them past 12 million, and 120 drawn from 5,000 to 200,000. `n /
  rate` lands one sample early at 100,003, 1,000,003 and 4,000,001 and on 4 of the 120. A sample,
  not a count. No model of where pedalboard rounds was borne out: one that holds the time as a
  float32 predicted misses that did not happen.
- **2 ** 24 samples are given:** 16,777,216 samples at 48 kHz in 1.25 s, every sample finite.
- **Vital gives samples past full scale,** up to a ceiling of 2.1, and none held at 1.0. With
  `volume` at its maximum one C4 peaks at 1.43.
- **A render with no MIDI holds the preset's own sound, not a fixed transient.**
  - On the start preset: a peak of 0.017 to 0.021 over the transcript's renders, 0.074 with
    `volume` at its maximum, its last non-zero sample 4,889 at most. (Sections 7 and 7b print
    "4928 at most" in a sentence of the probe's own: that figure is an earlier run's, which was
    not kept, and no line of the kept transcript measures it.)
  - On the 75 installed presets: the largest peak as loaded is 2.1, the ceiling; one preset
    reaches full scale as loaded and 17 with `volume` at its maximum; 51 peak above the start
    preset's 0.02 and 28 above 0.1; 67 are still non-zero after 0.5 s, 32 stay at or above 0.001
    for a second or more, and 8 for 4 s or more.
  - It recurs at every render. On a fresh instance nothing was played on, Plucked String opens
    at 0.31 and decays over 2 s; Super Nice Pluck opens at 0.73 and is at 0.1 after 2 s.
  - It is larger with the reset `VitalHost.render` makes, and not absent without it: on a fresh
    instance, Plucked String peaks at 0.012 without a reset and 0.21 with one, Super Nice Pluck
    at 0.18 and 0.64, the start preset at 0.010 and 0.021.
- **Vital reports no load it cannot use.** Of 20 texts, each loaded in a process of its own:
  - 11 never returned. Vital puts up a modal alert and its caller waits for ever: the sampled
    process sits in AppKit's `NSAlert runModal` under Vital's
    `SynthProcessor::setStateInformation`. Each was killed after 6 s, by design.
  - Of those 11, the guard decided on refuses 4 the package's writer can write (no section at
    all, `wavetables` an object, `sample` an empty object, `synth_version` "abc"); 4 the writer
    cannot write, the models refusing them first (an empty object, empty `settings`, a string
    where a float belongs, `wavetables` a string); and 3 pass it, their fault being inside a
    section the package does not read (three wavetables whose `groups` is a number, eight lfos
    whose `points` is a string, a sample whose `length` is a string).
  - `synth_version` 99.0.0 is ignored whole, with no error and the plugin unchanged.
  - `wavetables` or `lfos` as an empty array loads the floats and keeps the sections the plugin
    had.
  - A key the text lacks goes to its default, 132 of 132; names Vital does not know as a
    routing's source and destination load.
- **One load is not enough, and two are, but for what Vital itself makes of an older preset.**
  After a set of every parameter and a render, counted on the start preset, the fixture and the
  75 installed presets:
  - one load leaves 17 to 53 of the 903 floats off the model on every text, 2,335 in all;
  - two loads leave none on 66 texts and 46 floats on 11;
  - a third load holds the same 903 as the second on all 77.
  - On the start preset and the fixture: 22 after one load, all of them the off-grid defaults,
    one or two float32 steps off, and 0 after two.
  - The 46 are Vital 1.6.4's own upgrade of a preset older than it, versions 0.6.1 to 1.0.0:
    29 are keys the text lacks set to other than the default (21 `lfo_N_smooth_mode`, seven on
    each of three presets, 0 where the default is 1; 3 `chorus_cutoff`, 20 where it is 60; 3
    `stereo_mode`; 2 `chorus_spread`); 3 are `flanger_center` moved into its range; 14 are
    floats inside their scale renumbered or rescaled (`osc_N_stack_style` one higher on 8: 9 to
    10 on 5, 10 to 11 on 2, 5 to 6 on 1; `filter_N_style` 1 to 0 on 2;
    `osc_3_spectral_morph_type` 10 to 7 on 2; two modulation amounts, each to 0.375 of itself).
  - The sample's 4-sample delay is counted from the text each time: one, two and three loads of
    one text hold the same sample, and only a load of the state read back adds 4 more.
- **The centroid, over the held note under a Hann window:** 320.56 Hz on all 20 renders at the
  low cutoff and 2,349.97 to 2,349.98 Hz on all 20 at the high one, on two instances; the
  smallest ratio 7.331 of 400 pairs; the smallest RMS 0.014134, and exactly 0 with no MIDI. Cut
  at sample 7,200 with no window, the low cutoff's centroid ran from 674 to 1,931 Hz and the
  smallest ratio was 1.19: the cut's own step is in that spectrum.
- **A note left sounding** at the end of one render is not heard in the next: its peak from
  sample 7,200 on is 0.
- **What a call costs:** a load of the start preset 4 ms, a get and a set of each of the 903
  parameters 55 ms in all, a read of the state 0.6 ms. A load of a 10 MB preset takes seconds.

## The owner's answers after the probes

Asked on 2026-11-15, in two rounds, once the probes had hit the stops set in shaping. In the
owner's words.

**A load Vital cannot use**, to "Guard what was measured": "1. With these additions:
- The transcript lists all 17 texts with what each did, and for the 8 that never returned,
  which the guard now refuses and which it cannot (and why not).
- The host issue is drafted and presented with the others, and it says plainly that until it
  lands a patch with a section Vital cannot read blocks the calling process forever, with the
  sample as evidence and the candidate remedies (a trial load in a child process; a watchdog).
  It asks one more question for that spec to answer: whether a load Vital silently ignores can
  be detected afterwards by a cheap check through the diagnostic read.
- It runs before the first agent experiment. Record that ordering in shape.md and in the
  README's known limits, in a sentence a user would understand: a malformed preset section
  can hang the process.
- The 0.1.0 draft states it too: core's "PatchRejectedError, changing nothing" holds for every
  patch the guard can judge, and not for a section Vital itself cannot read, with the host
  issue's number.
- No test may hang the gate: every load a test sends to Vital passes the guard first, and the
  probes that provoked the hangs stay as transcripts run in child processes with a timeout,
  never as tests."

The transcript kept lists 20 texts: the 17, and 3 added to show what passes the guard and
still blocks.

**The opening sound**, to "Keep the rule, file a host issue": "1. With these additions:
- The host issue is drafted and presented with the others: the measurements (peak as loaded
  and at maximum volume per preset, how long each sounds, that it appears with the reset and
  not without), the two presets named as examples, and the candidate remedies for its own
  spec to probe. Say whether it and the blocking-load issue are better as one host spec or
  two, and recommend.
- Hold today's behaviour with a characterization test naming that issue, run only where the
  presets are installed: a render of no notes on one named installed preset opens at about
  the measured level, to a named tolerance, so the host fix has to change the test on purpose.
- render's docstring, the README's known limits and the standard say it in a sentence a user
  would understand: until that issue lands, a render of most presets opens with the preset
  sounding though no note was played.
- shape.md records the order: both host issues before the first agent experiment. The 0.1.0
  draft mentions it as the adapter's limit, not core's.
- The centroid and warning tests stay on the start preset, and the centroid's measure starts
  after the transient's measured end, so the test measures the note and not the opening."

The probe corrects one clause of that answer: the sound is smaller without the reset, not
absent, as above.

**Loading twice**, first to "Every load is made twice": "1, once it is counted beyond the start
preset: for the fixture and each of the 75 installed presets, after a set of every parameter and
a render, load the preset's text once and twice and count, through the diagnostic read, how many
of the 903 floats differ from the model after each. Record every count in a transcript. If two
loads leave any float differing on any preset, stop and present before adopting the rule. The
standard states it as a measured workaround with no known cause, names the Vital and pedalboard
versions and the machine, and a test against Vital holds it, so a new Vital that needs one load
or three fails by name. Say also what two loads do to the sample section (whether the 4-sample
delay is counted from the text each time or accumulates) with the measurement."

Then, the count having found the 46, to "Adopt, and state the upgrade": "1. With these
additions:
- The limit is stated for what it is, not as rounding: on a preset older than the plugin, a
  few parameters can be reported by get with the file's value where Vital plays its upgraded
  one, and for a choice that can be a different setting by name (the osc_N_stack_style and
  filter_N_style cases given as examples). README's known limits, load_patch's docstring and
  the standard say so.
- The issue's draft records the 46 by preset, key, file value and held value, grouped as you
  have them (keys the text lacks set to other than the default; flanger_center moved into
  range; floats renumbered or rescaled), and sets out the options for its own spec without
  choosing: the model takes Vital's upgraded floats for those keys through the diagnostic
  read, as a stated exception to Decision 1; the upgrade is reproduced in the package (say
  what that would mean for the licence, since Vital's source is GPLv3 and this package is
  MIT: the owner's call, not legal advice); or older presets are refused or flagged. It also
  asks whether a load should expose which keys Vital changed.
- It joins the two host issues as work before the first agent experiment; say in shape.md
  which order you recommend for the three and why."

**The probe's rerun**, to "Rerun whole, 6 s a blocked load": "1. Nothing in the tree is touched
while it runs, and the transcript says each blocked load was killed after 6 s by design, with the
process sample that shows where it was waiting kept for at least one of them."

**The centroid's measure**, to "The held note under a Hann window": "1. The window's bounds
(0.2 s to 1.4 s) are named constants beside the tolerance and the floor, with a comment saying
why they sit inside the held note and clear of its start and end. measures.md records the lesson
in the retrospective: a measure over part of a render is taken under a window, never by a bare
cut, with probes.txt's unwindowed figures as the evidence."

## Decisions made on the probes

24. **A MIDI time is half a sample past its sample,** `(2n + 1) / (2 * rate)`, on the
    measurement above. Plan Decision 12 left this to the probe.
25. **`load_patch` guards what was measured.** Before the plugin is called it refuses a
    `synth_version` that is not digits and dots or is newer than the plugin's; `wavetables` and
    `lfos` that are not arrays of three and of eight objects; a `sample` that is not an object
    holding `length`, `name`, `sample_rate` and `samples`; and a parameter's float with no
    finite display. All 77 files on hand hold their sections so. It cannot refuse a section
    whose inside Vital cannot read, since the package does not read sections.
26. **No test may hang the gate.** Every load a test sends to Vital passes the guard first. The
    loads that block stay as transcripts, each in a child process with a time limit.
27. **The clipping rule stands as decided,** over the whole render. The opening sound is the
    hosted plugin's, held by a characterization test on one named installed preset and put to
    a host issue.
28. **Every load is made twice,** a measured workaround with no known cause.
29. **A preset older than the plugin keeps its file's floats in the model,** by the issue's
    Decision 1, and Vital plays its own upgrade of them. The limit is stated as what it is: `get`
    can report the file's value where Vital plays another, and for a choice that is another
    setting by name.
30. **The centroid is measured over the held note, 0.2 s to 1.4 s, under a Hann window,** the
    bounds named constants. A measure over part of a render is taken under a window, never by a
    bare cut.
31. **Three issues are drafted for this repository and presented with the drafts for core,**
    not filed without the owner's word: a load Vital cannot use blocks its caller; a render
    opens with the preset's own sound; Vital upgrades a preset older than it. All three come
    before the first agent experiment.

## The owner's answers on the retrospective and the issues

2026-11-16, in the owner's words. Each question was a multi-select; the options chosen are named
before the words.

**Project standards, 1 of 2** (`vital/instrument.md`, new; `vital/plugin-state.md`;
`vital/parameter-map.md`, all three chosen): "1, 2 and 3, each its own change set with its
index.yml entry. For instrument.md and plugin-state.md: the three measured limits (a load Vital
cannot use blocks; a render opens with the preset's sound; an older preset is upgraded) each
name the issue that owns the remedy, and each measurement gives the Vital and pedalboard
versions and the machine."

**Project standards, 2 of 2** (`vital/measures.md`; `vital/preset-tests.md`; `index.yml`'s
`vital:` entries, all three chosen): "1, 2 and 3. For preset-tests.md: committing
tests/data/upgraded-floats.txt (preset names, keys and 46 measured values, no preset's content)
is recorded as the owner's call of 2026-11-16, not legal advice, beside the manifest's and the
start preset's, to revisit before any PyPI release."

**Base proposals, 1 of 3** (`tests.md`: a run named for its target; fixtures in the module; no
input that blocks, all three chosen): "1, 2 and 3, in one new issue unless one refines a
proposal already open, in which case it is revised into that issue in place. For 2: word it as
the general rule (where one module takes the fixtures they may live in that module) with the
conftest conflict as its evidence, not as the rule itself. Filed only after the gate's clean
run."

**Base proposals, 2 of 3** (a new standard, the model is the truth; the same standard, refused
whole; `errors.md`, core's check re-raised: the third chosen): "3 only, revised into
fromtheoutfit/patchbay-standards#34 in place with a "Revised 2026-11-16" paragraph. Proposals 1
and 2 are marked "held by owner, 2026-11-16: project standard in vital/instrument.md until a
second adapter shows what is common", and shape.md names the two sections of that file a future
base standard would be drawn from."

**Base proposals, 3 of 3** (#38, a still tree while it runs; #39, an issue drafted and not yet
filed, both chosen): "1 and 2, each revised into its issue in place with a "Revised 2026-11-16"
paragraph, after the gate's clean run. For 2: once the issues are filed, shape.md lists each
such test with the number its title now has, so a reader can go from the test to the issue
without the spec folder."

**When the three issues for this repository are filed** (file the three now, chosen): "1. File
the three as drafted, no attribution, each read back, each saying it runs before the first
agent experiment and where it sits in the order of the three. With the numbers known, the two
characterization tests name their issues by number (proposal 2 of the last set then has this
spec as a case where the number could be had before the gate, and says so). The four drafts for
core wait for the gate and are shown together."

## Decisions made on those answers

32. **The three issues for this repository are filed before the gate,** #20, #21 and #22, and
    each says it runs before the first experiment that puts an agent in front of the instrument
    and where it sits among the three.
33. **What can name an issue by number does.** The tests, the instrument's docstring, the
    README, the CHANGELOG and the standards name #20, #21 and #22. The one issue named by its
    title is the one drafted for core, which is filed only after the gate; "The tests that hold
    today's behaviour for an issue", below, gives each test with its issue.
34. **The five project standards are edited as drafted,** each its own change set with its
    `index.yml` entry, the three measured limits each naming the issue that owns its remedy
    and each measurement giving Vital's and pedalboard's versions and the machine.
35. **Committing `tests/data/upgraded-floats.txt` is the owner's call of 2026-11-16,** not legal
    advice, revisited before any release to PyPI: the names of 11 presets Vital installs, keys
    and 46 measured values, and no preset's content. It is recorded in `vital/preset-tests.md`
    beside the manifest and the start preset, and in the README's licence paragraph.
36. **Six base proposals go upstream after the gate's clean run and two are held:** three for
    `tests.md` as one new issue; one revised into each of
    fromtheoutfit/patchbay-standards#34, #38 and #39 in place. "Standards Retrospective",
    below.

## What was built

- **New modules:** `instrument.py`, 436 lines, the one that imports the host; `patch.py`, 314;
  `midi.py`, 69; `start.py`, 172; and `data/start.vital`, 60,875 bytes, written by the census.
- **Changed:** `errors.py` (three errors, each core's too), `census.py` (a third file),
  `__init__.py` (six names re-exported), and `pyproject.toml` in `[project.entry-points]` alone.
  `uv.lock` is unchanged, and no gate file is touched.
- **Not touched,** as decided: `host.py`, `format.py`, `preset.py`, `parameters.py`. So no count
  of the map is owed again.
- **Tests: 777, where `main` has 534.** 574 in `tests/unit/` and 203 in `tests/integration/`.

  | Module | Tests | New here |
  |---|---|---|
  | `tests/unit/test_instrument.py` | 63 | all, 13 of them core's contract suite over a fake plugin |
  | `tests/unit/test_patch.py` | 32 | all |
  | `tests/unit/test_midi.py` | 15 | all |
  | `tests/unit/test_start.py` | 9 | all |
  | `tests/unit/test_errors.py` | 44 | the three errors' cases |
  | `tests/unit/test_census.py` | 36 | the third file, and a rename failing at it |
  | `tests/unit/test_package.py` | 11 | the entry point and the surface |
  | `tests/integration/test_vital_instrument.py` | 35 | all, 13 of them core's contract suite against Vital |
  | `tests/integration/test_factory_round_trip.py` | 152 | each manifest preset through a patch and its JSON |
  | `tests/integration/test_vital_plugin.py` | 16 | the census test checks three files |

- **While building,** `scripts/gate.sh` was run by hand after the errors, the start preset and
  the census (555 tests) and after the instrument (776 tests, 80 s). Those runs are not kept;
  the gate's record is the one run of "Verification Gate", below.

### Where the build left the plan

- **The start preset's text is written from a map directly,** `start_text(found)`, not through
  the preset's models as the plan's `build_start(map)` had it: the census must be able to write
  it for a Vital whose keys the models do not know yet. A test writes one for a map with a new
  key.
- **The guard refuses one thing more than the probes named:** a float with no finite display,
  which no scale can show and `get` could not return.
- **An instrument loads the start preset twice as it is built,** by Decision 28, where the plan
  had a fixture load it once before the constructor.
- **The centroid's tolerance is 3.6,** half the smallest ratio the windowed measure gave, 7.331,
  by Decision 30. The plan's measure, a cut at sample 7,200, gave 1.19 and was dropped.
- **`test_the_census_regenerates_the_committed_map` is renamed**
  `test_the_census_regenerates_the_three_committed_files`, since it now holds three; the two
  standards that named it are corrected in the retrospective.
- **Three issues for this repository** were not in the plan. The probes found them.
- **The transcripts that read the built instrument were run again,** once the docstrings and
  comments named the issues and the figures below were corrected, so each prints `src/` and
  `tests/` by blob as the gate ran on them. The first runs, of 2026-11-16 07:56 to 08:16, gave
  the same counts.
- **The harness is run three times,** where the plan named one: every test but j, then j, the
  CI replay, as the harness's own header says its transcripts are kept and as the last rerun
  was; and every test but j once more after the gate, at the owner's word, for a transcript the
  wrapper finished.

### Figures corrected against the kept transcripts

Found on 2026-11-16, while each sentence of the standards' drafts was checked against the kept
transcripts: four figures in this file, in comments and docstrings and in issue #21 were those of
the two probe runs that were not kept. Each is corrected to what `verification/probes.txt` shows.

| Where it stood | It said | The kept transcript shows |
|---|---|---|
| "What the probes showed", issue #21 | the start preset peaks at 0.083 with `volume` at its maximum | 0.074 (section 4) |
| the same two, `vital/plugin-state.md`'s draft, a test's comment | its last non-zero sample is 4,928 at most | 4,889 at most (sections 1, 4 and 8: 4,857, 4,873, 4,889) |
| the instrument's docstring, the README, `vital/instrument.md`'s draft | the start preset's transient is under 0.02 | 0.017 to 0.021 (sections 1, 4 and 4b), so "about 0.02" |
| a test's comment and docstring | Plucked String opens at 0.21 to 0.34 over eight renders | 0.21 to 0.37 over six (sections 4 and 4b) |

- Issue #21 was edited in place on GitHub and read back.
- The probe's own sentence in sections 7 and 7b, "its last non-zero sample 4928 at most", is
  text the script prints, not a measurement of that run. It stands in the transcripts as
  printed.
- No tolerance moves: `_OPENING_ENDS` is 7,200 samples, past 4,889 as it was past 4,928;
  `_TRANSIENT` is 0.05 and `_OPENING_SOUND` 0.1.
- Recounted from the kept transcripts at the same time, and found as written: every other
  figure of "What the probes showed" but two, corrected above in place (17 values of n chosen,
  not 13; the breakdown of the 46 floats); the 20 loads of issue #20, 11 of them never
  returning, 4, 3 and 4 by what the writer and the guard make of them; the 75 presets of issue
  #21; and the 46 floats of issue #22, whose table is generated from
  `tests/data/upgraded-floats.txt`. All 75 installed presets are older than 1.6.4, versions
  0.6.1 to 1.0.0, read from the files.

## What the transcripts show

Each is in `verification/`, written outside the tree and copied in, printing the date, the
branch, the machine and the tree before and after its run, the two trees compared, and every
script it ran. All five were run on 2026-11-16, one after another, once `src/`, `tests/` and the
standards' edits were made, nothing in the tree touched meanwhile; each ends with the tree after
the run being the tree before it. A copy differs from what was printed in two substitutions
alone: the scratch directory's path is written `<scratchpad>` and the home directory `~`.
Written after them, so not in the trees they print: this section, one test's name corrected in
`vital/instrument.md` and in the table below it, and the gate's results.

- **`contract-run.txt`** (2026-11-16 08:47 EST): core's thirteen contract tests, core at
  `eddba95404a9b633d358dc4d6b07b084a8f975ad`.
  - Against the installed Vital, on the module's one host: 13 passed, 22 deselected in 3.15s.
  - Against the installed Vital, a fresh `VitalHost` for each: 13 passed of 13, each load 2.31
    to 2.42 s.
  - Over the fake plugin, as CI runs them: 13 passed, 50 deselected in 0.52s.
  - The instrument's whole integration module: 35 passed in 39.69s.
- **`carrying-count.txt`** (2026-11-16 08:48 EST), a count over every preset on hand, the start
  preset, the fixture and the 75 installed: 77 texts, 59,477 floats,
  59,442 carried in `values` and 35 in the preset entry, on
  26 texts; 10,057 keys absent and left absent;
  77 of 77 byte for byte through a patch and
  77 of 77 through the patch's JSON. The 35 by key:
  `{'flanger_dry_wet': 26, 'chorus_damping': 3, 'flanger_center': 3, 'compressor_band_upper_ratio': 1, 'compressor_low_upper_ratio': 1, 'compressor_high_upper_ratio': 1}`.
- **`off-grid-count.txt`** (2026-11-16 08:48 EST), a count: the floats a set cannot land on, and how
  far a set of each one's own display moves it.
  - The start preset: 22 of 903, one float32 step on 5 and two on
    17; the display moves by at most 2.38e-07 of itself.
  - The 75 installed presets: 2,201 of 57,636 inside their bounds, in all
    75: one step on 676, two on 1,332, and 3 to 184 on the other 193;
    the display moves by at most 2.11e-05 of itself. A set of the display shows that display
    again on 0 of them.
  - **This corrects the shaping answer's "one float32 step".** It is one or two steps on
    2,008 of the 2,201 and more on 193. The draft for core gives the
    distribution.
- **`wheel-contents.txt`** (2026-11-16 08:48 EST): the built wheel's `entry_points.txt` holds
  `vital = patchbay_vital.instrument:VitalInstrument` under `[patchbay.instruments]`, and its
  `patchbay_vital/data/start.vital`, 60,875 bytes, has the tree's blob, `95e8053ccc85`.
- **`mutation.txt`** (2026-11-16 08:48 EST): 30 mutants, one per decided rule, each made on a scratch
  copy outside the tree; 0 survived. Each fails the test named beside it, by name.

  | Mutant | What it does | A test it fails |
  |---|---|---|
  | MK1 | a set of the value already shown is carried out like any other (the keep rule gone) | `test_a_set_of_the_value_already_shown_keeps_what_is_held` |
  | MR1 | a set stores the curve's own float32, not what Vital holds for it | `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest` |
  | ME1 | a set publishes before the model is replaced | `test_contract_against_a_fake_plugin[set_emits_parameter_changed_once]` |
  | ML1 | a load replaces the model before the plugin has taken the text | `test_a_load_the_plugin_refuses_puts_the_model_s_text_back_and_is_refused_as_a_patch` |
  | ML2 | a load is made once | `test_it_starts_on_the_start_preset_loaded_into_the_plugin_twice` |
  | ML3 | PatchLoaded counts the preset's floats, not the patch's values | `test_parameter_count_is_the_number_of_values_in_the_patch_given` |
  | MG1 | the guard takes any synth_version that is digits and dots, a newer one too | `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called[a newer version]` |
  | MG2 | the guard does not count a section's entries | `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called[wavetables empty]` |
  | MG3 | the guard takes any object as a sample | `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called[a sample lacking a key]` |
  | MG4 | the guard lets through a float whose display is no finite number | `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called[a float whose display is no finite number]` |
  | MN1 | a render of no samples is asked of the plugin | `test_a_render_of_no_samples_is_an_empty_result_and_the_plugin_is_not_called` |
  | MN2 | no limit on a render's length | `test_a_render_past_a_limit_is_refused_naming_the_limit_and_its_value[too long]` |
  | MN3 | no limit on a render's rate | `test_a_render_past_a_limit_is_refused_naming_the_limit_and_its_value[too fast a rate]` |
  | MN4 | the warning is for a sample past full scale, not at it | `test_a_render_whose_largest_sample_is_exactly_full_scale_carries_the_warning` |
  | MP1 | a float is put in values without checking that its display gives it back | `test_a_float_its_display_cannot_carry_rides_in_the_entry_though_it_is_in_range` |
  | MP2 | a float outside its bounds is put in values | `test_a_float_outside_its_bounds_rides_in_the_entry_as_itself` |
  | MP3 | a parameter carried in both places is taken, the value winning | `test_a_parameter_carried_in_both_places_is_refused_by_name` |
  | MP4 | a value between an indexed scale's steps is kept as the curve gives it | `test_a_value_goes_to_the_float_a_preset_holds_for_it` |
  | MP5 | entries with no preset entry are taken as part of the start preset | `test_an_entry_without_the_preset_entry_it_belongs_to_is_refused` |
  | MP6 | the values are checked last id first | `test_the_first_value_to_refuse_is_the_first_by_id` |
  | MP7 | a wrong unit leaves as core's own error, not the package's | `test_a_value_is_checked_by_core_s_rule_and_refused_as_the_package_with_core_s_fields` |
  | MM1 | a MIDI time is the sample's own, not half a sample past | `test_a_note_lands_on_the_sample_core_s_rule_gives_it` |
  | MM2 | events on one sample come in the pattern's order, ons and offs alike | `test_a_pitch_repeated_without_a_gap_is_released_before_it_is_struck_again` |
  | MM3 | a note that starts at the render's length is sent | `test_a_note_that_starts_at_the_render_s_length_is_left_out_whole` |
  | MM4 | a note-off at the render's length is sent | `test_a_note_off_at_the_render_s_length_is_left_out_and_the_note_on_kept` |
  | MS1 | the committed start preset holds one float that is not the map's default | `test_the_committed_file_is_what_the_package_writes_from_the_committed_map` |
  | MS2 | the generator writes a wavetable that is not the ramp | `test_the_committed_file_is_what_the_package_writes_from_the_committed_map` |
  | MC1 | the census writes the key list and the map and not the start preset | `test_the_census_writes_its_three_files_and_names_a_parameter_it_cannot_fit` |
  | MX1 | the entry point names another object | `test_the_distribution_registers_the_instrument_under_vital` |
  | MV1 | a load is made once, against the installed Vital | `test_the_next_instrument_starts_clean` |

## The tests that hold today's behaviour for an issue

Each asserts what the code or the plugin does today, says so, and names the issue whose fix
changes it on purpose.

| Test | Module | Issue |
|---|---|---|
| `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding` | `tests/integration/test_vital_instrument.py` | #21, by number |
| `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none`, with `tests/data/upgraded-floats.txt` | `tests/integration/test_vital_instrument.py` | #22, by number |
| `test_the_guard_does_not_read_inside_a_section` | `tests/unit/test_instrument.py` | #20, by number |
| `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour`, and `..._holds_its_neighbour_on_vital` against the installed Vital | `tests/unit/test_instrument.py`, and `tests/integration/test_vital_instrument.py` | the issue drafted for core, "Instrument.get: a value `get` has returned is not always one `set` lands on", by its title: fromtheoutfit/patchbay#20, filed after the gate |

## Issues: three filed for this repository, four drafted for core

Seven texts: three for this repository, on what the hosted plugin does, and four for
fromtheoutfit/patchbay. None carries attribution.

- **The three for this repository were filed on 2026-11-16, at the owner's word, before the
  gate:** #20, #21 and #22, each as it reads below, each read back from GitHub against the text
  sent. Their evidence is the probe transcripts, which do not depend on the gate's result.
- **#21's body was corrected once after it was filed,** the same day: the start preset's three
  figures, which were an earlier run's ("Figures corrected against the kept transcripts",
  below). The text below is the corrected one, read back.
- **The four for core were shown to the owner together on 2026-11-16, after the gate's clean
  run,** each whole. The owner's answers:
  - draft 1: "1. File as drafted, no attribution, read back. It names the case, the counts (22
    defaults and 2,201 preset floats) and the candidate wordings without choosing one, and says
    whether any contract test's meaning changes."
  - drafts 2 and 3: "File as drafted (Recommended)".
  - draft 4, "Hold it": "2. Print draft 4 whole in your reply, as it would be filed, with the
    numbers of the three issues just filed on fromtheoutfit/patchbay filled in. File nothing
    until I say so."
- **Three are filed, fromtheoutfit/patchbay#20, #21 and #22,** as they read below, each read
  back from GitHub against the text sent. **The fourth, the 0.1.0 proposal, is held.** (Filed
  since, on 2026-11-16 after the merge, as fromtheoutfit/patchbay#26: see draft 4 below.)
- **The numbers coincide.** fromtheoutfit/patchbay-vital#20, #21 and #22 are the three on the
  hosted plugin; fromtheoutfit/patchbay#20, #21 and #22 are the three for core. Where this file
  writes a bare number it is this repository's.

The evidence each cites
is uncommitted work on branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7` until the owner pushes it.

**Two host specs, not one.** The blocking load and the opening sound are both
`host.py`'s, and are better as two specs than one: they are two methods, `load_state` and
`render`, two mechanisms, Vital's alert and what a reset sets off, with separate probes and
tests; and the first can stop a process dead while the second cannot, so it should not wait on
the second's probes. The older presets are the model's and the map's, a third spec.

**The order recommended, all three before the first experiment that puts an agent in front of
the instrument:**

1. **The load that blocks.** It ends an experiment with no error to act on: the process waits
   for ever on a window nobody is looking at.
2. **The opening sound.** It is in every render of most presets, 51 of the 75 installed, and an
   agent that listens judges a sound by its renders.
3. **The older presets.** It misreports 46 values on 11 of the 75 installed presets, only for
   presets older than the plugin; a preset Vital 1.6.4 saved has none.

### For this repository, 1: a load that blocks (filed as #20)

> **Title:** The host: a preset Vital cannot read blocks the calling process for ever
>
> `VitalHost.load_state` raises for no preset Vital cannot use. Given a text it cannot read,
> Vital 1.6.4 puts up a modal alert and never returns to its caller, so the process that called
> waits for ever and nothing in Python can catch it. **Until this lands, a patch with a section
> Vital cannot read blocks the calling process forever.** The instrument (#8) refuses every shape
> of text seen to do it, and cannot judge the inside of a section, which the package does not
> read.
>
> ## Evidence
>
> `agent-os/specs/2026-11-15-1448-the-instrument/verification/probes.txt`, section 5, on branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`: Vital 1.6.4 through
> pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). 20 texts, each loaded in a process of
> its own and killed after 6 s if it had not returned.
>
> - **11 never returned.** A sample of one waiting process shows where:
>   `SynthProcessor::setStateInformation` (Vital), `juce::AlertWindow::showNativeDialogBox`,
>   `juce::OSXMessageBox::getRawResult`, `-[NSAlert runModal]` (AppKit).
>   - Four are texts the package's writer can write and the instrument's guard refuses: no
>     section at all; `wavetables` an object; `sample` an empty object; `synth_version` "abc".
>   - Three are texts the writer can write that pass the guard, their fault inside a section:
>     three wavetables whose `groups` is a number; eight lfos whose `points` is a string; a
>     sample whose `length` is a string.
>   - Four the writer cannot write, the models refusing them first: an empty object; empty
>     `settings`; a string where a float belongs; `wavetables` a string.
> - **Two returned and were wrong, with no error.** A `synth_version` of 99.0.0 was ignored
>   whole, the plugin unchanged. `wavetables` or `lfos` as an empty array loaded the floats and
>   kept the sections the plugin had.
> - A key the text lacks goes to its default, 132 of 132, and names Vital does not know as a
>   routing's source and destination load.
>
> ## What exists today
>
> `instrument.check_loadable` refuses, before the plugin is called: a `synth_version` that is
> not digits and dots or is newer than the plugin's; `wavetables` and `lfos` that are not arrays
> of three and of eight objects; a `sample` without `length`, `name`, `sample_rate` and
> `samples`; a float with no finite display. No test sends Vital a text that may block: the
> loads that do live in the transcript, each in a process of its own.
>
> ## Candidate remedies, for this spec to probe
>
> - **A trial load in a child process,** with a time limit, before the real one: the child hosts
>   its own Vital, 2.3 s to load, or stays up across loads. What it costs a load, and whether a
>   text the child loads can still block the parent.
> - **A watchdog** that ends the alert's modal loop from another thread. macOS alone, and the
>   load then returns having failed without a word, which is the next question.
>
> ## One more question for this spec
>
> Can a load Vital silently ignores, the newer version above or an alert dismissed, be detected
> afterwards by a cheap check through the diagnostic read? The plugin upgrades and moves what it
> loads, so the state is not the text given back.
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. It runs before the first experiment that puts
> an agent in front of the instrument, and is the first of the three issues that do: this one,
> then the render that opens with the preset's own sound, then the preset older than the plugin.
> No test may hang the gate. The measured fact is in
> `agent-os/standards/vital/plugin-state.md`; the remedy changes it. CHANGELOG; gate green. No
> commit, pull request or push by an agent.

### For this repository, 2: the opening sound (filed as #21)

> **Title:** The host: a render opens with the preset's own sound though no note was played
>
> A render with no MIDI at all is not silent after a small transient, as the host spec measured
> on Vital's own starting state. It holds the preset's own sound, at every render. **Until this
> lands, a render of most presets opens with the preset sounding though no note was played.**
>
> ## Evidence
>
> `agent-os/specs/2026-11-15-1448-the-instrument/verification/probes.txt`, sections 4 and 4b, on branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`: Vital 1.6.4 through
> pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Section 4 gives, for each of the 75
> installed presets, its peak over 0.5 s as loaded and with `volume` at its maximum, its last
> non-zero sample, and how long it stays at or above 0.001 over 4 s.
>
> - **On the start preset:** a peak of 0.017 to 0.021 over the transcript's renders, 0.074 with
>   `volume` at its maximum, the last non-zero sample 4,889 at most.
> - **On the 75 installed presets:** the largest peak as loaded is 2.1, the plugin's ceiling.
>   One reaches full scale as loaded and 17 with `volume` at its maximum. 51 peak above 0.02 and
>   28 above 0.1. 67 are still non-zero after 0.5 s, 32 stay at or above 0.001 for a second or
>   more, and 8 for 4 s or more.
> - **Two examples,** each on a fresh instance nothing had been played on, peak per 100 ms:
>   Plucked String opens at 0.31 and decays over 2 s; Super Nice Pluck opens at 0.73 and is at
>   0.1 after 2 s. A second render straight after does the same.
> - **With the reset and without it.** `VitalHost.render` always resets. Reaching past the host
>   to render without one, on a fresh instance: Plucked String peaks at 0.012 without a reset
>   and 0.21 with one, Super Nice Pluck at 0.18 and 0.64, the start preset at 0.010 and 0.021.
>   So it is larger with the reset and not absent without it.
>
> ## What exists today
>
> The instrument's clipping warning counts the opening with the rest of the render and says
> where the peak is. `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding`
> holds today's behaviour on Plucked String, so a fix changes it on purpose. The centroid and
> warning tests are on the start preset, and measure past its opening.
>
> ## Candidate remedies, for this spec to probe
>
> - Find what sets the voices off: pedalboard's reset, Vital's own, or the load.
> - Render without pedalboard's reset, and say what then carries from one render to the next: a
>   note left sounding is not heard in the next render today.
> - Render a lead-in and discard it. How long it must be: 8 presets sound for 4 s or more.
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. It runs before the first experiment that puts
> an agent in front of the instrument, and is the second of the three issues that do: after the
> load that blocks, before the preset older than the plugin. Every audio assertion is a measure
> with a named tolerance. The measured fact is in
> `agent-os/standards/vital/plugin-state.md`; the remedy changes it. CHANGELOG; gate green. No
> commit, pull request or push by an agent.

### For this repository, 3: the older presets (filed as #22)

> **Title:** A preset older than the plugin: Vital upgrades it as it loads, and the model keeps the file's floats
>
> Vital 1.6.4 changes some floats of a preset written by an older Vital as it loads it. The
> instrument's model keeps the file's floats, by the first Decision of #8, so `get` reports the
> file's value for those parameters where Vital plays another, and for a choice that is another
> setting by name: `osc_1_stack_style` 9 in the file is played as 10.
>
> ## Evidence
>
> `agent-os/specs/2026-11-15-1448-the-instrument/verification/probes-2.txt`, section 9c, on branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`: Vital 1.6.4 through
> pedalboard 0.9.26 on arm64. For each of the 75 installed presets, after two loads of its text,
> each of the 903 floats the plugin holds that is not the model's: the file's own float for a key
> it holds, the parameter's default for one it lacks. 46 floats on 11 presets, versions 0.6.1 to
> 1.0.0; a third load holds the same. The other 64 presets, all older than 1.6.4 too, have none.
> `tests/data/upgraded-floats.txt` records them and
> `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none` holds
> Vital to them.
>
> **A key the file lacks, set to other than the default, 29:**
>
> | Preset | Key | In the file | Vital holds |
> |---|---|---|---|
> | Factory/Presets/Touch Tone | `chorus_cutoff` | absent | 20.0 |
> | Factory/Presets/Touch Tone | `lfo_1_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_2_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_3_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_4_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_5_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_6_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `lfo_7_smooth_mode` | absent | 0.0 |
> | Factory/Presets/Touch Tone | `stereo_mode` | absent | 1.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `chorus_cutoff` | absent | 20.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `chorus_spread` | absent | 0.800000011920929 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_1_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_2_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_3_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_4_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_5_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_6_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `lfo_7_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `stereo_mode` | absent | 1.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `chorus_cutoff` | absent | 20.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `chorus_spread` | absent | 0.800000011920929 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_1_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_2_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_3_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_4_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_5_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_6_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `lfo_7_smooth_mode` | absent | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `stereo_mode` | absent | 1.0 |
>
> **`flanger_center`, outside its scale in the file, moved into it, 3:**
>
> | Preset | Key | In the file | Vital holds |
> |---|---|---|---|
> | Factory/Presets/Touch Tone | `flanger_center` | 0.0 | 53.689998626708984 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `flanger_center` | 0.0 | 53.689998626708984 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `flanger_center` | -15.359999656677246 | 38.32999801635742 |
>
> **A float inside its scale, renumbered or rescaled, 14:**
>
> | Preset | Key | In the file | Vital holds |
> |---|---|---|---|
> | Factory/Presets/Ah Eh Ee Oh | `osc_1_stack_style` | 9.0 | 10.0 |
> | Databroth/Presets/Factory Presets/Snowcrash | `filter_2_style` | 1.0 | 0.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Boot Scre3n | `osc_2_stack_style` | 5.0 | 6.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Boot Scre3n | `osc_3_stack_style` | 9.0 | 10.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Memory Leak | `osc_3_spectral_morph_type` | 10.0 | 7.0 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `modulation_10_amount` | 0.19999998807907104 | 0.07499999552965164 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `modulation_12_amount` | 0.13422822952270508 | 0.050335586071014404 |
> | Halcyon Future Riddim Vol 1/Presets/Oolacile/Oolacile Evil Dubstep Bass | `osc_3_spectral_morph_type` | 10.0 | 7.0 |
> | Unsystematic Fragmentation/Presets/Factory Presets/A happy ending of the world | `osc_1_stack_style` | 9.0 | 10.0 |
> | Unsystematic Fragmentation/Presets/Factory Presets/A happy ending of the world | `osc_2_stack_style` | 10.0 | 11.0 |
> | Yuli Yolo/Presets/Factory Presets/Easy Mallet | `osc_1_stack_style` | 9.0 | 10.0 |
> | Yuli Yolo/Presets/Factory Presets/Jupiter Bass | `filter_1_style` | 1.0 | 0.0 |
> | Yuli Yolo/Presets/Factory Presets/Metal Head | `osc_1_stack_style` | 10.0 | 11.0 |
> | inktome/Presets/Piano from the yard sale | `osc_2_stack_style` | 9.0 | 10.0 |
>
> ## Options, for this spec to choose among
>
> - **The model takes Vital's upgraded floats for those keys,** read through the diagnostic read
>   after a load: a stated exception to the first Decision of #8, which keeps the plugin's state
>   from becoming the model.
> - **The upgrade is reproduced in the package,** so the model is upgraded before the plugin
>   sees it. Vital's source is GPLv3 and this package is MIT: rules copied from the source would
>   carry its licence, where rules measured from the plugin, as the parameter map is, would not.
>   The owner's call, not legal advice.
> - **An older preset is refused, or flagged:** the map is 1.6.4's, and a preset from another
>   version holds floats under that version's meanings.
>
> It also asks whether a load should say which keys Vital changed.
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. It runs before the first experiment that puts
> an agent in front of the instrument, and is the third of the three issues that do: after the
> load that blocks and the render that opens with the preset's own sound. A claim over the
> installed presets is counted. CHANGELOG; gate green. No commit, pull request or push by an agent.

### For fromtheoutfit/patchbay, 1: the clause in `Instrument.get` (filed as fromtheoutfit/patchbay#20)

> **Title:** Instrument.get: a value `get` has returned is not always one `set` lands on
>
> `Instrument.get` says, at `eddba95`: "After `set`, that is a value the parameter holds, not
> necessarily the one given: the value given itself at a bound, and at any value `get` has
> returned for it that `set` takes." An instrument that loads presets can hold a value its own
> set path cannot produce, and for such a value the last clause is not met.
>
> ## The case
>
> In patchbay-vital a preset's float is loaded as text and held as given, while a set goes
> through the host's normalized value, which lands on a grid. `get` returns the display of the
> float held. Then another value is set, and the first display is set back: the parameter holds
> the grid's neighbour and `get` returns the neighbour's display, not the value given, though
> `get` had returned that value and `set` takes it.
>
> ## The counts
>
> `agent-os/specs/2026-11-15-1448-the-instrument/verification/off-grid-count.txt` on patchbay-vital's branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`:
>
> - 22 of Vital 1.6.4's 903 default values are such floats. A set of each one's own display
>   holds a float one float32 step away on 5 and two on 17.
> - 2,201 of the 57,636 floats inside their bounds in the 75 presets Vital installs, in all 75:
>   one step on 676, two on 1,332, and 3 to 184 on the other 193. The display moves by at most
>   2.1e-5 of itself.
>
> ## What patchbay-vital does
>
> A set of the value a parameter shows now keeps what it holds, so `set(get())` changes nothing.
> That meets the clause at the value `get` returns now and at any value a set has left the
> parameter holding. It does not meet it for a value `get` returned for a loaded float once
> another value has been set. No memory short of every float ever loaded would.
> `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour` holds the case as it
> is.
>
> ## Candidate wordings
>
> - **"at the value `get` returns for it now, and at any value a `set` has left it holding."**
>   What an instrument with a loaded state can promise. `FakeInstrument` meets it, holding every
>   value it takes. No contract test changes:
>   `test_the_whole_number_fake_gives_back_a_value_get_returned` already sets what `get` returns
>   now.
> - **The wording kept, and `get` held to it:** an instrument never returns from `get` a value
>   its set path cannot land on. An adapter then reports the nearest value a set can land on in
>   place of what a loaded preset holds, and a bound in place of a value outside the bounds,
>   which "that `set` takes" was written to avoid (the revision after the review of #19,
>   Decision 3: `flanger_dry_wet` at 0.7072 shows 141.44 against 0 to 100). `FakeInstrument` and
>   the contract tests are as they are.
> - **The wording kept, and a contract test added** that loads a patch, gets, sets another
>   value and sets the first back. It needs a way for the suite to give an instrument a value
>   its set path cannot produce, which `FakeInstrument` does not have, and patchbay-vital fails
>   it today.
>
> No contract test's meaning changes under the first two; the third adds one.

### For fromtheoutfit/patchbay, 2: the entry-point group (filed as fromtheoutfit/patchbay#21)

> **Title:** The patchbay.instruments entry-point group: state its contract before 0.1.0, or mark it provisional
>
> At `eddba95` core reads no entry point: discovery of adapters is in the contracts spec's
> "Deferred". patchbay-vital registers one all the same, as its issue asked, and has had to
> choose what the group holds.
>
> What it registers, in `[project.entry-points."patchbay.instruments"]`:
>
> - **The key:** `vital`, lower-case, where the instrument's `name` is "Vital".
> - **The object:** `patchbay_vital.instrument:VitalInstrument`, a callable that takes the
>   `EventBus` the instrument publishes on and returns an `Instrument`, as `FakeInstrument(bus)`
>   is built, the one shape core shows.
> - **Loading it may need an optional extra:** it imports pedalboard, which comes with
>   patchbay-vital's `host` extra, so `EntryPoint.load()` raises `ImportError` for an adapter
>   installed without it.
>
> This asks core to state, before 0.1.0, the key's form and how it relates to `Instrument.name`,
> what the object is called with, and what a host does with an entry point that does not load;
> or to mark the group provisional in 0.1.0. patchbay-vital's CHANGELOG and README call its entry
> point provisional until then.

### For fromtheoutfit/patchbay, 3: a render of zero samples (filed as fromtheoutfit/patchbay#22)

> **Title:** Instrument.render: say what a render of zero samples is
>
> `RenderRequest.samples` can be 0: four beats at 23,040,000 bpm and 48 kHz with no tail round
> to no sample. `Instrument.render` says the result is `request.samples(pattern)` samples long
> and no more. `FakeInstrument` returns audio of shape `(1, 0)`, `audio_seconds` 0.0, and
> publishes `RenderCompleted` once; `RenderResult` validates an array of no samples; no contract
> test covers it. patchbay-vital follows the fake: an empty result of two channels, its plugin
> not called.
>
> This asks core to say so in `Instrument.render`, or to add a contract test for it, so the next
> adapter does not have to read the fake to find out.

### For fromtheoutfit/patchbay, 4: patchbay-core 0.1.0 (held until the pull request for #8 merged; filed as fromtheoutfit/patchbay#26 on 2026-11-16)

Written after the gate's clean run, which it cites, and shown to the owner with the other three.
Held on 2026-11-16, in the owner's words: "Print draft 4 whole in your reply, as it would be
filed, with the numbers of the three issues just filed on fromtheoutfit/patchbay filled in. File
nothing until I say so." So this is the text as it would be filed, #20, #21 and #22 in it being
fromtheoutfit/patchbay's. It is the one deliverable of issue #8 not done: drafted, and the
owner's to file.

One sentence was added when the numbers were filled in, and the owner is told so: that the
three issues on patchbay-vital carry the same three numbers by coincidence.

**When it is filed, by the owner's word of 2026-11-16, after he had read it:** "Draft 4 stays
held: it is filed after the pull request for issue #8 is reviewed and merged, citing the merged
commit, with the count of in-range preset floats (57,636 in the draft against 57,671 less the
out-of-range ones) checked and corrected if needed." So, at that time and not before:

- "Where the evidence is" names the merged commit in place of the branch and of "uncommitted
  when this was filed", and the gate's figures are those of the run that commit carries.
- **The count, checked on 2026-11-16 and found right: 57,636.** Recounted from the 75 installed
  files with `json` and the committed map's bounds alone, none of the package's carrying or
  counting code:
  - 57,671 numbers in the 75 presets' `settings`;
  - 3 of them are `chorus_damping`, which is no parameter, so 57,668 are a parameter's, which is
    75 times 903 less the 10,057 keys absent;
  - 32 of those are outside their scale (`flanger_dry_wet` 26, `flanger_center` 3, three
    compressor ratios), so 57,636 are a parameter's and inside it.
  - 57,671 less the 32 alone is 57,639: the three between are `chorus_damping`.
  - `verification/off-grid-count.txt` and `verification/carrying-count.txt` say the same: 2,201
    of 57,636, and 35 floats carried outside `values`, the 32 and the 3.
- The draft's sentence is reworded below so the count cannot be read as 57,671 less 32: "of the
  57,636 preset floats that are a parameter's and inside its bounds". No number changes.
  fromtheoutfit/patchbay#20, already filed, says "2,201 of the 57,636 floats inside their
  bounds", which is the same count.

**Revised 2026-11-16, after the review of PR 23**
(`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`). When it is filed, "The run"
cites that spec's `verification/contract-run.txt`: 13 of 13 on the module's one Vital and 13 of
13 on a `VitalHost` of its own for each test, run on the code the review revised. The gate's
figures are those of the run on the merged commit, as above. "What core does not say yet" gains
two lines, for the two issues filed on fromtheoutfit/patchbay that day at the owner's word:

- #23: `Patch`'s "a value for each parameter", against the 35 floats a patch carries in `opaque`.
- #24: what an adapter does when one channel cannot voice two notes of one pitch, which core's
  fake sums each for its own length.

"The adapter's limits" gains one line and asks core nothing new:

- When the plugin refuses a load and then the model's own text, its state is unknown.
  `load_patch` raises patchbay-vital's `PluginStateError`, which is not `PatchRejectedError`, and
  the instrument refuses every later call that would reach the plugin, saying to build a new one.

**Revised 2026-11-16, after the second review of PR 23**
(`agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/`). When it is filed, "The
run" cites that spec's `verification/contract-run.txt` in place of the first revision's: 13 of 13
on the module's one Vital and 13 of 13 on a `VitalHost` of its own for each test, run on the code
as the second revision leaves it. "What core does not say yet" gains one line, for the issue
filed on fromtheoutfit/patchbay that day at the owner's word:

- #25: what an instrument does once it has lost step with its device. `set` and `render` then
  raise an error outside the types the protocol names for them, ahead of the usual checks.

The line above under "The adapter's limits" stays, and no longer "asks core nothing new": the
limit is the adapter's, and what an instrument does in that state is now asked of core as #25.
The draft's line on fromtheoutfit/patchbay-vital#22 stands; that issue's body says, since the
same day, that a set of the value `get` shows mends 42 of its 46 floats. The draft stays held.

**Filed 2026-11-16 as fromtheoutfit/patchbay#26,** after the pull request for #8,
fromtheoutfit/patchbay-vital#23, merged as `0eac1dba4e0738d8b32d2b703ddfba0c09d11b18` on `main`.
The owner's words: "The pull request for issue #8 is merged. File draft 4, the patchbay-core
0.1.0 proposal, on fromtheoutfit/patchbay, no attribution: cite the merged commit on main (git
log -1 after pulling), the final gate and contract runs with their paths under that commit, and
the issues it lists (patchbay #20 to #25 as they apply, patchbay-vital #20 to #22). Check every
path and number in it resolves on main before filing, read it back, and record its number in the
instrument spec's shape.md. Then close nothing and stop: the release itself is the owner's."

The issue's body is the text below with what the notes above said would change. It was read back
from GitHub and is identical to the text sent. It carries no attribution.

- **"The run"** gives the figures of the gate run the merged commit carries, `scripts/gate.sh`
  exit 0 with 803 tests passed and none skipped
  (`agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/verification/gate-run.txt`,
  2026-11-16 15:47 EST), and cites that spec's `verification/contract-run.txt` (15:49 EST), each
  by its full path.
- **"Where the evidence is"** names the merged commit on `main` in place of the branch and of
  "uncommitted when this was filed". It says the two runs were made on the branch before the
  merge and that every file hash they print is that commit's, but for their own spec's
  `shape.md`, written to after they ran. That was checked blob by blob against the commit.
- **"What core does not say yet"** lists #23, #24 and #25 after #20 to #22.
- **"The adapter's limits"** gains the lost step as a paragraph after the three, since it has no
  issue on patchbay-vital, and points at #25 for what core is asked.
- **Three wordings differ from the draft,** each so that the text reads true and its numbers link
  where they should, and the owner is told:
  - "patchbay-vital's issue #8" is written fromtheoutfit/patchbay-vital#8. A bare #8 in an issue
    on fromtheoutfit/patchbay is core's own.
  - "the same three as the issues above" is "those of the first three issues above", six being
    listed now.
  - "Against" adds that `eddba95404a9b633d358dc4d6b07b084a8f975ad` is core's `main` as the issue
    is filed: checked, 0 commits ahead and 0 behind.
- **Checked on `main` at the merged commit before filing:**
  - each path the text names exists there, and `test_contract_against_vital` and
    `test_contract_against_a_fake_plugin` are in the modules it says;
  - the thirteen, counted in the installed core; 22 of 903 and 2,201 of 57,636
    (`verification/off-grid-count.txt`); 35 (the first revision's `carrying-count.txt`);
  - core's quoted words, in the installed package at `eddba95`, and a render of zero samples on
    core's fake, run: an empty result, `(1, 0)`;
  - the pin in `[tool.uv.sources]`, and `pyproject.toml` and `CHANGELOG.md` on core's `main`;
  - fromtheoutfit/patchbay#20 to #25 and fromtheoutfit/patchbay-vital#20 to #22 open,
    fromtheoutfit/patchbay-vital#8 closed and #23 merged, and no earlier proposal on file.
- **Nothing was closed.** Cutting the release is the owner's.

> **Title:** Propose patchbay-core 0.1.0: the contract suite passes against a real instrument, Vital
>
> patchbay-vital's `VitalInstrument` implements `patchbay.Instrument` over a hosted Vital, and core's thirteen `CONTRACT_TESTS` pass against it. patchbay-vital's issue #8 asked for this proposal once they did: cut patchbay-core 0.1.0, the contracts now held by an instrument that is not core's own fake.
>
> ## The run
>
> - **What ran:** `patchbay.testing.CONTRACT_TESTS`, all thirteen, as `test_contract_against_vital` in patchbay-vital's `tests/integration/test_vital_instrument.py`, each on a new `EventBus` and a new `VitalInstrument`.
> - **Against:** Vital 1.6.4, the VST3, hosted through pedalboard 0.9.26; patchbay-core 0.0.1 at `eddba95404a9b633d358dc4d6b07b084a8f975ad`; Python 3.12.16; arm64, an Apple M4 Pro, macOS 26.6.2.
> - **Result:** 13 passed of 13.
>   - In patchbay-vital's gate: `scripts/gate.sh` exit 0, 777 tests passed and none skipped, Vital installed (`verification/gate-run.txt`, 2026-11-16 09:40 EST).
>   - Apart from it (`verification/contract-run.txt`): on the test module's one Vital, and again on a `VitalHost` of its own for each test, 13 of 13 both ways.
> - **It is a local run.** CI has no Vital. What CI passes is `test_contract_against_a_fake_plugin`, the same thirteen over the adapter's real host on a fake plugin, and that is not a pass against Vital.
> - **Where the evidence is:** fromtheoutfit/patchbay-vital, branch `feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`, `agent-os/specs/2026-11-15-1448-the-instrument/`, uncommitted when this was filed; the owner's push puts it there.
>
> ## One clause of `Instrument.get` is met except in one case
>
> Every promise the suite checks is met. Of what it cannot check, `Instrument.get`'s "at any value `get` has returned for it that `set` takes" is met at the value `get` returns now, and at any value a set has left a parameter holding. It is not met for a value `get` returned for a loaded preset's float, once another value has been set: #20. 22 of Vital's 903 default values are such floats, and so are 2,201 of the 57,636 preset floats that are a parameter's and inside its bounds, in the 75 presets it installs. patchbay-vital holds the case with a test that names that issue by its title.
>
> ## What core does not say yet, found by building against it
>
> - #20: the clause above.
> - #21: the `patchbay.instruments` entry-point group. Core reads no entry point and states no contract for the group; patchbay-vital registers `vital` there and calls it provisional.
> - #22: a render of zero samples, which `Instrument.render` does not mention and `FakeInstrument` gives as an empty result.
>
> 0.1.0 either settles each or says it is provisional.
>
> ## The adapter's limits, which are not core's
>
> Stated so the version is not read as a claim about them. Each is the hosted plugin's, each has an issue on patchbay-vital, and all three come before the first experiment that puts an agent in front of the instrument. Their numbers there are the same three as the issues above, by coincidence:
>
> - fromtheoutfit/patchbay-vital#20: a preset Vital cannot read blocks the calling process for ever. `load_patch`'s "`PatchRejectedError`, changing nothing" holds for every patch the adapter's guard can judge; a patch with a section malformed inside can hang it.
> - fromtheoutfit/patchbay-vital#21: a render of most presets opens with the preset's own sound though no note was played.
> - fromtheoutfit/patchbay-vital#22: for a preset older than the plugin, `get` can report the file's value where Vital plays its upgraded one.
>
> ## Proposed
>
> patchbay-core 0.1.0, under this repository's own gate: the version in `pyproject.toml` and the CHANGELOG's release section. patchbay-vital pins core by commit in `[tool.uv.sources]`, a gate file there, so moving its pin to the release is a gate spec of its own.

## The import direction

Each module imports only what is above it; the root imports none of the three at the bottom.

```text
errors
  preset
    parameters        format
      start  (parameters, format, preset)
        patch  (start, parameters, format, preset, errors)
midi  (core alone)
host  (parameters, preset, state, errors)
  census  (host, start, parameters, files)
  instrument  (host, patch, midi, start, format, parameters, errors)
```

## A note for the semantics-data spec

Not a change here. The 29 indexed continuous parameters and their steps are not visible in
core's `Parameter`: 27 take whole numbers, `chorus_voices` runs in fours and `oversampling` in
powers of two. Describing them belongs with the per-parameter semantics. A step field upstream
is proposed only when a second adapter needs one.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`. One bullet is added to "What the adapter
  is", the owner's approved text, and nothing else under `agent-os/product/` changes. "No audio
  analysis" stays as it reads: the spectral centroid is a measure computed inside a test, and
  the package ships no analysis.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the contract suite's form, the mirror, files read from pytest's root.
- `base/python/events` — core's three events on a bus the instrument is given.
- `base/process/verification-gate` — the gate unchanged, its record, when the harness reruns.
- `base/process/standards-retrospective` — the last step; base changes proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step.
- `base/process/ownership` — no stage, commit, push or pull request; issues without attribution.
- `vital/plugin-state` — what the hosted plugin does to what it is given.
- `vital/measures` — every audio assertion a measure; expected values from primitives.
- `vital/parameter-map` — the scales, the set path and what a count is.
- `vital/preset-file` — where each part of a preset lives, which the carrying follows.
- `vital/preset-tests` — nothing of Vital's committed; the hosted tests skipping by name.

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script
under `scripts/` as git lists them, with no tracked file a `.gitignore` ignores;
`uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set and
`uv.lock`'s pins;
and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the commit in
`agent-os/standards/base/.version` — and the three judgment steps are recorded, in this order:
Docs, Version, then the standards retrospective below.

**Beforehand, how long the harness should take.** Written before it was started, so a run that
goes far past it is noticed. No gate file changed, but files are added under `src/`, `tests/`
and `agent-os/standards/`, which every case copies, so the harness is rerun, once.

- The last rerun, the sixth review of PR 14's on 2026-11-13, printed 40 pytest summaries summing
  1,010 s, when the whole suite took 33 s, and the rest of its 19 minutes was about two.
- The suite now takes about 80 s, 2.4 times that, 40 s of it the instrument's module against
  Vital. So about 2,450 s of pytest and a few minutes more: **about 45 minutes for every test
  but j, and about 3 for j.**
- A run past 70 minutes is stopped and looked at, not waited out.

**The harness, as it ran,** on 2026-11-16: every test but j twice and case j once. Nothing in
the tree was touched during any of the three runs, and each ends with the tree after the run
being the tree before it.

- `verification/gate-negative-tests.txt`, every test but j, **the whole transcript: 140 runs, 0
  unexpected,** exit 0, from 09:57 to 10:39 EST, 43 minutes; its 40 pytest summaries sum
  2,420 s. It was run after the gate, at the owner's word, below.
- `verification/gate-negative-tests-first.txt`, every test but j, the first run, before the
  gate: **140 runs, 0 unexpected,** exit 0, from 08:53 to 09:37 EST, 44 minutes against the 45
  estimated; its 40 pytest summaries sum 2,493 s against the 2,450 estimated.
- `verification/ci-negative-test.txt`, case j, the CI replay, before the gate: **3 runs, 0
  unexpected,** exit 0, a minute and a half.
- 140 is the count of the harness as `main` has it (the revision after the review of PR 12 kept
  140); `scripts/` is unchanged here.
- All three are kept whole, with the two substitutions of "What the transcripts show". The
  tools' own paths in them (uv's cache, a case's temporary directory) are as printed.
- **Why there are two of the first.** The wrapper that prints a transcript's tree and machine,
  which lives outside the tree, stopped at the end of the first run, after the run had ended
  and its two trees were compared, at the line that lists the scripts it embeds: it was given
  none, the harness being a file of the tree, and bash 3.2 under `set -u` refuses an empty
  array. The first transcript says so in a note in its tail, under which the wrapper's three
  helpers were appended by hand, with the blobs the other transcripts embed. The wrapper was
  then corrected, and case j's transcript, the gate's and the second run's embed the corrected
  one.
- **The owner's word on it, 2026-11-16, after the gate:** "Rerun the negative harness once on
  the present tree for a whole transcript, with the fixed wrapper, nothing in the tree touched
  while it runs. Keep the first run beside it as gate-negative-tests-first.txt, its note saying
  what was appended by hand. If the rerun is not clean, stop and present." It was clean.
- **The second run came after the gate and changes nothing the gate read.** By the blobs the
  three print: of the 27 paths the gate's tree lists under `src/`, `tests/`, `scripts/`, the
  standards, `pyproject.toml`, `uv.lock` and `README.md`, none differs in either harness run.
  The second run's tree differs from the gate's in this file, in the first transcript's new
  name, and in `gate-run.txt`, which the gate's own tree could not hold.

**Results (2026-11-16):** `scripts/gate.sh` exits 0 on branch
`feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`,
all six steps, 777 tests passed and none skipped, in 77 s, Vital installed. The record is
`verification/gate-run.txt`: the date and the branch on its first lines, the machine before and
after, the tree before and after by blob, compared with `cmp`, and the wrapper's scripts. It ran
once, at 09:40 EST, after the retrospective's edits, the five transcripts, the first harness run
and case j. One run came after it, the harness again for a whole transcript, above; no file the
gate reads has changed since the gate ran.

- **Every transcript ran on the code the gate ran on.** Compared by the blobs each prints: of
  the 20 paths the gate's tree lists under `src/`, `tests/` and the gate's own files, none
  differs in any of the eight other transcripts of 2026-11-16. The five of "What the transcripts
  show" differ from the gate's tree in one standard, `vital/instrument.md`, whose one corrected
  test name was written after them; the three harness runs differ in no standard.
- **The probes are older, and say so:** `probes.txt` and `probes-2.txt` ran on 2026-11-15 on the
  tree each prints, before the instrument was written. They measure Vital, not this package's
  instrument.
- **Written after the gate's run:** this paragraph, the upstream issues' numbers below, the
  text of the fourth draft for core, the owner's answers on the four, the numbers of the three
  filed, when the fourth is to be filed with its count checked, and the harness's second run
  with the first transcript's new name.
- **What issue #8 asked for and is not done:** the 0.1.0 issue on fromtheoutfit/patchbay. It is
  drafted, shown, and held at the owner's word. (Done since: filed on 2026-11-16, after the pull
  request merged, as fromtheoutfit/patchbay#26.)
- No gate file changed: `scripts/`, `.github/`, `uv.lock` and the `[tool.*]` sections of
  `pyproject.toml` are as `main` has them.

**Docs (step 7):** checked on 2026-11-16, each against the shipped code.

- `README.md`: the opening paragraph and the code example use the instrument as it is built;
  "The instrument" says what it starts on and why, what a set holds, that the entry point is
  provisional, and the three known limits with their issues and their order; the layout lists
  the four new modules and `data/start.vital`; the tests paragraph names both integration
  modules; the licence paragraph names the start preset and `tests/data/upgraded-floats.txt`
  beside pedalboard.
- `CLAUDE.md`: nothing there names what changed. Its gate paragraph says `[project]` is the
  package's, which is where the entry point went.
- `agent-os/product/mission.md`: the one bullet the owner approved, third of four under "What the
  adapter is". "No agent code" and "No audio analysis" read as they did. `tech-stack.md` is
  untouched and names nothing that changed.
- The modules' docstrings: `instrument.py` (the four known limits, three with their issues;
  each constant with its source), `patch.py`, `midi.py`, `start.py`, `errors.py`, `census.py`
  (three files) and `__init__.py`; and the headers of the test modules added or changed.
- `tests/data/upgraded-floats.txt`: its header says what was measured, on which Vital, host and
  machine, and by which probe.
- Issue #8's body, revised in place on 2026-11-15 and read back: finding 1 decided as Vital's
  rounding, findings 2 to 4 decided here.
- Issues #20, #21 and #22, filed on 2026-11-16 and read back; #21 corrected once.
- The standards that name what changed are the retrospective's, below.

**Version (step 8):** `CHANGELOG.md`, `[Unreleased]`, `### Added`, first entry: the instrument,
issue #8, with the provisional entry point and the known limits by issue. The version stays
0.0.1; no release is cut.

## Standards Retrospective

Step 9, last. Per `agent-os/standards/base/process/standards-retrospective.md`, from the shipped
code and tests, never from the plan. Every edit was drafted on a scratch copy, presented to the
owner and approved on 2026-11-16 before it was made. Each sentence was then checked against the
shipped files: every test, helper, mutant and path the five files cite exists, by a search of
`tests/`, `src/` and `verification/mutation.txt`; every figure was recounted from the kept
transcripts, which is where "Figures corrected", above, came from.

The retrospective's files are a change set apart from the feature's, and each standard is its own
with its `index.yml` entry, as the owner asked:

- `agent-os/standards/vital/instrument.md`, new, with the `vital: instrument` entry — what a
  later Vital feature must not break, each rule with the test that holds it: the model as the
  source of truth and the generated start preset; what a set holds; a patch; what the instrument
  does about Vital's loads; events and errors; a render; the contract suite. The three limits
  name issues #20, #21 and #22. Verified against `src/patchbay_vital/instrument.py`, `patch.py`,
  `midi.py`, `start.py`, the tests it names and `verification/mutation.txt`.
- `agent-os/standards/vital/plugin-state.md`, with its entry — the spec proved one sentence
  stale and measured six facts:
  - "A render from a reset opens with a decaying transient (peak 0.022, under 1e-5 by 50 ms)" is
    true of Vital's own starting state alone. A render with no MIDI holds the preset's own
    sound, up to 2.1 on installed presets (#21).
  - Vital reports no load it cannot use and blocks its caller on some (#20); one load is not
    enough and two are; it upgrades a preset older than it (#22); a MIDI time lands a sample
    early on some samples; it gives samples past full scale and 2 ** 24 in a render.
  - "The integration module loads Vital once" is now two modules; the census test's new name.
  - Verified against `verification/probes.txt`, `probes-2.txt` and the tests it names.
- `agent-os/standards/vital/parameter-map.md`, with its entry — the census writes three files,
  with its two new tests and the renamed one; and "issue #8's finding 1, still open" is decided:
  Vital's rounding. Verified against `src/patchbay_vital/census.py` and `tests/unit/test_census.py`.
- `agent-os/standards/vital/measures.md`, with its entry — a measure over part of a render is
  taken under a window, never by a bare cut, the lesson the owner asked for; a render is held
  audible before its spectrum is measured and a measure guards its own division; where an event
  lands is measured exactly, at a sample that tells two rules apart; quiet is measured past the
  opening of the preset it is on. Verified against `tests/integration/test_vital_instrument.py`
  (`_centroid`, `_rms`, `_held` and the named tolerances).
- `agent-os/standards/vital/preset-tests.md`, with its entry — the start preset the package
  ships and the licence call of 2026-11-15; a count measured over the installed presets may be
  committed where a preset may not, with the call of 2026-11-16 on
  `tests/data/upgraded-floats.txt`; no test gives Vital a text it may not return from; the
  second integration module. Verified against `tests/unit/test_start.py` and
  `tests/integration/test_vital_instrument.py`.
- `agent-os/standards/index.yml` — the `vital:` section alone: one entry added, four
  descriptions kept in step. The `base:` section is the sync's and is untouched;
  `scripts/sync-standards.sh --check` says identical.
- **Deviation, not a standard change:** `base/testing/tests.md` puts the contract suite's `bus`
  and `instrument` fixtures in the `conftest.py` beside the tests that run it. Here each of the
  two modules that run the suite holds its own, one over a fake plugin and one over the
  installed Vital, and there is no `conftest.py`. It is proposed upstream as the second
  proposal below; until it lands it stays a one-off of this repository.

Proposals sent upstream: fromtheoutfit/patchbay-standards#44; fromtheoutfit/patchbay-standards#34, #38 and #39, each revised in place; declined: a new base standard for an adapter's instrument (the model is the truth), the same new standard (a call checked whole, a patch refused whole)

### Standards retrospective (proposed, base)

Presented to the owner on 2026-11-16, eight proposals in three questions; six approved, two
held. Wording checked against the open issues on `patchbay-standards`, #34, #37, #38, #39, #40
and #42: three refine a proposal already open and are revised into its issue in place; none
contradicts one. Filed on 2026-11-16 after the gate's clean run, with no attribution, each read
back from GitHub against the text sent: one new issue, fromtheoutfit/patchbay-standards#44, and
a "Revised 2026-11-16" paragraph in each of #34, #38 and #39, whose "Depends on" lines gain this
branch. Nothing already in those three bodies was removed.

- `base/testing/tests.md`, "The contract suite" — **a run of the suite is named for what it
  runs against.** An adapter runs it against the real instrument where that is installed, and
  over a stand-in beneath its own host seam so CI holds it; each parametrization is named for
  its target, and a pass over the stand-in is never cited as a pass against the instrument.
  Verified against `tests/integration/test_vital_instrument.py`
  (`test_contract_against_vital`), `tests/unit/test_instrument.py`
  (`test_contract_against_a_fake_plugin`) and `verification/contract-run.txt`. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#44.
- `base/testing/tests.md`, "Test files" and "The contract suite" — **where one module takes the
  fixtures, they may live in that module.** The evidence is the conflict a `conftest.py` meets
  here: two modules in two directories each run the suite with a `bus` and an `instrument` of
  their own, `tests/` holds one `conftest.py` at most, and this repository's negative gate test
  q writes `tests/unit/conftest.py` into its copy. Verified against
  `tests/unit/test_instrument.py` (`bus`, `plugin`, `host`, `instrument`),
  `tests/integration/test_vital_instrument.py` (`vital`, `bus`, `instrument`) and
  `scripts/gate-negative-tests.sh`, case q. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#44.
- `base/testing/tests.md`, "Inside a test" — **no test gives a third party an input it may not
  return from.** One that answers a bad input by blocking, not raising, is probed in a child
  process with a time limit, kept as a transcript, and the adapter refuses the shapes seen
  before the third party is called. Verified against `verification/probes.txt`, section 5,
  `src/patchbay_vital/instrument.py` (`check_loadable`) and
  `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called`.
  Proposed, not applied; filed as fromtheoutfit/patchbay-standards#44.
- `base/python/errors.md` — **what the protocol package's own check raises is raised again as
  the adapter's error, with the protocol's fields and the protocol's error its cause.** Refines
  fromtheoutfit/patchbay-standards#34, its first proposal. Verified against
  `src/patchbay_vital/patch.py` (`check_value`) and
  `test_a_value_is_checked_by_core_s_rule_and_refused_as_the_package_with_core_s_fields`.
  Proposed, not applied; filed as fromtheoutfit/patchbay-standards#34, revised in place.
- `base/process/verification-gate.md` — **nothing in the tree is touched while a transcript
  runs, and one whose two trees differ is run again, not explained.** Refines
  fromtheoutfit/patchbay-standards#38, its second proposal. Verified against "What the probes
  showed", above, where a second run's own `cmp` line said the tree had changed and the run kept
  is a third on a still tree, and `verification/probes.txt`'s closing `cmp` line. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#38, revised in place.
- `base/testing/tests.md`, "Inside a test" — **a characterization test names its issue by
  number where the issue can be filed before the gate runs, and by its title and the spec
  folder where it cannot,** the spec's `shape.md` then listing each such test with the number.
  Refines fromtheoutfit/patchbay-standards#39. This spec holds both cases: #20, #21 and #22 were
  filed before the gate and are named by number; the issue for core is filed only after it.
  Verified against "The tests that hold today's behaviour for an issue", above, and the four
  tests it lists. Proposed, not applied; filed as fromtheoutfit/patchbay-standards#39, revised
  in place.
- A new base standard for an adapter's instrument — **the model, not the device, is the source
  of truth:** `get` reads it, `set` writes through, the device's state is never read back as
  the adapter's, a diagnostic read shows the device's own view to tests, and the first model is
  one the package ships. Declined by owner, 2026-11-16, in the owner's words: "held by owner,
  2026-11-16: project standard in vital/instrument.md until a second adapter shows what is
  common". A future base standard would be drawn from that file's section "The model".
- The same new standard — **a call is checked whole, then the device is called, then the model
  replaced, then one event published; a patch is taken whole or refused naming the first entry
  to refuse; when the device refuses after the checks pass, the model's state is sent to it
  again.** Declined by owner, 2026-11-16, in the owner's words: "held by owner, 2026-11-16:
  project standard in vital/instrument.md until a second adapter shows what is common". A
  future base standard would be drawn from that file's section "Events and errors", with the
  last rule of "A patch" and the last of "What the instrument does about Vital's loads".
