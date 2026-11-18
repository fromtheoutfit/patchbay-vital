# Testing against Vital's presets

What this repository's tests may hold of Vital's and how they read the rest. The general form, a
test over an instrument's installed content, is proposed upstream; what is here is the part about
Vital. Written from `tests/integration/test_factory_round_trip.py`, `test_vital_plugin.py` and
`tests/data/`; the evidence is the `verification/probes.txt` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), for the skip on another machine the revision
after the second review of PR 9
(`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), for the start preset and the
instrument's tests the spec of issue #8 (`agent-os/specs/2026-11-15-1448-the-instrument/`), for a
text Vital does not take the spec of issue #20
(`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`), and for a child that ends itself the
revision after the review of PR 26 (`agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`):
`alarm-probe.txt` and `mutation.txt`.

- **No preset, sample, wavetable, or LFO of Vital's is committed.** Vital's EULA (updated 2024-02-29)
  bars redistributing "presets, samples, wavetables, skins, LFOs or other media created from any
  unaltered VITAL AUDIO content", and this repository is public. A preset that embeds Vital's
  defaults counts: a saved Init carries its White Noise sample and Init wavetables. Verified against
  `tests/data/`.
- **The unit suite's one real file is a save from Vital 1.6.4 with its media replaced**,
  `tests/data/init-media-replaced.vital`: its structure and 909 settings are the save's, and its
  sample, wavetable audio and LFO shapes were written for the test, so the suite holds the current
  key set with none of Vital's media. Verified against `tests/unit/test_format.py`
  (`test_a_preset_comes_back_byte_for_byte`, `test_a_1_6_4_preset_reads_as_its_models`).
- **The preset the package ships is Vital's default values with media of the package's own.**
  `src/patchbay_vital/data/start.vital` holds each parameter's default, which the parameter map
  ships already as an interoperability fact, and a wavetable, LFO and warp shapes and a sample each
  generated from a formula, none of them Vital's. A test rebuilds every section from its formula, so
  the file cannot come to hold anything else. Shipping it is the owner's licence call of 2026-11-15,
  not legal advice, revisited before any release. Verified against `src/patchbay_vital/start.py` and
  `tests/unit/test_start.py`.
- **A count measured over the installed presets may be committed; a preset may not.**
  `tests/data/upgraded-floats.txt` holds 46 floats by preset name and key, what Vital makes of 11
  older presets as it loads them, and no preset's content beyond those floats. Its header says what
  was measured, on which Vital, host and machine, and its reader fails by name on a line that is not
  one. Committing it, preset names, keys and 46 measured values and no preset's content, is the
  owner's call of 2026-11-16, not legal advice, recorded here beside the manifest and the start
  preset and revisited before any release to PyPI. Verified against
  `tests/integration/test_vital_instrument.py` (`_upgraded`,
  `test_what_the_data_file_of_upgraded_floats_holds`).
- **The installed presets are read from `~/Music/Vital` against
  `tests/data/factory-manifest.txt`**, Vital's own seven and the packs' 68, grouped and reported
  apart. `User/` is where Vital keeps a person's saves, so the walk leaves it out. A file listed and
  missing, or present and unlisted, fails by name, and changing the manifest is a deliberate commit.
  Verified against `tests/integration/test_factory_round_trip.py`
  (`test_the_installed_presets_are_the_manifest_s`) and `verification/probes.txt`.
- **A test of the hosted plugin runs where Vital is installed at the host's `DEFAULT_PATH` and skips
  by name elsewhere**, CI among the places, and skips naming both machines where the committed
  map was measured on another machine than the tests run on: the host would refuse the map there
  and the census test would compare the other machine's name, and a new census is the remedy,
  not a failing test. It reads the same manifest and the same fixture, the fixture loaded as the
  plugin's state. What the plugin reports about itself, its parameters'
  names, ranges and display texts, is an interoperability fact and is committed as the parameter
  map; the plugin's own state, which embeds its default media, is never committed. Verified against
  `tests/integration/test_vital_plugin.py` (the `vital` and `host` fixtures,
  `test_every_installed_preset_loads_as_state`,
  `test_the_fixture_as_state_reads_back_but_its_sample_delayed`),
  `tests/integration/test_vital_instrument.py` (the `vital` fixture) and
  `src/patchbay_vital/data/parameters.json`.
- **No test gives Vital, in the test's own process, a text it may not return from; one that must
  gives it in a child it can kill.** Vital answers a preset it cannot read with a modal alert,
  which the host answers on macOS alone, and some texts kill the process
  (`vital/plugin-state.md`). So every load a test sends in its own process is a text Vital was seen
  to load, which passes the instrument's guard first. A test that holds the remedy against Vital
  gives its text in a child of its own under a time limit, 20 s, and a test of the watch itself runs
  AppKit's own alert the same way, 10 s. No test gives Vital a text that killed it: those are run
  only in a transcript. A test that hung would hang the gate.
- **Every child a test starts ends itself at a watchdog past its parent's limit.** The child's first
  statements arm `faulthandler.dump_traceback_later(<seconds>, exit=True)`, before anything that
  could block is imported: 40 s against the integration children's 20 s, 30 s against the real-alert
  child's 10 s, a test holding each greater. While the parent lives its kill comes first and the
  test fails by the parent's name; where the parent is gone, killed with no chance to kill its
  child, the child ends itself, its stack on its stderr. The watchdog is a C thread that needs no
  GIL, which pedalboard holds while Vital's alert waits: it ended a child blocked in Vital's alert,
  and one in AppKit's, 0.052 to 0.070 s past a 3 s limit. `signal.alarm` with SIGALRM's default
  action did too, 0.016 to 0.040 s past, and is not used, as it is not on every platform (the
  revision after the review of PR 26's `alarm-probe.txt`). "It ended itself" is three things
  together, status 1, a stderr line beginning "Timeout (", and no kill by the parent, judged by one
  function, `_ended_itself`, in each of the two modules that start children, the same name, checks
  and failure message in each, every failure carrying the child's stderr: a module of one suite
  cannot import from the other's, and test support shared between them has no home in the layout.
  "Timeout (" is CPython's header and not documented as a format, so in each module a stand-in its
  parent never kills is the test that fails if it changes. The stand-in that never returns holds its
  parent's limit, 3 s, by a lock it holds: the file says the child started and the lock is free,
  never a pid, which another process may have by then; "the child never started" and "it did not
  end" fail by names of their own. Verified against `tests/integration/test_vital_instrument.py`
  (`_armed`, `_ended_itself`, `_child_failed`, `_in_a_child`,
  `test_a_child_that_does_not_return_is_killed_at_its_limit_and_the_test_fails_by_name`,
  `test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog`,
  `test_each_child_s_watchdog_is_past_its_parent_s_limit`,
  `test_a_child_ended_itself_only_by_all_three_checks`,
  `test_a_patch_vital_answers_with_its_alert_is_refused_and_the_plugin_put_back`,
  `test_a_state_vital_ignores_is_refused_by_the_marker_and_the_plugin_left_as_it_was`),
  `tests/unit/test_host.py` (`_armed`, `_ended_itself`, `_child_failed`,
  `test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back`,
  `test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog`,
  `test_the_real_alert_child_s_watchdog_is_past_its_parent_s_limit`,
  `test_a_child_ended_itself_only_by_all_three_checks`), MW4 and MR16 to MR22 in the revision after
  the review of PR 26's `mutation.txt`, where a watch that answers nothing leaves that child to be
  killed at its limit, and `probes.txt` section 5 of the spec of issue #8.
