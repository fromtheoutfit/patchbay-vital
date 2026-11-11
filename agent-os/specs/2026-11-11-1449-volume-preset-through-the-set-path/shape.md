# Issue #13: volume's preset through the set's path — Shaping Notes

Shaped 2026-11-11 in plan mode with this repository's customized `/agent-os:shape-spec`. Before
anything was changed the findings below were measured and presented. The owner answered four
questions on the decision and four of the command's own.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #13, https://github.com/fromtheoutfit/patchbay-vital/issues/13, "The parameter map:
volume's display does not come back through the normalized path below 2 ** -43 (Hypothesis,
normalized 5.857149595214349e-20)". `test_a_value_the_parameter_holds_comes_back_exactly[volume]`
fails at that normalized value, at the second assertion of `_assert_comes_back`
(`tests/unit/test_parameters.py:221`). Its scope: decide which is wrong, the map at the volume
curve's inverse near its -80 dB offset or the property at the test's second assertion below
2 ** -43, fix that one, and pin the value with `@example(normalized=5.857149595214349e-20)` so the
gate holds it on every run. Branch
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`
from `558b85b` (`main`). CHANGELOG entry, gate green, `verification/gate-run.txt`. No gate file
changes; neither of issue #8's questions decided; no stage, commit, push or pull request by an
agent.

## Shaping answers

- **The fix:** the property, with three additions in the owner's words: "Below the floor, nothing
  now holds the display coming back through the path a set takes, and on 308,386 values
  (exponents -58..-56) it does not. Hold that as what the map does today: one characterization
  test beside test_where_volume_s_offset_absorbs_a_preset, naming one such value and asserting the
  display comes back one double ulp off, its docstring saying this is the behaviour issue #8
  decides and that a fix there changes this test on purpose. shape.md says what line 221 no longer
  holds below the floor and that this test is what marks it." `@example` pins the issue's value and
  one value from the 308,386. Issue #8 is revised in place (below).
- **Vital's own measure:** an integration test and a probe transcript. "The test is a measure in
  the terms of agent-os/standards/vital/measures.md and skips by name where the map was measured on
  another machine, as its neighbours do. The transcript records the machine and Vital's version
  and prints its tree before the run."
- **The docstrings:** corrected, and "check the same two claims wherever else they are written:
  README.md, CHANGELOG.md's entry for the map, and agent-os/standards/vital/parameter-map.md. A
  sentence there that says 'held' or 'nearest' is corrected against the shipped code, the standard
  in the retrospective as its own change set with its index.yml entry kept in step. shape.md lists
  each sentence changed, old beside new."
- **Issue #8:** "Not a comment: revise issue #8's body in place with a 'Revised 2026-11-11'
  paragraph, no attribution. Probe 4's 'exact on every value a parameter holds, every curve' is
  corrected where it stands, finding 3 of 'From core's review of PR 19' gains the counts and
  Vital's own measure (the plugin holds the normalized path's value, never to_preset's), and the
  restricted to_preset fix is recorded there as a candidate with what it would decide. Cite this
  spec's verification/ files by path and branch. Leave the rest of the body, and its footer if one
  is there, as they are."
- **Step 1, scope:** issue #13 as answered. **Step 2, visuals:** none. **Step 3, references:** those
  studied, in `references.md`. **Step 4, product context:** `agent-os/product/mission.md`, the map
  "so a value means the same thing on either side"; the change says where it does and where not.
- **Step 5, standards:** the core five, and `base/testing/tests`, `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/standards-index`, `base/process/ownership`,
  `vital/parameter-map`, `vital/measures`, `vital/preset-tests` and `vital/plugin-state`. Snapshot in
  `standards.md`, base at `e31f7db`.

## What was checked while shaping

Notation, after the property's own names: `r` the normalized value, `P0 = scale.to_preset(r)` the
preset the parameter holds, `D0 = to_display(P0)` its display, `P1 = to_preset(D0)` the preset the
display maps to, `N` the scale's `to_normalized`, `P2 = scale.to_preset(N(P1))` the preset a set of
`D0` holds (`MappedParameter.to_normalized(D0)` is `N(P1)`).

- **The replay** of the issue, on this tree before anything: `AssertionError` at
  `tests/unit/test_parameters.py:221`, exit 1.
- **What `_assert_comes_back` claims.** A1 (line 220) `to_display(P1) == D0`, the display back
  through display → preset. A2 (line 221) `scale.to_preset(N(P1)) == P1`, the preset the display
  maps to back through the normalized path: that `P1` is one the scale holds, `to_preset`'s
  docstring's "one the parameter holds". A3 (line 223) `P1 == P0`, asserted only above `_ABSORBED`.
- **What core's promise needs.** Core's `Instrument.get` at the pinned `dd2bcad`: "After `set`,
  that is a value the parameter holds, not necessarily the one given: the value given itself at a
  bound, and at any value `get` has returned for it that `set` takes." Core speaks of displays
  only. Under issue #8's Decision 1 the loaded preset model is the source of truth and `get` reads
  it, so get after set needs A1. Through the plugin it is SET, `to_display(P2) == D0`, the display
  back through display → preset → normalized → preset → display. A2 is the model and the plugin
  agreeing on the preset, which Decision 1 leaves to the renderer ("its off-grid snapping").
- **The falsifying value.** `P0 = 4.3339629239370393e-16`, `D0 = -79.99999997918182`,
  `P1 = 4.3339650415194074e-16`, `N(P1) = 5.857152180153763e-20`, `P2 = 4.3339647768216114e-16`.
  Near it the scale holds ...45121e-16, ...47768e-16 and ...53062e-16 and steps over `P1`, one
  float32 between two it holds. `to_display(P2) == D0`: the display comes back through the set's
  path; the preset does not.
- **How far it reaches, every value counted** (`verification/sweep.txt`). Every float32 normalized
  value in [0, 1], 1,065,353,217 of them, on each record with a curve offset, by a numpy check that
  reproduces the map's arithmetic exactly and agreed with the scalar methods on 200,006 values per
  record while shaping and 200,007 in the recorded run, 0 mismatches and no sum it could not
  certify exact. `volume`: A1 fails on none; HELD,
  `scale.to_preset(N(P0)) == P0`, on none; A2 on 16,069,858, in exponents -95 to -56; A3 on
  572,449,131; SET on 308,386, in exponents -58, -57 and -56 (31,879, 176,711 and 99,796), each
  display one double ulp, 1.42e-14 dB, from the one set. Every failure is at or below the floor:
  binade -56, which the floor's normalized value `1.53642479121845e-17` splits, has 7,490,097
  values above it and none fails anything. At or below the floor lie 596,489,679 values, 56% of
  the float32 values in [0, 1]. The other five records with an offset, the three filter cutoffs
  (one scale and curve) and the two delay tempos (one), fail nothing.
- **So swapping line 221 for core's set path would not make the property true:** SET fails on
  308,386 values.
- **Probe 4's 1,104,000** (the host spec's `verification/probes.txt`): 2000 `rng.random` doubles per
  continuous parameter, uniform in value, each made a preset value `x`; it checked
  `f32(inverse(display(x))) == x`, the display → preset round trip (A3's), and `fused(N(x)) == x`,
  the scale's inverse (HELD), and never the preset a display maps to through the normalized path
  (A2) or the display through the set's path (SET). The floor holds 56% of the float32 normalized
  values and about 1.5e-17 of [0, 1)'s measure, so 2000 uniform draws reach it with a probability
  near 3e-14. Decision 6's correction swept presets, every 53rd float32 below 2 ** -43, for A1 and
  A3, never the normalized path. Hypothesis's 32-bit floats spread over exponents and drew it.
- **What Vital holds** (`verification/plugin-probe.txt`). Vital 1.6.4 here, set through `VitalHost`
  with `to_normalized(D0)`: it holds `P2` exactly, never `P1`, at the falsifying value (its display
  `D0`) and at four of the 308,386 (their displays one ulp off). A preset load holding `P1` is held
  as `P2`, after a set and on a fresh instance alike. The map's arithmetic is the plugin's; below
  the floor `to_preset`'s value is one the plugin is never seen to hold.
- **Arbitrary displays** (`verification/sweep.txt`): 20,000 uniform displays per record; `to_preset`'s
  value is not the one a set holds on 5.7% of `volume`'s and 7.7% of `env_1_attack`'s, none of
  `filter_1_cutoff`'s or `osc_1_level`'s. That is issue #8's finding 1 from core's review of PR 19,
  and `to_preset`'s "one the parameter holds" was false there before issue #13.

## Decisions

1. **Issue #13 is the spec's scope** (https://github.com/fromtheoutfit/patchbay-vital/issues/13):
   decide which is wrong, the map or the property, fix that one, pin the value with `@example`.
2. **The property is wrong, at line 221 below the floor.** It asks there for what core does not
   need (core needs A1 under #8's Decision 1) and for what the map cannot give without choosing
   which preset a set stores where two presets share a display, the question the host spec's
   Decision 6 left to #8 ("what the instrument stores where two presets share a display is Spec
   B's") and #8's finding 3 of core's review asks. The map's arithmetic is Vital's: the plugin holds
   `P2` exactly where the map computes it.
3. **The smallest change that makes it true:** line 221 moves under the `_ABSORBED` guard beside
   A3, and HELD, `record.scale.to_preset(record.scale.to_normalized(preset)) == preset`, is asserted
   on every value. Measured on every float32 normalized value of every offset record: A1 and HELD
   fail on none anywhere, A2 and A3 on none above the floor.
   - **What line 221 no longer holds below the floor:** that the preset a display maps to is one
     the scale holds, which is false on 16,069,858 normalized values; and with it, that a set of
     that display holds that preset.
   - **What holds instead:** A1 on every value, the display a set is given showing again from the
     preset `to_preset` gives, which is core's get after set under Decision 1; HELD on every value,
     the normalized path inverting the scale on the preset the parameter holds, which line 221
     checked there wherever `P1 == P0`; and above the floor line 221 itself.
   - **What nothing in the property holds below the floor**, the display through the set's path,
     false on 308,386 values, is marked by the characterization test
     `test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off`, at the smallest of them.
     It asserts the map's behaviour today, one double ulp above; issue #8 decides it, and a fix
     there changes that test on purpose.
4. **Two examples pinned:** the issue's `5.857149595214349e-20` and `_ONE_ULP_OFF`,
   `3.4694490199051456e-18`, the smallest of the 308,386, both float32 values (`base/testing/tests.md`:
   a known counterexample pinned so every run tries it).
5. **The map fix is not taken; it goes to #8 as a candidate:** `to_preset` taking, where its
   float32 is not one the scale holds, the held neighbour that shows the given display. Then A2
   and SET come back on every value `get` returns and no arbitrary display changes, since no held
   preset shows one; it decides what a set stores where two presets share a display (finding 3's
   question), not whether `set` picks the nearer neighbour for an arbitrary value (finding 1's).
6. **Vital's own measure is an integration test**, a measure in `vital/measures.md`'s terms:
   `_BELOW_VOLUME_S_FLOOR`, each value with the double ulps the held display is off, its comment
   naming the probe; `_held_after_a_set` and `_double_ulps` written once, used by the test and
   imported by the probe. It takes the module's `host`, so it skips by name without Vital or where
   the map was measured on another machine.
7. **The docstrings say what `to_preset` returns:** the float32 nearest the curve's inverse, which
   need not be one the scale holds; a set holds the scale's value at `to_normalized`'s result. No
   behaviour changes. The same claims are checked wherever written; each sentence changed is
   listed under Docs.
8. **Issue #8's body is revised in place**, "Revised 2026-11-11", no attribution, its other text
   and footer unchanged.

## Context

- **Visuals:** none.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`: the map between parameters and preset keys
  "so a value means the same thing on either side". The display does, on every value; the preset
  does above `volume`'s floor and not below it, which the tests and the docs now say.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the property's strategy, the counterexamples pinned with `@example`.
- `base/process/verification-gate` — the gate, unchanged; its transcript.
- `base/process/standards-retrospective` — the last step; a base change proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entry kept in step.
- `base/process/ownership` — no stage, commit, push or pull request; an issue edited without
  attribution.
- `vital/parameter-map` — the claims the property holds, corrected in the retrospective.
- `vital/measures` — the integration test as a measure, its constant's comment naming its probe.
- `vital/preset-tests` — the hosted test skipping by name.
- `vital/plugin-state` — the module's one loaded Vital; a load of an off-grid value.

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script
under `scripts/` as git lists them, with no tracked file a `.gitignore` ignores;
`uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set and
`uv.lock`'s pins;
and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the commit in
`agent-os/standards/base/.version` — and the three judgment steps are recorded, in this order:
Docs, Version, then the standards retrospective below.

**Results (2026-11-11):** exit 0 on branch
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`
at `558b85b` with the change uncommitted, `verification/gate-run.txt`, run after the
retrospective's edits: steps 1 to 6 passed, 492 tests, the integration tests among them with
Vital installed, none skipped. A run before the retrospective's edits passed the same way. No gate
file changed, so no negative test was rerun. The issue's replay exits 0 on the change; both pinned
values fail the old `_assert_comes_back` at line 221 (checked with the old file stashed).

**Docs (step 7):** every file changed, and every standard and document naming them, checked
against the shipped code. Each sentence changed, old beside new:

- `src/patchbay_vital/parameters.py`, the module docstring's curve paragraph.
  Old: "A value a parameter holds goes to the display and back exactly; an arbitrary display value
  comes back as the nearest one the parameter holds, an indexed scale's a whole number (the host
  spec's `verification/probes.txt`, probe 4), and a choice or a boolean takes a whole index and
  nothing else, core's rule for them."
  New: "A value a parameter holds goes to the display and back to that display exactly, and to the
  same preset value but where a curve's offset absorbs it: below `volume`'s 2 ** -43 neighbouring
  presets share a display. A displayed value goes to the float32 nearest the curve's inverse, an
  indexed scale's a whole number, which need not be one the scale holds, below that floor or for an
  arbitrary display; a set then holds the scale's value at `to_normalized`'s result, as Vital does
  (the host spec's `verification/probes.txt`, probe 4; issue #13's spec, `verification/sweep.txt`
  and `verification/plugin-probe.txt`). A choice or a boolean takes a whole index and nothing else,
  core's rule for them."
- `MappedParameter.to_preset`'s summary. Old: "Return the preset value nearest a displayed value,
  one the parameter holds." New: "Return the float32 preset value nearest a display's curve
  inverse, within the scale." Its body gains: "It need not be one the scale holds, below
  `volume`'s 2 ** -43, where presets share a display, or for an arbitrary display value; where it is
  not, a set of `to_normalized`'s result holds a neighbour, as Vital does (issue #13)."
- `tests/unit/test_parameters.py`, `_ABSORBED`'s docstring: "(the spec's shape.md, Decision 6)"
  becomes "(the host spec's shape.md, Decision 6)", and it gains: "There the preset a display maps
  to may be a float32 the scale does not hold, and a set holds a neighbour: on 16,069,858 of the
  float32 normalized values, none above the floor (issue #13's spec, `verification/sweep.txt`)."
- `test_a_value_the_parameter_holds_comes_back_exactly`'s docstring. Old: "The preset value comes
  back too, but where a curve's offset absorbs it (`_ABSORBED`); the normalized value need not, many
  landing on one float32 preset value." New: "The preset value the parameter holds comes back
  through the normalized path, every time. The preset value the display maps to is that one, and
  comes back through the normalized path, but where a curve's offset absorbs it (`_ABSORBED`): there
  it may be a float32 the scale does not hold, and a set holds a neighbour (issue #13). The
  normalized value need not come back, many landing on one float32 preset value."
- `_assert_comes_back`'s docstring. Old: "Assert a normalized value's display, and its preset value
  but where absorbed, come back." New: "Assert a value's display and held preset come back, the
  display's preset but where absorbed.", with a paragraph saying which path each comes back
  through.
- `agent-os/standards/vital/parameter-map.md`, `measures.md`, `plugin-state.md` and two
  descriptions in `agent-os/standards/index.yml`: the retrospective's, old beside new below.
- New text, nothing replaced: `_ONE_ULP_OFF`'s docstring, the two `@example` comments,
  `test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off`, and in
  `tests/integration/test_vital_plugin.py` the `_BELOW_VOLUME_S_FLOOR` comment, `_held_after_a_set`,
  `_double_ulps` and `test_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`.
- Checked and true, unchanged: `README.md`, which says "held" or "nearest" of no value, and whose
  "exact conversions between the host's normalized value, the preset's value and the value Vital
  displays" is true, each conversion computing the plugin's own value exactly
  (`verification/plugin-probe.txt`); `CHANGELOG.md`'s entries for the map (`### Added`, "its
  normalized ↔ preset scale (linear or indexed, exact float32 with a fused multiply-add) and its
  preset ↔ display curve"; the PR 9 revision's "`MappedParameter.to_preset` rounds to a whole
  number on an indexed scale and refuses a non-whole value for a choice or a boolean"), neither
  saying "held" or "nearest"; `DisplayCurve.to_preset` ("the float32 preset value nearest the one a
  displayed value comes from"); `NormalizedScale.to_normalized` ("For a value the scale holds,
  `to_preset` of the result is that value again", HELD failing on no value); the two test modules'
  headers; `test_a_value_set_through_the_host_is_the_one_the_state_holds`, whose displays are
  above the floor; `CLAUDE.md`, which says nothing of the map.

**Version (step 8):** a `### Fixed` section at the end of `[Unreleased]` in `CHANGELOG.md`, this
spec's entry its one item, with the tests, the measure and the docstrings beneath it. The version
stays 0.0.1.

**Issue #8 (Decision 8):** its body revised in place on 2026-11-11, no attribution, the rest of its
text and its footer unchanged: a "Revised 2026-11-11 (after issue #13)" paragraph after the second
revision paragraph; probe 4's "on every value a parameter holds it is exact (1,104,000 of
1,104,000, every curve)" corrected where it stands with the counts and why the draws missed the
floor; "The plugin changes what it is given" gains the load observation and what it bears on
(`load_patch`, the loaded `VitalPreset` as the source of truth), as the owner asked when approving
the `plugin-state.md` edit; finding 3 of "From core's review of PR 19" gains the counts, Vital's
measure and the candidate with what it would decide. Each cites this spec's `verification/` files
by path and branch.

## Standards Retrospective

Step 9, from the shipped diff. The four questions:

1. **A pattern no standard covers:** three. A claim about every value a scale holds counted over
   every float32 normalized value, exponent by exponent (`verification/sweep.txt`); a
   characterization test of a behaviour an open issue decides
   (`test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off`); a measure of what Vital
   holds, compared exactly, its helpers written once and imported by the probe
   (`test_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`, `plugin-probe.txt`).
2. **A standard wrong or stale:** `vital/parameter-map.md`'s "A displayed value comes back exactly;
   a preset value does too" bullet and its "arbitrary display value comes back as the nearest one
   the parameter holds", proved stale by the sweep; `vital/plugin-state.md`'s off-grid snap, which
   the probe's fresh load shows is not the whole story; `vital/measures.md`, whose scope was audio
   alone.
3. **A deliberate deviation:** none.
4. **A pointer moved:** none; the new tests are added to the standards' "Verified against" lists.

The project edits, each approved by the owner on 2026-11-11 with AskUserQuestion, two with
conditions applied (`measures.md` rewritten as plain sentences and verified again; `plugin-state.md`
stated as an observation with its two cases, the machine and Vital's version), and listed apart
from the feature's files so they can be committed apart:

- `agent-os/standards/vital/parameter-map.md` — the header's evidence gains issue #13's spec. The
  bullet, old: "**A displayed value comes back exactly; a preset value does too, but where a curve's
  offset absorbs it.** `volume`'s presets at or below 2 ** -43 display within 3.4e-7 dB of −80 dB
  and share a display; the sweep found no other. An arbitrary display value comes back as the
  nearest one the parameter holds, which on an indexed scale is a whole number, rounded a half away
  from zero as the plugin rounds." New: "**A displayed value comes back exactly, and the preset a
  parameter holds through the normalized path; the preset a display maps to does too, but where a
  curve's offset absorbs it.**" with the floor's counts (16,069,858 unheld, 308,386 one double ulp
  off, which issue #8 decides and a characterization test holds), no other offset record failing
  anything, and an arbitrary display going to "the float32 nearest the curve's inverse … which need
  not be one the scale holds (5.7% of `volume`'s, issue #8's finding 1)"; its "Verified against"
  gains both new tests, `sweep.txt` and `plugin-probe.txt`. A new bullet: "**A claim about every
  value a scale holds is counted over every float32 normalized value, exponent by exponent, never
  drawn uniformly.**" Verified against `tests/unit/test_parameters.py` (`_assert_comes_back`, the
  property's `@example`s, the characterization test), `tests/integration/test_vital_plugin.py`,
  `src/patchbay_vital/parameters.py` (`MappedParameter.to_preset`), `verification/sweep.txt` and
  `verification/plugin-probe.txt`.
- `agent-os/standards/vital/measures.md` — old: "How a test asserts what Vital rendered." New: "How
  a test asserts what Vital rendered or holds.", the header's evidence gaining `plugin-probe.txt`.
  A new bullet: "**What Vital holds after a set is compared exactly with the value the map computes.
  How far that value's display lands from the display set is a measure, a count the probe made.**"
  Verified against `test_below_volume_s_floor_a_set_holds_the_normalized_path_s_value` (held equal
  to `scale.to_preset(to_normalized(display))`, not `to_preset(display)`, `_double_ulps` the
  constant's count), `_BELOW_VOLUME_S_FLOOR` (0 and 1, its comment naming the probe) and
  `plugin-probe.txt` (0 at the issue's value, 1 at four of the 308,386, through the test's own
  helpers).
- `agent-os/standards/vital/plugin-state.md` — after "a value off the host's grid snaps once after
  the host set that parameter." it gains: "A load with no set before it was also seen to move an
  off-grid value, once: on Vital 1.6.4 through pedalboard 0.9.26 on arm64, a fresh instance loading
  `volume` at 4.3339650415194074e-16, below its floor, held 4.3339647768216114e-16, the normalized
  grid's neighbour, while `chorus_feedback`'s off-grid 0.4000000059604645 in the same load was held
  as given; a set of `volume` and then the same load held the neighbour too. One load does not say
  why one value moved and the other did not." Its "Verified against" gains `plugin-probe.txt`.
  Verified against `plugin-probe.txt`'s two load cases and its header (machine, Vital's version,
  pedalboard's).
- `agent-os/standards/index.yml`, in this repository's `vital:` section; the `base:` section is
  untouched, `scripts/sync-standards.sh --check` passing. `parameter-map`, old: "a display coming
  back exactly as the nearest value held and a preset but where an offset absorbs it"; new: "a
  display and the held preset coming back exactly and a display's preset but where an offset
  absorbs it, a set there holding the normalized path's value, a claim about every value counted
  over every float32 by exponent". `measures` gains: "; what Vital holds after a set is compared
  exactly with the map's value, and how far its display lands from the display set is a count the
  probe made". `plugin-state`'s "re-quantizing what it loads" still covers its edit.

Proposals sent upstream: fromtheoutfit/patchbay-standards#39; declined: `base/testing/tests.md` (count every float32)

### Standards retrospective (proposed, base)

- `base/testing/tests.md`, "Inside a test" — a behaviour an open issue decides is held by a
  characterization test whose docstring says it is the code's behaviour today, names the issue
  that decides it, and says a fix there changes the test on purpose; it asserts the value exactly,
  at a named, documented value the property also pins. Verified against
  `tests/unit/test_parameters.py` (`test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off`,
  `_ONE_ULP_OFF`, `_assert_comes_back`) and this `shape.md`, Decision 3. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#39.
- `base/testing/tests.md` — a claim about every float32 a function takes is counted over every
  one, exponent by exponent, where 2 ** 32 values allow, its arithmetic checked value for value
  against the implementation first, since draws uniform in value miss the small exponents where
  most float32 values lie. Verified against `verification/sweep.txt` and
  `tests/unit/test_parameters.py`. Proposed, not applied; declined by owner, 2026-11-11: held as a
  project standard in vital/parameter-map.md until a second package needs it.
