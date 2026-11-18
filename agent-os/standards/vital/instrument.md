# The instrument

What `VitalInstrument` promises beyond core's protocol, and what a later Vital feature must not
break. A rule here is about Vital as an instrument; what the hosted plugin does is
`vital/plugin-state.md`'s, the map's conversions `vital/parameter-map.md`'s, and how a test asserts
audio `vital/measures.md`'s. Written from `src/patchbay_vital/instrument.py`, `patch.py`, `midi.py`
and `start.py`; the evidence is the `verification/` of the spec of issue #8
(`agent-os/specs/2026-11-15-1448-the-instrument/`), every measurement in it made on Vital 1.6.4
through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2): `probes.txt`, `probes-2.txt`,
`contract-run.txt`, `carrying-count.txt`, `off-grid-count.txt` and `mutation.txt`, and of the
revision after PR 23's review (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`):
`overlap-probe.txt`, `overlap-probe-2.txt`, `carrying-count.txt`, `load-and-set-sample.txt`,
`check-cost.txt`, `contract-run.txt` and `mutation.txt`, and of the revision after its second review
(`agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/`): `upgraded-set-count.txt`,
`mutation.txt` and `contract-run.txt`, and of the spec of issue #20
(`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`): `probes-4-counts.txt`,
`arrays-seen.txt`, `rollback-count.txt`, `remedy-run.txt`, `silent-and-loaded.txt` and
`mutation.txt`, and of the revision after the review of PR 26
(`agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`): `rollback-count.txt`,
`remedy-run.txt` and `mutation.txt`, made on its final tree, and of the revision after its second
review (`agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/`): `rollback-count.txt`,
`remedy-run.txt` and `mutation.txt`, made again on its final tree. Each rule names the test that
holds it;
a unit test runs over a fake plugin, so CI holds it, and a test of
`tests/integration/test_vital_instrument.py` runs against the installed Vital.

## The model

- **The model is the source of truth, and the plugin's state never becomes it.** The instrument
  holds a `VitalPreset`: `get` reads it, `patch` carries it, `set` writes through to it and to the
  plugin, `load_patch` replaces it and sends its text. Not even the first model comes from the
  plugin: the instrument starts on the preset the package ships. Verified against
  `test_it_starts_on_the_start_preset_loaded_into_the_plugin_twice`, which gives the plugin a state
  of its own first, and `test_the_next_instrument_starts_clean`.
- **The plugin's own view is a diagnostic read, used by tests alone.** `instrument.host.state()` is
  what the plugin holds; a test reads it to hold the plugin to the model, and no method of the
  instrument reads it. `instrument.preset` is the model. Verified against
  `test_after_a_set_at_each_bound_the_plugin_holds_the_model_s_float` (1,806 bounds, counted) and
  ML1 in `mutation.txt`.
- **The start preset is generated, never edited, and cannot drift.** `data/start.vital` holds the
  map's 903 defaults, 64 empty slots and media of the package's own, each from a formula: a ramp as
  each wavetable, two-point lines, a 16-sample ramp. The census writes it beside the map and the key
  list, all three together or none. It holds none of Vital's presets, wavetables, samples or LFO
  shapes; shipping it is the owner's licence call of 2026-11-15, revisited before any release.
  Verified against `tests/unit/test_start.py` (every float, every section rebuilt from its formula
  there, the file byte for byte through the format),
  `test_the_three_committed_files_are_what_the_census_writes_from_the_committed_map`,
  `test_the_census_regenerates_the_three_committed_files`,
  `test_a_rename_failing_at_the_start_preset_puts_the_key_list_and_the_map_back` and the instrument
  spec's MS1, MS2 and MC1.

## What a set holds

- **A set holds the value Vital holds for the display given, the map's `to_preset`, and no other
  rule.** `get` then returns that value's display and `ParameterChanged.new` carries it. It need not
  be the held value nearest the one given: `beats_per_minute` given 216.85141355537831 holds
  216.8514347076416. A second rule beside the map's is what issue #16 removed. Verified against
  `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest`, in both test modules, its
  expected value from primitives, and the instrument spec's MR1.
- **A bound comes back exactly.** Verified against
  `test_every_bound_of_every_parameter_comes_back_exactly`, 1,806 counted, and core's
  `get_after_set_returns_what_was_set`.
- **A value between steps is taken and the nearest step held,** a half away from zero. 29 continuous
  parameters are stepped, and not all in whole numbers: `chorus_voices` runs in fours and
  `oversampling` in powers of two. Core's `Parameter` does not show a step. Verified against
  `test_a_value_between_steps_is_taken_and_the_nearest_step_held`.
- **A set of the value a parameter already shows keeps what it holds only where that is a float no
  set lands on,** in the model and the plugin, and is still published, `old` equal to `new`. A preset
  holds such floats, 22 of the 903 defaults and 2,201 of the 57,671 floats of the installed presets,
  and a set of such a float's own display would hold a neighbour. Any other set reaches the plugin,
  one of the value shown on a float a set lands on among them.
  Verified against `test_a_set_of_the_value_already_shown_keeps_what_is_held`, 22 counted,
  `off-grid-count.txt`, `test_a_set_of_the_value_already_shown_on_a_float_a_set_lands_on_reaches_the_plugin`
  and MK1 to MK3 of the first revision's `mutation.txt`.
- **What a set of the value shown does to a float Vital upgraded is counted, and is not a rule.**
  Where Vital upgraded a preset's float as it loaded it (issue #22), a set of the value `get` shows
  puts Vital on the model's float only where the parameter takes that value and the model's float
  is one a set lands on. Of the 46 such floats on the installed presets, 42 are mended so. 3 are
  refused, `flanger_center` on Touch Tone, Memory Leak and Oolacile Evil Dubstep Bass, whose file
  value shows a display outside 8 to 136. 1 is kept, `modulation_10_amount` on Oolacile Evil Dubstep
  Bass, 0.19999998807907104 in the model and 0.07499999552965164 played: no set can mend it, the
  plugin taking a float only through a normalized value, and what the model should hold is issue
  #22's to decide. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS
  26.6.2). A consequence drawn from one float, as this one first was from Ah Eh Ee Oh's, is stated
  of that float alone until it is counted over the recorded set, the exceptions written out.
  Verified against
  `test_a_set_of_the_value_shown_mends_42_of_the_upgraded_floats_is_refused_on_3_and_kept_on_1`,
  `test_a_set_of_the_value_shown_on_an_upgraded_float_sets_vital_to_the_model_s` (Ah Eh Ee Oh's
  `osc_1_stack_style`, 9 held and 10 played),
  `test_a_set_of_the_value_shown_on_an_upgraded_float_no_set_lands_on_leaves_the_plugin_upgraded`,
  the second revision's `upgraded-set-count.txt` and its MK1.
- **A test that compares something with a set makes the set from another value, and counts it at
  the plugin.** A set of the value a parameter already shows can be the keep rule's no-op, and it
  then agrees with whatever float came before it. So a test of a load against a set sets first, on
  the start preset, asserts the plugin received each set, and loads afterwards. Its sample holds a
  display two floats show, where a load could take the wrong one and the no-op hide it: `volume`'s
  minimum, shown by 0 and by the float32 next above it, which a uniform draw never reaches. Verified against
  `test_an_arbitrary_display_in_a_patch_holds_what_a_set_of_it_holds` and the second revision's
  `mutation.txt`, where MD4, a load that takes another float showing the display, passes that
  test as it was at `64863c6` and fails it as it is.
- **One case of core's clause is not met, and a characterization test holds it.** A float off the
  grid, once another value has been set, is not got back by a set of the display `get` first
  returned for it: the parameter holds the neighbour. Verified against
  `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour` and, against the
  installed Vital, `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour_on_vital`,
  each naming by its title the issue filed for core, fromtheoutfit/patchbay#20.

## A patch

- **A float is carried in exactly one place.** In `values`, as the display that carries it, where
  the display passes `Parameter.check` and converts back to the very float by the rule below,
  checked for that float as the patch is built; otherwise in `opaque["preset"]`, as itself. Never
  both: a patch that carries one parameter twice is refused by name. So every entry of `values` is
  one `set` takes. Verified against `test_a_float_is_in_values_or_in_the_entry_and_never_in_both`,
  `test_a_float_its_display_cannot_carry_rides_in_the_entry_though_it_is_in_range`,
  `test_a_parameter_carried_in_both_places_is_refused_by_name` and the instrument spec's MP1, MP2
  and MP3.
- **A value is taken one way, by `load_patch` and by the carrying check alike.** On a linear scale,
  the curve's float32 for the display, kept within the scale's ends, where that float's own display
  is exactly the one given: the display names it, and it is stored. Any other value, and every
  value on an indexed scale, is taken as `set` takes it, `MappedParameter.to_preset`. So a patch the
  instrument gave restores every float it carried, and an arbitrary display in a patch holds what a
  set of it holds; the one difference is a display that is exactly an off-grid float's own, which a
  load restores and a set does not, fromtheoutfit/patchbay#20's case. No second rule beside the
  map's is made for a load: a value no float's display names goes through `to_preset`. Verified
  against `test_a_value_goes_to_the_float_a_set_of_it_holds_unless_it_names_a_float`,
  `test_an_arbitrary_display_in_a_patch_holds_what_a_set_of_it_holds` (a sample, 55 groups, 25
  uniform rounds of seed 23 and each bound, 1,485 displays),
  `test_a_display_that_is_an_off_grid_float_s_own_is_restored_by_a_load_and_not_by_a_set`,
  the first revision's `carrying-count.txt` (59,442 carried and 59,442 restored, as many as
  before), `load-and-set-sample.txt` (110,000 displays, 55 groups) and MD1 to MD3, and the second
  revision's MD4.
- **A preset comes back byte for byte,** through a patch and through the patch's JSON, a key it
  lacks staying absent. Verified against
  `test_a_built_preset_comes_back_byte_for_byte_through_a_patch_and_through_json`,
  `test_a_factory_preset_round_trips_through_a_patch`,
  `test_a_pack_preset_round_trips_through_a_patch`,
  `test_each_installed_preset_loads_through_a_patch_and_comes_back_byte_for_byte` and
  `carrying-count.txt`: 77 texts, 59,477 floats, 35 of them in the entry.
- **A float outside its parameter's bounds is shown truly, refused on set, and carried.** `get`
  returns 141.44 for `flanger_dry_wet` at 0.7072; it is absent from `values`; a set of a value in
  range brings it in. Verified against
  `test_a_preset_holding_a_float_outside_its_bounds_is_shown_refused_on_set_and_carried`.
- **`opaque` has fixed keys, and any other is refused by name:** `preset`, `settings.<name>`,
  `line_mapping.<slot>`, `tuning`. Verified against `test_what_opaque_holds_is_under_its_fixed_keys`
  and `test_an_opaque_key_that_is_no_entry_of_a_vital_patch_is_refused_by_name`.
- **A patch of values alone is the start preset with those values.** Entries without a `preset`
  entry are refused. Verified against
  `test_a_patch_of_values_alone_loads_as_the_start_preset_with_those_values`, in both test modules,
  `test_an_entry_without_the_preset_entry_it_belongs_to_is_refused` and the instrument spec's MP5.
- **A patch is taken whole or refused, and the refusal names the first entry to refuse,** in a fixed
  order: the instrument's name, the `opaque` keys sorted, the `values` sorted by id, the preset they
  make. A refused patch leaves the model, the plugin and the bus as they were. Verified against
  `test_the_first_value_to_refuse_is_the_first_by_id`,
  `test_a_patch_refused_part_way_leaves_the_model_the_plugin_and_the_bus_as_they_were`, which unlike
  core's contract test carries its sections, and the instrument spec's MP6.

## What the instrument does about Vital's loads

What Vital does with a load, measured, is `vital/plugin-state.md`'s. These are the instrument's
rules on it.

- **A preset seen to block, to be ignored, to keep old sections or to kill the process is refused
  before the plugin is called.** The guard, `patch.check_loadable`, needs no plugin and judges a
  preset and the map alone. It refuses a `synth_version` that is no version or is newer than the
  plugin's, versions compared by their numbers less trailing zeros, and every preset where the
  plugin's own version is no version; `wavetables` and `lfos` that are not arrays of three and of
  eight objects; a `sample` without its four keys; `custom_warps` and `random_values` that are
  not arrays of three objects, where the preset holds them; and a float with no finite display.
  The last two sections one entry longer killed the process, and shorter or empty were not held
  as given; none of the 75 installed presets holds either. A shape is guarded only once a
  transcript shows what Vital does with it. Verified against
  `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called`,
  twenty-five shapes, `test_the_guard_passes_what_vital_was_seen_to_load`,
  `test_the_sections_are_judged_in_the_order_the_guard_gives`,
  `test_every_installed_preset_passes_the_guard_and_holds_neither_optional_section`,
  `test_a_version_is_compared_by_its_numbers_less_trailing_zeros`,
  `test_a_plugin_version_that_is_not_digits_and_dots_refuses_every_preset_by_name`, the spec of
  issue #20's `arrays-seen.txt` and its MG1 to MG3, the instrument spec's MG1 to MG4 and the
  first revision's MV1 and MV2.
- **The guard judges a section's shape, never its inside; what gets past it Vital answers with its
  alert, and the host answers that on macOS.** `load_patch` then raises the patch error with
  Vital's own words. Of 335 texts, 249 raise the alert: the guard refuses 28 of them and the
  watch the other 221, and none failed to return. On any other platform such a patch still
  blocks the calling process, and the instrument's docstring and the README say so. A patch
  Vital dies on kills the calling process, but for the shapes the guard refuses. A patch Vital loads
  in part is not detected: of the 83 texts that raise no alert the guard refuses 19, and 64 still
  load. By how they reach the plugin, 54 load as a patch through the instrument and 10 are texts
  only the host can be given. By what the plugin then holds, 13 are held as given, 10 holding the
  changed section as the text gives it and 3 changing no section, and 51 of the 64 are not held as
  given: 15 hold it as the unchanged one, 1 keeps it from the preset before and 35 hold something
  the read cannot name (`vital/plugin-state.md`, `silent-and-loaded.txt`). The crash and the part
  load are issue #25's. Verified against
  `test_the_guard_does_not_read_inside_a_section`, `remedy-run.txt`, `silent-and-loaded.txt` and
  `test_a_patch_vital_answers_with_its_alert_is_refused_and_the_plugin_put_back`.
- **A load Vital answers with its alert, or ignores, meets the rollback that was there.** The
  host's `PluginStateError` is refused as a patch, chained, and the model's text loaded again:
  after an alert the plugin had taken the patch in part, so it is put back, not left. With each
  of the start preset, the fixture and the 75 installed presets as the model, the plugin then
  held all 903 floats and every section as the model's own double load had left them, 77 of 77.
  Verified against
  `test_a_load_vital_answers_with_its_alert_or_ignores_is_refused_and_the_model_s_text_put_back`
  and `rollback-count.txt`.
- **A load from a thread that is not the process's main one changes nothing and is refused as a
  patch.** On macOS `load_patch` raises `PatchRefusedError`, core's `PatchRejectedError`, chained
  from the host's `PluginThreadError`, as core's contract names that error for a patch the
  instrument cannot load, changing nothing. Its reason says, in this order, that the call came from
  a thread the plugin cannot be loaded from, naming it; that the patch passed the package's own
  checks, which come first, so a patch they refuse is refused for their reason from any thread and
  the thread is never asked; and that it was not given to Vital, so whether Vital takes it is
  unknown. It is not a state error, so no rollback answers it: the model, the plugin and the bus are
  as they were, and the instrument has not lost step. `VitalHost.load_state` and
  `VitalInstrument.__init__` still raise `PluginThreadError` itself. This reverses, for `load_patch`
  alone, the spec of issue #20's Decision 14 (the revision after the review of PR 26's finding 3);
  whether core names an error for a call from a thread the instrument cannot serve is a question for
  core. Verified against
  `test_a_load_from_a_second_thread_changes_nothing_and_is_refused_as_a_patch`,
  `test_a_patch_the_guard_refuses_is_refused_for_the_guard_s_reason_from_any_thread`, MR5 and MR6 in
  the revision after the review of PR 26's `mutation.txt`.
- **The host's marker never reaches the model.** It is set on the plugin and read there; `get`,
  `patch`, the preset and the bus never show it, on a load that succeeds or on one that fails.
  Verified against
  `test_the_marker_is_the_plugin_s_alone_on_a_load_that_succeeds_and_on_one_that_fails`.
- **Every load is made twice.** A measured workaround with no known cause, on Vital 1.6.4 through
  pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Verified against
  `test_one_load_after_a_set_leaves_the_off_grid_floats_off_and_a_second_holds_them`, which a Vital
  needing one load or three fails by name, and the instrument spec's ML2 and MV1.
- **For a preset older than the plugin, the model keeps the file's floats.** Vital upgrades it, so
  `get` can report the file's value where Vital plays another, which for a choice is another setting
  by name: 46 floats on 11 of the 75 installed presets, measured on Vital 1.6.4 through pedalboard
  0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Stated as that, never as rounding. What the model
  should hold is issue #22's to decide. Verified against
  `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none` and
  `tests/data/upgraded-floats.txt`.
- **When the plugin refuses a text after the checks pass, the model's own text is sent again.** The
  call is refused as a patch, chained from the host's error, and the plugin holds the model's
  floats. That is once the plugin has been given any of the text; a refusal before that is the next
  rule's. Verified against
  `test_a_load_the_plugin_refuses_puts_the_model_s_text_back_and_is_refused_as_a_patch`,
  `test_a_marker_read_the_plugin_refuses_after_the_first_load_s_change_is_rolled_back`, the
  instrument spec's ML1, and MQ8 in the revision after the second review of PR 26's `mutation.txt`.
- **When the plugin does not take the model's own text either, the instrument has lost step, and
  says so.** Refused, answered with the alert or ignored, alike. Its state is unknown, so core's
  "changing nothing" cannot be claimed: `PluginStateError`, not core's `PatchRejectedError`, names
  both refusals and says to build a new instrument. Every later `set`, `load_patch` and `render` is
  refused with it before any other check, the plugin not called and nothing published; `get` and
  `patch` answer from the model, which the plugin may no longer match. **So too when a load is cut
  off by an error from outside the package,** a `KeyboardInterrupt` or a `MemoryError` among them,
  once the text is being sent, or while the model's own text is sent again: the plugin may hold part
  of a text the model does not, so the instrument loses step, no rollback is tried, and that error
  leaves as itself, the same object. **An error raised before the plugin is given anything changes
  nothing and loses no step:** the checks', the host's thread rule's, and any error that leaves the
  host's count of state writes begun, `VitalHost.writes_begun`, as `load_patch` read it before the
  first of its two loads. The host's own refusal is then `PatchRefusedError`, chained from it and
  saying the plugin was not given the preset, with no rollback, which would meet the same refusal
  and lose a step no load had taken; an error from outside the package leaves as itself, nothing
  marked. Once the count has moved every error is met as above, one that strikes in the second load
  before its own change among them, since the plugin then holds the first load's text; and an error
  in the rollback's own loads loses the step whether or not the count moved again, the plugin
  holding what the failed load left. The count is raised before the first change and never after it
  (`vital/plugin-state.md`), so an interrupt between the two is treated as sent. Verified against
  `test_a_plugin_that_refuses_the_model_s_own_text_too_leaves_the_instrument_out_of_step`,
  `test_a_rollback_vital_answers_the_same_way_leaves_the_instrument_out_of_step`,
  `test_once_out_of_step_every_call_that_reaches_the_plugin_is_refused_before_anything_else`,
  `test_once_out_of_step_get_and_patch_answer_from_the_model`,
  `test_an_error_from_outside_the_package_mid_load_leaves_as_itself_and_the_step_is_lost` (in the
  first write, when the second load first reaches the plugin and in the second write),
  `test_a_marker_read_the_plugin_refuses_before_any_change_is_a_refused_patch_and_no_rollback`,
  `test_an_error_from_outside_the_package_before_any_change_leaves_as_itself_and_marks_nothing`,
  `test_an_error_in_the_rollback_before_its_own_change_still_loses_the_step`, the first
  revision's MS1 to MS4, and MR3, MQ7 and MQ9 in the revision after the second review of PR 26's
  `mutation.txt`.

## Events and errors

- **Checks, then the plugin, then the model, then one event.** A refused call publishes nothing and
  changes nothing; a carried-out one publishes once, after the change. Building the instrument
  publishes nothing. `PatchLoaded.parameter_count` is the number of values in the patch given.
  Verified against core's contract tests,
  `test_a_subscriber_that_raises_leaves_the_set_made_and_published`,
  `test_parameter_count_is_the_number_of_values_in_the_patch_given` and the instrument spec's ME1
  and ML3.
- **Nothing but the package's errors leaves the instrument, each core's own too.** What
  `Parameter.check` raises is raised again as the package's, with core's fields and core's error its
  cause. Verified against `test_every_refusal_is_the_package_s_error_and_core_s`,
  `test_a_set_it_refuses_is_the_package_s_error_with_core_s_fields_and_core_s_error_its_cause` and
  the instrument spec's MP7.

## A render

- **A render has declared limits, named constants with their source,** and one past them is refused
  naming the limit and its value: `MAX_SAMPLES`, 2 ** 24, a length Vital gives, and a rate from
  1,000 to 768,000 Hz, the range measured. Verified against
  `test_a_render_past_a_limit_is_refused_naming_the_limit_and_its_value`,
  `test_the_longest_render_is_given_and_one_sample_more_is_refused` and the instrument spec's MN2
  and MN3.
- **A render of no samples is an empty result, the plugin not called,** as core's reference gives
  it. Verified against `test_a_render_of_no_samples_is_an_empty_result_and_the_plugin_is_not_called`
  and the instrument spec's MN1.
- **A render that reaches full scale carries one warning saying the peak and where; the audio is
  never clipped here.** At full scale counts. Vital gives samples up to 2.1. Verified against
  `test_a_render_that_reaches_full_scale_carries_one_warning_saying_the_peak_and_where`,
  `test_a_render_whose_largest_sample_is_exactly_full_scale_carries_the_warning`,
  `test_a_render_that_clips_carries_one_warning_and_the_event_carries_it` and the instrument spec's
  MN4.
- **A render of most presets opens with the preset sounding though no note was played.** The warning
  counts that sound. On the start preset it is a transient of about 0.02; on installed presets it
  reaches full scale, measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). Held as it is until issue #21, a render that does not open so, changes it. Verified
  against `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding`, which
  names the issue,
  `test_a_render_of_no_notes_on_the_start_preset_is_its_small_transient_and_no_warning` and
  `probes.txt` sections 4 and 4b.
- **A note's bytes are core's `Note` as it is, and its time is half a sample past its sample.** The
  time of the sample itself lands one sample early on some samples. A note that starts at the
  render's length is left out, and a note-off there too. Verified against `tests/unit/test_midi.py`,
  its bytes written out, `test_a_note_lands_on_the_sample_core_s_rule_gives_it`, at a sample where
  the two differ, `probes.txt` section 1 and the instrument spec's MM1 to MM4.
- **Each note sounds for its own length, as core's reference instrument sums a sine per note.** On
  one channel Vital's first note-off releases every voice of its pitch, so a note whose pitch is
  already sounding on its channel goes out, on and off, on the lowest channel where it is not; of
  two struck on one sample the first in the pattern keeps its channel. A pitch sounds from its
  note-on to its note-off, so one released on a sample is free to a note struck there, and a note
  too short to last a sample is not. A seventeenth note of one pitch sounding at once is
  `RenderRefusedError`, naming the pitch and the sample. Where core's protocol leaves a meaning open
  and its reference instrument shows one, the reference decides, and a probe of Vital shows how to
  reach it. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2),
  with Vital's MPE setting off and on. Verified against `tests/unit/test_midi.py`, its bytes written
  out, `test_two_notes_of_one_pitch_that_overlap_each_sound_for_their_own_length`, under the probes'
  window with a named tolerance, `overlap-probe.txt`, `overlap-probe-2.txt` and the first revision's
  MM5 to MM10.

## The contract suite

- **A contract run is named for what it runs against.** `test_contract_against_vital` runs core's
  thirteen against the installed Vital; `test_contract_against_a_fake_plugin` runs them over a real
  `VitalHost` on a fake plugin, which CI can. A pass over the fake plugin is not a pass against
  Vital, and the local run is the only one against Vital. Verified against both tests and
  `contract-run.txt`.
- **Each integration module loads Vital once; each test gets a new bus and a new instrument.**
  Building the instrument loads the start preset, so no test's state reaches the next, in the model
  or the plugin. No `conftest.py` holds the fixtures: the gate's negative test q writes one.
  Verified against `tests/integration/test_vital_instrument.py` (`vital`, `bus`, `instrument`) and
  `test_the_next_instrument_starts_clean`, which compares the plugin's 903 floats.
