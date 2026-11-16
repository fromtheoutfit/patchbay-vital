# Revision after PR 23's second review (issue #8, the instrument) — Shaping Notes

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The second review on PR 23 (fromtheoutfit/patchbay-vital#23, `VitalInstrument`, closes #8): issue
comment 6927191623, "Final-round review of `64863c6`: correctness first", by the owner, 2026-11-16
19:44 UTC. It confirms six checks, leaves two correctness findings and lists nine items "for
later issues (not correctness)". Each correctness finding is checked against the code at
`64863c6` and fixed as the owner decided. Three later items are taken here and six go to two
issues. The branch is the PR's. Nothing is committed, pushed or posted to the PR by an agent.

| | Finding | Where |
|---|---|---|
| A | One recorded upgraded float is still kept, so Vital is not set back to the model's value | `agent-os/standards/vital/instrument.md:60`, `instrument.py:222` |
| B | The load-versus-set sample test passes whatever float the load chose | `tests/unit/test_instrument.py:643` |

After the work was reported, the owner had one more item fixed inside this spec, not a new one:
an assertion of `tests/unit/test_instrument.py`, line 365 at `64863c6`, that passed whether or not
its docstring was true. It is "One more item" below.

The nine later items, in the review's order:

| # | Item | Where |
|---|---|---|
| 1 | `load_patch` docstring still describes the old rule | `instrument.py:241` |
| 2 | The `midi.py` docstring claims velocity and two voices "with Vital's MPE setting off and on"; `plugin-state.md` repeats both | `midi.py:19` |
| 3 | After a lost step, `render` and `set` raise an error outside the types core names, ahead of the usual checks | `instrument.py:390` |
| 4 | The sixteen-note MIDI test computes its expected bytes and checks ons and offs apart | `test_midi.py:312` |
| 5 | `_Entry` re-lists the metadata fields by hand | `patch.py:107` |
| 6 | `_float_of` copies `to_preset`'s first step | `patch.py:154` |
| 7 | The merge of a preset's floats is written three times | `patch.py:198, 283, 388` |
| 8 | `_entry_text` repeats `start._section`'s JSON settings | `patch.py:184` |
| 9 | `check_loadable` decodes three sections a second time | `patch.py:399` |

## What was checked while shaping

Each by a run in memory, with nothing written to the tree. The counts on Vital itself are Task
6's, and every figure in a text comes from the run that is kept there.

### Finding A is real

For each line of `tests/data/upgraded-floats.txt`, the map says what `set(id, get(id))` does on a
model holding the file's float: `check_value` on the display, then
`writes_same(record.to_preset(display), held)`, as `set` decides it.

- **42 reach the plugin.** The 29 keys the file lacks (`chorus_cutoff` on 3 presets,
  `chorus_spread` on 2, `lfo_1_smooth_mode` to `lfo_7_smooth_mode` on 3, `stereo_mode` on 3),
  whose default is on the grid, and 13 floats inside their scale and on the grid:
  `osc_N_stack_style` 8 times, `filter_1_style` and `filter_2_style`, `osc_3_spectral_morph_type`
  twice, and `modulation_12_amount` on Oolacile Evil Dubstep Bass.
- **3 are refused as out of bounds,** `flanger_center` against 8 to 136:

  | Preset | In the file | Vital holds |
  |---|---|---|
  | Touch Tone | 0.0 | 53.689998626708984 |
  | Memory Leak | 0.0 | 53.689998626708984 |
  | Oolacile Evil Dubstep Bass | -15.359999656677246 | 38.32999801635742 |

- **1 is kept:** `modulation_10_amount` on Oolacile Evil Dubstep Bass. The model holds
  0.19999998807907104, which `scale.holds` rejects, on a linear scale from -1 to 1 shown as
  itself. `to_preset` of its display is 0.20000004768371582, and `writes_same` of the two is
  False, so the set is kept and `host.set` is not called. Vital holds 0.07499999552965164, which
  is off the grid too.

No rule for `set` makes the claim true as it was written. The plugin takes a float only through a
normalized value, so it cannot be set onto a float no normalized value lands on, and a reload of
the model's text is upgraded again. Core's clause is why the float is kept at all: `Instrument.get`
at `eddba95` gives "the value given itself at a bound, and at any value `get` has returned for it
that `set` takes".

Where the claim was made: `agent-os/standards/vital/instrument.md:60`, the module docstring of
`instrument.py`, `CHANGELOG.md` (the first revision's finding 1 bullet), the first revision's
`shape.md` (the reply's item 1 and the paragraph drafted for core's issue), and the body of
fromtheoutfit/patchbay#20, in its "Revised 2026-11-16" section.

### Finding B holds in a narrower form than its title

Both forms of the test were run in memory over the fake plugin, on the test's own sample (seed 23,
25 rounds of 55 groups, 1,375 comparisons): the old form, a load and then a set; and the new, a
set on the start preset and then a load.

| `_float_of` | Sample | Old form: disagreements, sets that called no plugin | New form: disagreements |
|---|---|---|---|
| as shipped | uniform | 0, 0 | 0 |
| MD1: always the curve's float32 | uniform | 243, 0 | 243 |
| the neighbour mutant | uniform | 0, 0 | 0 |
| as shipped | uniform and both bounds (1,485) | 0, 0 | 0 |
| the neighbour mutant | uniform and both bounds (1,485) | 0, 1 | 1 |

- **The old test could fail.** None of its 1,375 sets took the keep path, and MD1 fails it on 243
  comparisons, as the first revision's `mutation.txt` already shows (MD1, "2 failed").
- **It could not fail where the loaded float shows the display given.** There the set after the
  load is the keep rule's no-op, so a load that took another float showing that display passes.
  That needs a display two floats show. At the ends of the 55 groups' scales there is one:
  `volume` at -80 dB, shown by 0.0 and by 1.401298464324817e-45. Of 18,400 on-grid floats drawn
  over the linear groups, none shares its display with a neighbour.
- **A uniform draw never reaches that display,** so rewriting the test alone changes nothing a
  mutant can show. The neighbour mutant (where the curve's float32 shows the display, take the
  float32 beside it when that shows the display too) passes the old form with the bounds added,
  through one kept set, and fails the new form on one comparison, `volume` at its minimum.
- **The kept transcript stands.** `load-and-set-sample.txt` of the first revision compares
  `preset_of` with `MappedParameter.to_preset` directly, with no instrument and no keep rule.

## Shaping answers

In the owner's words, 2026-11-16.

**Finding A,** to "Correct the claim": "1. set is unchanged. Each place that made the claim says
what was counted: 42 mended, 3 refused as out of bounds, 1 kept, each named. The tests hold the
kept case and the three counts and name issue #22. Issue #22's body is revised in place with a
"Revised 2026-11-16" paragraph, not a comment: a set of the value shown mends 42 of its 46 floats,
and the four that remain are its own to decide, with the kept one (Oolacile Evil Dubstep Bass,
modulation_10_amount) as the case no set can reach."

**Finding B,** to "Set from another value": "1. The new mutant (a load that takes the curve's
float32 for an arbitrary display) is shown passing the old test and failing the new one by name,
in one transcript. The test's docstring says why the set is made from another value."

**Finding B's mutant,** once the run above was presented, to "The neighbour mutant, bounds added":
"1. The transcript shows both mutants against both forms, four results, with one sentence each on
what it shows. shape.md records that the mutant I named did not separate the forms and why, and
the reply to the review states finding B as verified: the old test could fail, but not where two
floats show one display."

**The mutant the owner named did not separate the forms.** A load that takes the curve's float32
for an arbitrary display is MD1. For an arbitrary display that float32 does not show the display
given, so the set after the load is a real set and holds what `to_preset` gives: the old test
compares the two and fails wherever the curve's float32 is off the grid, 243 times in 1,375. The
new form fails on the same 243. A mutant separates the forms only where its float shows the
display exactly.

**The later list,** choosing "load_patch docstring", "MPE and velocity wording" and "Sixteen-note
MIDI test": "1, 2 and 3. The nine "for later" items not taken here go into one patchbay-vital
issue, no attribution, each as the reviewer stated it and marked unverified, filed after the
gate's clean run; shape.md lists where each of the nine went."

**The rest of the later list,** to "Draft them for you", which replaces the note above on where
they go: "1, without a stop: after the gate's clean run, file both as drafted, no attribution,
each item as the reviewer stated it and marked unverified, each read back.
- One on fromtheoutfit/patchbay-vital: the five patch.py cleanups (_Entry, _float_of, the merge
  written three times, _entry_text, check_loadable's second decode). It blocks nothing.
- One on fromtheoutfit/patchbay: after a failed rollback an adapter's instrument has lost step
  with its device, and set and render then raise an error outside the types the Instrument
  protocol names for them, ahead of the usual checks; it asks whether core's contract should say
  what an instrument does in that state. Draft 4 (0.1.0) lists it with the others.
This replaces my earlier note putting all the later items in one patchbay-vital issue. shape.md
lists where each of the nine went."

**The two issue bodies,** to "Without a stop, with the issues": "2. Both revised in place after
the gate's clean run, in the same step as the two new issues, each keeping its existing text with
a dated paragraph added, no attribution, read back. If the gate is not clean, nothing is filed or
edited: stop and present."

**References, standards, visuals, product:** "Yes, as listed (Recommended)". The references are
the first revision's spec and the instrument spec. The standards are the core tier and the seven
in "Standards Applied". There are no visuals, and `agent-os/product/` is unchanged.

The plan was approved as written, the four drafts in it whole.

**One more item, after the report,** which had noted line 365 as not fixed and outside the spec:
"Fix tests/unit/test_instrument.py:365 here: it is this pull request's own file and a test that
passes whether or not its docstring is true. Make it compute the float32 below as its docstring
says (the next float32 toward 0.0, by the package's next_float32 or from primitives), show with a
mutant that it can now fail, and rerun the gate once for gate-run.txt. Then rerun the contract
tests against Vital on the final tree (shared host and fresh host) so draft 4 cites a run whose
file hashes are the merging tree's. I approve the retrospective change set as described:
vital/instrument.md, vital/plugin-state.md and the index.yml entry. Stop and print git status
--short. Do not commit or push."

And where it goes: "Make the change directly, inside the open revision spec
(agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/), not as a new spec: add it
to that spec's shape.md as one more item with its mutant, replace its gate-run.txt and
contract-run with the reruns on the final tree, and say in the retrospective whether it teaches
anything the standards lack ("no changes" is a valid answer)."

## Decisions

1. **Finding A: the claim is corrected; `set` is unchanged.** Each place that made the claim says
   what was counted: 42 mended, 3 refused as out of bounds, 1 kept, each named. A unit test holds
   the kept case on the fake plugin, and a test against Vital holds the three counts over the 46
   floats, the three refused and the one kept written out. Both name issue #22.
2. **Finding B: the set is made from another value.** The test stays an instrument test of a load
   against a set and keeps its name. Each round sets every display on the start preset, counts
   the sets at the plugin so none is the keep rule's no-op, then loads the same displays and
   compares the floats. The sample gains each group's two bounds, 1,485 comparisons, because
   `volume`'s minimum is a display two floats show. The docstring says why.
3. **B's evidence: both mutants against both forms.** MD1 and MD4, the neighbour mutant, each
   against the test as at `64863c6` and as rewritten: four results, one sentence each. The reply
   states finding B as verified in its narrower form.
4. **Three later items are fixed here:** the `load_patch` docstring; the MPE and velocity wording,
   reworded to what `overlap-probe-2.txt` shows, with no new probe; and the sixteen-note MIDI
   test, its 32 messages written out in stream order.
5. **The other six go to two issues, filed without a stop after the gate's clean run,** no
   attribution, each item as the reviewer stated it and marked unverified, each read back: the
   five `patch.py` cleanups on fromtheoutfit/patchbay-vital, and the lost-step errors on
   fromtheoutfit/patchbay. Draft 4 (0.1.0) lists the second with the others and stays held.
6. **Two issue bodies are revised in place in that same step,** each keeping its text with a dated
   paragraph added, read back: patchbay-vital#22 and fromtheoutfit/patchbay#20.
7. **If the gate is not clean, nothing is filed or edited: stop and present.** The same if a
   figure in a draft differs from the kept run.
8. **Stops.** Vital giving other counts than 42, 3 and 1; a disagreement in the rewritten sample
   test on the unmutated tree; any of the four mutation results falling otherwise than MD1
   failing both forms and MD4 passing the old and failing the new.
9. **No gate file changes,** and no file is added, removed or renamed under `scripts`, `src`,
   `tests` or `agent-os/standards`, so the negative harness is not rerun.
11. **One more item: the float32 below is computed, from primitives.** In
    `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest` the neighbour is taken
    by the float32's own bits, `struct` alone, as the module's rule for an expected value has it,
    and it is written out with its display. A mutant of the example shows the corrected line can
    fail where the line as it was passed. The gate is run once more and every transcript is run
    again on the final tree ("One more item" below).
10. **The earlier test keeps its name.**
    `test_a_set_of_the_value_shown_on_an_upgraded_float_sets_vital_to_the_model_s` is about Ah Eh
    Ee Oh's `osc_1_stack_style`, as its docstring says, and the first revision's `mutation.txt`
    names it. The new test beside it holds the counts.

## Context

- **Visuals:** None.
- **References:** the first revision's spec (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`)
  and the instrument spec (`agent-os/specs/2026-11-15-1448-the-instrument/`); core at `eddba95`,
  read in the installed package. `references.md` says what each gives.
- **Product alignment:** `agent-os/product/mission.md` and `tech-stack.md` are unchanged. The
  adapter describes the instrument, and a claim about it is counted.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `vital/instrument` — it holds the claim finding A corrects, the load rule finding B's test
  backs, and the note rule's MPE sentence.
- `vital/plugin-state` — what Vital does with an older preset, and the MPE and velocity bullet.
- `vital/parameter-map` — `to_preset`, `scale.holds` and what "a float a set lands on" means.
- `vital/preset-tests` — how a test reads the installed presets and `upgraded-floats.txt`.
- `vital/measures` — a claim about Vital's audio says what probe it came from.
- `testing/tests` — where a test lives and how its expected values are made.
- `process/verification-gate` — the gate this spec is held to.

## What was built

No rule of the package changed: `src/` differs in docstrings alone.

- **Finding A, the tests.**
  - `tests/unit/test_instrument.py`,
    `test_a_set_of_the_value_shown_on_an_upgraded_float_no_set_lands_on_leaves_the_plugin_upgraded`:
    on the fake plugin the model holds `modulation_10_amount` at 0.19999998807907104 and the
    plugin 0.07499999552965164. A set of the value shown calls no plugin, leaves both as they
    were, and is published once, `old` equal to `new`. That a set of the float would hold
    0.20000004768371582 is worked out from primitives.
  - `tests/integration/test_vital_instrument.py`,
    `test_a_set_of_the_value_shown_mends_42_of_the_upgraded_floats_is_refused_on_3_and_kept_on_1`:
    over the 11 presets and 46 floats, on Vital. The three refused and the one kept are written
    out by preset and key (`_REFUSED`, `_KEPT`), and 42 is `_MENDED`.
- **Finding A, the texts.** `instrument.py` (the issue #22 limit, and the docstrings of `set` and
  `load_patch`), `README.md` (the issue #22 limit) and `CHANGELOG.md` say what was counted. The
  first revision's `shape.md` gains two dated notes, under the reply's items and under the
  paragraph drafted for core's issue, its text kept.
- **Finding B.** `test_an_arbitrary_display_in_a_patch_holds_what_a_set_of_it_holds` keeps its
  name. Each of its 27 rounds loads the start preset, sets the 55 displays, asserts the plugin
  received 55 sets, then loads the same displays and compares each float with the set's, bit for
  bit. Two rounds are the bounds. Its docstring says why.
- **The three later items.** `load_patch`'s docstring gives the load rule. `midi.py`'s docstring
  says which MPE setting each thing was measured under. The sixteen-note test compares the whole
  stream with one literal tuple of 32 messages.
- **One more item, the float32 below.** `tests/unit/test_instrument.py` gains
  `_float32_toward_zero`, one less in a float32's bits, and
  `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest` uses it where it had
  `_float32(math.nextafter(own, 0.0))`. The test now asserts the neighbour and its display,
  written out, that a set of it lands on it, and that it is nearer the display given than what
  the set holds. Its docstring names the neighbour and says the scale holds it.
- **Two corrections made in passing,** each in a line this spec was already editing: the
  CHANGELOG's first-revision entry said the instrument's entry was "above" it, and it is below;
  `midi.py` cited "this revision's spec", which now names the first revision.

## What the transcripts show

Each ran on the tree as it is committed but for this spec's records and the retrospective's
standards files, was written outside the tree and copied in, and gives the machine and the tree
before and after by blob. All were run again after the last edit to `src/`, `tests/`,
`README.md` and `CHANGELOG.md`, which was the one more item's; the figures here are from those
runs, 2026-11-16 15:46 to 15:49 EST.

- **`verification/upgraded-set-count.txt`:** on Vital 1.6.4 through pedalboard 0.9.26, each of
  the 46 floats with the model's float, Vital's before the set, the outcome and Vital's after.
  Mended 42, refused 3, kept 1, none of the three 0. Before each set Vital held the float the
  data file records.
- **`verification/mutation.txt`:** on a scratch copy outside the tree. Unmutated, the sample test
  passes in both forms and the unit suite passes, 597.

  | Mutant | The test as at `64863c6` | The test as rewritten |
  |---|---|---|
  | MD1, a load always takes the curve's float32 | fails, at `beats_per_minute` 214.3012627664921 | fails, at the same display |
  | MD4, a load takes the float32 next above the curve's where it shows the display too | passes | fails, at `volume` -80 dB |

  - Beyond the four, each mutant against the old form given the new sample, a throwaway module
    in the copy alone. Under MD4 its agreement test passes and its second test fails: "1 set(s)
    after the load called no plugin: [('volume', -80.0)]". So the old form passes MD4 because of
    the form, not only for want of the display.
  - MD4 fails 10 tests of the unit suite and MD1 2: neither would have survived the suite. The
    finding was about what this one test could show.
  - MK1 (the keep rule gone) fails the new kept-case test, and MM9 (a moved note takes the
    highest free channel) fails the rewritten sixteen-note test. 0 unexpected, 0 survived.
  - MN1, the one more item's: the display given moved to 216.85142725, the other side of the
    curve's float32. The test as at `64863c6` passes and the test in the tree fails, "assert
    2.115258789103791e-05 < 7.457641601149589e-06". 2 results, 0 unexpected.
- **`verification/contract-run.txt`:** core's thirteen at `eddba95`, 13 of 13 on the module's one
  Vital, 13 of 13 on a `VitalHost` of its own for each test, and 13 of 13 over the fake plugin.

## One more item: the float32 below

Asked for by the owner after the report, and made inside this spec ("Shaping answers").

- **What was wrong.** `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest`, in
  `tests/unit/test_instrument.py`, says of `beats_per_minute` at 216.85141355537831 that the
  float32 below the curve's, shown as 216.8514060974121, is nearer the display given than what a
  set holds. Its line 365 at `64863c6` computed that neighbour as
  `_float32(math.nextafter(own, 0.0))`. `math.nextafter` steps a double, and the double next to
  a float32 rounds back to that float32, so the line compared the curve's own float32,
  3.6141903400421143, which is the nearest by construction. It passed whether or not the
  docstring's sentence was true.
- **What it is now.** `_float32_toward_zero` takes the neighbour by the float32's bits, one less,
  with `struct` alone, as the module's rule for an expected value has it. The test asserts:
  - the neighbour and its display, written out: 3.614190101623535 and 216.8514060974121;
  - that a set of it lands on it, by `builders.what_a_set_holds`, so it is a value the scale
    holds and "need not be the nearest" is about a value a set could have held;
  - that it is nearer the display given than what the set holds, 7.46e-06 against 2.12e-05.
- **Two things beyond the line itself,** which the owner is told of: the assertion that a set
  lands on the neighbour, and the docstring naming the neighbour and saying so. The docstring's
  sentence was true; the test now holds each figure in it.
- **The package's `next_float32` gives the same float,** checked while shaping the item. The test
  takes the neighbour from primitives and does not call it.
- **The mutant, MN1,** is of the test's example and not of the package: nothing in `src/` decides
  this assertion, whose three numbers are the example's. The display given is moved to
  216.85142725, on the other side of the curve's float32, so the curve's float32 and what a set
  holds are the same two floats and the float32 below is now the farther. The line as it was
  passes; the corrected line fails by name (`verification/mutation.txt`, Part 3).
- **No other line has the defect.** Every other `nextafter` under `tests/` either steps a double
  that is meant to be one, a display beside a bound or a sum in the host's rounding tests, or is
  numpy's on a `float32`.
- **Not changed:** the same test in `tests/integration/test_vital_instrument.py`. Its docstring
  says the float32 below the one held is nearer the display given and is not taken. That float is
  the curve's own, and the sentence is true by the figures the unit test pins; that module does
  not assert it.

## Where each of the nine later items went

| # | Item | Where it went |
|---|---|---|
| 1 | `load_patch` docstring | Fixed here: `instrument.py`. |
| 2 | MPE and velocity wording | Fixed here: `midi.py`, and `vital/plugin-state.md` in the retrospective. No new probe. |
| 3 | Error types after a lost step | fromtheoutfit/patchbay#25 (draft 2), as the reviewer stated it, unverified. Draft 4 (0.1.0) of the instrument spec lists it. |
| 4 | Sixteen-note MIDI test | Fixed here: `tests/unit/test_midi.py`. |
| 5 | `_Entry` | fromtheoutfit/patchbay-vital#24 (draft 1), as the reviewer stated it, unverified. |
| 6 | `_float_of` | The same issue. |
| 7 | The merge written three times | The same issue. |
| 8 | `_entry_text` | The same issue. |
| 9 | `check_loadable`'s second decode | The same issue. |

## Drafts for the owner

Drafts 1 to 4 were approved whole with the plan and are filed or added without a stop after the
gate's clean run, each read back (Decisions 5 to 7). None carries attribution. Two changes were
made to the approved text, both in draft 3, and the owner is told: the test is named, as the
draft said it would be once it existed, and "by the map" is added to the last sentence of its
third bullet, since that float was computed and not measured on Vital. The reply is the owner's
to post.

**What was done, 2026-11-16, after the gate's clean run** (exit 0, and every figure in the four
drafts as the kept runs give it):
- Both repositories' open issues were listed first; none already said either.
- Draft 1 is filed as fromtheoutfit/patchbay-vital#24, "The patch module: five cleanups from the
  second review of PR 23, unverified".
- Draft 2 is filed as fromtheoutfit/patchbay#25, "Instrument: what an instrument does once it
  has lost step with its device".
- fromtheoutfit/patchbay-vital#22's body gains draft 3 and fromtheoutfit/patchbay#20's gains
  draft 4, each under its dated heading at the end, the text before it kept whole.
- Each of the four was read back with `gh api`: both titles and all four bodies are identical to
  the text sent, and each revised body begins with the body as it was.
- Draft 4 of the instrument spec, the 0.1.0 proposal, gains a "Revised 2026-11-16, after the
  second review of PR 23" paragraph: it lists fromtheoutfit/patchbay#25 with the others and
  cites this spec's contract run. It stays held until the pull request for #8 merges.
- The two numbers are not the same issue: fromtheoutfit/patchbay#24 is core's question about
  two notes of one pitch, and fromtheoutfit/patchbay-vital#24 is the five cleanups.

### 1. New issue on fromtheoutfit/patchbay-vital

> **Title:** The patch module: five cleanups from the second review of PR 23, unverified
>
> The second review of PR 23 (fromtheoutfit/patchbay-vital#23, "Final-round review of `64863c6`", 2026-11-16) listed these under "For later issues (not correctness)". Each is given as the reviewer stated it and is **unverified**: a lead to check against the code, not a confirmed defect. It blocks nothing.
>
> - **`_Entry`** (`patch.py:107`): it re-lists the metadata fields by hand while `_whole` reads them through `METADATA`. A field added to `VitalPreset` would raise a bare `AttributeError` from `load_patch` instead of `PatchRefusedError`.
> - **`_float_of`** (`patch.py:154`): it copies `MappedParameter.to_preset`'s first step, so a later change to how `to_preset` bounds or rounds has to be made twice.
> - **The merge of a preset's floats:** `split_modulations` followed by `{**settings.values, **slot_floats}` is written three times (`patch.py:198, 283, 388`). `instrument._held`/`_holding` reach the same floats a fourth way.
> - **`_entry_text`** (`patch.py:184`): it repeats `start._section`'s JSON settings, so `_section`'s claim to be "the one writer of nested JSON" is already false.
> - **`check_loadable`** (`patch.py:399`): it decodes the wavetables, LFOs and sample sections a second time on every `load_patch`, after `VitalPreset`'s validator has already parsed them.
>
> The line numbers are the review's, at `64863c6`. The last was finding 7 of the first review, declined there on a measurement (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/verification/check-cost.txt`).
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. Each item is checked against the code first, then fixed or declined with its reason. CHANGELOG; gate green. No commit, pull request or push by an agent.

### 2. New issue on fromtheoutfit/patchbay

> **Title:** Instrument: what an instrument does once it has lost step with its device
>
> `Instrument`'s docstrings at `eddba95` name the errors a call raises. `set`: "ParameterNotFoundError, UnitMismatchError or ValueOutOfRangeError when the id, the unit or the value is not one the instrument takes". `render`: "RenderFailedError, publishing nothing, when nothing usable can be rendered". `load_patch`: "PatchRejectedError when the instrument cannot load all of it, changing nothing." Nothing says what an instrument does once it can no longer answer for its device.
>
> ## The case
>
> patchbay-vital's `VitalInstrument` holds a model and drives a hosted plugin. When the plugin refuses a load, the instrument sends the model's own preset again and the call is refused as `PatchRejectedError`, nothing changed. When the plugin refuses that too, its state is unknown while the model holds the preset before. The instrument has lost step with its device, and "changing nothing" cannot be claimed.
>
> What it does then, at `64863c6` on the branch of fromtheoutfit/patchbay-vital#23:
>
> - `load_patch` raises the adapter's `PluginStateError`, which is not a `PatchRejectedError`, naming both refusals and saying to build a new instrument.
> - Every later `set`, `load_patch` and `render` raises `PluginStateError`, the plugin not called and nothing published. That error is outside the types the protocol names for `set` and `render`.
> - The refusal comes ahead of the usual checks: a `set` of an unknown id is refused with it, not with `ParameterNotFoundError`.
> - `get`, `patch` and `parameters` go on answering from the model, which the device may no longer match.
>
> The second review of that pull request raised this as worth an issue against core's contract. It is given as the reviewer stated it and is **unverified** beyond the docstrings quoted.
>
> ## The question
>
> Should core's contract say what an instrument does in that state? For instance:
>
> - whether it may refuse every later call, and with which error, one core names, so a caller can catch it without knowing the adapter;
> - whether that refusal comes before or after the checks the protocol already names;
> - whether `get` and `patch` may go on answering from a model the device no longer matches.
>
> No contract test reaches the state: it takes a device that refuses twice.

### 3. A paragraph added to fromtheoutfit/patchbay-vital#22, its text kept

> ## Revised 2026-11-16
>
> A set of the value `get` shows reaches the plugin wherever the model holds a float a set lands on (the revision after the first review of PR 23). Counted over the 46 floats above, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (`agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/verification/upgraded-set-count.txt`, held by `test_a_set_of_the_value_shown_mends_42_of_the_upgraded_floats_is_refused_on_3_and_kept_on_1`):
>
> - **42 are mended by that set.** Vital then holds the float the model shows; for a key the file lacks that is the parameter's default.
> - **3 are refused as out of bounds:** `flanger_center` on Touch Tone, Memory Leak and Oolacile Evil Dubstep Bass. The file's value (0.0, 0.0 and -15.359999656677246) shows a display outside the parameter's bounds, which `set` does not take.
> - **1 is kept:** `modulation_10_amount` on Oolacile Evil Dubstep Bass. The model holds 0.19999998807907104, a float no set lands on, so a set of its own display keeps it and the plugin is not called. Vital goes on playing 0.07499999552965164. This is the case no set can reach: nothing the host can set puts Vital on the model's float, and a set of any other value and back holds the neighbour, 0.20000004768371582 by the map.
>
> So a set of the value shown mends 42 of the 46, and the four that remain are this issue's to decide, whichever option is chosen.

### 4. A paragraph added to fromtheoutfit/patchbay#20, its text kept

> ## Revised 2026-11-16, after the second review of patchbay-vital's PR 23
>
> One sentence of the section above said more than was counted: "On any other float it reaches the plugin, so the plugin goes back to the model's float after Vital upgrades a preset older than it." Counted over the 46 floats Vital upgrades on the presets it installs (fromtheoutfit/patchbay-vital#22): a set of the value `get` shows puts Vital back on the model's float for 42. 3 show a value outside their parameter's bounds, which `set` refuses. 1 holds a float no set lands on, so the set is kept and Vital stays on its upgraded value: `modulation_10_amount` on Oolacile Evil Dubstep Bass, 0.19999998807907104 in the model and 0.07499999552965164 played. The keep rule and this issue's question are unchanged. The evidence is `verification/upgraded-set-count.txt` in `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/` on patchbay-vital's branch for its issue #8.

### 5. Reply to PR 23's second review, for the owner to post on fromtheoutfit/patchbay-vital#23

Not posted by an agent. The two issue numbers were filled in once the issues were filed.

> Revised in `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/`. Both findings were checked against the code at `64863c6` first.
>
> **A. Fixed, by correcting the claim.** `set` is unchanged. No set can put Vital on a float off the grid, so no keep rule makes the claim true as it was written. Counted on Vital over the 46 upgraded floats (`verification/upgraded-set-count.txt`), a set of the value shown mends 42. 3 are refused as out of bounds: `flanger_center` on Touch Tone, Memory Leak and Oolacile Evil Dubstep Bass. 1 is kept: `modulation_10_amount` on Oolacile Evil Dubstep Bass. The standard, the docstrings, the README, the CHANGELOG and the first reply now say that. A unit test holds the kept case and a test against Vital holds the three counts. fromtheoutfit/patchbay-vital#22 and fromtheoutfit/patchbay#20 each gain a dated paragraph.
>
> **B. Verified in a narrower form, and fixed.** The old test could fail: none of its 1,375 sets took the keep path, and a load that takes the curve's float32 (MD1) fails it. It could not fail where the loaded float shows the display given, which takes a display two floats show. `volume` at -80 dB is one, and the uniform sample never reached it. The test now makes its set from another value, counts each set at the plugin, and takes each group's two bounds, 1,485 displays. `verification/mutation.txt` shows both mutants against both forms: MD1 fails both, and MD4, a load that takes the float32 above the curve's where it shows the display too, passes the old and fails the new at `volume`'s minimum.
>
> **The nine later items.**
> 1. `load_patch` docstring: fixed here.
> 2. MPE and velocity wording: fixed here, in `midi.py` and `plugin-state.md`, reworded to what `overlap-probe-2.txt` measured. No new probe.
> 3. Error types after a lost step: fromtheoutfit/patchbay#25, unverified.
> 4. Sixteen-note MIDI test: fixed here, its 32 messages written out in stream order.
> 5. to 9. The five `patch.py` items: fromtheoutfit/patchbay-vital#24, unverified.
>
> **One more, beyond the review.** `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest` said the float32 below the curve's is nearer the display given, but computed `_float32(math.nextafter(own, 0.0))`, which is the curve's float32 itself. It now takes the neighbour by its bits and asserts it, its display and that a set lands on it. `verification/mutation.txt` (MN1) shows a display on which the corrected line fails and the line as it was passed.

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

**Results (2026-11-16):** `scripts/gate.sh` exits 0 on branch
`feature/8-the-instrument-vitalinstrument-over-vitalhost-patchvitalpreset-and-cores-contract-tests-against-a-real-vital-spec-b-of-7`,
all six steps. 803 tests passed and none skipped, in 84 s, with Vital and its presets installed;
the PR's head had 801, and the two more are finding A's. The record is
`verification/gate-run.txt`: the date and branch, the machine and the tree before and after by
blob, and the script it ran. That run is the one made for the one more item, once, at 15:47 EST,
on the final tree. It replaces the run of 15:32 EST, made after the retrospective's edits, which
passed with the same 803.

- **All four transcripts ran on one tree, blob for blob:** `upgraded-set-count.txt` (15:46),
  `mutation.txt` (15:47), `gate-run.txt` (15:47) and `contract-run.txt` (15:49). That tree
  differs from the tree as it is committed only in this spec's `shape.md`, written to since, and
  in the four transcripts themselves, copied in after they ran. No path under `src/`, `tests/`,
  `scripts/` or `agent-os/standards/` differs, nor `README.md`, `CHANGELOG.md`, `pyproject.toml`
  or `uv.lock`. So the hashes `contract-run.txt` prints for the code and the tests are the
  merging tree's, which is what draft 4 cites.
- **The count and the mutation run were run again too,** though the owner asked for the gate and
  the contract run: the one more item changed `tests/unit/test_instrument.py` and
  `CHANGELOG.md`, and a transcript left as it was would print a blob the merging tree does not
  have. The count reads neither file and gave the same 42, 3 and 1.
- **Earlier runs were discarded.** Each of the three was first run before two lines were
  shortened to the line length, in `midi.py`'s docstring and in a comment of the new unit test,
  and before the README's last wording. The count had also been rerun once so that its "kept"
  label says only what the script observes, and the mutation run once to give pytest room to
  print each failure's reason. All three were run again on the tree as it then was, with the
  gate at 15:32 EST, and that set of four was replaced in turn by the runs for the one more
  item. No result differed between a replaced run and the kept one, the new mutant's two
  results aside, which are new; the times did.
- **The negative harness was not rerun.** No gate file changed, and no file was added, removed
  or renamed under a directory it copies (Decision 9).
- **Written after the gate's run:** this paragraph, "What the transcripts show", "One more item"
  and the retrospective's answer for it. Everything the first gate run was followed by (what was
  done with the drafts, the two issue numbers, the dated paragraph on draft 4 in the instrument
  spec's `shape.md`) was in the tree when the kept run was made. No file the gate reads has
  changed since it ran.

**Docs (step 7):** checked, and each reads true after the change.
- `README.md`, "Known limits": the issue #22 limit gives the counts, in round figures where a
  reader does not need the float.
- The module docstring of `instrument.py` (the issue #22 limit) and of `midi.py` (each note's own
  length), and the docstrings of `set` and `load_patch`. `load_patch`'s now agrees with
  `patch.py`'s and the README on how a value is taken.
- The docstrings of the three tests added or rewritten, and of the module constants `_MENDED`,
  `_REFUSED` and `_KEPT`.
- The docstring of `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest`, each
  figure in it now one the test asserts, and of the helper `_float32_toward_zero`. The same test
  in `tests/integration/test_vital_instrument.py` says "the float32 below it is nearer the display
  given" of the float32 below the one held, which is the curve's own, 3.6141903400421143: that is
  true, and that module was left as it is.
- `CHANGELOG.md`'s finding 5 line of the first revision, "measured with Vital's MPE setting off
  and on", was read against `overlap-probe-2.txt` and left: it is about each note's own length,
  which was measured both ways.
- Every vital standard that names what changed: `vital/instrument.md` and
  `vital/plugin-state.md`, corrected in the retrospective below. `vital/preset-tests.md`,
  `vital/measures.md` and `vital/parameter-map.md` were read and still read true.
- `CLAUDE.md` and `agent-os/product/mission.md` name nothing this changes.
- The first revision's `shape.md`, under its two dated notes.

**Version (step 8):** `CHANGELOG.md` under `[Unreleased]`:
- `### Changed` gains "Revision after the second review of PR 23", saying what A and B came to,
  which later items were taken and where the others go.
- The first revision's finding 1 bullet and the instrument's issue #22 limit under `### Added`
  give the counts.
- The same entry gains a bullet for the one more item, the float32 below.
- The version stays 0.0.1; no release is cut.

## Standards Retrospective

Step 9, always last, per `agent-os/standards/base/process/standards-retrospective.md`, written
from the shipped diff. Each edit is verified against the shipped code, tests and transcripts it
names, every cited test name checked to exist under `tests/`. These are their own change set,
apart from the feature's.

- `agent-os/standards/vital/instrument.md`:
  - **The keep rule's consequence is removed from it.** "So where Vital upgraded a preset's
    float … a set of the value `get` shows sets Vital back to the model's" was false of 4 of the
    46 floats. The rule itself reads as it did. Verified against `instrument.py` (`set`).
  - **"What a set of the value shown does to a float Vital upgraded is counted, and is not a
    rule"**, a new rule, with the counts, the three refused and the one kept named, and the
    lesson finding A taught: a consequence drawn from one float is stated of that float alone
    until it is counted over the recorded set, the exceptions written out. Verified against the
    two new tests, the Ah Eh Ee Oh test, `upgraded-set-count.txt` and MK1.
  - **"A test that compares something with a set makes the set from another value, and counts it
    at the plugin"**, a new rule, recording the pattern finding B's fix invented. Verified
    against the rewritten sample test and MD4 in `mutation.txt`.
  - "A value is taken one way" names the sample as it now is, 1,485 displays, and MD4.
  - The header names this revision's transcripts, and "the revision's" says which revision.
- `agent-os/standards/vital/plugin-state.md`:
  - **The channel rule says which MPE setting each thing was measured under.** The first
    note-off ending every note of its pitch, a note's own length on its own channel and a note
    alone sounding the same on any channel: off and on. Two voices of one pitch on one channel,
    and a note's own velocity on its own channel: off alone, the figures given. Verified against
    `overlap-probe.txt` and `overlap-probe-2.txt`, each figure read from the transcript. "Its
    level and centroid to the digits printed" became "its level within 0.000002": the levels
    printed differ in the sixth place.
- `agent-os/standards/index.yml`: the `vital:` entry `instrument` gains the two new rules. The
  `base:` section is untouched.
- Read and left as they are: `vital/preset-tests.md` (the new test reads `upgraded-floats.txt`
  through `_upgraded`, as the standard says), `vital/measures.md` and `vital/parameter-map.md`,
  whose "a count a reproduction's own definition forces to 0 is not evidence" is the same
  lesson, of a count, that the new test rule is of a test.

No pattern was used before it was written down: both new rules are written in this
retrospective from the tests that shipped. No rule was deliberately deviated from, and nothing a
standard points at moved or was renamed.

**The owner's approval, 2026-11-16:** "I approve the retrospective change set as described:
vital/instrument.md, vital/plugin-state.md and the index.yml entry." Nothing was added to it
after that.

**The one more item: no changes.** Asked of the diff of that item alone, the four questions:
- No pattern no standard covers. The neighbour is taken from primitives and written out, which
  is the rule the unit modules state for an expected value and `vital/instrument.md` cites for
  this very test ("its expected value from primitives"). `vital/parameter-map.md` already says
  `next_float32` "is the one way the package steps a float32", narrowing to float32 first; the
  test's helper does the same by the bits.
- No standard was wrong or stale. `vital/instrument.md`'s "it need not be the held value nearest
  the one given" was true, and the test it names now holds the part of it that nothing held: that
  the nearer float is one a set lands on.
- No deviation, and nothing a standard points at moved: the test keeps its name.
- What it teaches is not a missing rule but a rule not followed: a figure the docstring gave was
  worked out wrongly and never written out, so nothing pinned it. A rule that every figure in a
  test's docstring is asserted by the test was considered and is not written or proposed: it
  would be a base rule, `base/testing/tests`, and this is one instance of it in one test. If the
  owner wants it, it is a proposal for `patchbay-standards`, not an edit here.

No base standard is changed or proposed. The two new rules are about this instrument's keep rule
and its recorded floats. A general form of each exists, a claim over a set is counted over the
set and a test of two paths makes each from a state the other did not leave, but the owner held
that kind of rule on 2026-11-16 as a "project standard in vital/instrument.md until a second
adapter shows what is common", so they are written here and not proposed.

Proposals sent upstream: none
