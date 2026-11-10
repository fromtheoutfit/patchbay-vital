# References for the Revision after the Third Review of PR 9

## Similar Implementations

### A revision after a review

- **Location:** `agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`
- **Relevance:** the shape of a review revision on this same branch: a table of findings and
  outcomes in `shape.md`, each declined one with its reason, `verification/old-behaviour.txt`, the
  revision's tests run against the code as reviewed. Its Decision 2 is the reason finding 8 is
  declined a third time; its Decision 5 (every reach its own guard) is the rule finding 9 would
  break.

### Files replaced whole or not at all

- **Location:** `src/patchbay_vital/files.py` (`replace_files`, `_rename_each`, `_sync_directory`)
  and `tests/unit/test_files.py`
- **Relevance:** findings 1 and 2. The staging and the put-back stay; what is read before a
  rename, and when and how the directory is synced, change. The tests' monkeypatched `os.fsync`
  and `Path.replace` are the shape the new tests take.

### The fake plugin

- **Location:** `tests/unit/test_host.py` (`_FakePlugin`, `_FakeParameter`, the `fake` fixture)
- **Relevance:** findings 3, 5, 6 and 7. The fake records every call and the rounding mode it
  is entered with; this revision gives it a second host id bound to the same value (so one load
  per measurement shows against one per parameter) and a state whose text holds no settings
  object.

### The census's main tests

- **Location:** `tests/unit/test_census.py` (`_FakeHost`, `_host`, `_main`)
- **Relevance:** finding 4. A one-parameter fake host writes a two-key list; once the census
  refuses a list that forgets a known key, these tests set the known keys to the fake's.

### A refusal in the shape of `_whole`

- **Location:** `src/patchbay_vital/host.py` (`_whole`)
- **Relevance:** finding 6. A bool refused by name, then the built-in's `TypeError` turned into
  the package's error, chained; `set`'s normalized value follows the same shape with `math.isfinite`.

### pedalboard's parameters

- **Location:** `.venv/lib/python3.12/site-packages/pedalboard/_pedalboard.py`,
  `AudioProcessorParameter.__init__` (lines 284-330) and `ExternalPlugin.parameters` (653-680)
- **Relevance:** finding 9's reason. `plugin.parameters` is Python that steps `x / search_steps`
  and parses the plugin's texts between native calls, so the guard around it hands that work the
  process's environment; one guard around the load's four calls would hand it the flush-to-zero
  `VST3Plugin` left.

### The review

- **Location:** the fifth comment on https://github.com/fromtheoutfit/patchbay-vital/pull/9,
  2026-11-10 19:26Z, "Review findings: `main...HEAD`", at `d4fe077`
- **Relevance:** the 12 findings, each a row of `shape.md`'s table.
