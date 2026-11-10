# References for the Revision after PR 9's CI Run

## Similar Implementations

### The spec this revises

- **Location:** `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`
- **Relevance:** it shipped `host.py`'s floating-point guard (`verification/float-environment.txt`)
  and stays its own record, as it was handed over.

### The guard

- **Location:** `src/patchbay_vital/host.py` (`_c_library`, `_LIBC`, `_environment_kept`,
  `VitalHost.__init__`)
- **Relevance:** the code the fix changes, and the `PluginLoadError` branch it relies on.

### The host's unit tests

- **Location:** `tests/unit/test_host.py`
- **Relevance:** the two tests CI failed, and where the new tests go. They need no plugin, so they
  run on CI.

### A revision with an old-behaviour transcript

- **Location:** `agent-os/specs/2026-11-09-1610-revision-after-pr-6-review/`
- **Relevance:** its folder layout and `verification/old-behaviour.txt`: the revision's tests run
  against the code as it was, each failure named.

### CI

- **Location:** `.github/workflows/gate.yml`; the failing run
  https://github.com/fromtheoutfit/patchbay-vital/actions/runs/42814018117
- **Relevance:** what the container mirrors: ubuntu-24.04, the uv that `pyproject.toml` pins,
  `uv sync --locked`, then `scripts/gate.sh` from a checkout with `patchbay-standards` beside it.

### pedalboard's load failure

- **Location:** `.venv/lib/python3.12/site-packages/pedalboard/ExternalPlugin.h` (pedalboard 0.9.26,
  GPLv3), read for the fact only
- **Relevance:** on Linux a path it cannot load is `pybind11::import_error` ("unsupported plugin
  format or load failure"), so `test_a_path_the_host_cannot_load_is_named` holds there once the
  guard is fixed.
