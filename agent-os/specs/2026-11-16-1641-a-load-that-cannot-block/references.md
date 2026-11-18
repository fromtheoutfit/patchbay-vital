# References for a load that cannot block (issue #20)

## Similar Implementations

### The probe scripts of the instrument spec (issue #8)

- **Location:** `agent-os/specs/2026-11-15-1448-the-instrument/verification/probes.txt`, section 5
  and the scripts embedded at its end (`probe_load.py`, `probe_loads.sh`, `transcript.sh`,
  `tree.sh`, `machine.sh`).
- **Relevance:** the measurement issue #20 rests on: 20 texts, each loaded in a process of its
  own and killed after 6 s, 11 never returning.
- **Key patterns:**
  - One load per process under a time limit, the caller killing what has not returned, and one
    `sample` of a waiting process kept to show where it waits.
  - `CASES` in `probe_load.py`: the 20 texts, each built from the start preset, and beside each
    whether the package's writer can write it and what the guard does with it. This spec's
    probes take the same 20, by the same construction.
  - `transcript.sh`: the date and the branch, the machine and the tree before, the command's
    whole output, the tree and the machine after, the two trees compared with `cmp`, and every
    script embedded with its blob. Written outside the tree and copied in afterwards.
  - The marker: `filter_1_cutoff` set to normalized 0.9 before the load, read afterwards, to
    tell a load that was ignored from one that was made.

### `host.py`'s floating-point guard

- **Location:** `src/patchbay_vital/host.py` (`_LIBRARY_NAMES`, `_c_library`, `_environment_kept`,
  `_reached`) and `tests/unit/test_host.py`
  (`test_the_two_functions_are_found_where_the_tests_run`,
  `test_a_library_without_the_two_functions_is_passed_over`,
  `test_the_environment_comes_back_however_the_block_changed_it`,
  `test_without_the_two_functions_the_host_refuses_to_load`).
- **Relevance:** the package's one reach into a system library through `ctypes`, and the one
  place every call into the plugin goes through.
- **Key patterns:**
  - The library is looked up once, in order, and a library without what is needed is passed
    over; where none holds it the host refuses to load, by name.
  - A context manager around each call into the plugin, restoring however the call ends.
  - The guard is held by unit tests that need no plugin, so CI, which has no Vital, runs it. A
    reach into AppKit, or a child process, is held the same way or said not to be.

### The fake plugins

- **Location:** `tests/unit/test_host.py` (`_FakePlugin`, `_FakeParameter`, the `fake` fixture)
  and `tests/unit/test_instrument.py` (`_FakeVital`, `_FakeParameter`).
- **Relevance:** the stand-ins the unit tests drive a real `VitalHost` and a real
  `VitalInstrument` over, with no Vital.
- **Key patterns:**
  - `_FakePlugin.touch` runs at every call into the plugin, so a test can make any reach raise,
    or record the state each call found.
  - `_FakeVital` refuses a named text, which is how the rollback and the lost step are tested.
    A plugin that blocks, or that answers with an alert, extends these.

### `load_patch`'s rollback

- **Location:** `src/patchbay_vital/instrument.py` (`load_patch`, `_send`, `_refuse_once_lost`)
  and `tests/unit/test_instrument.py`
  (`test_a_load_the_plugin_refuses_puts_the_model_s_text_back_and_is_refused_as_a_patch`,
  `test_a_plugin_that_refuses_the_model_s_own_text_too_leaves_the_instrument_out_of_step`,
  `test_once_out_of_step_every_call_that_reaches_the_plugin_is_refused_before_anything_else`).
- **Relevance:** what the instrument already does when the host raises `PluginStateError` on a
  load: the model's own text is sent again and the call is refused as a patch; if that is
  refused too the instrument has lost step.
- **Key patterns:**
  - Checks, then the plugin, then the model, then one event; a refused call changes nothing
    and publishes nothing.
  - A load that now raises where it used to block arrives here as `PluginStateError` and needs
    no new path, if the plugin can be put back to the model's text afterwards. Whether it can is
    a probe's to say.

### pedalboard 0.9.26, as shipped

- **Location:** `.venv/lib/python3.12/site-packages/pedalboard/ExternalPlugin.h`, shipped in the
  wheel. Read for a fact; nothing is copied from it.
- **Relevance:** the `preset_data` setter calls the plugin's state load with no release of the
  GIL, so nothing in Python runs while the alert waits. The probes show it by count.
