# Revision after PR 9's CI run: find fegetenv where the platform keeps it

## Context

PR 9's CI gate fails at step 5 on ubuntu-24.04 (run 42814018117): `2 failed, 321 passed, 88
skipped`. Both failures are `tests/unit/test_host.py::test_a_path_the_host_cannot_load_is_named`,
with `AttributeError: /lib/x86_64-linux-gnu/libc.so.6: undefined symbol: fegetenv`.

The cause is in `host.py`:
- `_c_library()` (`src/patchbay_vital/host.py:69`) returns the first library that *loads* from
  `find_library("c")` or `"ucrtbase"`.
- glibc keeps `fegetenv` and `fesetenv` in its maths library, `libm.so.6`, so on Linux the guard
  gets a libc without them.
- The `_LIBC is None` check never fires, and a built-in `AttributeError` escapes `VitalHost()`.
  The base errors standard forbids a built-in leaving a public method.
- On macOS both `libc.dylib` and `libm.dylib` hold the two functions (checked), which is why the
  local gate passed.

The intended outcome: the guard finds the functions on Linux too. A unit test that needs no plugin
exercises the real lookup and a real save and restore, so CI's own run proves it. The gate exits 0
in a Linux container that mirrors CI before hand-over. The owner reviews PR 9 after this.

## Decisions (owner, 2026-11-10)

1. Scope: the fix and its tests, as a revision spec. Nothing else in Spec A changes.
2. **Linux proof before the push:** a Docker run of the gate, `ubuntu:24.04` `linux/amd64` as CI,
   uv 0.13.7, on a copy of the tree. The working tree and its `.venv` are never touched. Starting
   Docker Desktop is fine: it is installed, not being installed.
3. **The run must exercise the fix:** CI has no Vital, so the lookup and a save and restore of the
   environment happen in a unit test that runs without the plugin.
4. **Standards:** the core five, plus `process/verification-gate`, `standards-retrospective`,
   `standards-index`, `ownership`, `testing/tests` and `vital/plugin-state`.
5. **Folder:** a new revision folder, as the PR 3, 5 and 6 revisions had. Spec A's folder stays as
   handed over.
6. **The lookup:** search libc, then libm, then `ucrtbase`, and keep the first library that loads
   *and* has both functions. None found is the existing `PluginLoadError`.
7. **Evidence:** pedalboard raises `ImportError` on Linux for a path it cannot load
   ("unsupported plugin format or load failure", `ExternalPlugin.h` in the installed 0.9.26, read
   for the fact). So once the lookup is fixed, the two failing tests should pass on Linux; the
   container run confirms it.

## Task 1: Save spec documentation

`agent-os/specs/2026-11-10-{HHMM}-revision-after-pr-9-ci/`:
- `plan.md`: this plan.
- `shape.md`: the shaping answers; Decisions 1-7; the CI evidence, which is the run id, the
  failing lines and the macOS check.
- `standards.md`: a snapshot of the standards in Decision 4.
- `references.md`: `host.py`, `test_host.py`, the PR 6 revision's folder (layout,
  `old-behaviour.txt`) and `.github/workflows/gate.yml` (what the container mirrors).
- No visuals.

## Task 2: The fix (`src/patchbay_vital/host.py`)

- `_c_library()` tries `find_library("c")`, then `find_library("m")`, then `"ucrtbase"`.
- It skips a name that is None or fails to load (`OSError`), and returns the first library where
  `hasattr` finds both `fegetenv` and `fesetenv`. Otherwise it returns None.
- The docstring says what was measured: macOS's C library holds both, and glibc keeps them in
  libm (CI's run). No claim goes beyond the evidence.
- `_environment_kept` and `VitalHost.__init__` stay as they are. The None branch's
  `PluginLoadError` now also covers the case where no library holds the functions.

## Task 3: Unit tests without the plugin (`tests/unit/test_host.py`)

Each test reaches the private helpers by import (`from patchbay_vital.host import _c_library,
_environment_kept`) or through `monkeypatch.setattr(host, "_LIBC", ...)`:

- `test_the_floating_point_functions_are_found_where_the_tests_run`: the real `_c_library()`
  returns a library holding both functions. It fails on Linux with the old code.
- `test_a_library_without_them_is_passed_over`: monkeypatched `ctypes.util.find_library` and
  `ctypes.CDLL` fakes. libc lacks the functions, libm has them, and `ucrtbase` raises `OSError`;
  the libm fake is returned. A second case, where none has them, returns None. This proves the
  choice on macOS too, where the real libc would pass.
- `test_the_environment_comes_back_however_the_block_changed_it`: a real save and restore once.
  - Inside `_environment_kept()`, the test sets upward rounding through the found library's
    `fesetround`. Python's own `one + tiny` (runtime values, not folded) then lands on
    `math.nextafter(1.0, 2.0)`, showing the change took effect.
  - After the block, `fegetround()` is the original mode and `one + tiny == 1.0`.
  - `FE_UPWARD` is picked per `platform.machine()`: `0x800` for x86_64/AMD64, `0x400000` for
    arm64/aarch64. An unknown machine skips by name.
  - A `finally` restores the rounding mode, so a failure cannot poison later tests.
- `test_without_the_functions_the_host_refuses_to_load`: with `_LIBC` monkeypatched to None and
  an existing path, `VitalHost` raises `PluginLoadError` naming the floating-point environment.
- If upward rounding doesn't show under the container's amd64 emulation, the restore test falls
  back to comparing `fegetenv`'s bytes before and after. shape.md records the reason.

## Task 4: Linux runs in Docker (scratchpad script, nothing written to the repo but transcripts)

- Start Docker Desktop (`open -a Docker`) and wait for `docker info` with Monitor.
- `linux-gate.sh <mode>` runs in `docker run --rm --platform linux/amd64 ubuntu:24.04`. The repo
  is mounted read-only at `/src` and `../patchbay-standards` at `/standards`. The script:
  - installs `git`, `ca-certificates` and `curl`, then uv 0.13.7 from astral.sh;
  - copies both trees into `/work` with `tar --no-same-owner`, excluding `.venv` and the tool
    caches, and sets `safe.directory '*'`;
  - prints `uname -m` and `uv --version`;
  - runs `uv sync --locked` and `scripts/gate.sh`, then prints `exit=`.
- **`fixed`:** the working tree as it stands. The gate is expected to exit 0 →
  `verification/linux-gate-run.txt`, with the date, branch, image digest and machine.
- **`old-host`:** the same, but `git checkout HEAD -- src/patchbay_vital/host.py` in the copy, so
  the new tests run against the old lookup. Step 5 is expected to fail: the two original tests and
  the new lookup, restore and pass-over tests.
- `verification/old-behaviour.txt` holds CI run 42814018117's failing lines beside this run, which
  shows the container reproduces CI and each new test discriminates.
- A tool the minimal image lacks and the gate needs is apt-installed in the container and named in
  the transcript.

## Task 5 (FINAL): Verification gate

1-6. `scripts/gate.sh` exits 0 locally, with the plugin's integration tests run. The result goes
   to `verification/gate-run.txt` with date and branch, the last act before hand-over. No gate
   file changes, but `src/` and `tests/` change under what the negative harness copies, so
   `scripts/gate-negative-tests.sh` and `j` rerun, with one transcript each.
7. **Docs:** `host.py`'s docstrings and `README.md` (grep for the C library / `fegetenv`), recorded
   in shape.md.
8. **Version:** a `### Changed` entry under `[Unreleased]`: "Revision after PR 9's CI run, ...",
   saying the host finds `fegetenv`/`fesetenv` in the first library holding both (glibc's libm)
   and that unit tests hold the lookup and the restore without the plugin. The version stays
   0.0.1.
9. **Standards retrospective**, from the shipped diff:
   - Candidate project edit: `vital/plugin-state.md`'s process bullet ("the C library's
     `fegetenv`"), to say where the functions are found and that a unit test without the plugin
     holds the lookup and the restore.
   - Candidate base amendment: `fromtheoutfit/patchbay-standards#34`'s third proposal (keep the FP
     environment), adding that the lookup is held by a test that runs without the native code, so
     CI exercises it.
   - Presented to the owner with AskUserQuestion; filed with no attribution as the owner chooses.
     `Proposals sent upstream:` is recorded.

Then stop and print `git status --short`. No stage, commit or push. The report lists the
retrospective's edits apart from the fix. PR 9's description is not edited before the push; the
report gives the one Verification line to add after CI's run.

## Verification

- The `old-host` container run fails at step 5 with CI's `AttributeError`, and the new tests fail
  with it.
- The `fixed` container run exits 0 on linux/amd64.
- The local gate exits 0 with the plugin tests run; the negative harness and `j` end
  `0 unexpected`.
- After the owner's push, CI's gate on PR 9 is green.
