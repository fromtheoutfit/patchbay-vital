# The patchbay-core Pin at eddba95 and the Integration Marker — Shaping Notes

Shaped 2026-11-11 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered four questions: the marker's text, cases n and o, the mutations owed, and Steps 2 to 5
together.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #11, revised in place 2026-11-11 at the owner's word: `[tool.uv.sources]` moves
`patchbay-core` to `eddba95`, the head of core's `main` carrying fromtheoutfit/patchbay#18, with
`uv.lock` re-locked; the `integration` marker says what its tests need; negative tests t and y rerun,
and n and o made to match their pins whatever the value. A gate spec: its feature is the gate's own
files. Landed before #8 resumes on top of it. CHANGELOG entry, gate green,
`verification/gate-run.txt`, the harness rerun. No stage, commit, push or PR by an agent.

## Shaping answers

- **Step 1, scope:** issue #11, the prompt naming it the spec's scope; widened by the owner to cases
  n and o (Decision 6), the issue's body revised in place to say so.
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged; `agent-os/product/tech-stack.md`'s
  `patchbay-core` line names no commit, so it stays true.
- **Step 5, standards:** the core five, and `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/ownership`, `base/testing/tests` and
  `vital/preset-tests`. Snapshot in `standards.md`, base at `e31f7db`.

## Found while shaping

On a scratch copy of the tree at `558b85b`, outside the repository, before any change to the tree:

- `git ls-remote https://github.com/fromtheoutfit/patchbay refs/heads/main` gave
  `eddba95404a9b633d358dc4d6b07b084a8f975ad`: core's `main` had not moved past the commit the issue
  names. Core declares `version = "0.0.1"` there, and its `[project] dependencies` are unchanged
  since `dd2bcad`.
- The rev moved and `uv lock` run: uv's `Updated patchbay-core v0.0.1 (dd2bcad6) -> v0.0.1
  (eddba954)`, and two lines of `uv.lock` changed, both patchbay-core's source.
- The gate on that copy, the rev and the lock the only change: exit 0, 490 passed, as on the same
  copy at `dd2bcad`.
- Cases t and y, run from that copy with the new marker text too: `7 runs, 0 unexpected`.

The same steps on the tree are this spec's record (`verification/lock-change.txt`,
`verification/new-pin-gate.txt`).

## Decisions

1. **The scope is issue #11**: https://github.com/fromtheoutfit/patchbay-vital/issues/11, revised in
   place 2026-11-11 to add cases n and o.
2. **`[tool.uv.sources]` pins `patchbay-core` at `eddba95404a9b633d358dc4d6b07b084a8f975ad`**, read by
   `git ls-remote` from GitHub and never from the sibling checkout `../patchbay`, which sits on a
   feature branch. Its comment, "at the head of its main when this was written", reads true as
   written and is unchanged.
3. **The range stays `patchbay-core>=0.0.1,<1`**: core declares 0.0.1 at that commit, and
   `tests/unit/test_package.py` holds the installed version to the declared range (uv does not:
   issue #4's `verification/probes.txt`, P4).
4. **The marker reads "integration: needs an installed Vital, its plugin or its presets; skipped with
   its reason where that is absent"**, the issue's words. Who needs what:
   - `tests/integration/test_vital_plugin.py`, 12 cases: the plugin at the host's `DEFAULT_PATH`,
     through the `vital` fixture; `test_every_installed_preset_loads_as_state` the presets too.
   - `tests/integration/test_factory_round_trip.py`, 77 cases: 76 the presets, through the
     `presets_root` fixture; `test_the_manifest_holds_the_expected_count` nothing installed. It reads
     the committed manifest and is marked by its module's `pytestmark`. Unmarking it is test code,
     outside this gate spec: a note in the retrospective for the next spec that touches that module.

   The plugin's tests also skip where the map was measured on another machine. That is the parameter
   map's rule (`agent-os/standards/vital/parameter-map.md`, "The map records the machine the census
   ran on"; the `vital` fixture), so the marker does not repeat it.
5. **Cases t and y are unchanged.** t's `setrev` rewrites the rev whatever it is, `912987a` is still an
   ancestor of `eddba95` and so still "an earlier commit of patchbay's main", and its range edit
   matches any range. y's `sed '/^markers = \[$/,/^\]$/d'` matches the block's form, not its text, and
   `! grep -q '^markers'` stops the harness by name if it did not take; pytest's "'integration' not
   found" line does not depend on the description. No assertion of either changed, so
   `base/process/verification-gate.md` owes no mutation: the PR 5 revision's
   `verification/guard-mutations.txt`, M1–M8, stands as their evidence. Each of their failing runs
   still has to fail with its named reason or come back UNEXPECTED, and does
   (`verification/gate-negative-tests.txt`).
6. **Cases n and o match their pin's form, whatever value is there**, as `setrev` does for t. The
   revision after the review of PR 5 left them for this repository's next gate spec
   (`agent-os/specs/2026-11-09-1433-revision-after-pr-5-review/shape.md`, Standards Retrospective,
   "Noted, not fixed"); the owner put them in this one. n sets the ruff pin to `ruff==0.17.3` whatever
   it was; o sets `required-version` to `==0.13.6` whatever it was and names the running uv's version
   as `uv --version` prints it, where it spelled `0.13.7`. Each stops the harness by name when its
   value is already the one it sets. Their assertions changed, so each carries its mutations
   (`verification/guard-mutations.txt`), and `verification/pin-moves.txt` shows both following a moved
   pin where `main`'s harness stops at setup. Nothing else in the harness changes.
7. **No adapter code.** Against the newer core the gate passes unchanged (`verification/new-pin-gate.txt`):
   nothing in `src/` or `tests/` constructs an `Event` or `ParameterChanged`, implements `Instrument` or
   runs the contract tests, which are #8's, so `Event.at`'s wider refusal reaches nothing here;
   `VitalHost.get` and `set` promise nothing about what `get` returns after `set`, the wording #18
   changed; `errors.py`'s docstring speaks of core's error types, which did not change.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A; `tech-stack.md` reads true.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — a gate spec: a pin moved, a rule-set value changed, cases n and
  o changed with their mutations, the harness rerun
- `base/process/standards-retrospective` — the evidence this spec adds upstream
- `base/process/ownership` — the owner lands this spec, and #8 waits for it
- `base/testing/tests` — where the integration tests and the harness's marked test live
- `vital/preset-tests` — what the integration tests need and how they skip

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script under
`scripts/` as git lists them, with no tracked file a `.gitignore` ignores; `uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`, `uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule
set and `uv.lock`'s pins; and `scripts/sync-standards.sh --check` against `../patchbay-standards` at
the commit in `agent-os/standards/base/.version` — and the three judgment steps are recorded, in this
order: Docs, Version, then the standards retrospective below.

**Results (2026-11-11):** exit 0 on branch
`feature/11-gate-move-the-patchbay-core-pin-to-the-head-carrying-patchbay18-and-say-what-the-integration-marker-needs`,
`verification/gate-run.txt`, the last act before hand-over. Before any other edit, the gate against
the new pin: exit 0, 490 passed, `verification/new-pin-gate.txt`. `verification/lock-change.txt`: no
package added, removed or moved, patchbay-core's source alone moved, two lines of `uv.lock`; ruff
0.17.4, mypy 2.4.1 and pytest 9.2.0 where they were. Gate files changed, so the whole harness was
rerun, one run per transcript: `verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected`,
n, o, t and y among them, and `verification/ci-negative-test.txt` (j) `3 runs, 0 unexpected`.
`verification/guard-mutations.txt`: 3 mutations through n and o, 3 as required.
`verification/pin-moves.txt`: 4 runs, 4 as required. The hosted run exists only after the owner's
push, and is not claimed here.

**Docs (step 7):** checked and reads true against the shipped files:
- `pyproject.toml`: the header (`[tool.uv.sources]` "the commit of patchbay-core they install"), the
  comment on `dependencies` (uv does not check the range against a git source; the test does,
  negative test t), the comment on `[tool.uv.sources]` ("at the head of its main when this was
  written", true of `eddba95`; negative test t), `[tool.uv]`'s (negative test o), the dev group's (a
  pin changed without re-locking fails the gate, negative test n) and the one over `markers` ("runs
  at step 5 wherever what it needs is present", negative test y). Unchanged but for the rev and the
  marker's text.
- `README.md`: Layout's `tests/` bullet ("each skips, saying so, where what it needs is absent"), its
  `pyproject.toml` bullet (`[tool.uv.sources]` "pins the commit `patchbay-core` is taken from"),
  Install ("at the commit `[tool.uv.sources]` pins") and the gate section ("its transcripts live in
  the spec that last changed a gate file", now this one). Unchanged.
- `CLAUDE.md`: "`[tool.uv.sources]`' commit of `patchbay-core`" among the gate's files. Unchanged.
- `agent-os/product/tech-stack.md`: the `patchbay-core` line names no commit. Unchanged.
- `scripts/gate-negative-tests.sh`: the header's n, o, t and y entries and its "t resolves an earlier
  commit of patchbay" read true; n's and o's `hdr` lines now say "whatever it is now", and o's that
  it names the running uv as `uv --version` prints it.
- `agent-os/standards/vital/preset-tests.md`: says how the plugin's and the presets' tests skip and
  names no marker text. Unchanged.
- Issue #11's body: revised in place for cases n and o (Decision 1).

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff. No project standard changed, and
`agent-os/standards/index.yml` is untouched: no standard under `agent-os/standards/vital/` names the
old rev, the marker's text or the cases changed, and `vital/preset-tests.md` reads true of both
integration modules as they are.

1. **A pattern no standard covers:** one. Case o's expected line names the running uv's version as
   `uv --version` prints it, and n and o stop the harness by name where the value they set is already
   there: a refinement of a proposal already upstream, below.
2. **A standard wrong or stale:** `base/process/verification-gate.md` still makes every `[tool.*]`
   entry a gate file. This spec is a second one opened only for a dependency's source and a marker's
   meaning: evidence for the proposal already upstream, below. Nothing in `base/` at the pin is
   newly wrong.
3. **A deliberate deviation:** none.
4. **A pointer moved:** none. No standard names the rev, the marker's text or the harness's line
   numbers.

- **Noted, not fixed:** `test_the_manifest_holds_the_expected_count` in
  `tests/integration/test_factory_round_trip.py` carries the `integration` marker through its
  module's `pytestmark` and needs nothing installed, reading only the committed manifest. Unmarking it
  is test code, outside this gate spec; it is for the next spec that touches that module.

Proposals sent upstream: fromtheoutfit/patchbay-standards#30 and #31, revised in place

### Standards retrospective (proposed, base)

- `base/process/verification-gate.md`, "In a consuming project" and "The gate's own files change only
  in their own spec" — proposal 1 of `#30`, gaining evidence: issue #11 was opened for one
  `[tool.uv.sources]` rev and one `markers` string, the host spec of #7 having put tests that need the
  plugin under a marker it could not reword; each entry is still shown read by cases t and y, rerun
  unchanged. Verified against `pyproject.toml`, `verification/lock-change.txt` and
  `verification/gate-negative-tests.txt`. Proposed, not applied; sent as
  fromtheoutfit/patchbay-standards#30, revised in place 2026-11-11 at the owner's word.
- `base/process/verification-gate.md`, "A case states what it rests on" — proposal 2 of `#31`, two
  clauses added: an expected line naming a running tool's version reads it from the tool, and a case
  stops by name where the value it sets is already there. `#31`'s "Consuming projects left behind"
  no longer names this repository. Verified against cases n and o of `scripts/gate-negative-tests.sh`,
  `verification/guard-mutations.txt` M1–M3 and `verification/pin-moves.txt` P1–P2. Proposed, not
  applied; sent as fromtheoutfit/patchbay-standards#31, revised in place 2026-11-11 at the owner's
  word.
