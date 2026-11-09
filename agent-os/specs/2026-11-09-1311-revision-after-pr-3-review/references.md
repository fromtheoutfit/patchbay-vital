# References for the Revision after the Review of PR 3

## Similar Implementations

### patchbay's gate at its current main

- **Location:** `scripts/gate.sh` step 5, and cases q and s of `scripts/gate-negative-tests.sh`, in
  `fromtheoutfit/patchbay` at `2cbf179` (its PR 16)
- **Relevance:** finding 1 takes its form, `pytest -c pyproject.toml`, in place of a refusal by name.
- **Key patterns:** q's case per configuration file, a tracked failing test that the file cannot
  deselect; the listing reduced to `tests conftest.py`.

### The reviewed spec

- **Location:** `agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/`
- **Relevance:** what this spec revises; its harness, mutation set and `verification/` shape are
  carried forward. It stays its own record, but for finding 6.

### The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/3#issuecomment-6747535173, at
  `5dff391`
- **Relevance:** the scope.
