# The parameter map

How the map between Vital's VST3 parameters and a preset's keys is made, held and converted. A rule
here is about Vital's parameters; what any adapter's models do is `base/python/models.md`'s.
Written from `src/patchbay_vital/parameters.py`, `float32.py`, `census.py` and
`data/parameters.json`; the evidence is the `verification/` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`), measured on Vital 1.6.4 through
pedalboard 0.9.26 on arm64, of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`) and of the revision after the second
review (`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`).

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
- **`settings_keys.txt` is derived from the map**: its ids but the per-slot ones, and
  `PRESET_ONLY_KEYS` (`chorus_damping`, which old presets hold and no parameter does). The census
  writes both files and a test holds the one to the other. Verified against
  `ParameterMap.settings_keys` and `test_the_format_s_key_list_is_derived_from_the_committed_map`.

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
- **A displayed value comes back exactly; a preset value does too, but where a curve's offset absorbs
  it.** `volume`'s presets at or below 2 ** -43 display within 3.4e-7 dB of −80 dB and share a
  display; the sweep found no other. An arbitrary display value comes back as the nearest one the
  parameter holds, which on an indexed scale is a whole number, rounded a half away from zero as
  the plugin rounds. Verified against `MappedParameter.to_preset`,
  `test_a_value_the_parameter_holds_comes_back_exactly`,
  `test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step`,
  `test_where_volume_s_offset_absorbs_a_preset`, `test_every_committed_record_comes_back_exactly`
  and `verification/census-run.txt`.

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
