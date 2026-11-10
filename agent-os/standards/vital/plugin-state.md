# The hosted plugin

What Vital does when hosted, and how this package holds it to that. A rule here is about Vital
through pedalboard; the general form of a measured third party is `base/testing/tests.md`'s.
Written from `src/patchbay_vital/state.py` and `host.py`; the evidence is the `verification/` of
the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`):
`probes.txt`, `host-probes.txt`, `float-environment.txt` and `probes-first-attempt.txt`; and of its
revision after PR 9's CI run (`agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`):
`linux-gate-run.txt` and `old-behaviour.txt`.

## The state

- **The plugin's state is a preset's text in three containers, read and written by our own codec**:
  a `.vstpreset` (`VST3`, class id, `Comp` and empty `Cont`), JUCE's `VstW` header, and a VST2
  `CcnK`/`FBCh` bank of one chunk holding the JSON, exactly as a `.vital` file writes it, then 17 NUL
  bytes and `JUCEPrivateData`. Every field is kept as read, so `wrap(unwrap(x)) == x`; anything else
  is `PluginStateError` naming the layer. Written from the bytes, not from any program's source.
  Verified against `state.py`, `tests/unit/test_state.py` (`test_wrap_reverses_unwrap`,
  `test_the_layers_are_where_the_plugin_put_them`, `test_each_layer_is_refused_by_name`) and
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
  C library on macOS, the maths library on glibc, whose C library has neither. It refuses to load
  where no library holds them. Verified against `host.py` (`_c_library`, `_environment_kept`) and
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
- **pedalboard's parameter objects are reached through its public mapping on each access**, never
  held: a native parameter object held across state loads crashed the process. pedalboard adds
  that mapping to its native class at import, which its stubs do not show, so the loaded plugin is
  cast once to a private protocol of what `host.py` uses. Verified against `host.py`
  (`_HostedPlugin`, `_HostedParameter`) and `verification/probes-first-attempt.txt`.
- **The plugin is found at the path given, or at `DEFAULT_PATH`, and nowhere else**; nothing there,
  something the host cannot load, or a plugin not named Vital is `PluginLoadError`. Verified against
  `tests/unit/test_host.py`.

## A render

- **A render asks pedalboard for half a sample more than it wants**, pedalboard returning
  `int(duration · rate)` samples, and is refused as `PluginRenderError` unless exactly `(2,
  samples)`. A MIDI time is seconds from the render's start. A render from a reset opens with a
  decaying transient (peak 0.022, under 1e-5 by 50 ms). Verified against `host.py` (`render`),
  `test_a_render_is_the_length_asked_for_and_finite` and `test_a_note_sounds_from_its_time_and_not_before`.
