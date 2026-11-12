# References for Issue #15 in PR 14: the Parameter Map's Two Inverses Land on Held Presets

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14, the comment "Review of
  5e284ec" (2026-11-12 14:25Z).
- **Relevance:** the scope. Findings 1 and 2 are issue #15's two defects; findings 3 to 15 are the
  tests, the conftest and the transcripts around them.

## The issues

- **#15**, the map's two inverses, with the evidence its fix requires (sections 1 and 2).
- **#13**, the property this branch first corrected, which PR 14 closes.
- **#8**, whose findings 1 (the nearer neighbour for an arbitrary display) and 3 (whether
  `VitalInstrument.set` keeps the stored value) stay open, and which says #15 decides which preset
  a set of a shared display stores.

## Similar Implementations

### `main`'s round-trip property

- **Location:** `git show main:tests/unit/test_parameters.py`, `_assert_comes_back`.
- **Relevance:** the property the fix restores: the display back through `to_preset`, the preset
  a display maps to back through the normalized path on every value, and the preset itself back
  but where absorbed, `_ABSORBED` keyed by id.
- **Key patterns:** its three exact assertions; `_shares_its_display` takes `_ABSORBED`'s place.

### The second review's revision

- **Location:** `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`.
- **Relevance:** the notation (P0, D0, P1, N, P2; A1, A2, A3, HELD, SET, SHARE), the excuse
  consulted only where its claim fails, and the evidence scripts.
- **Key patterns:**
  - `verification/sweep.txt` embeds `sweep.py`, whose numpy reproduction of the scalar methods,
    its check on 200,007 values per count and its group keys are kept here;
  - `verification/plugin-probe.txt` embeds `plugin_probe.py`: the tree and blob hashes first, the
    four load histories, and the helpers imported from the test modules;
  - `verification/mutation.txt`: the scratch-copy method.

### The value predicate

- **Location:** `tests/unit/test_parameters.py`, `_shares_its_display`.
- **Relevance:** the one excuse that stays, now stepping through `float32.next_float32`.

### The float32 module and its tests

- **Location:** `src/patchbay_vital/float32.py`, `tests/unit/test_float32.py`.
- **Relevance:** pure-Python float32 arithmetic, exact; `next_float32` joins it in the same style
  and is tested beside `fma32` and `round_to_float32`.

### The integration module

- **Location:** `tests/integration/test_vital_plugin.py`.
- **Relevance:** the `vital` fixture's skip by name, `_held_after_a_set`, the floor and
  power-of-two measures and the load test; `_floats`, the host's reader, and the package's
  `loads` and `dumps`, whose round trip of the plugin's own state `tests/unit/test_format.py`
  holds.
