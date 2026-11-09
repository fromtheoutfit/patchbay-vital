# Tech stack

The decisions already made, implemented by the bootstrap spec (issue #1,
`agent-os/specs/2026-11-09-1115-bootstrap-and-toolchain/`), whose `shape.md` holds each departure
from patchbay and each dependency as a Decision with its reason. Each is one line here;
`pyproject.toml` is the configuration, and the standard that names it is
`agent-os/standards/base/python/toolchain.md`, synced in from `patchbay-standards`, which every spec
here includes (Step 5a of `/agent-os:shape-spec`).

- **uv** manages the project and **`uv_build`** builds it; the lockfile is committed. Tools the gate
  runs are pinned exactly in `pyproject.toml`'s `[dependency-groups] dev`, resolved in `uv.lock`, and
  run through `uv run --locked`. uv itself is pinned by `[tool.uv] required-version`, which CI's
  setup-uv reads too.
- **Python >= 3.12** (`requires-python`; `.python-version` pins the interpreter).
- **ruff** for linting and formatting, with `select = ["ALL"]`; every disabled rule is named with
  its reason.
- **mypy --strict** over the package and the tests.
- **pytest** for tests and **hypothesis** for property-based ones.
- **src layout**: `src/patchbay_vital/`, typed (`py.typed`); distribution `patchbay-vital`, import
  `patchbay_vital`.
- **`patchbay-core`** is not a dependency yet. It is added by the spec that first imports it, as a
  Decision there, with any other runtime dependency that spec needs.
