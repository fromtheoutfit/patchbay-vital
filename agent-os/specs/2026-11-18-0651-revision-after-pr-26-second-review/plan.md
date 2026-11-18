# Revision after the second review of PR 26 (issue #20) — plan

## Context

PR 26 (fromtheoutfit/patchbay-vital#26, branch
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, head
`c8ed333`) has a second review by the owner: issue comment 6965953694, "Review findings at
c8ed333", 2026-11-18 01:13 UTC. It lists 19 findings and says "None has been verified yet".
Shaping checked each against the code at `c8ed333`, and the owner decided each with conditions,
given verbatim in Appendix A, which is the source for `shape.md`.

**This is the last round.** Anything the work turns up that is not a correctness defect is
listed for a later issue in `shape.md` and not fixed here.

No agent commits, pushes, opens a PR or posts the reply. No gate file changes. No file is added,
removed or renamed under `scripts`, `src`, `tests` or `agent-os/standards`, so the negative
harness is not rerun. The spec folder is
`agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/`.

## What shaping checked

Read from the tree at `c8ed333`, nothing run against Vital. A figure is quoted only from a kept
transcript.

| # | Verdict | Decision |
|---|---|---|
| 1 | Holds: `answered()` installs at `host.py:278`, before its `try` and before `_alerts` is set | Fix: own method kept from build, state and install under one `try` |
| 2 | Holds: the plant at `host.py:767` is before the `try` | Fix: plant inside the `try` |
| 3 | Holds, narrower: through the instrument only a refused read or set of the marker reaches it; the map is resolved in `__init__`, so `_marker()` cannot raise there | Fix: the host counts writes begun |
| 4 | Holds; the last revision recorded it ("the instrument cannot tell those two apart") | Fix, by the same count; that choice is replaced |
| 5 | Does not hold: `opaque` never holds `null` (`preset._json_section` refuses all but an array or object; the file reader refuses it by name first) | No code; one test; reply says which check refuses first |
| 6 | Holds for a bare `VitalHost.load_state` only; the file reader refuses a boolean setting. What Vital does with `true` is unmeasured | A marker value that is no JSON number is refused; no probe |
| 7 | Holds: `patch._section` uses `DECODER.decode` | Fix: read through `decoded()` |
| 8 | Holds: `noted.append` is outside any guard | Fix: a flag first, the body guarded |
| 9 | Holds: the callback runs inside the plugin call; it does no float work today | Docs only |
| 10 | Holds: `_write` reports `alerts[0]`; no transcript shows two alerts for one text | Fix: every alert, in order, with the count |
| 11 | Repeat: open as patchbay-vital#27 | Stands; #27 revised in place only if the review adds something |
| 12 | Repeat: declined on `costs.txt` (pedalboard links AppKit; watch built in 0.14 ms). The fork-safety point is new and unmeasured | Stands; fork-safety listed for a later issue |
| 13 | Repeat: declined on `costs.txt` (0.6 ms median, 5.1 ms on the 10 MB preset) | Stands |
| 14 | Holds | Deferred to one host.py cleanups issue |
| 15 | Repeat: the second check was the owner's condition | Stands |
| 16 | Holds | Deferred, same issue as 14 |
| 17 | Recorded as deliberate in `vital/preset-tests.md` | Declined; base proposal for a home |
| 18 | "Not killed by the parent" is one of the standard's three checks | Declined |
| 19 | A design point; crashes are #25's | Reply, and one paragraph revised into #25 |

Also found, for the owner's condition on 6: the state's validator
(`state.PluginState._text_is_one_object`) checks only that the text is one JSON object, so it
refuses none of the five kinds (true, false, null, a string, an array) before `_planted`.

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/` with:
- **plan.md**: this plan.
- **shape.md**: scope, the table above, the owner's answers verbatim (Appendix A), Decisions
  each citing its finding, and these records:
  - the last revision's choice for a foreign error before the write ("the instrument cannot
    tell those two apart") replaced by finding 4, and why; that spec's text is not edited;
  - the readings below marked "Read in this plan";
  - "For a later issue, not filed": the fork-safety point of 12 in the reviewer's words with
    the `otool` lines of `costs.txt`, and anything the work turns up that is no correctness
    defect.
- **standards.md**: full text of the core tier (`base/python/toolchain`, `layout`, `typing`,
  `models`, `errors`) and of `vital/plugin-state`, `vital/instrument`, `vital/preset-tests`,
  `vital/preset-file`, `vital/parameter-map`, `base/testing/tests`,
  `base/process/verification-gate`, `base/process/standards-retrospective`,
  `base/process/ownership`. `base/python/errors` is named for findings 3, 6, 8 and 10.
- **references.md**: the first PR 26 revision (`2026-11-17-1238-…`: its plan's form,
  `costs.txt`, `mutation.txt`, the evidence scripts its transcripts embed); the issue #20 spec;
  `host.py`'s `_reached` and `_environment_kept`; `builders.StandInWatch`; `test_host.py`'s
  `_FakePlugin`, `_FakeParameter`, `_StandInMethod`, `_watch_over`, `_ThroughTheCallback`,
  `_first_depth_the_decoder_refuses`; `test_instrument.py`'s `_FakeVital`.
- No visuals. `agent-os/product/` is unchanged.

Every transcript is written outside the tree, copied in afterwards, made on a still tree with
its tree (by blob) and machine printed before and after. A first try that stops is kept as
`<name>-first.txt` beside its replacement. Ruff format, ruff check and a line-length pass run
over every changed file before the first kept run.

## Task 2: `host.py`, the watch (findings 1, 8, 10, 9)

- **Finding 1.** `_RUNTIME_FUNCTIONS` gains `method_getImplementation`, its argument and return
  types declared in `_appkit_watch`, which reads `-[NSAlert runModal]`'s own implementation
  once and gives it to `_AppKitWatch`, held for its lifetime. `install` no longer returns what
  it replaced. `answered()` refuses a nested entry before its `try`, as now; inside one `try`
  it sets its state, then installs the callback; the `finally` installs the kept
  implementation, then clears the state, whatever happened in the `try`.
- **Finding 8.** The callback's first statement stores a flag that needs no allocation (an
  existing attribute set to `True`); everything after it is under one guard, and the first
  button is returned whatever happens. `_write` raises `PluginStateError` whenever the flag is
  set, saying so where the alert could not be noted. `_AlertWatch`, `_NoWatch` and
  `builders.StandInWatch` carry the flag the same way.
- **Finding 10.** The error names every alert answered, in order, with the count; it is chained
  from the first read that failed, and with a pedalboard refusal from pedalboard's, as now.
- **Finding 9.** No code. The module docstring names the callback as the one place the
  package's Python runs under the plugin's floating-point environment, says it does no float
  arithmetic, and says why it is not switched (nothing may fail before the alert is noted). One
  comment line at the callback says the same.
- Tests in `tests/unit/test_host.py`, the real `_AppKitWatch` on stand-ins, every platform:
  - KeyboardInterrupt raised from the install before it swaps, and after it has swapped: the
    method is the kept one, the watch is not in place, the interrupt leaves as itself, and the
    next entry works;
  - putting the kept method back twice changes nothing;
  - a refused nested entry leaves the first entry's state and method as they were;
  - a noting step that raises MemoryError: 1000 comes back through the CFUNCTYPE object,
    nothing leaves the callback, and `_write` raises saying the alert could not be noted;
  - two alerts in one write on the fake plugin: both sets of words, in order, with the count.

## Task 3: `host.py`, the marker (2), the count (3, 4) and a value that is no number (6)

- **Finding 2.** `load_state` reads the marker's value before the `try`; the plant is inside
  it; on any error the marker is set back as now (`_set_back`, the write's error leaving as
  itself).
- **The count.** `VitalHost.writes_begun`, a read-only property with no setter, documented as
  "state writes begun" and as no part of core's contract. `load_state` raises it immediately
  before its first change to the plugin (the plant; the write where the load is unchecked), and
  `measure` before its first set. Raised before the change, never after.
- **Finding 6.** Where the text holds the marker's key and its value is not a JSON number
  (`true` and `false` included), `load_state` raises `PluginStateError` naming the key and the
  value's kind, before the count is raised and before the marker is read or set. A text without
  the key is as today. `_planted`'s docstring loses "a value there that is no number is read as
  absent".
- Tests in `test_host.py` on `_FakePlugin`:
  - KeyboardInterrupt from the setter that plants, before it sets and after: the marker is at
    the value it had and the interrupt leaves as itself;
  - the count is already raised when the planting setter is entered (an interrupt raised from
    the setter finds it moved), and is unchanged by a load refused before any change;
  - `true`, `false`, `null`, a string and an array under the marker's key: `PluginStateError`
    naming key and kind, the count unchanged, no setter called. Each test also holds the order:
    the validator passes the text and the marker's check refuses it.

Read in this plan:
- "The finally sets it back whenever the read succeeded, planted or not": on an error the
  set-back runs whether or not the plant's line completed. A load that succeeded is not set
  back to the value before: the marker then holds the text's value, and is read for the
  verdict as now.
- "Before the plugin is touched" (6): before any call that changes the plugin and before the
  marker's value is read. The one-time map lookup, which on a bare host's first load reads the
  plugin's name and version, comes first, since the key is the map's. Where the map is not the
  plugin's the load is unchecked as it was, and nothing is refused.

## Task 4: `instrument.py`, what was sent (findings 3, 4)

- `load_patch` reads `host.writes_begun` once, before the first of its two loads.
  - Unchanged after an error: nothing was sent. A `PluginStateError` becomes
    `PatchRefusedError`, chained, with no rollback and no lost step; a foreign error leaves as
    itself with nothing marked.
  - Changed: exactly as today, including an error in the second load before its own change.
  - `PluginThreadError` and other `VitalError`s: as today.
- `_rolled_back` is unchanged in what it does; its loads are counted the same way and a test
  holds that.
- The docstrings of `load_patch`, `_lose_step` and the module say this; "the instrument cannot
  tell those two apart" has no counterpart left in the code's docs.
- Tests in `tests/unit/test_instrument.py`, on `_FakeVital` through the real host:
  - a refused marker read before any change: `PatchRefusedError`, no rollback, not out of
    step, nothing published, `set`/`load_patch`/`render` still served;
  - KeyboardInterrupt and MemoryError before any change: the same object leaves, nothing
    marked;
  - each of those three again after the first load's change: rolled back, or out of step, as
    today;
  - the rollback's own loads: an error there, before or after its change, as today.

## Task 5: `patch.py`, the guarded section read (finding 7) and the test for finding 5

- `_section` reads through `preset.decoded()` and refuses nesting too deep as
  `PatchRefusedError` naming `settings.<name>`, chained.
- Tests in `tests/unit/test_patch.py`:
  - `_section` given a section one level past the decoder's limit, bisected in the test from
    `DECODER` itself, on a preset built without validation: `PatchRefusedError`. The bisecting
    helper moves from `test_host.py` to `tests/unit/builders.py`, which both modules import;
  - finding 5: a `null` section is refused by name before `check_loadable` is reached, as a
    patch (by the preset's validator, through `preset_of`) and as a file (by the reader).

## Task 6: Docs and Version

- `host.py` and `instrument.py` docstrings for Tasks 2–4; `README.md` where it describes the
  alert, the marker or a lost step.
- `CHANGELOG.md` `[Unreleased]` gains "Revision after the second review of PR 26", one line per
  finding saying what it came to. The version stays 0.0.1.
- Each claim that rests on a transcript still names what it was measured on; what is held by a
  stand-in alone (two alerts, a non-number marker value) says so.

## Task 7: Drafts and issue revisions, nothing written to GitHub without the owner's word

- **patchbay-vital#27** (finding 11). Its body already quotes "Closing or ordering out the
  alert's window before returning would stop the growth". Compare the second review's words
  against it. If nothing is new, change nothing and say so in the reply. If something is (the
  alert "never … released", the long agent run), show a "Revised 2026-11-18" paragraph in the
  reviewer's words, marked unverified, then revise the body in place and read it back. No
  comment is posted. The fork-safety point goes there only if it bears on the window.
- **patchbay-vital#25** (finding 19). Show the owner one "Revised 2026-11-18" paragraph before
  it is written: a trial child would also be the only remedy for the block on platforms other
  than macOS, where nothing is watched and nothing was probed; the reviewer's words where they
  are his, marked unmeasured. Earlier text kept; read back from GitHub.
- **Deferred-items issue** on patchbay-vital, host.py cleanups: findings 14 and 16 in the
  reviewer's own words, marked unverified; it blocks nothing and is not among the issues before
  the first agent experiment. For 14 it carries the constraint that on macOS a missing
  `pthread_main_np` means the host refuses to load (`plugin-state.md`). That note is beyond the
  reviewer's words, so the draft is shown first. Filed after the gate's clean run unless a file
  in the tree names it by number.
- **Reply to the review**, for the owner to post: one line per finding, 1 to 19 in order: holds,
  holds but narrower, or does not hold; then fixed, declined, deferred or stands, with the file,
  test, transcript or issue. It carries: for 5, which check refuses first; for 6, whether the
  validator refuses any of the five kinds (none); for 12 and 13, `costs.txt`'s figures; for 15,
  the owner's condition and
  `test_a_state_write_from_a_second_thread_is_refused_by_the_write_itself`; for 17,
  `preset-tests.md` and the stand-in test in each module; for 18, the three checks; for 19,
  that the trial child is #25's first candidate with its cost (2.38 s a load fresh, or about
  500 to 970 MiB kept up), its one slip (`random_values`, 1 of 11), and what it does and does
  not cover by `probes-4-counts.txt`.
- **In `shape.md`**: every count, limit and Decision in PR 26's description this revision makes
  untrue, each with its new value and source. The owner writes the description.

## Task 8: Retrospective edits, from the shipped code, each shown old beside new before writing

- `vital/plugin-state.md`: the watch bullet (1, 8, 10; no text was seen to raise two alerts, so
  that is held by the stand-in alone), the marker bullet (2, 6; Vital's reading of a non-number
  there was not measured, because such a text is never sent), the floating-point bullet (9).
- `vital/instrument.md`: the lost-step bullet (3, 4).
- `index.yml`: this repository's `vital:` entries, kept in step. The `base:` section is not
  touched.
- Base proposal, in `shape.md` only, under "Standards retrospective (proposed, base)":
  `base/testing/tests.md`, where test support two suites share lives. It states the question
  and the evidence (two suites, one helper, the negative-harness rerun a new file under
  `tests/` costs) and proposes a home; no file moves here. Its expected home is
  patchbay-standards#40, whose proposal 1 held a shared helper handed out as a fixture from
  `tests/conftest.py` and was withdrawn on 2026-11-12 for want of an instance: a "Revised
  2026-11-18" paragraph there, a new issue only if #40 turns out not to be its home. `shape.md`
  says which and why.

These edits are written before Task 9 so the final runs are on the final tree.

## Task 9: One rerun on the final tree. Asked for once.

Ask the owner once, saying how many windows will show and for how long (one mutant leaves a
real alert open by design, in a child its test kills). Then, on one still tree:
- `remedy-run.txt` (the 335 texts), `rollback-count.txt`, `marker-count.txt`, from the scripts
  the earlier transcripts embed;
- `mutation.txt`: the earlier mutants, each adaptation to moved code listed, plus one per new
  guard of this revision: the kept method put back; state and install under one `try`; the
  nested-entry refusal; the plant inside the `try`; the count raised before the change; the
  instrument's use of the count (refusal without rollback, and nothing marked); the non-number
  refusal; the callback's flag; every alert reported; `_section`'s guarded read. Each fails the
  test named for it, and none survives;
- `gate-run.txt`: `scripts/gate.sh` with the date and branch.

If any figure differs from what the docs or the Task 8 edits state, stop and present. Earlier
specs' transcripts stay as they ran; the issue #20 spec's and the first revision's `shape.md`
each gain a dated note naming these reruns.

## Task 10 (FINAL): Verification gate

1–6. `scripts/gate.sh`: `bash -n` over the scripts git lists under `scripts/`; `uv sync
   --locked` and `ruff format --check`; `ruff check`; `mypy`; `pytest -c pyproject.toml -p
   no:doctest`; `scripts/sync-standards.sh --check`. Exit 1 at the first failing step, by name.
   The kept run is Task 9's `gate-run.txt`. A failing step is fixed at its cause and rerun.
7. **Docs**: README, CLAUDE.md, the docstrings and every standard naming what changed read
   true. Recorded in `shape.md`.
8. **Version**: the `[Unreleased]` entry; 0.0.1 kept.
9. **Standards retrospective**, last: the four questions asked of the shipped diff, the project
   edits listed as their own change set, `Proposals sent upstream:` recorded. The base proposal
   is shown whole to the owner by AskUserQuestion with a "None of these" option, and filed or
   revised into #40 only at the owner's word, after the gate's clean run, with no attribution;
   declined ones marked by name.

Then file or revise whatever the owner approved, read each back, stop, and print
`git status --short`. Nothing is committed or pushed. The feature's files and the
retrospective's are listed apart.

## Appendix A: the owner's answers in shaping, verbatim (2026-11-18)

**1 and 2 (set-back)**, to "Fix both, own method kept": "1. Conditions:
- The watch reads runModal's own implementation once when it is built, through the runtime with argument and return types declared, and holds it for its lifetime. The finally installs that kept one whatever happened in the try, including when the install never ran; putting it back twice is harmless and a test holds that.
- "In place" for the nested-entry refusal is the watch's own state, set inside the try, and cleared in the finally after the kept method is back; a test holds that a refused nested entry leaves the first entry's state and method as they were.
- The marker: the value it had is read before the try, the plant is inside it, and the finally sets it back whenever the read succeeded, planted or not.
- Tests, on stand-ins, no Vital: KeyboardInterrupt raised from the install, from the line after it, from the setter that plants, and from the line after that; each asserts the method is the kept one, the marker is at the value it had, and the interrupt leaves as itself.
- Each has a mutant. plugin-state.md's watch and marker bullets are rewritten from the shipped code, old beside new.
- If the review has more findings, fix them all first. This changes code in host.py, so the four evidence runs are owed once more on the final tree: ask me once, at the end."

**3 and 4 (lost step)**, to "Host counts writes begun": "1. Conditions:
- The count is raised before the first change, never after it, so an interrupt between the two errs on the safe side: counted as begun, nothing changed, treated as sent. A test holds that order with an interrupt raised from the setter.
- The instrument reads the count once before the first of its two loads. Unchanged after an error: nothing was sent, a PluginStateError becomes PatchRefusedError with no rollback and no lost step, and a foreign error leaves as itself with nothing marked. Changed: exactly as today, including an error that strikes in the second load before its own change, since the plugin then holds the first load's text.
- The count is read-only from outside the host, a plain property with no setter, documented as "state writes begun", and it is not part of core's contract.
- Tests on stand-ins: a refused marker read before any change; KeyboardInterrupt and MemoryError before any change; each of those again after the first load's change; the rollback's own loads counted the same way.
- Each has a mutant. load_patch's docstring and instrument.md's lost-step bullet are rewritten from the shipped code, old beside new; the sentence "the instrument cannot tell those two apart" goes, and shape.md records that the last revision's choice was replaced.
- The single evidence rerun still comes once, at the end."

**5, 6 and 7 (reading a preset)**, an answer of the owner's own: "4. Conditions:
- 5: no code change; one test that a null section is refused by name before check_loadable, and the reply records the finding as "does not hold", with which check refuses first.
- 7: _section reads through decoded() and refuses as PatchRefusedError, tested at the decoder's own limit, bisected in the test; one mutant.
- 6: where the text holds the marker's key and its value is not a JSON number (true and false included), load_state raises PluginStateError naming the key and the value's kind, before the count of writes begun is raised and before the plugin is touched. A text without the key is as today. Tests on the stand-in for true, false, null, a string and an array; one mutant.
- Say whether the state's validator already refuses any of those five before _planted is reached; if it does, the test for that kind holds the order and the reply says so.
- plugin-state.md's marker bullet says that Vital's reading of a non-number there was not measured, because such a text is never sent. No probe is run.
- The single evidence rerun still comes once, at the end."

**8, 9 and 10 (alert callback)**, to "Fix 8 and 10, document 9": "2. Conditions:
- 8: the flag is the first thing the callback does and is something that cannot fail to store (no allocation); the whole body after it is guarded; _write raises PluginStateError when the flag is set, whether or not the alert could be noted, saying so when it could not. Test on the stand-in with a noting step that raises MemoryError; one mutant.
- 10: every alert's words in the error, in the order they were answered, with the count; test on the stand-in with two alerts in one write; one mutant. plugin-state.md says no text was seen to raise two alerts, so this is held by the stand-in alone.
- 9: no code. The module docstring names the callback as the one place the package's Python runs under the plugin's floating-point environment, says it does no float arithmetic, and says why it is not switched (nothing may fail before the alert is noted). A comment at the callback says the same in one line, so a later edit that adds float work sees it.
- plugin-state.md's watch bullet and floating-point bullet are rewritten to match, old beside new.
- The single evidence rerun still comes once, at the end."

**11, 12, 13 and 15 (repeats)**, to "All four stand": "1, without the comment. Conditions:
- patchbay-vital#27: check whether its body already carries the close-the-window suggestion in the reviewer's first-round words. If it does, nothing is changed and the reply says so. If the second review adds anything not already there, revise the body in place with a "Revised 2026-11-18" paragraph in the reviewer's words, marked unverified, and read it back. No comment is posted.
- 12, 13 and 15 stand. The reply cites costs.txt with its figures for 12 and 13, and for 15 my condition and the test that holds it (a caller that skips the helper still cannot write).
- The fork-safety point is recorded in shape.md and the reply as unmeasured, with the otool lines, and added to patchbay-vital#27 only if it bears on the window; otherwise it is listed for a later issue in the reviewer's words and not filed now."

**14 and 16 (tidiness)**, to "Defer both": "3. Conditions:
- One deferred-items issue on patchbay-vital for host.py cleanups, in the reviewer's own words, marked unverified, holding 14 and 16. It blocks nothing and is not among the issues before the first agent experiment.
- For 14 it notes, as a constraint on whoever takes it, that on macOS a missing pthread_main_np means the host refuses to load, per plugin-state.md, and the cleanup must not change that.
- If nothing in the tree will name it by number, it is filed after the gate; show it to me first only if it says anything beyond the reviewer's words.
- The reply lists both as deferred with the issue's number."

**17 and 18 (test helpers)**, to "Decline both, propose a home": "1. Conditions:
- The reply says for 17 that the copy is deliberate, citing preset-tests.md and the stand-in test in each module that holds the two alike; and for 18 that "not killed by the parent" is one of the three checks the standard names, true at every real call by design.
- The base proposal is checked against patchbay-standards#40 first (shared values through tests/conftest.py). If it refines #40, it is revised into #40 with a dated paragraph; a new issue only if #40 is not its home. Say which and why.
- It states the question and the evidence (two suites, one helper, the negative harness rerun a new file under tests/ costs) and proposes a home; it does not move any file here.
- Shown to me whole at the end, filed only at my word."

**19 (design)**, an answer of the owner's own: "4. Reply, plus one in-place revision of patchbay-vital#25. No comment, no new issue.
- The reply says the design is outside this PR, that the trial child is already #25's first candidate with its measured cost (2.38 s a load fresh, or about 500 to 970 MiB kept up) and its one slip (random_values, 1 of 11), and that by run 4's figures a trial child covers the block and most crashes but not a text Vital loads silently wrong, with the transcript named.
- patchbay-vital#25 gains a "Revised 2026-11-18" paragraph with the one point it does not yet hold: a trial child would also be the only remedy for the block on platforms other than macOS, where nothing is watched and nothing was probed; in the reviewer's words where they are his, marked as unmeasured. Earlier text kept; read back from GitHub.
- Show me that paragraph before it is written into #25."

**Setup**, to "As listed": "1. As listed. One reminder for the plan, not a change to the setup: this is the last round. Anything the work turns up that is not a correctness defect is listed for a later issue in shape.md and not fixed here."
