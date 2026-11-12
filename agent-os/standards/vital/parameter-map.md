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
of issue #13 (`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`) and of
the revision after PR 14's review (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`).

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
  anywhere. Verified against `parameters.py` (`NormalizedScale`, `_round_half_away`, `_span`),
  `float32.py`, `tests/unit/test_float32.py` (`test_every_recorded_vector_is_the_plugin_s_value`),
  `tests/data/fma-vectors.txt`, `test_a_half_on_the_grid_goes_away_from_zero` and
  `test_a_scale_s_span_is_kept_by_its_bounds_so_a_copy_has_its_own`.
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
- **A displayed value comes back exactly, and the preset a parameter holds through the normalized
  path but at a power of two the path lands short of; the preset a display maps to does too, and a
  set of the display shows it again exactly, but where a curve's offset absorbs it, where a set
  shows the display or a neighbouring double.** The normalized path is
  `NormalizedScale.to_normalized`, the float32 nearest `(preset - minimum) / span`: on the 12
  `env_N_delay` and `env_N_hold` records, at 126 held powers of two a record from 2 ** -125 to 1,
  it multiplies back short of the power, where the float32 spacing halves, and lands one float32
  below, as Vital holds it (a set of 1.0 s holds 0.9999999403953552). The property excuses exactly
  that shape, by `_lands_below_its_power_of_two`, and the row of
  `tests/data/power-of-two-presets.txt` holds it, until issue #15 returns the neighbour that
  lands on it.
  `volume`'s presets at or below 2 ** -43, normalized 1.53642479121845e-17, display within 3.4e-7 dB
  of −80 dB and share a display; no other record with an offset fails anything on any float32
  normalized value. There `to_preset` gives the float32 nearest the curve's inverse, on 16,069,858
  normalized values one the scale does not hold, and a set holds the scale's value at
  `to_normalized`'s result, as Vital does; on 308,386 of them, in exponents −58 to −56, that value
  displays one double ulp off the display set, 154,100 above it and 154,286 below, none further.
  Issue #15 is to take there the held neighbour that shows the display. Until it does, the
  property asserts the bound, and the four rows of `tests/data/volume-floor.txt`, each a value with
  the step its set's display lands at, hold the map there in both directions: one file, read
  through `tests/conftest.py`'s fixture by the unit and the integration tests, whose header says
  #15 changes its three non-zero rows. An
  arbitrary display value goes to the float32 nearest the curve's inverse, on an indexed scale a
  whole number rounded a half away from zero as the plugin rounds, which need not be one the scale
  holds (5.7% of `volume`'s, issue #8's finding 1). Verified against `MappedParameter.to_preset`,
  `_assert_comes_back` and `test_a_value_the_parameter_holds_comes_back_exactly`,
  `test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step`,
  `test_where_volume_s_offset_absorbs_a_preset`,
  `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded`,
  `NormalizedScale.to_normalized`, `_lands_below_its_power_of_two`,
  `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`,
  `test_every_committed_record_comes_back_exactly`, `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`),
  `tests/data/volume-floor.txt`, `tests/data/power-of-two-presets.txt`, `tests/conftest.py`,
  `verification/census-run.txt`, and the `verification/sweep.txt` and
  `verification/plugin-probe.txt` of issue #13's spec and of the
  revision after PR 14's review, whose `verification/sweep-first.txt` found the power of two.
- **A claim about every value a scale holds is counted over every float32 normalized value,
  exponent by exponent, wherever the count reproduces the map's arithmetic bit for bit, and is never
  drawn uniformly.** 56% of the float32 values in [0, 1] lie at or below `volume`'s floor and about
  1.5e-17 of its measure, so probe 4's 2000 uniform draws a parameter never reached it and
  Hypothesis's 32-bit floats did. The count reproduces the map's arithmetic exactly in numpy for
  the `linear`, `quadratic`, `quartic` and `square_root` curves, and is checked against the shipped
  scalar methods on 200,007 values of a group before it counts that group, a value it cannot
  certify exact going to the scalar method: 60 of the map's 69 scale and curve groups, and each of
  the six records with a curve offset, 1,065,353,217 values each. The 9 `exponential` and
  `exponential_inverted` groups skew through the platform's `pow` and `log2`, which numpy's own do
  not reproduce, so they rest on the property's exponent-spread draws and pinned examples; counting
  them would call the platform's libm value by value, hours of compute, open until it is scheduled.
  Verified against the revision after PR 14's review's `verification/sweep.txt` and the `@example`s
  of `test_a_value_the_parameter_holds_comes_back_exactly`.

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
