# Revision after the Review of PR 12 — Shaping Notes

Shaped 2026-11-11 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered four questions on the findings (case o, the helper, the marker, the proposals upstream),
then one confirming Steps 2 to 5 together and one on the evidence's form.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The review of PR 12 at `8ebce15`, the gate spec of issue #11: 15 findings, four in the harness, five
in the evidence and the record, three in the docs, two simplifications and one of process. All are
addressed. A gate spec: the harness, the `markers` entry of `pyproject.toml` and its comment change.
On the same branch, so PR 12 carries it. CHANGELOG entry, gate green, `verification/gate-run.txt`,
the harness rerun: these last three waited on #13 (Decision 9), and what became of them is under
"Resumed after #13" and Results. No stage, commit, push or PR by an agent; the PR's body and any
reply to the review are the owner's.

## Shaping answers

- **Step 1, scope:** the review's 15 findings, in the owner's words "read through the issues on PR
  12 and address them"; how each is addressed is the owner's answer to four questions (Decisions 3
  to 8).
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `base/process/verification-gate`,
  `base/process/standards-retrospective`, `base/process/ownership`, `base/testing/tests`,
  `vital/preset-tests` and `vital/parameter-map` (for the machine skip the marker's comment names).
  Snapshot in `standards.md`, base at `e31f7db`.

## Found while shaping

- `git log --first-parent dd2bcad..eddba95` in core gives two merges: fromtheoutfit/patchbay#16,
  "Revise the gate and Event.at after the review of PR 15", and fromtheoutfit/patchbay#19, which
  closes issue fromtheoutfit/patchbay#18 (finding 11).
- Nothing in the repository counts marked or skipped tests: case y writes a marked probe of its own,
  and `README.md`, `.github/workflows/gate.yml` and `agent-os/standards/vital/` name no count and no
  `pytestmark`.
- **The marker never skipped the manifest-count test.** pytest skips through the `presets_root` and
  `vital` fixtures, and `test_the_manifest_holds_the_expected_count` takes neither, so it ran and
  passed in CI at `8ebce15` as it did before. Unmarking it changes what the marker says of it, not
  whether it runs.
- The Actions API refuses this checkout's token (HTTP 403, the organization's two-factor rule), so
  CI's log at `8ebce15`, run 43073184618, cannot be read from here; `gh pr checks 12` reads its
  status, `pass`.

## Decisions

1. **The scope is the review**:
   https://github.com/fromtheoutfit/patchbay-vital/pull/12#issuecomment-6803400462.
2. **A new spec folder on this branch**, as the revisions after the reviews of PR 3, 5, 6 and 9
   did. The reviewed folder, `agent-os/specs/2026-11-11-1011-gate-core-pin-and-marker-needs/`,
   stays its record. These sentences of it are corrected here, not there:
   - Decision 6, "Their assertions changed, so each carries its mutations" (finding 12): n's run
     lines and expected text did not change, only its setup; o's expected line did, from `0.13.7`
     to the running version. `verification/guard-mutations.txt`'s heading says the same and is
     corrected likewise.
   - Decision 6, "Each stops the harness by name when its value is already the one it sets"
     (finding 1): true of n, not of o, which checked only the running uv. Decisions 3 and 4 make it
     true of both.
   - Results, "Before any other edit, the gate against the new pin" (finding 5): its transcript
     shows the gate's output and not the tree it ran on. `verification/new-pin-gate.txt` here shows
     both.
   - The Standards Retrospective's second proposal, "Verified against … M1–M3 and … P1–P2"
     (finding 9): none of those runs fires either new guard. `verification/guards/` here does, and
     #31 is revised to cite it (Decision 8).
   - `Proposals sent upstream: fromtheoutfit/patchbay-standards#30 and #31, revised in place`
     (finding 15): in none of the standard's four forms. Decision 8.
   - The Version record (finding 11): `CHANGELOG.md`'s entry named only #18. The entry is
     corrected in place, as it describes what lands, and this spec's Version record says so.
3. **Case o requires `==0.0.0`**, a version no uv release carries (finding 13), so no later pin of
   uv collides with it and the guard against a running 0.13.6 goes.
   - The expected line still names the running uv as `uv --version` prints it, read once (finding
     14: the second `uv --version` run becomes a note quoting the saved line, so the harness has
     140 runs where it had 141).
   - That version must be the whole of a plain `X.Y.Z` (`^[0-9]+\.[0-9]+\.[0-9]+$`), so a build
     printing more, such as `0.13.7+5`, stops the harness by name rather than ending UNEXPECTED on a
     line uv never prints (finding 4).
   - The guard against a table already holding the value stays, though `==0.0.0` cannot be a real
     pin: the guard is the rule (finding 1). Owner: "the guard is the rule, and it carries its own
     mutation."
4. **One helper, `setline`, makes every pin edit**, for t, n and o (findings 2, 3 and 14):
   `setline <case> <what> <table> <sed -E s command> <written line, an ERE>`.
   - The edit, and both of its checks, are limited to the table's address range: n's
     `[dependency-groups] dev` list (`/^dev = \[$/,/^\]$/`), o's `[tool.uv]`
     (`/^\[tool\.uv\]$/,/^\[/`), t's `[tool.uv.sources]` (`/^\[tool\.uv\.sources\]$/,/^\[/`).
   - Before the edit, the table holding the written line already stops the harness by name; after
     it, the table not holding it does. n's value must be in a pin's form, `[0-9][^";]*` before the
     closing `",`, so `ruff===0.17.4` and a pin with an environment marker are left alone and
     stopped by name, not rewritten.
   - `setrev` becomes one call to it. t's setup changes and its assertions do not: no run line, no
     expected text and no `hdr` of t changes, and `base/process/verification-gate.md` asks a
     mutation of a change to the harness's assertions. So M1-M8 of the revision after the review of
     PR 5 are not rerun, and `verification/t/` shows t's run the same before and after the helper,
     but for uv's timings (owner).
5. **A setup guard is proven by a pair of runs, once per guard, not once per caller** (owner).
   Each guard gets a fixture it exists for: from the shipped harness, the run stops by the guard's
   name, or runs as the case says where the guard is what lets it run; from a copy with that guard
   deleted or put back as it was, the same run ends otherwise. The standard's "must come back
   `UNEXPECTED` with the harness exiting 1" is the proof for an assertion. A setup guard deleted
   often lets the case pass on a value it never set, a green run where the guard stops one, so the
   pair's differing ends are its proof, each stated before the run.
6. **The manifest-count test is unmarked**, reversing the reviewed spec's deferral (its Decision 4
   and its "Noted, not fixed"): the marker's text cannot read true while a marked test needs
   nothing installed (finding 10). Owner: unmark it in this revision.
   - `tests/integration/test_factory_round_trip.py`'s module-wide `pytestmark` becomes
     `@pytest.mark.integration` on its three tests that take `presets_root`.
   - The marker reads "integration: needs Vital's plugin or its presets installed; skipped with its
     reason where they are absent": two things, either of which a marked test needs.
   - The comment over `markers` says the gate deselects nothing, so every marked test runs at step
     5 or skips with its reason, and names the second reason the plugin's tests skip: the map
     measured on another machine (`agent-os/standards/vital/parameter-map.md`).
7. **The evidence is one harness run to a file** (findings 5 to 8,
   `base/process/verification-gate.md`, "A kept transcript holds one run of the harness and ends on
   that run's count"). Each file is the whole of the run's output, ending on the run's own last line,
   its count or its `harness:` stop, with no tally of ours. Its heading gives what a rerun needs
   without the generator: the date and branch; the copy, made from `8ebce15` and this revision's
   changes as handed over, which the owner's commit of this revision holds; the fixture as a diff
   `git apply` takes; the command and its working directory; and what the run must show. The
   generator was a throwaway in the session's scratch directory, outside the repository, and is not
   committed: a shell script outside `scripts/` is one step 1 never parses (owner).
8. **The proposals sent in place are the owner's deviation**, on 2026-11-09 (the revision after the
   review of PR 5, revising #30) and 2026-11-11 (the reviewed spec, revising #30 and #31), from
   `base/process/standards-retrospective.md`'s "The approved proposals become one issue". Owner:
   recorded as the owner's, with both dates.
   - #31 is revised in place once more: its verification pointer cites `verification/guards/` here,
     and its clauses are checked against what ships, revised where `==0.0.0`, the table limit or
     the value's form changes one.
   - The rule itself becomes a proposal of this retrospective, presented like any other and, if
     approved, filed as an issue of its own, since it refines no open one.
9. **The revision waits on #13, not green.** The whole harness, rerun after the last edit to the
   gate's scripts, ended `140 runs, 5 unexpected`. All five are in case q, which runs the unit suite
   under a bare `pytest`. They are one Hypothesis failure, replayed from the example database in q's
   copy: `tests/unit/test_parameters.py::test_a_value_the_parameter_holds_comes_back_exactly[volume]`
   at normalized `5.857149595214349e-20`, where the display maps back to a preset value 2.6e-23 off.
   - It reproduces on the tree. `src/` and `tests/unit/` are unchanged from `main` since `bb7652a`,
     so the defect is on `main`, outside the review's findings, and gate step 5 can draw it by chance.
   - Owner: file the issue and stop the revision here, not green. The issue is
     https://github.com/fromtheoutfit/patchbay-vital/issues/13. It cites #8's "From core's review
     of PR 19", finding 3 (`volume`'s floor), and probe 4's 1,104,000 of 1,104,000, which this
     value falsifies.
   - The run is kept whole as `verification/gate-negative-tests-first.txt`. It is not rerun for a
     passing transcript, and no saved example is cleared.
   - Once #13's fix is on `main` and merged into this branch, the harness is rerun once for
     `verification/gate-negative-tests.txt` and the gate for `verification/gate-run.txt`. Only then
     is this revision done.
   - Resumed on 2026-11-13, once PR 14 had closed #13: "Resumed after #13", below. Of the five,
     three were bare `pytest` runs and two the gate's, so "under a bare `pytest`" above says less
     than the transcript does.

## Resumed after #13 (2026-11-13)

PR 14 closed #13, and #15 with it: `main` at `9474506b1e984494c414aa1d22903f88bf1991e0`, merged
into this branch as `331197c`. The owner's word for the resumption: say what the merge changed that
this revision's work touches before anything runs; then one run of the harness and one of the gate,
each transcript printing its tree before and after; stop and present if either is not clean, with
no rerun to green.

**What the merge changed** (`24b2b5d` to `331197c`, outside `agent-os/specs/`):
- under `tests/`: `tests/data/pinned-values.txt`, new, and `tests/unit/test_parameters.py`,
  `tests/unit/test_float32.py` and `tests/integration/test_vital_plugin.py`;
- `src/patchbay_vital/parameters.py` and `float32.py`;
- `README.md`, `CHANGELOG.md`, and `measures.md`, `parameter-map.md` and `plugin-state.md` under
  `agent-os/standards/vital/` with their entries in `index.yml`.

It brought no `tests/conftest.py`: PR 14 carried one for a time and removed it before it merged
(`2d2f7dc`). It left as they were at `24b2b5d` every file this revision edited but `CHANGELOG.md`,
and every file its evidence rests on: `scripts/`, `pyproject.toml`, `uv.lock`, `.github/`,
`.gitignore`, `agent-os/standards/base/`, `tests/integration/test_factory_round_trip.py`,
`tests/unit/test_package.py` and `tests/data/factory-manifest.txt`.

**No harness case's setup or expectation is affected**, said to the owner before the runs:
- No expectation names a count of tests. The suite is 507 tests where it was 490, and that shows
  only in pytest's output.
- Nothing a case writes into its copy has a name the tree holds, and git lists no `conftest.py`.
- `tests/data/pinned-values.txt` is tracked and not ignored, so `mk` copies it and each copy's
  `git add` takes it. Its name is not `test*.txt`, so a bare pytest takes it for no doctest. Both
  test modules read it through `pytestconfig.rootpath`.
- The lines a case rests on are in place: c's description in the `base:` section of `index.yml`,
  m's `line-length = 100`, p's `local_settings.py` in `.gitignore`, and t's
  `test_the_pinned_patchbay_core_is_in_the_declared_range`.
- n, o and t edit `pyproject.toml` through `setline`, and the merge did not change that file.
- `main`'s harness (`578dd16`) had run on these blobs of `tests/` and `src/`, all but this
  branch's `test_factory_round_trip.py`, in the revision after PR 14's sixth review:
  `141 runs, 0 unexpected`. This branch's harness differs from it in the header, `setline` and
  `setrev`, n and o.

**Case q**, whose block is `main`'s byte for byte:
- Setup: git lists no `tests/conftest.py` and no `tests/unit/conftest.py`, so q's ignored
  `tests/unit/conftest.py` is the only conftest pytest loads there, as at `24b2b5d`. PR 14's
  `tests/conftest.py` would not have been at q's path either.
- Expectations: 16 of q's runs run the suite, and 7 of them expect exit 0: one bare
  `pytest --ignore=…`, four bare `pytest -p no:doctest` under a pytest configuration file at the
  root, and the last two runs of the gate. In all three configurations pytest's root is the
  copy's root, so the new readers find the file. The merge adds no marker and no Hypothesis
  profile.
- #13's value is a pinned value now, run on every record in every run
  (`test_every_pinned_value_comes_back_on_every_record`), so it no longer rests on a draw.
- q's runs of the suite share one example database, the copy's `.hypothesis/`. The five of
  2026-11-11 were one draw, made in a run of the gate that expected exit 1 ("the same pytest.toml
  tracked") and replayed in three bare runs and two of the gate's. Decision 9's "under a bare
  `pytest`" is true of three of the five.

**The plugin's tests against core at `eddba95`.** The harness's copies were the first to run them,
PR 14's three new ones among them, against this branch's pin: `main` ran them against `dd2bcad`,
and CI has no Vital and skips them.

**What was not rerun.** `verification/guards/`, `mutations/`, `pin-moves/`, `t/`, `manifest/` and
`new-pin-gate.txt` stand as recorded on 2026-11-11: each rests only on files the merge left as they
were.

**Case j** (owner, asked before the runs). `verification/ci-negative-test.txt` was recorded on
2026-11-11, before the merge, and the harness reruns its tests when a spec adds a file under a
directory `mk` copies. Owner: rerun j as its own invocation, under the same stop rule, its
transcript printing its tree before and after. The run here replaces the earlier one, which stays
in history at `24b2b5d`.

**The transcripts' form.** Each is one run, written outside the tree and copied in afterwards by a
generator in the session's scratch directory, not committed (Decision 7). Each prints the tree
before the run and after it as fromtheoutfit/patchbay-standards#38's proposal 2 has read since the
revision after PR 14's fourth review refined it: HEAD, `git status --porcelain=v1` in full with its
line count, the blob of every path it lists, and `cmp` of the two. In the harness's two the tree
after the run is written in the heading, above the run, so that the file ends on the run's count
(`base/process/verification-gate.md`, "A kept transcript holds one run of the harness and ends on
that run's count"). `gate-run.txt`'s form puts it after the run.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — a gate spec: the harness's pin edits and o's assertion
  changed, each guard shown to discriminate, the kept transcripts one run each, the harness rerun
- `base/process/standards-retrospective` — the forms of `Proposals sent upstream:`, and the
  deviation from "one issue"
- `base/process/ownership` — the owner lands this revision; the PR body and the reply are theirs
- `base/testing/tests` — the marked and unmarked tests of `tests/integration/`
- `vital/preset-tests` — how the presets' tests skip
- `vital/parameter-map` — the machine the map was measured on, a reason the plugin's tests skip

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script under
`scripts/` as git lists them, with no tracked file a `.gitignore` ignores; `uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`, `uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule
set and `uv.lock`'s pins; and `scripts/sync-standards.sh --check` against `../patchbay-standards` at
the commit in `agent-os/standards/base/.version` — and the three judgment steps are recorded, in this
order: Docs, Version, then the standards retrospective below.

**Results (2026-11-13): green, and the revision is done.** It is finished against `main` at
`9474506b1e984494c414aa1d22903f88bf1991e0`, merged into this branch as `331197c`. Branch
`feature/11-gate-move-the-patchbay-core-pin-to-the-head-carrying-patchbay18-and-say-what-the-integration-marker-needs`.

`scripts/gate.sh` exits 0 on the working tree at `331197c` with Vital installed
(`verification/gate-run.txt`, 14:54 EST). All six steps pass, and step 5 reports 507 passed, none
skipped. Step 2's sync moved the tree's `.venv` from core at `dd2bcad`, `main`'s pin, to this
branch's `eddba95`, so step 5 ran against the locked core. The tree before and after the run is the
same by `cmp`, every listed path's blob printed: HEAD and four paths, this file, `CHANGELOG.md` and
the two harness transcripts. The transcript is written outside the tree and copied in afterwards.

The gate was the last run. Written after it: this paragraph; and, the gate being clean,
fromtheoutfit/patchbay-standards#43, with its number in `Proposals sent upstream:` and beside the
retrospective's last two proposals, the first of which gained `verification/gate-run.txt` in what
it is verified against.

On 2026-11-11 the revision stopped not green, waiting on
https://github.com/fromtheoutfit/patchbay-vital/issues/13 (Decision 9). The bullets below are that
day's but where they give a later date.

- **The harness:** `verification/gate-negative-tests.txt`, one whole run on 2026-11-13, 14:22 to
  14:41 EST, on `331197c` with nothing uncommitted, ends `140 runs, 0 unexpected`, exit 0. The tree
  after it is the tree before it by `cmp`. Case q's 16 runs of the suite ended as the case says.
  Every run of the suite passes all 507 of the tree's tests, none skipped, but t's third, where
  the range test fails as the case says.
  - Kept whole beside it, `verification/gate-negative-tests-first.txt` is the run of 2026-11-11,
    after the last edit to the gate's scripts: `140 runs, 5 unexpected`, all five case q's one
    Hypothesis failure, #13.
  - On 2026-11-11 `scripts/gate.sh` exited 0, 490 passed, on the tree after the harness, marker
    and test edits, but before the module docstring was reworded; that run is no record.
- **The CI replay:** `verification/ci-negative-test.txt` (j), one whole run on 2026-11-13, 14:41 to
  14:42 EST, its own invocation on the same tree, ends `3 runs, 0 unexpected`, exit 0, the tree
  unchanged by `cmp`. It replaces the run of 2026-11-11, which ended the same and stays in history
  at `24b2b5d`.
- **The lockfile:** `git diff 8ebce15 -- uv.lock` is empty.
- **The new pin** (finding 5): `verification/new-pin-gate.txt`, a clone at `558b85b` whose
  `git status --short` and `git diff --stat` show `pyproject.toml` and `uv.lock` alone changed,
  3 lines. The gate on it exits 0, 490 passed.
- **The setup guards** (Decision 5), `verification/guards/`. Each pair ended as its heading's Must
  said:

  | Guard | As shipped | Guard deleted or put back |
  |---|---|---|
  | g1, o's version anchor (uv shim printing `0.13.7+5`) | exit 2, o's named stop | exit 1, `2 runs, 1 unexpected` |
  | g2, the table already holds the value (dev ruff 0.17.3, re-locked) | exit 2, n's named stop | exit 1, `2 runs, 1 unexpected` (the copy's gate passed) |
  | g2 through o (`[tool.uv]` already `==0.0.0`; finding 1) | exit 2, o's named stop | (none: once per guard) |
  | g3, the table limit (`[tool.fixture]` holding `"ruff==0.17.3",`) | exit 0, `2 runs, 0 unexpected`, the fixture's line unchanged | exit 2, the already-set stop |
  | g4, the form: `ruff===0.17.4` | exit 2, the not-rewritten stop | exit 0, `2 runs, 0 unexpected`, the operator rewritten |
  | g5, the form: a pin with an environment marker | exit 2, the not-rewritten stop | exit 0, `2 runs, 0 unexpected`, the marker dropped |
  | g6, the line not written (dev's ruff pin removed) | exit 2, the not-rewritten stop | exit 1, `2 runs, 1 unexpected` |

- **The reviewed spec's mutations of `gate.sh`** (findings 7 and 8), `verification/mutations/`, one
  whole run each: M1 through n, `2 runs, 1 unexpected`; M2 and M3 through n and o, each
  `4 runs, 2 unexpected`. Harness exit 1 for all three.
- **The pin moves** (finding 6), `verification/pin-moves/`, one whole run each. P1 (ruff re-locked
  at 0.17.2) and P2 (`==0.13.8` under a running 0.13.7) exit 0 as shipped, P2's o naming
  `0.13.7`. `main`'s harness stops at setup by name: `harness: n: pin not rewritten` and
  `harness: o: required-version not rewritten`, exit 2.
- **Case t before and after `setline`**, `verification/t/`: each `4 runs, 0 unexpected`.
  `t-diff.txt`'s `diff -u` prints nothing (exit 0) once uv's and pytest's timings and the memory
  addresses in pytest's assertion message are normalized. The first comparison, normalizing
  timings alone, differed in one address only.
- **The manifest-count test**, `verification/manifest/`: `-m integration` selects 76 of the
  module's 77 tests as shipped, the manifest's count not among them, and all 77 at `8ebce15`. With
  `HOME` an empty directory, so no preset is installed, it PASSED and the 76 SKIPPED naming the
  absent presets, as shipped and at `8ebce15` alike: the marker never skipped it.
- **The hosted runs:** on 2026-11-11 CI's log could not be read from here (HTTP 403, the
  organization's two-factor rule), and the run of this revision existed only after the owner's
  push. On 2026-11-13 `gh run view --log` reads them:
  - run 43088824755 at `24b2b5d`, this revision's commit: `success`, 402 passed, 88 skipped;
  - run 43486961962 at `331197c`, the merge: `success`, 416 passed, 91 skipped.

  CI has no Vital. By count, 91 is the 76 tests that read the presets and the plugin module's 15;
  `-q` names none of them. The commit that holds this resumption's files has no run until it is
  pushed.

**Docs (step 7):** checked and reads true against the shipped files:
- `pyproject.toml`: the comment over `markers` names both reasons a marked test skips, what it
  needs absent and, for the plugin's, the map measured on another machine, and the marker its two
  needs (finding 10). The header, `[tool.uv]`'s comment (negative test o), `[tool.uv.sources]`'
  (negative test t) and the dev group's read true as they were.
- `scripts/gate-negative-tests.sh`: the header's o entry says `==0.0.0`, a uv no release carries;
  the paragraph on setup steps says a case edits a pin through `setline`, inside the pin's table,
  and how a setup guard is shown to discriminate (Decision 5); n's and o's `hdr` lines say which
  table and which value; `setline`'s and `setrev`'s comments say what each refuses.
- `tests/integration/test_factory_round_trip.py`: its docstring says the tests that read the presets
  carry the marker and the manifest's count does not.
- `README.md`: the `tests/` bullet ("each skips, saying so, where what it needs is absent, CI among
  them") reads true of a test that needs nothing; the gate section's "its transcripts live in the
  spec that last changed a gate file" is now this one. Unchanged.
- `CLAUDE.md` and `agent-os/product/tech-stack.md`: name no marker text, case value or helper.
  Unchanged.
- `agent-os/standards/vital/preset-tests.md`: says how the presets' and the plugin's tests skip and
  nothing of the marker or of the module marked as a whole; `vital/parameter-map.md`'s machine rule
  is the one the comment names. Unchanged, so no retrospective edit.
- `CHANGELOG.md`: the pin's entry names core's #16 beside #19 (finding 11).
- The reviewed spec's folder: unchanged, its sentences corrected by Decision 2 here.
- Re-checked on 2026-11-13 against the merged tree:
  - `pyproject.toml`: the marker's text is true of `tests/integration/test_vital_plugin.py` as
    merged. Its module-wide `pytestmark` marks 14 tests, PR 14's three new ones among them, and
    each takes `host`, so needs the plugin. The comment's
    `agent-os/standards/vital/parameter-map.md` still holds the rule of the map's machine.
  - `README.md`: the merge added `pinned-values.txt` to the `tests/` bullet. "its transcripts live
    in the spec that last changed a gate file" is still this one: the merge changed no gate file,
    and this folder holds the current transcripts, j's included.
  - `scripts/gate-negative-tests.sh`: the header's "whenever a spec adds, removes or renames a
    file under a directory mk copies" is the rule j's rerun follows. The script is unchanged.
  - `tests/unit/builders.py`: "the gate's negative test q writes a conftest of its own at
    tests/unit/conftest.py" reads true, git listing no conftest.
  - `measures.md`, `parameter-map.md` and `plugin-state.md` under `agent-os/standards/vital/`, as
    merged, name the plugin's test module and its fixtures, and no marker text, `pytestmark`,
    count of tests or harness case. `preset-tests.md`, `CLAUDE.md` and
    `agent-os/product/tech-stack.md` are not changed by the merge.
  - `CHANGELOG.md`: this revision's entry said its transcripts wait on #13's fix; corrected
    (Version).
  - This file: Decision 9's "under a bare `pytest`" is said exactly under "Resumed after #13".
    `plan.md`'s Decision 6 names `parameter-map.md:33`, a line the merge moved to 42; `plan.md` is
    the plan as shaped, and no shipped file names the line.

**Version (step 8):** this spec's entry, first under `### Changed` in `[Unreleased]`,
`CHANGELOG.md`; and the reviewed spec's entry corrected in place to name both of core's merges that
`eddba95` brings in, fromtheoutfit/patchbay#19 (issue fromtheoutfit/patchbay#18) and
fromtheoutfit/patchbay#16 (core's gate and `Event.at`, after the review of its PR 15), which the
reviewed spec's Version record left out. The version stays 0.0.1, no release being cut.

On 2026-11-13 the entry's last sentence, "The revision's harness and gate transcripts wait on its
fix", was corrected: the fix, PR 14, is merged into this branch, and the transcripts are runs of
that merge. The merge left the entry first under `### Changed`; PR 14's are under `### Fixed`.

## Standards Retrospective

Step 9, answered from the shipped diff. No project standard changed, and
`agent-os/standards/index.yml` is untouched: `vital/preset-tests.md` and `vital/parameter-map.md`
read true of the unmarked test and of the comment that names the map's machine.

1. **A pattern no standard covers:** three. The proof of a setup guard by a pair of runs (Decision
   5). A transcript that says what tree it ran on shows it (finding 5, `verification/new-pin-gate.txt`).
   And, refining an open proposal, a pin edit held to its table and its value's form, a runner
   version no release carries, and a version read from the tool whole (`setline`, cases n and o).
   Below.
2. **A standard wrong or stale:** `base/process/standards-retrospective.md`'s "The approved
   proposals become one issue" names no way to send a refinement of a proposal already filed and
   still open, and its `Proposals sent upstream:` forms have none for it (finding 15). Below.
3. **A deliberate deviation:** the in-place revisions of #30 and #31, the owner's, on 2026-11-09 and
   2026-11-11 (Decision 8), and once more here for #31.
4. **A pointer moved:** none. No standard names the harness's line numbers, a case's value or the
   marker's text.

- **Noted, not fixed:**
  - Case s writes a `uv.toml` requiring `==0.13.6`, as o did. A later pin of uv 0.13.6 would make its
    bare `uv sync` pass and the run end UNEXPECTED. It is outside the review's findings; it is
    recorded under #31's "Consuming projects left behind" for this repository's next gate spec.
  - The transcripts of the reviewed spec and of the revision after the review of PR 5 keep their
    excerpted, tallied form as recorded; this spec's `verification/` holds the whole runs.
  - #13, the volume round trip below 2 ** -43 (Decision 9), for its own spec.

**On resuming, 2026-11-13.** The four questions again, for what the resumption added: three
transcripts, this record and one sentence of `CHANGELOG.md`, and no code, script, test or standard.

1. **A pattern no standard covers:** two. A step that fails on a defect outside what the spec may
   change, filed, waited for and finished against (Decision 9). And the rerun a branch that changed
   the harness owes when a merge brings in a file under a directory the tests copy (case j, under
   "Resumed after #13"). Both below, the last two of the proposals.
2. **A standard wrong or stale:** none. `#38`'s proposal 2, as this file records it below, asks
   for `git log -1`, `git status --short` and `git diff --stat` before the run. The revision after
   PR 14's fourth review refined it in place, and the transcripts here follow the refined form.
3. **A deliberate deviation:** on 2026-11-11 the revision was handed over without a green run,
   committed as `24b2b5d` and pushed, where `base/process/verification-gate.md` has the run "the
   last thing done before the work is handed over". The owner's, by Decision 9. The first of the
   two proposals is the exception it asks the standard to grow.
4. **A pointer moved:** none in a standard.

Proposals sent upstream: fromtheoutfit/patchbay-standards#38 and fromtheoutfit/patchbay-standards#43; fromtheoutfit/patchbay-standards#31, revised in place

The second half of that line is in none of the standard's four forms. It is the form the
`#38` proposal asks for, used here at the owner's word (Decision 8). The first half names two
issues where the forms have one: `#38` carries the proposals of 2026-11-11 and `#43` the two of the
resumption, a new issue at the owner's word on 2026-11-13.

### Standards retrospective (proposed, base)

- `base/process/verification-gate.md`, "A change to the harness's assertions is shown to
  discriminate": a setup guard is shown by a fixture it exists for, run from the harness as shipped
  and from a copy with the guard deleted or put back, the two ending apart, once per guard. Verified
  against `setline` and case o's version anchor in `scripts/gate-negative-tests.sh`, and
  `verification/guards/` g1 to g6. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#38.
- `base/process/verification-gate.md`, "Every spec keeps its green run": a transcript that says what
  tree it ran on prints `git log -1`, `git status --short` and `git diff --stat` before the run.
  Verified against `verification/new-pin-gate.txt`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#38.
- `base/process/verification-gate.md`, "A case states what it rests on", proposal 2 of `#31`: the
  edit and its checks held to the pin's table, the value pattern taking only a pin's form, a runner
  version no release carries (`==0.0.0`), and a version read from the tool whole. Verified against
  `setline` and cases n and o, `verification/guards/` g1, g3, g4 and g5, and
  `verification/pin-moves/`. Proposed, not applied; revised into
  fromtheoutfit/patchbay-standards#31 in place on 2026-11-11 at the owner's word, its verification
  pointer corrected to these transcripts and case s added to its "Consuming projects left behind".
- `base/process/standards-retrospective.md`, "The approved proposals become one issue": an approved
  proposal that refines one filed and still open is revised into that issue in place, with a
  "Revised <date>" paragraph, and `Proposals sent upstream:` gains `<issue>, revised in place`.
  Verified against #30 and #31, revised in place twice, and the `Proposals sent upstream:` lines of
  the revision after the review of PR 5's and the reviewed spec's `shape.md`. It changes the gate
  task of patchbay-standards' `shape-spec.md`, so `#38` is a gate spec. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#38.

The two of the resumption, each presented to the owner on 2026-11-13 with AskUserQuestion. The
owner's answer: "1 and 2, filed as one new issue. Word 1 so it does not contradict
patchbay-standards#39's rule: it applies where the defect is outside what the spec may change (a
gate spec meeting a defect in package code, or a fix that decides another open issue's question);
a defect inside the spec's own files whose fix is known and checked is fixed there. Cite #39 in
the proposal. The gate has not run yet: if it is not clean, stop and present before filing
anything."

- `base/process/verification-gate.md`, "A failing step is fixed at its cause": where a step fails
  on a defect outside what the spec may change, the spec does not fix it. That is a gate spec
  meeting a defect in package code, or a fix that decides another open issue's question. The defect
  is filed as an issue of its own, and the spec stops, not green, at the owner's word. The failing
  run is kept whole in a file of its own, not rerun for a passing transcript, and no saved example
  is cleared. Once the fix is merged into the branch, the tests and the gate are each run once, and
  `shape.md` names the commit of main the spec was finished against. A defect inside the spec's own
  files whose fix is known and checked is fixed there, which is the limit
  fromtheoutfit/patchbay-standards#39 gives, and this proposal leaves it as it is. Verified against
  Decision 9, `verification/gate-negative-tests-first.txt`, `verification/gate-negative-tests.txt`
  and `verification/gate-run.txt`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#43.
- `base/process/verification-gate.md`, "The spec that adds or changes a step ships its negative
  test": the rule reruns the tests "whenever a spec adds, removes or renames a file under a
  directory the tests copy", and the spec that adds the file reruns the tests its own branch holds.
  It does not say what a branch that changed the tests owes when a merge brings such a file into
  it. That branch reruns them, the CI replay among them, and a transcript recorded before the merge
  is replaced by the rerun's and stays in history. Verified against
  `verification/ci-negative-test.txt`, replaced on 2026-11-13 with the earlier run in history at
  `24b2b5d`, `verification/gate-negative-tests.txt`, and `tests/data/pinned-values.txt`, which PR
  14 added and whose own spec reran `main`'s harness. It changes a sentence the header of
  patchbay-standards' `scripts/gate-negative-tests.sh` carries, a gate file, so `#43` is a gate
  spec. Proposed, not applied; filed as fromtheoutfit/patchbay-standards#43.
