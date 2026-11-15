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
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`), of the revisions after
PR 14's fourth, fifth and sixth reviews
(`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`,
`agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/` and
`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`), of the spec of issue #16
(`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`) and of the revision after the
review of patchbay-vital's PR 19 (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`).

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
  within the scale, and on an indexed scale the nearest whole number to it, a half away from zero.
  The answer is what a set of that value holds: the scale's value at `to_normalized`'s result,
  Vital's own rounding of it, which is the value itself wherever the scale holds it. There is one
  exception: the float32 on the other side of it, away from what the set holds, is the answer
  where what the set holds does not show the display exactly, that float32 does, and the scale
  holds it. So the answer is always a preset the scale holds, and a set of
  `to_normalized(display)` holds it (issue #16).

  So a set of any display a parameter shows holds a preset that shows it, on Vital as in the map.
  Only `volume`, at or below its 2 ** -43, has a float32 the scale skips for a display it shows,
  on 16,069,858 normalized values:
  - on 15,761,472 of them, what a set holds shows the display, so a set holds what it held before
    issue #15;
  - on the other 308,386, the values where a set before the fix showed a display one double off,
    the float32 on the other side is taken, the exception;
  - on no value does what a set holds fail to show the display with nothing on the other side to
    take (`UNHELD` 0 then, `FELL` 0 in issue #16's count).

  These are counted from `to_preset`'s own results in the revision after PR 14's fifth review,
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/verification/direct-count.txt`,
  run on arm64, macOS 26.6.2 (25G83), with `main` at commit `558b85b` and this branch's work tree
  on `d21f160`, each file read printed by blob. The shipped method is called on every float32
  normalized value of `volume`, the branch read from what it returns, and every count split value
  by value at a held preset of 2 ** -43. No value above 2 ** -43 leaves the curve's float32. The fourth review's
  `verification/sweep.txt` gave the same three counts, but as a numpy reproduction's.

  The code holds the rule in `to_preset` itself: what a set of the curve's float32 holds, with
  the exception tried only where that is not the float32 and does not show the display. The sixth
  review's
  `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/floor-pass.txt`
  calls `e852aac`'s shipped methods, which these counts describe, and the restructured ones,
  each imported from its own tree, on every float32 normalized
  value of `volume` below 2 ** -54 and at the envelope group's 143 held powers of two, and
  finds no `to_preset` or `to_normalized` changed; no other value can differ, by reading.

  What a set holds comes first, so where both it and the float32 on the other side show the
  display, it is taken (`test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`, at issue
  #13's value). The exception asks `NormalizedScale.holds` of the float32 on the other side. A
  float32 past an end the scale does not hold can show the display and still be one no normalized
  value in [0, 1] lands on, so it is refused and the display takes what a set holds, the float32
  below the end: `test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken`, on a
  constructed scale whose maximum is unheld. An end is not always held.

  **`holds` answers False for a value outside what the scale's ends land on,** `to_preset(0.0)`
  and `to_preset(1.0)`, before it lands the value. That covers an infinity, a NaN and a finite
  value too large for its quotient to be a float32, each of which raised a built-in
  (`test_a_scale_holds_no_value_that_is_not_finite`,
  `test_a_scale_holds_nothing_outside_what_its_ends_land_on`), so the exception never raises.
  - The check is against what the ends land on, never the bounds. From -16777216 to
    1.0000001192092896 the span rounds up and 1 lands on 2, past the maximum, which the scale
    holds (`test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum`). On all
    903 committed records 0 lands on the minimum and 1 on the maximum.
  - It rests on the scale's value rising with the normalized value
    (`test_a_scale_s_value_rises_with_the_normalized_value`). No committed scale runs the other
    way, and `holds` answers as it did before the check on every committed record: 13,397
    presets at the pinned values and 798,179 at the indexed whole numbers, their halves and
    past each end (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/verification/holds-check.txt`).
  - `holds` does not test the landing's normalized value again, as it did before the check.
    Within what the ends land on, a preset the landing reaches is reached from [0, 1]:
    `_landing` keeps its step there, and the float32 nearest the quotient is there by
    rounding, since what 1 lands on is at most `span * 2 ** -24` past `minimum + span`
    (`test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval`; the argument is
    Decision 10 of that revision's `shape.md`, and the test put back is M3, an equivalent, in
    its `verification/mutation.txt`).
  - The scale's own `to_normalized` and `to_preset` still raise a built-in on a value outside
    what the scale can take, finite or not: issue #18.

  `to_normalized` of a display is `scale.to_normalized(to_preset(display))`, the scale's own
  normalized value for the preset `to_preset` gives, by definition. It lands that preset a
  second time, so it costs about 27 µs a call on `volume` against `main`'s 8, measured on an
  Apple M4 Pro, arm64, 14 cores, under macOS 26.6.2 (25G83) with Python 3.12.16
  (`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/cost.txt`);
  no fast path is kept for it.

  The fourth review's `verification/plugin-probe.txt` shows a load of the curve's float32 held by
  Vital at that same value. The rule has no tie to break. It replaced the neighbour nearer the
  curve's inverse, whose exact ties only a sort's order decided.

  **An arbitrary display.** One no held preset shows exactly takes what a set of its float32
  holds, a held preset that shows another display: `beats_per_minute` at 216.85141355537831 takes
  3.6141905784606934, shown as 216.8514347076416. Before issue #16 the rule had a third branch
  there, which kept the curve's float32, one the scale need not hold, so a model that stored it
  disagreed with what Vital held after a set. The sweep and the direct count reach only displays
  some held preset shows, so an arbitrary display is held by tests and by a sample:
  - `test_an_arbitrary_display_takes_what_a_set_of_it_holds`, at the two `tempo_displays` of
    `tests/data/pinned-values.txt`, on `beats_per_minute`'s scale and curve, built in the test
    module as `_TEMPO`. It reverses `test_an_arbitrary_display_keeps_the_curve_s_float32`, issue
    #16's characterization, on purpose.
  - `test_any_display_in_range_maps_to_a_preset_a_set_of_it_holds`, on every hand-built record,
    and `test_every_committed_record_maps_any_display_to_a_preset_a_set_of_it_holds`: the
    normalized value is in [0, 1], the forward scale lands it on `to_preset`'s value, and that
    value is what the test works out a set holds, or the float32 on the other side where that
    shows the display and what the set holds does not. The helper checks the exception both
    ways: where the map takes what a set holds and that does not show the display, the other
    side must not be one the rule would take. A draw over a parameter's bounds does not reach
    a display a held preset shows, so the two properties pass a `to_preset` without its
    exception; the pinned displays hold it, through the same helper, in
    `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds` (M5 in the
    `verification/mutation.txt` of the revision after the review of patchbay-vital's PR 19).
  - A sample, never a count, since a group's displays are doubles and cannot be enumerated:
    200,000 displays a continuous group, uniform over its bounds (`numpy.random.default_rng(16)`),
    11,000,000 over 55 groups, each through `main`'s shipped methods and the spec's. 2,041,885
    give another preset than `main`'s, on 31 groups. On every one `main`'s preset was not held,
    the new one is, and the normalized value a set sends is the same. Of 20,000 over `volume`'s
    range (seed 8), 1,108 change, the ones that took the third branch
    (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/verification/arbitrary-displays.txt`).
  - At `volume`'s floor the doubles can be enumerated, so they are counted: of the 23,726,567
    from -80 to the display at 2 ** -43, 344,580 give another preset than `main`'s. `main`'s
    showed the display and was not held; the new one is held and shows a display one double away.
  - Vital 1.6.4 holds the map's preset after a set of 200 seeded arbitrary displays on each of
    the 46 linear-scale groups, 9,200 sets, and held `main`'s value on none of the 2,085 that
    changed (that spec's `verification/plugin-probe.txt`).

  Which held preset an arbitrary display should take, Vital's rounding as here or the nearer held
  neighbour, is issue #8's finding 1, still open.

  **An indexed scale** goes through the same set path: its display goes to the nearest whole
  number, a half away from zero, as the plugin rounds, and the answer is what a set of that whole
  number holds. On every whole number of every one of the map's 351 indexed records that is the
  whole number itself, as on `main`: 398,563 calls, counted in full, over 21 distinct scales
  holding 371,476 whole numbers (that spec's `verification/indexed-count.txt`). On a scale wider
  than its float32s, which the map has none of, it is the nearest whole number the scale holds,
  not always the one asked for: on a constructed scale from -1 to 2 ** 24 the bound's display
  takes 16777215 (`test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds`).

  An indexed scale takes the exception too, but only where the float32 on the other side is
  itself a whole number: from 2 ** 23 up, where float32s are 1 apart. The map's widest indexed
  scale ends at 362,879, so no value of the map does. The branch is held by a test on a made-up
  record, an indexed scale from -2 ** 24 to 2 ** 24 under a linear curve of multiply 3 and
  offset 2 ** 54, where the held 8388610 comes back only through it
  (`test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display`; limited to
  linear scales, `to_preset` gives 8388612 there, MI1 in that revision's
  `verification/mutation.txt`).

  **The exception, in plain words.** `_assert_comes_back` runs every check exactly first, on every
  value. Only where the check that the display's preset is the held one fails does it ask
  `_unnamed_by_its_display`, and the value then passes only if that holds: the curve's own
  float32 for the display is not the held preset, so the display does not name it, and the
  display's preset is what a set of that float32 holds. The test works that value out from
  primitives (`_what_a_set_holds`: `curve.to_preset`, the float32 nearest the exact quotient,
  worked out with `Fraction`, the forward `scale.to_preset` at it and at the float32 either side,
  and `next_float32`), never from `MappedParameter.to_preset` or `to_normalized`, the scale's
  `to_normalized`, `holds` or `_landing`, so a wrong rule or a wrong landing in the map cannot
  agree with itself. Before issue #16 the helper called the scale's `to_normalized`, and a
  `_landing` that kept a missed step passed the property; it now fails it by name (issue #16's
  `verification/mutation.txt`).
  - It is asked on 570,997,534 values, all of `volume`'s, every one below 2 ** -54 at a held
    preset at or below 2 ** -43, and holds on each. There the display's preset is another held
    one that shows the display, and the display cannot say which of them was held. Counted with
    the shipped methods and the test module's own predicate, value by value, in
    `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/floor-pass.txt`,
    which also finds no value at or above 2 ** -54 asking it. The fourth review's reproduction,
    `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/verification/sweep.txt`,
    gave the same total and no value of the other 68 groups asking it.
  - The float32 on the other side, which `to_preset` takes as its exception, is not
    excused: that count finds it on no value, so a record that needed it would fail the
    property. The test module's hand-built records are not counted.
  - `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds` offers it what it must
    refuse: at `_SHARED`, a `volume` value in binade -80, a held float32 three steps away that
    shows the display, the held float32 on the other side, and, at that float32's own display,
    which names it, the preset `_SHARED` held. Each refusal is held by a mutant (MA, MB and MP2
    to MP4 in the sixth review's `verification/mutation.txt`).
  - It replaced `_shares_its_display`, which asked whether the float32 next to the held preset
    toward the display's preset shows the display. On a monotone curve that holds wherever the
    display's preset shows it, the property's first assertion, so it bounded nothing (the sixth
    review's finding 1).

  **The pinned values.** The values that found each defect are written once, in
  `tests/data/pinned-values.txt`, each with its set and its name, and both test modules read it
  through `pytestconfig.rootpath` (`vital/measures.md`). They were the property's `@example`s;
  a decorator runs at import, before pytest's root is known, so
  `test_every_pinned_value_comes_back_on_every_record` runs them through `_assert_comes_back` on
  every hand-built record instead, and fails the regression only they reach whatever Hypothesis
  draws (MC in the sixth review's `verification/mutation.txt`).

  Verified against `MappedParameter.to_preset` and `to_normalized`,
  `NormalizedScale.to_normalized`, `NormalizedScale.holds`, `_assert_comes_back`,
  `_unnamed_by_its_display`, `_what_a_set_holds` and
  `test_a_value_the_parameter_holds_comes_back_exactly`,
  `test_every_committed_record_comes_back_exactly`,
  `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`,
  `test_every_pinned_value_comes_back_on_every_record`, `tests/data/pinned-values.txt`,
  `test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset`,
  `test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`,
  `test_else_a_display_takes_the_float32_on_the_other_side`,
  `test_an_arbitrary_display_takes_what_a_set_of_it_holds`,
  `test_any_display_in_range_maps_to_a_preset_a_set_of_it_holds`,
  `test_every_committed_record_maps_any_display_to_a_preset_a_set_of_it_holds`,
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds`,
  `test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds`,
  `test_a_scale_holds_no_value_that_is_not_finite`,
  `test_a_scale_holds_nothing_outside_what_its_ends_land_on`,
  `test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum`,
  `test_a_scale_s_value_rises_with_the_normalized_value`,
  `test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval`,
  `test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display`,
  `test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step`,
  `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`,
  `test_an_arbitrary_display_set_through_the_host_holds_the_map_s_preset`),
  `verification/census-run.txt`, the `verification/direct-count.txt`,
  `verification/indexed-count.txt`, `verification/arbitrary-displays.txt`,
  `verification/plugin-probe.txt` and `verification/mutation.txt` of issue #16's spec
  (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`), and the
  `verification/sweep.txt`, `verification/plugin-probe.txt` and `verification/mutation.txt` of the
  revision after PR 14's fourth review, and the `verification/floor-pass.txt`,
  `verification/mutation.txt` and `verification/cost.txt` of the sixth. The defects were first
  found by the
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
  first. All 14 matched their groups, each table whole with its closing line, the run time
  stripped (the fifth review's `verification/duplicates.txt`), so a later count leaves them out.

  **The 69 groups.** The count covers all 69 of the map's groups, 1,065,353,217 values each. For
  the `linear`, `quadratic`, `quartic` and `square_root` curves, 60 groups, it reproduces the map's
  arithmetic exactly in numpy. For the 9 `exponential` and `exponential_inverted` groups it calls
  the platform's own `pow` and `log2` value by value, as `DisplayCurve` does. That count is true of
  the machine it ran on, macOS 26.6.2 on arm64, whose libSystem 1351 holds the libm, and of
  another machine only as far as its libm gives the same values.
  Issue #16's spec ran it again with the rule as it now reads: each of the 69 groups' tables
  equals the fourth review's, and no value takes what a set holds where that does not show the
  display (its `verification/sweep.txt`, a reproduction's, checked on 200,010 values a group).

  **The check before counting.** Each group's reproduction is first checked against the shipped
  scalar methods on 200,010 values. The check covers every value it counts, the branch each value
  takes, and the tests' own excuse as it then read, `_shares_its_display`. A value it cannot
  certify exact goes to an
  exact scalar computation instead. The check is a sample: of `volume`'s 200,010 values, 2,989
  take the first branch and 69 the second (the fifth review's
  `verification/arbitrary-displays.txt`). So a count the reproduction gives is called the
  reproduction's, with this size beside it.

  **An exception** consulted only where its claim fails is counted by the failures it leaves,
  each split by the value it allowed. A value it allows that the count never finds is not
  allowed (the sixth review's second candidate). It is tested by what it refuses, never by
  what it passes: a predicate the property's own assertions imply, as `_shares_its_display`'s
  was, bounds nothing, however its count reads.

  **A rule's branches are each counted.** A branch no counted value reaches is either removed or
  held by a unit test, and the standard says which. `to_preset`'s third branch was held by a test
  until issue #16 removed it; what an arbitrary display takes now is held by the tests and the
  sample above.

  **A claim over values that cannot be enumerated is sampled and called a sample,** with its
  size, its generator and its seed beside it, and never called a count. A display is a double,
  so a group's arbitrary displays are sampled; where a range's doubles can be enumerated, as
  `volume`'s 23,726,567 at its floor, they are counted, and the transcript labels each part.

  **A fix is counted against the old code itself: the old tree's shipped methods and the new
  tree's, each imported from its own tree and called value by value.** A count a reproduction's
  own definition forces to 0 is not evidence, in any form: by a copied guard, as issue #15's spec
  counted `CHANGEDx` and `NCHANGEDx`, or by building the new result from the old one wherever the
  old one lands, as the fourth review's sweep did. Both pairs were 0 by construction and are
  retired.

  The revision after PR 14's fifth review counted directly (`verification/direct-count.txt`),
  over every float32 normalized value of `volume` and of `env_1_delay`, which stands for the 12
  envelope records by their one group key:
  - on `volume` the display's preset differs from `main`'s on 16,069,858 values, all at or below
    2 ** -43, and the normalized value a set sends on 308,386 of them;
  - on `env_1_delay` the normalized value differs at 126 held powers of two, and no display's
    preset differs;
  - nothing else differs on either record;
  - a control with two branches swapped moves the counts, so they are read from the result.

  Issue #16's spec counted the same way
  (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/verification/direct-count.txt`),
  `main` at `f533b1b` against its work tree, on arm64, macOS 26.6.2 (25G83). A display a held
  preset shows is where that change is meant to move nothing, so any difference stops the run:
  - on `volume`, all five calls give `main`'s value on every one of the 1,065,353,217 values,
    with 15,761,472 taking what a set holds and 308,386 the exception, as before;
  - on `env_1_delay`, the display, its preset and its normalized value are `main`'s on every
    value;
  - a control with the exception removed moves 99,796 values of binade -56.

  **A count calls only what can differ, and shows which.** Both trees' `parameters.py` and
  `float32.py` are parsed, each function's statements compared with its docstring dropped, and
  each call the count makes followed to every function it can reach. A call that reaches only
  statements the old tree has cannot differ and need not be called in both trees. In issue #16's
  count 46 of 48 functions and module values were `main`'s, and only `to_preset` and
  `to_normalized` of a display reached the other two, so the envelope record was counted on
  those. A method is never ruled out by an earlier count of another tree.

  **A change inside one branch is recounted where that branch runs.** The revision after the
  review of patchbay-vital's PR 19 changed `NormalizedScale.holds` alone, which `to_preset`
  calls only from its exception.
  - Parsing both trees showed every other function's statements the same as in the tree issue
    #16's count ran on, 47 of 48.
  - That count's classes then say where the exception is taken: the 308,386 OTHER values of
    `volume`, in binades -58 to -56, with none entering it and falling through.
  - Those three binades were recounted against `main`, 25,165,824 values, with no difference and
    the same 308,386 (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/verification/direct-count.txt`).

  An earlier count's classes say where a branch runs only for a tree whose statements up to
  that branch are shown to be the ones it counted.

  **A count's cost is timed as the count will run,** every pool at its full size at once. Issue
  #16's timing ran 4 processes and estimated 4.25 hours for `volume`; the count ran 13, on 10
  performance cores and 4 efficiency ones, and took 5.25. A stop on a budget is checked against
  the clock while the run goes, not only against the estimate made before it.

  **The other 67 groups were not counted directly,** by the owner's decision at about 2.5 hours
  wall a group. Two things hold the claim there, that a quotient which lands is returned
  unchanged:
  - the unit test `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it`,
    which fails when the step is preferred (M15 in the fifth review's
    `verification/mutation.txt`);
  - the fourth review's sweep, a reproduction's, with its check against the shipped methods on
    200,010 values a group.

  Verified against the `verification/sweep.txt`, both its sections, and the
  `verification/sweep-afterwards.txt` of the revision after PR 14's fourth review, the
  `verification/direct-count.txt`, `verification/duplicates.txt`,
  `verification/arbitrary-displays.txt` and `verification/mutation.txt` of the revision after its
  fifth review, `tests/data/pinned-values.txt`, every value of which
  `test_every_pinned_value_comes_back_on_every_record` runs through the property's own assertions,
  issue #13's among them, and the `@example`s
  `test_a_value_the_parameter_holds_comes_back_exactly` keeps: 0.0, 1.0 and 5.2383727406426375e-33.

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
