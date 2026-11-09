# Revision after the review of PR 3 — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered the Step 1 question, three design questions and one confirmation of Steps 2 to 5.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The owner's review of PR 3 at `5dff391`: 15 findings, each checked against the code, the installed
tools and the CI log while shaping. Findings 1 to 8 and 15 are fixed, 9's wording is corrected, 9 and
10 go to the owner as proposals, and 11 to 14 are left. A gate spec: `scripts/gate.sh`, the harness,
`[tool.uv]` and the gate task's wording change, each changed step with its negative test and each
new guard with its mutation. On the same branch, so PR 3 carries it. CHANGELOG entry, gate green,
`verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** the review's triage, and one issue on `fromtheoutfit/patchbay` for the findings
  that hold there too.
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged; `tech-stack.md`'s interpreter line follows
  Decision 3.
- **Step 5, standards:** the core five, and `process/verification-gate`, `process/standards-sync`,
  `process/standards-retrospective`, `process/ownership` and `testing/tests`. Snapshot at `e31f7db`
  in `standards.md`.

## Decisions

1. **The scope is the review's triage**, at the owner's call:
   https://github.com/fromtheoutfit/patchbay-vital/pull/3#issuecomment-6747535173. Fix 1 to 8 and 15;
   correct 9's wording; 9 and 10 as proposals; leave 11 to 14. A new spec folder on this branch; the
   reviewed spec's folder stays its record, but for finding 6.
2. **Finding 1 takes patchbay's form:** `uv run --locked pytest -c pyproject.toml -p no:doctest`. The
   four filename refusals go, since pytest no longer reads those files and a file no step reads never
   fails the gate; a tracked `pytest.ini` was the hole, and the refusal could only ever see an ignored
   one. The `uv.toml` refusal and the ignored-`conftest.py` refusal stay. This reverses the bootstrap's
   Decision 2, "pytest takes no `-c`". `-p no:doctest` stays on the command line, not in `addopts`
   (the bootstrap's Decision 3; `base/python/toolchain.md` fixes `addopts`).
3. **Finding 3 is `[tool.uv] python-preference = "only-managed"`, at the owner's call after a
   conflict between two answers was put back to them.** `.python-version` stays `3.12`, which
   `base/python/toolchain.md` requires ("holds the floor and nothing else"). The setting is written
   once, so a local run and CI agree. **The version chosen is CPython 3.12.16**, the newest 3.12 that
   uv 0.13.7 ships for Linux and the one in the local `.venv` (`verification/probes.txt`); the next
   hosted run confirms it. It moves only when the uv pin does.
4. **Finding 5 is `CDPATH= cd -- ...` in `scripts/gate.sh` and the harness.** That changes the
   skeleton `base/process/verification-gate.md` says is shared: a recorded deviation, and a proposal.
5. **Finding 6:** run 42668230570 is recorded in the reviewed spec's
   `verification/hosted-ci-run.txt`, and that spec's one false sentence is corrected. Nothing else in
   that folder changes, its `plan.md` included.
6. **Finding 9:** the `uv sync --locked` step stays, as `base/process/verification-gate.md` ("CI")
   requires. Only the "nothing else" wording changes.
7. **Finding 10:** no code change. `base/python/layout.md` prescribes the eager form and forbids
   logic in `__init__.py`. The review's "150 modules" is the total after the import; the import adds
   117, measured at 32.7 ms without bytecode.
8. **Issues #1 and #2:** the trailing rule and attribution line removed from each, nothing else
   changed. The review named only #1; #2 ends the same way.
9. **One issue on `fromtheoutfit/patchbay`** for its next gate spec, at the owner's word: findings 2,
   3, 4, 5 and 15, confirmed at its `main` (`2cbf179`), each with the fix it takes here, no attribution. Filed as
   fromtheoutfit/patchbay#17.
10. **`gate-run.txt` stays the last thing done**, rerun after filing writes issue numbers here.
11. **Added while building: step 2 fails on uv's settings warning.** The plan said a value uv cannot
    use in `[tool.uv]` fails the sync by name. Case x's first run showed it does not: uv warns,
    drops the setting and exits 0, so a typo in `python-preference` would bring finding 3 back behind a
    green gate (`verification/probes.txt` section 4; `required-version` does survive).
    `base/process/verification-gate.md` asks that such a value fail the step by name, so step 2 keeps
    the sync's output and fails on the warning.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** `agent-os/product/tech-stack.md`, the interpreter line.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `process/verification-gate` — the shape of the gate, the skeleton and the negative-test rules
- `process/standards-sync` — step 6 and the harness's fixture
- `process/standards-retrospective` — gate step 9, the probe rule and the route of a base proposal
- `process/ownership` — no stage, commit or push by an agent
- `testing/tests` — `test_package.py`

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/1-bootstrap-and-toolchain-shape-spec-claudemd-gate-ci-pyprojecttoml-readme-changelog`,
`verification/gate-run.txt`, the last thing done before hand-over.

- `verification/gate-negative-tests.txt`: 134 runs, 0 unexpected. `verification/ci-negative-test.txt`
  (j): 3 runs, 0 unexpected. One run each, j's after the last edit to the workflow. The baseline before
  them had 2 unexpected in the new case x: an expected text too narrow, and the value uv only warns
  about, which is Decision 11. That run is not kept.
- `verification/guard-mutations.txt`: 57 mutations, each as required: 48 guards caught, 7 harness
  assertions each shown to be what caught its mutation, and 2 of the harness's own guards (the
  scratch directory, and its `cd` under `CDPATH`).
- `verification/probes.txt`: the four pytest files with and without `-c`; the hooks beside a root
  `ruff.toml`; the interpreter and the version chosen, 3.12.16, on CI's architecture; uv's warning. A
  first reading of the interpreter listing covered this machine's architecture alone; `--all-arches`
  corrected it, and the answer held. A first guess that uv's warning also drops `required-version` was
  disproved by the probe, and is not claimed.
- `verification/test-package-proof.txt`: a used `import json` fails the corrected test and passes the
  old filter; the package's own submodule still passes.
- `verification/gate-sh-diff.txt`: against patchbay at `2cbf179`, each code difference classed.
- The next hosted run cannot exist until the owner pushes; its id, conclusion and `Using CPython` line
  go in `verification/` then.

**Docs (step 7):** checked and reads true against the shipped files:
- `README.md`: step 5 and its paragraph, the settings warning, what CI runs, where uv puts the
  interpreter and what it writes outside the repository, `CLAUDE.md`'s order.
- `CLAUDE.md`: the gate sentence and the CI sentence.
- `.claude/commands/agent-os/shape-spec.md`: the gate task, its one-line form and the template.
- The headers of `scripts/gate.sh`, `scripts/gate-negative-tests.sh`, `.github/workflows/gate.yml`,
  and the comments in `pyproject.toml`.
- `agent-os/product/tech-stack.md`: the interpreter line.
- The reviewed spec's `shape.md` line on the hosted run, and its new `verification/hosted-ci-run.txt`.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff; this repository has no project standards, so
every change is a base proposal.

1. **A pattern no standard covers:** two. A setting that picks the interpreter, and a step that fails
   on a tool's warning because the tool will not refuse. Below.
2. **A standard wrong or stale:** the pre-commit form leaves the hooks open to a stray `ruff.toml`
   (finding 2), the skeleton's `cd` follows an exported `CDPATH` (finding 5), the separate sync step
   hides step 2's reason (finding 9), and the eager version costs an import (finding 10). Below.
3. **A deliberate deviation:** two, below.
4. **A pointer moved:** none.

- **Deviation, not a standard change:** `scripts/gate.sh`'s `cd` differs from the shared skeleton
  (Decision 4), until the proposal below lands and this repository's next gate spec takes it.
- **Deviation, not a standard change:** the gate's pytest line carries `-c pyproject.toml` beyond the
  line `base/python/toolchain.md` gives at `e31f7db` (Decision 2). `#27` proposal 2 carries it.

Proposals sent upstream: fromtheoutfit/patchbay-standards#29; declined: `base/python/layout.md` (lazy `__version__`).

### Standards retrospective (proposed, base)

- `base/python/toolchain.md`, "One tool per job" or `[tool.uv]` — `python-preference = "only-managed"`
  beside `required-version`, so a `.python-version` of `3.12` resolves to uv's own build locally and in
  CI. Without it uv took ubuntu-24.04's 3.12.3 (hosted run 42668230570) where a local run had 3.12.16.
  Verified against `pyproject.toml`, case x of `scripts/gate-negative-tests.sh` and M42. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#29.
- `base/python/toolchain.md`, "pre-commit" — each `entry` carries `--config pyproject.toml`, so the
  hooks hold the gate's rule set beside a stray `ruff.toml`. Verified against `.pre-commit-config.yaml`
  and `verification/probes.txt` section 2. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#29.
- `base/process/verification-gate.md`, "A step that installs its pinned tools fails as itself" — uv
  only warns about a key or value it cannot use in `[tool.uv]` and goes on without it, so the sync's
  output is checked for that warning. Verified against `scripts/gate.sh` step 2, case x, M27 and
  `verification/probes.txt` section 4. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#29.
- `base/process/verification-gate.md`, the shared skeleton — the `cd` to the repository root empties
  `CDPATH` (`CDPATH= cd -- ...`). Verified against `scripts/gate.sh`, case w, M2 and M57. Proposed, not
  applied; filed as fromtheoutfit/patchbay-standards#29.
- `base/process/verification-gate.md`, "CI" — the separate `uv sync --locked` step goes, so a stale
  lockfile fails as `FAIL  step 2/6` with step 2's guards run first. Verified against
  `.github/workflows/gate.yml` and the review's finding 9. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#29.
- `base/python/layout.md`, "`__init__.py`" — `__version__` read on first use through a module-level
  `__getattr__`, since the eager read adds 117 modules and 32.7 ms to an import. Verified by measuring
  `src/patchbay_vital/__init__.py` as shipped. Proposed, not applied; declined by owner, 2026-11-09.
