# Revision after the second review of PR 26 (issue #20) — Shaping Notes

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The second review on PR 26 (fromtheoutfit/patchbay-vital#26, "Keep a preset Vital cannot read
from blocking the calling process on macOS", closes #20): issue comment 6965953694, "Review
findings at c8ed333", by the owner, 2026-11-18 01:13 UTC. It lists 19 findings and says "None
has been verified yet: each is a lead to check against the code, not a confirmed bug". Each was
checked against the code at `c8ed333` while shaping, and decided by the owner with conditions
("Shaping answers" below). The branch is the PR's,
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`. No agent
commits, pushes, opens a pull request or posts to the PR.

**This is the last round,** in the owner's words: "Anything the work turns up that is not a
correctness defect is listed for a later issue in shape.md and not fixed here."

| # | Finding, as the review gives it | Where |
|---|---|---|
| 1 | The alert callback can stay installed for good | `host.py:271` |
| 2 | The marker is planted outside the `try` that sets it back | `host.py:765` |
| 3 | An error raised before anything is written marks the instrument permanently lost | `instrument.py:351` |
| 4 | `except BaseException` marks the instrument out of step before any text is sent | `instrument.py:355` |
| 5 | A `null` section counts as absent | `patch.py:405` |
| 6 | A JSON boolean for the marker key is read as absent | `host.py:499` |
| 7 | `_section` bypasses the guarded decode | `patch.py:424` |
| 8 | The callback can raise and leave the alert unanswered | `host.py:252` |
| 9 | The callback's Python runs under Vital's floating-point environment | `host.py:700` |
| 10 | Only the first alert is reported | `host.py:711` |
| 11 | Each answered alert leaks a window | `host.py:652` |
| 12 | AppKit loads as soon as the module is imported | `host.py:461` |
| 13 | The whole preset is parsed on every write | `host.py:499` |
| 14 | The C library is looked up twice | `host.py:355` |
| 15 | The main-thread check runs twice per load | `host.py:694` |
| 16 | Two flags for one cached result | `host.py:568` |
| 17 | Test helpers are copied between suites | `test_vital_instrument.py:866` |
| 18 | The `killed` keyword is never used | `test_vital_instrument.py:866` |
| 19 | Three per-platform fixes for one root problem | `host.py:41` |

## What was checked while shaping

Each check was a read of the code at `c8ed333`, with nothing written to the tree and nothing run
against Vital. None of it is evidence for a claim in a doc or a standard: a figure is quoted only
from a kept transcript.

- **1, holds.** `_AppKitWatch.answered` calls `self._install(...)` at `host.py:278` and sets
  `self._alerts` on the next line, both before its `try`. An interrupt between the install and
  the `try` leaves the callback installed with `_alerts` None; the next entry passes the guard
  and saves the callback's own address as the original.
- **2, holds.** `load_state` plants the marker at `host.py:766-767` and enters its `try` on the
  line after. An interrupt between the two, or a refusal raised by the plant itself, leaves with
  no set-back.
- **3, holds but narrower.** `load_patch` answers every `PluginStateError` from `_sent` with a
  rollback. Through the instrument the marker's lookup cannot raise one: `__init__` calls
  `parameter_ids()`, which resolves the map. What can is a refused read or set of the marker
  itself, before the write. The rollback then meets the same refusal and the instrument is
  marked lost, though no text was sent.
- **4, holds.** The `except BaseException` around `_sent` covers the thread check, the
  validation and `_planted`'s decode, all before the plugin is given anything. The first
  revision recorded this as its reading of the owner's condition: "a foreign error that strikes
  inside `load_state` before it reaches the plugin also marks the instrument out of step: the
  instrument cannot tell those two apart."
- **5, does not hold.** `VitalPreset.opaque` never holds `null`. The model's validator
  (`preset._json_section`) refuses a section whose text does not begin `[` or `{`, and the file
  reader (`format._read_settings`) takes only a list or an object as a section, so a `null`
  under `custom_warps` is refused there by name. `_section`'s `None` therefore only ever means
  the key is absent.
- **6, holds for a bare `VitalHost.load_state` alone.** `_planted` reads a boolean as absent.
  The file reader refuses a setting that is no float, so no text the instrument sends holds one.
  What Vital does with `true` there was not measured. The state's validator
  (`state.PluginState._text_is_one_object`) checks only that the text is one JSON object, so it
  refuses none of `true`, `false`, `null`, a string or an array under the marker's key.
- **7, holds.** `patch._section` reads with `DECODER.decode`, at another stack depth than the
  model's validator, which read the same section through `decoded`.
- **8, holds.** In `_answered_at_once` only the text read is guarded: `noted.append(...)` and the
  assignment in the `except` are not.
- **9, holds.** The callback runs inside `self._plugin.preset_data = data`, under `_reached`, so
  under whatever environment Vital has set by then. It does no float arithmetic today.
- **10, holds.** `_write` reports `alerts[0]` alone. No kept transcript shows whether Vital
  raises two alerts for one text.
- **11, a repeat.** Open as fromtheoutfit/patchbay-vital#27, whose body quotes the first
  review's "Closing or ordering out the alert's window before returning would stop the growth".
- **12, a repeat with one new point.** Declined in the first revision on `costs.txt`: pedalboard's
  native module links AppKit and libobjc, and the watch was built in a median of 0.123 ms. The
  fork-safety worry is new and unmeasured.
- **13, a repeat.** Declined in the first revision on `costs.txt`: a decode took a median of
  0.60 ms on the median-sized installed preset and 5.19 ms on the largest, 10 MB.

The figures for 12 and 13 above are `costs.txt`'s own. The plan, and the questions put to the
owner while shaping, gave them as 0.14 ms, 0.6 ms and 5.1 ms, which were the first revision's
shaping reads as its plan's table holds them, not the kept transcript's. `plan.md` is left as it
was approved; everything written from here quotes the transcript.
- **14, holds.** `_alert_watch` calls `find_library("c")` and `CDLL` though the module holds the
  library as `_LIBC`.
- **15, a repeat.** The check in `_write` was the owner's condition in the first revision: "The
  write itself also refuses when the check fails, so a later caller that forgets the helper
  cannot write from another thread; a test holds it."
- **16, holds.** `_marker_sought` and `_marker_found` are two attributes for one cached result.
- **17, recorded as deliberate.** `agent-os/standards/vital/preset-tests.md`: "a module of one
  suite cannot import from the other's, and test support shared between them has no home in the
  layout."
- **18, by design.** The same standard names "no kill by the parent" as one of three checks
  judged together; a killed child raises `TimeoutExpired` before the function is asked, so the
  keyword is False at every real call.
- **19, a design point.** Crashes are fromtheoutfit/patchbay-vital#25's, whose first candidate
  remedy is already a trial load in a child process.

## Shaping answers

In the owner's words, 2026-11-18, by AskUserQuestion. The option chosen is named first.

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

## Decisions

1. **The scope is the review comment, every finding,** each checked against the code before it
   was decided. Where the check disagreed with the reviewer, the reply says what was found.
2. **Finding 1: the watch keeps `-[NSAlert runModal]`'s own implementation from the day it is
   built** and never takes it from a swap's return. `answered()` sets its state and installs
   under one `try`, and its `finally` puts the kept implementation back whatever happened.
3. **Finding 2: the marker's plant is inside the `try` that sets it back.** The value it had is
   read before it.
4. **Findings 3 and 4: the host counts state writes begun, and the instrument asks whether the
   count moved.** Unchanged after an error, nothing was sent: a `PluginStateError` is a refused
   patch with no rollback and no lost step, and a foreign error leaves as itself with nothing
   marked. Changed, everything is as it was.
5. **Finding 5 does not hold.** No code changes; one test holds the refusal that comes first.
6. **Finding 6: a marker value that is no JSON number is refused,** as `PluginStateError` naming
   the key and the value's kind, before the count is raised. No probe is run.
7. **Finding 7: `_section` reads through `decoded()`** and refuses as `PatchRefusedError`.
8. **Finding 8: the callback stores a flag first, and everything after it is guarded.** A write
   in which the flag was set is `PluginStateError` whether or not the alert could be noted.
9. **Finding 9 is documented, not changed.** The callback is the one place the package's Python
   runs under the plugin's floating-point environment; it does no float arithmetic.
10. **Finding 10: every alert answered is in the error,** in order, with the count.
11. **Findings 11, 12, 13 and 15 stand as they were decided.** patchbay-vital#27 is revised in
    place only if this review says something its body does not. No comment is posted.
12. **Findings 14 and 16 are deferred** to one issue on fromtheoutfit/patchbay-vital for
    `host.py` cleanups, in the reviewer's words, marked unverified.
13. **Findings 17 and 18 are declined,** and the question of where test support two suites share
    lives goes upstream as a base proposal, checked against patchbay-standards#40 first.
14. **Finding 19 is answered in the reply,** and patchbay-vital#25 gains one dated paragraph,
    shown to the owner before it is written.
15. **One rerun of the issue #20 evidence, on the final tree, asked for once at the end:**
    `remedy-run`, `rollback-count`, `marker-count` and `mutation`, this revision's mutants with
    them, and the gate.
16. **No gate file changes,** and no file is added, removed or renamed under `scripts`, `src`,
    `tests` or `agent-os/standards`, so the negative harness is not rerun.
17. **This is the last round.** What the work turns up that is no correctness defect is listed
    under "For a later issue, not filed" and not fixed.

### What was replaced while shaping, and why

- **The first revision's reading of a foreign error before the write.** Its plan read the
  owner's "inside the send" as "from the first `load_state` on", and said so: "a foreign error
  that strikes inside `load_state` before it reaches the plugin also marks the instrument out of
  step: the instrument cannot tell those two apart." Finding 4 showed that this contradicts
  `load_patch`'s own docstring, "An error raised before the text is sent … loses no step".
  Decision 4 above replaces it: the host's count lets the instrument tell them apart. That
  spec's text is left as it is.

### Read in the plan

- **"The finally sets it back whenever the read succeeded, planted or not"** (findings 1 and 2):
  on an error the set-back runs whether or not the plant's line completed. A load that succeeded
  is not set back to the value before: the marker then holds the text's value, and is read for
  the verdict as before.
- **"Before the plugin is touched"** (finding 6): before any call that changes the plugin and
  before the marker's value is read. The one-time map lookup, which on a bare host's first load
  reads the plugin's name and version, comes first, since the key is the map's. Where the map is
  not the plugin's the load is unchecked as it was, and nothing is refused.

### For a later issue, not filed

- **`_AlertWatch`'s docstring** in `host.py` says what the watch answers and where a write may
  be made, and not that it also says whether an alert was answered (`alerted`). Found in the
  Docs step, after the tree was final. Not a correctness defect.
- **Finding 12's fork-safety point,** in the reviewer's words: "It also brings process-wide side
  effects, such as Objective-C fork-safety aborts in children forked after AppKit's initializers
  ran." Unmeasured. It does not bear on the alert's window, so it is not added to
  patchbay-vital#27. The first revision's `verification/costs.txt` shows pedalboard's own native
  module linking AppKit, so `import pedalboard` loads it whether or not the watch is built:

  ```
  /System/Library/Frameworks/AppKit.framework/Versions/C/AppKit (compatibility version 45.0.0, current version 2575.60.5)
  /System/Library/Frameworks/Cocoa.framework/Versions/A/Cocoa (compatibility version 1.0.0, current version 24.0.0)
  /System/Library/Frameworks/Foundation.framework/Versions/C/Foundation (compatibility version 300.0.0, current version 3502.1.255)
  /usr/lib/libobjc.A.dylib (compatibility version 1.0.0, current version 228.0.0)
  ```

## The owner's answers during the build

In the owner's words, 2026-11-18. The first four were to one set of questions, put once the code,
the tests and the docs were written and before anything was written to the standards or to
GitHub; the last three to what that left open.

**The standards edits, old beside new**, to "Write as drafted": "1. Write as drafted, as their own change set, before the rerun. Conditions:
- After the rerun and before the gate, every test, name, mutant and transcript the edited standards cite is checked over the whole tree, the listing kept, as last time. Every mutant is cited with the spec whose mutation.txt holds it.
- Any figure or citation that differs from the rerun: the standard is corrected to the transcript and shown to me. An edit after the rerun is tied to the final tree by the kept listing of differing paths, none of them code."

**The paragraph for patchbay-vital#25**, to "Write, with changes": "2. One sentence added after the reviewer's quoted words, then write it and read it back:
"By this issue's own evidence a trial child covered the block and, with two loads, the crashes seen but for one slip (random_values, 1 of 11 fresh children); it cannot see a text Vital loads in part, and a load ignored whole is seen only if the child makes the marker check too (probes-4-counts.txt)."
Check each clause against the transcript before writing; if any clause is not what the transcript shows, correct it to the transcript and show me the sentence. Nothing else in the body changes. The same text goes into shape.md first, so what is filed equals what is recorded."

**The paragraph for patchbay-vital#27 and the cleanups issue**, choosing both: "1 and 2. Conditions:
- #27: the paragraph claims nothing beyond the reviewer's words; the three additions are listed as his, unverified. Earlier text kept, no comment, read back from GitHub.
- The cleanups issue: filed after the gate's clean run, blocks nothing, not among the issues before the first agent experiment, the pthread_main_np constraint stated as drafted. Read back; its number goes into the reply only, since nothing in the tree names it."

**The single rerun**, to "Not now": "3. Finish everything that does not depend on the runs: write the standards, revise #25 and #27 as answered, and confirm the tree is final (nothing outside the spec folder left to edit). Then wait. I will say when to start the rerun."

**The sentence for #25, after the check**: "1. The #25 sentence: accept your corrected version as it stands in shape.md. Write it into #25 after the reviewer's quoted words, nothing else in the body changed, and read it back. shape.md keeps my sentence, the check and yours, as you have it."

**A clause for `vital/preset-file.md`**, which the first set of edits had not shown: "2. The preset-file.md clause: write it now, as shown, with its "Verified against" additions, in the standards change set. It is covered by the citation checks after the rerun."

**The rerun, again**: "3. The rerun: not yet. Wait for my word; I will give it when I am at the office."

What was written to GitHub at these answers, each read back, no comment posted on either:

- **patchbay-vital#27**, 2026-11-18: the "Revised 2026-11-18" paragraph under "Drafts for the
  owner", 1, placed before "What is already recorded". No earlier line changed.
- **patchbay-vital#25**, 2026-11-18: the paragraph under "Drafts for the owner", 2, as written
  whole there, a paragraph of the trial-load bullet under "Candidate remedies". No earlier line
  changed.

## Decisions made during the build

Each is a choice the plan left open, or a reading of one of the owner's conditions.

1. **The watch says whether an alert was answered: `alerted()`,** on `_AlertWatch`, `_NoWatch`,
   `_AppKitWatch` and `builders.StandInWatch`. The callback's mark is the attribute behind it,
   `_alerted`, set False when the watch is entered and True as the callback's first statement.
   `_write` asks it and no longer asks whether the list is empty, so an alert that could not be
   noted is refused like any other (finding 8).
2. **"With the count" (finding 10) is read as: the count is stated where there is more than
   one.** One alert keeps the wording it had, "Vital answered the state with its alert, …",
   which says one; an integration test against Vital and the evidence scripts read that wording.
   Two or more read "Vital answered the state with 2 alerts: 1, …; 2, …".
3. **`writes_begun` is raised once by a load and once by a measurement,** in `load_state`
   before the plant, or before the write where the load is unchecked, and in `measure` before
   its first set. `_write` itself raises nothing: its two callers do.
4. **The refusal of a marker value that is no number is in `_planted`,** where the value is
   read, and names six kinds: a boolean, null, a string, an array, an object. The owner's five
   are tested, and an object with them.
5. **This revision's mutants are MQ1 to MQ15.** `MS`, the natural name, is the PR 23 revision's
   in `vital/instrument.md` ("the first revision's MS1 to MS4"), and `MQ` is cited by no
   standard and held by no transcript.
6. **Finding 5's two refusals name different things.** The file reader names the key,
   `UnknownSettingError('custom_warps')`. The preset's validator, reached through `preset_of`,
   says what a section is, "a section is the text of a JSON array or object", and names the
   field `opaque`, not the key. The test holds each as it is; the reply says so.
7. **The decoder-depth helpers moved from `tests/unit/test_host.py` to `tests/unit/builders.py`,**
   as `nested` and `first_depth_the_decoder_refuses`, since `test_patch.py` now needs them too.
   No file is added.
8. **Finding 7 is tested on a preset built without its validator,** by `model_copy(update=…)`,
   which pydantic does not validate: the validator would refuse the section before `_section`
   could, by the margin the finding is about.
9. **The watch reads the method's own implementation when it is built,** which is when the
   module is imported, as the watch always was. Finding 12, building it later, stands declined.

## Drafts for the owner

Nothing here is written to GitHub by an agent before the owner's word.

### 1. fromtheoutfit/patchbay-vital#27, a paragraph revised into its body

The body already holds the first review's suggestion, "Closing or ordering out the alert's
window before returning would stop the growth". The second review's finding 11 adds three
things it does not hold: that the alert is never released, where the close would go, and the
case the growth matters in. Placed after the sentence on the line number, before "What is
already recorded". The owner's condition, 2026-11-18: "the paragraph claims nothing beyond the
reviewer's words; the three additions are listed as his, unverified", so its last paragraph was
rewritten from the first draft, which called the release "a second thing to measure beside the
close", a claim of the draft's own. As written into #27:

> Revised 2026-11-18. The second review of PR 26 (fromtheoutfit/patchbay-vital#26, "Review
> findings at c8ed333", 2026-11-18) gave this again, as its finding 11. In the reviewer's own
> words, and **unverified** as before: the revision that answered that review probed nothing
> for it either.
>
> > **11. Each answered alert leaks a window** `src/patchbay_vital/host.py:652` Every answered
> > alert leaves behind an NSWindow that is never shown (500 after 500 alerts, per the
> > docstring), and the callback never closes or releases the alert. A long agent run that sends
> > thousands of bad patches keeps growing memory in one process. Sending `[[alert window]
> > close]` (or `orderOut:`) after reading the texts would avoid it.
>
> What this adds to the first review's words, each the reviewer's and each unverified: that
> the callback "never closes or releases the alert"; that the close would come "after reading
> the texts"; and the case, "a long agent run that sends thousands of bad patches". The line
> number is the review's, at `c8ed333`.

### 2. fromtheoutfit/patchbay-vital#25, a paragraph revised into its body

Shown to the owner before it is written. Placed under "Candidate remedies, for this spec to
probe", after the bullet on a trial load in a child process. The owner asked for one sentence
more, each clause to be checked against the transcript first; the check found three clauses
that are not what the transcript shows (below the draft), and the owner accepted the sentence
as the transcripts show it. The first draft:

> Revised 2026-11-18 (after the second review of fromtheoutfit/patchbay-vital#26, "Review
> findings at c8ed333", its finding 19). One point this issue did not hold, and it is
> **unmeasured**: a trial load in a child process would also be the only remedy for the block
> on a platform other than macOS. The host answers Vital's alert on macOS alone; on any other
> platform nothing is watched, so a text Vital cannot read may block its caller there, and
> nothing was probed there. In the reviewer's words: "Nothing protects Linux or Windows from
> the alert", and "Loading the text in a child Vital process with a timeout, before the
> in-process load, would cover hangs, ignored loads and crashes the same way on every platform,
> without changing global Objective-C state." No child was run on any platform but macOS:
> whether Vital raises its alert there at all, and what a trial child costs there, are not
> known.

The owner's sentence, 2026-11-18, to follow the reviewer's quoted words: "By this issue's own
evidence a trial child covered the block and, with two loads, the crashes seen but for one slip
(random_values, 1 of 11 fresh children); it cannot see a text Vital loads in part, and a load
ignored whole is seen only if the child makes the marker check too (probes-4-counts.txt)."

Each clause against the issue #20 spec's transcripts:

- **"a trial child covered the block":** not `probes-4-counts.txt`'s to show. Every child of run
  4 loaded "on the main thread under the watch 'answer'", so on the 249 texts that alert the
  watch answered and the child returned (verdict `AA` in the fresh child): none waited on the
  alert. A child that did wait is in `probes-2-alert.txt`, section 2a, no watch: on 2 of 2
  texts it "DID NOT RETURN within 3 s: the child is killed, by design (gone 11 ms after the
  kill)". That, a child ended at its limit, is what a platform with no watch would rely on.
- **"with two loads, the crashes seen but for one slip (random_values, 1 of 11 fresh
  children)":** as the transcript shows, with its label read as that spec's `shape.md` corrects
  it. Section 4c: each of the 3 texts' children died in all 11 fresh children, `custom_warps`
  and `wavetables` in the first load (`X?`), `random_values` in the second (`-X`) in 10. Its
  eleventh is printed `!!`, "the child died before the text's first load was said", which is
  the third of that spec's "Four mislabels in the transcripts": the child had reported both
  loads returned and died at exit.
- **"it cannot see a text Vital loads in part":** so by its verdict: the 82 texts that load
  have the verdict `--` from every source. Section 4d adds what a read of the plugin would
  see: the check of the four sections that come back flags 32 of the 82 (5, 10, 3 and 14).
- **"a load ignored whole is seen only if the child makes the marker check too":** section 4d
  has the one text ignored whole "flagged by the markers 1, by the floats 1, by the sections
  1". Any of the three reads sees it, not the marker check alone; the verdict alone does not.

The sentence as the transcripts show it, for the owner to accept or change:

> By this issue's own evidence: with no watch, a child that waited on the alert did not return
> within 3 s and was killed, on 2 of 2 texts (`probes-2-alert.txt`, 2a), which is what a
> platform with no watch would rely on; under the watch, as every child of run 4 was, a trial
> child with two loads died on each of the 3 texts seen to crash but for one slip
> (`random_values`, 1 of its 11 fresh children, which returned from both loads and died at
> exit: the transcript prints it `!!`, the third of the issue #20 spec's "Four mislabels in the
> transcripts"); by its verdict it cannot see a text Vital loads in part, 82 texts returning
> from both loads with no alert, of which a read of the four sections that come back would flag
> 32; and the one load ignored whole is seen only if the child reads the plugin back too, where
> the markers, the floats and the sections each flagged it (`probes-4-counts.txt`, 4b to 4d).

Accepted by the owner on 2026-11-18, "as it stands", and written into #25 after the reviewer's
quoted words, nothing else in the body changed. The paragraph as written, whole:

> Revised 2026-11-18 (after the second review of fromtheoutfit/patchbay-vital#26, "Review
> findings at c8ed333", its finding 19). One point this issue did not hold, and it is
> **unmeasured**: a trial load in a child process would also be the only remedy for the block on
> a platform other than macOS. The host answers Vital's alert on macOS alone; on any other
> platform nothing is watched, so a text Vital cannot read may block its caller there, and
> nothing was probed there. In the reviewer's words: "Nothing protects Linux or Windows from the
> alert", and "Loading the text in a child Vital process with a timeout, before the in-process
> load, would cover hangs, ignored loads and crashes the same way on every platform, without
> changing global Objective-C state." By this issue's own evidence: with no watch, a child that
> waited on the alert did not return within 3 s and was killed, on 2 of 2 texts
> (`probes-2-alert.txt`, 2a), which is what a platform with no watch would rely on; under the
> watch, as every child of run 4 was, a trial child with two loads died on each of the 3 texts
> seen to crash but for one slip (`random_values`, 1 of its 11 fresh children, which returned
> from both loads and died at exit: the transcript prints it `!!`, the third of the issue #20
> spec's "Four mislabels in the transcripts"); by its verdict it cannot see a text Vital loads
> in part, 82 texts returning from both loads with no alert, of which a read of the four
> sections that come back would flag 32; and the one load ignored whole is seen only if the
> child reads the plugin back too, where the markers, the floats and the sections each flagged
> it (`probes-4-counts.txt`, 4b to 4d). No child was run on any platform but macOS: whether
> Vital raises its alert there at all, and what a trial child costs there, are not known.

### 3. A new issue on fromtheoutfit/patchbay-vital, filed after the gate's clean run

Shown first, since the constraint under the first item is not the reviewer's. Approved by the
owner on 2026-11-18 and filed after the gate's clean run as fromtheoutfit/patchbay-vital#28,
read back from GitHub: the body written, a paragraph a line. Nothing in the tree outside this
spec folder names it by number.

**Title:** The host: two cleanups from the second review of PR 26, unverified

> The second review of PR 26 (fromtheoutfit/patchbay-vital#26, "Review findings at c8ed333",
> 2026-11-18) listed these under "Cost, duplication and tidiness", as its findings 14 and 16.
> Each is given as the reviewer stated it and is **unverified**: a lead to check against the
> code, not a confirmed defect. It blocks nothing, and it is not among the issues that come
> before the first experiment that puts an agent in front of the instrument.
>
> - **The C library is looked up twice** (`src/patchbay_vital/host.py:355`): "`_alert_watch`
>   calls `find_library("c")` and CDLL again, although the module already holds the library as
>   `_LIBC`. If the two lookups ever resolved differently, the library used for the
>   floating-point environment and the one used for `pthread_main_np` would no longer match.
>   Fix: pass `_LIBC` in, checking `hasattr(_LIBC, "pthread_main_np")`."
>
>   A constraint on whoever takes it: on macOS a missing `pthread_main_np` means the host
>   refuses to load (`agent-os/standards/vital/plugin-state.md`, "A state is written under a
>   watch that answers the alert, on macOS"), and the cleanup must not change that.
> - **Two flags for one cached result** (`src/patchbay_vital/host.py:568`): "`_marker_sought`
>   and `_marker_found` have to be kept in step by hand. A later edit that sets one without the
>   other would make `_marker` return a stale `None` or search again on every call. One
>   sentinel-valued attribute would do the same job."
>
> The line numbers are the review's, at `c8ed333`.
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. Each item is checked against the code first,
> then fixed or declined with its reason. CHANGELOG; gate green. No commit, pull request or push
> by an agent.

### 4. Reply to the second review of PR 26, for the owner to post

Not posted by an agent. Written after the single rerun, from its transcripts.

> Revised in `agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/`. Each finding was checked against the code at `c8ed333` before it was decided. Nothing new was measured on Vital: the issue #20 evidence was run again on the final tree, and what a stand-in alone holds says so. The transcripts named are in that spec's `verification/` unless another spec is named; a mutant is one of its `mutation.txt`'s 54, each caught.
>
> 1. **Holds.** **Fixed:** the watch reads `-[NSAlert runModal]`'s own implementation once, when it is made, and never takes it from a swap's return; its state and the install are under one `try`, whose `finally` puts the kept one back (`test_an_interrupt_in_the_watch_s_install_leaves_the_method_its_own`, `test_putting_the_method_s_own_implementation_back_twice_changes_nothing`, `test_a_refused_nested_entry_leaves_the_first_entry_s_state_and_method_as_they_were`; MQ1 to MQ3).
> 2. **Holds.** **Fixed:** the value the marker had is read before the `try`, and the plant is inside it (`test_an_interrupt_in_the_marker_s_plant_leaves_as_itself_and_the_marker_is_as_it_was`; MQ4).
> 3. **Holds, but narrower.** Through the instrument the marker's lookup cannot raise, the map being resolved in `__init__`; what reaches it is a read or a set of the marker that the plugin refuses before the write. **Fixed:** `VitalHost.writes_begun` counts the loads and measurements that have begun to change the plugin, raised before the first change each makes. Where an error leaves it as `load_patch` read it, the host's refusal is `PatchRefusedError`, "the plugin was not given the preset", with no rollback and no lost step; once it has moved, a refusal is met by the rollback as before (`test_a_marker_read_the_plugin_refuses_before_any_change_is_a_refused_patch_and_no_rollback`, `test_a_marker_read_the_plugin_refuses_after_the_first_load_s_change_is_rolled_back`, `test_the_count_of_writes_begun_is_raised_by_a_change_and_by_nothing_refused_before_one`; MQ5 to MQ8).
> 4. **Holds.** The first revision had recorded it as its reading: "the instrument cannot tell those two apart". **Fixed** by the same count, and that reading is replaced: an error from outside the package that leaves the count as it was leaves as itself, nothing marked (`test_an_error_from_outside_the_package_before_any_change_leaves_as_itself_and_marks_nothing`; MQ9).
> 5. **Does not hold.** A preset never holds a `null` section for the guard to pass. As a patch, the preset's own validator refuses it first, through `preset_of`: "a section is the text of a JSON array or object". As a file, the reader refuses its key first, by name: `UnknownSettingError('custom_warps')`. **No code changed;** `test_a_null_section_is_refused_before_the_guard_is_reached` holds both.
> 6. **Holds, but narrower.** Only a text given to a bare `VitalHost.load_state` can hold one: the file's reader refuses a setting that is no float. The state's validator refuses none of `true`, `false`, `null`, a string or an array there, asking only for one JSON object. **Fixed**, with no probe: a marker value that is no JSON number is `PluginStateError` naming the key and the value's kind, before anything is set. What Vital itself makes of one was not measured, since such a text is never sent (`test_a_marker_value_that_is_no_number_is_refused_before_anything_is_set`; MQ10).
> 7. **Holds.** **Fixed:** `_section` reads through `decoded()` and refuses as `PatchRefusedError` (`test_a_section_past_the_decoder_s_limit_is_refused_as_a_patch`, at the decoder's own limit, bisected in the test; MQ11).
> 8. **Holds.** **Fixed:** the callback first marks that an alert was answered, storing nothing new, and everything after the mark is guarded. A write so marked is `PluginStateError` whether or not the alert could be noted, and says so where it could not (`test_the_callback_marks_an_alert_it_cannot_note_and_returns_the_first_button`, `test_an_alert_that_could_not_be_noted_is_still_the_package_s_error`; MQ12 to MQ14).
> 9. **Holds;** the callback does no float arithmetic today. **Documented, no code:** the module docstring, a comment at the callback and `vital/plugin-state.md` name it as the one place the package's Python runs under the plugin's floating-point environment, and say why it is not switched: nothing may fail before the alert is noted. No test holds that it stays so.
> 10. **Holds.** **Fixed:** every alert of a write is in the error, in the order answered, with how many where there is more than one; one alert keeps the wording it had. No text was seen to make Vital raise two, so a stand-in alone holds it (`test_every_alert_of_one_write_is_in_the_error_in_the_order_answered`; MQ15).
> 11. **A repeat** of the first review's finding 11. **Stands deferred:** fromtheoutfit/patchbay-vital#27, unverified. Its body already held the suggestion to close the window; it now also holds what this review adds, in its words: the release, where the close would go, and the long run.
> 12. **A repeat** of the first review's finding 15, which did not hold as stated: pedalboard's native module links AppKit, Cocoa, Foundation and libobjc itself (`otool -L`), and the watch then builds in a median of 0.123 ms (the first revision's `costs.txt`). **Stands declined.** The fork-safety point is new and unmeasured; `shape.md` records it for a later issue.
> 13. **A repeat** of the first review's finding 12. **Stands declined:** a decode took a median of 0.60 ms on a median-sized installed preset and 5.19 ms on the largest, 10 MB (the first revision's `costs.txt`).
> 14. **Holds.** **Deferred:** fromtheoutfit/patchbay-vital#28, unverified, with the constraint that on macOS a missing `pthread_main_np` still means the host refuses to load.
> 15. **A repeat, kept on purpose.** `_write` asks again so that a caller that skips the helper still cannot write from another thread, a condition of the first revision. **Stands** (`test_a_state_write_from_a_second_thread_is_refused_by_the_write_itself`; MR8).
> 16. **Holds.** **Deferred:** fromtheoutfit/patchbay-vital#28, unverified.
> 17. **Deliberate.** `vital/preset-tests.md` records it: a module of one suite cannot import from the other's, and test support the two share has no home in the layout. In each module `test_a_child_ended_itself_only_by_all_three_checks` and `test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog` hold the two copies alike. **Declined;** where such support should live is a proposal for the base standards.
> 18. **By design.** "Not killed by the parent" is one of the three checks that standard names. It is true at every real call because a killed child raises `TimeoutExpired` before the function is asked. **Declined.**
> 19. **A design, outside this PR.** A trial load in a child process is already fromtheoutfit/patchbay-vital#25's first candidate, with its measured cost, 2.38 s a load in a fresh child or a second Vital kept up at about 500 to 970 MiB, and its one slip, `random_values` in 1 of 11 fresh children. By run 4 (`probes-4-counts.txt` of the issue #20 spec) a trial child with two loads sees the crashes found but for that slip, and by its verdict cannot see a text Vital loads in part; the block it would end at its time limit (`probes-2-alert.txt`, 2a). #25 now also says a trial child would be the only remedy for the block off macOS, unmeasured.

## Context

- **Visuals:** None.
- **References:** the first PR 26 revision, the issue #20 spec, the host's guards and the test
  doubles. `references.md` says what each gives.
- **Product alignment:** `agent-os/product/` is unchanged. The adapter says what it does on each
  platform, and a claim about Vital is measured.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a. `base/python/errors` is named for findings 3, 6, 8 and 10.

**Feature-specific:**
- `vital/plugin-state` — the watch, the marker and the floating-point environment, each
  rewritten.
- `vital/instrument` — the lost-step state.
- `vital/preset-tests` — the children's helpers findings 17 and 18 are about.
- `vital/preset-file` — the one decoder helper finding 7 is about.
- `vital/parameter-map` — the marker's key and its scale.
- `base/testing/tests` — where each test lives, and the proposal findings 17 and 18 lead to.
- `base/process/verification-gate` — the gate this spec is held to.
- `base/process/standards-retrospective` — the gate's last step.
- `base/process/ownership` — no agent commits, pushes or files without the owner's word.

## What was built

- **`src/patchbay_vital/host.py`.** `_AppKitWatch` is made with the method's own implementation,
  read once by `_appkit_watch` with `method_getImplementation`; `answered` sets its state and
  installs under one `try`. The callback marks before it notes, and is guarded whole;
  `alerted()` on the watch protocol; `_write` asks it and reports every alert (`_alerts_said`).
  `load_state` plants inside its `try`; `_planted` refuses a value that is no number (`_KINDS`);
  `writes_begun` and its three raises. Docstrings for each, and for finding 9.
- **`src/patchbay_vital/instrument.py`.** `load_patch` reads `writes_begun` before its loads and
  asks it in two handlers. Docstrings.
- **`src/patchbay_vital/patch.py`.** `_section` reads through `preset.decoded`.
- **`tests/unit/builders.py`.** `StandInWatch` gains `alerted` and `unnoted_alert`; `nested` and
  `first_depth_the_decoder_refuses`, moved from `test_host.py`.
- **`tests/unit/test_host.py`**, 9 new test functions, 16 cases; **`test_instrument.py`**, 4 new,
  7 cases; **`test_patch.py`**, 2 new. The planted test loses its three rows for a value that is
  no number, which now have a test of their own. 924 tests in all where there were 902: 707
  unit, where there were 685, and 217 integration.
- **`README.md`, `CHANGELOG.md`.** The entry under `[Unreleased]`, "Changed", one line a
  finding; the issue #20 entry under "Fixed" kept true.
- **The retrospective's own change set:** `agent-os/standards/vital/plugin-state.md`,
  `vital/instrument.md`, `vital/preset-file.md` and the `vital:` lines of
  `agent-os/standards/index.yml`.
- **Dated notes** in the issue #20 spec's and the first revision's `shape.md`.
- No gate file changed. No file was added, removed or renamed under `scripts`, `src`, `tests` or
  `agent-os/standards`, so the negative harness was not rerun.

## What the transcripts show

All in `verification/`, each made on a still tree it prints before and after, by blob, on
2026-11-18: Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS 26.6.2.

- **The single rerun, at the owner's word,** in this order: `rollback-count-first.txt`,
  `rollback-count.txt`, `remedy-run.txt`, `mutation.txt`, `marker-count.txt`. The scripts are
  those the first revision's transcripts embed, each written out and checked against the blob
  listed there; the mutation script is that revision's with its mutants adapted and 15 added.
  - `rollback-count.txt`: 77 of 77 on every count: refused as a patch with Vital's own words,
    all 903 floats and every section as the model's double load left them, the model still the
    preset. The refused call took 100.0 to 625.6 ms, a median of 189.6, where the first
    revision's took 93.6 to 615.9, a median of 180.4; no standard or doc cites that timing. No
    child's window, and no window of another new process at 0 of 3,976 polls.
  - `remedy-run.txt`: 335 of 335 returned, none died, none killed; 3, 28, 221, 64 and 19 by
    outcome; 0 disagree with run 4; beside issue #20's remedy run, 0 texts moved. No child's
    window. A window of another process new since the run began showed at 132 of 17,740 polls:
    the owner's own use of the machine during the run, by the poll data loginwindow and the
    wallpaper's agent at 09:54:00 to 09:54:02, then Alfred at 10:05:11 and one application's
    window, 10:05:13 to 10:05:18. The first revision's run has the same line, at 80 polls.
  - `mutation.txt`: the unchanged copy passes, 707 unit tests and the 8 child tests; this
    revision's unit tests on `src` as it was at `c8ed333` fail, 24 of them. 54 mutants, the
    first revision's 39 adapted and MQ1 to MQ15, each caught by every test named for it, none
    surviving. MW4's real alert ran from 10:10:34 to 10:10:55.
  - `marker-count.txt`: the marker read the text's value after 154 of 154 loads under each
    history, no load raising; all 903 floats and every section the same with the check as
    without, 77 of 77.
- **`cited-names.txt`**, after the rerun and before the gate: every name the four `vital`
  standards the script reads cite, three of them edited here. 205 test names, all found
  (83, 73, 14 and 35). Every mutant cited is in a spec's mutation transcript, MQ1 to MQ15 in
  this one's alone; every transcript cited is in a spec's `verification/`. One name is found
  nowhere, `_VOLUME_FLOOR` in `plugin-state.md`, which the standard cites as a constant that
  is gone; the first revision's listing has the same one.
- **`bare-citations.txt`:** no mutant cited without its spec in `plugin-state.md`,
  `instrument.md` or `preset-file.md`, as they were at `c8ed333` or as they are now.
- **`gate-run.txt`:** `scripts/gate.sh`, exit 0, all six steps, 924 passed, none skipped.
- **`tree-since-the-rerun.txt`**, last: the five transcripts of the rerun printed one tree,
  before and after alike. Nine paths differed from it when the listing was made, none code:
  this file, and the eight transcripts copied into `verification/` after the runs. The listing
  itself is the tenth. No standard, source file or test differs: the rerun, the listings and
  the gate all read the code, tests, scripts and standards as they stand.

No figure the docs or the standards state differs from the rerun, so no standard was corrected
after it.

### Runs that are kept beside their replacement

- **`rollback-count-first.txt`** did not stop: it ended with exit 0 and the same 77 of 77 on
  every count (the call 100.2 to 632.8 ms, a median of 186.6). One line differed from the first
  revision's run: "a window of a process new since the run began that is no child of it: at 4
  of 4168 polls". By the poll data it was one window of one process, about 1004 by 754 at layer
  0, for some 0.2 s at 09:46:38, a minute and a half after the run began; the process had gone
  by the time it was looked for, so it is not named. The run began as soon as the owner gave
  the word, before the owner could have read the request to leave the machine alone. It was
  run once more, at once, and kept as `rollback-count.txt`; the first is kept as it ran. The
  remedy run's like line was not answered with a rerun: the owner was using the machine then,
  by arrangement, and the first revision records the same of its own run.
- **Two forms of the wrapper, neither a stop.** `gate-run.txt` names no script of its own to
  embed, and was written by the wrapper's later form, the one the first revision's
  `gate-run.txt` embeds, since the earlier form fails on an empty list. `mutation.txt` and the
  two listings were written by the earlier form. Each transcript embeds the wrapper that wrote
  it.

## Where PR 26's description no longer reads true

The owner writes the description. Each line: what it says, what is so now, and where it is
shown. The first revision's list, in its `shape.md`, still stands but for the counts below.

- "`-[NSAlert runModal]` is replaced by a function that notes the alert's two texts and returns
  the first button at once. The method is put back in a `finally`": a callback that marks the
  alert, notes it, then its texts; the method's own implementation is read once, when the watch
  is made, and that one is put back whatever interrupts the watch (Decision 2).
- "A write in which an alert was answered raises `PluginStateError` with the alert's words":
  with the words of every alert answered, in order; and one that could not be noted is refused
  too (Decisions 8 and 10).
- "A write that left it there raises `PluginStateError`" (the marker): and a text holding under
  the marker's key what is no number is refused before anything is set; the plant is inside the
  `try` that sets the marker back (Decisions 3 and 6).
- "The rollback `load_patch` already had answers the host's new refusals: the patch error is
  raised and the model's own text is loaded again": once the plugin has been given any of the
  text. A refusal before that is a refused patch with no rollback, and an error from outside
  the package then loses no step, by `VitalHost.writes_begun`, which is new (Decision 4).
- "`patch.py`: `check_loadable` also refuses …": still so; it now reads a section through the
  one guarded decoder (Decision 7).
- "Tests: 859, where `main` has 803. 649 are unit tests and 210 are integration tests": 924,
  707 and 217 (`gate-run.txt`).
- "Locally `scripts/gate.sh` exits 0 with 859 passed": 924 passed (`gate-run.txt`). "CI's gate
  passes at `9bc336c`" and "At `9bc336c` it reports 651 passed and 208 skipped": CI has not run
  on this revision.
- "The rollback, counted … The refused call takes 81.6 to 580.3 ms, a median of 171.8": 100.0
  to 625.6 ms, a median of 189.6, every count the same (`rollback-count.txt`).
- "Mutation (`mutation.txt`): 16 mutants": 54, all caught (`mutation.txt`).
- "The evidence and the committed code (`tree-since-the-evidence.txt`)": the four runs are made
  again on this revision's final tree and tied to it by `tree-since-the-rerun.txt`.
- "Filed here: #25", and the upstream list: #28 here, new; #25 and #27 each revised in place on
  2026-11-18; and what the retrospective below sent upstream.
- "The branch is two commits": more, once the owner commits this revision.

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script
under `scripts/` as git lists them, with no tracked file a `.gitignore` ignores;
`uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml`
and `uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set and
`uv.lock`'s pins;
and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the commit in
`agent-os/standards/base/.version` — and the three judgment steps are recorded, in this order:
Docs, Version, then the standards retrospective below.

**Results (2026-11-18):** `scripts/gate.sh` exits 0 on branch
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, all six
steps: three scripts parse; the locked toolchain synced and 35 files formatted; no lint
violation; no type error in 35 source files; 924 passed, none skipped, Vital installed; the
base standards, the `base:` section and the sync script match patchbay-standards at `e31f7db`.
The kept run is `verification/gate-run.txt`, made once, last, after the four evidence runs and
the two citation listings. No gate file changed, and no file was added, removed or renamed under
`scripts`, `src`, `tests` or `agent-os/standards`, so no negative test was rerun.

**Docs (step 7):** read after the change, each against the shipped code:
- `README.md`, "A patch Vital cannot use": the bullet on a load cut off by an error from
  outside the package now says "once the plugin has been given any of the patch", and that an
  error before that leaves the instrument as it was; the paragraph above the list names this
  spec and says it measured nothing new. Its other bullets read true as they were.
- `CHANGELOG.md`: see Version.
- `CLAUDE.md`: names nothing this revision changed.
- `host.py`: the module docstring's paragraph on the floating-point environment (the callback),
  its three bullets on a load and the sentence on `writes_begun`; `_AppKitWatch`,
  `_answered_at_once`, `answered`, `alerted`, `_appkit_watch`, `_planted`, `writes_begun`,
  `_write`, `_set_back`, `_unplanted`, `load_state`, `measure`, `_alerts_said`. One docstring
  was found short and left, the tree being final by then: `_AlertWatch`'s one line says the
  watch "answers the alerts a state write raises, and says where a write may be made", and does
  not say it also says whether one was answered. It is not false; it is listed below for a
  later issue.
- `instrument.py`: the module docstring's paragraph on a lost step, `load_patch` and
  `_lose_step`. `patch.py`: `_section`.
- The test modules' docstrings: `test_host.py`, `test_instrument.py`, `builders.py`.
- Every standard that names what changed: `vital/plugin-state.md`, `vital/instrument.md` and
  `vital/preset-file.md`, rewritten in the retrospective; `vital/preset-tests.md` names nothing
  that changed. `cited-names.txt` holds every name they cite.
- The issue #20 spec's and the first revision's `shape.md` each gained a dated note.

**Version (step 8):** `CHANGELOG.md`, `[Unreleased]`, "Changed": "Revision after the second
review of PR 26", one line a finding. Under "Fixed", the issue #20 entry says "the words of every
alert answered" and that a marker value that is no number is refused. The version stays 0.0.1:
no release is cut.

## Standards Retrospective

Step 9, always last, per `agent-os/standards/base/process/standards-retrospective.md`, written
from the shipped diff and the kept transcripts. These edits are their own change set, apart
from the feature's: `agent-os/standards/vital/plugin-state.md`, `vital/instrument.md`,
`vital/preset-file.md` and the `vital:` section of `agent-os/standards/index.yml`. The `base:`
section is untouched.

- `vital/plugin-state.md`: the watch bullet (the method's own implementation kept from when the
  watch is made, the state and the install under one `try`, the callback's mark and its guard,
  every alert of a write reported, an alert that could not be noted, two alerts held by a
  stand-in alone, the nested entry refused before the `try`, what the watch is built from); the
  marker bullet (a value that is no number refused and Vital's reading of one not measured, the
  plant inside the `try`, `writes_begun` and where it is raised); the bullet on the
  floating-point environment (the callback, which no test holds); the header's evidence.
- `vital/instrument.md`: the lost-step bullet (an error before the plugin is given anything, by
  the host's count; the rollback's own loads as they were); the rollback bullet (once the
  plugin has been given any of the text); the header's evidence.
- `vital/preset-file.md`: the guard's read of a section among those that go through the one
  guarded decoder, with its test and MQ11.
- `agent-os/standards/index.yml`: the `vital:` entries `plugin-state` and `instrument`.

Each verified against the shipped code, tests and transcripts it names, every name cited
searched for over the tree after the rerun (`cited-names.txt`) and every mutant cited with its
spec (`bare-citations.txt`); every figure cited is the rerun's. The owner approved the first two
shown old beside new, and the clause for `preset-file.md` as shown, on 2026-11-18, before they
were written; none was changed after the rerun.

The four questions:
1. **A pattern no standard covered:** a count raised before the first change a call makes, so
   its caller can tell an error that struck before anything was sent from one that struck
   after; a mark stored before anything that can fail, standing for what could not be noted; a
   restore that puts back a value kept from the start, never one taken from a swap's return.
   Each is written in the project standards above. None is proposed for the base: each is one
   instance, about one plugin.
2. **A standard proved stale:** the watch built "from three calls", and its callback said to
   "fix the button it returns"; the marker set back "however the write ends", the plant not
   among the ways; and the lost-step bullet's "told from it only by where it leaves, so one that
   struck inside a load before the plugin was reached loses step too". Corrected above.
3. **A deliberate deviation:** the children's three helpers stay written in two test modules
   (findings 17 and 18 declined). Not a standard change here; where such support should live is
   the base proposal below. And one alert keeps the error's wording it had, the count stated
   only for more than one (Decision 2 of the build): a reading of the owner's condition, not a
   standard's.
4. **Something a standard points at moved:** `_AppKitWatch` is made from four things, the
   method's own implementation among them, and its `install` gives nothing back; the
   decoder-depth helpers moved to `tests/unit/builders.py`, which no standard named. Each
   standard that names one says so now, and `cited-names.txt` finds no test name missing.

Proposals sent upstream: fromtheoutfit/patchbay-standards#40, revised in place

### Standards retrospective (proposed, base)

One proposal, checked against fromtheoutfit/patchbay-standards#40 first, as the owner asked.
Presented to the owner whole on 2026-11-18, after the gate's clean run, and approved, in the
owner's words: "1. Revise #40 in place as shown, nothing else in the body changed, read it back
from GitHub, record it in shape.md. This reverses my 2026-11-12 withdrawal for the shared helper
alone; the shared reader stays withdrawn. Then stop and print git status --short." Written into
#40 the same day and read back from GitHub: the body written, no earlier line changed, no
comment posted. The paragraph says the helper is "put again, on its own"; that the shared reader
stays withdrawn is the owner's, recorded here.

1. `base/testing/tests.md`, "Test files": **where test support that two suites share lives,
   when it is a function and no recorded value.** It states the question and the evidence and
   proposes a home; no file is moved here. Verified against `tests/unit/test_host.py` and
   `tests/integration/test_vital_instrument.py` (`_armed`, `_ended_itself`, `_child_failed`,
   `test_a_child_ended_itself_only_by_all_three_checks` and
   `test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog` in each),
   `tests/unit/builders.py` (its docstring) and `agent-os/standards/vital/preset-tests.md` (its
   last bullet). Proposed, not applied; filed as fromtheoutfit/patchbay-standards#40, revised in
   place.

**Its home is #40, revised in place, and not a new issue.** #40's proposal 1 already named the
mechanism and the reason: "a helper that tests in two directories share lives beside the shared
reader in `tests/conftest.py`. It is handed to tests as a fixture and never imported from the
conftest", `tests/` being no package and the standard allowing one `conftest.py` at most. The
owner withdrew proposal 1 on 2026-11-12, "the shared helper with it", when its instance went,
and said it "may be filed again when a package holds recorded values two test directories
share". This is the helper half put again on its own: a function, with no recorded file. A new
issue would state the same mechanism a second time beside the first. The first revision recorded
the same question as "a candidate for the standards batch" and judged that #40 "does not cover a
shared function"; that is so of #40's text as withdrawn, which is why the paragraph below puts
it as a question and not as a rule already practised.

The paragraph for #40, placed after its last "Revised" paragraph and before the rule texts:

> Revised 2026-11-18 (after the second review of patchbay-vital's PR 26, https://github.com/fromtheoutfit/patchbay-vital/pull/26#issuecomment-6965953694, findings 17 and 18, and its revision, `agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/`): proposal 1's shared helper is put again, on its own, as a question with its evidence and a proposed home, approved by the owner on 2026-11-18. No file was moved in patchbay-vital for it. The evidence is in that spec folder on patchbay-vital's branch `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, pull request fromtheoutfit/patchbay-vital#26, uncommitted when this was revised; the owner's push puts it there.
>
> - **The question.** Where does test support that two suites share live, when it is a function and no recorded value? `tests/` is no package, so a module of `tests/integration/` cannot import a plain module of `tests/unit/`, and the standard allows one `conftest.py` at most.
> - **The evidence.** patchbay-vital's two modules that start child processes each hold the same three functions, `_armed`, `_ended_itself` and `_child_failed`, by the same names, with the same checks and the same failure message, each docstring naming the other module. In each module one test holds its copy to the three checks (`test_a_child_ended_itself_only_by_all_three_checks`) and another holds that a child no parent kills ends itself (`test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog`). The copies were written in the revision after the first review of PR 26, and the second review listed them as its findings 17 and 18: "A fix to the watchdog-header detection in one copy and not the other would leave one suite's hang detection silently wrong." patchbay-vital's `vital/preset-tests.md` records the copy as deliberate: "a module of one suite cannot import from the other's, and test support shared between them has no home in the layout".
> - **The home proposed.** The one `conftest.py` the standard allows, at `tests/`, the directory that holds every test taking it, hands the function to tests as a fixture; it is never imported from the conftest. That is the form proposal 1 gave a shared helper on 2026-11-11, beside a shared reader. Here it is asked for a helper alone, with no recorded file.
> - **What it costs, for the rule to say.** A new file under `tests/` changes the list of files the gate reads. In patchbay-vital each spec gives "no file is added, removed or renamed under `scripts`, `src`, `tests` or `agent-os/standards`" as its reason for not running the negative harness again, so the spec that moves the helpers owes that rerun. And a helper that a Hypothesis property takes at its decorator or under `@given` cannot be a function-scoped fixture, so a plain module beside the tests stays for those, as patchbay-vital's `tests/unit/builders.py` is, whose docstring says so.
> - **Verified against** patchbay-vital's `tests/unit/test_host.py` and `tests/integration/test_vital_instrument.py` (`_armed`, `_ended_itself`, `_child_failed`, and the two tests named above in each), `tests/unit/builders.py` (its docstring) and `agent-os/standards/vital/preset-tests.md` (its last bullet).
