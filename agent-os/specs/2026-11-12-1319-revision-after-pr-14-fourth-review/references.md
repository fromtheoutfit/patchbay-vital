# References for the Revision after PR 14's Fourth Review

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6831965378,
  "Review of f3625d1" (2026-11-12 18:12Z).
- **Relevance:** the scope: seven checks, three other findings and four smallest fixes.

## The issues

- **#15**, the map's two inverses, which this branch fixes, and **#13**, the property it first
  corrected. PR 14 closes both.
- **#8**, whose findings 1 (the neighbour for an arbitrary display) and 3 (whether
  `VitalInstrument.set` keeps a stored value) stay open.
- **fromtheoutfit/patchbay-standards#39**: a behaviour an open issue decides is held by a
  characterization test that names the issue. Decision 4's test is one.
- **fromtheoutfit/patchbay-standards#40**: proposal 2, a property's known exception excused by a
  stated value predicate. `_shares_its_display` is its instance.

## Similar Implementations

### The previous spec's sweep

- **Location:** `agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/verification/sweep.txt`.
  Its `sweep.py` and `sweep_exponential.py` are embedded in the transcript.
- **Relevance:** the every-float32 count this revision reruns.
- **Key patterns:**
  - the exact float32 arithmetic in numpy;
  - the check against the scalar methods before counting;
  - counts by binade;
  - the libm section through `math.pow` and `math.log2`.
- **What changes:**
  - `Vec.fixed` and `Vec.Nf` shared the shipped guards, so CHANGEDx and NCHANGEDx were 0 by
    construction;
  - the BOTH and NONE flags were never checked;
  - its docstring said 200,007.

### The previous spec's probe and mutation

- **Location:** the same folder, `verification/plugin-probe.txt` and `verification/mutation.txt`,
  each embedding its script (`plugin_probe.py`, `mutate.sh`).
- **Relevance:** rerun at the same pinned values, and with the mutants this revision's rule and
  tests need.
- **Key patterns:**
  - the probe imports the integration module's tuples and `_held_after_a_set`, printing each
    file's blob;
  - the mutants run on scratch copies of the tree, as git lists it.

### The test modules

- **Location:**
  - `tests/unit/test_parameters.py`: `_assert_comes_back`, `_shares_its_display`, the pinned
    tuples and the direct tests;
  - `tests/unit/test_float32.py`: `_numpy` and `_next_up`, numpy as the independent oracle;
  - `tests/integration/test_vital_plugin.py`: the same tuples and `_held_after_a_set`.
- **Relevance:** what this revision changes, and the numpy pattern its new `next_float32`
  property follows.
