# References for the patchbay-core Pin at eddba95 and the Integration Marker

## Similar Implementations

### The gate spec that added the source and the marker

- **Location:** `agent-os/specs/2026-11-09-1405-gate-patchbay-core-source-and-marker/`
- **Relevance:** the precedent: the same two entries of `pyproject.toml`, added in a gate spec of
  their own ahead of the feature that needed them (issue #4, ahead of #2), as this spec moves them
  ahead of #8.
- **Key patterns:** `verification/lock-change.txt`'s form (packages at `main` and now, added, removed,
  moved, the tools' pins, the source); `verification/probes.txt` P4: uv does not check the range
  against a git source, so `tests/unit/test_package.py` holds it; the pin read from GitHub, never
  from the sibling checkout.

### Its revision after the review of PR 5

- **Location:** `agent-os/specs/2026-11-09-1433-revision-after-pr-5-review/`
- **Relevance:** made cases t and y what they are now, and `shape.md`'s Standards Retrospective left
  cases n and o, which still spell their pins, "for this repository's next gate spec": this one.
- **Key patterns:** `verification/guard-mutations.txt`: each mutation a fresh copy of the tree as git
  lists it, made outside the repository, one guard deleted or put back as it was, the covering case
  run from the copy and required to come back UNEXPECTED with harness exit 1; M1–M8 cover t and y.

### The harness's cases n, o, t and y

- **Location:** `scripts/gate-negative-tests.sh`: `setrev` (lines 246-251), cases n (406), o (415),
  t (671) and y (781), as shipped by this spec
- **Relevance:** `setrev` rewrites the copy's rev whatever it is now, so a move of the pin leaves t
  working; n and o are made to do the same for their pins. y removes the `markers` block by its form
  (`markers = [` to `]`), not its text.
- **Key patterns:** every edit followed by a setup guard that stops the harness by name (exit 2) when
  the edit did not take; the expected text names uv's own line, then the gate's `FAIL` line.

### patchbay's marker

- **Location:** `pyproject.toml` of `fromtheoutfit/patchbay` at `eddba95`, `[tool.pytest.ini_options]`
- **Relevance:** core's own `integration` marker, "needs a running instrument; not selected by the
  gate until a spec says so", unchanged since `dd2bcad`. Ours differs on purpose: this gate deselects
  nothing.
