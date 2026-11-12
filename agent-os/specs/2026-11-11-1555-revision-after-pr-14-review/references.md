# References for the Revision after the Review of PR 14

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6806758858
  (2026-11-11 20:49Z, at `0568b32`).
- **Relevance:** the scope: sixteen findings and the six checks it was asked for.

## Similar Implementations

### Issue #13's spec folder

- **Location:** `agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`
- **Relevance:** the spec under review. Its `shape.md` gives the notation this spec keeps (P0, D0,
  P1, N, P2; A1, A2, A3, HELD, SET) and the decisions the findings revisit.
- **Key patterns:** `verification/sweep.txt`'s `Vec`, the exact float32 arithmetic in numpy
  (TwoSum, the midpoint rule, three candidates for a quotient), which this spec's sweep
  generalizes to any multiply, four skews and indexed scales. `verification/plugin-probe.txt`'s
  shape: the tree first, the machine and versions, the test module's helpers imported.

### The two test modules

- **Location:** `tests/unit/test_parameters.py` (`_assert_comes_back`, `_ABSORBED`, `_ONE_ULP_OFF`,
  the property's `@example`s, the characterization test) and
  `tests/integration/test_vital_plugin.py` (`vital`, `initial` and `host` fixtures, `_ulps`,
  `_held_after_a_set`, `_double_ulps`, `_BELOW_VOLUME_S_FLOOR`, the census test's name and version
  check).
- **Relevance:** what the findings name, line by line.
- **Key patterns:** the `vital` fixture's skip by name on another machine; the census test's
  `(host.name, host.version) == (committed.instrument, committed.vital_version)`, the way a test
  records the plugin it measured.

### A recorded data file read by a test

- **Location:** `tests/data/fma-vectors.txt`, read by `tests/unit/test_float32.py:98` through
  `pytestconfig.rootpath`; `tests/data/grisu2-vectors.txt` by `tests/unit/test_grisu2.py:18`.
- **Relevance:** the precedent for `tests/data/volume-floor.txt`: hex float32 rows, read through
  the rootpath, not imported.

### Why `builders.py` is not a conftest

- **Location:** `tests/unit/builders.py`, its docstring.
- **Relevance:** a plain module imported by bare name works inside one test directory only; a
  property test takes its strategies at the decorator, where a fixture cannot reach. The rows of
  `volume-floor.txt` are taken by plain tests in two directories, so a fixture in `tests/conftest.py`
  suits them where `builders.py` would not.

### One conftest

- **Location:** `agent-os/standards/base/testing/tests.md`, "Test files": `tests/` has no
  `__init__.py`; it holds one `conftest.py` at most, in the directory that holds every test taking
  its fixtures, the fixtures function-scoped. `pyproject.toml`'s `"tests/**"` per-file ignores
  (S101, INP001) cover `tests/conftest.py`.
- **Relevance:** where the shared reader can live without a gate file changing.

### The gate's negative case q

- **Location:** `scripts/gate-negative-tests.sh`, case q (its header at line 79, the case at
  495-560).
- **Relevance:** it writes an ignored `tests/unit/conftest.py`; with a tracked `tests/conftest.py`
  beside it, the rerun shows it still does what its header says.

### Spec format and the corrections pattern

- **Location:** `agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/` (the format of a
  review revision: decisions, a findings table, verification files) and `24b2b5d`'s
  `agent-os/specs/2026-11-11-1321-revision-after-pr-12-review/shape.md`, Decision 2 (on the branch
  of #11: the reviewed folder stays its record, and its sentences are corrected in the new one).
- **Relevance:** the shape of this folder and of its "Corrections to issue #13's spec".
