# References for the Revision after the Second Review of PR 14

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6811755893
  (2026-11-12 01:34Z, of `88d438d`, `0568b32`, `412b21a` and `c159446`).
- **Relevance:** the scope, its main problem, two tests #15's fix would break, the six requested
  checks and five smaller findings.

## Similar Implementations

### The first review's revision

- **Location:** `agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`
- **Relevance:** the revision under review. Its `shape.md` gives the notation (P0, D0, P1, N, P2;
  A1, A2, A3, HELD, SET) and Decision 8, the power-of-two exception.
- **Key patterns:**
  - its `verification/sweep.txt` script, generalized again here;
  - its `verification/plugin-probe.txt`, whose shape (tree, blobs, helper source) the new probe
    keeps;
  - its `verification/mutation.txt`, whose scratch-copy method the new mutation keeps.

### The value predicate already in the property

- **Location:** `tests/unit/test_parameters.py`, `_lands_below_its_power_of_two`.
- **Relevance:** the shape `_shares_its_display` follows. A value condition is consulted only where
  its claim fails, `claim or predicate`, so it excuses nothing that holds.

### The shared reader and the row files

- **Location:** `tests/conftest.py` (`recorded_rows`, `volume_floor`, `power_of_two_presets`),
  `tests/data/volume-floor.txt`, `tests/data/power-of-two-presets.txt`.
- **Relevance:** `stepped` joins `recorded_rows` there, a fixture of the same name handing it to
  tests. The power-of-two file gains two rows and a reader in the integration tests.

### The test modules

- **Location:** `tests/unit/test_parameters.py` (`_assert_comes_back`, both characterization
  tests) and `tests/integration/test_vital_plugin.py` (the `vital` fixture's skip by name, the
  census test's version check, `_held_after_a_set`, the volume measure, the load test).
- **Relevance:** what the findings name, line by line.
