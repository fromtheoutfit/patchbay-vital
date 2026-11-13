# Gate spec: move the patchbay-core pin to eddba95, say what the integration marker needs, and let cases n and o follow their pins (issue #11)

## Context

Issue #11 (https://github.com/fromtheoutfit/patchbay-vital/issues/11). Issue #8 will end by proposing
patchbay-core 0.1.0 because core's contract tests pass against Vital, so the run it cites must be
against the core being released. The pin is `dd2bcad` (core's PR 15); core's `main` is `eddba95`,
which carries fromtheoutfit/patchbay#18 (`Instrument.get` says what an adapter relies on). The
`integration` marker reads "needs an installed Vital's presets", but `test_vital_plugin.py` carries it
and needs the plugin. Both entries are gate sections of `pyproject.toml`, so this is their gate spec,
landed before #8 resumes (precedent: issue #4). While shaping, the owner widened the scope to harness
cases n and o, which still hard-code their pins and were left by the PR 5 revision "for this
repository's next gate spec".

Branch: `feature/11-gate-move-the-patchbay-core-pin-to-the-head-carrying-patchbay18-and-say-what-the-integration-marker-needs`
(checked out, clean at `558b85b`). No stage, commit, push or PR.

## Found while shaping (scratch copy outside the repository; the tree untouched)

- `git ls-remote …/patchbay refs/heads/main` → `eddba954…`: core's `main` has not moved. Core is
  `0.0.1` there with unchanged `[project] dependencies`, so `>=0.0.1,<1` still fits.
- Re-lock (uv 0.13.7): `Updated patchbay-core v0.0.1 (dd2bcad6) -> v0.0.1 (eddba954)`; the diff is
  two lines, both patchbay-core's source (`uv.lock:475` `source`, `uv.lock:511` `requires-dist`).
- Gate against the new pin, nothing else edited: exit 0, `490 passed`, as at `dd2bcad`.
- Nothing in `src/`/`tests/` constructs an `Event`, implements `Instrument` or runs the contract tests,
  and `VitalHost.get`/`set` promise nothing core's new wording touches: no adapter code is forced.
- t and y unchanged, run from that copy with the new pin and the new marker text: `7 runs, 0 unexpected`.

## Decisions (for shape.md)

1. **Scope is issue #11**, revised in place 2026-11-11 to add cases n and o (owner's answer).
2. **`[tool.uv.sources]` rev `eddba95404a9b633d358dc4d6b07b084a8f975ad`**, read by `git ls-remote`, never
   from the sibling checkout (on a feature branch). Its comment reads true as written.
3. **Range unchanged**: core declares 0.0.1 at that commit; `tests/unit/test_package.py` holds it.
4. **Marker text** (the issue's): `"integration: needs an installed Vital, its plugin or its presets;
   skipped with its reason where that is absent"`. The skip where the map was measured on another
   machine is the parameter map's rule (`agent-os/standards/vital/parameter-map.md:33`, the `vital`
   fixture), so the marker does not repeat it. Who needs what: `test_vital_plugin.py`'s 12 cases the
   plugin (`test_every_installed_preset_loads_as_state` the presets too); `test_factory_round_trip.py`'s
   76 preset cases the presets; `test_the_manifest_holds_the_expected_count` nothing installed, marked
   by its module's `pytestmark` — unmarking it is test code, outside this gate spec (retrospective note).
5. **t and y unchanged**: `setrev` matches any rev and `912987a` is still an ancestor of `eddba95`; y's
   `sed` matches the block's form and `! grep -q '^markers'` dies if it fails. No assertion changed, so
   no mutation is owed; the PR 5 revision's `verification/guard-mutations.txt` M1–M8 stand.
6. **n and o match their pin's form, whatever value is there**, as `setrev` does for t, citing the PR 5
   revision's note (`agent-os/specs/2026-11-09-1433-revision-after-pr-5-review/shape.md`, "Noted, not
   fixed"). Each carries mutation evidence. Nothing else in the harness changes.
7. **No adapter code**: the newer core forces none.

## Tasks

### Task 1: Revise the issue, save spec documentation

- `gh issue edit 11 --body-file <scratch file>`: the body as it is, plus a "Revised again 2026-11-11, at
  the owner's word" paragraph (cases n and o join; the PR 5 revision left them for the next gate spec)
  and a Scope bullet: *Negative tests `n` (a dev pin edited, the lockfile left) and `o` (`required-version`
  not the running uv) match their pin's form, whatever value is there, as `setrev` does for `t`, each
  with its mutation evidence; nothing else in the harness changes.* The body's closing attribution line
  is not carried over (CLAUDE.md, "No AI attribution").
- `agent-os/specs/2026-11-11-1011-gate-core-pin-and-marker-needs/`: `plan.md`, `shape.md` (Decision 1
  cites #11; shaping answers; Decisions above), `standards.md` (core five + `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/ownership`, `base/testing/tests`,
  `vital/preset-tests`, full text, base at `e31f7db`), `references.md` (issue #4's spec and its PR 5
  revision: `probes.txt` P4, `guard-mutations.txt`; harness cases n, o, t, y and `setrev`). None of these
  is a file the gate's tools read.

### Task 2: The pin first, and the gate on it before any other edit

- `pyproject.toml:76` rev → `eddba95…`; `uv lock` → `verification/lock-change.txt` (uv's line; packages
  at `main` and now; added/removed/moved none; ruff 0.17.4, mypy 2.4.1, pytest 9.2.0; `git diff main --
  uv.lock`). **Anything but patchbay-core's source moves: stop.**
- `scripts/gate.sh` → `verification/new-pin-gate.txt`. A failure is the newer core's: fixed only if
  forced, each change named in `shape.md`.

### Task 3: The marker

`pyproject.toml:167`: the one entry rewritten to Decision 4's text, the block's form kept
(`markers = [`, one string line, `]`). The comment above it already reads true.

### Task 4: Cases n and o (`scripts/gate-negative-tests.sh:406-422`)

- **n:** `sed -E 's/^(    "ruff==)[^"]+"/\10.17.3"/'`, whatever ruff's pin is; setup guards: the line
  rewritten, and the harness stops by name if the pin already was `0.17.3`. `hdr`: "the ruff pin changed
  to ruff==0.17.3, whatever it is now". Run lines and expected text unchanged.
- **o:** `sed -E 's/^required-version = "[^"]*"$/required-version = "==0.13.6"/'`, whatever is there;
  the running uv's version read once from `uv --version` (setup guard: a version, and not `0.13.6`);
  the expected line becomes `` error: Required uv version `==0.13.6` does not match the running version `$running` ``.
- Header lines 67-70 checked; edited only where one reads false. t, y and every other case untouched.

### Task 5: Evidence for n and o

- `verification/guard-mutations.txt`, the PR 5 revision's form (a throwaway script in the scratchpad,
  each mutation a fresh copy, which must come back UNEXPECTED, harness exit 1):

  | Mutation (in `scripts/gate.sh`) | Cases |
  |---|---|
  | M1: step 2's sync loses `--locked` | n |
  | M2: step 2's sync status ignored | n, o |
  | M3: step 2's reason put back as it was before the PR 5 revision | n, o |

- `verification/pin-moves.txt`: the change does what it says. A copy with ruff pinned `0.17.2` and
  re-locked, and one with `required-version = "==0.13.8"`: the shipped n and o each run as expected;
  `main`'s harness stops at setup (`n: pin not rewritten`, `o: required-version not rewritten`, exit 2).
  The `==0.13.8` copy also shows o's expected text names the running uv, not the pin.

### Task 6: Docs

Checked, edited only where false: `pyproject.toml` (header; dependencies, sources, markers and dev-group
comments), `README.md`, `CLAUDE.md`, `agent-os/product/tech-stack.md`, the harness header (n, o, t, y,
line 113), `agent-os/standards/vital/preset-tests.md` (names no marker text).

### Task 7 (FINAL): Verification gate

1–6. `scripts/gate.sh`, exit 0.
Gate files changed, so the whole harness reruns, one run per transcript, in the background:
`scripts/gate-negative-tests.sh` → `verification/gate-negative-tests.txt` (ends `N runs, 0 unexpected`);
`scripts/gate-negative-tests.sh j` → `verification/ci-negative-test.txt`.
7. **Docs**, recorded in `shape.md`.
8. **Version**: `CHANGELOG.md` `[Unreleased]` `### Changed`: the pin `dd2bcad` → `eddba95`
   (patchbay#18), the marker's text, n and o following their pins, the spec folder; version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff. Expected: no project standard change;
   the manifest-count test's marker as a note for the next spec in that module; candidate base evidence
   for fromtheoutfit/patchbay-standards#30 (a second spec existing only for a dependency source and a
   marker's registration) and #31 (n and o now match any value of their pin). Presented with
   AskUserQuestion; approved ones filed or added as the owner says, no attribution; `Proposals sent
   upstream:` written.

Then `scripts/gate.sh` → `verification/gate-run.txt`, first line the date and branch, the last act.
Stop and print `git status --short`.

## Verification

- `git diff main -- uv.lock` is the two patchbay-core source lines; step 2's sync names `eddba95`.
- `scripts/gate.sh` exits 0; the harness transcript and j's each end `0 unexpected`.
- `guard-mutations.txt`: 3 mutations, each as required; `pin-moves.txt`: shipped n and o as expected,
  `main`'s stopping at setup.
