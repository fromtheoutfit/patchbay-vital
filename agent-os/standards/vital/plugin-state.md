# The hosted plugin

What Vital does when hosted, and how this package holds it to that. A rule here is about Vital
through pedalboard; the general form of a measured third party is `base/testing/tests.md`'s.
Written from `src/patchbay_vital/state.py` and `host.py`; the evidence is the `verification/` of
the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`):
`probes.txt`, `host-probes.txt`, `float-environment.txt` and `probes-first-attempt.txt`; of its
revision after PR 9's CI run (`agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`):
`linux-gate-run.txt` and `old-behaviour.txt`; and of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), whose `shape.md` records the
reading of pedalboard 0.9.26's wrappers and its `old-behaviour.txt` the findings' tests failing on
the code as reviewed.

## The state

- **The plugin's state is a preset's text in three containers, read and written by our own codec**:
  a `.vstpreset` (`VST3`, class id, `Comp` and empty `Cont`), JUCE's `VstW` header, and a VST2
  `CcnK`/`FBCh` bank of one chunk holding the JSON, exactly as a `.vital` file writes it, then 17 NUL
  bytes and `JUCEPrivateData`. Every field is kept as read, so `wrap(unwrap(x)) == x`; anything else
  is `PluginStateError` naming the layer, a negative chunk size and a text that nests too deeply to
  read among them, so no built-in `RecursionError` leaves the codec. Written from the bytes, not
  from any program's source. Verified against `state.py`, `tests/unit/test_state.py`
  (`test_wrap_reverses_unwrap`, `test_the_layers_are_where_the_plugin_put_them`,
  `test_each_layer_is_refused_by_name`, `test_a_text_that_is_not_one_object_is_refused`) and
  `test_the_codec_reads_and_writes_the_plugin_s_own_bytes`.
- **The state's text has one key a file lacks, `tuning`, held like any unread section**, as
  `VitalPreset.tuning`. Verified against `preset.py`, `format.py` and
  `tests/unit/test_format.py` (`test_a_plugin_state_comes_back_byte_for_byte`).
- **A preset loaded as state can be complete, routing and media included, but the plugin changes it.**
  It upgrades a preset older than 1.6.4 (keys added, sections re-encoded, floats moved); every load
  delays the embedded sample by 4 samples and re-quantizes it, a 16-bit value moving one step; a
  value off the host's grid snaps once after the host set that parameter. So the plugin's state is
  never read back as the preset it was given; the instrument keeps the preset it loaded (issue #8).
  Verified against `test_the_fixture_as_state_reads_back_but_its_sample_delayed`,
  `test_every_installed_preset_loads_as_state` and `test_a_routing_only_in_the_preset_text_is_heard`.

## The process

- **Every call into the plugin keeps the process's floating-point environment.** Loading and
  rendering Vital turn on flush-to-zero for the whole process and leave it on, so every subnormal
  after them, in Python and numpy, is zero. `host.py` saves the environment with `fegetenv` before
  each call and restores it with `fesetenv` after, both from the first library that holds them: the
  C library on macOS, the maths library on glibc, whose C library has neither, each name looked up
  only once the one before it is passed over. It refuses to load where no library holds them. Every
  public method that reaches the plugin does so inside the guard, reads included, and a fake plugin
  that turns upward rounding on at every call holds that: after each method the rounding mode is
  back. Verified against `host.py` (`_c_library`, `_environment_kept`, every `with
  _environment_kept()`), `tests/unit/test_host.py`
  (`test_every_public_method_gives_the_environment_back`) and
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
- **What pedalboard raises never leaves the host.** A value or a state the plugin refuses is
  `PluginStateError`, a render `PluginRenderError`, each chained from pedalboard's `RuntimeError`,
  `ValueError` or `TypeError`; pedalboard's `preset_data` setter raises a bare `RuntimeError` on
  bytes it cannot take. Verified against `host.py` (`_PEDALBOARD_ERRORS`, `set`, `load_state`,
  `render`) and `test_what_pedalboard_raises_is_the_package_s_error`.
- **The plugin is found at the path given, or at `DEFAULT_PATH`, and nowhere else**; nothing there,
  something the host cannot load, or a plugin not named Vital is `PluginLoadError`. Verified against
  `tests/unit/test_host.py`.
- **The map is used only on the machine it was measured on.** Its scales are the plugin's build's
  (`vital/parameter-map.md`); where the map's `machine` is not `platform.machine()` the host raises
  `MachineMismatchError` at the first method that needs the map, never at load or in `measure`, so
  the census still runs there and a new map is the remedy. Verified against `host.py`
  (`_parameter_map`) and `test_the_map_is_refused_on_another_machine_where_it_is_first_used`.
- **A measurement restores the state however its reads end**, each parameter's grid under a
  `try/finally` that puts the starting state back. Verified against `host.py` (`measure`) and
  `test_a_measurement_restores_the_state_however_it_ends`.

## A render

- **A render asks pedalboard for one sample more than it wants and returns the first `samples`**,
  contiguous, pedalboard returning `int(duration · rate)` samples; fewer than asked, or another
  shape, is `PluginRenderError`, as is a length or a rate that is not a positive whole number,
  refused before the plugin is called. A MIDI time is seconds from the render's start. A render
  from a reset opens with a decaying transient (peak 0.022, under 1e-5 by 50 ms). Verified against
  `host.py` (`render`, `_whole`), `tests/unit/test_host.py`
  (`test_a_render_is_the_first_samples_asked_for_in_one_block`,
  `test_a_render_length_or_rate_that_is_not_a_positive_whole_number_is_refused`),
  `test_a_render_is_the_length_asked_for_and_finite` and
  `test_a_note_sounds_from_its_time_and_not_before`.
- **The integration module loads Vital once**, about two seconds a load, and a function-scoped
  fixture loads the initial state's text before each test, the sample's 4-sample delay on a load
  being nothing a test there depends on. Verified against `tests/integration/test_vital_plugin.py`
  (`vital`, `initial`, `host`).
