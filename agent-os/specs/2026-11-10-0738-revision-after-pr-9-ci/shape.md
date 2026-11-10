# Revision after PR 9's CI Run — Shaping Notes

Shaped 2026-11-10 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered three questions: how the fix is proven on Linux, the standards, and where the spec lives.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

PR 9's CI gate fails at step 5 on ubuntu-24.04, in
https://github.com/fromtheoutfit/patchbay-vital/actions/runs/42814018117:

```
FAILED tests/unit/test_host.py::test_a_path_the_host_cannot_load_is_named[directory] - AttributeError: /lib/x86_64-linux-gnu/libc.so.6: undefined symbol: fegetenv
FAILED tests/unit/test_host.py::test_a_path_the_host_cannot_load_is_named[file] - AttributeError: /lib/x86_64-linux-gnu/libc.so.6: undefined symbol: fegetenv
2 failed, 321 passed, 88 skipped in 4.90s
FAIL  step 5/6: a test failed, or pytest could not read its configuration (see above)
```

The cause is in `host.py`:
- `_c_library()` returned the first library that loaded, from `find_library("c")` then
  `"ucrtbase"`.
- glibc keeps `fegetenv` and `fesetenv` in its maths library, so on Linux the guard got a C library
  without them.
- The guard's `_LIBC is None` check never fired, and a built-in `AttributeError` left `VitalHost()`,
  which `base/python/errors` ("What escapes") forbids.
- On macOS the C library holds both functions, so the local gate passed. Checked with this tree's
  interpreter:

```
c /usr/lib/libc.dylib True True
m /usr/lib/libm.dylib True True
```

Scope: the fix and its tests, on PR 9's branch, so PR 9 carries it. CHANGELOG entry, gate green,
`verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** the CI failure, in the owner's words "let's make that fix before I review the
  pr".
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, plus `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests` and `vital/plugin-state`. Snapshot in `standards.md`.
- **Linux proof:** a Docker run, with the owner's condition: "make sure the Linux run actually
  exercises the fix: CI has no Vital, so the fegetenv/fesetenv lookup must happen in a unit test
  that runs without the plugin (resolve the symbols, save and restore the environment once), or
  the container proves nothing the push wouldn't. Starting Docker Desktop is fine; it's installed,
  not being installed."
- **Folder:** a new revision folder, this one.

## Decisions

1. **Scope:** the fix and its tests, as a revision spec. Nothing else in Spec A
   (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`) changes, and its folder stays
   as handed over.
2. **Linux proof before the push:** a Docker run of the gate on a copy of the tree, as CI runs it:
   `ubuntu:24.04` `linux/amd64`, the uv `pyproject.toml` pins, `uv sync --locked`, then
   `scripts/gate.sh`. The working tree and its `.venv` are never touched.
3. **The run exercises the fix:** CI has no Vital, so the lookup and a real save and restore of the
   environment are unit tests that need no plugin.
4. **Standards:** as Step 5 above.
5. **Folder:** a new revision folder, as the PR 3, 5 and 6 revisions had.
6. **The lookup:** try `find_library("c")`, then `find_library("m")`, then `"ucrtbase"`. Keep the
   first library that loads *and* holds both functions. No library holding them is the existing
   `PluginLoadError`.
7. **Evidence the two failing tests then pass on Linux:** pedalboard 0.9.26 refuses a path it
   cannot load with `pybind11::import_error` on Linux too ("unsupported plugin format or load
   failure"; `ExternalPlugin.h` in the installed package, GPLv3, read for the fact only). The
   container run confirms it.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a; `errors` names the defect (a built-in escaping a public method)

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `src/` and `tests/` changing under what
  it copies
- `base/process/standards-retrospective` and `base/process/standards-index` — the project standard
  this corrects, and the amendment to a base proposal still open
- `base/process/ownership` — the owner commits and pushes
- `base/testing/tests` — tests of the module's private guard, and the platform's constant picked by
  name with a skip elsewhere
- `vital/plugin-state` — its process rule names the C library's `fegetenv`

## Found while building

- **The minimal `ubuntu:24.04` image lacks `libatomic.so.1`**, which pedalboard's native module
  links. The first container run failed at step 5 with `ImportError: libatomic.so.1` before any
  test ran; CI's runner image has it (CI imported pedalboard). The container installs `libatomic1`,
  and `verification/linux-gate-run.txt` says so. Nothing in the repository changes for it.
- **The pass-over case where libc fails to load and `ucrtbase` holds both passes on the old code
  too**, since the old lookup tried `ucrtbase` after libc. The other two cases fail on it
  (`verification/old-behaviour.txt`).
- **Upward rounding shows under the container's amd64 emulation**, so the restore test needed no
  fallback to comparing `fegetenv`'s bytes.

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script under
`scripts/` as git lists them, with no tracked file a `.gitignore` ignores; `uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml` and
`uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set
and `uv.lock`'s pins; and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the
commit in `agent-os/standards/base/.version` — and the three judgment steps are recorded, in this
order: Docs, Version, then the standards retrospective below.

**Results (2026-11-10):** exit 0 on branch
`feature/7-the-host-and-the-parameter-map-load-vital-through-pedalboard-map-all-903-parameters-to-preset-keys-and-pass-cores-contract-tests-as-a-real-instrument`,
`verification/gate-run.txt`, 417 tests, the plugin's integration tests among them and not skipped.
- **On Linux, before the push:** `verification/linux-gate-run.txt` is the gate on `ubuntu:24.04`,
  linux/amd64, at uv 0.13.7. It exits 0 with 329 passed and 88 skipped, the skips being the plugin
  tests, as on CI, and this revision's host tests all run.
- **The old lookup:** `verification/old-behaviour.txt` holds CI's failing lines, then the same
  container with `host.py` put back at `1fb324f`. That run has 7 failed, CI's two among them, each
  new test the old lookup breaks failing.
- **The negative harness:** no gate file changed, and no file under what it copies was added,
  removed or renamed, but `src/`, `tests/` and `agent-os/standards/` changed, so it was rerun on
  the final tree. `verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
  `verification/ci-negative-test.txt` `3 runs, 0 unexpected`.
- **CI's own run** of this revision exists only after the owner's push.

**Docs (step 7):** checked against the shipped files, and each reads true:
- `src/patchbay_vital/host.py`: the module docstring says where `fegetenv` and `fesetenv` come
  from; `_c_library`'s docstring gives the order and why a library that loads is still passed
  over; `VitalHost`'s refusal names the two functions.
- `tests/unit/test_host.py`: its module docstring says the file holds what needs no plugin, the
  guard included.
- `README.md`, `CLAUDE.md` and `agent-os/product/`: unchanged. None names the C library or the
  floating-point guard.
- `agent-os/standards/vital/plugin-state.md`: corrected in the retrospective below.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** a guard around native code, held by unit tests that need no
   native code, so a CI without it runs them. Added to `vital/plugin-state.md`, and to the base
   proposal still open (below).
2. **A standard wrong or stale:** `vital/plugin-state.md` said the C library's `fegetenv`, which
   glibc proves wrong. So did the third proposal of `fromtheoutfit/patchbay-standards#34`, filed by
   the spec this revises.
3. **A deliberate deviation:** none.
4. **A pointer moved:** none.

The retrospective's own change set, to commit apart from the fix:

- `agent-os/standards/vital/plugin-state.md` — the process rule:
  - the functions come from the first library holding both (the C library on macOS, the maths
    library on glibc);
  - a new rule that unit tests needing no plugin hold the guard;
  - the evidence line names this revision's folder.

  Verified against `host.py` (`_c_library`, `_environment_kept`), `tests/unit/test_host.py` (the
  four tests the rule names), `verification/linux-gate-run.txt` and `verification/old-behaviour.txt`.
- `agent-os/standards/index.yml` — the `vital:` section's `plugin-state` description follows it;
  the `base:` section is the sync's and unchanged.

**Which side each rule fell on, and why.** Where Vital's host finds the functions, and which tests
hold them here, are this repository's and stayed in `vital/plugin-state`. The same correction to
the rule any adapter loading native code follows went upstream as a revision of the proposal that
stated it, still open and unshaped.

Proposals sent upstream: fromtheoutfit/patchbay-standards#34

### Standards retrospective (proposed, base)

- `base/testing/tests.md` — a revision of `fromtheoutfit/patchbay-standards#34`'s third proposal
  (the floating-point environment). Both corrections were approved by the owner, 2026-11-10:
  - `fegetenv` and `fesetenv` come from the first library that holds both, the C library on macOS
    and the maths library on glibc; a library that loads without them is passed over, never
    trusted.
  - Unit tests that need no native code hold the guard, the lookup and one real save and restore,
    so a CI without the plugin runs them.

  Verified against `src/patchbay_vital/host.py` (`_c_library`), `tests/unit/test_host.py`,
  `verification/linux-gate-run.txt` and `verification/old-behaviour.txt`. Proposed, not applied.
  Filed by editing #34's body in place with a "Revised 2026-11-10" paragraph and proposal 3
  rewritten, as the owner directed and as every revised issue so far has been.
