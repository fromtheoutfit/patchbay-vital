# References for Issue #16: to_preset Returns a Held Preset

## The issues

- **#16**, the scope: https://github.com/fromtheoutfit/patchbay-vital/issues/16. The rule, the
  evidence it requires, and six findings carried from PR 14's final review, each unverified.
- **#8**, "From core's review of PR 19", findings 1 and 3. This spec narrows finding 1 to which
  held preset an arbitrary display takes and decides neither.
- **#15** and **#13**, which PR 14 closed, and whose rule this spec completes.

## Similar Implementations

### The fifth review's direct count

- **Location:**
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/verification/direct-count.txt`,
  with `direct_count.py`, `run_direct.sh` and `group_key.py` embedded.
- **Relevance:** the shape of this spec's direct count: two pools of processes, each importing
  one tree, the shipped scalar methods called value by value, binades as bit-pattern ranges,
  timing first with a stop, the trees printed before and after and compared with `cmp`, a
  control that moves the counts.
- **What changes:** the old tree is `main` at `f533b1b`; the branch read from the result has no
  unheld class, and gains one for what a set holds where that does not show the display; the
  run stops on any difference at all; the envelope record is counted on the two methods that can
  differ.

### The fifth review's arbitrary displays

- **Location:** the same folder, `verification/arbitrary-displays.txt`.
- **Relevance:** 20,000 displays of `volume`, `numpy.random.default_rng(8)`, the branch read from
  the shipped result: 1,108 on the third branch. This spec's sample meets that number and the
  issue's 1,085 (`random.uniform`, seed 8) before it widens to every continuous group.

### The fourth review's sweep

- **Location:**
  `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/verification/sweep.txt`,
  with `sweep.py` and `sweep_exponential.py` embedded.
- **Relevance:** the reproduction over all 69 groups, 1,065,353,217 values a group, checked
  against the shipped scalar methods on 200,010 values a group before it counts. Its 83 counts
  took 4,236 s on 10 processes and the 9 exponential groups 989 s on 9.
- **What changes:** the rule's last branch; the tests' predicate, now `_unnamed_by_its_display`;
  the pinned values, now read from `tests/data/pinned-values.txt`; `CHANGEDx` and `NCHANGEDx`,
  retired by the fifth review, are not counted.

### The sixth review's floor pass, mutation transcript and cost

- **Location:** `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/`:
  `floor-pass.txt` (with `tree.sh`, which lists both trees by blob), `mutation.txt` (with
  `mutate.sh`) and `cost.txt` (with `cost.py`).
- **Relevance:** how a transcript prints its trees before and after; a scratch copy of the tree a
  mutant, its diff, the tests that fail and the exit status; µs a call in each tree.

### The plugin probe

- **Location:**
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/verification/plugin-probe.txt`.
- **Relevance:** a probe that imports the integration module's `_held_after_a_set` and runs the
  test's own sequence, `initial` loaded before each set.

### The unit tests' helpers

- **Location:** `tests/unit/test_parameters.py`: `_record`, `_nearest_quotient`,
  `_what_a_set_holds`, `_assert_comes_back`, `_unnamed_by_its_display`, `_pinned`.
- **Relevance:** `_nearest_quotient` is the primitive `_what_a_set_holds` is rebuilt on;
  `_record` builds the made-up scales; `_assert_comes_back` is the pattern of the new property's
  helper.

### The integration module's helpers

- **Location:** `tests/integration/test_vital_plugin.py`: `_held_after_a_set`, `_one_of_each`,
  `_pinned`, and the host's `_floats`.
- **Relevance:** the set sequence the new test and the probe both run.
