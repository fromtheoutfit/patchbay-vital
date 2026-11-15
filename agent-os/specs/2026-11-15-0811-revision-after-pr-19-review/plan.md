# Revision after the review of patchbay-vital's PR 19

- **Spec folder:** `agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`
- **Branch:** `refactor/16-…`, at `f26e6bc`, the head the review read. `main` is `f533b1b`.
- **Shaped** 2026-11-15 in plan mode with `/agent-os:shape-spec`; eight questions in two rounds.
- **Naming:** shape.md, the CHANGELOG entry and every issue edit write "patchbay-vital's PR 19"
  or its URL, never a bare "PR 19": issue #8 uses "core's review of PR 19" for
  fromtheoutfit/patchbay#19.

## Context

The owner's review of `f26e6bc`
(https://github.com/fromtheoutfit/patchbay-vital/pull/19#issuecomment-6894640094) has seven
findings: one bug, three test gaps, three efficiency and cleanup notes. The PR's main claim held
up. This revision fixes the bug and the three test gaps, declines the two efficiency notes, and
answers the seventh with a test instead of a code change. It decides neither of #8's questions
and none of #18's, and changes no gate file.

## Checked while shaping

Read-only, in memory, against `f26e6bc`; nothing written.

| # | Finding | On this tree |
|---|---|---|
| 1 | `holds` raises on a huge finite value | True: `holds(3.5e38)`, `holds(±1e300)` and a tiny-span scale's `holds(1.0)` raise `OverflowError` |
| 2 | The properties miss a `to_preset` without its exception | True: M5 in #16's `mutation.txt` fails four tests, neither property among them |
| 3 | The unit reader checks less than the integration reader | True, by reading. An emptied set fails the count test while two looping tests pass |
| 4 | "The double above" steps toward 0.0 | True and latent: every display that test uses is negative |
| 5 | `to_normalized` lands the preset twice | True |
| 6 | Indexed records pay for a landing | True |
| 7 | The exception cannot succeed on an indexed scale | False from 2 ** 23 up; true of the map |

- **Finding 1's suggested fix is not exact.** On `NormalizedScale(kind="linear",
  minimum=-16777216.0, maximum=1.0000001192092896)` normalized 1.0 lands on 2.0, past the
  maximum, and `holds(2.0)` is True today. On all 903 committed records `to_preset(0.0)` is the
  minimum and `to_preset(1.0)` the maximum.
- **Finding 1 reaches #18's method too:** `scale.to_normalized(3.5e38)` raises `OverflowError`.
- **Finding 2's `else` branch, with the exception removed:** fails on 3 of the 4 pinned floor
  displays, on 0 of 20,000 uniform displays (`random.Random(19)`), and on 15 of 20,160 displays of
  held presets (160 a binade, `default_rng(19)`). So the pinned-display test catches the mutant by
  name; the two Hypothesis properties still pass it.
- **Finding 7's premise:** `next_float32` of a whole number is whole from 2 ** 23 up, not
  2 ** 24. The map's largest indexed end is 362,879.
- **Finding 7's record.** A made-up record validates: indexed scale -16777216 to 16777216,
  linear curve, multiply 3, offset 2 ** 54. At normalized 0.7500000596046448 the held preset is
  8388610 and the curve's value for its display is 8388611, unheld. As shipped `to_preset` takes
  the exception and returns 8388610, which shows the display. Limited to linear scales it returns
  8388612, which does not. On 8,100 sampled values (`default_rng(7)`) the exception is taken on
  86; the record fails the come-back property on 102 as shipped, 188 with the limit.
- **Where a counted linear scale calls `holds`:** only from the exception. In the 2026-11-14
  count that is `volume`'s 308,386 OTHER values, in binades -58, -57 and -56 (31,879, 176,711
  and 99,796), with FELL 0 everywhere and every `env_1_delay` value KEPT.

## Shaping answers, in the owner's words

- **Finding 1:** "1. Shown by tests whose expected values come from primitives, each with a
  mutant failing by name: a huge finite value (3.5e38) answers False without raising; on the
  made-up scale whose top lands past its maximum, the value normalized 1.0 lands on answers True
  and the next float32 above it False. shape.md states the assumption the check rests on (the
  scale's value rises with the normalized value) and says whether any committed scale runs the
  other way; if one does, stop and present. holds gives the same answer as before this change on
  every committed record, checked over the pinned values and the indexed whole numbers."
- **Test gaps:** all three, "2: the else branch, 3: the unit reader, 4: toward math.inf".
- **Efficiency:** "1. Declined by the owner, citing the two earlier decisions (the fast path in
  PR 14's sixth review; finding 8 in this spec). shape.md records the timings with the machine,
  so a later spec that does need the speed starts from measured numbers."
- **Finding 7, first answer, withdrawn:** limit to linear, with the indexed count rerun, the
  linear statements shown unchanged from the diff, and "If the change cannot be made without
  altering what a linear scale executes, stop and present before touching it."
- **Finding 7, second answer:** "1. shape.md records that the earlier answer (limit to linear)
  was withdrawn once a record reaching the branch was found, with the record's fields. The
  reviewer's premise is corrected to 2 ** 23. The mutant limiting the exception to linear scales
  fails the new test by name."
- **The direct count:** "1. The transcript says how the three binades were identified as the only
  ones where the exception is taken (cited from the 2026-11-14 direct count's branch counts) and
  shows the recount's 308,386 matching that figure. Both trees and the machine are printed
  before and after. Any difference from main: stop and present."
- **Issue #18:** "Revise issue #18's body in place with a "Revised 2026-11-15" paragraph, no
  attribution, not a comment: the same defect reaches a huge finite value
  (scale.to_normalized(3.5e38) raises OverflowError), so the issue's scope reads "a value outside
  what the scale can take, finite or not", with the example added beside the others. Nothing in
  to_normalized or _landing changes here; shape.md and the CHANGELOG say the finite case was
  found in this revision and sits with #18. The text is short and factual, so file it without
  presenting first, and read it back."
- **Steps 2 to 5:** confirmed, with the naming rule above, and "The drafted reply to the review
  stays a draft in shape.md for the owner to post." No visuals. Standards beside the core five:
  `base/testing/tests`, `base/process/verification-gate`, `base/process/standards-retrospective`,
  `base/process/standards-index`, `base/process/ownership`, `vital/parameter-map`,
  `vital/measures`, `vital/preset-tests`, `vital/plugin-state`.

## Decisions

1. **The scope is the review's seven findings,** cited by URL in shape.md's first Decision.
2. **Finding 1: `holds` answers False outside what the scale's ends land on.**

   ```python
   if not self.to_preset(0.0) <= preset <= self.to_preset(1.0):
       return False
   normalized, landed = _landing(self, preset)
   return 0.0 <= normalized <= 1.0 and landed == preset
   ```

   - One check covers an infinity, a NaN and a huge finite value, so it replaces `isfinite`.
   - It rests on the scale's value rising with the normalized value. shape.md states that and
     says whether any committed scale runs the other way; one that does stops the work.
   - `_landing`, `to_normalized` and `MappedParameter.to_preset` are not touched.
3. **Findings 2, 3 and 4 are fixed** as the review asks. shape.md says what each change does and
   does not catch: the properties still pass without the exception, and finding 4 changes no
   value.
4. **Findings 5 and 6 are declined by the owner.** shape.md records the timings with the machine.
5. **Finding 7: the exception stays on an indexed scale and is held by a test.** No statement of
   `to_preset` changes. The first answer is recorded as withdrawn, with the record's fields.
6. **The direct count stands but for the three binades where `holds` runs,** which are recounted
   against `main`.
7. **The finite case of `to_normalized` sits with #18,** revised in place.
8. **A test's expected value comes from primitives,** as in #16's spec, Decision 7.
9. **No gate file changes.** No file is added, removed or renamed under `scripts`, `src`, `tests`
   or `agent-os/standards`, so the negative harness is not rerun.

## Task 1: Save spec documentation

Create the spec folder with **plan.md** (this plan), **shape.md** (the template, with the table
and the answers above), **standards.md** (the 14 standards as they read at `f26e6bc`),
**references.md** (#16's spec folder and its transcripts' scripts, the review comment) and
**verification/**. No visuals.

## Task 2: The fix, `src/patchbay_vital/parameters.py`

- `NormalizedScale.holds`: the body of Decision 2, and its docstring.
- `MappedParameter.to_preset`'s docstring only: where an indexed scale can take the exception
  (from 2 ** 23 up, which the map has none of). Its statements are not edited; the diff shows it.

## Task 3: Unit tests, `tests/unit/test_parameters.py`

Reuses `_a_set_lands_on`, `_what_a_set_holds`, `_nearest_quotient`, `_record`, `fma32`,
`next_float32`.

- **Finding 1, two tests:**
  - 3.5e38, ±1e300 and a tiny-span scale's 1.0 are not held, and nothing raises. Expected from
    `fma32(1.0, span, minimum)`, the top, which each value is past.
  - On the scale from -16777216 to 1.0000001192092896: the top, from `fma32`, is past the
    maximum and held; the float32 above it is not. Expected from `_a_set_lands_on`.
  - A Hypothesis property beside them: on every hand-built scale, `to_preset` of a larger
    normalized value is not smaller.
- **Finding 2:** `_assert_a_set_holds_it` gains the `else` branch: where what a set holds does
  not show the display, the other side does not both show it and land in [0, 1].
- **Finding 3:** `_pinned` fails by name on a set with no value and on a normalized value outside
  [0, 1], as the integration reader does (`tests/integration/test_vital_plugin.py`, `_pinned`).
- **Finding 4:** `math.nextafter(display, math.inf)`.
- **Finding 7:** one test on the made-up indexed record, at the display of 8388610: `to_preset`
  is the whole number on the other side, 8388610, worked out by `_what_a_set_holds` and written
  beside it as a literal.

## Task 4: The evidence

Each transcript: date, branch, both trees by blob and the machine, before and after, compared
with `cmp`; its scripts embedded; written outside the tree and copied in. The scripts are #16's,
in the session scratchpad (`pools.py`, `tree.sh`, `indexed_count.py`, `direct_count.py`,
`arbitrary_displays.py`, `mutate.sh`, `plugin_probe.py`, `cost.py` and their wrappers).

- **`holds-check.txt`, a count.** The tree before this change is `f26e6bc`, extracted with
  `git archive`.
  - Every committed scale: its ends in order, `to_preset(0.0)` and `to_preset(1.0)`.
  - `holds` in both trees on every committed record, at the pinned values' presets, the curve's
    float32 for each, what a set holds, and the float32 either side of each.
  - `holds` in both trees on every whole number and half of every indexed record, and one past
    each end.
- **`indexed-count.txt`,** rerun in full against `main`.
- **`direct-count.txt`, `volume`'s binades -58 to -56,** five columns, against `main`, about 9
  minutes, under `caffeinate`.
  - It prints the 2026-11-14 transcript's lines that show OTHER in those three binades alone and
    FELL 0 throughout.
  - It shows the recount's OTHER total against 308,386.
- **`arbitrary-displays.txt`, `plugin-probe.txt`,** rerun as checks.
- **`mutation.txt`,** on scratch copies, with the earlier mutants rerun:
  - `holds` without its check fails finding 1's first test by name;
  - `holds` checked against `[minimum, maximum]`, the review's form, fails its second;
  - the exception removed fails the pinned-display test through the helper, and the transcript
    says the two properties pass it;
  - the exception limited to linear scales fails finding 7's test by name;
  - an emptied set and a value of 1.5, on `f26e6bc`'s unit tests and on this tree's;
  - finding 4's old line is named an equivalent on the values the test uses.
- **`cost.txt`,** rerun; its figures go into shape.md with the machine.

**Stops, presented at once:** a committed scale that runs the other way; `holds` differing from
before on any checked value; any difference from `main` in the recount or the indexed count; a
recount total other than 308,386; a changed display that was held on `main`; Vital holding
another value; the fix needing an edit to `_landing` or to `to_preset`'s statements.

## Task 5: Docs, Version and issue #18

- `CHANGELOG.md`, `[Unreleased]`: #16's entry gains the revision after patchbay-vital's PR 19,
  with each finding's outcome and the finite case left to #18.
- **Issue #18,** body revised in place, a "Revised 2026-11-15" paragraph and the example, no
  attribution; read back afterwards. Its example is run on this tree first.
- **shape.md** holds the drafted reply to the review, one line a finding, for the owner to post,
  and the lines of the PR's body the revision makes stale.

## Task 6: The standards retrospective

From the shipped diff, its own change set. Each edit is drafted on a scratch copy and approved
before it is made.

- `vital/parameter-map.md`: `holds` outside what the ends land on; the exception on an indexed
  scale, held by the new test; a recount limited to the values a changed statement runs on, and
  how they are identified.
- `vital/measures.md` and `index.yml`: both readers' checks.
- Base proposals, presented multi-select; one that refines an open upstream issue is revised
  into it in place, only after the gate is clean. Candidates: #42's evidence (both readers), and
  an assertion helper that checks a rule's exception in both directions.

## Task 7 (final): Verification gate

1. `bash -n` on every shell script under `scripts/` as git lists them.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check`.
3. `uv run --locked ruff check --config pyproject.toml`.
4. `uv run --locked mypy --config-file pyproject.toml`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`.
6. `scripts/sync-standards.sh --check`.
7. **Docs**, recorded in shape.md.
8. **Version**, recorded in shape.md.
9. **Standards retrospective**, last, with `Proposals sent upstream:`.

`scripts/gate.sh` runs 1 to 6, last, and `verification/gate-run.txt` records it with the date,
the branch, the tree and the machine before and after. Only the Results paragraph and the
upstream issues' numbers are written after it. Then print `git status --short`, list the
feature's files and the retrospective's separately, and stop. No stage, commit, push or pull
request edit.

## Verification, end to end

- The unit suite and, with Vital, the integration module pass; each new test is failed by name
  by its mutant.
- `holds-check.txt` and `indexed-count.txt` show no value differing; the recount shows 308,386
  and no difference from `main`.
- `scripts/gate.sh` exits 0, recorded in `gate-run.txt`.
