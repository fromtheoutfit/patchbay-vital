# The hosted plugin

What Vital does when hosted, and how this package holds it to that. A rule here is about Vital
through pedalboard; the general form of a measured third party is `base/testing/tests.md`'s. Written
from `src/patchbay_vital/state.py` and `host.py`; the evidence is the `verification/` of the spec of
issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`): `probes.txt`,
`host-probes.txt`, `float-environment.txt` and `probes-first-attempt.txt`; of its revision after PR
9's CI run (`agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`): `linux-gate-run.txt` and
`old-behaviour.txt`; of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), whose `shape.md` records the reading
of pedalboard 0.9.26's wrappers and its `old-behaviour.txt` the findings' tests failing on the code
as reviewed; of the revision after the second review
(`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), whose `old-behaviour.txt`
does the same for its findings; of the revision after the third review
(`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`): `restore-probe.txt` and
`old-behaviour.txt`; and of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`), the revisions after PR 14's
reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
`agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`) and the spec of issue #15
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`): `plugin-probe.txt`; and of
the spec of issue #8 (`agent-os/specs/2026-11-15-1448-the-instrument/`): `probes.txt` and
`probes-2.txt`; and of the spec of issue #20
(`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`): `probes-1-costs.txt`,
`probes-2-alert.txt`, `probes-3-counts.txt`, `probes-3-crash-reports.txt`, `probes-4-counts.txt`,
`arrays-seen.txt`, `marker-count.txt`, `rollback-count.txt`, `remedy-run.txt`,
`silent-and-loaded.txt` and `mutation.txt`; and of the revision after the review of PR 26
(`agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`): `midpoint-probe.txt`, `costs.txt`,
`marker-count.txt`, `rollback-count.txt`, `remedy-run.txt` and `mutation.txt`, the last four made on
its final tree; and of the revision after its second review
(`agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/`), which measured nothing new
on Vital: `marker-count.txt`, `rollback-count.txt`, `remedy-run.txt` and `mutation.txt`, made again
on its final tree.

## The state

- **The plugin's state is a preset's text in three containers, read and written by our own codec**:
  a `.vstpreset` (`VST3`, class id, `Comp` and empty `Cont`), JUCE's `VstW` header, and a VST2
  `CcnK`/`FBCh` bank of one chunk holding the JSON, exactly as a `.vital` file writes it, then 17 NUL
  bytes and `JUCEPrivateData`. Every field is kept as read, so `wrap(unwrap(x)) == x`; anything else
  is `PluginStateError` naming the layer, a negative chunk size and a text that nests too deeply to
  read among them, the decoder's `RecursionError` turned into `ValueError` by `preset.decode_end`,
  the one place in the package that does it, so no built-in leaves the codec. Written from the
  bytes, not from any program's source. Verified against `state.py`, `tests/unit/test_state.py`
  (`test_wrap_reverses_unwrap`, `test_the_layers_are_where_the_plugin_put_them`,
  `test_each_layer_is_refused_by_name`, `test_a_text_that_is_not_one_object_is_refused`) and
  `test_the_codec_reads_and_writes_the_plugin_s_own_bytes`.
- **The state's text has one key a file lacks, `tuning`, held like any unread section**, as
  `VitalPreset.tuning`. Verified against `preset.py`, `format.py` and
  `tests/unit/test_format.py` (`test_a_plugin_state_comes_back_byte_for_byte`).
- **The containers around the text are read once, when the plugin loads, and every load reuses
  them.** A load changes the text and no container, so `load_state` reads nothing from the plugin
  first; a plugin whose state the codec cannot read is refused where it loads, `PluginLoadError`
  naming the path, chained. Verified against `host.py` (`__init__`, `load_state`),
  `tests/unit/test_host.py` (`test_a_load_reuses_the_containers_read_when_the_plugin_loaded`,
  `test_a_plugin_whose_state_the_codec_cannot_read_is_refused_at_load`) and
  `tests/integration/test_vital_plugin.py`
  (`test_the_fixture_as_state_reads_back_but_its_sample_delayed` and
  `test_every_installed_preset_loads_as_state`, each holding the containers after a load to the
  ones before it).
- **A preset loaded as state can be complete, routing and media included, but the plugin changes it.**
  It upgrades a preset older than 1.6.4 (keys added, sections re-encoded, floats moved); every load
  delays the embedded sample by 4 samples and re-quantizes it, a 16-bit value moving one step; a
  value off the host's grid snaps once after the host set that parameter. A load of the starting
  state and then, with no set between them, of a state holding `volume` at or below its floor at a
  float32 the scale does not hold, the curve's own for the display, moves that value to the
  normalized path's, while `chorus_feedback`'s off-grid 0.4000000059604645 in the same load is held
  as given: on Vital 1.6.4 through pedalboard 0.9.26 on arm64, at each of the four values of
  `tests/data/pinned-values.txt`'s `volume_floor` set (issue #15's probe transcript prints them as
  `_VOLUME_FLOOR`, the integration module's constant until the revision after PR 14's sixth review
  moved the values to the file), after each of the four histories the probe tried before the first
  load (a fresh instance, the census's sets, a set of each of the two, the measure's own sets). The
  state is written with the package's `dumps`, which gives the starting state's own text back byte
  for byte, so it differs from text Vital wrote only in `volume`'s value, and read with the host's
  `_floats`. It is an observation: nothing measured says why one value moves and the other does
  not, and the test that holds it does not rely on which history precedes it. So the plugin's state
  is never read back as the preset it was given; the instrument keeps the preset it loaded
  (`vital/instrument.md`). Verified against `test_the_fixture_as_state_reads_back_but_its_sample_delayed`,
  `test_every_installed_preset_loads_as_state`, `test_a_routing_only_in_the_preset_text_is_heard`
  and `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`,
  which holds the load's move, and the `verification/plugin-probe.txt` of the revisions after PR
  14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
  `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`) and of the spec of issue
  #15 (`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`), section 2; first seen
  in issue #13's (`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`).
- **Vital reports no load it cannot use.** Of 335 texts, 20 written by hand and 315 that change
  one value inside one section of the start preset, each loaded twice in a process of its own, on
  Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2):
  - **249 raise its modal alert.** Unanswered, the caller waits for ever, in AppKit's `NSAlert
    runModal` under Vital's `SynthProcessor::setStateInformation`, and nothing in Python runs
    meanwhile: pedalboard holds the GIL through the write, and a thread's ticks and a signal
    handler's alarms stopped, 10 and 4 in the second before the load and 0 and 0 after it began.
    The alert is the text's and not the instance's: a text's first load has the same verdict in a
    fresh instance and after each of three histories on 335 of 335. By then Vital has taken the
    text in part: its floats on 246 of the 249, a section on 245.
  - **3 kill the process** inside Vital's own reading of the text, each a section one entry
    longer than Vital holds: `custom_warps` and `wavetables` in the first load, `random_values` in
    the second, the first having returned clean. Each killed all 14 of its children. Once in 11
    fresh children `random_values` let both loads return, and the child died at exit. So one load
    of a text is no trial of it, which is further evidence for loading twice (below).
  - **A `synth_version` newer than the plugin's is ignored whole,** with no error and the plugin
    unchanged.
  - **The other 82 load, not all as given.** By the state read after each, loaded over an older
    installed preset: 10 hold the changed section as the text gives it, and 3 change no section;
    16 hold it as the unchanged one, the change read past; 9 keep it from the preset before; 41
    hold something the read cannot name; and on 3 the read cannot tell a kept section from an
    unchanged one. `wavetables` or `lfos` as an empty array keeps what the plugin had.
  - A key the text lacks goes to its default, 132 of 132.

  Each text changed one value: none had two faults, or a fault past an array's first entry, and
  6 of the 18 arrays in the presets on hand were never made longer or shorter. A load that may
  not return, or may kill, is run only in a process of its own with a time limit, as a
  transcript. Verified against the spec of issue #20's `probes-4-counts.txt`,
  `probes-2-alert.txt`, `probes-3-crash-reports.txt`, `arrays-seen.txt` and
  `silent-and-loaded.txt`, and issue #8's `probes.txt` sections 5 and 5b.
- **A state is written under a watch that answers the alert, on macOS.** For the length of each
  write, a load's and the one a measurement ends on alike, `host.py` replaces `-[NSAlert runModal]`
  with a callback that marks that an alert was answered, notes it, then its two texts, and returns
  its first button, and puts the method back in a `finally`, as the floating-point environment is.
  The method's own implementation is read once, with `method_getImplementation`, when the watch is
  made, kept for its lifetime and never taken from a swap's return. The watch sets its own state and
  installs the callback inside one `try`, whose `finally` puts the kept implementation back and
  then clears the state, whatever happened before it: an interrupt in the install, or on the line
  after it, leaves the method its own and the watch out of place, and putting the kept one back
  twice changes nothing. The callback's mark comes first and stores an object that already exists in
  an attribute that already does, so it cannot fail for want of memory. Everything after it is
  guarded, what noting the alert raises dropped, the mark standing for it, and what reading the
  texts raises kept: nothing leaves the callback, since ctypes prints and drops an error raised
  there and returns 0, not the first button (seen in memory, with no Vital; what Vital does with 0
  was not measured). A write in which the mark was made is `PluginStateError` with the words of
  every alert answered, in the order they were answered, and how many where there is more than one,
  "Error opening preset" on every one whose words were read; one whose words could not be read says
  so in its place, the error chained from what the first such read raised; one that could not be
  noted at all says that; and a write in which pedalboard raised too is one `PluginStateError`
  carrying both, chained from pedalboard's error. No text was seen to make Vital raise two alerts in
  one write: that rule is held by a stand-in alone. The watch is one object for the whole process
  and refuses to be entered while it is in place, before its `try`, so the entry in place keeps its
  state and its method; with every write the main thread's and nothing but Vital and the callback
  running inside one, no lock is needed. The Objective-C runtime is reached through `ctypes`, the
  standard library alone, and where it or `pthread_main_np` cannot be on macOS the host refuses to
  load. The watch is built from what `_appkit_watch` reads and makes from the runtime and the C
  library, so its own rules are held by unit tests on every platform with those stood in. Under the
  watch no load failed to return and no window showed: 383 children in the probes, and 335 and 77 on
  the shipped code. It costs a median of 31.5 microseconds a load. Its limits:
  - the method is replaced for the whole process while a write runs, so any alert run on the main
    thread in that time is answered and counted as the write's. Nothing tells Vital's own alert
    from another, and none other was seen;
  - each answered alert leaves one window object in the application's own list, never shown and
    never listed by the window server: 500 after 500 of them, resident memory going from 603 to 701
    MiB over those 1,500 loads, the alerts' share of it not separated from the loads' (issue #27,
    unverified, the revision after the review of PR 26's finding 11);
  - on any other platform nothing is watched, so a text Vital cannot read may block there.
    Nothing was probed off macOS, nor in a process with no screen.

  Verified against `host.py` (`Alert`, `_AppKitWatch`, `_alert_texts`, `_appkit_watch`, `_NoWatch`,
  `_alert_watch`, `VitalHost._write`, `_alert_said`, `_alerts_said`), `tests/unit/test_host.py`
  (`test_the_watch_is_in_place_for_a_state_write_and_at_no_other_time`,
  `test_a_state_the_plugin_answers_with_its_alert_is_the_package_s_error_with_its_words`,
  `test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back`, which runs AppKit's own
  alert in a child it kills at 10 s, `test_without_the_runtime_the_host_refuses_to_load`,
  `test_off_macos_no_alert_is_watched`,
  `test_the_watch_refuses_to_be_entered_while_it_is_in_place_and_puts_the_method_back`,
  `test_the_callback_notes_an_alert_whose_words_cannot_be_read_and_returns_the_first_button`,
  `test_an_alert_whose_words_could_not_be_read_is_the_package_s_error_chained_from_the_read`,
  `test_an_alert_and_a_pedalboard_refusal_are_one_error_carrying_both`,
  `test_an_interrupt_in_the_watch_s_install_leaves_the_method_its_own`,
  `test_putting_the_method_s_own_implementation_back_twice_changes_nothing`,
  `test_a_refused_nested_entry_leaves_the_first_entry_s_state_and_method_as_they_were`,
  `test_the_callback_marks_an_alert_it_cannot_note_and_returns_the_first_button`,
  `test_an_alert_that_could_not_be_noted_is_still_the_package_s_error`,
  `test_every_alert_of_one_write_is_in_the_error_in_the_order_answered`),
  `test_a_patch_vital_answers_with_its_alert_is_refused_and_the_plugin_put_back`,
  `probes-2-alert.txt`, `probes-4-counts.txt`, and the revision after the second review of PR 26's
  `remedy-run.txt`, made on its final tree, and MW1 to MW4, MR9, MR12 to MR14, MQ1 to MQ3 and MQ12
  to MQ15 in its `mutation.txt`.
- **A state is written on the process's main thread, on macOS.** `load_state` and `measure` ask
  first, before the plugin is touched, and `_write`, the one place the plugin's state is set, asks
  again, so a later caller that forgets cannot write elsewhere: from any other thread each raises
  `PluginThreadError`, and a measurement refused there has set nothing. The thread is told by
  `pthread_main_np`, reached through `ctypes` with its return type declared, which names the
  process's main thread, the one AppKit needs; `threading.main_thread()` names the thread that
  started Python, another one where an interpreter is embedded and started off the main thread. That
  case is reasoned from what `pthread_main_np` means and was not measured. From another thread
  AppKit refuses the alert's window, `NSInternalInconsistencyException: NSWindow should only be
  instantiated on the main thread!` under `-[NSAlert init]`; the load raises through pedalboard; the
  plugin's parameters are then read stale, as they are after a good text loaded so; and the process
  died at its next render, 11 of 11, in AppKit's assertion on the main event queue. It is not a
  `PluginStateError`: nothing was touched, so nothing is to be put back. `set` and `render` check no
  thread, and neither was measured from a second thread. Off macOS the host writes from any thread,
  as it always did, and none was probed there: should the parameters be read stale there as they
  were on macOS, the marker would refuse a good load made so. Verified against `host.py`
  (`_AppKitWatch.may_write_here`, `_appkit_watch`, `VitalHost._on_a_writing_thread`, `_write`,
  `load_state`, `measure`), `errors.py` (`PluginThreadError`),
  `test_a_load_from_a_second_thread_is_refused_before_the_plugin_is_called`,
  `test_a_measurement_from_a_second_thread_is_refused_before_any_parameter_is_set`,
  `test_a_state_write_from_a_second_thread_is_refused_by_the_write_itself`,
  `test_the_watch_lets_a_state_be_written_only_where_pthread_main_np_says_main`,
  `test_on_macos_pthread_main_np_answers_the_main_thread_and_no_other`,
  `test_on_macos_a_library_that_is_not_found_leaves_no_watch`,
  `test_where_no_alert_is_answered_a_load_is_made_from_any_thread`,
  `test_a_load_from_another_thread_is_no_state_error` (in `tests/unit/test_errors.py`),
  `test_a_load_from_a_second_thread_changes_nothing_and_is_refused_as_a_patch`,
  `probes-3-counts.txt`, `probes-3-crash-reports.txt`, and MT1, MT2, ME1, MR7, MR8, MR10 and MR11 in
  the revision after the review of PR 26's `mutation.txt`.
- **A load is checked with a marker, which is the plugin's alone.** Before each write `host.py`
  sets `MARKER`, the switch `filter_1_on`, to the end of its range the text does not hold: the
  maximum, unless the text's value is at the scale's midpoint or above, and then the minimum. A
  text without the key holds the default. One that holds under the key what is no JSON number,
  `true` and `false` among them, is `PluginStateError` naming the key and the value's kind, before
  the marker is read or set: which end such a text holds is not known. Vital's reading of a
  non-number there was not measured, because such a text is never sent: the file's reader refuses a
  setting that is no float, so only a text given to a bare host can hold one, and the state's
  validator, which asks only for one JSON object, passes it. After the write the marker is read:
  left as planted, the load was ignored, `PluginStateError`. The value the marker had is read before
  the `try` and the plant is inside it: however the plant or the write ends, an error from outside
  the package, a `KeyboardInterrupt` or a `MemoryError`, among the ways, an interrupt in the plant
  or on the line after it too, the marker left as planted is set back to the value it had, and the
  error that ended it leaves as itself; one raised while setting it back is a note on it, never in
  its place. `VitalHost.writes_begun`, read-only, counts the loads and measurements that have begun
  to change the plugin. It is raised just before the first change each makes, the plant, the write
  of an unchecked load or a measurement's first set, and never after it, so an interrupt between the
  two leaves it raised with nothing changed, the safe side. A load refused before any change, by the
  thread rule, the validator, the marker's own check or a read of the marker the plugin refuses,
  leaves it as it was, which is how the instrument knows the plugin was given nothing
  (`vital/instrument.md`). The marker is sought once, and settled only by a lookup that
  found it or by `MapMismatchError`: any other error leaves that load, and the next load seeks it
  again. For the marker, a switch, Vital's parameter read held every value given as given, the
  float32s either side of 0.5 and of each end among them, and only the state's own text rounds one
  between the ends, below 0.5 to 0 and from 0.5 to 1: so the end planted is never what the read
  holds after a load Vital took (57 values in the revision after the review of PR 26's
  `midpoint-probe.txt`, each boundary located between two adjacent float32s). The text's settings
  are read through `_settings`, the package's one guarded decoder, though the state's validator
  refuses a text nesting too deeply first: 9994 levels through it against 9997 directly on Python
  3.12.16 (the revision after the review of PR 26's `costs.txt`), a margin measured and not
  promised. On the start preset, the fixture and the 75 installed presets the marker read the text's
  value after 154 of 154 loads, under each of two histories, and the two-load result is the same
  with the check as without it, all 903 floats and every section, 77 of 77. It needs the map, so
  where the map is not the plugin's a load is made unchecked; it needs no AppKit, and was
  measured on macOS alone. It does not see an alert that was answered: the floats are the
  text's by then, and the watch is what tells. Its cost is the probe's figure and no other:
  planting two markers and reading them back took a median of 156 microseconds, the text's
  decode apart (`probes-1-costs.txt`); `marker-count.txt` does not measure it. Verified against
  `host.py` (`MARKER`, `_planted`, `_KINDS`,
  `VitalHost._marker`, `_set_back`, `_unplanted`, `writes_begun`, `load_state`, `measure`),
  `test_the_marker_is_planted_at_the_end_of_its_range_the_text_does_not_hold`, its expected
  values from the scale's two ends,
  `test_a_load_the_plugin_ignores_is_refused_by_the_marker_it_left`,
  `test_a_marker_a_failed_write_left_is_set_back_to_the_value_it_had`,
  `test_where_the_map_is_not_the_plugin_s_a_load_is_made_unchecked`,
  `test_a_state_vital_ignores_is_refused_by_the_marker_and_the_plugin_left_as_it_was`,
  `test_an_error_from_outside_the_package_in_a_write_leaves_as_itself_and_the_marker_is_set_back`,
  `test_a_marker_that_cannot_be_set_back_is_noted_on_the_write_s_own_error`,
  `test_a_marker_lookup_that_fails_is_sought_again_at_the_next_load`,
  `test_the_marker_is_never_planted_where_vital_holds_a_switch_s_value`,
  `test_the_settings_helper_refuses_a_text_one_level_past_the_decoder_s_limit`,
  `test_a_text_past_the_decoder_s_limit_is_refused_by_the_validator_before_the_marker`,
  `test_an_interrupt_in_the_marker_s_plant_leaves_as_itself_and_the_marker_is_as_it_was`,
  `test_the_count_of_writes_begun_is_raised_by_a_change_and_by_nothing_refused_before_one`,
  `test_a_marker_value_that_is_no_number_is_refused_before_anything_is_set`, the revision after the
  second review of PR 26's `marker-count.txt`, made on its final tree, and MM1 to MM6, MR1, MR2,
  MR4, MR15, MR23, MQ4 to MQ6 and MQ10 in its `mutation.txt`.
- **What a load can still do, measured and not remedied.** A text Vital dies on kills the calling
  process: the guard refuses the three shapes found (`vital/instrument.md`) and no others. A text
  Vital loads in part is not detected. Of the 83 texts that raised no alert, the shipped guard
  refuses 19, the one ignored whole among them, and 64 still load: 54 as a patch through the
  instrument, and 10 the package's writer cannot write, which only the host can be given. By the
  state read after each of the 64: 10 hold the changed section as the text gives it, and 3
  change no section; 15 hold it as the unchanged one; 1 keeps it from the preset before; and 35
  hold something the read cannot name, 25 of them a wavetable, 6 a custom warp, 2 an lfo and 2 the
  sample. So 51 of the 64 are not held as given. Only `custom_warps`, `lfos`, `modulations` and
  `random_values` come back from the plugin as a good text gives them, 77 of 77, where `sample`
  differs on 77 and `wavetables` on 75. So a check of those four after a load, counted over the 82
  that loaded with no guard, flags 32 of them, for a state read and a parse of 0.9 to 54 ms, and
  cannot see a wavetable or a sample that was made into something. That check is not built. Nor is a
  trial load in a child process, the one candidate that reaches a crash: 2,379 ms a load in a fresh
  child, or a second Vital kept up at 497 to 967 MiB and one more double load, and it passed
  `random_values` once in 11. Nor a timer that ends the alert's modal loop, which returned the 11
  texts it ran on and showed a 4 by 4 window. The crash and the part load are issue #25's to remedy.
  Verified against `probes-1-costs.txt`, `probes-2-alert.txt`, `probes-4-counts.txt`,
  `remedy-run.txt` and `silent-and-loaded.txt`.
- **One load of a text is not enough, and two are: a measured fact, no cause known.** After a set of
  every parameter and a render, on the start preset, the fixture and the 75 installed presets: one
  load leaves 17 to 53 of the 903 floats off the text's on every text, 2,335 in all; two loads leave
  none on 66; a third holds the same 903 as the second on all 77. On a fresh instance with no set
  before it, one load of an older preset leaves floats off too, 7 to 18 on four of six tried. The
  sample's 4-sample delay is counted from the text each time, so two loads of one text hold the
  sample one load does. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). Verified against `probes.txt` sections 6, 9 and 9b and
  `test_one_load_after_a_set_leaves_the_off_grid_floats_off_and_a_second_holds_them`.
- **Vital upgrades a preset older than it as it loads, and no number of loads undoes it.** On 11 of
  the 75 installed presets, versions 0.6.1 to 1.0.0, 46 floats differ from the text's after two
  loads and after three: 29 are keys the text lacks set to other than the default (`chorus_cutoff`
  20 where the default is 60), 3 are `flanger_center` moved into its range, and 14 are floats inside
  their scale renumbered or rescaled (`osc_1_stack_style` 9 held as 10, `filter_1_style` 1 as 0).
  The map is 1.6.4's, so such a float means another setting in the file than in the plugin. Measured
  on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). What the model
  holds for such a preset is issue #22's to decide. Verified against `probes-2.txt` section 9c,
  `tests/data/upgraded-floats.txt` and
  `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none`.

## The process

- **Every call into the plugin keeps the process's floating-point environment.** Loading and
  rendering Vital turn on flush-to-zero for the whole process and leave it on, so every subnormal
  after them, in Python and numpy, is zero. `host.py` saves the environment with `fegetenv` before
  each call and restores it with `fesetenv` after, both from the first library that holds them: the
  C library on macOS, the maths library on glibc, whose C library has neither, each name looked up
  only once the one before it is passed over. It refuses to load where no library holds them. Every
  call into the plugin is its own guard, reads included and each read of a loop its own, so the
  Python work between two calls, the JSON a measurement parses among it, runs in the process's
  own environment and never in the one the plugin left: one guard around a loop would hand the
  second call the first's. The load's four calls are four guards too, with nothing in Python
  between them: pedalboard's `parameters` is Python that steps raw values and parses texts between
  its own native calls, and one guard from `VST3Plugin` on would enter it in the flush-to-zero the
  load left. A fake plugin that turns upward rounding on at every call holds both:
  after each public method the rounding mode is back, and no call finds the mode the one before
  it set. One piece of the package's Python does run under the plugin's environment: the callback
  that answers Vital's alert, which Vital calls from inside a state write. It does no float
  arithmetic, a comment at it saying so for a later edit, and it is not switched to the process's
  own environment, since nothing may fail before the alert is noted. No test holds that it stays
  so. Verified against `host.py` (`_c_library`, `_environment_kept`, `_reached`, `_name_of`,
  `_text_for`, `VitalHost.__init__`, `_AppKitWatch._answered_at_once`), pedalboard 0.9.26's
  `AudioProcessorParameter.__init__` (read
  for the fact), `tests/unit/test_host.py` (`test_every_public_method_gives_the_environment_back`,
  `test_every_call_into_the_plugin_is_entered_in_the_process_s_own_environment`) and
  `test_the_process_keeps_its_floating_point_environment`.
- **The guard is held by unit tests that need no plugin**, so CI, which has no Vital, runs it: the
  lookup on the platform the tests run on, a library without the two functions passed over, and one
  real save and restore that upward rounding set inside it does not survive. A guard proven only
  beside the plugin went untested where the plugin is absent, and failed there. Verified against
  `tests/unit/test_host.py` (`test_the_two_functions_are_found_where_the_tests_run`,
  `test_a_library_without_the_two_functions_is_passed_over`,
  `test_the_environment_comes_back_however_the_block_changed_it`,
  `test_without_the_two_functions_the_host_refuses_to_load`) and the revision's
  `verification/linux-gate-run.txt`.
- **pedalboard's Python parameter wrappers are held, one mapping per host; its native parameter
  objects never are.** A native object held across state loads crashed the process. The wrappers
  pedalboard's public mapping gives fetch the native parameter afresh on every attribute access,
  which is what makes holding them safe, and pedalboard caches them itself while rebuilding the
  mapping on each read of `parameters`, about 3 ms for 903, so the host reads it once. pedalboard
  adds that mapping to its native class at import, which its stubs do not show, so the loaded
  plugin is cast once to a private protocol of what `host.py` uses. Verified against `host.py`
  (`VitalHost.__init__`, `_HostedPlugin`, `_HostedParameter`), pedalboard 0.9.26's
  `AudioProcessorParameter.__getattr__` and `_get_parameters` (read for the fact), and
  `verification/probes-first-attempt.txt`.
- **What pedalboard raises never leaves the host, from any method that reaches it.** A read, a
  value or a state the plugin refuses is `PluginStateError`, a render `PluginRenderError`, each
  chained from pedalboard's `RuntimeError`, `ValueError` or `TypeError`, through the one guard
  every reach goes through; pedalboard's `preset_data` setter raises a bare `RuntimeError` on
  bytes it cannot take. A restore the plugin refuses in a measurement is `PluginStateError` too,
  the read's failure kept in its context chain. Verified against `host.py` (`_PEDALBOARD_ERRORS`,
  `_reached`, every `with _reached(...)`), `test_what_pedalboard_raises_is_the_package_s_error`,
  `test_every_reach_the_plugin_refuses_is_the_package_s_error` and
  `test_a_restore_the_plugin_refuses_is_the_package_s_error_after_the_read_s`.
- **Nor does a built-in's error leave the host.** A normalized value that is no number is
  `ParameterRangeError`, `math.isfinite`'s `TypeError` chained, and a bool is refused by name, as a
  render's length is, before anything is set; a host id `display_texts` does not host is
  `UnknownParameterError`, core's field a plain string; a state holding no `settings` object is
  `PluginStateError`, its text already one JSON object by the codec's validator. Verified against
  `host.py` (`_normalized`, `display_texts`, `_floats`),
  `test_a_normalized_value_that_is_no_number_is_refused_as_the_package`,
  `test_display_texts_for_a_host_id_not_hosted_is_named` and
  `test_a_state_holding_no_settings_object_is_the_package_s_error`.
- **The plugin is found at the path given, or at `DEFAULT_PATH`, and nowhere else**; nothing there,
  something the host cannot load, or a plugin not named Vital is `PluginLoadError`. Verified against
  `tests/unit/test_host.py`.
- **The map is used only on the machine, and with the plugin and version, it was measured
  from.** Its scales are the plugin's build's and its records that version's
  (`vital/parameter-map.md`); the host compares the map's `machine` with `platform.machine()`,
  then its `instrument` and `vital_version` with what the plugin reports, and raises one
  `MapMismatchError` naming the first that differs, its value in the map and the one found, at the
  first method that needs the map, never at load or in `measure`, so the census still runs there
  and a new map is the remedy. The map's `host`, pedalboard's version, is provenance and is not
  compared: the scales are the plugin's. Verified against `host.py` (`_parameter_map`),
  `errors.py` (`MapMismatchError`),
  `test_the_map_is_refused_on_another_machine_where_it_is_first_used` and
  `test_the_map_is_refused_on_another_vital_version_where_it_is_first_used`.
- **A measurement puts each parameter back and loads the starting state once, however its reads
  end.** Each parameter's grid is under a `try/finally` that sets it back to the normalized value it
  had, so the next is measured from the starting state; that is exact but for a float32 step on 22
  of 1.6.4's 903 (`env_1_decay_power` -2.0 comes back -2.0000005), the normalized value not
  reaching every preset value. The whole loop is under a `try/finally` that loads the starting
  state once, which puts those 22 back exactly and, as every load does, delays the sample by 4
  samples: a load after every parameter was 903 loads, 20.9 s a census against 14.4 s. A grid row
  holding other float keys than the starting state's is `CensusError` naming the parameter before
  any key is indexed. Verified against `host.py` (`measure`, `_moving_key`),
  `verification/restore-probe.txt`,
  `test_a_measurement_restores_the_state_however_it_ends`,
  `test_a_measurement_puts_each_parameter_back_and_loads_the_state_once`,
  `test_a_parameter_that_changes_the_preset_s_keys_is_named` and
  `test_the_census_regenerates_the_three_committed_files`.

## A render

- **A render asks pedalboard for one sample more than it wants and returns the first `samples`**,
  contiguous, pedalboard returning `int(duration · rate)` samples; fewer than asked, or another
  shape, is `PluginRenderError`, as is a length or a rate that is not a positive whole number, a
  bool included, refused before the plugin is called. A MIDI time is seconds from the render's
  start. Verified against `host.py` (`render`, `_whole`), `tests/unit/test_host.py`
  (`test_a_render_is_the_first_samples_asked_for_in_one_block`,
  `test_a_render_length_or_rate_that_is_not_a_positive_whole_number_is_refused`),
  `test_a_render_is_the_length_asked_for_and_finite` and
  `test_a_note_sounds_from_its_time_and_not_before`.
- **A render with no MIDI holds the preset's own sound, not a fixed transient.** On Vital's own
  starting state and on the start preset it is a transient that peaks near 0.02 and whose last
  non-zero sample is 4,889 at most. On the 75 installed presets the largest peak is 2.1, the
  plugin's ceiling: one reaches full scale as loaded and 17 with `volume` at its maximum, 51 peak
  above 0.02, and 32 stay at or above 0.001 for a second or more. It recurs at every render, and it
  is larger with the reset the host makes and not absent without it: Plucked String peaks at 0.21
  with one and 0.012 without. The host spec measured the starting state alone and called it a
  transient of 0.022. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). A render that does not open so is issue #21's to make. Verified against
  `probes.txt` sections 4 and 4b,
  `test_a_render_of_no_notes_on_the_start_preset_is_its_small_transient_and_no_warning` and
  `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding`, which holds
  today's behaviour by name.
- **A MIDI time lands one sample early on some samples; half a sample past lands on the sample.**
  The time of sample n itself, n over the rate, lands on n - 1 at 100,003, 1,000,003 and 4,000,001
  at 48 kHz and on 4 of 120 drawn; `(n + 0.5) / rate` lands on n at every value tried, five past 12
  million among them. A sample, not a count; a model that holds the time as a float32 predicted
  misses that did not happen. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4
  Pro, macOS 26.6.2). Verified against `probes.txt` section 1, `midi.py` and
  `test_a_note_lands_on_the_sample_core_s_rule_gives_it`.
- **On one channel, a note-off releases every voice of its pitch; on another channel a note keeps
  its own.** On one channel the first note-off of a pitch ends every note of it: of C4 from 0 to
  1 s and C4 from 0.5 to 1.5 s, the render falls silent at 1.015 s, where the second alone ends at
  1.510 s, and two struck on one sample both stop at the first end. On two channels each keeps its
  own length, and three overlapping on three channels each end at their own, where on one channel
  all three stop at the first end. A note alone sounds the same on any channel, its level within
  0.000002 and its centroid to the digits printed. The second probe measured these with the
  `mpe_enabled` setting off and on, but for the two-note overlap, which the first measured with it
  off. Two things are measured with it off alone, and are not claimed with it on:
  - that Vital voices two notes of one pitch on one channel as two voices until the note-off. With
    MPE off their overlap measures 0.2122 against one note's 0.1439; with it on it measures 0.1435,
    about the level of one, and two on two channels sum to another level than with it off,
    observations with no cause claimed;
  - that a note on a channel of its own keeps its own velocity, measured with `velocity_track` at
    100 %: 0.0892 for velocity 100 and 0.0223 for velocity 50 alone, and 0.0223 where the second
    sounds on after the first. On the start preset velocity sets no level, `velocity_track` being
    0 %, and the MPE-on runs were made there.

  Measured on Vital 1.6.4
  through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Verified against
  the revision after PR 23's review (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`)'s `overlap-probe.txt` and `overlap-probe-2.txt`, `midi.py` and
  `test_two_notes_of_one_pitch_that_overlap_each_sound_for_their_own_length`.
- **Vital gives samples past full scale, up to 2.1, and 2 ** 24 samples in one render,** every one
  finite, in 1.3 s, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2).
  Verified against `probes.txt` sections 2 and 3,
  `test_a_render_that_clips_carries_one_warning_and_the_event_carries_it` and
  `test_the_longest_render_is_given_and_one_sample_more_is_refused`.
- **Each integration module loads Vital once**, about two seconds a load. In `test_vital_plugin.py`
  a function-scoped fixture loads the initial state's text before each test, the sample's 4-sample
  delay on a load being nothing a test there depends on. In `test_vital_instrument.py` each test
  builds a new instrument, which loads the start preset twice, so the plugin holds the start's 903
  floats whatever the test before it set. Where the map was measured on another machine each module
  skips by name (`vital/preset-tests.md`). Verified against `tests/integration/test_vital_plugin.py`
  (`vital`, `initial`, `host`), `tests/integration/test_vital_instrument.py` (`vital`, `instrument`)
  and `test_the_next_instrument_starts_clean`.
