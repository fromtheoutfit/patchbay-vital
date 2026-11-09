# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The base standards under `agent-os/standards/base/` are pinned to the commit in `base/.version`;
a sync forward is recorded here by the sync's own commit, one entry naming the old commit and the
new as the sync's report gives them. The script writes no `CHANGELOG.md`: the person who syncs
writes the entry, in that commit
(`agent-os/standards/base/process/standards-sync.md`, "Pinned, not tracking").

## [Unreleased]

### Changed

- Revision after the review of PR 3, `agent-os/specs/2026-11-09-1311-revision-after-pr-3-review/`:
  findings 1 to 8 and 15 of the review at `5dff391` fixed, 9's wording corrected, 9 proposed upstream
  (`fromtheoutfit/patchbay-standards#29`), 10 declined by the owner, 11 to 14 left. Findings that
  hold in patchbay too are `fromtheoutfit/patchbay#17`. The version stays 0.0.1.
  - `scripts/gate.sh` step 5 runs `pytest -c pyproject.toml -p no:doctest`, so a root `pytest.ini`,
    `.pytest.ini`, `pytest.toml` or `.pytest.toml`, tracked or ignored, cannot replace the test
    rules; the four filename refusals are gone, the `uv.toml` refusal stays.
  - `[tool.uv] python-preference = "only-managed"`: a local run and CI both use uv's own build of
    the interpreter, CPython 3.12.16 at this uv pin, where CI had taken the runner's 3.12.3.
  - Step 2 fails by name when uv warns it cannot use a key or value in `[tool.uv]`, where uv goes on
    without it and the gate passed.
  - `scripts/gate.sh` and the harness empty `CDPATH` for the `cd` to the repository root.
  - The pre-commit hooks read `pyproject.toml` alone (`--config`), as the gate does.
  - `tests/unit/test_package.py` exempts only the package's own submodules from the public surface.
  - The harness: q holds each of the four files, ignored and tracked; new cases w (`CDPATH`) and x
    (`python-preference`); j pins pyyaml. `verification/guard-mutations.txt`: each guard's mutation
    caught.
  - Docs: where uv puts the interpreter, what CI runs besides the gate, and that `CLAUDE.md` opens
    with `## Git`. The bootstrap spec records its hosted run, 42668230570.

### Added

- `patchbay-core>=0.0.1,<1` as the first runtime dependency, taken from its public repository at
  `dd2bcad` by `[tool.uv.sources]`, and the `integration` pytest marker, for issue #2 to build on. A
  gate spec, issue #4, `agent-os/specs/2026-11-09-1405-gate-patchbay-core-source-and-marker/`;
  negative tests t and y. `uv.lock` adds six packages and moves no existing pin. The version stays
  0.0.1.
- sync base standards: e31f7dbfb474752339a43fe08a37ab26c7956f5c, the first sync. Written by the spec
  after it (`agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/`), since the sync's commit
  `fe84938` came before this file existed.

- First spec, `agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/` (issue #1): this repository
  becomes a patchbay repository, its second consuming project. Every departure from the issue's text
  and from patchbay is a Decision in the spec's `shape.md`. The version is 0.0.1.
  - `scripts/gate.sh`, `scripts/gate-negative-tests.sh` and `.github/workflows/gate.yml` from
    patchbay at `dd2bcad`, with this repository's paths. On top of that skeleton, as the issue
    names them: ruff and mypy told by flag to read `pyproject.toml` alone, a root `uv.toml` refused
    by name at step 2, and `-p no:doctest` on the pytest step.
  - The harness rebuilt for this repository: every step with its case and every guard with its
    mutation (`verification/guard-mutations.txt`), the CI replay, and case `v` for the guards that
    had no case. Its runs of the gate from patchbay's history are gone.
  - `pyproject.toml`: the toolchain standard applied, the ruff ignore list being what this tree's
    own first run gave. `.pre-commit-config.yaml`, registration only.
  - `src/patchbay_vital/__init__.py` holds `__version__` from the installed metadata and `__all__`;
    `tests/unit/test_version.py` and `test_package.py` hold them.
  - `.claude/commands/agent-os/shape-spec.md` customized for this repository's gate, `CLAUDE.md`,
    `README.md`, `agent-os/product/mission.md` and `tech-stack.md`.
  - `patchbay-core` is not a dependency yet: this spec ships no adapter code.
