# References for the .vital Format

## Similar Implementations

### patchbay's models and errors

- **Location:** `src/patchbay/models.py` and `src/patchbay/errors.py` of `fromtheoutfit/patchbay` at
  `dd2bcad`
- **Relevance:** `Patch` is the form of a read-only sorted mapping with its wrap serializer and
  coded unhashability, and `opaque` the form of an unread section; every error here is shaped like
  `ParameterNotFoundError`.

### The version test

- **Location:** `tests/unit/test_version.py`
- **Relevance:** hypothesis with a pinned `@example`, and reading a file from pytest's root.

### nlohmann::json

- **Location:** `include/nlohmann/detail/conversions/to_chars.hpp` of `nlohmann/json` at v3.11.3
- **Relevance:** what `src/patchbay_vital/grisu2.py` ports, and what `verification/probes.txt`
  compares it with.
