# Revision after PR 23's review (issue #8, the instrument)

## Context

PR 23 (`VitalInstrument`, closes #8) has one review on file: issue comment 6922873382 by the
owner, covering 63ad5ae. It lists 17 findings, deduplicated and **unverified** ("leads to check").
This spec checks each one against the code and against core at `eddba95`, and fixes, declines or
probes each as the owner decided in shaping on 2026-11-16. The work stays on the PR's branch,
`feature/8-…-spec-b-of-7`. Nothing is committed, pushed or posted by an agent.

Core was read during shaping (in `.venv/…/patchbay`, eddba95). Two of the owner's stop conditions
fired and were answered:
- `Patch`'s docstring says "a value for each parameter". No contract test checks it. Because of
  that, `values` stays complete and the load rule is made precise (Decision 2), rather than moving
  off-grid floats to `opaque`.
- `FakeInstrument` defines what overlapping notes mean ("a sine per note … cut at the note's
  end", summed), so each note sounds for its own length. The earlier answer on finding 5 (cut the
  earlier note) is withdrawn, and Vital is probed first.
- Core's contract says nothing about an instrument staying usable after an error, so finding 4
  goes ahead as decided.

## Decisions (each recorded in shape.md)

1. **Finding 1, the keep rule narrowed.** In `set`, `held = record.to_preset(value.value)`. The
   set is skipped (model and plugin untouched, event still published, `old == new`) only when
   the value equals the display shown **and** `held` is not the float the model holds, i.e. the
   held float is one no set lands on. Otherwise `host.set(scale.to_normalized(held))` is called
   and the model updated. So `set(osc_1_stack_style, 9)` on an upgraded preset (model 9, plugin
   10) reaches the plugin.
2. **Findings 2 and 3, one load rule.** `patch._float_of(record, display)`:
   - **Linear scale:** let `c` be the curve's float32 for the display, clamped to the scale. If
     `record.to_display(c) == display` exactly, the value names `c` and `c` is stored. Otherwise
     `record.to_preset(display)` is stored, as a set would hold it.
   - **Indexed scale:** `record.to_preset` as today. On an indexed scale the curve's float32 for
     a value between steps shows that value, so the linear branch would break Decision 9 of #8
     (`chorus_voices` 6 holds 8 on set and load). Stated as how the owner's rule applies there.
   - The same function is the "back" of `patch_of`'s carrying check. Every float carried today
     (`c == held`) is still carried, so `values` can only grow. The start preset keeps Vital's
     defaults, all 903 stay in `values`, and #8's Decision 2 stands with this rule added.
   - The one case where load and set differ: a value that is exactly the display of an off-grid
     float is restored by a load and not by a set. That is fromtheoutfit/patchbay#20's case, and
     it is tested and cross-referenced there.
   - **Stop and present with the counts** if the exact-naming test cannot be made sound (for
     example a display two floats show breaks the round trip), or if any float carried today
     leaves `values`.
3. **Finding 4, a lost step.**
   - The setup: the plugin refuses the new text and then refuses the rollback too.
   - `load_patch` then raises the package's `PluginStateError`, naming both refusals and saying
     to build a new instrument. The instrument records that it has lost step.
   - From then on `set`, `load_patch` and `render` raise `PluginStateError`, naming the earlier
     failure and saying to build a new instrument. That check comes before any other. The plugin
     is not called and nothing is published.
   - `get`, `patch`, `parameters` and `name` still answer from the model. Their docstrings say
     the plugin no longer matches it.
   - The 0.1.0 draft lists this under the adapter's limits and asks core nothing new.
4. **Finding 5, probe first and follow the fake.**
   - If Vital gives each of two overlapping same-pitch notes its own length with today's bytes,
     the bytes stay and finding 5 is recorded as not reproduced.
   - If the first note-off releases both, **stop and present** what the probe found, including
     whether another channel gives each note its own voice.
   - Either way, `midi.py` says and tests what two notes of one pitch struck on the same sample
     do, with the expected bytes written out.
5. **Finding 6.** Versions are compared with trailing `.0` parts dropped, so `1.6.4.0` equals
   `1.6.4`. A plugin version that is not digits and dots refuses every preset by name, rather
   than skipping the comparison.
6. **Finding 7, declined.** The re-decode is measured against the two loads on the largest
   installed preset (`check-cost.txt`). A load of a 10 MB preset takes seconds already.
7. **Finding 8, fixed.** The `Patch` is cached beside `_preset`, and dropped wherever `_preset`
   is replaced.
8. **Finding 9, in part.** `_clipping` takes peaks as `np.maximum(audio.max(0), -audio.min(0))`,
   with no `np.abs` copy. Declined: the second `isfinite` (core's validator is core's; ours names
   the refusal as `RenderRefusedError` first), and passing the length to `midi_of` (it is O(1)
   arithmetic, not a scan of the buffer).
9. **Findings 10–14, fixed.**
   - `format.py` exposes `METADATA` and a public "writes the same float" helper, and `patch.py`
     uses both (10, 11).
   - `start.py` writes strings and objects through `format`'s writers and keeps its own sorted
     `json.dumps` only for the nested sections, which `format` never writes (12).
   - `preset.py` gains one helper beside `SLOT_KEY` that returns a slot key's slot and field.
     `instrument._slot_field` goes, and `_held`/`_holding` use the helper (13).
   - `check_loadable` and its helpers move to `patch.py` and are re-exported from the package
     root, with the public-surface test updated (14).
10. **Findings 15 and 16, fixed.** The known limits say the first three each wait on an issue
    (#20, #21, #22) and the fourth, the double load, is a measured workaround that no issue owns.
    The CHANGELOG's "all three" becomes four. The `files.py` docstring says census writes three
    files, `start.vital` among them.
11. **Finding 17, declined.** The size of these transcripts is being decided in
    fromtheoutfit/patchbay-standards#41. This spec's pair (about 26.6k lines each) is added to
    #41's evidence in place, with a "Revised 2026-11-16" line, since this is the third review to
    raise it. The text is presented first and posted after the gate's clean run.
12. **For core.**
    - Draft 4 (0.1.0, held until the PR merges) is revised in the instrument spec's shape.md
      with a "Revised 2026-11-16" paragraph. It cites this spec's contract runs and finding 4's
      limit.
    - A new draft 5 asks whether "a value for each parameter" allows the 35 floats the installed
      presets carry in `opaque` (out of range, or no parameter's).
    - A comment cross-referencing the load/set exception (Decision 2) is drafted for
      fromtheoutfit/patchbay#20.
    - All of these are presented whole and filed or posted only at the owner's word, after the
      gate is clean.
13. **No gate file changes.** No file is added, removed or renamed under `scripts`, `src`,
    `tests` or `agent-os/standards`, so the negative harness is not rerun. If one has to be, it
    is rerun and this decision corrected.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/` with:
- `plan.md`: this plan.
- `shape.md`: the review quoted by finding, the core checks and both stops with the owner's
  words, the decisions above, and the 22 start-preset off-grid keys listed by key (from
  `off-grid-count.txt`). Also a note for the semantics-data spec: a patch read without an
  instrument shows a parameter's display, not the float.
- `standards.md`: the core tier plus vital/instrument, vital/parameter-map, vital/measures,
  vital/plugin-state, vital/preset-file, vital/preset-tests, testing/tests, python/events and
  process/verification-gate, as they read now.
- `references.md`: the instrument spec (`2026-11-15-1448-the-instrument/`: Decisions 2, 4, 7–9,
  13, 17, 24–29; `off-grid-count.txt`, `carrying-count.txt`, `mutation.txt`, `probes.txt`) and
  the PR 19 revision spec (`2026-11-15-0811-…`) as the shape of a review round and its reply.
- `verification/`, no `visuals/`.

## Task 2: Probe overlapping notes on Vital (finding 5), before any MIDI change

The probe is a throwaway script in the scratchpad. It renders on the start preset at 48 kHz and
measures each note's length as windowed RMS (Hann windows, bounds as named constants) for:
- the same pitch overlapping (A 0–2 beats, B 1–3 beats);
- the same pitch struck on the same sample with different lengths and velocities;
- a control of two different pitches.

The transcript, `verification/overlap-probe.txt`, gives the machine, Vital's and pedalboard's
versions, and nothing in the tree is touched while it runs. If both notes are released at A's
end, stop and present (Decision 4).

## Task 3: The keep rule and the load rule (findings 1–3)

- `src/patchbay_vital/instrument.py` `set`: the narrowed condition (Decision 1).
- `src/patchbay_vital/patch.py` `_float_of`: the linear exact-naming branch (Decision 2). Its
  docstring, the module docstring, `load_patch`'s and `patch`'s docstrings, and the README say
  what `values` holds and how a value is taken.
- Unit tests (`tests/unit/test_instrument.py`, `tests/unit/test_patch.py`), expected values
  worked out from primitives:
  - a set of the shown display on an off-grid float calls no plugin and changes nothing;
  - a set of the shown display on an on-grid float reaches the fake plugin with its normalized
    value;
  - a whole patch restores each float it carried;
  - an arbitrary display loads to what a set holds;
  - a display that is exactly an off-grid float's is restored by a load and not by a set,
    naming fromtheoutfit/patchbay#20.
- Integration test (`tests/integration/test_vital_instrument.py`, skipped where the installed
  presets are absent): on the upgraded preset where the model holds `osc_1_stack_style` 9 and
  Vital plays 10, `set(…, 9)` leaves Vital holding 9, read through `host.state()`.
- Counts, as transcripts:
  - `carrying-count.txt` again: the fixture, the start preset and the 75 installed presets, with
    the floats carried in `values` against today's 59,442, those restored exactly, and the byte
    round trip through the patch and its JSON. Also `PatchLoaded.parameter_count` for each form
    of patch (whole, values alone, with floats in `opaque`).
  - `load-and-set-sample.txt`: a labelled sample of arbitrary displays per continuous group, with
    size, generator and seed, showing that load and set leave the same float.
  - Stop if Decision 2's stop applies.

## Task 4: A lost step (finding 4)

`instrument.py`: the double refusal raises the package's `PluginStateError` and marks the
instrument. A check at the top of `set`, `load_patch` and `render` refuses any later call. The
docstrings of all six methods say what Decision 3 says. Fake-plugin tests replace
`test_a_plugin_that_refuses_the_model_s_own_text_too_is_the_host_s_error`:
- the error and its chain;
- each of `set`, `load_patch` and `render` refused afterwards, with the plugin not called and
  nothing published;
- `get` and `patch` still answering from the model.

## Task 5: MIDI (finding 5), as the probe decides

The `midi.py` docstring drops "as MIDI has it", states what Vital was measured to do, and says
what two same-pitch notes on one sample do. `tests/unit/test_midi.py` writes the expected bytes
out for overlap, same-sample and the control. An integration measure of B's length on the start
preset, under a window with a named tolerance whose comment cites the probe, goes in
`tests/integration/test_vital_instrument.py`.

## Task 6: Versions, caching and clipping (findings 6, 8, 9)

`check_loadable`'s comparison and the refusal of a plugin version that cannot be compared
(Decision 5). The cached `Patch` (Decision 7). The `_clipping` peaks (Decision 8). Unit tests:
- `1.6.4.0` is taken;
- `1.6.5` is refused;
- a map version of `1.6.4b` refuses by name;
- `patch()` called twice gives the same object, and a new one after a set or a load;
- the clipping tests that exist still pass unchanged.

`verification/check-cost.txt` records finding 7's decline.

## Task 7: One definition each (findings 10–14)

As Decision 9, in `format.py`, `preset.py`, `start.py`, `patch.py`, `instrument.py` and
`__init__.py`. The import direction stays `errors → … → format → … → patch → instrument`, with
`patch.py` still free of pedalboard. Tests that import `check_loadable` from `instrument`
(`tests/unit/test_instrument.py:72`, `tests/integration/test_vital_instrument.py:56`) import it
from where it now lives. `test_package.py` holds the root surface, and the census test still
regenerates all three files byte for byte.

## Task 8: Docs (findings 15, 16)

The `instrument.py` known limits, `CHANGELOG.md` (the limit count, plus this revision under
`[Unreleased]`), the `files.py` docstring, and the README where Decisions 1–5 change what it says.

## Task 9: Evidence runs

All of these run on a still tree, once the code is final, with figures quoted only from the run
that was kept:
- `contract-run.txt`: core's thirteen contract tests against Vital twice, with a shared host
  and with a fresh `VitalHost` per test.
- `mutation.txt`: one mutant per rule changed here. That covers the narrowed keep condition, each
  branch of the new `_float_of`, the lost-step check, the version padding and the fail-closed
  version, and the patch cache's invalidation. Each mutant must fail a named test.

## Task 10: Drafts, for the owner

In shape.md, each shown whole and filed or posted only at the owner's word, after the gate's
clean run:
- draft 4's revision;
- draft 5 for core;
- the fromtheoutfit/patchbay#20 comment;
- the patchbay-standards#41 evidence revision;
- a reply to PR 23, one line per finding (Fixed, Declined or Not reproduced, with why), for the
  owner to post.

## Task 11 (FINAL): Verification gate

1. `bash -n` on every shell script under `scripts/` as git lists them, at a work-tree top that
   is the repository root, with no tracked file a `.gitignore` ignores.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check`.
3. `uv run --locked ruff check --config pyproject.toml`.
4. `uv run --locked mypy --config-file pyproject.toml`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`, with Vital installed.
6. `scripts/sync-standards.sh --check` against `../patchbay-standards` at the pinned commit.

`scripts/gate.sh` runs steps 1–6 as one command, and its run is kept as
`verification/gate-run.txt`. Then the three judgment steps, recorded in shape.md in order:
7. **Docs:** README, CHANGELOG, the module and method docstrings changed, and every vital
   standard naming them, read true.
8. **Version:** under `[Unreleased]` in `CHANGELOG.md`; no version bump.
9. **Standards retrospective:** per `base/process/standards-retrospective.md`, against the
   shipped diff.
   - Likely project edits: `vital/instrument.md` (the keep rule's narrowed form, the load rule,
     the lost step, overlapping notes) and `index.yml`'s `vital:` entries. Each is listed as its
     own change set.
   - Any base proposal is presented with AskUserQuestion and filed as one issue at the owner's
     word, or marked declined.
   - `Proposals sent upstream:` is recorded either way.

If a step fails, fix the cause and rerun from step 1. Never bypass a step, and never clear a
saved Hypothesis example.

## Verification, end to end

The gate is green with Vital installed, and the 13 contract tests pass against Vital both ways.
The carrying recount shows every float the 77 texts carry restored exactly, and 77 of 77 byte
for byte. The sample shows load and set agree on arbitrary displays. Every mutant fails a named
test. The stack_style test shows Vital holding 9 after the set. The overlap probe and its
integration measure agree with the fake's meaning, or the work has stopped and been presented.
