# References for the revision after the second review of PR 26 (issue #20)

## Similar Implementations

### The first revision after the review of PR 26

- **Location:** `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`
- **Relevance:** the round before this one, on the same code. Its Decisions 2, 5, 6, 9 and 11 are
  the ones this review's findings 4, 15, 8, 12 and 13, and 11 return to.
- **Key patterns:** the form of a review revision: what shaping checked before any decision, the
  owner's answers in their own words, one line of the reply for each finding, drafts shown whole
  and filed only at the owner's word. `verification/costs.txt` holds the figures findings 12 and
  13 were declined on, and the `otool -L` lines the fork-safety point is recorded with.
  `verification/mutation.txt` lists the mutants this revision's run repeats, and the evidence
  scripts (`remedy-run.txt`, `rollback-count.txt`, `marker-count.txt`) are embedded at the end
  of their transcripts.

### The issue #20 spec

- **Location:** `agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`
- **Relevance:** the remedy both reviews are of.
- **Key patterns:** the transcript wrapper, which prints the date, the branch, the machine and
  the tree by blob before and after, is written outside the tree and copied in afterwards.
  `verification/probes-1-costs.txt`, `probes-2-alert.txt` and `probes-4-counts.txt` hold the
  trial child's figures the reply to finding 19 quotes.

### The host's guards

- **Location:** `src/patchbay_vital/host.py` (`_environment_kept`, `_reached`, `_AppKitWatch`,
  `_appkit_watch`, `VitalHost._write`, `_set_back`, `_unplanted`, `load_state`, `_planted`,
  `_settings`) and `src/patchbay_vital/preset.py` (`decoded`)
- **Relevance:** findings 1, 2, 6, 8 and 10 are each in one of them, and finding 7's fix is
  `decoded`.
- **Key patterns:** one context manager per guard, put back in a `finally`; nothing pedalboard
  raises leaving as itself; the write's own error leaving as itself, with a failed set-back
  noted on it; one guarded decoder that turns `RecursionError` into `ValueError`.

### The test doubles

- **Location:** `tests/unit/builders.py` (`StandInWatch`); `tests/unit/test_host.py`
  (`_FakePlugin`, `_FakeParameter`, the `fake` fixture, `_StandInMethod`, `_watch_over`,
  `_ThroughTheCallback`, `_nested`, `_first_depth_the_decoder_refuses`);
  `tests/unit/test_instrument.py` (`_FakeVital`)
- **Relevance:** every new unit test runs over these.
- **Key patterns:** a fake plugin that records each call and refuses where the test asks; the
  real `_AppKitWatch` built from stand-in runtime calls, so the shipped class is tested on every
  platform; the decoder's limit bisected from `DECODER` in the test, never a guessed number.
