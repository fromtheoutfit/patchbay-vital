# Measures, not samples

How a test asserts what Vital rendered or holds. Written from
`tests/integration/test_vital_plugin.py`; the evidence is the `verification/probes.txt` and
`verification/host-probes.txt` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`) and the
`verification/plugin-probe.txt` of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`) and of
the revisions after PR 14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`
and `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`), of the spec of issue
#15 (`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`) and of the revision
after PR 14's fourth review (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`).

- **Vital's audio is not sample-reproducible**, so no test compares samples: two renders in a row
  differ, and so do two instances in one state (spectral centroids 4657 and 4610 Hz). Verified
  against `verification/probes.txt` ("two renders in a row identical: False").
- **Every audio assertion is a measure against a named tolerance, and the constant's comment says
  which probe its number came from and what the probe measured**: the 20 ms RMS variation of a
  routed render above 0.5 where the probe measured 1.351, the quiet before a note under 1e-6 where it
  measured 0. A tolerance with no source is a guess. Verified against the constants at the head of
  `tests/integration/test_vital_plugin.py` and `test_a_routing_only_in_the_preset_text_is_heard`,
  `test_a_note_sounds_from_its_time_and_not_before`.
- **A measure is the probe's own computation, written once**, so the test measures what the probe
  did: `_variation` is the probes' 20 ms RMS coefficient of variation over 0.2-1.4 s. Verified
  against `tests/integration/test_vital_plugin.py` (`_variation`) and `verification/probes.txt`
  (`variation`).
- **What Vital holds after a set is compared exactly with the value the map computes, and its
  display with the display set.** The map gives the preset a set holds, the scale's value at
  `to_normalized`'s result, and the test asserts that the state's float is that value, with no
  tolerance.
  - At `volume`'s pinned values at or below its floor it is `to_preset`'s value, one the scale
    holds and never the curve's own float32 (`record.curve.to_preset`), and its display is the
    display set. At issue #13's value that is what a set of the curve's float32 holds, and at the
    other three the float32 on its other side.
  - At the envelope records' pinned powers of two it is the power, a set of 1.0 s holding 1.0.

  The pinned values are constants in the integration module, written as the unit module writes
  the same values, each with a comment naming it. `test_the_integration_module_pins_the_same_values`
  holds the two copies equal. It reads the integration module's source, and it fails by name if
  either tuple is missing, renamed, not a plain literal or different (M11 to M14 in the
  `verification/mutation.txt` of the revision after PR 14's fourth review). It also fails by name
  unless the name is bound exactly once in the module, by one assignment at the top level, to a
  tuple of floats: an augmented assignment, a second assignment inside an `if` and a literal
  `ast.literal_eval` refuses each fail it (M19 to M21 in the fifth review's
  `verification/mutation.txt`).

  The test and the probe run one sequence, `initial` loaded before each set. `_held_after_a_set` is
  written once in the test module, and the probe imports it and the pinned values and prints them
  by blob and source, so the test and the probe compute the same thing.

  Verified against `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`, `_held_after_a_set`, `_VOLUME_FLOOR`,
  `_POWERS_OF_TWO`), `tests/unit/test_parameters.py`
  (`test_the_integration_module_pins_the_same_values`), and the `verification/plugin-probe.txt`
  of the revision after PR 14's fourth review
  (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`).
