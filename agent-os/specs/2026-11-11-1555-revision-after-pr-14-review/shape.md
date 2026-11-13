# Revision after the Review of PR 14 — Shaping Notes

Shaped 2026-11-11 in plan mode with this repository's customized `/agent-os:shape-spec`. Before any
question each finding was checked against the code at the PR head, and the claims it rests on were
measured. The owner answered four questions on the findings, then three more (the named values,
the earlier text, steps 2 to 5), then one on where the shared reader lives; while implementing,
one more on the defect this revision's count found (Decision 8).

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The review of PR 14 at `0568b32`, the comment on https://github.com/fromtheoutfit/patchbay-vital/pull/14
(https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6806758858, 2026-11-11 20:49Z,
"Review"): sixteen findings against issue #13's spec,
`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`, none a crash, most claims
that say more than the tests hold. In the owner's words, "Let's address the issues in the review
on PR 14". On the same branch, so PR 14 carries it. CHANGELOG entry, gate green,
`verification/gate-run.txt`. No behaviour changes and no gate file changes. No stage, commit, push
or pull request edit by an agent.

## Shaping answers

- **Finding 12, the map fix**, in the owner's words: "Neither as offered: keep it out of this PR,
  but do not leave it to #8. Answer finding 12 in shape.md by agreeing the map is also wrong below
  the floor, and file its own patchbay-vital issue, no attribution, for the spec that runs before
  #8:
  - Scope: where to_preset's float32 is not one the scale holds, it returns the held neighbour
    that shows the given display. Evidence required: the every-float32 sweep rerun showing A2 and
    the set path hold on every value and that no arbitrary display's result changes; the
    integration measure against Vital; the characterization test
    test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off replaced on purpose by the
    property holding everywhere.
  - What it leaves to #8, said in the issue: whether VitalInstrument.set keeps the stored value
    when the display given is the one it already shows, and the nearer neighbour for arbitrary
    displays (finding 1).
  - Revise #8 in place: its finding 3 points at the new issue for the set path's display, #8
    depends on it, and the candidate fix recorded there moves to the new issue.

  This revision changes no behaviour."
- **Findings 2 to 4, the set path:** "The bound is stated as what it is: exact above the floor,
  within one neighbouring double at or below it, and the property's docstring says the second half
  is what the new map issue removes. The three pinned values each name their direction. The new
  sweep prints its tree first and shows the bound holding on every float32 normalized value, with
  the count of values at each distance (0, +1, -1) so 308,386 and its split are on record there."
- **Finding 10, the counting rule:** "The rule in vital/parameter-map.md then says exactly what was
  done: counted over every float32 normalized value for the 60 groups whose curves the sweep
  reproduces bit for bit, and for the six records with a curve offset; the 9 exponential groups
  rest on the property's exponent-spread draws and pinned examples, because the platform's
  pow/log2 are not reproduced by the sweep's arithmetic. The sweep checks its arithmetic against
  the shipped implementation before counting, per group, and its transcript shows that check.
  Record the exponential groups' full count as open in shape.md, with what it would take (the
  platform libm, call by call, hours of compute), for the owner to schedule or decline; do not
  start it here."
- **Finding 8, the load observation:** an integration test. "The test records the machine's and
  Vital's version the same way its neighbours do and skips by name on another machine.
  plugin-state.md's bullet cites the test as what holds it, and the probe transcript as where it
  was first seen."
- **Finding 14, the named values:** one recorded file. "The file lives with the other test data,
  is read through one helper both modules import, and _double_ulps is removed in favour of _ulps.
  Its header says what produced the values (the sweep, by spec folder) and that the map issue
  filed from finding 12 is expected to change the three non-zero rows; the base standard on
  measured data recording its machine applies only if a row was measured on the plugin, and the
  header says which rows were."
- **The shared reader**, asked again because `tests/` has no `__init__.py` (`base/testing/tests`)
  and pytest's import path is per directory, so `tests/integration` cannot import a plain module
  from `tests/unit`: a fixture in `tests/conftest.py`, with two things to show. "The harness rerun
  is this branch's harness (main's, since #11's revision is not merged), one run, its transcript
  whole: case q must still do what its header says with a tests/conftest.py present beside the one
  it writes. shape.md notes for the #11 revision, which reruns its own changed harness after this
  merges, that tests/conftest.py now exists, so that rerun is the first to exercise its case q
  against it."
- **Findings 1, 9 and 16, the earlier text:** issue #13's folder stays as written, "with two
  changes to the rest: This spec's shape.md lists each corrected sentence with its file and line,
  old beside new, under a heading a reader of the earlier folder would look for, as the revision
  after PR 12's review did. No PR body draft: the owner writes PR bodies. List instead, in the
  final report, which sentences of the PR body and of commit 88d438d's message are now untrue and
  what is true, and leave both as they are. Issue #8's body is revised in place in the same edit as
  finding 12's, as proposed."
- **Steps 2 to 5:** confirmed as listed. No visuals. References in `references.md`. Product: the
  mission unchanged. Standards: the core five, and `base/testing/tests`,
  `base/process/verification-gate`, `base/process/standards-retrospective`,
  `base/process/standards-index`, `base/process/ownership`, `vital/parameter-map`,
  `vital/measures`, `vital/preset-tests` and `vital/plugin-state`. Snapshot in `standards.md`,
  base at `e31f7db`.

## What was checked while shaping

Notation, issue #13's: `r` the normalized value, `P0 = scale.to_preset(r)`, `D0 = to_display(P0)`,
`P1 = to_preset(D0)`, `N` the scale's `to_normalized`, `P2 = scale.to_preset(N(P1))` the preset a
set of `D0` holds. A1 `to_display(P1) == D0`; HELD `scale.to_preset(N(P0)) == P0`; A2
`scale.to_preset(N(P1)) == P1`; A3 `P1 == P0`; SET `to_display(P2) == D0`.

- **Finding 1, by running:** at r = 1.4144055385838898e-18, below the floor, `P1 == P2` and `P1` is
  one the scale holds, so a set holds `to_preset`'s value exactly. Of the 596,489,679 normalized
  values at or below the floor, A2 fails on 16,069,858; on the other 580,419,821 `P1` is held and
  a set holds it. "Never `to_preset`'s" was true only of the values the probe chose, each one where
  `P1` is not held.
- **Finding 3's bound, by counting while shaping** (issue #13's sweep arithmetic over exponents
  −58 to −56, where every SET failure lies): all 308,386 are exactly one double ulp off, 154,100
  above the display set and 154,286 below. This folder's `verification/sweep.txt` records it over
  every value.
- **Finding 4, by reading:** once `back == preset`, `record.to_normalized(display)` is
  `scale.to_normalized(preset)`, so line 241 re-ran line 238.
- **Finding 7, by running:** at 1.53642479121845e-17, `N(2 ** -43)`, `P1` is not held and the
  set's display lands one ulp below; a normalized 1e-14 gives preset 7.4e-11, far above the floor.
- **Finding 9, by running:** `volume`'s `parameter.minimum`, −80 dB, maps to preset 0, at the
  floor; `P1 == P0 == 0`, held.
- **Finding 10, by grouping the committed map** by (parameter kind, scale kind, minimum and
  maximum, curve kind, multiply and offset, parameter minimum and maximum): 69 groups, 54 linear,
  5 exponential, 4 exponential_inverted, 3 quadratic, 2 quartic, 1 square_root. Including the
  parameter's bounds in the key splits none (69 either way). Issue #13's sweep counted 3 of them.
- **Finding 14, by reading:** `tests/unit/builders.py` is imported by bare name, which works
  because pytest puts each test file's own directory on `sys.path`; `tests/integration` is never
  given `tests/unit`. `pyproject.toml`'s `"tests/**"` per-file ignores (S101, INP001) cover a
  `tests/conftest.py`, so it needs no gate file.
- **Finding 8, by reading:** the integration module's first test, the census's, sets every
  parameter, `chorus_feedback` included, so any later test's load follows sets of it.
- **Findings 5, 6, 11, 13, 15 and 16, by reading:** each holds as written.

## Decisions

1. **The map is also wrong at or below the floor (finding 12), and its fix is its own issue,**
   filed as #15 for the spec that runs before #8, which takes the map's other inverse too
   (Decision 8) (the scope, evidence and what it leaves to #8 in
   the owner's words above; its body below). Issue #8 is revised in place: its finding 3 points at
   #15 for the set path's display, it depends on #15, and the candidate fix moves to #15. This
   revision changes no behaviour.
2. **The set path's bound is stated as what it is (findings 2 to 4).** `_assert_comes_back` drops
   the line that restated HELD. Above the floor the set path is exact, which follows from A3 and
   HELD; at or below it the property asserts that a set's display is the display or a neighbouring
   double, the half #15 removes. The characterization test holds four rows, each with its
   direction: issue #13's value (0), the smallest of the 308,386 (+1), 1.439742266862027e-17 (−1)
   and the floor's own normalized value 1.53642479121845e-17 (−1).
3. **The count says what it covered (findings 10 and 16).** The sweep counts the 60 groups whose
   curves it reproduces bit for bit and each of the six offset records directly, each checked
   against the shipped scalar methods on 200,007 values before it is counted. The 9 exponential
   groups rest on the property's draws and pinned examples. Their full count is open (below).
4. **A load's off-grid move is held by an integration test (finding 8)**, recording the plugin as
   the census test does, skipping by name on another machine.
5. **The named values are one recorded file, `tests/data/volume-floor.txt`, read through one
   fixture in `tests/conftest.py` (finding 14).** `_double_ulps` goes; `_ulps` counts float32 or
   double steps. The negative harness is rerun once, whole.
6. **Issue #13's folder stays as written (findings 1, 9, 16);** its sentences are corrected under
   "Corrections to issue #13's spec" below. Issue #8 is revised in the same edit as Decision 1's.
   The PR body and `88d438d`'s message are the owner's: the final report lists what in them is now
   untrue.
8. **The map's other inverse misses a held power of two, and #15 takes it too (found by this
   revision's count, `verification/sweep-first.txt`).** On the 12 records of `env_1_delay`'s
   group, `env_N_delay` and `env_N_hold` (scale [0, 1.4142135381698608], quartic), HELD fails on
   126 normalized values a record, one in each binade from −126 to −1: the held preset is a power
   of two, 2 ** -125 to 1, and `NormalizedScale.to_normalized` returns the float32 nearest
   `preset / span`, which multiplies back short of the power, where the float32 spacing halves, so
   its fused multiply-add lands one float32 below. Vital, measured while implementing: a set of
   display 1.0 s on `env_1_delay` or `env_3_hold` through the map holds 0.9999999403953552, and
   the float32 above the map's normalized value holds 1.0; likewise at 0.5 and 2 ** -20. The
   property asserted HELD on every value of every record, so it was false there, the same latent
   flake as issue #13's. Presented to the owner with AskUserQuestion; in the owner's words: "The
   map issue being filed takes both inverse defects, and says so in its title: to_preset below
   volume's floor (finding 12), as already drafted. to_normalized at held presets that are exact
   powers of two on the 12 env_N_delay/env_N_hold records (126 values a record): it returns the
   float32 nearest preset/span, whose fma32 lands one float32 below, so a set of 1.0 s holds
   0.99999994 on Vital, measured, where the float32 above gives exactly 1.0. Candidate fix
   recorded there: the nearest unless its fma32 misses the preset, then the neighbour that lands
   on it. Evidence required: the sweep with HELD 0 everywhere, an @example, and an integration
   test of Vital holding 1.0. In this revision, no behaviour change: HELD in _assert_comes_back
   excludes exactly those presets by a stated predicate (not by record name alone), a
   characterization row pins one of them in tests/data with its direction, to_normalized's
   docstring is corrected, and shape.md says what HELD no longer holds and that the issue's fix
   changes the test on purpose. The sweep transcript records the 12 records and the count."
   - **The predicate**, `_lands_below_its_power_of_two(preset, held)`: the preset is a positive
     power of two and the normalized path's preset is the float32 just below it. HELD is asserted
     as `held == preset or` that, on every value of every record, so a HELD failure of any other
     shape still fails. `verification/sweep.txt` counts, beside every HELD failure, those the
     predicate excuses (HELD2), and they are the same on every count.
   - **What HELD no longer holds:** that the preset a parameter holds comes back through the
     normalized path on every value. It does but at the predicate's values: on the 12 records,
     126 powers of two each, 1,512 (record, value) pairs, where the preset comes back one float32
     below. There the set path's display is not exact either.
   - **What holds it instead:** `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`
     at the row of `tests/data/power-of-two-presets.txt`, `env_1_delay` at preset 1.0, landing −1
     float32 step, and the float32 above the map's normalized value landing on the power. #15's
     fix is expected to change the row to 0 and drop the predicate from `_assert_comes_back`, on
     purpose.
   - `NormalizedScale.to_normalized`'s docstring said "For a value the scale holds, `to_preset` of
     the result is that value again"; it now says where it is not, and names #15.
9. **Decided in shaping, within those answers:** the integration test asserts that Vital does not
   hold the curve's own float32, `record.curve.to_preset(display)`, which #15's fix leaves as it is,
   so the test's code survives the fix and only the file's rows change (finding 5); it loads
   `initial` before each set, as the probe does (finding 6); the host test calls
   `_held_after_a_set` (finding 11); the probe prints the blob hash of each file it imports and the
   source of each helper it calls (finding 13); the `plugin-state` index entry is the
   retrospective's (finding 15).

## The 16 findings

| # | Finding | Outcome |
|---|---|---|
| 1 | "never `to_preset`'s" is false for most values below the floor | Fixed: scoped to where `to_preset`'s float32 is not one the scale holds, in the test, the CHANGELOG, #8 and `measures.md`; issue #13's folder corrected here |
| 2 | The CHANGELOG overstates the characterization test | Fixed: four rows with their directions, and the property's bound on every value; the CHANGELOG says so (Decision 2) |
| 3 | Nothing bounds the set path below the floor | Fixed: within one neighbouring double at or below the floor, counted on every float32 (Decision 2) |
| 4 | The line moved under the guard can't fail | Fixed: dropped; HELD replaced line 221 (Corrections) |
| 5 | The integration test pins today's map without saying so | Fixed: asserted against the curve's own float32; the docstring and the file's header say #15 changes the rows (Decision 9) |
| 6 | The test doesn't run the sequence the probe measured | Fixed: `initial` loaded before each set; the probe reruns that sequence |
| 7 | "below 2 ** -43" should read "at or below"; units mixed | Fixed |
| 8 | No shipped test holds the load-snap observation | Fixed: an integration test (Decision 4) |
| 9 | The Docs step gives a wrong reason | Corrected here (Corrections) |
| 10 | The new counting rule isn't met by the change that adds it | Fixed: 60 groups and the six offset records counted, the rule scoped, the rest open (Decision 3) |
| 11 | The set path is written twice | Fixed |
| 12 | Altitude: the fix weakens the property, not the map | Agreed; the map fix filed as #15, before #8 (Decision 1) |
| 13 | The probe ran uncommitted helpers | Fixed: blob hashes and helper source in the transcript |
| 14 | Duplicated helper and constants | Fixed: one file, one fixture, `_ulps` (Decision 5) |
| 15 | `index.yml` is out of step | Fixed in the retrospective |
| 16 | The sweep is described as covering more than it did | Fixed: all six counted directly, the parameter's bounds in the key, the check "on 200,007 values"; corrected here, in #8 and in `parameter-map.md` |

Found by this revision's own count, not by the review: `to_normalized` at a held power of two
on the 12 envelope delay and hold records (Decision 8), excused by a stated predicate here and
fixed by #15.

## Corrections to issue #13's spec

`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/` stays its record, as the
revisions after the reviews of PR 9 and PR 12 left theirs. These of its sentences are corrected
here, not there:

- **`shape.md:86-89`** (finding 16). Old: "Every float32 normalized value in [0, 1], 1,065,353,217
  of them, on each record with a curve offset, by a numpy check that reproduces the map's
  arithmetic exactly and agreed with the scalar methods on 200,006 values per record while shaping
  and 200,007 in the recorded run". New: on one record of each of the three groups with a curve
  offset, `volume`, `filter_1_cutoff` and `delay_tempo`, the other three sharing every constant,
  agreeing with the scalar methods on those 200,007 values, not on every value. This folder's
  `verification/sweep.txt` counts all six directly, and 60 of the map's 69 groups.
- **`shape.md:92-93`** (found while checking finding 3). Old: "SET on 308,386 … each display one
  double ulp, 1.42e-14 dB, from the one set." True, but the sweep it cites counted only that each
  differs and printed the distance of two. New: 154,100 one double ulp above the display set and
  154,286 below, none further, counted in this folder's `verification/sweep.txt`.
- **`shape.md:96-97`** (finding 16). Old: "The other five records with an offset … fail nothing."
  New: the two counted fail nothing, and the three sharing their constants were not counted; this
  folder's sweep counts them and they fail nothing.
- **`shape.md:108-112`** (finding 1). Old: "it holds `P2` exactly, never `P1` … below the floor
  `to_preset`'s value is one the plugin is never seen to hold." New: at the five values measured,
  each one where `P1` is not one the scale holds, it holds `P2`, not `P1`. Where `P1` is held, on
  580,419,821 of the 596,489,679 values at or below the floor, `P2` is `P1` and a set holds
  `to_preset`'s value exactly (r = 1.4144055385838898e-18).
- **Decision 3, `shape.md:135-138`** (finding 4). Old: "What holds instead: … and above the floor
  line 221 itself." New: above the floor line 221 restated HELD, `N(P1)` being `N(P0)` once
  `P1 == P0`, and could not fail when line 220 and A3 passed. HELD replaced line 221 entirely; this
  revision drops the restated line.
- **Decision 3, `shape.md:139-143`** (finding 2). Old: the set path's failure "is marked by the
  characterization test …, at the smallest of them." True of one value in one direction. New: the
  property bounds it on every value, and four rows hold both directions (Decision 2 here).
- **Decision 5, `shape.md:147-151`.** Old: "The map fix is not taken; it goes to #8 as a
  candidate". New: it is #15, for the spec before #8 (Decision 1 here).
- **Decision 6, `shape.md:152-156`** (findings 6, 13, 14). Old: "`_held_after_a_set` and
  `_double_ulps` written once, used by the test and imported by the probe." The test set both
  values back to back on one instance where the probe loaded `initial` before each; the probe
  imported them from an uncommitted test module; the values were literals in both test modules.
  New: the rows are `tests/data/volume-floor.txt`, read through `tests/conftest.py`; `_ulps` counts
  the steps; the test loads `initial` before each set; the probe prints the hashes of what it
  imports.
- **Docs, `shape.md:264-265`** (finding 9). Old: "`test_a_value_set_through_the_host_is_the_one_the_state_holds`,
  whose displays are above the floor". New: its displays are above the floor but `volume`'s
  minimum, −80 dB, which maps to preset 0, at the floor; its `held == record.to_preset(display)`
  passes there because preset 0 is one the scale holds. The verdict holds; the reason did not.
- **Standards Retrospective, `shape.md:346`** (finding 15). Old: "`plugin-state`'s "re-quantizing
  what it loads" still covers its edit." New: it did not; the phrase is the embedded sample's
  16-bit re-quantization. This folder's retrospective adds the load to the description.
- **The retrospective's `parameter-map.md` entry, `shape.md:315-317`** (findings 10 and 16): the
  counting rule and "checked value for value against the methods first" are corrected in this
  folder's retrospective, against `verification/sweep.txt` here.
- **`verification/sweep.txt` and `verification/plugin-probe.txt`** stay as run. This folder's
  transcripts of the same names supersede them: the sweep counts what that one did not, and the
  probe runs the tests' own sequence with the hashes of what it imports.

## Open

- **The 9 exponential groups' full count** (5 `exponential`, 4 `exponential_inverted`, 159
  records): their skew is the platform's `pow` or `log2`, which numpy's `exp2` and `log2` do not
  reproduce bit for bit, so the sweep's arithmetic cannot count them. Counting them would call the
  platform libm value by value, `math.pow` or `math.log2` on each of 1,065,353,217 normalized
  values a group, hours of compute across the 9 on this machine's 14 cores. Until then they rest on
  the property's exponent-spread draws and pinned examples. For the owner to schedule or decline;
  not started here. Decision 8's defect is one the count would look for there too: an
  exponential record's held power of two that the normalized path lands short of is not yet known
  to exist or not.

## For #11's revision

`tests/conftest.py` exists from this revision on, beside the ignored `tests/unit/conftest.py` the
gate's negative case q writes. This revision reran main's harness with it present
(`verification/gate-negative-tests.txt`); #11's revision, which reruns its own changed harness
after this merges, is the first to exercise its own case q against it.

## The map issue (Decisions 1 and 8)

Filed 2026-11-11 as https://github.com/fromtheoutfit/patchbay-vital/issues/15, no attribution,
after the second sweep had confirmed its counts. Title: "The parameter map's two inverses:
to_preset at or below volume's floor and to_normalized at a held power of two miss the preset a
set should hold". Its body, as filed:

````markdown
The parameter map's two inverses each miss a preset a set should hold. The review of PR 14 found the first (finding 12, https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6806758858): issue #13 corrected the property at or below `volume`'s floor, and the map is wrong there too. The revision after that review found the second, counting every float32 normalized value. This spec runs before #8, which depends on it. Until it lands, the property excuses both by a stated rule, and rows under `tests/data/` hold where today's map lands.

## 1. `to_preset` at or below `volume`'s floor

At or below the floor, preset 2 ** -43 (normalized 1.53642479121845e-17), `MappedParameter.to_preset` returns, for a display the parameter shows, the float32 nearest the curve's inverse. On 16,069,858 of the float32 normalized values that float32 is not one the scale holds. A set of that display through the normalized path then holds a neighbour, and so does Vital. On 308,386 of them, in exponents -58 to -56, the neighbour shows a display one double ulp from the one set: 154,100 above it and 154,286 below, none further. Under #8's Decision 1 the loaded `VitalPreset` model stores `to_preset`'s value, so the model would hold a preset Vital is not seen to hold.

- **Scope:** where `to_preset`'s float32 is not one the scale holds, it returns the held neighbour that shows the given display.
- **Evidence required:**
  - The every-float32 sweep rerun, as in the revision after PR 14's review. It must show A2 (the preset a display maps to, back through the normalized path) and the set path (the display back through display → preset → normalized → preset → display) holding on every float32 normalized value of every counted group, and no arbitrary display's result changing.
  - The integration measure against Vital, `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`, rerun with Vital installed, with its probe.
  - The characterization test `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded` replaced on purpose by the property holding everywhere: `_assert_comes_back` asserting the set path exactly on every value, with the three non-zero rows of `tests/data/volume-floor.txt` changed or the file gone.

## 2. `to_normalized` at a held power of two

`NormalizedScale.to_normalized` returns the float32 nearest `(preset - minimum) / span`. On the 12 `env_N_delay` and `env_N_hold` records (scale [0, 1.4142135381698608], quartic curve), at the held presets that are exact powers of two, 126 a record from 2 ** -125 to 1, that float32 multiplies back short of the power, where the float32 spacing halves, and its fused multiply-add lands one float32 below. So a set of 1.0 s holds 0.9999999403953552 on Vital, measured, where the float32 above the map's normalized value gives exactly 1.0. It breaks `to_normalized`'s own promise, that a value the scale holds comes back, and HELD, which the property asserts on every value: the same latent gate flake as issue #13.

- **Scope:** `to_normalized` returns the nearest float32 unless its fused multiply-add misses the preset, then the neighbour that lands on it. This is the candidate recorded in the revision after PR 14's review.
- **Evidence required:**
  - The sweep with HELD failing on no value anywhere.
  - An `@example` pinning one such value.
  - An integration test of Vital holding 1.0 after a set of 1.0 s.
  - `_lands_below_its_power_of_two` dropped from `_assert_comes_back` and the row of `tests/data/power-of-two-presets.txt` changed to 0 or the file gone, with `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`, on purpose.

## Left to #8

- Whether `VitalInstrument.set` keeps the stored value when the display given is the one it already shows (#8's finding 3 of core's review of PR 19).
- The nearer neighbour for an arbitrary display (#8's finding 1 of that review).

## Evidence so far

On branch `refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`:

- Issue #13's spec, `agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`: `verification/sweep.txt`, the first count at the floor, and `verification/plugin-probe.txt`, the first measure of Vital there.
- The revision after PR 14's review, `agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`:
  - `verification/sweep-first.txt`, which found the second defect;
  - `verification/sweep.txt`, every float32 normalized value of the 60 groups whose curves it reproduces bit for bit, of each of the six records with a curve offset and of each of the 12 envelope records, with the set path's distance counted and HELD's failures split by the excusing rule;
  - `verification/plugin-probe.txt`, Vital holding the normalized path's value at each row after a set and after a load.

The 9 exponential groups (159 records) were not counted, since their skew is the platform's `pow` or `log2`, so the second defect's reach there is not known.

## Rules

Shaped in plan mode with `/agent-os:shape-spec`. The Step 5a standards apply, `base/testing/tests.md` and `vital/parameter-map.md` especially. CHANGELOG; gate green. No commit, PR or push by an agent.
````

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/mission.md`, the map "so a value means the same thing on
  either side": the display does on every value; the preset does above `volume`'s floor and,
  at or below it, wherever `to_preset`'s float32 is one the scale holds; #15 makes it every value.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/testing/tests` — the property, its pinned counterexample, the one `conftest.py` in the
  directory holding every test that takes its fixture, function-scoped.
- `base/process/verification-gate` — the gate unchanged; its transcript; the negative harness
  rerun once.
- `base/process/standards-retrospective` — the last step; a base change proposed, never edited.
- `base/process/standards-index` — `index.yml`'s `vital:` entries kept in step (finding 15).
- `base/process/ownership` — no stage, commit, push or pull request edit; issues filed and edited
  without attribution.
- `vital/parameter-map` — the claims the property holds and the counting rule, corrected in the
  retrospective.
- `vital/measures` — the integration test as a measure, exact against the map's value, its rows
  in one file.
- `vital/preset-tests` — the hosted tests skipping by name.
- `vital/plugin-state` — the module's one loaded Vital; the load of an off-grid value.

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
at `0568b32` with the change uncommitted, `verification/gate-run.txt`, run on the final tree after
the retrospective's edits: steps 1 to 6 passed, 494 tests (492 and the two new ones), the
integration tests among them with Vital installed, none skipped. A run before `README.md`'s
sentence and one docstring's rewrap passed the same way. No gate file changed.

- **Not run by the gate:**
  - **The sweep**, `verification/sweep.txt`, the second run, and `verification/sweep-first.txt`,
    the first. Every float32 normalized value of 60 groups, the six offset records and the 12
    envelope records: 74 counts, each matching the shipped scalar methods on 200,007 values with no
    fallback. A1 fails on none. HELD fails on 1,512, the predicate holding on the same 1,512, and
    the property as stated breaks on none (`bound!: 0`). The set path at or below volume's floor
    gives 154,100 +1 and 154,286 −1, none further.
  - **The probe**, `verification/plugin-probe.txt`, Vital 1.6.4 through pedalboard 0.9.26 on arm64.
    Each row of both files is as recorded. The load observation holds after every history. The
    blob hashes of the four files it reads are those of the tree the gate ran, which no edit
    touched after it.
  - **The mutation**, `verification/mutation.txt`. An unheld preset in (1e-13, 2 ** -43] was sent
    eight float32 steps up. This revision's tests fail at the bound (`tests/unit/test_parameters.py:243`,
    through the rows' test) and PR 14's pass, exit 0. The property's draws did not reach it; the
    rows did.
  - **The negative harness:** this branch's harness, main's (`scripts/gate-negative-tests.sh`
    `578dd16`, HEAD's blob), one run of every test but j, `verification/gate-negative-tests.txt`,
    whole: 141 runs, 0 unexpected. This revision adds files under `tests/`, which every case
    copies, so the harness's own header asks for the rerun. Case q copied the tracked
    `tests/conftest.py` (`A  tests/conftest.py`) beside the ignored `tests/unit/conftest.py` it
    writes and did what its header says: each ignored file failed step 5 by name before pytest ran,
    exit 1; pytest given `--ignore` for the conftest passed with "494 passed, 1 deselected"; the
    root's ignored conftest failed step 5 by name. Case j, the CI replay, the harness's own header
    keeping its transcript apart, `verification/ci-negative-test.txt`: 3 runs, 0 unexpected. The
    harness started before `README.md`'s sentence and a docstring's rewrap, neither read by any
    case's assertion.

**Docs (step 7):** every file changed, and every document and standard naming them, checked
against the shipped code. Each sentence changed, old beside new:

- `src/patchbay_vital/parameters.py`:
  - The module docstring: "below `volume`'s 2 ** -43" and "below that floor" become "at or below".
    The sources name the revision's verification files beside issue #13's. A sentence is added:
    "Issue #15 is to take, at or below the floor, the held neighbour that shows the display."
  - `NormalizedScale.to_normalized`. Old: "Return the normalized value the host sets for a preset
    value. For a value the scale holds, `to_preset` of the result is that value again: the float32
    nearest `(preset - minimum) / span` lands on it (probe 4, P3)." New: "Return the normalized
    value the host sets for a preset, the nearest float32 quotient. For a value the scale holds,
    `to_preset` of the result is that value again (probe 4, P3), but where the value is a power of
    two the nearest float32 multiplies back short of", followed by the 12 records, the 126 powers,
    Vital, the evidence, and #15.
  - `MappedParameter.to_preset`: "below" becomes "at or below", and it gains "and at or below the
    floor issue #15 is to return the held neighbour that shows the display."
- `tests/unit/test_parameters.py`:
  - `_ABSORBED`'s docstring: "under 2 ** -43" becomes "at or below 2 ** -43, the preset of
    normalized 1.53642479121845e-17". The count is cited to this revision's sweep.
  - The property's and `_assert_comes_back`'s docstrings say what HELD holds but at the predicate,
    and the set path's bound; #15 removes both exceptions.
  - New:
    - `_lands_below_its_power_of_two`;
    - `test_a_held_power_of_two_lands_as_recorded_through_the_normalized_path`;
    - the renamed `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded`, its
      docstring saying it holds today's map, which #15 changes.
  - Removed: `_ONE_ULP_OFF` and its `@example`.
- `tests/integration/test_vital_plugin.py`:
  - Removed: `_BELOW_VOLUME_S_FLOOR` and `_double_ulps`.
  - Changed: `_ulps` gains a docstring and a `dtype`.
  - The measure is renamed `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`.
    Its summary changes from "Below 2 ** -43 the plugin holds the scale's value at
    `to_normalized`'s, not `to_preset`'s." to "At or below the floor, Vital holds the normalized
    path's value, not an unheld float32." Its body is scoped to where `to_preset`'s float32 is not
    held, and names #15 and the shared file.
  - New: `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`.
  - The module's header is unchanged and true.
- `tests/conftest.py`, `tests/data/volume-floor.txt` and `tests/data/power-of-two-presets.txt`: new.
  `tests/unit/builders.py`'s "A plain module and not a conftest" still reads true. Its reasons are a
  property test's decorator and the `tests/unit/conftest.py` case q writes, and the new conftest is
  `tests/conftest.py`, taken by plain tests.
- `README.md`, the `tests/` paragraph. Old: "… `fma-vectors.txt` holds the plugin's own values that
  `float32.py` is held to." New: "… `fma-vectors.txt` holds the plugin's own values that
  `float32.py` is held to; `volume-floor.txt` and `power-of-two-presets.txt` hold where the map
  lands today at values issue #15 is to change, read through the fixtures of `conftest.py`, the one
  module both trees share." The rest of `README.md` checked and true. `attack.to_normalized(0.5)` is
  `env_1_attack`'s, a group the sweep counts with no HELD failure.
- Checked and true, unchanged:
  - `CLAUDE.md`, whose gate description ("no root `conftest.py`") is of the root, not `tests/`;
  - `agent-os/product/`;
  - the `vital/parameter-map.md` "Two conversions" bullet, which is of normalized to preset.
- The standards that name a renamed test or a removed constant, `vital/parameter-map.md` and
  `vital/measures.md`, are the retrospective's, below. After it, `git grep` finds none of the old
  names outside the spec folders.

**Version (step 8):** `CHANGELOG.md`'s `[Unreleased]` `### Fixed` entry for issue #13 is corrected
in place, since it describes what lands. It changes as follows:

- "below `volume`'s floor" becomes "at or below".
- Both spec folders are named.
- "The property was wrong, not the map" becomes "The property was wrong there, and so is the map,
  whose fix is issue #15", and the second defect, also #15's, is added.
- `_ONE_ULP_OFF`, the 308,386 claim and "never `to_preset`'s" are replaced by the rows, the bound,
  the renamed tests and the load test.
- The docstrings' line gains `to_normalized`.

No behaviour changes; the version stays 0.0.1.

**Issue #8:** its body is revised in place on 2026-11-11 with no attribution; the rest of its text,
and the footer it already carried, are unchanged (`gh issue view 8` read before the edit, compared
with the body first read, and read back after it). The edits, old beside new:

- The "Revised 2026-11-11 (after issue #13)" paragraph is corrected where it stands:
  - "on every record with a curve offset" becomes "on one record of each of the three groups with a
    curve offset (corrected after PR 14's review; …)";
  - "No other record fails anything. Vital holds the normalized path's value, never `to_preset`'s"
    becomes "No other record counted fails anything. Vital holds the normalized path's value, which
    where `to_preset`'s float32 is not one the scale holds is not `to_preset`'s (corrected …)";
  - "until this spec decides it" becomes "until #15 decides it (…, where it said this spec)".
- A new "Revised 2026-11-11 (after PR 14's review)" paragraph:
  - the map is wrong too, its fix is #15, and #8 depends on it;
  - the candidate fix moves there;
  - finding 3 points at #15;
  - #15 also takes `to_normalized` at a held power of two;
  - the recounted numbers, with the evidence by path and branch.
- "## Depends on" gains #15.
- "The plugin changes what it is given" gains the measure again and the test that holds it.
- Finding 3: "never `to_preset`'s" becomes "not `to_preset`'s unheld float32", and the paragraph
  ends "The set path's display there is #15's."
- Its candidate paragraph is replaced by one saying it moved to #15 and what #15 leaves to #8.

## Standards Retrospective

Step 9, from the shipped diff. The four questions:

1. **A pattern no standard covers:** three.
   - Values two test directories share, kept in one recorded file read through `tests/conftest.py`
     (`recorded_rows`, the two row files).
   - A property's known exception excused by a stated value predicate, its set counted equal to the
     failures (`_lands_below_its_power_of_two`, `verification/sweep.txt`).
   - A characterization test's values held as rows that every test holding the behaviour reads
     (`tests/data/volume-floor.txt` and its two readers).
2. **A standard wrong or stale:**
   - `vital/parameter-map.md`'s round-trip bullet: "below", the preset through the normalized path
     on every value, the one characterization value.
   - Its counting rule: "never drawn" without its scope, and "checked value for value".
   - `vital/measures.md`'s "is not `to_preset`'s", its constants and helpers, and "the test and the
     probe compute the same thing" when they ran different sequences.
   - `vital/plugin-state.md`'s load observation, held by no test (finding 8).
   - `index.yml`'s `plugin-state` entry (finding 15).
3. **A deliberate deviation:** none.
4. **A pointer moved:** the renamed tests and the removed constants, updated in every standard that
   names them.

The project edits, each approved by the owner on 2026-11-11 with AskUserQuestion, and listed apart
from the feature's files so they can be committed apart. In the owner's words, "Each standard is
its own change set with index.yml in step": each change set below is a standard and its own entry
of `index.yml`'s `vital:` section, the `base:` section untouched (`scripts/sync-standards.sh
--check` passing).

- **`agent-os/standards/vital/parameter-map.md` with `index.yml`'s `parameter-map` entry.**
  - The header's evidence gains this revision.
  - The round-trip bullet now says "and the preset a parameter holds through the normalized path but
    at a power of two the path lands short of; … and a set of the display shows it again exactly,
    but where a curve's offset absorbs it, where a set shows the display or a neighbouring double".
    It adds:
    - the power-of-two defect (12 records, 126 powers, Vital's 0.9999999403953552), excused by
      `_lands_below_its_power_of_two` and held by the row, until #15;
    - the floor's normalized value and the 154,100/154,286 split, none further;
    - the four rows in one file read through the conftest fixture, whose header says #15 changes
      them;
    - "issue #8 decides" becomes #15.

    Its "Verified against" names the new and renamed tests, both row files, `tests/conftest.py` and
    both folders' transcripts.
  - The counting rule: "never drawn uniformly" becomes "wherever the count reproduces the map's
    arithmetic bit for bit, and is never drawn uniformly". "checked value for value against the
    methods first" becomes "checked against the shipped scalar methods on 200,007 values of a group
    before it counts that group". It now gives the 60 groups and six offset records, and the 9
    exponential groups resting on the property's draws, their count open.
  - The entry: "a display and the held preset coming back exactly and a display's preset but where
    an offset absorbs it, a set there holding the normalized path's value, a claim about every value
    counted over every float32 by exponent" becomes "a display and the held preset coming back
    exactly, but a power of two the normalized path lands short of, and a display's preset and a
    set's display but where an offset absorbs it, a set there holding the normalized path's value
    within one neighbouring double, each exception held at rows a file records, a claim about every
    value counted over every float32 by exponent wherever the count reproduces the arithmetic".
  - Verified against:
    - `tests/unit/test_parameters.py` (`_assert_comes_back`, `_lands_below_its_power_of_two`, both
      characterization tests);
    - `tests/conftest.py` and both row files;
    - `src/patchbay_vital/parameters.py` (`to_normalized`, `to_preset`);
    - `verification/sweep.txt` (the 74 counts, HELD = HELD2, the split) and
      `verification/plugin-probe.txt`.
- **`agent-os/standards/vital/measures.md` with `index.yml`'s `measures` entry.**
  - The header's evidence gains this revision.
  - In the set bullet:
    - "and is not `to_preset`'s" becomes "and is not the curve's own float32
      (`record.curve.to_preset`) where the scale does not hold it, which a fix of `to_preset`
      leaves as it is";
    - "counted in double ulps … `_BELOW_VOLUME_S_FLOOR` … `_double_ulps`" becomes the rows' signed
      steps by `_ulps`, the one file read through `volume_floor` and `recorded_rows`, and the test
      and the probe running one sequence, the probe printing blobs and source.
  - The entry gains ", the test and the probe running one sequence over the rows of one file both
    test trees read".
  - Verified against `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`
    (`host.load_state(initial)` before each set, `record.curve.to_preset`, `_ulps` with direction),
    `tests/conftest.py`, `tests/data/volume-floor.txt` and `verification/plugin-probe.txt`'s
    header and section 1.
- **`agent-os/standards/vital/plugin-state.md` with `index.yml`'s `plugin-state` entry (finding
  15).**
  - The header's evidence gains issue #13's spec and this revision's `plugin-probe.txt`.
  - The load sentences are restated as an observation with its rows and histories, the machine and
    Vital's version, claiming no cause, as the owner conditioned: "A load with no set before it also
    moves `volume`'s value at or below its floor where that is a float32 the scale does not hold, to
    the normalized path's value, while `chorus_feedback`'s off-grid 0.4000000059604645 in the same
    load is held as given: on Vital 1.6.4 through pedalboard 0.9.26 on arm64, at each row of
    `tests/data/volume-floor.txt`, after every history the integration module can give the load (…).
    It is an observation: nothing measured says why one value moves and the other does not."
  - Its "Verified against" gains the new load test as what holds it, this revision's probe, and
    issue #13's as where it was first seen.
  - The entry: "the plugin upgrading, delaying and re-quantizing what it loads so its state is
    never read back as the preset" becomes "the plugin upgrading, delaying and re-quantizing what
    it loads and a load moving volume's unheld value at or below its floor while an off-grid
    chorus_feedback is kept, so its state is never read back as the preset".
  - Verified against
    `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given` and
    `verification/plugin-probe.txt`'s section 2 and header.

Proposals sent upstream: fromtheoutfit/patchbay-standards#40; #39, revised in place

### Standards retrospective (proposed, base)

Each presented to the owner on 2026-11-11 with AskUserQuestion and approved; in the owner's words,
"(a) and (c) go in one new patchbay-standards issue; (b) is revised into #39 in place with a
"Revised 2026-11-11" paragraph", and for (c) "word the second half so it does not require what
only some domains allow".

- (a) `base/testing/tests.md`, "Test files": values that two test directories both hold live in
  one recorded file under `tests/data/`, read through one function-scoped fixture in
  `tests/conftest.py`, since `tests/` is no package and a plain module of one test directory is
  not importable from another. Verified against `tests/conftest.py`, both row files, the tests that
  read them, `verification/plugin-probe.txt` and `verification/gate-negative-tests.txt`. Proposed,
  not applied; filed as fromtheoutfit/patchbay-standards#40.
- (b) `base/testing/tests.md`, #39's rule: the characterization test's values live in a recorded
  file that every test holding the behaviour reads, its header naming the issue expected to change
  the rows and which rows were measured on the plugin. Verified against `tests/data/volume-floor.txt`,
  `test_at_or_below_volume_s_floor_a_set_s_display_lands_as_recorded` and
  `test_at_or_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#39, revised in place.
- (c) `base/testing/tests.md`, "Inside a test": a property's known exception is excused by a
  stated predicate over values, never by a record's name, so any failure of another shape still
  fails. "Where the domain can be counted, a count shows the predicate's set equals the failures;
  where it cannot, the proposal says what stands in for the count." Verified against
  `_lands_below_its_power_of_two`, `_assert_comes_back`, `tests/data/power-of-two-presets.txt`
  and `verification/sweep.txt` (HELD 1,512, HELD2 1,512, `bound!` 0). Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#40.
