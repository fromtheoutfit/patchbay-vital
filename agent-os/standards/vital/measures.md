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
after PR 14's fourth review (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`);
the pinned values' file is the revision after its sixth review's
(`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`).

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

  The pinned values are written once, in `tests/data/pinned-values.txt`: a `#` header saying
  what each set is and which spec measured it, then one `<set> <float32> <name>` line a value.
  Each test module reads it through `pytestconfig.rootpath` with a reader of a few lines of its
  own, since it is the values, not the parsing, that must not be written twice. A missing file
  fails each test that reads it with the path, and a line that is not a float32 of a known set
  with the file and the line (ME, MF and MF2 in the sixth review's `verification/mutation.txt`,
  in both modules, the integration module's with Vital). That replaced two copies of the values
  held equal by a test reading the integration module's source, whose syntax-tree checks the
  fifth and sixth reviews each found gaps in.

  The test and the probe run one sequence, `initial` loaded before each set. `_held_after_a_set` is
  written once in the test module. The fourth and fifth reviews' probe imported it and the
  pinned values, then constants, and printed them by blob and source, so the test and the probe
  computed the same thing; a probe now reads the values from the file, as the tests do.

  Verified against `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`, `_held_after_a_set`, `_pinned`),
  `tests/unit/test_parameters.py` (`_pinned`,
  `test_the_pinned_values_file_holds_two_named_sets`), `tests/data/pinned-values.txt`, the
  `verification/plugin-probe.txt` of the revision after PR 14's fourth review
  (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`) and the
  `verification/mutation.txt` of the sixth.
