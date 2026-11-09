# Bootstrap and toolchain: shape-spec, CLAUDE.md, gate, CI, pyproject.toml, README, CHANGELOG

## Context

Issue #1 (fromtheoutfit/patchbay-vital#1) makes this repository a patchbay repository: the customized shape-spec, `CLAUDE.md`, the gate, CI, the docs and the toolchain, in one spec. It is the second consuming project, so the spec also tests whether the bootstrap is routine. No adapter code ships and `patchbay-core` is not added.

Outcome: `scripts/gate.sh` green on patchbay's skeleton, a rebuilt harness with every step cased and every guard mutated, transcripts in `verification/`. No stage, commit, push or PR by an agent.

Found while shaping, and settled with the owner:

- **The reference is `origin/main` at `dd2bcad`.** The local `main` in `../patchbay` is behind at `2c98c8a`. Every reference is read with `git show origin/main:<path>`; that checkout's working tree is on another branch with uncommitted edits.
- **PR 15 merged at `912987a` without its review revision.** The revision exists only uncommitted in `../patchbay`, its remote branch is gone, and patchbay-standards#27's "Depends on" cites it. Issue #1's explicit config flags, `uv.toml` refusal and `-p no:doctest` come from that revision. The owner chose: **main plus those three**, the revision being prior art only, each behaviour probed again here.

## Decisions for shape.md

1. **Issue #1 is the scope** (first Decision, citing https://github.com/fromtheoutfit/patchbay-vital/issues/1). Shaped with the stock command this once; Step 4 skipped, no `agent-os/product/` yet. Answers: no visuals; references as in `references.md`; standards below.
2. **The gate is `dd2bcad` plus what the issue names:** `ruff format --config pyproject.toml`, `ruff check --config pyproject.toml`, `mypy --config-file pyproject.toml`; a root `uv.toml` refused by name at step 2 before the sync, tracked or not, since `toolchain.md` makes `pyproject.toml` the only config; `-p no:doctest`, replacing main's `test*.txt` arm, since a file no step reads never fails the gate. Main's refusal of an ignored root `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini` stays, and pytest takes no `-c`.

Where patchbay and a base standard disagree, the standard wins:

3. **`-p no:doctest` sits on `gate.sh`'s pytest command, not in `addopts`.** `toolchain.md` at `e31f7db` fixes `addopts = "-q --strict-markers --strict-config"`. patchbay-standards#27 proposes changing that; it moves here on the sync that lands it.
4. **The ruff ignore list is this tree's own**, from a run of `ALL` with the list empty, each entry with its reason. The issue says "patchbay's ignore list"; `toolchain.md` says nothing is listed from memory.
5. **No `[tool.uv.build-backend] module-name`.** `toolchain.md` asks for it only when the import name is not the distribution's; `patchbay-vital` gives `patchbay_vital`.
6. **No `integration` marker.** Nothing here uses one, and `toolchain.md` sets nothing until a spec needs it.

Adaptations:

7. **`test_package.py` drops `test_the_package_re_exports_the_contract_surface`**: this package has no module to re-export from. The spec that adds the first module adds it (`layout.md`).
8. **`.gitignore` gains `.DS_Store`**, as patchbay's has; harness case g rests on it.
9. **The harness loses `old_file` and its history runs.** Commits `92cd215`, `6adf50e` and `2c98c8a` will never exist here, so those branches could only skip. Direct-tool controls that need no history stay.
10. **The harness gains cases patchbay lacks**, because every guard gets a case: see test v below.
11. **`gate.sh`'s header states the refusal reads the work tree's `.gitignore` files**, not "only committed" ones. The standard's sentence is false of `git ls-files --exclude-per-directory` (#27 proposal 3). A deviation in one comment, recorded; the code is the skeleton's.
12. **Five dev tools, as Decisions** (`toolchain.md`, "Dependencies": what it does, why the standard library cannot, its license), at patchbay's pins and dates, checked against `uv.lock`'s upload times: ruff 0.17.4, mypy 2.4.1, pytest 9.2.0, hypothesis 6.170.14, pre-commit 4.7.0.
13. **`gate-run.txt` stays the last thing done.** Filing writes an issue number into `shape.md`, so the gate is rerun and the transcript overwritten after it (patchbay's Decision 7 of its PR 15 spec).
14. **The first sync's CHANGELOG entry is written now**, naming `e31f7db` alone and saying it is late; `fe84938` made the sync before a CHANGELOG existed.

## Tasks

### Task 1: Save spec documentation

Create `agent-os/specs/2026-11-09-{HHMM}-bootstrap-and-toolchain/` (`date +%H%M` at execution) with `plan.md`, `shape.md`, `references.md`, `verification/`, and `standards.md`.

- `standards.md`: full text at `e31f7db`, concatenated by script from `agent-os/standards/base/`: core five (`python/toolchain`, `layout`, `typing`, `models`, `errors`) and `process/verification-gate`, `standards-sync`, `standards-retrospective`, `ownership`, `testing/tests`.
- `references.md`: `../patchbay` at `dd2bcad` per file; its spec `2026-11-09-0802-gate-after-sync-and-event-utc-offset` for the verification folder's shape; `../patchbay-standards` `scripts/gate.sh` at `e31f7db`; the uncommitted revision as prior art only.

### Task 2: The package and toolchain

Copy from `dd2bcad`, adapt, and keep the header comments true.

- `pyproject.toml`: name `patchbay-vital`, version `0.0.1`, the README's description, `license = "MIT"`, `license-files = ["LICENSE"]`, `[build-system]` as it stands, `[tool.uv] required-version = "==0.13.7"`, dev group exact-pinned with dates, `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`. No runtime dependencies; the comment says `patchbay-core` arrives with the spec that imports it.
- `.pre-commit-config.yaml`: patchbay's, registration only. `.gitignore`: `.DS_Store`.
- `src/patchbay_vital/__init__.py`: docstring, `import importlib.metadata as _metadata`, `__version__`, `__all__`; `hello()` goes. `py.typed` stays.
- `tests/unit/test_version.py`, `tests/unit/test_package.py`, renamed to `patchbay_vital` and `patchbay-vital`.
- `uv lock`. Run `ALL` with an empty ignore list, setup shown, into `verification/ruff-all-empty-ignore.txt`; fix what is right, ignore what is wrong for this tree with its reason (Decision 4).

### Task 3: The gate and CI

- `scripts/gate.sh` from `dd2bcad` with Decisions 2, 3 and 11. Run it; green before Task 4.
- `.github/workflows/gate.yml`: `path:` and `working-directory:` become `patchbay-vital`, comments follow; action SHAs unchanged. Both repositories are public, so the second checkout needs no token.
- `verification/gate-sh-diff.txt`: `diff -u` against patchbay's `gate.sh` and `gate.yml` at `dd2bcad`, each hunk classed as step list, pin, path or a named Decision.

### Task 4: Commands, rules and docs

- `.claude/commands/agent-os/shape-spec.md`: patchbay's at `dd2bcad`, gate task and template reworded for Decisions 2 and 3.
- `CLAUDE.md`: Git, No AI attribution and Ownership verbatim; the Specs section naming this gate; the consuming-project line.
- `agent-os/product/mission.md` (the `.vital` format, the VST3↔preset map and unit conversions, sound-design semantics as data; no agent code, no audio analysis) and `tech-stack.md`.
- `README.md` (what, layout, install, gate, pre-commit, sync, specs, the import name `patchbay_vital`) and `CHANGELOG.md` (patchbay's header; this spec and Decision 14 under `[Unreleased]`; version stays 0.0.1).

### Task 5: Rebuild the harness

`scripts/gate-negative-tests.sh` from `dd2bcad`: `<case>/patchbay-vital`, `src/patchbay_vital/`, `import patchbay_vital`, no `old_file`. Cases keep their letters.

| Case | Change |
|---|---|
| a–f, h–o, r, u, j | paths only |
| g, p | history runs gone |
| q | `test*.txt` arm gone. An ignored failing `test_local.txt` passes the gate, with a bare `uv run --locked pytest` as the control that reads it. An ignored `.py` under `__pycache__` passes. |
| **s (new)** | A root `ruff.toml` and `.ruff.toml`, a nested `tests/ruff.toml`, `mypy.ini` and `.mypy.ini` cannot hide a fault from its step, each with a control run without the flag. `uv.toml` untracked, ignored, tracked and a dangling symlink each fail step 2 by name, 3/6 never printed. |
| **v (new)** | Guards with no case in patchbay: git lists no file under `scripts/`; no `.py`; none under `src/` or `tests/`; `uv` not on `PATH` (scratch `PATH`, stopped by name if `uv` is found); a listed `.py` missing from the disk and a symlink to nothing at step 2; a file gone by step 4, through a `uv` shim that removes it after `ruff check`. |

Each case states what it rests on and stops by name on a failed setup.

Run once each: `verification/gate-negative-tests.txt` (all but j), `verification/ci-negative-test.txt` (j, the CI replay). `verification/probes.txt`, setup shown, at the pins: `uv.toml` read ahead of `[tool.uv]`; ruff and mypy config precedence with and without the flag; the doctest plugin with and without `-p no:doctest`.

### Task 6: Guard mutations

`verification/guard-mutations.txt`, after the last edit to the gate's scripts. Each is a fresh copy of the tree as git lists it, outside the repository, with one guard deleted or its status ignored, run through the covering case; each must come back `UNEXPECTED`, harness exit 1. The driver stays in the session's scratchpad; the transcript holds each diff.

| Where | Guard → case |
|---|---|
| Entry | `cd` failure, usage → u |
| Step 1 | `--is-inside-work-tree`, `--show-cdup`, `mktemp` check, refusal's listing status → g; refusal deleted, refusal reading `--exclude-standard`, `fail_list` stopping at the first path → p; `scripts/` listing status, `present` (symlink, missing), non-shell file → g; no file listed → v; `bash -n` → a |
| Step 2 | listing status → r; no `.py`, `present`, `uv` on `PATH` → v; `uv.toml` refusal, `ruff format --config` → s; sync status → n; format status → h |
| Step 3 | `ruff check --config` → s; status → i |
| Step 4 | listing status → r; none under `src/`/`tests/`, `present` → v; `--config-file` → s; status → k |
| Step 5 | listing status → r; `.py` arm, root config arm, `__pycache__` arm, `-p no:doctest` → q; status → l |
| Step 6 | status → b |
| Harness | `check`'s status, `says`, `later`, `only`, `named`, `holds`, `times`, the scratch directory refused inside the repository |

### Task 7 (final): Verification gate

Rerun the whole harness if any file `mk` copies changed since Task 5, one run per transcript. Then, in order:

1. `scripts/gate.sh`, exit 0.
2. Docs: the README, `CLAUDE.md`, `shape-spec.md`, every header comment changed, read against the shipped files; recorded in `shape.md`.
3. Version: `[Unreleased]` entry; 0.0.1; recorded.
4. Standards retrospective: the four questions against the diff; `Proposals sent upstream:` always written. Base proposals go to the owner by AskUserQuestion, multi-select, and the approved ones are filed as one issue with `gh issue create --repo fromtheoutfit/patchbay-standards`, no AI attribution, each declined one marked. Patchbay's differences from a standard found here are candidates, those #27 already carries named as such.
5. `verification/gate-run.txt`, its first line the date and the branch, rerun after filing (Decision 13).
6. Stop, and print `git status --short`.

The hosted CI run cannot exist until the owner opens the PR; the hand-over says its run id goes in `verification/` then.

## Verification

- `scripts/gate.sh` exits 0, on the transcript's named branch.
- `scripts/gate-negative-tests.sh`: last line `N runs, 0 unexpected`. `scripts/gate-negative-tests.sh j` likewise, the workflow's `run` steps replayed clean and broken.
- `guard-mutations.txt`: every entry `result: as required`.
- `gate-sh-diff.txt`: no hunk outside step lists, pins, paths and the named Decisions.
- Wheel check: `uv build` in a scratch copy holds `LICENSE`; `test_distribution_names_its_license_file` holds the metadata at every gate run.
