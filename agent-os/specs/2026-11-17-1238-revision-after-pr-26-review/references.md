# References for the revision after the review of PR 26 (issue #20)

## Similar Implementations

### The issue #20 spec

- **Location:** `agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`
- **Relevance:** the remedy this review is of. Decisions 13 to 20 in its `shape.md` say what was
  built and why. Decision 14, the thread rule's error, is the one finding 3 reverses, and it is
  not edited.
- **Key patterns:** the probe drivers, the child runner and the window polling, each embedded at
  the end of its transcript (`probes-2-alert.txt`, `probes-4-counts.txt`, `remedy-run.txt`,
  `rollback-count.txt`, `marker-count.txt`, `mutation.txt`). The midpoint and alarm probes reuse
  them, and the single rerun runs the four evidence scripts as they are embedded. Its transcript
  wrapper prints the date, the branch, the machine and the tree by blob before and after, is
  written outside the tree, and is copied in afterwards.

### The PR 23 second-review revision

- **Location:** `agent-os/specs/2026-11-16-1509-revision-after-pr-23-second-review/`
- **Relevance:** the form of a review revision.
- **Key patterns:** "What was checked while shaping" before any decision; the owner's answers in
  their own words; a table of where each item went; drafts shown whole and filed only at the
  owner's word; a reply for the owner to post.

### The host's guards

- **Location:** `src/patchbay_vital/host.py` (`_environment_kept`, `_reached`, `_AppKitWatch`,
  `_NoWatch`, `_alert_watch`, `VitalHost._write`, `_marker`, `_unplanted`, `load_state`,
  `measure`) and `src/patchbay_vital/preset.py` (`decode_end`)
- **Relevance:** each finding of 1, 2, 4 to 7, 13 and 14 is in one of them.
- **Key patterns:** one context manager per guard, entered around exactly one call into the
  plugin and put back in a `finally`; nothing pedalboard raises leaving as itself; one guarded
  decoder that turns `RecursionError` into the package's `ValueError`.

### The test doubles

- **Location:** `tests/unit/builders.py` (`StandInWatch`); `tests/unit/test_host.py`
  (`_FakePlugin`, the `fake` fixture, `_REAL_ALERT`); `tests/unit/test_instrument.py`
  (`_FakeVital`, `_lose_step`); `tests/integration/test_vital_instrument.py` (`_in_a_child`,
  `_NEVER_RETURNS`, `_ALERTING`, `_IGNORED`)
- **Relevance:** every new unit test runs over these, and findings 8 and 9 are about the last
  file's children.
- **Key patterns:** a fake plugin that records each call and refuses where the test asks; a
  stand-in watch that fails by name when an alert is raised with no watch in place; a child of
  this interpreter given a time limit, which fails the test by name when it is killed.
