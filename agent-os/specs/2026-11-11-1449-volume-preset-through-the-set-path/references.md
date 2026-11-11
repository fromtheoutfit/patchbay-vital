# References for Issue #13: volume's preset through the set's path

## Similar Implementations

### The property and its excuse

- **Location:** `tests/unit/test_parameters.py` (`_assert_comes_back`, `_ABSORBED`,
  `test_a_value_the_parameter_holds_comes_back_exactly`, `test_where_volume_s_offset_absorbs_a_preset`,
  `test_every_committed_record_comes_back_exactly`)
- **Relevance:** the failing assertion (line 221) and the guard that already excuses the preset
  coming back below `volume`'s floor (line 222).
- **Key patterns:** a known counterexample pinned with a commented `@example`; one excuse table,
  `_ABSORBED`, documented with the measurement it rests on; a deterministic test beside the
  property naming the value at the edge.

### The map's conversions

- **Location:** `src/patchbay_vital/parameters.py` (`NormalizedScale`, `DisplayCurve`,
  `MappedParameter.to_preset`, `to_normalized`, `from_normalized`), `src/patchbay_vital/float32.py`
  (`fma32`, `round_to_float32`, `to_float32`)
- **Relevance:** the paths the property composes: normalized → preset by one float32 rounding of
  the exact multiply-add, preset → display in double, display → preset as the float32 nearest the
  curve's inverse, preset → normalized as the float32 nearest the exact quotient.
- **Key patterns:** exact arithmetic the sweep reproduces in numpy (a product of two float32 values
  exact in a double; a sum rounded once with TwoSum's remainder; a quotient's nearest float32
  chosen from three candidates by exact distance), checked value for value against these methods.

### The plugin's measures

- **Location:** `tests/integration/test_vital_plugin.py` (the `vital` and `host` fixtures,
  `test_a_value_set_through_the_host_is_the_one_the_state_holds`, `_ulps`, the probe-sourced
  constants at the head of the module), `src/patchbay_vital/host.py` (`VitalHost.set`, `get`,
  `state`, `load_state`, `_floats`)
- **Relevance:** where Vital's own value after a set is read; the new measure sits beside the test
  that sets a display through the host and reads the state's float.
- **Key patterns:** a constant whose comment names the probe its number came from; a helper written
  once and used by the probe; the module's one loaded Vital, skipping by name without it.

### Probe 4 and its correction

- **Location:** `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/verification/probes.txt`
  (probe 4, lines 406-451 and 603-609) and its `shape.md` Decision 6
- **Relevance:** the 1,104,000 values issue #13 says this value falsifies, and the earlier sweep
  that set `_ABSORBED` at 2 ** -43.
- **Key patterns:** what was drawn (`rng.random`, uniform in value) and what was checked (the
  display → preset round trip and the scale's inverse, never the preset through the normalized
  path); Decision 6 leaving "what the instrument stores where two presets share a display" to #8.

### Core's promise

- **Location:** `patchbay/contracts.py` at `dd2bcad69dadeb38c6e1e660b2e0ddced13861eb`
  (`Instrument.get`, `Instrument.set`), installed in `.venv`
- **Relevance:** what the property has to hold for the instrument of issue #8: after `set`, the
  value given comes back at a bound and at any value `get` has returned that `set` takes.

### Issue #8

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/issues/8 ("Findings that bear on
  it", probe 4; "From core's review of PR 19", findings 1 and 3; Decision 1)
- **Relevance:** the questions this spec leaves open (whether `set` picks the nearer neighbour,
  what `set(get())` does to the stored value at the floor), and the body this spec revises.
