# Revision after the review of PR 3

## Context

The owner's review of PR 3 at `5dff391` (https://github.com/fromtheoutfit/patchbay-vital/pull/3#issuecomment-6747535173) has 15 findings. The hosted gate passed, but a tracked root `pytest.ini` can silently replace the gate's test rules, and CI and local runs use different interpreters. Each finding was checked against the code, the installed tools and the CI log while shaping, and each holds.

Outcome: findings 1–8 and 15 fixed, 9's wording corrected, 9 and 10 presented as proposals, 11–14 left. A gate spec, on the same branch so PR 3 carries it. Every changed step has its negative test, every new guard its mutation. No stage, commit, push or PR by an agent.

Found while shaping:

- patchbay's revision landed at `2cbf179` (PR 16), so `patchbay-standards#27`'s evidence now exists and `pytest -c pyproject.toml` has a reference on `main`.
- Issue #2 carries the same attribution line as #1; the review named only #1.
- The review's "150 modules" for finding 10 is the total after import; the import itself adds 117 (32.7 ms measured without bytecode).

## Decisions for shape.md (owner's answers, 2026-11-09)

1. **Scope is the review's triage** (first Decision, citing the comment above): fix 1–8 and 15; correct 9's wording; 9 and 10 as proposals; leave 11–14. New spec folder on this branch; the reviewed spec's folder stays its record, but for finding 6.
2. **Finding 1 takes patchbay's form:** `uv run --locked pytest -c pyproject.toml -p no:doctest`. The four filename refusals go, since pytest no longer reads those files and a file no step reads never fails the gate. The `uv.toml` refusal and the ignored-`conftest.py` refusal stay. This reverses the bootstrap's Decision 2, "pytest takes no `-c`". `-p no:doctest` stays on the command line (the bootstrap's Decision 3, `toolchain.md` fixing `addopts`).
3. **Finding 3 is `[tool.uv] python-preference = "only-managed"`.** `.python-version` stays `3.12`, as `toolchain.md` requires. Written once, so local and CI agree. The version chosen is recorded: 3.12.16, the newest uv 0.13.7 ships for Linux and the one in the local `.venv`; the next hosted run confirms it.
4. **Finding 5 is `CDPATH= cd -- ...` in `gate.sh` and the harness.** That is a change to the skeleton `verification-gate.md` says is shared: a recorded deviation, and a proposal.
5. **Finding 6:** run 42668230570 recorded in the reviewed spec's `verification/hosted-ci-run.txt`, and that spec's one false sentence (`shape.md:149`) corrected. Nothing else in that folder changes.
6. **Finding 9:** the `uv sync --locked` step stays, as `verification-gate.md` ("CI") requires. Only the "nothing else" wording changes.
7. **Finding 10:** no code change; `layout.md` prescribes the eager form and forbids logic in `__init__.py`.
8. **Issues #1 and #2:** the trailing rule and attribution line removed from each, nothing else changed.
9. **One issue on `fromtheoutfit/patchbay`** for its next gate spec: findings 2, 3, 4, 5 and 15, confirmed at its `main` (`2cbf179`), each with the fix it takes here, no attribution.
10. **`gate-run.txt` stays the last thing done**, rerun after filing writes issue numbers into `shape.md`.

## Tasks

### Task 1: Save spec documentation

Create `agent-os/specs/2026-11-09-{HHMM}-revision-after-pr-3-review/` (`date +%H%M` at execution): `plan.md`, `shape.md`, `references.md`, `verification/`, and `standards.md` by script at `e31f7db` (core five, `process/verification-gate`, `standards-sync`, `standards-retrospective`, `ownership`, `testing/tests`).

`references.md`: patchbay at `2cbf179` (`scripts/gate.sh` step 5, harness q and s); the reviewed spec.

### Task 2: `scripts/gate.sh`

- Finding 1: step 5's listing becomes `-- tests conftest.py`, the filename arm goes, pytest gains `-c pyproject.toml`; banner and header sentences follow.
- Finding 5: the `cd` line.
- Finding 7: header line 74, the interpreter goes to uv's Python directory, not its cache.
- Finding 9: header line 8.

### Task 3: Package and tooling

- `pyproject.toml`: `python-preference` with its reason beside it; `addopts` comment names `-c`.
- `.pre-commit-config.yaml` (finding 2): `--config pyproject.toml` on both entries.
- `tests/unit/test_package.py` (finding 4): exempt only modules whose `__name__` starts with `patchbay_vital.`.
- `.github/workflows/gate.yml`: comments for findings 3 and 9. Action SHAs unchanged, no `uv python` step.

### Task 4: Docs

- `README.md`: step 5 and its paragraph; line 39 (9); 51–54 (7); 40 and 130 (8: `## Git` and `## Ownership` first).
- `CLAUDE.md` and `.claude/commands/agent-os/shape-spec.md` (gate task, one-line form, template): step 5, CI wording.
- `agent-os/product/tech-stack.md`: the interpreter line.
- `CHANGELOG.md`: this spec under `[Unreleased]`, version stays 0.0.1.
- The reviewed spec: Decision 5.

### Task 5: The harness

`scripts/gate-negative-tests.sh`, with the same `cd` fix:

| Case | Change |
|---|---|
| q | Each of the four names, ignored **and tracked**, cannot deselect a tracked failing test: step 5 names the failure. Control: `pytest -p no:doctest` without `-c` deselects it. |
| r | Step 5's listing reason, if reworded. |
| j | `--with pyyaml==6.0.3`, the version `uv.lock` resolves; header corrected (finding 15). |
| **w (new)** | An exported `CDPATH` naming a decoy git top with a `scripts/` directory: the gate runs on its own tree, the decoy's script never listed. |
| **x (new)** | `python-preference` is read: with an empty `UV_PYTHON_INSTALL_DIR`, downloads off and a Python 3.12 on `PATH`, `uv python find` in a copy refuses it, and finds it under `--python-preference managed`. A value uv cannot use fails step 2's sync by name. |

One run each: `verification/gate-negative-tests.txt`, `verification/ci-negative-test.txt`.

`verification/probes.txt`, setup shown: the four names with and without `-c`, tracked and ignored; the pre-commit hooks with a root `ruff.toml`, with and without `--config`; the interpreter resolved under `only-managed` and the version chosen.

`verification/test-package-proof.txt`: a used `import json` in `__init__.py` fails the corrected test and passes the old filter; a submodule import still passes.

### Task 6: Guard mutations

`verification/guard-mutations.txt`, after the last edit to the gate's scripts: the bootstrap's set rerun, its driver updated (a fresh copy per mutation, each `UNEXPECTED`, harness exit 1, assertion removals passing). Removed: the root config arm. Added:

| Guard | Case |
|---|---|
| `pytest -c pyproject.toml` deleted | q |
| `CDPATH=` deleted from `gate.sh` | w |
| `CDPATH=` deleted from the harness | shown as M52 was, the driver running it under a decoy `CDPATH` |
| `python-preference` deleted | x |

`verification/gate-sh-diff.txt`: `diff -u` against patchbay's `gate.sh` and `gate.yml` at `2cbf179`, hunks classed; what `main` changed that the review did not ask for (step 1's pathspec, step 2's listing) is named as out of scope.

### Task 7 (final): Verification gate, filing and hand-over

Rerun the whole harness if any file `mk` copies changed since Task 5. Then, in order:

1. `scripts/gate.sh`, exit 0.
2. Docs and Version, recorded in `shape.md`.
3. Issue bodies (Decision 8): `gh issue edit` on #1 and #2, each asserted to end in exactly that attribution before it is removed.
4. Standards retrospective, the four questions against the diff. Candidates, presented with AskUserQuestion, multi-select, at most three to a question, each ending "None of these":
   - `toolchain.md`: `python-preference = "only-managed"` (finding 3);
   - `toolchain.md`, "pre-commit": entries carry `--config pyproject.toml` (finding 2);
   - `verification-gate.md`, the skeleton's `cd` under `CDPATH` (finding 5);
   - `verification-gate.md`, "CI": drop the separate sync so a stale lockfile fails as step 2 (finding 9);
   - `layout.md`: `__version__` read lazily (finding 10).

   The approved ones filed as one issue on `patchbay-standards`, each declined one marked. `#27` already carries `pytest -c`.
5. The issue on `fromtheoutfit/patchbay` (Decision 9), no attribution, citing this branch and spec.
6. `verification/gate-run.txt`, first line the date and branch, rerun after filing (Decision 10).
7. Stop, and print `git status --short`.

The next hosted run cannot exist until the owner pushes; the hand-over says its id, conclusion and `Using CPython` line go in `verification/` then.

## Verification

- `scripts/gate.sh` exits 0.
- `scripts/gate-negative-tests.sh` and `scripts/gate-negative-tests.sh j`: last lines `N runs, 0 unexpected`.
- `guard-mutations.txt`: every entry `result: as required`.
- `gh issue view 1` and `2`: bodies end before the removed lines, otherwise byte-identical.
- After the owner's push: the hosted log shows `Using CPython 3.12.16`, under uv's managed directory.
