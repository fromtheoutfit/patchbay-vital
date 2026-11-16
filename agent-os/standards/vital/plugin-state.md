# The hosted plugin

What Vital does when hosted, and how this package holds it to that. A rule here is about Vital
through pedalboard; the general form of a measured third party is `base/testing/tests.md`'s.
Written from `src/patchbay_vital/state.py` and `host.py`; the evidence is the `verification/` of
the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`):
`probes.txt`, `host-probes.txt`, `float-environment.txt` and `probes-first-attempt.txt`; of its
revision after PR 9's CI run (`agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`):
`linux-gate-run.txt` and `old-behaviour.txt`; of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), whose `shape.md` records the
reading of pedalboard 0.9.26's wrappers and its `old-behaviour.txt` the findings' tests failing on
the code as reviewed; of the revision after the second review
(`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), whose `old-behaviour.txt`
does the same for its findings; of the revision after the third review
(`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`): `restore-probe.txt` and
`old-behaviour.txt`; and of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`), the revisions after PR
14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
`agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`) and the spec of issue #15
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`): `plugin-probe.txt`; and of
the spec of issue #8 (`agent-os/specs/2026-11-15-1448-the-instrument/`): `probes.txt` and
`probes-2.txt`.

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
- **Vital reports no load it cannot use, and `load_state` raises for none.** Of 20 texts, each
  loaded in a process of its own, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2):
  - 11 never returned. Vital puts up a modal alert and its caller waits for ever, in AppKit's
    `NSAlert runModal` under Vital's `SynthProcessor::setStateInformation`, by a sample of the
    process. A text with no sections does it, and so does one whose fault is inside a section: three
    wavetables whose `groups` is a number.
  - A `synth_version` newer than the plugin's is ignored whole, with no error and the plugin
    unchanged.
  - `wavetables` or `lfos` as an empty array loads the floats and keeps the sections the plugin had.
  - A key the text lacks goes to its default, 132 of 132.

  So a text is judged before the plugin is given it (`vital/instrument.md`, the guard); a load
  that may not return is run only in a process of its own with a time limit, as a transcript; and
  no test sends one. A load that cannot block is issue #20's to make. Verified against
  `probes.txt` sections 5 and 5b, `instrument.py` (`check_loadable`) and
  `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called`.
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
  it set. Verified against `host.py` (`_c_library`, `_environment_kept`, `_reached`, `_name_of`,
  `_text_for`, `VitalHost.__init__`), pedalboard 0.9.26's `AudioProcessorParameter.__init__` (read
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
