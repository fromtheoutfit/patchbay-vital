# The parameter map

How the map between Vital's VST3 parameters and a preset's keys is made, held and converted. A rule
here is about Vital's parameters; what any adapter's models do is `base/python/models.md`'s.
Written from `src/patchbay_vital/parameters.py`, `float32.py`, `census.py` and
`data/parameters.json`; the evidence is the `verification/` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`), measured on Vital 1.6.4 through
pedalboard 0.9.26 on arm64, of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), of the revision after the second
review (`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), of the revision
after the third (`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`), of the spec
of issue #13 (`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`), of the
revision after PR 14's review (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`), of
the revision after its second review
(`agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`), of the spec of issue #15
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`) and of the revision after
PR 14's fourth review (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`).

## Where it comes from

- **The map is measured from the plugin and committed as data, never written by hand or from Vital's
  source.** `census.py` sets each hosted parameter on a grid of normalized values, reads which state
  float moves and what the plugin displays, fits the scales and writes `data/parameters.json`; a
  parameter it cannot fit is `CensusError`, naming it, as are two parameters moving one preset
  value, a record the map's models refuse and ends that make no scale, and nothing is written;
  what is written is written whole or not at all, the key list and the map both staged and then
  both renamed over, the key list put back when the map's rename fails
  (`patchbay_vital.files.replace_files`), so the two never disagree. The scale is fitted by
  building the linear one once and the indexed one only where both ends are whole. Vital's source
  is GPLv3 and may be cited for corroboration, never copied. A new Vital is a new census in a
  spec. Verified against `census.py` (`build_map`, `fit_scale`, `_record`, `main`),
  `tests/unit/test_census.py` (`test_a_scale_that_is_neither_is_named`,
  `test_ends_that_make_no_scale_are_named`, `test_texts_in_no_one_known_unit_are_named`,
  `test_two_parameters_moving_one_preset_value_are_named`,
  `test_a_default_that_displays_as_no_number_is_named`,
  `test_a_key_list_that_cannot_be_written_leaves_the_map_unwritten`,
  `test_a_rename_failing_after_the_key_list_s_puts_the_key_list_back`) and
  `tests/integration/test_vital_plugin.py` (`test_the_census_regenerates_the_committed_map`).
- **The map records the machine the census ran on and the plugin it measured, and is used with
  no other.** The scales are the plugin's build's: the arm64 build computes a scale with one fused
  multiply-add, and another build may round the product and the sum apart, which the exact fit
  would refuse rather than write; the records are one version's parameters, and another version
  may rename or rescale them. `ParameterMap.machine` is `platform.machine()` where the census
  ran, `instrument` and `vital_version` what the plugin reported, `host` the pedalboard it ran
  through; the host refuses the map where the machine, the instrument or the version differs,
  naming which, and compares the host not at all (`vital/plugin-state.md`); a new census is the
  remedy. Verified against `census.py` (`build_map`), `parameters.py` (`ParameterMap`),
  `host.py` (`_parameter_map`), `test_the_map_records_the_machine_the_census_ran_on` and
  `test_the_committed_map_holds_every_hosted_parameter`.
- **A parameter's id is its preset key; pedalboard's key is `host_id`, read only by `host.py`.** 256
  of the 903 differ (`envelope_1_attack` is `env_1_attack`), and the preset key is the one a file, a
  diff and the instrument share. Verified against `parameters.py` (`MappedParameter.id`,
  `ParameterMap.find`), `host.py` and `tests/unit/test_parameters.py`
  (`test_a_map_finds_a_record_by_its_preset_key`).
- **`settings_keys.txt` is derived from the map, and a census never forgets a key**: its ids but
  the per-slot ones, and `PRESET_ONLY_KEYS` (`chorus_damping`, which old presets hold and no
  parameter does). The census writes both files and a test holds the one to the other. A key is
  known once Vital has written it, so a newer Vital that drops a parameter still has presets
  holding its key: the census refuses a list lacking a key the format knows now, `CensusError`
  naming up to four, and a spec adds them to `PRESET_ONLY_KEYS`, so the list stays derived from the
  map rather than kept as a union no map can check. Verified against `ParameterMap.settings_keys`,
  `census.py` (`key_list`, `main`), `test_the_format_s_key_list_is_derived_from_the_committed_map`,
  `test_the_committed_map_s_key_list_forgets_no_key_the_format_knows` and
  `test_a_key_list_that_would_forget_a_known_key_is_refused_and_nothing_written`.

## Two conversions

- **Normalized ↔ preset is `linear` or `indexed`, exact in float32.** The preset value is
  `r · span + minimum` rounded once to float32, a fused multiply-add as the arm64 build computes it
  (`float32.fma32`, in `Fraction` and integer rounding; separately rounded arithmetic is wrong on 252
  parameters); indexed rounds that to a whole number, a half away from zero, which the grid does
  land on: 0.5 on every boolean's scale computes to exactly 0.5 and the plugin holds 1 there, so
  `round`, a half to even, would fit no boolean. The span is computed once per pair of bounds and
  kept by them, never on the model, so a copy with another bound has its own. No tolerance
  anywhere. Back, `to_normalized` is the float32 nearest `(preset − minimum) / span`, unless
  `to_preset` of it misses the preset; then the float32 one step toward the preset
  (`float32.next_float32`), where that is in [0, 1] and lands on it, the scale rising with `r` so
  only that side can. On the 12 `env_N_delay` and `env_N_hold` records, at 126 powers of two each
  from 2 ** -125 to 1, the nearest multiplies back one float32 short, where the spacing halves, and
  only the step lands, so a set of 1.0 s holds 1.0 on Vital. The step is kept only inside [0, 1],
  where the host can set it, and that guard is reachable: on a scale from -1 to 2 ** 24 only the
  float32 above 1 lands on the maximum, so the maximum is not one the scale holds and its
  normalized value stays 1. `holds` says whether some normalized value in [0, 1] lands on a preset
  value, which `to_normalized` finds where any does; both read one private `_landing`, which
  computes the normalized value and where it lands once. `next_float32` narrows both its arguments
  to float32 first, as C's `nextafterf` receives them, and is the one way the package steps a
  float32; its tests check it against numpy's `nextafter`. Verified against `parameters.py`
  (`NormalizedScale`, `_landing`, `_round_half_away`, `_span`), `float32.py`,
  `tests/unit/test_float32.py` (`test_every_recorded_vector_is_the_plugin_s_value`,
  `test_a_float32_steps_to_its_neighbour_as_numpy_steps_it`), `tests/data/fma-vectors.txt`,
  `test_a_half_on_the_grid_goes_away_from_zero`,
  `test_a_scale_s_span_is_kept_by_its_bounds_so_a_copy_has_its_own`,
  `test_a_held_power_of_two_comes_back_through_the_normalized_path`,
  `test_a_scale_holds_its_values_and_none_past_its_ends` and
  `test_the_step_toward_a_preset_stays_where_the_host_can_set_it`.
- **Preset ↔ display is a curve: `multiply · skew(preset) + offset`**, the skew one of the six
  measured (linear, quadratic, quartic, square root, 2^x, 2^−x), its constants the shortest decimals
  that print every display text at six significant digits. A record's `Parameter` is in display
  units and its bounds and default are what the scale and curve compute, exactly on the machine
  that measured them; the model holds the record together in float32, the bounds and the default's
  display reaching the scale's ends and the preset default through the curve, so a libm whose
  `pow` is a double ulp apart still reads the map, and `to_preset` takes the parameter's own bounds
  and this platform's display of the scale's ends alike. Those displayed ends are computed in one
  place, `displayed_ends`, sorted whatever the curve's direction and kept by the curve's and the
  scale's values, which the census writes a parameter's bounds from and `to_preset` bounds by.
  Verified against `DisplayCurve`, `displayed_ends`, `MappedParameter`
  (`_the_parameter_reaches_the_scale`, `to_preset`), `census.py` (`_fit_curve`, `_record`) and
  `test_a_record_whose_parameter_is_not_its_scales_is_refused`,
  `test_a_record_holds_together_in_float32_so_a_libm_an_ulp_apart_still_reads_it`,
  `test_a_record_s_displayed_ends_are_the_scale_s_through_its_curve_in_order`,
  `test_a_curve_and_its_unit_are_found_from_the_texts`.
- **A displayed value comes back exactly, and so do the preset a parameter holds and the preset a
  display maps to, each through the normalized path, on every value; and the preset a display maps
  to is the held one but where neighbouring presets share a display, the one exception, stated over
  values, never a record's name.**

  **The rule.** `MappedParameter.to_preset` first takes the float32 nearest the curve's inverse,
  within the scale. Where the scale holds that float32, it is the answer. Where the scale does not
  hold it, the answer is, in this order:
  - what a set of that float32 holds, the scale's value at `to_normalized`'s result, which is
    Vital's own rounding of it, where that shows the display exactly;
  - otherwise the float32 on the other side of it, away from that value, where the scale holds it
    and it shows the display exactly;
  - otherwise the float32 itself, which the scale does not hold.

  So a set of any display a parameter shows holds a preset that shows it, on Vital as in the map.
  Only `volume`, at or below its 2 ** -43, has a float32 the scale skips for a display it shows,
  on 16,069,858 normalized values:
  - on 15,761,472 of them, what a set holds shows the display, so a set holds what it held before
    issue #15;
  - on the other 308,386, the values where a set before the fix showed a display one double off,
    the float32 on the other side is taken;
  - no value takes the third branch (`UNHELD` 0).

  These are counted in the revision after PR 14's fourth review, `verification/sweep.txt`. That
  spec's `verification/plugin-probe.txt` shows a load of the curve's float32 held by Vital at that
  same value. The rule has no tie to break. It replaced the neighbour nearer the curve's inverse,
  whose exact ties only a sort's order decided.

  **The third branch.** It is kept, not removed, though no counted value reaches it. The sweep
  counts only displays some held preset shows, and an arbitrary display, one no preset shows
  exactly, reaches the third branch. A unit test holds it:
  `test_an_arbitrary_display_keeps_the_curve_s_float32`, on `beats_per_minute`'s scale and curve,
  built in the test module as `_TEMPO`, at 216.85141355537831. The test is issue #8's
  characterization: whether such a display should take the nearer held neighbour is #8's finding
  1, and a decision there reverses the test on purpose. Of 20,000 displays drawn uniformly over
  `volume`'s range (seed 8), 5.4% take the third branch. An indexed scale takes no branch: its
  display goes to the nearest whole number, a half away from zero, as the plugin rounds.

  **The exception, in plain words.** `_assert_comes_back` runs every check exactly first, on every
  value. Only where the check that the display's preset is the held one fails does it ask
  `_shares_its_display`, and the value then passes only if that holds. The predicate asks one
  float32, the one next to the held preset on the side of the preset the display maps to: does it
  show the held preset's display? A float32 on the far side sharing the display excuses nothing,
  and at 2 ** -43 the float32 below shows its display where the one above does not
  (`test_where_volume_s_offset_absorbs_a_preset`). So the exception excuses a failure where its
  predicate holds, and never a value whose exact check passed.
  - It is asked on 570,997,534 values, all of `volume`'s, and holds on each (`A3x` 0). There the
    display's preset is another held one that shows the display, and the display cannot say which
    of them was held.
  - A float32 next to the preset, on either side, shows its display on 1,061,211,035 more values,
    where the exact check passes and the predicate is never asked. These are 18,227,438 of
    `volume`'s and 1,042,983,597 of the 9 exponential groups', `oversampling`'s whole numbers
    among them, whose neighbours the scale does not hold.
  - Both counts are in the same `verification/sweep.txt`.

  **The pinned values.** The values that found each defect are pinned as constants, written the
  same way in the unit and the integration modules, each with a comment naming it.

  Verified against `MappedParameter.to_preset` and `_resolve`, `NormalizedScale.to_normalized`,
  `NormalizedScale.holds`, `_assert_comes_back`, `_shares_its_display` and
  `test_a_value_the_parameter_holds_comes_back_exactly`,
  `test_every_committed_record_comes_back_exactly`, `test_where_volume_s_offset_absorbs_a_preset`,
  `test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset`,
  `test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`,
  `test_else_a_display_takes_the_float32_on_the_other_side`,
  `test_an_arbitrary_display_keeps_the_curve_s_float32`,
  `test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step`,
  `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`), `verification/census-run.txt`, and the
  `verification/sweep.txt`, `verification/plugin-probe.txt` and `verification/mutation.txt` of the
  revision after PR 14's fourth review. The defects were first found by the
  `verification/sweep.txt` of issue #13's spec and the `verification/sweep-first.txt` of the
  revision after PR 14's review.
- **A claim about every value a scale holds is counted over every float32 normalized value,
  exponent by exponent, and is never drawn uniformly.** 56% of the float32 values in [0, 1] lie at
  or below `volume`'s floor, yet they make up only about 1.5e-17 of the interval's length. So probe
  4's 2000 uniform draws a parameter never reached them, and Hypothesis's 32-bit floats did.

  **Each scale and curve group is counted once, by its first record.** Every method the count's
  paths call reads only the group's key: the parameter's kind and bounds, the scale's kind and
  bounds, and the curve's kind, multiply and offset. So a record's count is its group's. The
  revision after PR 14's fourth review also counted 14 records beside their groups: the three
  records with a curve offset and the 11 envelope delay and hold records that are not their group's
  first. All 14 matched their groups line for line (`verification/sweep-afterwards.txt`), so a
  later count leaves them out.

  **The 69 groups.** The count covers all 69 of the map's groups, 1,065,353,217 values each. For
  the `linear`, `quadratic`, `quartic` and `square_root` curves, 60 groups, it reproduces the map's
  arithmetic exactly in numpy. For the 9 `exponential` and `exponential_inverted` groups it calls
  the platform's own `pow` and `log2` value by value, as `DisplayCurve` does. That count is true of
  the machine it ran on, macOS 26.6.2 on arm64, whose libSystem 1351 holds the libm, and of
  another machine only as far as its libm gives the same values.

  **The check before counting.** Each group's reproduction is first checked against the shipped
  scalar methods on 200,010 values. The check covers every value it counts, the branch each value
  takes, and the tests' own `_shares_its_display`. A value it cannot certify exact goes to an
  exact scalar computation instead.

  **An exception** consulted only where its claim fails is counted by the failures it leaves
  (`A3x` 0). The count also says where its predicate holds but it is never asked.

  **A rule's branches are each counted.** A branch no counted value reaches is either removed or
  held by a unit test, and the standard says which; the third branch of `to_preset`, above, is
  held by a test.

  **A fix is counted against the old code's results, by a reproduction that shares none of the new
  code's guards.** A count the reproduction makes 0 by copying a guard is not evidence. Issue
  #15's spec counted `CHANGEDx` and `NCHANGEDx` that way, and both were 0 by construction. The
  revision after PR 14's fourth review instead reproduces each method another way:
  - `to_normalized` as the landing float32 nearest the exact quotient;
  - `to_preset` as its rule evaluated on every value.

  It compares both with `main`'s results, outside `main`'s unheld values:
  - nothing changed where a set of `main`'s value held it (`CHANGEDx` 0);
  - nothing changed where `main`'s normalized value landed (`NCHANGEDx` 0);
  - the display's preset changed on `volume`'s 16,069,858 values (`CHANGED`);
  - the normalized value changed at the 1,512 envelope powers of two, 126 on each of the 12
    records (`NCHANGED`).

  Verified against the `verification/sweep.txt`, both its sections, and the
  `verification/sweep-afterwards.txt` of the revision after PR 14's fourth review, and the
  `@example`s of `test_a_value_the_parameter_holds_comes_back_exactly`.

## Units and kinds

- **A unit is the display's suffix, renamed into `patchbay.Unit` by one table**: secs and s are
  seconds, ms seconds (÷1000), dB db, % percent, semitones and c (÷100) semitones, Hz hz, and x, v,
  voices and none none; `Beats Per Minute` is bpm by its label. An unknown suffix fails the census.
  Verified against `census.py` (`SUFFIX_UNITS`, `LABEL_UNITS`) and
  `test_the_label_names_a_unit_the_display_does_not_print`.
- **A switch is a boolean, other names a choice, other numbers continuous.** An indexed parameter of
  two values shown Off and On, or as numbers, is a boolean; one whose texts are other names is a
  choice, two names included (`eq_low_mode` is Shelf or High Pass); a numeric one (transposes,
  voices) is continuous on its indexed scale. A choice's value is its index, the preset value less
  the scale's minimum (`delay_tempo` starts at 4), and a choice or a boolean takes a whole index
  and nothing else, core's rule for them, so `to_preset` refuses a non-whole value as
  `ParameterRangeError`. Verified against `fit_record`, `MappedParameter.to_preset`,
  `test_a_parameter_of_two_values_is_a_switch_or_a_choice`,
  `test_a_choice_is_its_index_from_the_scale_s_minimum`,
  `test_a_choice_or_a_boolean_takes_a_whole_index_and_nothing_else` and
  `test_numbers_on_an_indexed_scale_are_continuous`.
- **Empty or repeated choice names are told apart by their index** (`option_<i>`, `<name>_<i>`),
  a made-up name lengthened by `_<i>` again while it is a kept name's or one already given, so no
  two choices share a name whatever the plugin's list; the plugin's own names are kept in
  `choice_labels`, so core's rule that choices are distinct and non-empty holds. Six parameters
  need it. Verified against `census.py` (`_choices`),
  `test_a_made_up_name_never_collides_with_a_given_one` and
  `test_the_committed_map_tells_its_choices_apart`.
