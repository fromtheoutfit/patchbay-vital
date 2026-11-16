# Revision after PR 23's second review (issue #8, the instrument)

## Context

PR 23 (`VitalInstrument`, closes #8) has a second review on file: issue comment 6927191623 by the
owner, "Final-round review of `64863c6`: correctness first", 2026-11-16 19:44 UTC. It confirms six
checks and leaves two correctness findings (A and B) and nine "for later issues" items. This spec
checks A and B against the code, fixes them as the owner decided in shaping on 2026-11-16, takes
three of the later items, and sends the other six to two issues. The work stays on the PR's
branch. Nothing is committed, pushed or posted to the PR by an agent.

What shaping found, each checked by a run in memory with nothing written to the tree:

- **Finding A is real.** Of the 46 floats in `tests/data/upgraded-floats.txt`, a set of the value
  `get` shows reaches the plugin on 42, is refused as out of bounds on 3 (`flanger_center` on
  Touch Tone, Memory Leak and Oolacile Evil Dubstep Bass) and is kept on 1 (Oolacile Evil Dubstep
  Bass, `modulation_10_amount`: the model holds 0.19999998807907104, off the grid; Vital plays
  0.07499999552965164; a set would hold 0.20000004768371582). Counted against the map, not yet
  against Vital. No set can put Vital on an off-grid float, so no keep rule makes the claim true.
- **Finding B holds in a narrower form than its title.** On the test's sample (seed 23, 1,375
  comparisons) no set took the keep path, and the old test does fail a wrong load: MD1 of the
  earlier `mutation.txt` fails it on 243. It cannot fail only where the loaded float shows the
  display given, which needs a display two floats show. At the ends of the 55 groups there is
  one: `volume` at -80 dB (0.0 and 1.4e-45), which a uniform draw never reaches.
- The kept `load-and-set-sample.txt` compares `preset_of` with `to_preset` directly, so it stands.
- The claim is also in fromtheoutfit/patchbay#20's "Revised 2026-11-16" section.

## Decisions (each recorded in shape.md with the owner's words)

1. **Finding A: the claim is corrected; `set` is unchanged.** Each place that made the claim says
   what was counted: 42 mended, 3 refused as out of bounds, 1 kept, each named. Tests hold the
   kept case and the three counts and name issue #22.
2. **Finding B: the set is made from another value.** The test stays an instrument test of a load
   against a set. Its sample gains each group's two bounds. Its docstring says why the set is made
   from another value.
3. **B's evidence: both mutants against both forms, four results, one sentence each.** MD1 (the
   mutant the owner named) and the neighbour mutant, each against the test as at `64863c6` and as
   rewritten. shape.md records that the named mutant did not separate the forms and why. The
   reply states finding B as verified: the old test could fail, but not where two floats show
   one display.
4. **Three later items are fixed here:** the `load_patch` docstring, the MPE and velocity wording
   (reworded to what `overlap-probe-2.txt` shows; no new probe), and the sixteen-note MIDI test.
5. **The other six go to two issues, filed without a stop after the gate's clean run,** no
   attribution, each item as the reviewer stated it and marked unverified, each read back:
   - one on fromtheoutfit/patchbay-vital, the five `patch.py` cleanups; it blocks nothing;
   - one on fromtheoutfit/patchbay, the lost-step errors. Draft 4 (0.1.0) lists it with the
     others and stays held.
6. **Two issue bodies are revised in place in that same step,** each keeping its text with a dated
   paragraph added, no attribution, read back: patchbay-vital#22 and fromtheoutfit/patchbay#20.
7. **If the gate is not clean, nothing is filed or edited: stop and present.** The same if any
   figure in a draft below differs from the kept run.
8. **shape.md lists where each of the nine later items went.**
9. **No gate file changes,** and no file is added, removed or renamed under `scripts`, `src`,
   `tests` or `agent-os/standards`, so the negative harness is not rerun. If one has to be, it is
   rerun and this decision corrected.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/` with:

- `plan.md`: this plan.
- `shape.md`: the review quoted by finding, what shaping checked (the 42/3/1 table by key, the
  two in-memory runs on B), the owner's answers in his words, the decisions, the four drafts
  below, and a table of where each of the nine later items went.
- `standards.md`: the core tier plus `vital/instrument`, `vital/plugin-state`,
  `vital/parameter-map`, `vital/preset-tests`, `vital/measures`, `testing/tests` and
  `process/verification-gate`, as they read now.
- `references.md`: the earlier PR 23 revision spec (`2026-11-16-1334-…`: Decisions 1 and 2,
  `mutation.txt`, `load-and-set-sample.txt`, `overlap-probe-2.txt`) and the instrument spec
  (`2026-11-15-1448-…`: `probes-2.txt` section 9c, Draft 4).
- `verification/`; no `visuals/`.

## Task 2: Finding A, the tests

- `tests/unit/test_instrument.py`, beside
  `test_a_set_of_the_value_already_shown_on_a_float_a_set_lands_on_reaches_the_plugin`: a new
  test on the fake plugin. The model holds `modulation_10_amount` at the float32 below 0.2, the
  fake plugin is given 0.07499999552965164 as Vital's upgrade, and a set of the value shown
  calls no plugin, leaves the plugin's float and the model as they were, and publishes once,
  `old` equal to `new`. That the float is off the grid is worked out from primitives
  (`builders.what_a_set_holds`). The docstring names issue #22 and the data file's line.
- `tests/integration/test_vital_instrument.py`, beside
  `test_a_set_of_the_value_shown_on_an_upgraded_float_sets_vital_to_the_model_s`: a new test over
  the 11 presets and 46 floats `_upgraded` reads. For each float it sets the value `get` shows
  and sorts the outcome: refused (`ParameterRangeError`), mended (Vital holds the model's float)
  or kept (Vital still holds its upgraded float, the model unchanged). The three refused and the
  one kept are written out by preset and key, the kept one with its two floats, and the 42 is a
  named count. It skips where the presets are absent, as its neighbours do.
- **Stop and present** if Vital gives other counts than 42, 3 and 1.

## Task 3: Finding A, the texts (the standards' are Task 9's)

Each says what was counted, with the three refused and the one kept named:

- `src/patchbay_vital/instrument.py`: the module docstring ("What a set holds" and the issue #22
  limit) and the docstrings of `set` and `load_patch` (its last paragraph).
- `README.md`: the issue #22 limit.
- `CHANGELOG.md`: the earlier revision's finding 1 bullet.
- The earlier revision's `shape.md`, in place under a dated note with its text kept: the reply's
  item 1 and the paragraph drafted for fromtheoutfit/patchbay#20.

## Task 4: Finding B, the test

Rewrite `test_an_arbitrary_display_in_a_patch_holds_what_a_set_of_it_holds` in
`tests/unit/test_instrument.py`, keeping its name:

- The sample is the 25 uniform rounds as today (seed 23) and two more, each group's minimum and
  its maximum: 27 rounds of 55, 1,485 comparisons, counted.
- Each round loads the start preset (`Patch(instrument="Vital", values={})`), sets every display,
  and asserts the fake plugin received one set for each, so none was the keep rule's no-op. It
  then loads the same displays as a patch and compares each loaded float with the set's.
- The docstring says why the set is made from another value, and that the bounds are in the
  sample because `volume`'s minimum is a display two floats show.
- **Stop and present** if any comparison disagrees on the unmutated tree.

## Task 5: The three later items

- **`load_patch` docstring** (`instrument.py`): the sentence giving the old rule ("the nearest
  float32 the curve gives") is replaced by the load rule as `patch.py`'s docstring states it.
- **MPE and velocity wording**: `src/patchbay_vital/midi.py`'s docstring and the CHANGELOG's
  finding 5 line say what `overlap-probe-2.txt` measured and under which setting: each note's own
  length with MPE off and on; its own velocity with MPE off only, `velocity_track` at 100 %; two
  voices of one pitch on one channel with MPE off only. Each reworded sentence is checked against
  the transcript's section before it is written. (`plugin-state.md` and `instrument.md` carry the
  same claims and are Task 9's.)
- **Sixteen-note MIDI test** (`tests/unit/test_midi.py`): the expected stream is one literal
  tuple of all 32 messages with their times, in stream order, no loop.

## Task 6: Evidence runs

Each runs on a still tree once the code, tests and texts are final. Each is written outside the
tree and copied in afterwards, with the machine, Vital's and pedalboard's versions, and the tree
before and after by blob. Figures are quoted only from the run that was kept.

- `verification/upgraded-set-count.txt`, against the installed Vital: the 46 floats by preset and
  key, with the model's float, Vital's float before the set, the outcome, and Vital's float after;
  then the three totals.
- `verification/mutation.txt`, on a scratch copy outside the tree, with the earlier revision's
  harness (`mutate.sh`, `mutate.py`, as its `mutation.txt` prints them):
  - MD1 (a load always takes the curve's float32) and MD4 (where the curve's float32 shows the
    display, a load takes the float32 next above when it shows the display too), each against
    the sample test as at `64863c6` (`git show`) and as rewritten: four results, one sentence
    each. Expected: MD1 fails both; MD4 passes the old and fails the new at `volume` -80 dB.
    **Stop and present** if any of the four falls otherwise.
  - Each mutant's result on the whole unit suite, so the transcript says where else it is caught.
  - MK1 (the keep rule gone) must fail Task 2's new unit test; MM9 (a moved note takes the
    highest free channel) must fail the rewritten sixteen-note test.
- `verification/contract-run.txt`: core's thirteen against Vital with a shared host and with a
  fresh host per test, and over the fake plugin.

## Task 7: Docs and Version, recorded in shape.md

- **Docs (step 7):** `README.md`; the module and method docstrings changed in `instrument.py` and
  `midi.py`; the docstrings of the tests changed; `CLAUDE.md` and `agent-os/product/mission.md`
  (expected to name nothing this changes); every vital standard that names what changed.
- **Version (step 8):** `CHANGELOG.md` under `[Unreleased]`, `### Changed`: "Revision after the
  second review of PR 23", saying what A and B came to and which later items were taken. The
  version stays 0.0.1.

## Task 8: Drafts, in shape.md

The four texts below, as filed or added. Also, for the owner to post: a reply to the second
review, saying what A came to (the counts), B as verified in its narrower form, and where each of
the nine later items went.

### Draft 1: new issue on fromtheoutfit/patchbay-vital

> **Title:** The patch module: five cleanups from the second review of PR 23, unverified
>
> The second review of PR 23 (fromtheoutfit/patchbay-vital#23, "Final-round review of `64863c6`",
> 2026-11-16) listed these under "For later issues (not correctness)". Each is given as the
> reviewer stated it and is **unverified**: a lead to check against the code, not a confirmed
> defect. It blocks nothing.
>
> - **`_Entry`** (`patch.py:107`): it re-lists the metadata fields by hand while `_whole` reads
>   them through `METADATA`. A field added to `VitalPreset` would raise a bare `AttributeError`
>   from `load_patch` instead of `PatchRefusedError`.
> - **`_float_of`** (`patch.py:154`): it copies `MappedParameter.to_preset`'s first step, so a
>   later change to how `to_preset` bounds or rounds has to be made twice.
> - **The merge of a preset's floats:** `split_modulations` followed by
>   `{**settings.values, **slot_floats}` is written three times (`patch.py:198, 283, 388`).
>   `instrument._held`/`_holding` reach the same floats a fourth way.
> - **`_entry_text`** (`patch.py:184`): it repeats `start._section`'s JSON settings, so
>   `_section`'s claim to be "the one writer of nested JSON" is already false.
> - **`check_loadable`** (`patch.py:399`): it decodes the wavetables, LFOs and sample sections a
>   second time on every `load_patch`, after `VitalPreset`'s validator has already parsed them.
>
> The line numbers are the review's, at `64863c6`. The last was finding 7 of the first review,
> declined there on a measurement
> (`agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/verification/check-cost.txt`).
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. Each item is checked against the code first,
> then fixed or declined with its reason. CHANGELOG; gate green. No commit, pull request or push
> by an agent.

### Draft 2: new issue on fromtheoutfit/patchbay

> **Title:** Instrument: what an instrument does once it has lost step with its device
>
> `Instrument`'s docstrings at `eddba95` name the errors a call raises. `set`:
> "ParameterNotFoundError, UnitMismatchError or ValueOutOfRangeError when the id, the unit or the
> value is not one the instrument takes". `render`: "RenderFailedError, publishing nothing, when
> nothing usable can be rendered". `load_patch`: "PatchRejectedError when the instrument cannot
> load all of it, changing nothing." Nothing says what an instrument does once it can no longer
> answer for its device.
>
> ## The case
>
> patchbay-vital's `VitalInstrument` holds a model and drives a hosted plugin. When the plugin
> refuses a load, the instrument sends the model's own preset again and the call is refused as
> `PatchRejectedError`, nothing changed. When the plugin refuses that too, its state is unknown
> while the model holds the preset before. The instrument has lost step with its device, and
> "changing nothing" cannot be claimed.
>
> What it does then, at `64863c6` on the branch of fromtheoutfit/patchbay-vital#23:
>
> - `load_patch` raises the adapter's `PluginStateError`, which is not a `PatchRejectedError`,
>   naming both refusals and saying to build a new instrument.
> - Every later `set`, `load_patch` and `render` raises `PluginStateError`, the plugin not called
>   and nothing published. That error is outside the types the protocol names for `set` and
>   `render`.
> - The refusal comes ahead of the usual checks: a `set` of an unknown id is refused with it, not
>   with `ParameterNotFoundError`.
> - `get`, `patch` and `parameters` go on answering from the model, which the device may no
>   longer match.
>
> The second review of that pull request raised this as worth an issue against core's contract.
> It is given as the reviewer stated it and is **unverified** beyond the docstrings quoted.
>
> ## The question
>
> Should core's contract say what an instrument does in that state? For instance:
>
> - whether it may refuse every later call, and with which error, one core names, so a caller can
>   catch it without knowing the adapter;
> - whether that refusal comes before or after the checks the protocol already names;
> - whether `get` and `patch` may go on answering from a model the device no longer matches.
>
> No contract test reaches the state: it takes a device that refuses twice.

### Draft 3: a paragraph added to fromtheoutfit/patchbay-vital#22, its text kept

> ## Revised 2026-11-16
>
> A set of the value `get` shows reaches the plugin wherever the model holds a float a set lands
> on (the revision after the first review of PR 23). Counted over the 46 floats above, on Vital
> 1.6.4 through pedalboard 0.9.26 on arm64
> (`agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/verification/upgraded-set-count.txt`,
> held by the test Task 2 adds, named here once it exists):
>
> - **42 are mended by that set.** Vital then holds the float the model shows; for a key the file
>   lacks that is the parameter's default.
> - **3 are refused as out of bounds:** `flanger_center` on Touch Tone, Memory Leak and Oolacile
>   Evil Dubstep Bass. The file's value (0.0, 0.0 and -15.359999656677246) shows a display outside
>   the parameter's bounds, which `set` does not take.
> - **1 is kept:** `modulation_10_amount` on Oolacile Evil Dubstep Bass. The model holds
>   0.19999998807907104, a float no set lands on, so a set of its own display keeps it and the
>   plugin is not called. Vital goes on playing 0.07499999552965164. This is the case no set can
>   reach: nothing the host can set puts Vital on the model's float, and a set of any other
>   value and back holds the neighbour, 0.20000004768371582.
>
> So a set of the value shown mends 42 of the 46, and the four that remain are this issue's to
> decide, whichever option is chosen.

### Draft 4: a paragraph added to fromtheoutfit/patchbay#20, its text kept

> ## Revised 2026-11-16, after the second review of patchbay-vital's PR 23
>
> One sentence of the section above said more than was counted: "On any other float it reaches
> the plugin, so the plugin goes back to the model's float after Vital upgrades a preset older
> than it." Counted over the 46 floats Vital upgrades on the presets it installs
> (fromtheoutfit/patchbay-vital#22): a set of the value `get` shows puts Vital back on the
> model's float for 42. 3 show a value outside their parameter's bounds, which `set` refuses. 1
> holds a float no set lands on, so the set is kept and Vital stays on its upgraded value:
> `modulation_10_amount` on Oolacile Evil Dubstep Bass, 0.19999998807907104 in the model and
> 0.07499999552965164 played. The keep rule and this issue's question are unchanged. The
> evidence is `verification/upgraded-set-count.txt` in
> `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/` on patchbay-vital's branch
> for its issue #8.

## Task 9 (FINAL): Verification gate

The standards retrospective's edits are made first and the gate is run once after them and after
every other transcript, as the earlier revision did; the three judgment steps are then recorded.

1. `bash -n` on every shell script under `scripts/` as git lists them, at a work-tree top that
   is the repository root, with no tracked file a `.gitignore` ignores.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check`.
3. `uv run --locked ruff check --config pyproject.toml`.
4. `uv run --locked mypy --config-file pyproject.toml`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`, with Vital and its presets installed.
6. `scripts/sync-standards.sh --check` against `../patchbay-standards` at the pinned commit.

`scripts/gate.sh` runs steps 1–6 as one command; its run is kept as `verification/gate-run.txt`.
Then, recorded in shape.md in this order:

7. **Docs**, as Task 7.
8. **Version**, as Task 7.
9. **Standards retrospective**, per `base/process/standards-retrospective.md`, from the shipped
   diff, each edit verified against the shipped code and tests it names, every cited test name
   checked to exist. Its own change set, listed apart from the feature's:
   - `vital/instrument.md`: the keep rule's consequence with the counts and the new tests; the
     load rule's evidence (the rewritten sample test, MD4); the note rule's MPE sentence; the
     header's transcripts.
   - `vital/plugin-state.md`: the MPE and velocity bullet, reworded to `overlap-probe-2.txt`.
   - `vital/preset-tests.md` and `index.yml`'s `vital:` entries, only where one no longer reads
     true. The `base:` section is untouched.
   - Any base proposal is presented with AskUserQuestion and filed at the owner's word or marked
     declined. `Proposals sent upstream:` is recorded either way.

If a step fails, fix the cause and rerun from step 1. Never bypass a step, and never clear a
saved Hypothesis example.

## Task 10: After the gate's clean run

Only if `scripts/gate.sh` exited 0 and every figure in the four drafts matches the kept run;
otherwise stop and present, with nothing filed or edited.

- Check both repositories' open issues for one that already says it, then file Draft 1 with
  `gh issue create --repo fromtheoutfit/patchbay-vital` and Draft 2 with
  `gh issue create --repo fromtheoutfit/patchbay`, bodies from files.
- Add Draft 3 to patchbay-vital#22's body and Draft 4 to patchbay#20's, the existing text
  fetched and kept whole.
- Read each of the four back with `gh api` and compare it with the text sent.
- Revise Draft 4 of the instrument spec (the 0.1.0 proposal) in place, under a dated note: it
  lists the new core issue with the others and cites this spec's contract run. It stays held.
- Record in shape.md what was done, the issue numbers, and where each of the nine went.
- Report the feature's change set and the retrospective's apart, for the owner to commit.

## Files changed

- `src/patchbay_vital/instrument.py`, `src/patchbay_vital/midi.py`: docstrings only.
- `tests/unit/test_instrument.py`, `tests/unit/test_midi.py`,
  `tests/integration/test_vital_instrument.py`.
- `README.md`, `CHANGELOG.md`.
- `agent-os/specs/2026-11-16-1509-…/` (new); the earlier revision's and the instrument spec's
  `shape.md`, each under a dated note.
- Retrospective, apart: `agent-os/standards/vital/instrument.md`, `plugin-state.md`, and
  `preset-tests.md` and `index.yml` if needed.

## Verification, end to end

- The gate exits 0 with Vital and its presets installed, in one kept run after every other edit.
- `upgraded-set-count.txt` shows 42 mended, 3 refused and 1 kept on Vital, and the integration
  test holds the same.
- `mutation.txt` shows the four results on B and no surviving mutant among MK1 and MM9.
- The thirteen contract tests pass against Vital both ways and over the fake plugin.
- Each of the four GitHub texts reads back as sent, and shape.md accounts for all nine later
  items.
