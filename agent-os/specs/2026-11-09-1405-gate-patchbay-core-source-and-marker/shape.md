# The patchbay-core Source and the Integration Marker — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`, while
shaping issue #2. The owner answered that spec's discovery questions and this spec's Steps 2 to 5.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #4: what issue #2 needs from the sections of `pyproject.toml` that only a gate spec may change.
`patchbay-core` as a dependency with its range and a `[tool.uv.sources]` pin, the `integration`
marker registered, `uv.lock` re-locked, and a negative test for each. No adapter code. CHANGELOG
entry, gate green, `verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** issue #4, from the owner's answer while shaping #2: "shape the small gate spec
  now (the `[tool.uv.sources]` pin to patchbay at dd2bcad with its range, and the integration
  marker), land it, then resume #2 on top."
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged; `tech-stack.md`'s `patchbay-core` line is
  corrected.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/ownership` and `testing/tests`. Snapshot at `e31f7db`
  in `standards.md`.

## Decisions

1. **The scope is issue #4**: https://github.com/fromtheoutfit/patchbay-vital/issues/4.
2. **`patchbay-core>=0.0.1,<1`** in `[project] dependencies`, the version the gate runs to the next
   major (`base/python/toolchain.md`, "Dependencies"). What it does: the models, the errors and the
   `Instrument` protocol every adapter plugs into, `PatchbayModel`, `PresetKey` and `PatchbayError`
   first. Why the standard library cannot: it is this family's own contract. License: MIT. **uv
   does not check this range against a git source:** a range the pinned commit cannot meet,
   `>=9,<10`, syncs and locks with exit 0, and `uv.lock`'s `requires-dist` holds the source and no
   specifier (`verification/probes.txt`, P1, P4 and P4b). So the gate proves the commit and not the
   range; the range is what the built wheel declares (P6).
3. **`[tool.uv.sources]` pins it to `https://github.com/fromtheoutfit/patchbay` at
   `dd2bcad69dadeb38c6e1e660b2e0ddced13861eb`**, the head of its `main`, read with
   `git rev-parse main` and never from its checkout, which sits on a fix branch. It is not on PyPI
   and has no tag or release. The repository is public, so CI's `uv sync --locked` needs no change
   to the workflow.
4. **Deviation, at the owner's direction:** `base/python/toolchain.md` adds a dependency "by the spec
   that uses it, never ahead of it"; this one arrives one spec early, the owner having asked for the
   pin "with its range". uv would have taken the source alone, ignoring it until a dependency names
   it (`verification/probes.txt`, P5), so the deviation is a choice and not a necessity. Recorded and
   not proposed: the retrospective's proposal removes the cause.
5. **The marker's text says what #2 does with it**: it needs the presets of an installed Vital, is
   skipped with its reason where they are absent, and is run by the gate where they are present.
   patchbay's text differs on purpose, its integration tests not being selected by its gate.
6. **Limit:** the wheel carries the range but not the source, so installing it elsewhere needs
   `patchbay-core` on an index. Nothing installs it elsewhere yet.
7. **Negative test y has no case for a value pytest refuses, because pytest refuses none:** `markers
   = 3` fails exactly as an absent entry does, naming the unregistered marker, and a bare string
   registers it (`verification/probes.txt`, P7 to P10). The plan made that third run conditional on
   finding one. The file-unparsable case is m's.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `tech-stack.md`'s `patchbay-core` line.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — a gate spec, a pin and a rule-set value each shown read
- `base/process/standards-retrospective` — the owner's upstream proposal
- `base/process/ownership` — the owner lands this spec, and #2 waits for it
- `base/testing/tests` — where the marker's test lives in the harness's copy

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/4-gate-the-patchbay-core-source-and-the-integration-marker`, `verification/gate-run.txt`.
Gate files changed, so the whole harness was rerun: `verification/gate-negative-tests.txt` ends
`139 runs, 0 unexpected` (t and y among them) and `verification/ci-negative-test.txt` `3 runs, 0
unexpected`. No harness assertion changed, so no mutation is owed. `verification/lock-change.txt`:
six packages added, none removed, no version moved. `uv run --locked python -c "from patchbay import
PatchbayModel, PresetKey"` imports 0.0.1 from the pin. The first hosted run of the git source is
run 42681632482, success at `d638b39`, `verification/hosted-ci-run.txt`.

**Docs (step 7):** checked and reads true against the shipped files:
- `pyproject.toml`: the header now names `[tool.uv.sources]`, and the comment on `dependencies` says
  the range is not checked against the source.
- `README.md`: the Layout bullet names `[tool.uv.sources]`, and Install says the first sync fetches
  `patchbay-core` from GitHub. "No adapter code ships yet" is still true.
- `agent-os/product/tech-stack.md`: the `patchbay-core` line.
- `scripts/gate-negative-tests.sh`: the header lists t and y and says where t's commit comes from.
- `CLAUDE.md`, unchanged and deliberately so: its parenthetical "(the rule set and `[tool.uv]`'s uv
  pin)" does not name `[tool.uv.sources]`, which is still a `[tool.*]` section and so still the
  gate's. Whether that entry stays the gate's is proposal 1 below; the wording follows that decision.

**Version (step 8):** this spec's entry under `### Added` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff. No project standard changed, and
`agent-os/standards/index.yml` is untouched: this repository still has none outside `base/`. This spec
is about the gate and taught nothing about Vital's file, so `agent-os/standards/vital/` is issue #2's.

1. **A pattern no standard covers:** one, a family package on no index. Proposal 2 below.
2. **A standard wrong or stale:** `base/process/verification-gate.md` draws gate files too widely.
   Proposal 1 below.
3. **A deliberate deviation:** one, below.
4. **A pointer moved:** none.

- **Deviation, not a standard change:** `patchbay-core` arrives one spec ahead of the code that
  imports it, against `base/python/toolchain.md` (Decision 4), at the owner's direction. Proposal 1
  removes the cause, so a later adapter adds the dependency in the spec that uses it.

Proposals sent upstream: fromtheoutfit/patchbay-standards#30

### Standards retrospective (proposed, base)

- `base/process/verification-gate.md`, "In a consuming project" and "The gate's own files change only
  in their own spec" — the tool pins, the rule sets and the gate's own flags are gate files; a
  dependency's source and a marker's registration are the package's, as the dev group's non-tool
  entries already are. The owner's proposal; this spec is the evidence, having existed only to add
  those two entries. Verified against `pyproject.toml` and cases t and y of
  `scripts/gate-negative-tests.sh`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#30.
- `base/python/toolchain.md`, "Dependencies" — a family package on no index takes its range in
  `[project] dependencies` and a commit in `[tool.uv.sources]`; uv does not check the range against
  a git source, so the gate proves the commit and not the range, and the wheel carries the range and
  not the source. Verified against `pyproject.toml`, `verification/probes.txt` P1, P4, P4b and P6
  and case t. Proposed, not applied; filed as fromtheoutfit/patchbay-standards#30.
