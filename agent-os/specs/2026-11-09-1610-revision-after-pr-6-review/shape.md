# Revision after the Review of PR 6 — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered three design questions and one confirmation of Steps 2 to 5.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The owner's review of PR 6 at `6d7f747`: sixteen findings, ten correctness and six cleanup, each
checked against the code, the tools and the real files while shaping, all of which hold, #6's
evidence being weaker than stated. On the same branch, so PR 6 carries it. CHANGELOG entry, gate
green, `verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** the review's sixteen findings.
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/ownership` and `testing/tests`. Snapshot at `e31f7db`
  in `standards.md`.

## Decisions

1. **The scope is the review**:
   https://github.com/fromtheoutfit/patchbay-vital/pull/6#issuecomment-6751377414.
2. **A new spec folder on this branch.** The reviewed folder stays its record.
3. **#6: `license` stays refused**, at the owner's word. The string sits among config-file strings
   (`errors.txt`, `ttwt_language`, `check_for_updates`), not beside the preset keys; 0 of 77 presets
   hold it; the pack catalogue has no such field. Known means Vital has been seen to write it.
4. **#9: only what follows the object is refused**, at the owner's word, with `"preset_name":null`.
   Interior whitespace still loads and is documented as normalized. Neither that nor the stricter
   option makes every accepted text reproducible: `1.50` and unsorted keys normalize either way.
5. **#14 is declined**, at the owner's word: `json.decoder.WHITESPACE` is outside `json`'s `__all__`,
   so `_skip_space` stays.
6. **#5 is fixed here**, by `_PicklableMappings`: pickled state holds each proxy as a dict, and a deep
   copy is a shallow one, everything held being immutable. **Corrected during the work:** the
   approved plan covered `__deepcopy__`, but pydantic deep-copies field by field when `model_copy`
   is given an update, so `model_copy` drops `deep` too. A test caught it.
7. **#3:** `dump` writes a temporary beside the target, keeps its mode, writes through a symlink, and
   renames over it. The temporary is removed on failure.
8. **#4:** `diff` compares floats as written, so `is_empty` means the two presets write the same
   bytes. Model `==` stays Python's, where `0.0 == -0.0`.
9. **#11:** `settings` and `modulations` are walked by span in the first pass. The model's own
   validation stays, so its guarantee does not depend on who built it. On 6 MB, `loads` went from
   162 ms to 106 ms; one `json` decode is 51 ms.
10. **#15: `tests/unit/builders.py`**, a plain module of the shared strategies and builders, at the
    owner's word. `tests/unit/conftest.py` would collide with harness case q, and a function-scoped
    fixture fails hypothesis's health check under `@given` (probed). `base/testing/tests.md` does not
    place helpers in `conftest.py`, so the owner's condition for a proposal does not arise.

## The sixteen findings

| # | Finding | Outcome |
|---|---|---|
| 1 | Surrogate metadata loads but cannot be saved | Fixed: refused by the model |
| 2 | A NUL in a path leaks `ValueError` | Fixed |
| 3 | A failed `dump` destroys the file | Fixed |
| 4 | `diff` misses `0.0` against `-0.0` | Fixed |
| 5 | Presets cannot be pickled or deep-copied | Fixed here; proposed upstream |
| 6 | `license` missing from top-level keys | Left refused (Decision 3) |
| 7 | Sections accept `NaN` and stray whitespace | Fixed |
| 8 | A format change reported as malformed | Fixed |
| 9 | `loads` accepts text it changes on write | Fixed for what follows the object and `null` |
| 10 | `join_modulations` leaks core's error | Fixed |
| 11 | Sections decoded three times | Now twice (Decision 9) |
| 12 | `SLOT_KEY` restates the field tuples | Fixed |
| 13 | `_METADATA` restates the model | Fixed |
| 14 | `_skip_space` restates the stdlib | Declined (Decision 5) |
| 15 | Duplicated test helpers and serializers | Fixed (Decision 10) |
| 16 | Redundant mask and constant | Fixed |

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `tests/` changing under what it copies
- `base/process/standards-retrospective` — the project standard this changes, and a base proposal
- `base/process/ownership` — the owner commits
- `base/testing/tests` — where shared helpers live

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/2-the-vital-format-parse-write-diff-and-round-trip-every-factory-preset`,
`verification/gate-run.txt`, 242 tests, the 75 round trips among them and not skipped. No gate file
changed; `tests/` changed under a directory the harness copies, so it was rerun:
`verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
`verification/ci-negative-test.txt` `3 runs, 0 unexpected`. `verification/old-behaviour.txt`: this
revision's tests against the code as reviewed at `6d7f747`, 31 failing, each a behaviour changed by
findings 1, 2, 3, 4, 5, 7, 8, 9 or 10. CI has no presets, so the integration tests skip there, and
the hosted run of this revision exists only after the owner's push.

**Docs (step 7):** checked and reads true against the shipped files:
- `src/patchbay_vital/format.py`'s module docstring says what may follow the object and that interior
  whitespace is normalized; `loads`, `dump` and `join_modulations` name what they raise.
- `src/patchbay_vital/preset.py`: `_PicklableMappings` says why; `PresetDiff.is_empty` says "write the
  same bytes", which the README's example relies on.
- `tests/unit/test_format.py`: the docstring finding 1 proved false is corrected.
- `README.md`, `CLAUDE.md`, `agent-os/product/tech-stack.md`, unchanged: this revision touches none
  of what they describe.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** a read-only mapping that must still pickle (below). Shared test
   builders as a plain module also has no rule, and by the owner's condition is not proposed:
   `base/testing/tests.md` does not place helpers in `conftest.py`.
2. **A standard wrong or stale:** `base/python/models.md` holds a mapping as a `MappingProxyType` and
   says nothing of what that costs (below). `vital/preset-file.md` described the unknown-key rule this
   revision changes, and is corrected.
3. **A deliberate deviation:** none.
4. **A pointer moved:** none.

The retrospective's own change set, to commit apart from the fixes:

- `agent-os/standards/vital/preset-file.md` — the unknown-key rule now holds wherever the key is and
  whatever its value's type; `license` noted as not known; what may follow the object; `dump` whole
  or not at all; two presets the same when they write the same bytes. Verified against `format.py`
  and the tests each entry names.
- `agent-os/standards/index.yml` — the `vital:` section's `preset-file` description follows it; the
  `base:` section is the sync's and unchanged.

**Which side each rule fell on, and why.** The rules about what Vital's file may hold are Vital's,
and stayed in `vital/preset-file`. "A model holding read-only mappings must still pickle and
deep-copy" is about any model on the base, core's `Patch` first among them, so it went upstream.

Proposals sent upstream: fromtheoutfit/patchbay-standards#33

### Standards retrospective (proposed, base)

- `base/python/models.md`, "Frozen inside" — a model holding read-only mappings must still pickle and
  deep-copy: the pickled state holds each proxy as a dict, and a deep copy is a shallow one, including
  through `model_copy`. Core's `Patch` has the same defect. Verified against
  `src/patchbay_vital/preset.py` (`_PicklableMappings`), `tests/unit/test_preset.py`
  (`test_a_preset_can_be_pickled`, `test_a_preset_can_be_deep_copied`,
  `test_updating_a_deep_copy_leaves_the_original_alone`) and `verification/old-behaviour.txt`.
  Proposed, not applied; filed as fromtheoutfit/patchbay-standards#33.
