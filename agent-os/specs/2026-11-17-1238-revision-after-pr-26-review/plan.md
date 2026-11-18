# Revision after the review of PR 26 (issue #20) — plan

## Context

PR 26 (fromtheoutfit/patchbay-vital#26, issue #20's remedy, branch
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, head
`9bc336c`) has one review comment by the owner: issue comment 6954622361, "Review findings",
2026-11-17 16:47 UTC. It lists 17 findings and says "None was checked a second time, so treat
each as likely rather than confirmed". Shaping checked each one against the code at `9bc336c`.
The owner then decided each with conditions, given verbatim in Appendix A, which is the source
for `shape.md`. This revision fixes what the owner chose and declines or defers the rest with
their figures. It drafts two issues and a reply for the owner, and reruns the issue #20
evidence once, on the final tree.

No agent commits, pushes, opens a PR or posts the reply. No gate file changes. No file is added,
removed or renamed under `scripts`, `src`, `tests` or `agent-os/standards`, so the negative
harness is not rerun. The spec folder is
`agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`.

## What shaping checked

Shaping reads were made in memory with nothing written to the tree. None of them is evidence for
a doc: a figure is quoted only from a kept transcript.

| # | Verdict | Decision |
|---|---|---|
| 1 | Real, narrower: `_reached` already turns pedalboard's RuntimeError/ValueError/TypeError into PluginStateError; what skips `_unplanted` is anything else (KeyboardInterrupt, MemoryError, the watch's own errors) | Fix in host and instrument |
| 2 | Real for a bare `VitalHost`; the instrument resolves the map in `__init__` | Fix |
| 3 | Real against core's docstring; the issue #20 spec chose it (Decision 14) | `load_patch` raises PatchRefusedError chained from PluginThreadError; a new core issue is drafted |
| 4 | Real: `measure()` ends on an unchecked write; probes-3 shows a good load from a second thread leaves parameters reading stale | Fix |
| 5 | Reachable only through 4 | No lock; the watch refuses to be entered twice |
| 6 | Real for an embedded interpreter, reasoned, not measured | `pthread_main_np` |
| 7 | Real: a raising ctypes callback returned 0, not 1000 (in memory, no Vital) | Fix |
| 8 | Real: a Python watcher can't run while pedalboard holds the GIL | Children arm SIGALRM's default action, after a probe |
| 9 | Real | File lock, 3 s limit, two failures named apart |
| 10 | Unmeasured: no transcript shows Vital with a switch between its ends | Probe, then decide |
| 11 | Real, already a recorded limit | Deferred-items issue |
| 12 | Real but small: `_floats` is not on the load path; decode 0.6 ms median, 5.1 ms on the 10 MB preset | Declined on the cost transcript |
| 13 | Does not hold as stated: the decoder's limit is 9997 called directly and 9994 through the validator, which runs first (Python 3.12.16; 9998 under 800 more frames) | Guarded anyway (one decoder helper), tested directly |
| 14 | Real | Fix |
| 15 | Does not hold as stated: pedalboard's native module links AppKit and libobjc (`otool -L`); the watch built in 0.14 ms | Declined on the cost transcript |
| 16 | Real | Fix, in the retrospective (project standard) |
| 17 | Real | Fix |

Facts shaping found that the owner asked to have recorded:
- `set` and `render` check no thread. The kept probes made loads from a second thread and
  rendered on the main thread. Neither `set` nor `render` from a second thread was measured.
- What Vital does when `runModal` returns 0 was not measured. The in-memory run used no Vital.
- `_write` is the package's only writer of the plugin's state. `load_state` calls it twice
  (`host.py:640`, `:649`) and `measure` once (`:733`).

## Task 1: Save spec documentation

Create `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/` with:
- **plan.md**: this plan.
- **shape.md**: the scope, what shaping checked (above), and the owner's answers verbatim
  (Appendix A). Its Decisions follow below, each citing its finding. It records these
  reversals and replacements with their reasons:
  - Decision 14 of the issue #20 spec reversed by finding 3, Decision 14 itself left unedited;
  - the owner's wording "the patch itself was not judged" replaced: the guard runs first;
  - the owner's first test condition for 13 replaced: the validator refuses first, by 3 levels.

  It also holds the note for fromtheoutfit/patchbay#25, a second way an instrument loses step
  (a foreign error mid-load), recorded and not filed.
- **standards.md**: the full text of the core tier (`base/python/toolchain`, `layout`,
  `typing`, `models`, `errors`) and of `vital/plugin-state`, `vital/instrument`,
  `vital/preset-tests`, `vital/preset-file`, `vital/parameter-map`, `base/testing/tests`,
  `base/process/verification-gate`, `base/process/standards-retrospective` and
  `base/process/ownership`. `base/python/errors` is named for findings 1, 3 and 14.
- **references.md**: the issue #20 spec (Decisions 13–20; the probe, child-runner and
  window-polling scripts embedded in its transcripts); the PR 23 second-review revision
  (`2026-11-16-1509-…`), for a review revision's form; `host.py`'s `_reached` and
  `_environment_kept` and `preset.decode_end`; `builders.StandInWatch`, `test_host.py`'s
  `_FakePlugin` and `fake`, `test_instrument.py`'s `_FakeVital` and `_lose_step`, and
  `test_vital_instrument.py`'s `_in_a_child` and `_NEVER_RETURNS`.
- No visuals. `agent-os/product/` is unchanged.

Every transcript below is written outside the tree, copied in afterwards, and made on a still
tree with its tree (by blob) and machine printed before and after. A first try that stops is
kept as `<name>-first.txt` beside its replacement.

## Task 2: The midpoint probe (finding 10). Runs without a further word.

`verification/midpoint-probe.txt`. Each case runs in a child under a time limit, with window
polling reused from the issue #20 scripts. If a window appears: kill the child, report it, stop.
- Values of `filter_1_on` on the start preset: 0, 0.25, 0.49, the float32 below 0.5, 0.5, the
  float32 above 0.5, 0.51, 0.75, 0.99 and 1. Wherever the held value or a verdict changes between
  two neighbouring values, bisect over the float32s between them down to two adjacent float32s,
  so the boundary is located, not bracketed.
- Each value under each plant (0.0 and 1.0), after the first and the second load: the value
  held by the parameter read and by the state's text, and the marker's verdict beside the right
  one (taken).
- Through `VitalInstrument.load_patch` with a whole-preset patch: the model's float, what `get`
  returns, and any refusal.
- **Every verdict right:** the rule stands. The planting test takes its expected values from the
  scale's two ends and the transcript's boundary, never from `_planted`.
- **Any verdict wrong:** stop, show the transcript and propose a rule change with its cost.
  Write nothing until the owner answers.

## Task 3: The alarm probe (finding 8). Started only at the owner's word.

`verification/alarm-probe.txt`. Two children, each unwatched and with a 3 s `signal.alarm` and
SIGALRM's default action: AppKit's own alert (the `_REAL_ALERT` construction, no watch), then
Vital's (a text that raises the alert, the watch replaced by `_NoWatch`). Before each window
opens, and when it has gone, say so with the clock time. The parent never kills a child, and each
exit is reported as the signal it died of. If a window is still up 5 s after its alarm was due:
kill the child, report that the alarm did not end it, and stop.

## Task 4: The cost transcript (findings 12, 13, 15)

`verification/costs.txt`, no Vital loaded:
- the decode time on the median and the largest installed preset;
- the time to build `_alert_watch()` after `import pedalboard`, and the `otool -L` lines of
  `pedalboard_native` that name AppKit, Cocoa, Foundation and libobjc;
- the decoder's first refused depth, called directly, through `PluginState.with_text`, and
  directly under 800 more Python frames, all three on one text shape, with the Python version.

Figures are quoted from this transcript, not from the shaping reads.

## Task 5: `host.py`, threads (findings 4, 5, 6)

- `_AlertWatch` replaces `main_thread_only` with `may_write_here() -> bool`. `_NoWatch` answers
  True. `_AppKitWatch` asks `pthread_main_np()`, reached through `ctypes` with `restype` c_int
  and empty `argtypes`. `builders.StandInWatch` follows its `main_thread_only` flag.
- `_AppKitWatch` is built from three callables: one installs an implementation and returns the
  previous one, one reads an alert's two texts, one asks for the main thread. `_alert_watch()`
  builds them from the runtime and the C library, and returns None when the runtime, AppKit,
  `runModal` or `pthread_main_np` is missing. The host then refuses to load, its reason naming
  `pthread_main_np` alongside the runtime and AppKit. So the real class is tested on every
  platform.
- One helper, `VitalHost._on_a_writing_thread()`, raises `PluginThreadError` with the thread's
  name. It runs first in `load_state` and in `measure`, before any plugin call, so a refused
  measure sets nothing. `_write` calls it too, so a later caller that forgets it still cannot
  write from another thread.
- `_AppKitWatch.answered()` refuses to be entered while it is already in place:
  `PluginStateError` whose reason names the watch already in place, raised before anything is
  installed. Its docstring says why finding 5 is otherwise settled: every write on macOS is the
  main thread's, and the callback never writes.
- Tests in `tests/unit/test_host.py`, on every platform unless marked:
  - `measure` from a second thread is refused, with no plugin call and no parameter set;
  - `_write` called from a second thread is refused, with no plugin call;
  - the existing `load_state` thread test is kept;
  - the real watch, built from stand-ins: a nested entry is refused by name, `install` is called
    once, the original is put back, and `may_write_here` follows the stand-in;
  - on macOS only, `pthread_main_np` answers true on the main thread and false on another, with
    no plugin, skipping by name elsewhere;
  - `_alert_watch()` gives None where `pthread_main_np` is not found.

## Task 6: `host.py`, an alert's words (findings 7, 14)

- The callback first records that an alert was answered, with a return value that is the first
  button whatever follows. Only then does it read the texts, catching anything they raise and
  keeping it in the record (`_Answered(message, informative, unread)`). The suppression comment
  names BLE001 and the reason in one line.
- After the write, an alert whose texts could not be read is still `PluginStateError`, saying an
  alert was answered and its words could not be read, chained from what the read raised.
- When pedalboard raises during a write that alerted, `_write` raises one `PluginStateError`
  carrying the alert's words and pedalboard's, chained from pedalboard's own error. The marker is
  still set back on that path.
- Tests: the real watch's callback called directly through its CFUNCTYPE object, on every
  platform, with a stand-in alert whose text read raises. The alert is recorded, 1000 comes back,
  nothing leaves the callback, and `_write` raises as above. On the fake plugin, an alert plus a
  pedalboard refusal gives both texts in one error, with `__cause__` RuntimeError. The macOS
  real-alert child test stays as well.

## Task 7: `host.py`, the marker (findings 1, 2) and the guarded settings helper (finding 13)

- `load_state`: on every way out of `_write` (`except BaseException`), `_unplanted` runs and the
  original error is re-raised as itself, the same object. If `_unplanted` raises, the original
  still leaves, with the second attached by `add_note` naming its type and message, and the second
  error does not replace it.
- `_marker()`: `_marker_sought` is set only after a lookup that succeeded or a
  `MapMismatchError`. Any other error leaves, and the next load looks again.
- One guarded helper, `_settings(text)`, is used by `_planted` and `_floats`. It decodes through
  the package's guarded decoder and refuses nesting too deep as `PluginStateError`. Its docstring
  says, in one sentence, why it is guarded though the validator runs first today: the standard's
  one decoder helper, and the margin between the two limits is measured, not promised.
  `decode_end` and a value-returning form share one guarded function in `preset.py`.
- Tests in `test_host.py`:
  - KeyboardInterrupt and MemoryError raised in the write: the same object leaves, and the
    marker is set back;
  - `_unplanted` failing: the original leaves with a note naming the second;
  - the first lookup failing on a refused `version`: that load raises, and the next looks again
    and plants;
  - `MapMismatchError` settles the lookup (the existing test, extended);
  - the helper given a text one level past the decoder's limit, bisected in the test from
    `DECODER` itself: `PluginStateError`;
  - a `load_state` test of the order only: the validator refuses first, with nothing planted and
    no plugin call. It does not claim to exercise the helper.

## Task 8: `instrument.py`, a foreign error (finding 1) and the thread (finding 3)

- `_send` is split, so the text is made before the try and only the loads are inside it.
  `load_patch` then:
  - on PluginThreadError raises PatchRefusedError chained from it. The message says, in this
    order: the call came from a thread the plugin cannot be loaded from on macOS, naming it; the
    patch passed the package's own checks; it was not given to Vital, so whether Vital takes it
    is unknown. No rollback, not out of step, no event;
  - on PluginStateError rolls back as now;
  - on any other VitalError re-raises, marking nothing;
  - on any other BaseException from inside the loads marks the instrument out of step (`_lost`
    naming the error's type), attempts no rollback, and re-raises the same object. A foreign
    error during the rollback also marks it out of step and is re-raised as itself.
- Errors raised before the plugin is called (`preset_of`, `check_loadable`, PluginThreadError,
  MapMismatchError) mark nothing. `VitalHost.load_state` and `VitalInstrument.__init__` keep
  raising PluginThreadError. The docstrings say all of this.
- Tests in `test_instrument.py`, on `_FakeVital` through the real host:
  - KeyboardInterrupt and MemoryError × {in the first write; when the second load first reaches
    the plugin, after the first returned; in the second write}. Each case checks that the raised
    object is the one that leaves, the marker is not left planted, the instrument is out of step,
    `set`, `load_patch` and `render` are refused, `get` and `patch` answer from the model, and
    nothing is published;
  - `test_a_load_from_another_thread_is_no_state_error`, kept, now expects PatchRefusedError,
    the cause's type and the message's three statements;
  - a new test: a patch the guard refuses from a second thread is refused for the guard's reason,
    and the thread is never asked.

## Task 9: The tests' children (findings 8, 9)

- Every child the tests start arms `signal.alarm` with SIGALRM's default action, as its first
  statements, before importing anything that could block: `_ALERTING` and `_IGNORED` (through
  `_in_a_child`), `_REAL_ALERT` and `_NEVER_RETURNS`. The limits are named constants past the
  parents' (`_CHILD_ALARM_SECONDS` > `_CHILD_SECONDS`; `_REAL_ALERT_ALARM_SECONDS` >
  `_REAL_ALERT_SECONDS`), and a test asserts each is the greater.
- A new CI test: a stand-in child its parent never kills ends at its alarm, and the test asserts
  that it died of SIGALRM, not merely that it ended.
- Finding 9: the stand-in takes an `fcntl.flock` on a file the test made and then writes
  "started". The test checks the lock, never a pid. "The child never started" and "it did not
  end" are two failures, each by name. The limit goes from 1 s to 3 s.
- On a platform without `signal.alarm` or `fcntl` (Windows), those tests skip by name, and the
  docs say what such a platform gets.

## Task 10: Docs (finding 17) and Version

- `README.md`, `CHANGELOG.md` and the docstrings: each claim that rests on a transcript names what
  it was measured on (Vital 1.6.4, pedalboard 0.9.26, arm64, macOS 26.6.2) once per section, and
  says of other platforms only that nothing was probed there. `load_patch`'s "on any platform"
  goes. The three are searched for "any platform", "every platform" and "always", and each hit
  is listed in `shape.md` with what it became or why it stayed.
- The docstrings of `host.py` and `instrument.py` are rewritten for Tasks 5–8, and for finding
  10's outcome if it changes anything.
- `CHANGELOG.md` `[Unreleased]` gains "Revision after the review of PR 26", saying what each
  finding came to. The version stays 0.0.1.

## Task 11: Drafts, each shown whole

None carries attribution, and each is filed only at the owner's word:
- **Deferred-items issue** (fromtheoutfit/patchbay-vital): finding 11 in the reviewer's own
  words, marked unverified, citing the soak's 500 window objects and 603 to 701 MiB and
  `plugin-state.md`'s limit. If the README, the CHANGELOG, a docstring or a standard will name
  it by number, ask to file it before Task 13, so the final runs cover the number. Otherwise it
  is filed after the gate's clean run.
- **Core issue** (fromtheoutfit/patchbay): one question: should core name an error for a call
  made from a thread the instrument cannot serve, and for which methods? It cites the 11 of 11,
  AppKit's refusal and the stale reads, and what the adapter does meanwhile. patchbay#25 is not
  touched. The same timing rule applies if a file names it.
- **Reply to the review**: one line per finding, 1 to 17 in order. Each says whether the
  finding is real, real but narrower, or does not hold, then whether it was fixed, declined or
  deferred, with its file, test or transcript. Where the check disagreed with the reviewer, the
  line says what was measured. No finding is merged with another.
- **In `shape.md`**: every count, limit and Decision in PR 26's description that this revision
  makes untrue, each with its new value and source. The owner writes the description.

## Task 12: Retrospective edits, from the shipped code, shown old beside new before writing

- `vital/plugin-state.md`: the watch bullet (7, 14, 5), the main-thread bullet (4, 6; the
  embedded case reasoned from `pthread_main_np`'s meaning, not measured), the marker bullet
  (1, 2, 10), and the window limit citing the deferred-items issue.
- `vital/instrument.md`: the lost-step bullet (1), the thread bullet (3), and line 181
  (finding 16). That line's two splits of the 64 are written as two sentences, each adding to
  64, with "51 of the 64 are not held as given" stated outright and every figure checked against
  `silent-and-loaded.txt`. `plugin-state.md` and patchbay-vital#25 are checked for the same
  figures. If #25 needs it, its body is revised in place with a "Revised 2026-11-17" paragraph,
  shown first, then read back.
- `vital/preset-tests.md`: the last bullet, with the alarm and both limits.
- `index.yml`: this repository's `vital:` entries, kept in step. The `base:` section is not
  touched.
- Base proposals go only in `shape.md`, under "Standards retrospective (proposed, base)".

These edits are written before Task 13 so that the final runs are on the final tree. The
retrospective's judgment is recorded last, in Task 14.

## Task 13: One rerun on the final tree. Asked for once.

Ask the owner once, saying how many windows will show and for how long. One mutant of the issue
#20 run leaves a real alert open by design, in a child its test kills. Then, on one still tree:
- `remedy-run.txt` (the 335 texts), `rollback-count.txt` and `marker-count.txt`, from the
  scripts their issue #20 transcripts embed;
- `mutation.txt`: issue #20's 16 mutants, each adaptation to moved code listed, plus one mutant
  per new guard of this revision. Each fails the test named for it, and none survives;
- `gate-run.txt`: `scripts/gate.sh` with the date and branch.

If any figure differs from what the docs or the Task 12 edits state, stop and present. The
issue #20 spec's transcripts stay as they ran, and its `shape.md` gains a dated note naming these
reruns. `shape.md` lists the paths that differ between the runs' tree and the committed tree:
none that a run reads.

## Task 14 (FINAL): Verification gate

1–6. `scripts/gate.sh`: `bash -n` over the scripts git lists under `scripts/`; `uv sync --locked`
   and `ruff format --check`; `ruff check`; `mypy`; `pytest -c pyproject.toml -p no:doctest`;
   `scripts/sync-standards.sh --check`. It exits 1 at the first failing step, by name. The kept
   run is Task 13's `gate-run.txt`. If a step fails, fix the cause, never bypass it, and rerun.
7. **Docs**: README, CLAUDE.md, the docstrings and every standard naming what changed read true.
   The search hits are listed. Recorded in `shape.md`.
8. **Version**: the `[Unreleased]` entry. 0.0.1 kept.
9. **Standards retrospective**, last: the four questions asked of the shipped diff, the project
   edits listed as their own change set, and `Proposals sent upstream:` recorded. Each base
   proposal goes to the owner by AskUserQuestion, multi-select, at most three to a question, each
   with a "None of these" option. The approved ones are filed as one issue on
   fromtheoutfit/patchbay-standards after the gate's clean run, with no attribution, and the
   declined ones marked by name.

Then file whatever the owner approved, read each one back, stop, and print `git status --short`.
Nothing is committed or pushed.

## Appendix A: the owner's answers in shaping, verbatim (2026-11-17)

**1 and 2 (marker)**, to "Host and instrument": "1. Conditions:
- Host: _unplanted runs on every way out of a write and the original error is re-raised as itself, the same object, not wrapped. If _unplanted itself fails on the way out, the original error still leaves, with the second one attached to it and not in its place.
- Instrument: only an error that leaves from inside the send to the plugin marks it out of step. One raised before the plugin is called (the guard, validation, PluginThreadError, MapMismatchError) changes nothing and marks nothing, as today. The catch covers BaseException, since KeyboardInterrupt is not an Exception; no rollback is attempted for these, and the error is re-raised as itself.
- Tests on a stand-in plugin, no Vital: KeyboardInterrupt and MemoryError raised in the first load, between the two loads, and in the second; each asserts the marker is not left planted, the instrument is out of step, set/load_patch/render are refused and get/patch answer from the model, and the error that leaves is the one raised.
- _marker_sought: a test where the first lookup fails with another error, and the next load looks again and is checked; and one where MapMismatchError settles it.
- Each new guard is held by a mutant in this revision's mutation.txt.
- instrument.md's lost-step bullet and plugin-state.md's marker bullet are rewritten from the shipped code after it is written, shown to me old beside new.
- Note it for fromtheoutfit/patchbay#25 in shape.md: a second way an instrument loses step (a foreign error mid-load), as evidence for that question; nothing is filed on core.
- Evidence: this changes code in host.py and instrument.py, so by the rule sent to standards #38 the four evidence runs are owed again on the final tree. Do not rerun now. Fix every finding of this review first, then ask me once for one rerun at the end."

(Read in this plan: "the second one attached to it" is `add_note` on the original error, naming
the second error's type and message, the standard way to attach to an error in flight. "Inside
the send" is from the first `load_state` on, so a foreign error that strikes inside
`load_state` before it reaches the plugin also marks the instrument out of step: the instrument
cannot tell those two apart.)

**3 (contract)**, to "Patch error, tell core": "1, with the core question as a new drafted issue and not a paragraph on patchbay#25. Conditions:
- load_patch raises PatchRefusedError chained from PluginThreadError. Its message says first that the call came from a thread the plugin cannot be loaded from, and that the patch itself was not judged; a test asserts the cause's type and that wording.
- Nothing changed, no rollback, not out of step, no event: the existing test of that is kept and now expects the patch error.
- VitalHost.load_state and VitalInstrument.__init__ keep PluginThreadError.
- Say what set and render do from a second thread on macOS today, from the code and from any probe already kept; if nothing was measured, say so. Run no new probe for it here.
- Decision 14 is not edited: this revision's shape.md records the reversal, the review finding and the reason.
- instrument.md's thread bullet is rewritten from the shipped code, shown old beside new.
- Draft a new issue for fromtheoutfit/patchbay, one question: should core name an error for a call made from a thread the instrument cannot serve, and for which methods. It cites this package's evidence (the 11 of 11, AppKit's refusal, the stale reads) and what the adapter does meanwhile. It speaks for me, so show it whole and file only at my word. patchbay#25 is not touched.
- This is one of the review's fixes; the single evidence rerun still comes once, at the end."

**3 (message)**, to "Say what was checked": "1. Conditions:
- The message says, in this order: the call came from a thread the plugin cannot be loaded from on macOS, naming the thread; the patch passed the package's own checks; it was not given to Vital, so whether Vital takes it is unknown.
- The test asserts those three statements are in the message and that the cause is PluginThreadError.
- A patch the guard refuses is still refused for the guard's reason from any thread, the thread never being asked; a test holds that order.
- shape.md records that my earlier wording ("the patch itself was not judged") was replaced and why."

**4–6 (threads)**, to "One OS-level check": "1. Conditions:
- The helper runs first in load_state and in measure, before the plugin is touched at all; measure sets parameters before its write, so a refusal there must leave them unset.
- List every caller of the state write in the package and show each goes through the helper. The write itself also refuses when the check fails, so a later caller that forgets the helper cannot write from another thread; a test holds it.
- No lock. But the watch refuses to be installed while it is already installed, raising by name, so a nested entry can never save the replacement as the original. A unit test on the stand-in holds that; say so in the watch's docstring with the reason finding 5 is otherwise settled.
- pthread_main_np is reached through ctypes with its return type declared, standard library only. If it cannot be found on macOS, the host refuses to load, as it does when AppKit cannot be reached.
- Tests: on the stand-in, on every platform, that load_state and measure from a second thread are refused before the plugin is called and change nothing. On macOS, one test that the real check answers true on the main thread and false on another, with no plugin.
- The embedded-interpreter case is not probed here; plugin-state.md says what the check is and that this case was reasoned from pthread_main_np's meaning, not measured.
- plugin-state.md's main-thread bullet is rewritten from the shipped code, old beside new.
- Each new guard has a mutant. The single evidence rerun still comes once, at the end."

(Read in this plan: "a unit test on the stand-in" is the real `_AppKitWatch` built from stand-in
runtime calls, so it is the shipped refusal that the test holds; `StandInWatch` mirrors it.
"Raising by name" is read as `PluginStateError` whose reason names the watch already in place,
not a new error class.)

**7 and 14 (alert words)**, to "Fix both": "1. Conditions:
- The callback does two things before anything that can fail: records that an alert was answered, and fixes its return value to the first button. Reading the texts comes after, and anything it raises is caught and kept, not dropped.
- After the write returns, an alert whose texts could not be read is still a PluginStateError, saying an alert was answered and its words could not be read, chained from what the read raised.
- The callback's logic is tested on every platform by calling it directly with a stand-in alert whose text read raises: the alert is recorded, the first button is returned, nothing leaves the callback. The macOS test against a real alert is in addition, in a child with its time limit.
- Finding 14: one PluginStateError carrying the alert's words and pedalboard's, chained from pedalboard's error; the test on the fake plugin asserts both texts are in it and the cause's type. The marker is still unplanted on that path.
- Say what Vital does when the method returns 0 and not the first button, if the in-memory run showed it; if not, say it was not measured. Run no probe against Vital for it.
- The suppression comment names the rule suppressed and the reason in one line; no gate file changes.
- Each new guard has a mutant. plugin-state.md's watch bullet is rewritten from the shipped code, old beside new. The single evidence rerun still comes once, at the end."

**8 and 9 (children)**, to "Children end themselves": "1. Conditions:
- The probe: start it at my word. Say just before each of the two windows opens and when it has gone, with clock times; I will not click them. Each child's exit is reported as the signal it died of, and the parent does not kill either one: if a window is still up 5 s after its alarm was due, kill it, report that the alarm did not end it, and stop.
- The transcript is kept, prints its tree and machine, and a first try that stops is kept beside its replacement.
- Every child the tests start arms the alarm before it imports anything that could block: the two integration children and the unit test's real-alert child. The alarm's limit is a named constant past the parent's, and a test asserts the one is greater than the other.
- signal.alarm is not on every platform: say what a platform without it gets, and those tests skip there by name.
- The CI test: a stand-in child its parent never kills ends at its alarm, and the test asserts it died of SIGALRM, not that it merely ended.
- Finding 9: the lock is the standard library's, the test checks the lock and never a pid, and "the child never started" is a failure by name, distinct from "it did not end".
- preset-tests.md's last bullet is rewritten from the shipped tests, old beside new, with the alarm and both limits.
- Each new guard has a mutant. The single evidence rerun still comes once, at the end."

**10 (midpoint)**, to "Probe, then decide": "1. Start it; no window is expected, so it needs no word from me beyond this. Conditions:
- Add the float32 values either side of 0.5 to the list, so the boundary is located and not bracketed.
- For each value, under each end the marker would be planted at: what the plugin holds after the first load and after the second, by the parameter read and by the state's text, and the marker's verdict beside what the right verdict is.
- Also record what the model holds and what get returns for that parameter after such a load, since the model keeps the text's float.
- Kept transcript on a still tree, tree and machine printed; if a window does appear, kill the child, report it and stop.
- If every verdict is right: the test that pins the rule takes its expected values from the scale's two ends and the transcript's boundary, not from the method under test.
- If any verdict is wrong: stop, show the transcript, and propose the rule change with what it would cost; write nothing until I answer."

(Plan mode allows no run that writes, and the transcript belongs in the spec's `verification/`,
so the probe is Task 2, the first task after the spec is saved.)

**11, 12, 13, 15 (costs)**, to "13 fixed, rest per evidence": "1. Conditions:
- 13: the test's nested text is built from the decoder's own depth limit, not a guessed number, and asserts PluginStateError with the marker not planted and the plugin not called. The helper has a mutant.
- 12 and 15: the cost transcript is kept, on a still tree with its machine printed, and shape.md records each as declined with its figures and the reviewer's words. For 15, record the otool listing's relevant lines too.
- 11: goes to the deferred-items issue in the reviewer's own words, marked unverified, with the soak's existing figures (500 window objects, 603 to 701 MiB) and plugin-state.md's limit cited. Nothing is probed for it here.
- The single evidence rerun still comes once, at the end."

**13, after the depth limits were found**, to "Guard it, test directly": "1. Conditions:
- The direct test bisects the limit from the decoder in the test itself, as proposed, so it holds on another Python; its expected error is the package's, and the helper's mutant fails there.
- The load_state test holds the order only: the validator refuses first, the marker is not planted, the plugin is not called. It does not claim to exercise the helper.
- The helper's docstring says in one sentence why it is guarded though the validator runs first today: the standard's one decoder helper, and that the margin between the two limits is measured, not promised.
- shape.md and the reply record 13 as "does not hold as stated", with the three limits (9997, 9994, 9998 under 800 frames), the Python version, and the kept cost transcript. My earlier test condition is recorded as replaced, and why."

**Setup**, to "As listed": "1. One addition: base/python/errors, for findings 1, 3 and 14 (what is re-raised as itself, what is wrapped and chained, and how two causes are carried in one error)."

**16 and 17 (docs)**, to "Fix both": "1. Conditions:
- 17: every claim in the README, the CHANGELOG and the docstrings that rests on a transcript names what it was measured on (Vital 1.6.4, pedalboard 0.9.26, arm64, macOS 26.6.2) once per section, and says of other platforms only that nothing was probed there. Search all three for "any platform", "every platform" and "always", and list each hit with what it became or why it stayed.
- 16: the two splits as two sentences or two lists, each adding to 64, with "51 of the 64 are not held as given" stated outright. plugin-state.md and patchbay-vital#25 carry the same figures: check them, and if #25's body needs the same clarity, revise it in place with a "Revised 2026-11-17" paragraph and read it back.
- Show me both old beside new before writing.
- The docstring edit changes no code; it is covered by the single evidence rerun at the end in any case."

**Drafts**, choosing the deferred-items issue and the reply: "1 and 2. Not 3; in its place, a short list in shape.md of every count, limit and Decision in the PR's description that this revision makes untrue, each with its new value and source. I write the description myself.
- The deferred-items issue: the reviewer's own words, marked unverified. If the README, the CHANGELOG, a docstring or a standard will name it by number, ask me to file it before the gate, as patchbay-vital#25 was, so the gate's run covers the number; otherwise after.
- The reply: one line per finding, 1 to 17, in order: real, real but narrower, or does not hold; then fixed, declined or deferred, with the file, test or transcript. No finding is merged with another, and where the check disagreed with the reviewer the reply says what was measured.
- The new fromtheoutfit/patchbay issue stays as already agreed: one question, shown whole, filed at my word."
