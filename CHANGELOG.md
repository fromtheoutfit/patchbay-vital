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

### Added

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
