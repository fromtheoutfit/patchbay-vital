# References for Bootstrap and Toolchain

Every patchbay reference below was read with `git show origin/main:<path>` at `dd2bcad`, GitHub's
`main` of `fromtheoutfit/patchbay`. The checkout's local `main` is behind at `2c98c8a`.

## Similar Implementations

### patchbay's gate and CI

- **Location:** `scripts/gate.sh`, `scripts/gate-negative-tests.sh`, `.github/workflows/gate.yml`
- **Relevance:** the skeleton this repository's gate, harness and workflow are taken from.
- **Key patterns:** the exit contract; `step`, `fail`, `git_list`, `listed`, `fail_list`, `present`;
  step 1's root guard, temporary directory and refusal; the harness's `check`, `says`, `later`,
  `only`, `named`, `holds`, `times`, `shim`, `upper`, `mk`; the CI layout of two checkouts side by
  side.

### patchbay's toolchain and package

- **Location:** `pyproject.toml`, `.pre-commit-config.yaml`, `src/patchbay/__init__.py`,
  `tests/unit/test_version.py`, `tests/unit/test_package.py`
- **Relevance:** the toolchain standard as shipped, and the package's two root tests.
- **Key patterns:** the header saying which sections are the gate's; dev pins with dates; the private
  `_metadata` import; the version read from installed metadata.

### patchbay's rules and docs

- **Location:** `.claude/commands/agent-os/shape-spec.md`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`,
  `agent-os/product/mission.md`, `agent-os/product/tech-stack.md`
- **Relevance:** the customized command and the documents the issue names.
- **Key patterns:** Step 5a, the snapshot paragraph, the base-ownership rule, the gate task, the
  present-and-file step, the `shape.md` template.

### patchbay's newest gate spec

- **Location:** `agent-os/specs/2026-11-09-0802-gate-after-sync-and-event-utc-offset/`
- **Relevance:** the shape of `verification/` for a gate spec.
- **Key patterns:** `gate-sh-diff.txt` with its hunks classed, `guard-mutations.txt`, one run per
  transcript, `gate-run.txt` rerun after filing.

### The gate skeleton

- **Location:** `../patchbay-standards`, `scripts/gate.sh` at `e31f7db`
- **Relevance:** the skeleton `base/process/verification-gate.md` names as shared by every
  repository.

### patchbay's uncommitted revision after the review of PR 15 (prior art only)

- **Location:** the working tree of `../patchbay`,
  `agent-os/specs/2026-11-09-0900-gate-revision-after-pr-15-review/`
- **Relevance:** where the issue's explicit config flags, `uv.toml` refusal and `-p no:doctest` come
  from. It is not on `main`, so nothing is copied from it as a reference; each behaviour is probed
  again in this spec's `verification/probes.txt`.
