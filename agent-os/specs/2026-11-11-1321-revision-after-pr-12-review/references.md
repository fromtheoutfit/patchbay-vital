# References for the Revision after the Review of PR 12

## Similar Implementations

### The reviewed spec

- **Location:** `agent-os/specs/2026-11-11-1011-gate-core-pin-and-marker-needs/`
- **Relevance:** the gate spec of issue #11 that PR 12 carries at `8ebce15`, and the subject of the
  review. Its folder stays its record; this spec's Decisions correct the sentences the review showed
  false, by name.
- **Key patterns:** `verification/lock-change.txt` (the pin's two lines of `uv.lock`, unchanged
  here); `verification/new-pin-gate.txt`, `guard-mutations.txt` and `pin-moves.txt`, whose form the
  review faulted (findings 5 to 8) and this spec's `verification/` replaces.

### The revision after the review of PR 5

- **Location:** `agent-os/specs/2026-11-09-1433-revision-after-pr-5-review/`
- **Relevance:** the precedent for a revision of a gate spec in a folder of its own on the same
  branch, and for correcting a reviewed record by a Decision rather than in place. Its
  `verification/guard-mutations.txt` M1-M8 stand for cases t and y, whose assertions this spec does
  not change.
- **Key patterns:** each mutation a fresh copy of the tree outside the repository, one guard deleted
  or put back as it was. Its transcript excerpts each run and ends on a tally, the form findings 7
  and 8 fault in the reviewed spec's; this spec keeps one whole run per file.

### The harness's pin edits and cases n, o, t and y

- **Location:** `scripts/gate-negative-tests.sh` at `8ebce15`: `setrev` (lines 246-251), cases n
  (406), o (415), t (671) and y (781)
- **Relevance:** `setrev` rewrote t's rev whatever it was, but anywhere in the file; n and o wrote
  out the same rewrite, `rm .bak` and check by hand (finding 14), unscoped to their tables (finding
  3), n's value pattern taking another operator and a marker (finding 2), o checking the running uv
  but not the file (finding 1). This spec puts the three behind one helper, `setline`.
- **Key patterns:** every edit followed by a setup guard that stops the harness by name (exit 2);
  y removes the `markers` block by its form (`markers = [` to `]`), the address range `setline`
  uses for a table.

### The parameter map's machine rule

- **Location:** `agent-os/standards/vital/parameter-map.md`, "The map records the machine the census
  ran on" (line 33), and the `vital` fixture of `tests/integration/test_vital_plugin.py`
- **Relevance:** the skip the marker's comment now names: the plugin's tests skip where the map was
  measured on another machine, even with the plugin installed (finding 10).
