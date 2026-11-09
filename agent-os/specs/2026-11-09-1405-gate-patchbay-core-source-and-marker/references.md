# References for the patchbay-core Source and the Integration Marker

## Similar Implementations

### The harness's cases for a rule set and a pin

- **Location:** `scripts/gate-negative-tests.sh`, cases m, n and o
- **Relevance:** a pin shown read by editing it and leaving the lockfile (n), a changed rule-set value
  applied (m), the sync's own reason ending the run before any tool (n, o).
- **Key patterns:** `mk`, `run`, `times`, the `F2SYNC` line; asserting each `sed` took effect before
  relying on it; `never` a later step printed.

### The last gate spec

- **Location:** `agent-os/specs/2026-11-09-1311-revision-after-pr-3-review/`
- **Relevance:** the shape of a gate spec in this repository: `shape.md`'s Decisions and results, and
  the `verification/` transcripts it keeps.

### patchbay's marker and runtime dependencies

- **Location:** `pyproject.toml` of `fromtheoutfit/patchbay` at `dd2bcad`, `[tool.pytest.ini_options]`
  and `[project] dependencies`
- **Relevance:** where the marker is registered and how a runtime range and its comment read. Its
  marker's meaning differs here on purpose (`shape.md`, Decision 5).
