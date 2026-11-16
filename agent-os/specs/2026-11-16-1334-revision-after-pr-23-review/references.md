# References for the revision after PR 23's review

## Similar Implementations

### The instrument spec (issue #8)

- **Location:** `agent-os/specs/2026-11-15-1448-the-instrument/`
- **Relevance:** the spec PR 23 ships; every finding is against its code and its decisions.
- **Key patterns:**
  - Decisions 2 (the start preset), 4 (a float in exactly one place), 7 to 9 (what a set holds,
    the keep rule, between steps), 13 (events), 17 (MIDI) and 24 to 29 (the probes' decisions).
  - `verification/off-grid-count.txt` and `carrying-count.txt`: counts whose scripts are
    embedded in the transcript, with the tree and the machine printed before and after.
  - `verification/mutation.txt`: one mutant per decided rule on a scratch copy, each failing a
    named test.
  - `verification/probes.txt`: a probe of Vital in a process of its own, killed after a time
    limit where a load can block.
  - Draft 4, the 0.1.0 proposal, held in its `shape.md` until the PR merges.

### The revision after PR 19's review

- **Location:** `agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`
- **Relevance:** the shape of a review round on this repository: findings by number, decisions,
  counts and probes as transcripts, and a reply for the owner to post.
- **Key patterns:** "For the owner to post on patchbay-vital's PR 19; not posted by an agent",
  one numbered line per finding, Fixed or Declined with the reason.

### Core at eddba95

- **Location:** `.venv/lib/python3.12/site-packages/patchbay/` (`contracts.py`, `models.py`,
  `testing/contract_tests.py`, `testing/fake.py`)
- **Relevance:** the protocol's words the findings are judged by: `Patch`'s "a value for each
  parameter", `load_patch`'s "changing nothing", and the fake's "a sine per note … cut at the
  note's end".
