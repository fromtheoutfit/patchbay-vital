# Issue #13 — volume's preset through the normalized path below 2 ** -43

## Context

Issue #13 (open): `test_a_value_the_parameter_holds_comes_back_exactly[volume]` fails at
normalized `5.857149595214349e-20`, the second assertion of `_assert_comes_back`
(`tests/unit/test_parameters.py:221`); the gate can fail on it by chance, and #12's revision waits
on the fix. The issue is the spec's scope: decide which is wrong, the map or the property, fix that
one, pin the value with `@example`. Branch (already checked out, clean at `558b85b`):
`refactor/13-the-parameter-map-volumes-display-does-not-come-back-through-the-normalized-path-below-2--43-hypothesis-normalized-5857149595214349e-20`.
Replay on this tree before anything: `AssertionError` at line 221, exit 1.

Shaped in plan mode with `/agent-os:shape-spec`; the owner answered eight questions (below). No gate
file changes, nothing of #8's questions decided, no stage/commit/push/PR by the agent.

## Findings (measured while shaping; re-run into `verification/` in Task 2)

`P0 = scale.to_preset(r)` (held), `D0 = to_display(P0)`, `P1 = to_preset(D0)`,
`N = to_normalized`, `P2 = scale.to_preset(N(P1))` (what a set holds).

- A1 (line 220) `D(P1) == D0`; A2 (line 221) `S(N(P1)) == P1` — `to_preset`'s "one the parameter
  holds"; A3 (line 223) `P1 == P0`, above `_ABSORBED` only. Core's `Instrument.get` (`dd2bcad`)
  under #8's Decision 1 (get reads the model) needs A1; through the plugin it is SET
  `D(S(N(P1))) == D0`. Core never needs A2.
- Falsifying value: `P1=4.3339650415194074e-16` is a float32 the scale steps over; `P2=…47768e-16`;
  `D(P2) == D0` — the display comes back through the set's path, the preset does not.
- Every float32 normalized value (1,065,353,217), exact vectorised check (0 mismatches against the
  scalar methods on 200,006 per record): `volume` A1 0, HELD `S(N(P0)) == P0` 0, A2 16,069,858
  (exponents −95..−56), A3 572,449,131, **SET 308,386** (−58/−57/−56: 31,879/176,711/99,796), each
  one double ulp off; every failure at or below the floor (binade −56 split exactly: 7,490,097
  above, 0 failures). Cutoffs ×3 and tempos ×2, the other offset records: 0 failures of anything.
- Probe 4's 1,104,000: uniform `rng.random` draws, A3 and HELD only; the floor is 56% of float32
  normalized values but ~1.5e-17 of [0, 1)'s measure.
- Vital 1.6.4 here: after `set(to_normalized(D0))` it holds `P2` exactly, never `P1` (falsifying
  value: display D0; four SET failures: one ulp off); a load holding `P1` is held as `P2`, fresh
  instance too. Arbitrary displays: `to_preset`'s value is not the one a set holds on 5.7% of
  `volume`'s and 7.7% of `env_1_attack`'s (20,000 each) — #8's finding 1.
- **The property is wrong**: A2 below the floor asks what core does not need and what the map
  cannot give without choosing what a set stores where two presets share a display, which the host
  spec's Decision 6 left to #8. The map fix (to_preset takes the held neighbour that shows the
  given display) is recorded on #8 as a candidate, not taken.

## Task 1: Save spec documentation

`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`:
- `plan.md` (this plan); `shape.md` — Core Architecture, Scope, Shaping answers (the eight), What
  was checked while shaping (the findings above), Decisions (first: issue #13 is the scope; then
  the property is wrong and why; line 221 moved under the guard — what it no longer holds below the
  floor, what holds instead, and that the characterization test marks the 308,386; the map fix
  left to #8; docstrings corrected; #8 revised in place), Context, Standards Applied, Verification
  Gate, Standards Retrospective; `standards.md` — full text of the core five and `base/testing/tests`,
  `base/process/verification-gate`, `standards-retrospective`, `standards-index`, `ownership`,
  `vital/parameter-map`, `vital/measures`, `vital/preset-tests`, `vital/plugin-state` (base at
  `.version`'s commit); `references.md` — the files studied; no visuals.

## Task 2: The measures, into `verification/`

Each transcript opens with date, branch, `git rev-parse HEAD` and `git status --short`, then the
script, then its output. Scripts live inside the `.txt` (a `.py` there would be ruff's).
- `verification/sweep.txt`: the vectorised checker validated against the scalar methods; the
  per-exponent table of A1, A2, A3, SET, HELD for `volume`, `filter_1_cutoff` and `delay_tempo`
  over every float32 normalized value (noting the identical cutoff and tempo records); binade −56
  split by the floor; the smallest and largest SET failures; arbitrary displays on four records.
- `verification/plugin-probe.txt` (Task 4, after the test exists): `platform.machine()`, Vital's
  version (`host.version`), pedalboard's; the set at the falsifying value and the SET failures,
  through the integration test's own helpers; the load of `P1`, fresh instance and after a set.

## Task 3: The property, its examples and the characterization (`tests/unit/test_parameters.py`)

- `_assert_comes_back`: keep line 220 (A1); add `record.scale.to_preset(record.scale.to_normalized(preset)) == preset`
  unconditionally (HELD, 0 failures); move line 221 under the `_ABSORBED` guard beside A3. Docstring:
  the display and the held preset come back every time, the display's preset but where absorbed.
- `test_a_value_the_parameter_holds_comes_back_exactly`: `@example(normalized=5.857149595214349e-20)`
  (issue #13) and `@example(normalized=_ONE_ULP_OFF)`, each commented; docstring says below the
  floor the display's preset may be a float32 the scale does not hold, and a set holds a neighbour.
- `_ONE_ULP_OFF = 3.4694490199051456e-18` beside `_ABSORBED`, documented: the smallest of the
  308,386 (`verification/sweep.txt`). `_ABSORBED`'s docstring gains the issue-13 sentence.
- New `test_below_volume_s_floor_a_set_s_display_comes_back_one_ulp_off` beside
  `test_where_volume_s_offset_absorbs_a_preset`: at `_ONE_ULP_OFF`, `to_display(to_preset(display))
  == display` and `to_display(scale.to_preset(to_normalized(display))) == math.nextafter(display,
  math.inf)`. Docstring: this is the map's behaviour today, issue #8 decides it, and a fix there
  changes this test on purpose.
- Verify: the issue's replay exits 0; `uv run --locked pytest -c pyproject.toml -p no:doctest
  tests/unit/test_parameters.py`.

## Task 4: Vital's own measure (`tests/integration/test_vital_plugin.py`)

A measure in `vital/measures.md`'s terms, beside `test_a_value_set_through_the_host_is_the_one_the_state_holds`,
taking the module's `host` fixture (so it skips by name without Vital or on another machine):
- a head constant `_BELOW_VOLUME_S_FLOOR = {5.857149595214349e-20: 0, 3.4694490199051456e-18: 1}`,
  normalized value → double ulps the held display is off, its comment citing
  `verification/plugin-probe.txt` and what it measured;
- helpers written once, used by the test and imported by the probe: `_held_after_a_set(host,
  record, display) -> float` (set `to_normalized(display)`, read `_floats(host.state())`) and
  `_double_ulps(a, b) -> int` (the float64 twin of `_ulps`);
- `test_below_volume_s_floor_a_set_holds_the_normalized_path_s_value`: for each value, held ==
  `scale.to_preset(to_normalized(display))`, held != `to_preset(display)`, and
  `_double_ulps(to_display(held), display)` is the constant's count.
- Then run the probe (Task 2's `plugin-probe.txt`).

## Task 5: Docstrings read true (`src/patchbay_vital/parameters.py`, no behaviour change)

- The module docstring's curve paragraph (lines 11–15) and `MappedParameter.to_preset` (line 235):
  `to_preset` returns the float32 nearest the curve's inverse, clamped (a whole number on an indexed
  scale), which need not be one the scale holds — below `volume`'s floor for a display two presets
  share, and for an arbitrary display (#8) — and a set holds the scale's value at `to_normalized`'s
  result, which Vital holds exactly.
- Checked, recorded old beside new in `shape.md`: `README.md` (no "held"/"nearest" claim; "exact
  conversions" true), `CHANGELOG.md`'s map entries (none), `DisplayCurve.to_preset` and
  `NormalizedScale.to_normalized` (true, HELD 0 failures).

## Task 6: CHANGELOG

`### Fixed` under `[Unreleased]`: issue #13 with the spec folder — line 221 asserted above the floor
only, HELD everywhere, the two `@example`s, the characterization test, the integration measure, the
docstrings. Version stays 0.0.1.

## Task 7 (FINAL): Verification gate

1–6. `scripts/gate.sh` (bash -n; uv sync --locked + ruff format --check; ruff check; mypy; pytest;
   sync-standards --check), its transcript in `verification/gate-run.txt` opened with date,
   branch and commit; exit 0 required, fixing causes, never bypassing.
7. Docs — every file changed and every standard naming them; each sentence changed listed old
   beside new in `shape.md`.
8. Version — the `[Unreleased]` entry; no bump.
9. Standards retrospective, its own change set: `vital/parameter-map.md`'s "A displayed value comes
   back exactly…" bullet and its "arbitrary display … nearest one the parameter holds" sentence
   corrected against the shipped code, with the `vital:` `parameter-map` description in `index.yml`
   kept in step; candidates weighed from the shipped diff (a claim over every value measured per
   float32 exponent, not by uniform draws; the load snapping `P1` in `vital/plugin-state.md`,
   only if the probe's cases tell it apart). A base change (e.g. `base/testing/tests.md`) is a
   proposal: presented with AskUserQuestion, approved ones filed as one issue on
   `fromtheoutfit/patchbay-standards`, declined ones marked; `Proposals sent upstream:` recorded.
   Project edits presented to the owner for approval. Rerun `scripts/gate.sh` after them; the
   final run is `gate-run.txt`.

## Task 8: Revise issue #8's body in place

`gh issue view 8 --json body` into the scratchpad, edit, `gh issue edit 8 --body-file`; no
attribution, the rest of the body and its footer unchanged: a "Revised 2026-11-11 (after issue
#13)" paragraph; probe 4's "exact (1,104,000 of 1,104,000, every curve)" corrected where it stands
(16,069,858 below the floor whose `to_preset` is not held; 308,386 one double ulp off through the
set path); finding 3 of "From core's review of PR 19" gains those counts and Vital's measure (holds
the normalized path's value, never `to_preset`'s) and the candidate (to_preset takes the held
neighbour that shows the given display: closes both, changes no arbitrary display, decides what a
set stores where two presets share a display — finding 3's question — and not finding 1's);
citations by path and branch to this spec's `verification/` files.

Then stop: print `git status --short`, list the feature's files and the retrospective's apart. No
commit, push or PR.
