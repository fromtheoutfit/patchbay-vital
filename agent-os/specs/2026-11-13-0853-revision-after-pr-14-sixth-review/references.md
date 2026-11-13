# References for the Revision after PR 14's Sixth Review

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6854235653,
  "Review of `e852aac`" (2026-11-13 13:24Z).
- **Relevance:** the scope: three checks and nine findings.

## The issues

- **#15**, the map's two inverses, which this branch fixes, and **#13**, the property it first
  corrected. PR 14 closes both.
- **#8**, whose finding 1 narrows and which comes to depend on the new issue this revision files
  for the general rule (finding 9).

## Similar Implementations

### The fifth-review direct count

- **Location:**
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/verification/direct-count.txt`,
  its scripts embedded in the transcript.
- **Relevance:** the floor pass is its shape: two pools of processes, each importing one tree, the
  shipped scalar methods called value by value, binades as bit-pattern ranges, the tree printed
  before and after and compared with `cmp`, timing first with a stop.
- **What changes:** the old tree is `e852aac`, not `main`; the columns are the excuse's
  candidates and the two methods' differences; the range is every value below 2 ** -54 with both
  trees and every value above it with the new one.

### The fifth-review mutation transcript

- **Location:** the same folder, `verification/mutation.txt` (its `mutate` function).
- **Relevance:** a scratch copy of the tree, one mutant at a time, its diff, the tests that fail
  and the exit status. Its code mutants M1 to M10, M15 and M16 are rerun on the restructured
  `to_preset`.

### The first review's seeded regression

- **Location:**
  `agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/verification/mutation.txt`.
- **Relevance:** the mutant only the pinned rows caught, rerun as MC against the test over the
  file's values.

### The unit tests' helpers

- **Location:** `tests/unit/test_parameters.py`: `_record`, `_what_a_set_holds` and
  `_assert_comes_back`.
- **Relevance:** `_what_a_set_holds` computes the excuse's two candidates from primitives;
  `_record` builds the hand-built records the file's values run on.

### Reading `tests/data`

- **Location:** `tests/unit/test_float32.py` (`test_every_recorded_vector_is_the_plugin_s_value`)
  and `tests/unit/test_grisu2.py`, each reading its file through `pytestconfig.rootpath`;
  `base/testing/tests.md`, "A test reads the repository's files from pytest's root".
- **Relevance:** the one way into a repository file, which both modules' readers follow.
