# Revision after the Review of PR 5 — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered one design question and one confirmation of Steps 2 to 5.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The owner's review of PR 5 at `d638b39`: eleven findings, each checked against the code, run
42681632482 and the standards while shaping, all of which hold. A gate spec: `scripts/gate.sh` and
the harness change. On the same branch, so PR 5 carries it. CHANGELOG entry, gate green,
`verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** the review's eleven findings.
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/ownership` and `testing/tests`. Snapshot at `e31f7db`
  in `standards.md`.

## Decisions

1. **The scope is the review**:
   https://github.com/fromtheoutfit/patchbay-vital/pull/5#issuecomment-6749244150.
2. **A new spec folder on this branch**, as the PR 3 revision did. The reviewed folder stays its
   record, but for `verification/hosted-ci-run.txt` and the one sentence that run made false.
3. **`packaging==26.3` joins the dev group.** What it does: parses the declared range in a unit test
   (finding 1). Why the standard library cannot: it has no PEP 440 specifier parser. License: Apache-2.0
   OR BSD-2-Clause. Published 2026-08-04. Already locked through pytest, so no package is added;
   declared because the test imports it directly (`base/python/toolchain.md`, "Dependencies").
4. **Finding 4 corrects the reviewed spec's "no harness assertion changed".** Cases t and y were new
   assertions, and `base/process/verification-gate.md` asks that a change to them be shown to
   discriminate. `verification/guard-mutations.txt` does so here.
5. **Finding 6 reverses what the reviewed spec left deliberately.** `CLAUDE.md` names
   `[tool.uv.sources]` now, as the README does; the wording follows upstream's decision when it lands.
6. **Case y's marked test fails on purpose**, so step 5 naming it proves it was collected and run; a
   passing run cannot tell "ran" from "deselected", and its `holds` line could not fail after an
   exit 0.
7. **Findings 1 and 3 live in `tests/unit/test_package.py`**, which `base/testing/tests.md` gives the
   root's surface and its distribution's metadata, so no test module breaks the mirror.
8. **Case t's range and rev edits match whatever is there**, so a later pin or range move leaves the
   harness working (finding 8).

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — a gate spec; each changed case shown to discriminate
- `base/process/standards-retrospective` — the correction to the proposals already filed
- `base/process/ownership` — the owner lands this revision
- `base/testing/tests` — where the two new tests live

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/4-gate-the-patchbay-core-source-and-the-integration-marker`, `verification/gate-run.txt`.
Gate files changed, so the whole harness was rerun: `verification/gate-negative-tests.txt` ends
`141 runs, 0 unexpected` and `verification/ci-negative-test.txt` `3 runs, 0 unexpected`.
`verification/guard-mutations.txt`: 8 mutations, 8 as required. `verification/lock-change.txt`: no
package added, removed or moved. Run 42681632482, the hosted run of the reviewed head, is recorded in
the reviewed spec's `verification/hosted-ci-run.txt`. The hosted run of this revision exists only
after the owner's push, and is not claimed here.

**Docs (step 7):** checked and reads true against the shipped files:
- `CLAUDE.md`: names `[tool.uv.sources]` among the gate's entries (finding 6) and `packaging` among
  the package's.
- `README.md`: Install says uv and git are assumed (finding 7), the gate section names a failed
  fetch (finding 9), Layout says the wheel installs only where `patchbay-core` resolves (finding
  11), and both lists of the dev group's entries name `packaging`.
- `pyproject.toml`: the header and dev-group comments name `packaging`; the `dependencies` comment
  says the test holds the range.
- `scripts/gate.sh` header says what git is needed for; `scripts/gate-negative-tests.sh` header
  says what t and y now hold.
- `agent-os/product/tech-stack.md`: the `patchbay-core` line no longer says #2 is the first to
  import it, a test here doing so.
- The reviewed spec's `shape.md`: the one sentence on the hosted run. Its "no mutation is owed" stays
  as its record, corrected by Decision 4 here.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff. No project standard changed, and
`agent-os/standards/index.yml` is untouched. This revision taught nothing about Vital's file, so
`agent-os/standards/vital/` stays issue #2's.

1. **A pattern no standard covers:** two, what a passing case can show and how a case edits a pin.
   Below.
2. **A standard wrong or stale:** none in `base/` at the pin. A proposal this repository already
   filed was: `fromtheoutfit/patchbay-standards#30` said the gate proves the commit and not the
   range, which this revision makes false. Revised in place, as that repository's issues do.
3. **A deliberate deviation:** none new. The reviewed spec's Decision 4 stands.
4. **A pointer moved:** none.

- **Noted, not fixed:** cases n and o of `scripts/gate-negative-tests.sh` still spell their pins, the
  weakness finding 8 named in t. Outside the review's findings; recorded upstream as work left behind
  by `fromtheoutfit/patchbay-standards#31`, for this repository's next gate spec.

Proposals sent upstream: fromtheoutfit/patchbay-standards#30 (revised), fromtheoutfit/patchbay-standards#31

### Standards retrospective (proposed, base)

- `base/python/toolchain.md`, "Dependencies" — proposal 2 of `#30`, rewritten: a unit test compares the
  installed version with the specifier in the project's own `Requires-Dist`, since uv does not check
  the range against a git source. Verified against `tests/unit/test_package.py`, case t and M4.
  Proposed, not applied; `fromtheoutfit/patchbay-standards#30`, revised in place at the owner's word.
- `base/process/verification-gate.md`, the harness's assertions — a case claiming something ran makes
  it fail on purpose, and a named line on a passing run must be one the run could have lacked.
  Verified against case y, M5 and M6. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#31.
- `base/process/verification-gate.md`, "A case states what it rests on" — a case that edits a pin
  matches any value of it. Verified against `setrev` and case t. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#31.
