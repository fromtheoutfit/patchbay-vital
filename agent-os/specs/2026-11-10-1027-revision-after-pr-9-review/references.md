# References for the Revision after the Review of PR 9

## Similar Implementations

### A revision after a review

- **Location:** `agent-os/specs/2026-11-09-1610-revision-after-pr-6-review/`
- **Relevance:** the shape of a review revision: a table of findings and outcomes in `shape.md`,
  each declined one with its reason, and `verification/old-behaviour.txt`, the revision's tests run
  against the code as reviewed, each failure a finding.

### The spec this revises

- **Location:** `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/` and its revision
  `agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`
- **Relevance:** the Decisions behind the code the findings touch, and
  `verification/probes-first-attempt.txt`: the crash finding 13 rests on came from pedalboard's
  typed `_parameters` objects fetched once, the native objects, not the Python wrappers its public
  mapping gives. Both folders stay as handed over.

### A file replaced whole or not at all

- **Location:** `src/patchbay_vital/format.py` (`_replace_file`, before this revision), its tests
  `test_a_failed_write_leaves_the_file_as_it_was`, `test_writing_over_a_file_keeps_its_permissions`
  and `test_writing_through_a_symlink_keeps_the_link` in `tests/unit/test_format.py`
- **Relevance:** the body `files.replace_file` takes whole, and the tests `tests/unit/test_files.py`
  mirrors for it.

### Deep nesting turned into the package's error

- **Location:** `src/patchbay_vital/preset.py` (`_json_section`)
- **Relevance:** the pattern `state._object_end` follows: `RecursionError` from the decoder becomes
  `ValueError`, so pydantic reports it and the package's error wraps it.

### pedalboard's parameter wrappers

- **Location:** `.venv/lib/python3.12/site-packages/pedalboard/_pedalboard.py` (pedalboard 0.9.26,
  GPLv3), `ExternalPlugin._get_parameters`, `AudioProcessorParameter.__init__`, `__getattr__` and
  `__setattr__`; read for the facts only, nothing copied
- **Relevance:** `parameters` caches each wrapper in `__python_parameter_cache__` and rebuilds the
  mapping on every access (~3 ms for 903); a wrapper's construction scans 1001 raw values; every
  attribute access fetches the native parameter afresh through `__get_cpp_parameter`. So holding the
  wrappers is safe and holding the native objects is not, which is what finding 13's docs now say.

### The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/9#issuecomment-6770350222
- **Relevance:** the 24 findings, each a row of `shape.md`'s table.
