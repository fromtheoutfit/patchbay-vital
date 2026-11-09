# Gate spec: the patchbay-core source and the integration marker

## Context

Issue #2 needs `patchbay-core` and an `integration` pytest marker. `patchbay-core` is not on PyPI
and has no tags, so its range needs a `[tool.uv.sources]` git pin, and `--strict-markers` needs the
marker registered in `[tool.pytest.ini_options]`. Both sit in the `[tool.*]` sections `CLAUDE.md`
and `base/process/verification-gate.md` make gate-owned, which change only in a spec whose feature
is the gate. The owner chose to land that spec first and resume #2 on top. Outcome: a green gate on
`main`'s successor with `import patchbay` available and the marker registered. No adapter code.

## Decisions

1. **Scope is the issue filed in Task 1**, from the owner's answer of 2026-11-09.
2. **`patchbay-core>=0.0.1,<1`** in `[project] dependencies`: the version the gate runs to the next
   major (`base/python/toolchain.md`). It supplies `PatchbayModel`, `PresetKey`, `PatchbayError`;
   the standard library cannot, since it is this family's own contract. MIT.
3. **`[tool.uv.sources]` pins it to `https://github.com/fromtheoutfit/patchbay` at
   `dd2bcad69dadeb38c6e1e660b2e0ddced13861eb`**, `main`'s head, read by `git rev-parse main`. The
   repository is public, so CI's `uv sync --locked` needs no workflow change.
4. **Deviation at the owner's direction:** `toolchain.md` adds a dependency "by the spec that uses
   it, never ahead of it"; this one arrives one spec early. Recorded, not proposed: the retrospective's
   proposal removes the cause.
5. **Marker text** says what #2 does with it: needs the presets of an installed Vital, skipped with
   its reason where they are absent, and run by the gate where they are present. It differs from
   patchbay's on purpose, its integration tests not being selected by its gate.
6. **Limit, recorded:** the wheel carries the range but not the source, so installing it elsewhere
   needs `patchbay-core` on an index. Nothing installs it elsewhere yet.

## Tasks

### Task 1: Save spec documentation

- `gh issue create` on patchbay-vital, no attribution; `git switch -c` a branch from `main` named
  for it. #2's branch stays as it is.
- Copy the appendix below to `~/.claude/plans/issue-2-discovery-record.md`, outside the repository,
  with a project memory pointing at it; #2's Task 1 moves it into `verification/discovery.md`.
- Create `agent-os/specs/{YYYY-MM-DD-HHMM}-gate-patchbay-core-source-and-marker/` with `plan.md`
  (this plan without the appendix), `shape.md` (first Decision cites the issue; the shaping answers),
  `standards.md` (core five and `process/verification-gate`, `process/standards-retrospective`,
  `process/ownership`, `testing/tests`, full text at `e31f7db`), `references.md`
  (`scripts/gate-negative-tests.sh` cases m, n, o; `agent-os/specs/2026-11-09-1311-revision-after-pr-3-review/`).

### Task 2: Probe at the pinned tools, in a scratch copy

Into `verification/probes.txt`: uv 0.13.7 locks the git source; a `rev` edited with the lockfile
left fails `uv sync --locked`, and how; whether pytest 9.2.0 refuses a `markers` value it cannot
use; what the built wheel's metadata says about the dependency.

### Task 3: `pyproject.toml` and `uv.lock`

- `[project] dependencies`: the range, its comment replacing "None yet".
- `[tool.uv.sources]` after the `[tool.uv]` block, with a comment saying what it pins and why.
- `markers` in `[tool.pytest.ini_options]`.
- `uv lock` under uv 0.13.7. `verification/lock-change.txt` shows the packages added and that
  ruff 0.17.4, mypy 2.4.1, pytest 9.2.0 and every other existing pin did not move.

### Task 4: Negative tests in `scripts/gate-negative-tests.sh`

Two new cases, in the header list and both `tests=(...)` lines:

- **t, the source pin is read:** `rev` changed in the copy, `uv.lock` left; step 2's sync fails with
  uv's reason and the sync's `F2SYNC` line, exit 1, 3/6 never printed.
- **y, the marker is registered:** a copy with a test under `@pytest.mark.integration` passes step
  5; with the `markers` entry removed, and separately with the mark misspelled, step 5 fails naming
  it, exit 1, 6/6 never printed. A `markers` value pytest refuses is a third run if Task 2 finds one.

### Task 5: Docs

`agent-os/product/tech-stack.md`'s `patchbay-core` line; `README.md` where it describes the
`[tool.*]` sections and dependencies; the header comment of `pyproject.toml`. `CLAUDE.md` is
unchanged: the sections are still gate-owned until the proposal lands.

### Task 6 (FINAL): Verification gate

1-6. `scripts/gate.sh`: shell scripts parse; `uv sync --locked` then ruff format; ruff check; mypy;
pytest; `scripts/sync-standards.sh --check`. Exit 0, and `verification/gate-run.txt` with the date
and the branch.
Then, gate files having changed, `scripts/gate-negative-tests.sh all`, transcripts in
`verification/gate-negative-tests.txt` and `verification/ci-negative-test.txt` (j).
7. **Docs**, recorded in `shape.md`.
8. **Version**: `[Unreleased]` in `CHANGELOG.md`; the version stays 0.0.1.
9. **Standards retrospective**, last. Project standards: expected none, and said so. Base proposal,
   the owner's: `base/process/verification-gate.md` narrows which `[tool.*]` entries are gate files.
   Tool pins, rule sets and the gate's own flags are; a dependency source and a marker registration
   are the package's, as the dev group's non-tool entries already are. Evidence: this spec's
   `pyproject.toml` and cases t and y. Presented with AskUserQuestion, the approved ones filed as one
   issue on `fromtheoutfit/patchbay-standards`, no attribution, and the `Proposals sent upstream:`
   line written.

Then stop and print `git status --short`. No stage, commit, push or PR: the owner lands this, and
the first hosted run of the git source is recorded after that push. Then #2 resumes on top.

## Verification

- `scripts/gate.sh` exits 0 on the branch; `scripts/gate-negative-tests.sh all` ends with every case
  as expected, t and y among them.
- `uv run --locked python -c "from patchbay import PatchbayModel, PresetKey"` imports from the pin.
- `git diff main -- uv.lock` adds packages and moves no existing pin.

