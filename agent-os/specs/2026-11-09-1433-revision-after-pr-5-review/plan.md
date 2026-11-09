# Revision after the review of PR 5

## Context

The owner's review of PR 5 at `d638b39`
(https://github.com/fromtheoutfit/patchbay-vital/pull/5#issuecomment-6749244150) lists eleven
findings, mostly gaps in what the gate proves. Each was checked while shaping against the code,
run 42681632482 and the standards, and all eleven hold. This revision fixes all of them, so PR 5
proves what it claims before #2 builds on it. It is a gate spec: `scripts/gate.sh` and the harness
change. No adapter code.

## Decisions

1. **The scope is the review's eleven findings**, at the owner's word.
2. **A new spec folder on this branch, so PR 5 carries it**, as the PR 3 revision did. The reviewed
   folder stays its record, but for adding `verification/hosted-ci-run.txt` and correcting the one
   sentence the run made false (`shape.md:91`).
3. **`packaging==26.3` joins the dev group**: published 2026-08-04, Apache-2.0 OR BSD-2-Clause. It
   parses the range; the standard library has no PEP 440 specifier parser. Already locked through
   pytest, so no package is added, and declared because the test imports it directly.
4. **Finding 6 reverses what the reviewed spec left deliberately:** `CLAUDE.md` names
   `[tool.uv.sources]` now, as the README does, and follows upstream's decision when it lands.
5. **Case y's marked test fails on purpose**, so step 5 naming it proves it was collected and run.
   A passing run cannot tell "ran" from "deselected".
6. **Finding 3 and finding 1 live in `tests/unit/test_package.py`**, which `base/testing/tests.md`
   gives the root's surface and its distribution's metadata, so no test module breaks the mirror.

## Tasks

### Task 1: Save spec documentation

`agent-os/specs/{YYYY-MM-DD-HHMM}-revision-after-pr-5-review/`: `plan.md` (this plan), `shape.md`
(first Decision cites the review), `standards.md` (core five, `process/verification-gate`,
`process/standards-retrospective`, `process/ownership`, `testing/tests`, full text at `e31f7db`),
`references.md` (the PR 3 revision's `verification/guard-mutations.txt`; cases n, t and y).

### Task 2: Tests and `packaging` (findings 1, 3)

- `pyproject.toml`: `packaging==26.3` in the dev group with its date; the header and dev-group
  comments that list the non-tool entries; the `dependencies` comment says a test now holds the
  range. `uv lock` under 0.13.7; `verification/lock-change.txt` shows no package added or moved.
- `tests/unit/test_package.py`:
  - the installed `patchbay-core` version meets the specifier in patchbay-vital's `Requires-Dist`
    (`importlib.metadata.requires`, `packaging.requirements.Requirement`);
  - `PatchbayModel`, `PresetKey` and `PatchbayError` import from `patchbay` and come from its
    modules, so a rev lacking them fails step 5.

### Task 3: `scripts/gate.sh` (finding 9)

Step 2's reason also names a locked package that could not be fetched (the network, a missing git,
a commit gone). The header says steps 2-5 need git for that fetch too.

### Task 4: Harness, `scripts/gate-negative-tests.sh` (findings 2, 8, 9, 10)

- `F5RUN` defined first, `F5T` built from it; `F2SYNC` follows gate.sh's new reason.
- **t:** the rev rewritten by `sed -E` matching any rev, so it survives a pin move. Two new runs,
  each from a restored copy: a commit that does not exist fails step 2 naming the failed fetch
  (P3); the range edited to `>=9,<10` passes steps 2-4 and step 5 names the range test.
- **y:** the marked test fails on purpose, entry in place: step 5 names
  `FAILED tests/unit/test_marked.py::test_under_the_marker`. The `holds` line goes. The
  entry-removed and misspelled runs stay.
- The header's t and y entries say so.

### Task 5: Mutations (finding 4)

`verification/guard-mutations.txt` in the PR 3 revision's form, a throwaway script outside the
repository, each mutation a fresh copy run through the case that covers it, which must come back
UNEXPECTED with harness exit 1:

| Mutation | Case |
|---|---|
| gate.sh's `uv sync --locked` loses `--locked` | t |
| step 2's sync status ignored | t |
| gate.sh's reason put back as it was | t (fetch run) |
| the range test deleted from `test_package.py` | t (range run) |
| `-m 'not integration'` in `addopts` | y |
| `-m 'not integration'` on step 5's pytest line | y |
| the `markers` entry deleted | y |
| `--strict-markers` dropped from `addopts` | y |

### Task 6: Records and docs (findings 5, 6, 7, 11)

- Reviewed folder: `verification/hosted-ci-run.txt` for run 42681632482 (success, head `d638b39`,
  CPython 3.12.16, built the git source, 7 passed), and `shape.md:91` corrected.
- `CLAUDE.md:93` names `[tool.uv.sources]`, and its list of the dev group's non-tool entries gains
  `packaging`.
- `README.md`: Install says uv and git are assumed, `uv sync` calling git to fetch `patchbay-core`;
  the gate section names a failed fetch; Layout says the wheel declares the range and not the
  source, so it installs only where `patchbay-core` resolves; both lists of dev entries gain
  `packaging`.

### Task 7 (FINAL): Verification gate

1-6. `scripts/gate.sh`: shell scripts parse; `uv sync --locked` then ruff format; ruff check; mypy;
pytest; `scripts/sync-standards.sh --check`. Exit 0; `verification/gate-run.txt` with date and
branch, the last act before hand-over.
Gate files having changed: `scripts/gate-negative-tests.sh`, then `j`, each one run in its own
transcript, `verification/gate-negative-tests.txt` and `verification/ci-negative-test.txt`.
7. **Docs**, recorded in `shape.md`.
8. **Version**: `[Unreleased]` in `CHANGELOG.md`; the version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff. Expected: no project standard; present
   to the owner a correction to `fromtheoutfit/patchbay-standards#30`, whose proposal 2 says the gate
   proves the commit and not the range, and any new base proposal the diff supports (a candidate:
   a passing-run assertion its exit status already implies asserts nothing). The approved ones
   filed with no attribution, and the `Proposals sent upstream:` line written.

Then stop and print `git status --short`. No stage, commit or push: the owner lands this, and the
hosted run of this revision exists only after that push.

## Verification

- `scripts/gate.sh` exits 0; the harness and `j` each end `0 unexpected`.
- `guard-mutations.txt` ends with every mutation as required.
- `git diff d638b39 -- uv.lock` adds and moves no package.
- Editing the range to `>=9,<10` fails step 5 by the range test's name (case t).
