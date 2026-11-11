# Measures, not samples

How a test asserts what Vital rendered or holds. Written from
`tests/integration/test_vital_plugin.py`; the evidence is the `verification/probes.txt` and
`verification/host-probes.txt` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`) and the
`verification/plugin-probe.txt` of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`).

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
- **What Vital holds after a set is compared exactly with the value the map computes. How far that
  value's display lands from the display set is a measure, a count the probe made.** The map gives
  the preset a set holds, the scale's value at `to_normalized`'s result, and the test asserts that
  the state's float is that value, with no tolerance, and is not `to_preset`'s. The distance of its
  display from the one set is counted in double ulps: the probe counted 0 at issue #13's value and
  1 at each of four of the 308,386 values below `volume`'s floor whose display comes back off.
  `_BELOW_VOLUME_S_FLOOR` holds the count for the issue's value and for the smallest of those four,
  and its comment names the probe. `_held_after_a_set` and `_double_ulps` are written once in the
  test module, and the probe imports them, so the test and the probe compute the same thing.
  Verified against `tests/integration/test_vital_plugin.py`
  (`test_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`) and issue #13's
  `verification/plugin-probe.txt`.
