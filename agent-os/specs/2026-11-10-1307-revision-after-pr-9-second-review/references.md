# References for the Revision after the Second Review of PR 9

## Similar Implementations

### A revision after a review

- **Location:** `agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`
- **Relevance:** the shape of a review revision on this same branch: a table of findings and
  outcomes in `shape.md`, each declined one with its reason, the base proposals presented and
  filed, and `verification/old-behaviour.txt`, the revision's tests run against the code as
  reviewed, each failure a finding. Its Decision 7 is the reason finding 12 is declined again.

### Deep nesting turned into the package's error, twice

- **Location:** `src/patchbay_vital/preset.py` (`_json_section`) and `src/patchbay_vital/state.py`
  (`_object_end`)
- **Relevance:** the copy finding 15 names: both call `DECODER.raw_decode` and turn
  `RecursionError` into `ValueError`. `preset.decode_end` is the one place that now does it; each
  keeps its own first-byte and end checks.

### A file replaced whole or not at all

- **Location:** `src/patchbay_vital/files.py` (`replace_file`) and `tests/unit/test_files.py`
- **Relevance:** the staging, mode-keeping and rename `replace_files` generalises to several
  files, and the tests it mirrors: a failed write, the mode kept, a symlink followed.

### The fake plugin

- **Location:** `tests/unit/test_host.py` (`_FakePlugin`, `_FakeParameter`, the `fake` fixture)
- **Relevance:** pedalboard's plugin as the host sees it, turning upward rounding on at every
  call. This revision has it record the rounding mode each call is entered with (finding 3), drop
  a key from a grid row (finding 8), report another version (finding 2) and refuse any read
  (finding 1).

### The review

- **Location:** the third comment on https://github.com/fromtheoutfit/patchbay-vital/pull/9,
  2026-11-10 18:02Z, at `0fc8152`
- **Relevance:** the 17 findings, each a row of `shape.md`'s table.
