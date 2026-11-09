# Bootstrap and toolchain — Shaping Notes

Shaped 2026-11-09 in plan mode with the stock `/agent-os:shape-spec`, this once, since this spec is
the one that installs the customized command. The owner answered the Step 1, 2, 3 and 5 questions.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking, at the owner's word, ahead of this spec installing
  Step 5a; their full text in `standards.md`.

## Scope

Issue #1 as it stands: the customized shape-spec, `CLAUDE.md`, the gate, its harness and CI,
`pyproject.toml` and the toolchain, the version and package tests, the product docs, `README.md` and
`CHANGELOG.md`, in one spec. No adapter code, and `patchbay-core` is not a dependency yet. A gate
spec, since it creates the gate's files: every step with its negative test, every guard with its
mutation. CHANGELOG entry, gate green, `verification/gate-run.txt`. No stage, commit or push by an
agent.

## Shaping answers

- **Step 1, scope:** issue #1, one spec on this branch; the gate is main plus the issue's three
  additions (Decision 2).
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** skipped; `agent-os/product/` does not exist until this spec writes it.
- **Step 5, standards:** the core five, and `process/verification-gate`, `process/standards-sync`,
  `process/standards-retrospective`, `process/ownership` and `testing/tests`. Snapshot at `e31f7db`
  in `standards.md`.

## Decisions

1. **Issue #1 is the scope**: https://github.com/fromtheoutfit/patchbay-vital/issues/1. Its
   reference for every file it names is `../patchbay` at its `main`, which is `dd2bcad`
   (`origin/main` and GitHub's). The local `main` in that checkout is behind at `2c98c8a`, and its
   working tree is on another branch with uncommitted edits, so every reference was read with
   `git show origin/main:<path>`.
2. **The gate is `dd2bcad` plus what the issue names, at the owner's call.** The issue's step list
   names three things `dd2bcad` does not have: an explicit config for the tools, an ignored
   `uv.toml` refused by name, and `-p no:doctest`. They exist only in the revision after the review
   of patchbay PR 15, which is uncommitted in `../patchbay`: PR 15 merged at `912987a` without it,
   and its branch is gone. That revision is prior art here, and each behaviour is probed again in
   this spec (`verification/probes.txt`). So: `ruff format --config pyproject.toml`,
   `ruff check --config pyproject.toml` and `mypy --config-file pyproject.toml`; a root `uv.toml`
   refused by name at step 2 before the sync, tracked or not, since uv reads it ahead of `[tool.uv]`
   and `base/python/toolchain.md` makes `pyproject.toml` the only config file; and `-p no:doctest`,
   which replaces `dd2bcad`'s `test*.txt` arm, since a file no step reads never fails the gate.
   `dd2bcad`'s refusal of an ignored root `pytest.toml`, `.pytest.toml`, `pytest.ini` or
   `.pytest.ini` stays, as the issue says, and pytest takes no `-c`.

Where patchbay and a base standard disagree, the standard wins, and the difference is recorded here:

3. **`-p no:doctest` sits on `gate.sh`'s pytest command, not in `addopts`.** `base/python/toolchain.md`
   at `e31f7db` fixes `addopts = "-q --strict-markers --strict-config"`, and the issue names the flag
   under the gate's steps. patchbay's revision puts it in `addopts` and
   `fromtheoutfit/patchbay-standards#27` proposes that; it moves here on the sync that lands it.
4. **The ruff ignore list is this tree's own**, from a run of `ALL` with the list empty
   (`verification/ruff-all-empty-ignore.txt`), each entry with its reason. The issue says "patchbay's
   ignore list and reasons"; `toolchain.md` says nothing is listed from memory and a package lists an
   entry when its own run gives it.
5. **No `[tool.uv.build-backend] module-name`.** patchbay needs it, its distribution being
   `patchbay-core` and its import `patchbay`. `toolchain.md` asks for the key only when the import
   name is not the one the distribution name gives, and `patchbay-vital` gives `patchbay_vital`.
6. **No `integration` marker.** patchbay registers one. Nothing here uses it, and `toolchain.md`
   sets nothing under `[tool.pytest.ini_options]` until a spec needs it.

Adaptations:

7. **`test_package.py` drops `test_the_package_re_exports_the_contract_surface`.** This package has
   no module to re-export from, and `__all__` is `["__version__"]`. The spec that adds the first
   module adds the test (`base/python/layout.md`).
8. **`.gitignore` gains `.DS_Store`**, as patchbay's has; harness case g rests on it.
9. **The harness loses `old_file` and every run of the gate from history.** Commits `92cd215`,
   `6adf50e` and `2c98c8a` will never exist in this repository, so those branches could only skip,
   and a branch that only skips is not known to check anything. The direct-tool controls that need
   no history stay.
10. **The harness gains cases patchbay's lacks**, since every guard gets one: `s` for the three
    additions and `v` for the guards `dd2bcad`'s harness has no case for (no file listed, `uv` not on
    `PATH`, a listed `.py` missing at steps 2 and 4).
11. **`gate.sh`'s header says the refusal reads the work tree's `.gitignore` files.** `dd2bcad`'s
    header and `base/process/verification-gate.md` say only committed `.gitignore` files count, which
    is false of `git ls-files --exclude-per-directory`
    (`fromtheoutfit/patchbay-standards#27`, proposal 3). A deviation in one comment; the code is the
    skeleton's.
12. **Five dev tools, each a Decision** (`toolchain.md`, "Dependencies"), at patchbay's pins, the
    dates checked against the upload times in `uv.lock`:
    - **ruff 0.17.4** (2026-11-05): lints and formats; the standard library has no linter or
      formatter. MIT.
    - **mypy 2.4.1** (2026-10-28): checks the types strictly; the standard library has `typing` and
      no checker. MIT.
    - **pytest 9.2.0** (2026-10-27): collects and runs the tests, with assertion rewriting and
      fixtures `unittest` does not give. MIT.
    - **hypothesis 6.170.14** (2026-10-30): property tests with generated, shrunk inputs; nothing in
      the standard library generates or shrinks. MPL-2.0.
    - **pre-commit 4.7.0** (2026-10-12): runs the local hooks at commit; the standard library has no
      hook runner. MIT.
13. **`gate-run.txt` stays the last thing done.** The owner's order is gate green, `gate-run.txt`,
    present-and-file. Filing writes an issue number into `shape.md`, an edit after the run, so the
    gate is rerun and the transcript overwritten once that is written.
14. **The first sync's CHANGELOG entry is written now and says it is late.** `fe84938` made the sync
    before a `CHANGELOG.md` existed.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A; this spec writes `agent-os/product/`.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `process/verification-gate` — the shape of the gate, the skeleton and the negative-test rules
- `process/standards-sync` — step 6, the harness's fixture and the CI layout
- `process/standards-retrospective` — gate step 9, the probe rule and the route of a base proposal
- `process/ownership` — no stage, commit or push by an agent; `CLAUDE.md`'s `## Ownership`
- `testing/tests` — `test_version.py` and `test_package.py`

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/1-bootstrap-and-toolchain-shape-spec-claudemd-gate-ci-pyprojecttoml-readme-changelog`,
`verification/gate-run.txt`, the last thing done before hand-over.

- `verification/gate-negative-tests.txt`: 116 runs, 0 unexpected. `verification/ci-negative-test.txt`
  (j, the CI replay): 3 runs, 0 unexpected, the clean copy passing the job and the broken one stopping
  it at the gate's step. One run each. The baseline run before them came back with 1 unexpected, a
  case of this spec's own expecting uv's status to be 1 where uv exits 2; the case was corrected, and
  that run is not kept.
- `verification/guard-mutations.txt`: 52 mutations, each as required. 39 delete a guard in the gate or
  ignore its status; 12 hold the harness's own assertions, paired so that removing an assertion lets
  the mutation it caught pass; the last shows the scratch directory refused inside the repository. A first run had 2 flaws in the driver, not in the gate:
  one replacement also matched the header comment, and macOS's `mktemp -d` ignored the `TMPDIR` a
  setup relied on. Both were fixed and the whole set rerun, so the file holds one run.
- `verification/gate-sh-diff.txt`: against patchbay at `dd2bcad`, every hunk is a step list or a path,
  or a named Decision (2, 3 and 11); no pin differs.
- `verification/probes.txt`: the three additions, and Decision 11, at the pins. The first draft of the
  `setup.cfg` control used a section pytest refuses, so it could not tell the claims apart; it was
  corrected to `[tool:pytest]` and the refusal kept as its own observation.
- `verification/ruff-all-empty-ignore.txt`: `ALL` over this tree with the list empty.
- The wheel built by `uv build` in a scratch copy holds `LICENSE` and `py.typed`.
- The hosted CI run cannot exist until the owner opens the pull request; its run id and conclusion go
  in `verification/` then (`base/process/verification-gate.md`, "CI").

**Docs (step 7):** checked and reads true against the shipped files:
- `README.md`: the layout, the install, the six steps with their flags, pre-commit, the sync; every
  path it names exists.
- `CLAUDE.md`: Git, No AI attribution and Ownership as in patchbay; the gate sentence with this
  gate's flags.
- `.claude/commands/agent-os/shape-spec.md`: Step 5a, the gate task, its one-line form and the
  `shape.md` template.
- The headers of `scripts/gate.sh`, `scripts/gate-negative-tests.sh`, `.github/workflows/gate.yml`,
  `.pre-commit-config.yaml` and `pyproject.toml`, and the docstring of
  `src/patchbay_vital/__init__.py`.
- `agent-os/product/mission.md` and `tech-stack.md`.
- The Python floor reads the same in its four places; `minimum_pre_commit_version` is the dev group's
  pin; no config file `toolchain.md` forbids exists; no attribution marker in any file this spec adds.

**Version (step 8):** the first spec's entry and the first sync's late entry under `### Added` in
`[Unreleased]`, `CHANGELOG.md`. The version is 0.0.1, as the issue says.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff; this repository has no project standards yet,
so every change is a base proposal.

1. **A pattern no standard covers:** the three additions of Decision 2, carried upstream already by
   `fromtheoutfit/patchbay-standards#27` (proposals 2 and 4); this spec adds nothing to them but
   independent evidence (`verification/probes.txt`). One gap is new: a case for each guard, below.
2. **A standard wrong or stale:** two. "Only committed `.gitignore` files count" in
   `base/process/verification-gate.md`, which `verification/probes.txt` section 5 shows false, is #27's
   proposal 3. `base/process/standards-sync.md` names one project's directory as every project's,
   below.
3. **A deliberate deviation:** three, below.
4. **A pointer moved:** none. The base standards point at patchbay's files, and none moved here.

- **Deviation, not a standard change:** the gate's command lines carry `--config`, `--config-file` and
  `-p no:doctest` beyond the lines `base/python/toolchain.md` gives at `e31f7db`, as the issue asks
  (Decisions 2 and 3). Stays until #27 lands and this repository's gate spec after that sync brings
  the two in step.
- **Deviation, not a standard change:** `scripts/gate.sh`'s header says the refusal reads the work
  tree's `.gitignore` files (Decision 11). The code is the skeleton's; the sentence is true where the
  standard's is not.
- **Deviation, not a standard change:** the first sync's CHANGELOG entry was written late (Decision
  14). One-off: a repository's first sync comes before its `CHANGELOG.md`.

Proposals sent upstream: fromtheoutfit/patchbay-standards#28.

### Standards retrospective (proposed, base)

- `base/process/standards-sync.md`, "In a consuming project" — `<case>/patchbay` names the first
  consuming project's directory as every project's. It becomes `<case>/<the repository's name>`.
  Verified against `mk` and j's replay in `scripts/gate-negative-tests.sh`, which lay a case out as
  `<case>/patchbay-vital`, and `.github/workflows/gate.yml`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#28.
- `base/process/verification-gate.md`, "Every step that can fail is proven to fail" — each way a step
  can fail has its case, not only each step. `dd2bcad`'s harness has a case per step and none for
  seven of its reasons: no file under `scripts/`, no `.py`, none under `src/` or `tests/`, `uv` not on
  `PATH`, and a listed `.py` missing or a symlink to nothing at step 2 and missing at step 4.
  `#22` proposal 1 asks a mutation of a guard a gate spec adds; this asks a case of a guard that is
  already there. Verified against case v of `scripts/gate-negative-tests.sh` and M15, M18–M20, M29 and
  M30 of `verification/guard-mutations.txt`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#28.
