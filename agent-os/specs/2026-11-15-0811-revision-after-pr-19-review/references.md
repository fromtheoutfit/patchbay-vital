# References for the Revision after the Review of patchbay-vital's PR 19

## The review and the issues

- **The review,** the scope: the owner's comment on patchbay-vital's PR 19, of `f26e6bc`,
  https://github.com/fromtheoutfit/patchbay-vital/pull/19#issuecomment-6894640094. Seven
  findings: one bug, three test gaps, three efficiency and cleanup notes.
- **#16,** which the pull request closes: https://github.com/fromtheoutfit/patchbay-vital/issues/16.
- **#18,** the scale's `to_normalized` and `to_preset` raising a built-in. This revision finds
  the finite case and leaves it there.
- **#8,** "From core's review of PR 19", which is fromtheoutfit/patchbay#19, another pull
  request. Neither of its questions is decided here.

## Similar Implementations

### Issue #16's spec

- **Location:** `agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`, its
  `shape.md` and the eight transcripts of its `verification/`.
- **Relevance:** the code this revision changes, the decisions it keeps, and every script the
  evidence reuses, each embedded in the transcript that ran it: `pools.py` and `tree.sh`,
  `indexed_count.py`, `direct_count.py`, `arbitrary_displays.py`, `mutate.sh`,
  `plugin_probe.py`, `cost.py` and their wrappers.
- **What changes:** the tree before the change is `f26e6bc`, the pull request's head, beside
  `main` at `f533b1b`; the direct count runs on three binades, not on every one; each wrapper
  already prints the machine before and after.

### Issue #16's direct count

- **Location:** that folder's `verification/direct-count.txt`, run 2026-11-14 to 15.
- **Relevance:** its class counts say where `to_preset` takes its exception, and so where a
  linear scale calls `holds`: OTHER is 31,879, 176,711 and 99,796 in `volume`'s binades -58, -57
  and -56 and 0 in every other, FELL is 0 throughout, and every value of `env_1_delay` is KEPT.
- **Key pattern:** two pools of processes, each importing one tree, the shipped scalar methods
  called value by value, a stop at once on any difference from `main`.

### The integration module's reader

- **Location:** `tests/integration/test_vital_plugin.py`, `_pinned`.
- **Relevance:** finding 3 gives the unit module's reader the same two checks: a set with no
  value fails by the set's name, and a normalized value outside [0, 1] by the file and the line.

### The unit module's helpers from primitives

- **Location:** `tests/unit/test_parameters.py`: `_nearest_quotient`, `_a_set_lands_on`,
  `_what_a_set_holds`, `_assert_a_set_holds_it`, `_record`.
- **Relevance:** every new test's expected value is worked out with them, and with `fma32` and
  `next_float32`, never with `holds`, `to_normalized` or `_landing`.
