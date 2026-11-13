# Revision after the review of PR 12 (issue #11's gate spec)

## Context

PR 12 (`8ebce15`, branch `feature/11-gate-move-the-patchbay-core-pin-…-marker-needs`) has one review:
https://github.com/fromtheoutfit/patchbay-vital/pull/12#issuecomment-6803400462, 15 findings, none
inline. The pin and the lock are clean. What it found:
- the new guards in cases n and o are incomplete (1–4);
- the evidence is excerpted and tallied, and fires no guard (5–9);
- three docs and records don't read true (10–12);
- two simplifications (13–14);
- the upstream proposals deviate from the one-issue rule (15).

The owner wants all 15 addressed, as answered in shaping. This is a gate spec revision on the same
branch, so PR 12 carries it. No stage, commit, push or PR; the PR body and any reply to the review
are the owner's.

Found while shaping:
- `git log dd2bcad..eddba95` in core shows two merges: #16, "Revise the gate and Event.at after the
  review of PR 15", and #19, which is issue #18's.
- Nothing counts marked tests: case y uses its own probe, and README, CI and `vital/preset-tests.md`
  name no count and no `pytestmark`.
- **The marker never skipped the manifest-count test.** Skips come from the `presets_root` and
  `vital` fixtures, and that test uses neither, so it already ran in CI at `8ebce15`. Unmarking it
  changes what the marker claims, not what runs.
- The Actions API returns 403 here (the org's 2FA rule), so I can't read CI's log. The hosted run of
  this revision exists only after the owner's push.

## Decisions (for the new shape.md)

1. **Scope:** the review's 15 findings. Decision 1 cites the review comment.
2. **New spec folder** `agent-os/specs/2026-11-11-HHMM-revision-after-pr-12-review/`, as the PR 3,
   5, 6 and 9 revisions did.
   - The reviewed folder stays as its record.
   - The new folder's Decisions correct its sentences by name: Decision 6's "assertions changed"
     (finding 12) and "each stops…" for o (1); Results' "before any other edit" (5); the #31
     verification pointer (9); the `Proposals sent upstream:` line (15); and the Version record's
     missing #16 (11).
3. **o requires `==0.0.0`**, a version no uv release carries (finding 13).
   - The "running uv is not 0.13.6" guard goes.
   - The expected line still names the running uv, read once from `uv --version`.
   - That output must be a plain `X.Y.Z`, end-anchored (`^[0-9]+\.[0-9]+\.[0-9]+$`). A suffixed
     build (`0.13.7+5`) stops the harness by name (finding 4).
   - The pre-check stays, per the owner's rule (finding 1).
   - The second `uv --version` run becomes a `note` with the saved line (finding 14), so the harness
     goes from 141 runs to 140.
4. **One `setline` helper serves t, n and o** (findings 2, 3 and 14):
   `setline <case> <what> <table> <sed -E s-command> <written-line ERE>`.
   - **Pre-check:** the table already holds the written line → die by name.
   - **Edit:** limited to the table's address range.
   - **Post-check:** the table holds the written line after the edit, or die by name.
   - Tables: n uses `/^dev = \[$/,/^\]$/` with `^(    "ruff==)[0-9][^";]*",`, which refuses `===`
     and an environment marker. o uses `/^\[tool\.uv\]$/,/^\[/`. `setrev` becomes a call to it,
     using `/^\[tool\.uv\.sources\]$/,/^\[/`.
   - t's setup changes but its assertions don't. Per `base/process/verification-gate.md`, mutations
     are owed for assertion changes, so M1–M8 are not rerun. t's run is shown the same before and
     after (owner).
5. **Setup-guard proof form.** Each of the helper's guards and o's anchor is proven once per guard,
   not per caller.
   - Each guard gets a fixture and two runs: the shipped harness, which stops by the guard's name or
     runs as the case says, and a copy with the guard deleted or put back, which ends otherwise.
   - "Otherwise" means UNEXPECTED with exit 1, a false green with exit 0, or another guard's stop.
   - The standard's "UNEXPECTED, exit 1" is the form for assertions. Deleting a setup guard often
     yields the false green it exists to prevent, so a pair of runs with differing ends is the proof.
6. **The manifest-count test is unmarked.** This reverses the reviewed spec's deferral: the marker's
   text can't read true while a marked test needs nothing installed.
   - The module's `pytestmark` becomes `@pytest.mark.integration` on its three preset tests.
   - Marker text: `"integration: needs Vital's plugin or its presets installed; skipped with its reason where they are absent"`.
   - The comment over `markers` names the parameter map's machine skip
     (`agent-os/standards/vital/parameter-map.md:33`).
7. **Evidence form** (findings 5–8):
   - One harness run per file: the whole output, ending on the run's own last line (its count, or
     its `harness:` stop).
   - Each heading gives what's needed to rerun it without the generator: the date and branch, the
     copy made from `8ebce15` plus this revision's changes as handed over, the fixture diff as
     `git apply` takes it, the command with its working directory, and what the run must show.
   - No tally of mine. The generator is a scratchpad throwaway, not committed: a shell script
     outside `scripts/` is one that step 1 never parses.
8. **Upstream (finding 15).** In-place revision is recorded as the owner's deviation, on 2026-11-09
   (PR 5 revision) and 2026-11-11 (issue #11 spec).
   - #31 is revised in place: its verification pointer cites the new transcripts, and any clause
     that `==0.0.0` or the table limit changes is checked against what ships.
   - The in-place rule becomes a retrospective proposal (below).

## Tasks

### Task 1: Save spec documentation
`plan.md`, `shape.md` (scope, shaping answers, Decisions above), `standards.md` and `references.md`.
- `standards.md` holds the core five plus `base/process/verification-gate`, `standards-retrospective`,
  `ownership`, `base/testing/tests`, `vital/preset-tests` and `vital/parameter-map`, as full text,
  base at `e31f7db`.
- `references.md` points at the reviewed folder, the PR 5 revision's `guard-mutations.txt`, and the
  harness's `setrev`/n/o/t/y.

### Task 2: Harness (`scripts/gate-negative-tests.sh`)
- Add `setline` beside `mk` (~line 246) and make `setrev` call it.
- Rewrite n (~406) and o (~415) per Decisions 3–4.
- Update their `hdr` lines and the header's n/o entries (lines 67–70: o's "a uv no release carries").
- Leave t's body, y and the other cases alone.

### Task 3: Marker and test
- `pyproject.toml:165-167`: the comment and the marker text (Decision 6).
- `tests/integration/test_factory_round_trip.py:16`: `pytestmark` replaced by the decorator on
  `test_the_installed_presets_are_the_manifest_s`, `test_a_factory_preset_round_trips` and
  `test_a_pack_preset_round_trips`.
- Check `uv.lock` is unchanged (`git diff 8ebce15 -- uv.lock` empty).

### Task 4: Records
- **CHANGELOG:** fix the pin entry in place (finding 11): `eddba95` brings in fromtheoutfit/patchbay#19
  (for #18) and #16 (the gate and `Event.at` after core's PR 15 review). Add a new first entry for
  this revision.
- **The new shape.md:** Decisions correcting the reviewed record (Decision 2). Version record names
  both merges.

### Task 5: Evidence, after the last harness edit (Decision 7; scratchpad generator, files in `verification/`)
- **`new-pin-gate.txt`** (finding 5): a clone at `558b85b`, with only the rev and `uv.lock`'s two
  lines changed. The top shows `git log -1`, `git status --short` and `git diff --stat`, then
  `scripts/gate.sh`.
- **`guards/`** (findings 1–4 and 9):

  | Guard | Fixture | Shipped must | Mutated |
  |---|---|---|---|
  | g1 anchor | uv shim printing `uv 0.13.7+5 (…)`, case o | exit 2, "no plain version" | anchor removed → UNEXPECTED, 1 |
  | g2 pre-check | dev ruff `0.17.3`, re-locked, case n | exit 2, "already" | deleted → gate passes, UNEXPECTED, 1 |
  | g2-o | `[tool.uv]` holds `==0.0.0`, case o | exit 2 by name (finding 1, shipped only) | — |
  | g3 table limit | `[tool.fixture]` list holding `"ruff==0.17.3",`, case n | exit 0, outside line untouched | range removed → exit 2, pre-check's name |
  | g4 form `===` | dev `"ruff===0.17.4",`, case n | exit 2, "not rewritten" | `[^"]+` back → exit 0 (false green) |
  | g5 form marker | dev `"ruff==0.17.4; python_version >= '3.12'",`, case n | exit 2, "not rewritten" | `[^"]+` back → exit 0 |
  | g6 post-check | dev's ruff line removed, case n | exit 2, "not rewritten" | deleted → exit 0 |
- **`mutations/`** (findings 7–8): the reviewed M1 (n), M2 (n o) and M3 (n o) on `gate.sh`, rerun
  against the revised harness in correct form, one run each. Each must be UNEXPECTED with exit 1.
- **`pin-moves/`** (finding 6), whole transcripts:
  - `p1-shipped` and `p2-shipped` must exit 0. P2 shows o naming the running 0.13.7 under a
    `==0.13.8` pin.
  - `p1-main` and `p2-main` (harness from `git show 558b85b:…`) must end on their named `harness:`
    stop.
- **`t/`:** `t-before` (`8ebce15`'s harness on the revised tree) and `t-after`, plus `t-diff.txt`: the
  diff after normalizing uv's timing figures, the normalization stated. It must show no
  difference apart from setup lines.
- **The manifest test**, one pytest run per file:
  - `-m integration --collect-only -q` on the module: it isn't selected.
  - With `HOME` set to an empty scratch dir and `-rA`: it PASSED, and the 76 preset tests SKIPPED
    "no installed Vital presets".
  - The same run at `8ebce15`'s marked module: it passed there too.

### Task 6 (FINAL): Verification gate
1–6. `scripts/gate.sh` exits 0. Gate files changed, so the whole harness reruns one run per
transcript: `gate-negative-tests.txt` must end `140 runs, 0 unexpected`, and
`ci-negative-test.txt` (j) `3 runs, 0 unexpected`.

7. **Docs**, edited only where something reads false:
   - `pyproject.toml` comments; README's `tests/` bullet ("each skips… where what it needs is
     absent"); `CLAUDE.md`; `tech-stack.md`.
   - The harness header and `hdr` lines; the module docstring.
   - `vital/preset-tests.md` and `parameter-map.md`. Neither says the module is marked as a whole,
     so I expect no edit. If one does, it's edited in the retrospective as its own change set.

8. **Version**: the CHANGELOG entries as in Task 4. The version stays 0.0.1.

9. **Standards retrospective**, from the shipped diff, presented with AskUserQuestion (multi-select).
   Expected candidates:
   - `base/process/standards-retrospective.md`: an approved proposal that refines one already filed
     and still open is revised into that issue in place with a "Revised <date>" paragraph, and
     `Proposals sent upstream:` gets the form "#N, revised in place". Evidence: #30 and #31, twice.
   - `base/process/verification-gate.md`: Decision 5's setup-guard proof form; and a transcript
     that claims what tree it ran on shows it (`git status --short`, `git diff --stat`).
   - Refinements of #31's proposal 2 (the table limit, the value's form, a runner version no
     release carries), revised into #31 in place with the corrected pointer.

   Approved new proposals are filed as one new patchbay-standards issue, with no AI attribution.
   `Proposals sent upstream:` is written. The project standards are expected unchanged.

Then `scripts/gate.sh` → `verification/gate-run.txt` (first line the date and branch) as the last
act. Stop and print `git status --short`. The hand-over lists any retrospective edits apart and
offers draft PR-body text for the owner.

## Verification
- `gate.sh` exits 0; the harness ends `140 runs, 0 unexpected`; j `3 runs, 0 unexpected`.
- Every guard pair ends as its row says; each mutation ends UNEXPECTED with exit 1; the pin moves
  end as required; `t-diff.txt` shows timing lines only.
- The manifest test is unselected by `-m integration` and passes with the presets absent.
- `git diff 8ebce15 -- uv.lock` is empty.
