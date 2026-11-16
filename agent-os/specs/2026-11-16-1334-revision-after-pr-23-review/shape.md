# Revision after PR 23's review (issue #8, the instrument) — Shaping Notes

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The findings of the one review on PR 23 (fromtheoutfit/patchbay-vital#23, `VitalInstrument`,
closes #8): issue comment 6922873382, "Review of 63ad5ae", by the owner, 2026-11-16 16:47 UTC.
Seventeen findings, deduplicated and, in the review's words, "not yet verified, so treat them as
leads to check, not confirmed defects". Each is checked against the code at 63ad5ae and against
core at `eddba95`, then fixed, declined or probed as the owner decided. The branch is the PR's.
Nothing is committed, pushed or posted by an agent.

The findings, by the review's numbers and headings:

| # | Finding | Where |
|---|---|---|
| 1 | `set` skips the plugin when the value equals the one `get` shows | `instrument.py:278` |
| 2 | Floats the scale cannot hold are handled by a special case, not one normalisation path | `instrument.py:278` |
| 3 | `load_patch` and `set` hold different floats for the same value | `patch.py:143` |
| 4 | A failed rollback breaks "`PatchRejectedError` ... changing nothing" | `instrument.py:324` |
| 5 | Overlapping notes of the same pitch and channel share note-offs | `midi.py:64` |
| 6 | The version comparison is fragile | `instrument.py:140` |
| 7 | `check_loadable` decodes the wavetables, lfos and sample sections a second time | `instrument.py:170` |
| 8 | `patch()` rebuilds `patch_of(self._preset)` on every call | `instrument.py:346` |
| 9 | A render scans the buffer several times | `instrument.py:406` |
| 10 | `patch._METADATA` is written out by hand | `patch.py:84` |
| 11 | `patch._same` repeats `format._same` | `patch.py:146` |
| 12 | `start._json` and `start._object` repeat `format._string` and `format._object` | `start.py:72` |
| 13 | Slot keys are parsed by hand | `instrument.py:173` |
| 14 | `check_loadable` lives in the module that needs pedalboard | `instrument.py:117` |
| 15 | The known-limits text does not match its own list | `instrument.py:24` |
| 16 | The `files.py` docstring is stale | `files.py:19` |
| 17 | Two nearly identical gate negative-test transcripts are committed | the instrument spec's `verification/` |

## What was checked while shaping

- **Findings 1 to 3 are real as described.** `set` compares `value.value != old.value` and does
  nothing else when they are equal (63ad5ae `instrument.py:278`). `_float_of` keeps the curve's
  float32 on a linear scale (`patch.py:143`), where `set` stores `MappedParameter.to_preset`.
  Decisions 7 and 8 of #8 made both on purpose.
- **Finding 4 is the documented behaviour,** held by
  `test_a_plugin_that_refuses_the_model_s_own_text_too_is_the_host_s_error`.
- **Finding 5 is documented in `midi.py`** ("as MIDI has it"), and no test holds it. What Vital does
  with it is unmeasured.
- **Core at eddba95,** read in the installed `patchbay` package:
  - No contract test needs every parameter in `patch().values`. `Patch`'s docstring opens "An
    instrument's state: a value for each parameter, and the sections it does not interpret."
    That fired the owner's first stop, below.
  - `FakeInstrument` renders "a sine per note at the note's pitch, … cut at the note's end", each
    note summed into one buffer on its own. So two overlapping notes of one pitch each sound for
    their own length. That fired the second stop.
  - Nothing in `contracts.py` or the contract tests says an instrument must stay usable after
    any error it raises. So finding 4's answer goes ahead without a stop.
- **The 22 floats of the start preset that no set lands on,** from the instrument spec's
  `verification/off-grid-count.txt`: `chorus_feedback`, `compressor_band_lower_ratio`,
  `compressor_high_lower_ratio`, `compressor_low_lower_ratio`,
  `compressor_low_upper_threshold`, `env_1_decay_power` to `env_6_decay_power`,
  `env_1_release_power` to `env_6_release_power`, `osc_1_detune_power` to
  `osc_3_detune_power`, `reverb_chorus_frequency` and `reverb_high_shelf_gain`. Each is one or
  two float32 steps from what a set of its own display holds.

## Shaping answers

In the owner's words, 2026-11-16.

**Findings 1–3,** to "One rule: to_preset": "1. With these conditions:
- Before changing anything, check core: does any contract test or docstring require every
  parameter to appear in patch().values? If one does, stop and present.
- State the cost where a caller looks: patch()'s docstring and the README say values holds
  the parameters whose stored float a set of its display holds; the rest (22 on the start
  preset, listed by key in shape.md, and about 2,201 across the installed presets) are carried
  in opaque and read with get. Record in shape.md, as a note for the semantics-data spec, that
  a patch read without an instrument does not show those parameters.
- The keep rule's narrowed form is held by tests both ways: a set of the display shown on an
  off-grid float changes nothing; a set of the display shown on an on-grid float reaches the
  plugin, with the osc_1_stack_style case on an upgraded preset (model 9, plugin 10) as the
  example, measured against Vital.
- Recount the carrying on the fixture and the 75 presets, the byte-for-byte round trip
  included, and say what PatchLoaded.parameter_count now is for each form of patch.
- The contract suite is run again both ways against Vital (shared and fresh host), the
  mutation run covers the removed _float_of path, and draft 4 cites the new run."

**The stop on findings 1–3,** core's `Patch` docstring presented: "Neither 1 nor 2: values stays
complete, and the load rule is made precise.
- Finding 1: narrow the keep rule as option 3 says, with the tests both ways and the Vital
  measure of osc_1_stack_style.
- Findings 2 and 3: load_patch and the carrying check take a value this way: if the curve's
  float32 for the display shows exactly that display, the value names that float and it is
  stored; otherwise the value is taken as set takes it, record.to_preset(display). So a patch
  the instrument gave restores every float it carried, and an arbitrary display in a patch
  holds what a set of it holds. The start preset keeps Vital's defaults as they are and all
  903 stay in values; Decision 2 stands, with this rule added to it.
- Shown: on the fixture and the 75 presets every float carried in values is restored exactly
  (counted); on a labelled sample of arbitrary displays per continuous group, load_patch and
  set leave the same float; and the one case where they differ is stated and tested: a value
  that is exactly the display of an off-grid float is restored by a load and not by a set,
  which is core issue #20's case and is cross-referenced there.
- If the exact-naming test cannot be made sound (for instance a display two floats show),
  stop and present with the counts.
- The drafts for core gain one question regardless: "a value for each parameter" is not met
  for the 35 floats the installed presets carry in opaque (out of range, or not a
  parameter's), and core should say whether that is allowed.
- The contract suite is rerun both ways, and draft 4 cites the new run."

The first answer's conditions that rest on its option 1 (the cost stated as floats moved to
`opaque`, the note for the semantics-data spec in those words) are superseded by the second. The
rest hold: the tests both ways, the measure against Vital, the recount, the contract runs and the
mutation run, which covers the changed `_float_of` rather than a removed one.

**Finding 4,** to "Keep, state it plainly": "1. The docstring says what a caller does after it:
the plugin's state is unknown and the model holds the old preset, so the instrument should be
discarded and a new one built; say whether any later call on the same instrument is refused or
attempts a reload, and hold that with a test. The 0.1.0 draft notes it under the adapter's limits
and asks core nothing new, unless core's contract says an instrument must stay usable after any
raised error, in which case stop and present."

Then, to "Refuse, plugin untouched": "1. The error names the earlier failure and says to build a
new instrument, and the docstrings of set, load_patch and render say so. get's and patch()'s
docstrings say they still answer from the model after such a failure and that the plugin no
longer matches it. Tests on the fake plugin hold each call's behaviour in that state and that
nothing is published."

**Finding 5,** to "Cut the earlier note": "1. Check core first: if Pattern, Note or
FakeInstrument says what two overlapping notes of one pitch mean, follow that and say so; if core
is silent, do as proposed and add a line to the drafts for core noting the gap. In midi.py, say
and test what two notes of one pitch struck on the same sample do (which one sounds, with which
velocity and length), with the expected bytes written out in the tests. The integration measure
of B's length on Vital is taken under a window on the start preset, with a named tolerance."

Then, the stop presented (core's fake defines the meaning), to "Probe Vital, follow the fake": "1.
The probe's transcript records the two notes' measured lengths under a window on the start
preset, with the machine and Vital's version, for at least: an overlap of the same pitch, the
same pitch struck on the same sample, and a control of two different pitches. Whatever it finds,
the unit tests write the expected bytes out and the integration measure has a named tolerance.
shape.md records that the earlier answer on finding 5 was withdrawn because core's fake defines
the meaning."

**The earlier answer on finding 5, to cut the earlier note, is withdrawn,** because core's fake
defines what two overlapping notes of one pitch mean: each sounds for its own length.

**Finding 17,** to "Keep both": "1. Declined, citing fromtheoutfit/patchbay-standards#41 as
where the size of these transcripts is being decided. Add this spec's pair (about 26.6k lines
each) to #41's evidence in place, with a "Revised 2026-11-16" line, since this is the third time
a review has raised it."

**References, standards, visuals, product:** "Yes, as listed (Recommended)". The references are
the instrument spec and the PR 19 revision spec. The standards are the core tier and the nine in
"Standards Applied". There are no visuals, and `agent-os/product/` is unchanged.

**Findings 6 to 16** were not put to the owner one by one: the plan gives each a recommendation,
and the owner approved the plan as it stands.

## Decisions

1. **Finding 1: the keep rule is narrowed.**
   - In `set`, `held = record.to_preset(value.value)`.
   - The set is kept (model and plugin untouched, the event still published, `old` equal to
     `new`) only when the value equals the display shown **and** `held` is not the float the
     model holds, that is, when the model's float is one no set lands on.
   - Otherwise the plugin is set to `scale.to_normalized(held)` and the model updated. So
     `set(osc_1_stack_style, 9)` on an upgraded preset, model 9 and plugin 10, reaches the
     plugin.
2. **Findings 2 and 3: one load rule, for `load_patch` and for the carrying check.**
   - **On a linear scale,** let `c` be the curve's float32 for the display, kept within the
     scale's ends. When `record.to_display(c)` is exactly the display, the value names `c` and
     `c` is stored. Otherwise the value is taken as `set` takes it, `record.to_preset(display)`.
   - **On an indexed scale,** `record.to_preset`, as today. On an indexed scale the curve's
     float32 for a value between steps shows that value (`chorus_voices` 6), so the linear
     branch there would break #8's Decision 9, that a value between steps holds the nearest
     step on `set` and on `load_patch`. This is how the owner's rule applies on that scale.
   - The same function is the back of `patch_of`'s carrying check. Every float carried today
     came back as `c` itself, and then `c`'s display is the display, so every one is still
     carried: `values` can only grow.
   - The start preset keeps Vital's defaults, all 903 stay in its `values`, and #8's Decision 2
     stands with this rule added.
   - The one case where a load and a set differ: a value that is exactly the display of an
     off-grid float is restored by a load and not by a set. That is
     fromtheoutfit/patchbay#20's case. It is tested, and cross-referenced there.
   - **Stop and present with the counts** if the exact-naming test cannot be made sound, for
     instance a display two floats show breaks the round trip, or if any float carried today
     leaves `values`.
3. **Finding 4: a lost step.**
   - When the plugin refuses the new text and then refuses the model's own text too,
     `load_patch` raises the package's `PluginStateError`, naming both refusals and saying to
     build a new instrument. The instrument records that it has lost step with the plugin.
   - From then on `set`, `load_patch` and `render` raise `PluginStateError` naming the earlier
     failure and saying to build a new instrument. That is checked before anything else, the
     plugin is not called and nothing is published.
   - `get`, `patch`, `parameters` and `name` answer from the model still, and their docstrings
     say the plugin no longer matches it.
   - The 0.1.0 draft notes it under the adapter's limits and asks core nothing new.
4. **Finding 5: probe first, and follow core's fake.**
   - If Vital gives each of two overlapping notes of one pitch its own length with today's
     bytes, the bytes stay and finding 5 is recorded as not reproduced.
   - If the first note-off releases both, stop and present what the probe found, whether
     another channel gives each note its own voice among it.
   - Either way, `midi.py` says and tests what two notes of one pitch struck on the same sample
     do, the expected bytes written out.
5. **Finding 6.** Versions are compared with trailing zero parts dropped, so `1.6.4.0` is
   `1.6.4`. A plugin version that is not digits and dots refuses every preset by name, rather
   than leaving the comparison out.
6. **Finding 7: declined.** The second decode is measured beside the two loads on the largest
   installed preset (`verification/check-cost.txt`). A load of a 10 MB preset takes seconds.
7. **Finding 8: fixed.** The `Patch` is cached beside the model and dropped wherever the model is
   replaced.
8. **Finding 9, in part.** `_clipping` takes each sample's peak as the larger of the channels'
   maximum and the negated minimum, with no `np.abs` copy. Declined:
   - the second `isfinite`, since core's validator is core's, and the instrument's own check
     names the refusal as `RenderRefusedError` first;
   - giving `midi_of` the length, since `request.samples` is arithmetic and not a scan of the
     buffer.
9. **Findings 10 to 14: fixed.**
   - `format.py` names `METADATA` and a public helper saying whether two floats write the same,
     and `patch.py` uses both (10, 11).
   - `start.py` writes strings and objects through `format`'s writers. It keeps its own sorted
     `json.dumps` only for the nested sections, which `format` never writes, holding them as
     text (12).
   - `preset.py` gains one helper beside `SLOT_KEY` that gives a slot key's slot and field.
     `instrument._slot_field` goes (13).
   - `check_loadable` and its helpers move to `patch.py`, which needs no pedalboard, and the
     package root re-exports it (14).
10. **Findings 15 and 16: fixed.**
    - The known limits say that the first three each wait on an issue of their own, #20, #21 and
      #22, and that the fourth, the double load, is a measured workaround that no issue owns.
    - The CHANGELOG's count of limits is corrected.
    - `files.py`'s docstring says the census writes three files.
11. **Finding 17: declined.** The size of these transcripts is decided in
    fromtheoutfit/patchbay-standards#41. This spec's pair, about 26.6k lines each, is added to
    #41's evidence in place with a "Revised 2026-11-16" line, since this is the third review to
    raise it. The text is shown first and posted after the gate's clean run.
12. **For core.**
    - Draft 4, the 0.1.0 proposal held until the PR merges, is revised in the instrument spec's
      `shape.md` with a "Revised 2026-11-16" paragraph. It cites this spec's contract runs and
      finding 4's limit.
    - A new draft 5 asks whether "a value for each parameter" allows the 35 floats the installed
      presets carry in `opaque`.
    - A comment on fromtheoutfit/patchbay#20 cross-references Decision 2's one case.
    - Each is shown whole and filed or posted only at the owner's word, after the gate's clean
      run.
13. **No gate file changes,** and no file is added, removed or renamed under `scripts`, `src`,
    `tests` or `agent-os/standards`, so the negative harness is not rerun. If one has to be, the
    harness is rerun and this Decision corrected.

## A note for the semantics-data spec

A patch carries a parameter's value as the display the plugin shows, and the float behind it only
when no display carries it. A reader of a patch without an instrument sees the display, and cannot
tell an off-grid float from the on-grid neighbour that shows the same display to the digits
printed. The exact float is what `load_patch` restores (Decision 2). The 35 floats the installed
presets carry in `opaque`, outside their bounds or no parameter's, are not in `values` at all:
fromtheoutfit/patchbay#23 asks core whether that meets "a value for each parameter".

Recorded without acting on it, at the owner's word: on the start preset velocity 50 and 100
measure the same level, 0.143940 (`verification/overlap-probe.txt`), because `velocity_track`, the
parameter that would make velocity matter, is 0 % there. At 100 % a note of velocity 100 measures
0.089243 and one of 50 measures 0.022311 (`overlap-probe-2.txt`). A patch of values alone
therefore plays every velocity alike unless it sets `velocity_track`.

## What the probes showed

`verification/overlap-probe.txt` (2026-11-16 13:40 EST) and `overlap-probe-2.txt` (13:43 EST),
Vital 1.6.4 through pedalboard 0.9.26, arm64, Apple M4 Pro, macOS 26.6.2. Each render is on the
start preset at 48 kHz and 120 bpm, measured as RMS under a 20 ms Hann window every 5 ms. A level
is the median over a span, and an end is the last window centre at or above half of a note's
level alone. Trial runs came first and are not kept; every figure below is from the kept runs.

- **With today's bytes, one channel releases both notes at the first note-off.** Take C4 from 0
  to 1 s and C4 from 0.5 to 1.5 s, both on channel 0. The render ends at 1.015 s, where the second
  note alone ends at 1.510 s. Between 1.05 and 1.45 s it measures 0.000000, against 0.143940 for
  the second note alone. Two C4s struck on one sample, 1 and 3 beats long, both stop at the first end, at 0.515 s and
  0.525 s in the two orders.
  Three overlapping C4s on one channel (beats 0 to 3, 1 to 4, 2 to 5) all stop at 1.515 s. So
  finding 5 reproduces on Vital, and the review's lead was right.
- **On channels of their own, each note keeps its own length.** The two overlapping C4s on
  channels 0 and 1 end at 1.510 s, and the second measures 0.143944 between 1.05 and 1.45 s. The
  three on channels 0, 1 and 2 end at 2.510 s, C's own end, with MPE off and on alike. The two
  struck on one sample, on channels 0 and 1, end at 1.510 s.
- **A note alone sounds the same on any channel, with `mpe_enabled` off and on.** C4 on channel
  0, 1 or 2 measures 0.143940 between 0.55 and 0.95 s (0.143941 on channel 0 with MPE off) and has
  a centroid of 815.96 Hz, in both settings. The owner's stop for MPE ("if a moved note sounds different there") therefore did not
  fire.
- **Two voices of one pitch sum differently with MPE on,** on one channel or two alike. With MPE
  off, the two struck on one sample measure 0.287879 on two channels and 0.235966 on one; with MPE
  on, 0.160817 and 0.145788. Moving a note does not cause this: today's one-channel bytes show the
  same difference. It is recorded as an observation, with no cause claimed.
- **With `velocity_track` at 100 %, each moved note keeps its own velocity.** Of the two struck on
  one sample, the velocity-50 note measures 0.022310 from 0.55 to 0.95 s, after the velocity-100
  note has ended, where it measures 0.022311 alone.

## The owner's answer after the probe

The stop was presented on 2026-11-16 as "Free channel per note", and the owner answered: "1.
Before relying on it, probe and record:
- three overlapping notes of one pitch, and two struck on one sample, each sounding its own
  length under a window;
- the same with Vital's MPE setting on, if the map has one (say which parameter), since under
  MPE a channel carries per-note expression: if a moved note sounds different there, stop and
  present.
In midi.py: the rule is stated in the docstring (a note keeps its own channel unless its
pitch is already sounding there; then the lowest channel where it is not), the expected bytes
in the unit tests are written out, and the refusal of a 17th overlapping note names the pitch
and the sample. A line joins the drafts for core: Note carries a channel, the fake sums a
sine per note, and core does not say what an adapter does when one channel cannot voice two
notes of one pitch.
Record the side finding in shape.md without acting on it: on the start preset velocity 50 and
100 measure the same level, with the parameter that would make velocity matter, as a note for
the semantics-data spec."

The map's MPE parameter is `mpe_enabled`, a boolean, default 0. `overlap-probe-2.txt` is the
probe that answer asked for.

## Decisions made on the probes

14. **A note keeps its own channel unless its pitch is already sounding there; then it goes out on
    the lowest channel where it is not,** both its note-on and its note-off.
    - A pitch is sounding on a channel from its note-on to its note-off. A note released on a
      sample therefore frees its channel for a note struck on that sample.
    - A note too short to last a sample is released after every note-on of its sample, so it does
      not free its channel.
    - Of two notes struck on one sample, the first in the pattern keeps its channel.
    - A seventeenth note of one pitch sounding at once is `RenderRefusedError`, naming the pitch
      and the sample.
    - This departs from "the bytes are core's `Note` as it is" for the moved note's channel only.
      Core's fake decides the meaning (each note sounds for its own length), and the probe shows
      the way to reach it on Vital.

## What was built

- **Changed modules:**
  - `instrument.py`: the narrowed keep rule; the lost step; the patch built once per model; the
    clipping peak without a copy; slot keys through `preset`. The guard and its helpers moved out.
  - `patch.py`: the load rule in `_float_of`; `check_loadable` with the version rule; `format`'s
    metadata and same-float helper.
  - `midi.py`: the channel rule and the refusal.
  - `format.py`: `METADATA`, `writes_same`, `write_string` and `write_object` made public, and
    `slot_key` taken from `preset`.
  - `preset.py`: `SLOT_KEY` with named groups, `slot_key` and `slot_place`.
  - `start.py`: strings and objects through `format`'s writers.
  - `errors.py`: two docstrings.
  - `files.py`: its docstring.
  - `__init__.py`: `check_loadable` re-exported.
- **No file is added, removed or renamed** under `scripts`, `src`, `tests` or
  `agent-os/standards`, so Decision 13 stands and the negative harness is not rerun. No gate file
  changes, no dependency is added, and the version stays 0.0.1.
- **Tests:** a unit test of each side of the keep rule, the load rule (a labelled sample of 25
  displays a group over 55 groups, seed 23), the one case where a load and a set differ, the
  patch cache, the lost step (three tests, one parametrized five ways), the versions, and
  `test_midi.py`'s eight new tests with their bytes written out. Two integration tests: the
  stack-style set on Ah Eh Ee Oh and the overlap measure under the probes' window. The tests the
  revision replaced: `test_a_plugin_that_refuses_the_model_s_own_text_too_is_the_host_s_error`
  (by the lost-step tests) and `test_a_value_goes_to_the_float_a_preset_holds_for_it` (by
  `test_a_value_goes_to_the_float_a_set_of_it_holds_unless_it_names_a_float`).
- **`tests/unit/builders.py`** gains `what_a_set_holds`, which `test_instrument.py` had as a
  private helper, so `test_patch.py` uses the same primitives and not a second copy.

## What the transcripts show

All of these ran 2026-11-16 on a still tree, each printing the tree and the machine before and
after. The two printouts match in every transcript, compared after each run. Each embeds the
scripts it ran.

- **`carrying-count.txt` (13:59 EST):** the start preset, the fixture and the 75 installed
  presets, 77 texts and 59,477 floats.
  - 59,442 are carried in `values`, as many as under the rule before this revision. None is in
    `values` now and not before, and none the other way, so Decision 2's stop did not fire.
  - 35 are carried in the preset entry, the same 35 as before.
  - All 59,442 are restored exactly by a load of the patch, and 77 of 77 texts come back byte
    for byte through a patch and through its JSON.
  - `PatchLoaded.parameter_count` is 903 for a whole patch of the start preset, 2 for a patch of
    two values alone, and 770 for a whole patch of Ah Eh Ee Oh, whose one entry float is outside
    `values`. Each is the patch's own count of values.
- **`load-and-set-sample.txt` (14:00 EST):** 55 continuous groups, 2,000 displays each, drawn by
  `numpy.random.default_rng(20261116).uniform`. On all 110,000 a load and a set leave the same
  float, and none drawn was a display naming its own float. It is a sample, not a count.
- **`check-cost.txt` (14:00 EST):** the guard, best of 5, beside the two loads.
  - On Float Chords, the largest installed preset at 10,126,117 bytes: 4.96 ms against 487.30 ms,
    1.0 % of the loads. The three sections' decode alone measured 5.34 ms, best of 5, more than
    the whole guard, so the two figures are within each other's noise.
  - On the start preset: 0.31 ms against 8.16 ms.
  - Finding 7 is declined on these figures.
- **`contract-run.txt` (14:01 EST):** core's thirteen at `eddba95`. 13 of 13 on the module's one
  Vital, 13 of 13 on a `VitalHost` of its own for each test, and 13 of 13 over the fake plugin,
  which is not a pass against Vital.
- **`mutation.txt` (14:01 EST):** 23 mutants, one per rule this revision changed, each on a
  scratch copy outside the tree, and 0 survived. Each fails the test named beside it, among them
  MK2 and MK3 (the keep rule as it was, in a unit test and against Vital), MD1 to MD3 (the load
  rule's three branches), MS1 to MS4 (the lost step), MV1 and MV2 (the versions), and MM5 to
  MM10 (the channel rule, MM6 against Vital).
- **`overlap-probe.txt` and `overlap-probe-2.txt`:** see "What the probes showed".

## Drafts for the owner

Each was shown whole and filed or posted only at the owner's word, after the gate's clean run.
None carries attribution.

**The owner's answer, 2026-11-16, after the gate:** "All three, changed as follows:
- patchbay#20: revise the issue's body in place with a "Revised 2026-11-16" paragraph, not a
  comment: the case where a load restores a float a set does not, and the narrowed keep rule.
- Draft 5 becomes two issues on fromtheoutfit/patchbay, one question each, as #20 to #22 are:
  "a value for each parameter" against the 35 floats carried in opaque; and what an adapter
  does when one channel cannot voice two notes of one pitch. Draft 4 (0.1.0) then lists both
  among what core does not say yet.
- patchbay-standards#41: revised in place as drafted.
Each read back. Draft 4 stays held until the pull request merges."

**What was done, the same day:**
- fromtheoutfit/patchbay#20's body is revised in place: its text is kept and a "Revised
  2026-11-16" section is added, draft 2 below reworded from a comment into that section.
- Draft 5 is filed as two issues: fromtheoutfit/patchbay#23, "Patch: "a value for each parameter"
  and a float no display carries", and fromtheoutfit/patchbay#24, "Note: two overlapping notes of
  one pitch on one channel". #24 gives the measurements and what patchbay-vital does, which
  draft 5's one paragraph did not.
- fromtheoutfit/patchbay-standards#41's body is revised in place as drafted, its text kept.
- Each was read back with `gh api` and matches the text it was written from, trailing
  whitespace aside.
- Draft 4 in the instrument spec lists #23 and #24 among what core does not say yet, and stays
  held.
- The reply to PR 23 is the owner's to post; it names #24 under finding 5.

### 1. Reply to PR 23's review, for the owner to post on fromtheoutfit/patchbay-vital#23

> Revised in `agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`. Each finding was checked against the code at `63ad5ae` and core at `eddba95` first.
>
> 1. **Fixed.** A set of the value shown is kept only where the model holds a float no set lands on. Any other set reaches the plugin, so on Ah Eh Ee Oh, where the model holds `osc_1_stack_style` 9 and Vital plays 10, a set of 9 leaves Vital holding 9. A unit test covers each side of the rule and an integration test covers this case on Vital.
> 2. **Fixed, with finding 3.** A full normalisation path is not possible: a loaded preset and the start preset hold floats no set lands on (22 of the 903 defaults), and the byte-for-byte round trip keeps them. One rule now decides both what a patch carries and what a load stores (below). The narrowed keep rule applies only to those floats, and both of its sides are tested.
> 3. **Fixed.** `load_patch` and the carrying check take a value the same way. If the curve's float32 for a display shows exactly that display, the value names that float and the float is stored. Otherwise it is stored as a set stores it. Every float a patch carries is restored: 59,442 of 59,442 on the 77 texts on hand, the same 59,442 carried before. On a labelled sample of 110,000 arbitrary displays across 55 groups, a load and a set leave the same float on all of them. The one case where they differ is a display that is exactly an off-grid float's own. It is tested, and is fromtheoutfit/patchbay#20's case.
> 4. **Fixed, differently.** Raising core's `PatchRejectedError` there would claim nothing changed. Instead, the instrument records that it has lost step: `PluginStateError` names both refusals and says to build a new instrument. Every later `set`, `load_patch` and `render` is refused naming that failure, with nothing published, while `get` and `patch` answer from the model.
> 5. **Fixed.** It reproduces on Vital: on one channel the first note-off releases both notes. Core's `FakeInstrument` gives each note its own length, so a note whose pitch already sounds on its channel now goes out on the lowest channel where it does not. This was measured with Vital's MPE setting off and on (`verification/overlap-probe.txt`, `overlap-probe-2.txt`). A 17th note of one pitch sounding at once is refused by name. Whether that is core's meaning is put to it as fromtheoutfit/patchbay#24.
> 6. **Fixed.** Versions are compared with trailing zeros dropped, and a plugin version that is not digits and dots refuses every preset by name.
> 7. **Declined.** On the largest installed preset, 10 MB, the guard takes about 1 % of the two loads it precedes (`verification/check-cost.txt`).
> 8. **Fixed.** The patch is built once per model.
> 9. **In part.** The clipping peak no longer copies the audio. The second `isfinite` stays, because core's validator is core's and ours names the refusal first. `midi_of` keeps computing the length, which is arithmetic, not a scan.
> 10. **Fixed.** `patch.py` uses `format.METADATA`.
> 11. **Fixed.** One `format.writes_same`.
> 12. **Fixed.** `start.py` writes strings and objects through `format`'s writers. Its own writer remains only for the nested sections, which `format` never writes.
> 13. **Fixed.** `preset.slot_key` and `preset.slot_place` are now the only code that builds or reads a slot key.
> 14. **Fixed.** `check_loadable` is in `patch.py`, re-exported at the root, and needs no plugin.
> 15. **Fixed.** The first three limits each wait on an issue; the double load is a workaround no issue owns. The CHANGELOG is corrected to match.
> 16. **Fixed.**
> 17. **Declined.** The size of these transcripts is being decided in fromtheoutfit/patchbay-standards#41. This pair is added to its evidence.

### 2. For fromtheoutfit/patchbay#20, the one case where a load and a set differ (drafted as a comment; its body revised in place instead, at the owner's word)

> Since patchbay-vital's revision after the review of its PR 23 (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`), the case has a second side.
>
> - **`load_patch` restores what `set` does not.** A patch value that is exactly the display of a float no set lands on names that float, and loading the patch restores it. Setting the same display holds the neighbour on the grid. That is how a patch the instrument gave back restores every float it carried. Every other display, arbitrary ones included, loads to what a set of it holds, on a sample of 110,000.
> - **`set(get())` still changes nothing,** but the rule behind it is narrower. A set of the value shown is kept only where the held float is one no set lands on. On any other float it reaches the plugin, so the plugin goes back to the model's float after Vital upgrades a preset older than it.
>
> `test_a_display_that_is_an_off_grid_float_s_own_is_restored_by_a_load_and_not_by_a_set` holds it, naming this issue. The candidate wordings above are unchanged by it.

### 3. Draft 5 for fromtheoutfit/patchbay (filed as two issues, #23 and #24, at the owner's word)

> **Title:** Patch: "a value for each parameter" and a float no display carries
>
> `Patch`'s docstring at `eddba95` opens: "An instrument's state: a value for each parameter, and the sections it does not interpret." No contract test checks it.
>
> ## The case
>
> patchbay-vital's `VitalInstrument.patch()` puts in `values` every parameter whose preset float its display can name. A float no display names is carried as the float itself in `opaque`, so a patch keeps a preset byte for byte. Of the 59,477 floats in the 77 presets on hand (the start preset, a fixture and the 75 Vital installs), 35 are carried that way:
>
> - 32 are outside their parameter's bounds: `flanger_dry_wet` 0.7072 shows 141.44 against 0 to 100, and `get` returns that;
> - 3 are `chorus_damping`, a key older presets hold that no parameter has.
>
> The evidence is `verification/carrying-count.txt` in `agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/` on patchbay-vital's branch for its issue #8. A key a preset lacks is in neither place and reads as its default.
>
> ## The question
>
> Does "a value for each parameter" allow this: a parameter missing from `values` whose float rides in `opaque`, and which `get` still reads? If it does, the docstring could say "a value for each parameter it can name" (or similar). If it does not, an adapter must put some value in `values` for those 32: a bound, losing the preset's own, or a display `set` refuses.
>
> Separately, `Note` carries a channel and `FakeInstrument` sums a sine per note, so two overlapping notes of one pitch each sound for their own length. Core does not say what an adapter does when one channel cannot voice two notes of one pitch. On Vital the first note-off releases both, so patchbay-vital moves the later note to a channel of its own. If that is core's meaning, `Instrument.render` or `Note` could say so.

### 4. A revision of fromtheoutfit/patchbay-standards#41, a paragraph added in place (done as drafted)

> **Revised 2026-11-16.** A third review has raised it: patchbay-vital's PR 23, https://github.com/fromtheoutfit/patchbay-vital/pull/23 (the review of `63ad5ae`, finding 17). The instrument spec, `agent-os/specs/2026-11-15-1448-the-instrument/verification/`, commits two whole runs of the harness, `gate-negative-tests-first.txt` and `gate-negative-tests.txt`, about 26,600 lines each. The owner kept both, the first for the note on what its wrapper got wrong. The finding was declined in favour of this issue. The extract this issue proposes would have committed the two as their heading and exit lines and count, with the wrapper's note.

### 5. Draft 4's revision, added in place in the instrument spec's shape.md

Draft 4 stays held until the pull request for #8 merges. Its revision is written there, beside
the draft, and reads:

> **Revised 2026-11-16, after the review of PR 23** (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`). When it is filed, "The run" cites that spec's `verification/contract-run.txt`: 13 of 13 on the module's one Vital and 13 of 13 on a `VitalHost` of its own for each test, on the code the review revised. The gate's figures are taken from the run on the merged commit. "The adapter's limits" gains one line, and asks core nothing new:
>
> - When the plugin refuses a load and then the model's own text, its state is unknown. `load_patch` raises patchbay-vital's `PluginStateError`, which is not `PatchRejectedError`, and the instrument refuses every later call that would reach the plugin, saying to build a new one.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, unchanged. The revision keeps the
  instrument's sentence there true.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `vital/instrument` — every rule this revision changes: the keep rule, the carrying rule, the
  guard, the lost step, MIDI.
- `vital/parameter-map` — `to_preset` and the curve, which the load rule reads and does not
  change; a claim over values that cannot be enumerated is a labelled sample.
- `vital/measures` — the overlap measure under a window, with a named tolerance from the probe.
- `vital/plugin-state` — what Vital does with a load and an upgraded preset (#22's case).
- `vital/preset-file` — `format.py`'s writers and metadata, `SLOT_KEY`.
- `vital/preset-tests` — the installed presets read against the manifest, skipped where absent.
- `base/testing/tests` — expected values from primitives, tests mirroring the source.
- `base/python/events` — nothing published on a refusal, the lost step's included.
- `base/process/verification-gate` — the gate unchanged, its record, when the harness reruns.

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

**Results (2026-11-16):** `scripts/gate.sh` exits 0 on branch
`feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`,
all six steps. 801 tests passed and none skipped, in 78 s, with Vital and its presets installed;
the PR's head had 777. The record is `verification/gate-run.txt`: the date and branch, the machine
and the tree before and after by blob, and the script it ran. It ran once, after the
retrospective's edits and every other transcript.

- **Every evidence transcript ran on the code the gate ran on.** By the blobs each prints, the
  trees of `carrying-count.txt`, `load-and-set-sample.txt`, `check-cost.txt`, `contract-run.txt`
  and `mutation.txt` differ from the gate's tree only in this spec's records, the instrument
  spec's `shape.md` (draft 4's revision) and the four standards files of the retrospective. No
  path under `src/`, `tests/` or `scripts/` differs, nor `README.md`, `CHANGELOG.md`,
  `pyproject.toml` or `uv.lock`.
- **The two probes ran on the code before the revision, by design:** they measure what today's
  bytes do, and the second gives the moved channels explicitly.
- **The negative harness was not rerun.** No gate file changed, and no file was added, removed or
  renamed under a directory it copies (Decision 13).
- **Written after the gate's run:** this paragraph; in "Drafts for the owner", the owner's answer,
  what was done and the issue numbers; the issue numbers in "A note for the semantics-data spec",
  the retrospective's deviation and the reply's finding 5; and draft 4's two lines in the
  instrument spec. No file the gate reads has changed since it ran.

**Docs (step 7):** checked, and each reads true after the change.
- `README.md`, "The instrument": what a set holds and a patch's value, what `values` names, each
  note's own length, and the lost step. "Known limits" says the first three each wait on an issue
  and lists the double load as the fourth, a workaround no issue owns.
- The module docstrings of `instrument.py`, `patch.py`, `midi.py`, `files.py`, `start.py` and
  `__init__.py`.
- The method docstrings of `get`, `set`, `load_patch`, `patch` and `render`, and of `_float_of`,
  `check_loadable` and the new helpers.
- The docstrings of `PluginStateError` and `RenderRefusedError`.
- `CLAUDE.md` names nothing this changes.
- Every standard that names a moved or renamed function: `vital/plugin-state.md` named
  `instrument.py` for `check_loadable` and `vital/preset-file.md` named `format._same`, and both
  are corrected in the retrospective below.
- `agent-os/product/mission.md` still reads true.
- Draft 4 in the instrument spec gains its "Revised 2026-11-16" paragraph.

**Version (step 8):** `CHANGELOG.md` under `[Unreleased]`:
- `### Changed` gains "Revision after the review of PR 23", saying what each finding came to.
- The instrument's entry under `### Added`, unreleased, reads as the revision leaves it: the keep
  rule, the load rule, `check_loadable`, the channel rule, the lost step, and the limits counted
  right.
- The version stays 0.0.1; no release is cut.

## Standards Retrospective

Step 9, always last, per `agent-os/standards/base/process/standards-retrospective.md`, written
from the shipped diff. Each edit is verified against the shipped code and tests it names, every
cited test name checked to exist under `tests/`. These are their own change set, apart from the
feature's.

- `agent-os/standards/vital/instrument.md`:
  - **The keep rule, narrowed.** Kept only where the model's float is one no set lands on; any
    other set reaches the plugin. Verified against `instrument.py` (`set`) and the keep-rule
    tests both ways, the Ah Eh Ee Oh test against Vital among them, and MK1 to MK3.
  - **"A value is taken one way"**, a new rule. Verified against `patch.py` (`_float_of`), the
    three load-rule tests, `carrying-count.txt`, `load-and-set-sample.txt` and MD1 to MD3. "A
    float is carried in exactly one place" now refers to it.
  - **The guard.** It lives in `patch.py` and needs no plugin, versions are compared less
    trailing zeros, and a plugin version that is not digits and dots refuses every preset.
    Verified against `check_loadable`, the two version tests, MV1 and MV2.
  - **"When the plugin refuses the model's own text too, the instrument has lost step"**, a new
    rule. Verified against `instrument.py` (`load_patch`, `_refuse_once_lost`), the three
    lost-step tests and MS1 to MS4.
  - **"Each note sounds for its own length"**, a new rule, recording the pattern this revision
    invented: where core's protocol leaves a meaning open and its reference instrument shows one,
    the reference decides, and a probe of Vital shows how to reach it. Verified against `midi.py`,
    `test_midi.py`, the overlap measure against Vital, both probes and MM5 to MM10.
  - The case of core's clause names fromtheoutfit/patchbay#20 by number, now that it is filed.
  - The header names this revision's transcripts.
- `agent-os/standards/vital/plugin-state.md`:
  - **"On one channel, a note-off releases every voice of its pitch; on another channel a note
    keeps its own"**, a new measured rule, with the MPE observation stated without a cause, and
    `velocity_track` at 0 % on the start preset. Verified against `overlap-probe.txt`,
    `overlap-probe-2.txt` and the overlap measure.
  - `check_loadable` is named in `patch.py`.
- `agent-os/standards/vital/preset-file.md`:
  - "Two presets are the same when they write the same bytes" names `format.writes_same`, the one
    helper the diff, the carrying check and the keep rule use (MF1).
  - The slot rule says a slot key is written and read only by `preset.slot_key` and
    `preset.slot_place`, checked by grep over `src/` (MF2).
- `agent-os/standards/index.yml`: the `vital:` entries `instrument` and `plugin-state` updated for
  the above. The `base:` section is untouched.
- **Deviation, not a standard change:** the moved note's channel departs from `midi.py`'s "the
  bytes are core's `Note` as it is", for that one byte. It is stated in `midi.py` and in
  `vital/instrument.md`, and it stays this adapter's until core says what a channel that cannot
  voice two notes of one pitch means (fromtheoutfit/patchbay#24).

No base standard is changed or proposed. The rule that a reference instrument decides an open
meaning is any adapter's, but the owner held the same kind of rule on 2026-11-16 ("project
standard in vital/instrument.md until a second adapter shows what is common"), so it is written
here as a project rule and not proposed.

Proposals sent upstream: none
