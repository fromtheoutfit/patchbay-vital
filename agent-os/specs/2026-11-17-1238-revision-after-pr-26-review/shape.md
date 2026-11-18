# Revision after the review of PR 26 (issue #20) — Shaping Notes

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The review on PR 26 (fromtheoutfit/patchbay-vital#26, "Keep a preset Vital cannot read from
blocking the calling process on macOS", closes #20): issue comment 6954622361, "Review findings",
by the owner, 2026-11-17 16:47 UTC. It covers `main...HEAD` (`8f32777` and `9bc336c`) and lists 17
findings, 5 serious, 4 fragile and 8 smaller, adding "None was checked a second time, so treat
each as likely rather than confirmed". Each was checked against the code at `9bc336c` while
shaping, and decided by the owner with conditions ("Shaping answers" below). The branch is the
PR's, `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`. No
agent commits, pushes, opens a pull request or posts to the PR.

| # | Finding, as the review gives it | Where |
|---|---|---|
| 1 | The marker is undone only on `PluginStateError` | `host.py:650` |
| 2 | `_marker()` sets `_marker_sought` before the lookup and catches only `MapMismatchError` | `host.py:583` |
| 3 | `load_patch` can raise `PluginThreadError`, not core's `PatchRejectedError` | `instrument.py:320` |
| 4 | `measure()` writes through `_write(start)` with no main-thread check | `host.py:733` |
| 5 | The watch is one object for the whole process and cannot handle two writes at once | `host.py:257` |
| 6 | The main-thread check uses `threading.main_thread()`, not the Cocoa main thread | `host.py:633` |
| 7 | If the replacement callback raises, ctypes only prints the error | `host.py:244` |
| 8 | The child processes are killed only by `subprocess.run` | `test_vital_instrument.py:911`, `test_host.py:984` |
| 9 | The stand-in test depends on timing | `test_vital_instrument.py:952` |
| 10 | A `filter_1_on` of exactly 0.5 plants 0.0 | `host.py:422` |
| 11 | Each answered alert's window stays in `[NSApp windows]` | `host.py:244` |
| 12 | `_planted` parses the whole preset again just to read one key | `host.py:418` |
| 13 | `_planted`'s second decode can raise a bare `RecursionError` | `host.py:418` |
| 14 | The alert's words are lost when pedalboard also raises | `host.py:599` |
| 15 | Importing `host` on macOS now loads AppKit at import time | `host.py:287` |
| 16 | Two splits of the 64 are mixed together | `agent-os/standards/vital/instrument.md:181` |
| 17 | The crash and marker bullets name no platform, and the heading drops the macOS version | `README.md:98`, `:83` |

## What was checked while shaping

Each check was a read of the code at `9bc336c` or a run in memory, with nothing written to the
tree. None of it is evidence for a claim in a doc or a standard: a figure is quoted only from a
kept transcript, and the cost transcript measures the in-memory figures again.

- **1, real but narrower.** `_reached` turns pedalboard's `RuntimeError`, `ValueError` and
  `TypeError` into `PluginStateError`, chained, so those three already reach `_unplanted`. What
  skips it is anything else: `KeyboardInterrupt` and other `BaseException`s, `MemoryError`, or an
  error from the watch itself. `load_patch` rolls back on `PluginStateError` alone, so after such
  an error the plugin can hold part of the new text while the model holds the old one.
- **2, real for a bare `VitalHost`.** On the first load, `_marker()` reaches `_parameter_map()`,
  whose name and version reads are guarded and raise `PluginStateError` when refused, and
  `_hosted_parameter(MARKER)`, which raises `UnknownParameterError`. Either leaves `load_state`,
  and `_marker_sought` is already True, so every later load is made unchecked with no warning.
  `VitalInstrument.__init__` calls `parameter_ids()` first, which resolves the map, so the
  instrument cannot reach this.
- **3, real against core's docstring.** `patchbay.contracts.Instrument.load_patch`: "PatchRejectedError
  when the instrument cannot load all of it, changing nothing." The issue #20 spec chose
  `PluginThreadError` on purpose (its Decision 14). fromtheoutfit/patchbay#25 is open on a
  related question, the errors an instrument raises once it has lost step.
- **4, real.** `measure()` ends on `self._write(start)` with no thread check. The issue #20
  spec's run 3 found that a good text loaded from a second thread leaves the host's parameter
  reads stale (`probes-3-counts.txt`). `start` is the plugin's own state, so no alert arises
  there.
- **5, reachable only through 4.** Once every write on macOS is the main thread's, the one
  process-wide watch is entered by one thread, one write at a time. The only code that runs
  inside a write is the callback, which writes nothing. Off macOS `_NoWatch` holds no state.
- **6, real for an embedded interpreter, reasoned and not measured.** `threading.main_thread()`
  is the thread that started Python. AppKit needs the process's main thread, which
  `pthread_main_np()` names.
- **7, real.** A `ctypes` callback that raises: ctypes printed the traceback, and the call
  returned 0, three times out of three, not `_FIRST_BUTTON` (1000). This was run in memory, with
  no Vital. The alert also goes unrecorded, so `_write` reports success on a text Vital refused.
- **8, real.** `subprocess.run` kills the child only on an exception in the parent. A SIGTERM or
  SIGKILL sent to pytest alone leaves the child running. A Python watcher inside the child cannot
  help: pedalboard holds the GIL while Vital's alert waits (the issue #20 spec's "What shaping
  read"). SIGALRM's default action is the kernel's and needs no Python.
- **9, real.** `_NEVER_RETURNS` writes its pid file after the interpreter starts, the parent kills
  it at 1 s, and the test then reads the file: a slow start can beat that. After the kill
  `subprocess.run` reaps the child, so the pid can be reused, and `os.kill(pid, 0)` can then find
  another process.
- **10, unmeasured.** `_planted` plants 0.0 when the text's value is at the midpoint or above. Only
  0 and 1 were seen on Vital. If Vital rounds a switch's 0.5 down, a load it took is refused as
  ignored; if it truncates a switch, the same happens for every value from 0.5 to below 1.0.
- **11, real and already recorded** as a limit in `vital/plugin-state.md` (500 window objects after
  500 answered alerts; resident memory 603 to 701 MiB over those 1,500 loads, the alerts' share
  not separated). Closing the window would need a new AppKit call inside the callback, unmeasured.
- **12, real but small, and its figure partly wrong.** `_floats` is called by `measure` alone, not
  on the load path. Each `load_state` decodes the text twice, once in the state's validator and
  once in `_planted`, so a `load_patch` decodes it four times. In memory a decode took a median of
  0.6 ms on a median-sized installed preset (Big Stomp, 751,303 bytes) and 5.1 ms on the largest
  (Float Chords, 10,126,117 bytes).
- **13, does not hold as stated.** The decoder's C scanner counts C recursion, which Python frames
  do not use on 3.12. Measured in memory on Python 3.12.16: the first JSON array depth refused was
  9997 inside an object called directly, as `_planted` calls it; 9994 through
  `PluginState.with_text`, the pydantic validator `load_state` runs first; and 9998 for a bare
  array, both at the top and under 800 more Python frames. Within one `load_state`, `_planted`'s
  decode therefore has 3 more levels of room than the validator's, and a text the validator passes
  cannot make it raise `RecursionError`.
- **14, real.** In `_write`, `_reached` raises inside the `with` before `if alerts:` runs, so when
  pedalboard raises in a write that alerted, the alert's words are lost.
- **15, does not hold as stated.** `host.py` imports `pedalboard` at its top. Its native module,
  `pedalboard_native.cpython-312-darwin.so`, links AppKit, Cocoa, Foundation, CoreFoundation and
  `/usr/lib/libobjc.A.dylib` (`otool -L`). In memory `_alert_watch()` then took 0.14 ms, after
  `import pedalboard` took 12 ms and `import host` 6 ms more.
- **16, real.** Line 181 reads "64 still load, 54 of them as a patch, 10 held as given and 3
  changing no section among the 64". It runs together the split by entry point (54 as a patch, 10
  given to the host alone) with the split by outcome, and "51 of the 64 are not held as given"
  is never stated.
- **17, real.** The README's crash and marker bullets name no platform, and its heading at line 83
  gives "Vital 1.6.4 through pedalboard 0.9.26 on arm64" without macOS 26.6.2. `load_patch`'s
  docstring says a patch Vital dies on "kills the calling process on any platform", and nothing
  was measured off macOS.

Facts the owner asked to have recorded:

- **What `set` and `render` do from a second thread on macOS today.** From the code: neither
  checks the thread. `set` writes `raw_value` and `render` calls `process` from any thread. From
  the kept probes: run 3 made loads from a second thread and then rendered on the main thread
  (`probes-3-counts.txt`, `probes-3-crash-reports.txt`). Neither `set` nor `render` from a second
  thread was measured. No probe is run for it here.
- **What Vital does when the replaced method returns 0 and not the first button** was not
  measured. The in-memory run called a raising callback from Python and used no Vital. No probe
  is run for it here.
- **Every caller of the state write.** `VitalHost._write` is the only place the plugin's
  `preset_data` is set (`host.py:598`). It is called by `load_state` (`host.py:640`, unchecked,
  and `:649`, checked) and by `measure` (`host.py:733`). "What was built" shows each going
  through the thread helper.

## Shaping answers

In the owner's words, 2026-11-17, by AskUserQuestion. The option chosen is named first.

**1 and 2 (marker)**, to "Host and instrument": "1. Conditions:
- Host: _unplanted runs on every way out of a write and the original error is re-raised as itself, the same object, not wrapped. If _unplanted itself fails on the way out, the original error still leaves, with the second one attached to it and not in its place.
- Instrument: only an error that leaves from inside the send to the plugin marks it out of step. One raised before the plugin is called (the guard, validation, PluginThreadError, MapMismatchError) changes nothing and marks nothing, as today. The catch covers BaseException, since KeyboardInterrupt is not an Exception; no rollback is attempted for these, and the error is re-raised as itself.
- Tests on a stand-in plugin, no Vital: KeyboardInterrupt and MemoryError raised in the first load, between the two loads, and in the second; each asserts the marker is not left planted, the instrument is out of step, set/load_patch/render are refused and get/patch answer from the model, and the error that leaves is the one raised.
- _marker_sought: a test where the first lookup fails with another error, and the next load looks again and is checked; and one where MapMismatchError settles it.
- Each new guard is held by a mutant in this revision's mutation.txt.
- instrument.md's lost-step bullet and plugin-state.md's marker bullet are rewritten from the shipped code after it is written, shown to me old beside new.
- Note it for fromtheoutfit/patchbay#25 in shape.md: a second way an instrument loses step (a foreign error mid-load), as evidence for that question; nothing is filed on core.
- Evidence: this changes code in host.py and instrument.py, so by the rule sent to standards #38 the four evidence runs are owed again on the final tree. Do not rerun now. Fix every finding of this review first, then ask me once for one rerun at the end."

(Read in this spec: "the second one attached to it" is `add_note` on the original error, naming
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

(Read in this spec: "a unit test on the stand-in" is the real `_AppKitWatch` built from stand-in
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

The references, standards, visuals and product were confirmed as listed, with
`base/python/errors` added ("Setup" above). The plan was approved as written, `plan.md`.

## Decisions

1. **The scope is the review comment, every finding,** each checked against the code before it
   was decided. Where the check disagreed with the reviewer, the reply says what was measured.
2. **Finding 1: the marker is set back on every way out of a write, in the host, and a foreign
   error from inside the loads marks the instrument out of step.** The original error leaves as
   itself; one raised while setting the marker back is attached to it by `add_note`. A
   `VitalError` raised before the plugin is called marks nothing, as today. No rollback is tried
   for a foreign error.
3. **Finding 2: the marker's lookup is settled only by a lookup that succeeded or by a
   `MapMismatchError`.** Any other error leaves that load, and the next load looks again.
4. **Finding 3: `load_patch` refuses a load from the wrong thread as a patch,**
   `PatchRefusedError` chained from `PluginThreadError`, its message in the owner's order. The
   guard still runs first. `VitalHost.load_state` and `VitalInstrument.__init__` keep raising
   `PluginThreadError`. This reverses the issue #20 spec's Decision 14 for `load_patch` alone.
   That Decision is not edited: the review found it breaks core's `load_patch` contract for a
   core caller on a worker thread, and the patch error is what that contract names. The core
   question goes to a new drafted issue on fromtheoutfit/patchbay; patchbay#25 is not touched.
5. **Findings 4 to 6: one thread check, the OS's.** `pthread_main_np()` through the watch, first
   in `load_state` and `measure` and again in `_write`. No lock: the watch refuses to be entered
   while it is in place, as `PluginStateError` naming that. The host refuses to load on macOS
   where `pthread_main_np` cannot be reached.
6. **Findings 7 and 14: an alert's words always reach the error.** The callback records the
   alert and fixes its return before anything that can fail. An alert whose words could not be
   read is still `PluginStateError`, chained from what the read raised. An alert together with a
   pedalboard refusal is one `PluginStateError` carrying both, chained from pedalboard's error.
7. **Findings 8 and 9: a child the tests start ends itself at its alarm,** SIGALRM's default
   action, armed before anything that could block, at a named limit past the parent's, shown by a
   probe at the owner's word first. The stand-in test checks a lock and never a pid, and its limit
   is 3 s.
8. **Finding 10: probe first.** If every verdict is right, the rule stands and a test pins it from
   the scale's ends and the transcript's boundary. If any is wrong, stop and present.
9. **Findings 12 and 15 are declined,** on the figures of the kept cost transcript and in the
   reviewer's words.
10. **Finding 13 does not hold as stated, and the helper is guarded anyway:** the standard's one
    decoder helper, with the margin between the two limits measured and not promised. It is
    tested directly, and a `load_state` test holds only the order.
11. **Finding 11 is deferred** to a new issue on fromtheoutfit/patchbay-vital, in the reviewer's
    words, marked unverified.
12. **Findings 16 and 17 are fixed:** 17 in the feature's change set, 16 in the retrospective's,
    since it is a project standard. Each is shown to the owner old beside new before it is
    written.
13. **One rerun of the issue #20 evidence, on the final tree, asked for once at the end:** the
    four runs (`remedy-run`, `rollback-count`, `marker-count`, `mutation`), this revision's
    mutants with them, and the gate.
14. **Drafts are shown whole and filed only at the owner's word, with no attribution:** the
    deferred-items issue, the core issue and the reply. An issue a file names by number is filed
    before the final runs; otherwise after the gate's clean run. The owner writes PR 26's
    description, and "Where the PR description no longer reads true" lists what changed.
15. **No gate file changes,** and no file is added, removed or renamed under `scripts`, `src`,
    `tests` or `agent-os/standards`, so the negative harness is not rerun.

### What was replaced while shaping, and why

- **The issue #20 spec's Decision 14,** "It is not a `PluginStateError`, so `load_patch` does not
  answer it with a rollback", stands for the rollback. Its other half, that `load_patch` raises
  `PluginThreadError` itself, is reversed by Decision 4 above: the review's finding 3 showed that a
  core caller catching `PatchRejectedError` meets an error it does not catch. That spec's text is
  left as it is.
- **The owner's wording "the patch itself was not judged"** was replaced at the owner's word by
  three statements in order. `load_patch` reads the patch and runs the guard before the first load
  reaches the thread check, so a patch that gets to the thread error has passed the package's
  checks. What was not done is giving it to Vital.
- **The owner's first test condition for finding 13** asked for a test through `load_state`
  asserting `PluginStateError`, the marker not planted and the plugin not called, with the
  helper's mutant caught there. The validator's limit is 3 levels below `_planted`'s, so through
  `load_state` the validator always refuses first, and such a test cannot fail on the helper. It
  was replaced at the owner's word by a direct test of the helper and a `load_state` test of the
  order alone.

### A note for fromtheoutfit/patchbay#25, recorded and not filed

patchbay#25 asks what an instrument does once it has lost step with its device. This revision
adds a second way to lose step. Before it, only a refused rollback lost step. Now an error from
outside the package that leaves while the loads are being sent, a `KeyboardInterrupt` or a
`MemoryError`, also leaves the plugin in a state the model does not describe. `load_patch` then
marks the instrument out of step and re-raises that error as itself, and a core caller meets an
error core names nowhere. This is evidence for patchbay#25's question. Nothing is filed on core
for it.

## Context

- **Visuals:** None.
- **References:** the issue #20 spec, the PR 23 second-review revision, the host's guards and the
  test doubles. `references.md` says what each gives.
- **Product alignment:** `agent-os/product/` is unchanged. The adapter says what it does on each
  platform, and a claim about Vital is measured.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a. `base/python/errors` is named for findings 1, 3 and 14.

**Feature-specific:**
- `vital/plugin-state` — the watch, the main-thread rule and the marker, each rewritten.
- `vital/instrument` — the lost-step state, the thread rule and the line finding 16 is about.
- `vital/preset-tests` — a test that gives Vital a text it may not return from does so in a child
  it can kill.
- `vital/preset-file` — the one decoder helper finding 13 is about.
- `vital/parameter-map` — the marker's scale and its two ends.
- `base/testing/tests` — where each test lives and how its expected values are made.
- `base/process/verification-gate` — the gate this spec is held to.
- `base/process/standards-retrospective` — the gate's last step.
- `base/process/ownership` — no agent commits, pushes or files without the owner's word.

## The owner's answers during the build

2026-11-17, by AskUserQuestion, in the owner's words.

**The alarm probe**, offered with faulthandler's watchdog as a second mechanism, to "Start, both
mechanisms": "2. Start it; I will not click the windows. Conditions:
- Post the four clock times before starting and say when each window has gone.
- For each of the four children: when its window went, how it ended (the signal, or the
  exit code and the first line the watchdog wrote), and how long after its limit.
- The parent kills none unless a window is still up 5 s after its limit was due; then it
  kills that child, reports that the mechanism did not end it, and stops.
- Kept transcript, tree and machine printed; a first try that stops is kept beside its
  replacement.
- Then come back with both results and say, for each mechanism, how a test would tell "the
  child ended itself at its limit" from any other failure. If both work, my leaning is the
  watchdog thread, since it needs no skip and the probes already use it; I decide after the
  figures."

**The mechanism**, after the probe, to "faulthandler watchdog": "1. Conditions:
- The watchdog is armed first in every child, before any import that could block, with a
  limit that is a named constant past the parent's; a test asserts the one is greater.
- "It ended itself" is three things together: exit status 1, a stderr line beginning
  "Timeout (", and the parent not having killed it. The helper that judges this is one
  function, used by every test that starts a child.
- The CI stand-in test asserts all three on a child its parent never kills, and its
  docstring says the header is CPython's and undocumented, so this is the test that will
  fail if it changes.
- The child's stderr is shown in the test's failure message, so the traceback of where it
  was stuck is not lost.
- preset-tests.md is rewritten from the shipped tests, old beside new, naming the watchdog
  and why SIGALRM was not used, with alarm-probe.txt cited for both.
- shape.md records that the first decision (SIGALRM) was replaced after the probe."

**One judge**, once it was found that neither test module can import from the other, to "One
judge per module": "2. My condition is amended: one judge per module, the same rule in each.
Conditions:
- The two functions have the same name, the same three checks (exit status 1, a stderr line
  beginning "Timeout (", not killed by the parent) and the same failure message carrying
  the child's stderr.
- Each module has its stand-in test on a child its parent never kills, so CI holds both;
  the unit one keeps its limit short, and both limits are named constants.
- Each function's docstring names the other's module, so a change to one is made to both.
- No test moves, no file is added, no gate file changes.
- shape.md records the amendment and why a shared module was not used (the negative
  harness rerun and Decision 15).
- Note it as a candidate for the standards batch, not filed now: test support shared
  between the unit and integration suites has no home in the layout."

**The standards edits**, shown old beside new, to "Write as drafted": "1. Write as drafted, as
their own change set. Conditions:
- The edits cite things that do not exist yet: MR1 to MR23, and this revision's
  marker-count.txt and remedy-run.txt "made on its final tree". After the single rerun and
  before the gate, check every mutant and transcript the four standards cite: that it
  exists, and that it says what the standard says of it. Any that differs, the standard is
  corrected to the transcript and shown to me; the transcript is never bent to the standard.
- One stale test name was found in plugin-state.md. Check them all: every test name and
  every function or class name cited in the four standards is searched for in the tree, and
  the ones not found are listed. Keep the listing in verification/.
- preset-tests.md: the sentence about "Timeout (" being CPython's undocumented header
  appeared twice in what I was shown. It is written once.
- The deferred-items issue is filed before the gate, since plugin-state.md names it as #N;
  its draft comes to me whole first, with the other drafts.
- The figures in instrument.md's guard line are checked once more against
  silent-and-loaded.txt after writing: 54 and 10, 13 (10 and 3), 51 (15, 1 and 35)."

**Draft 1**, to "File it now": "1. File it as shown, read it back from GitHub against shape.md's
text, and tell me its number. Conditions:
- It claims nothing beyond the reviewer's words and the soak's figures; if its closing
  sections propose a remedy, they say it is the reviewer's suggestion and unmeasured.
- It is not listed among the issues that come before the first agent experiment.
- Its number goes into plugin-state.md and the reply, both non-code, before the single
  rerun; nothing under src/ or tests/ is touched for it."

**Drafts 2 and 3**, to "Both as shown (Recommended)".

## Decisions made during the build

16. **Finding 10: the marker's rule stands.** Every verdict of the shipped rule was right on the
    57 values of `verification/midpoint-probe.txt`: Vital's parameter read held each as given,
    and only its own text rounds a switch, below 0.5 to 0 and from 0.5 to 1. A test pins the
    rule from the scale's two ends and the transcript's values. The only wrong verdicts were
    under the end the shipped rule never plants: 0 planted at 0, and 1 at 1.
17. **Finding 8: faulthandler's watchdog, not SIGALRM.** Decision 7's first mechanism,
    `signal.alarm`, was replaced after `verification/alarm-probe.txt`: both ended a child
    blocked in Vital's alert and one in AppKit's, SIGALRM 0.016 to 0.040 s past a 3 s limit
    and the watchdog 0.052 to 0.070 s past, and the watchdog is on every platform. "It ended
    itself" is three checks together: status 1, a stderr line beginning "Timeout (", and no
    kill by the parent.
18. **One judge per module, the owner's condition amended.** `_ended_itself`, `_armed` and
    `_child_failed` are written in `tests/unit/test_host.py` and in
    `tests/integration/test_vital_instrument.py`, the same name, checks and message in each,
    each docstring naming the other module. A shared module was not used: a new file under
    `tests/` means the negative harness's rerun, and Decision 15 says no file is added. pytest
    puts each test file's own directory on the path, and the integration suite is collected
    first, so neither module can import from the other. **A candidate for the standards
    batch, not filed now:** test support shared between the unit and integration suites has
    no home in the layout.
19. **The instrument's thread test is renamed** to
    `test_a_load_from_a_second_thread_changes_nothing_and_is_refused_as_a_patch`: its old
    name said it was the thread's error, which it no longer is. The test is the same one,
    expecting the patch error.
20. **The figures quoted are the kept transcripts', not shaping's.** Shaping's in-memory reads
    gave 9998 for a bare array's limit at the top and under 800 frames; `costs.txt` measures
    all three limits on one text shape, `{"a":` then the arrays, and gives 9997 directly,
    9994 through the validator and 9997 under 800 more frames. The decode and watch figures
    are `costs.txt`'s: 0.60 ms, 5.19 ms and 0.123 ms.
21. **A test name taken for stale, and is not.** While the retrospective was drafted,
    `test_a_load_from_another_thread_is_no_state_error`, cited by `vital/plugin-state.md`, was
    searched for in `tests/unit/test_instrument.py` alone, not found, called stale to the owner
    and replaced in the draft the owner approved. It is in `tests/unit/test_errors.py`, and the
    issue #20 spec's `mutation.txt` shows it failing under ME1. The citation is put back beside
    the new one, the owner is told, and every name the four standards cite is searched for over
    the whole tree (the owner's condition above, `verification/cited-names.txt`).

## Drafts for the owner

Each is shown whole and filed only at the owner's word, with no attribution. Draft 1 changed
in one sentence after it was approved, to meet the owner's condition that a remedy it names be
the reviewer's suggestion and unmeasured.

### 1. New issue on fromtheoutfit/patchbay-vital, filed before the gate

> **Title:** The alert watch: each answered alert leaves its window in the application's list, unverified
>
> The review of PR 26 (fromtheoutfit/patchbay-vital#26, "Review findings", 2026-11-17) gave this as finding 11, one of its smaller items. It is given in the reviewer's own words and is **unverified**: the revision that answered the review probed nothing for it.
>
> > **`src/patchbay_vital/host.py:244` — each answered alert's window stays in `[NSApp windows]`.** The transcript shows 500 windows after 500 alerts, and memory going from 603 to 701 MiB over 1,500 loads. Closing or ordering out the alert's window before returning would stop the growth.
>
> The line number is the review's, at `9bc336c`; the callback is `_AppKitWatch._answered_at_once` in `host.py`.
>
> ## What is already recorded
>
> `agent-os/standards/vital/plugin-state.md` states it as a limit of the watch: each answered alert leaves one window object in the application's own list, never shown and never listed by the window server, 500 after 500 of them, resident memory going from 603 to 701 MiB over those 1,500 loads, the alerts' share of it not separated from the loads'. The figures are the soak in the spec of issue #20 (`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/`), on Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS 26.6.2.
>
> ## What is not known
>
> The reviewer's suggestion, closing or ordering out the window before returning, would be a new AppKit call made inside the callback that stands in for `-[NSAlert runModal]`, and it is unmeasured: whether the window exists to close by then, whether closing it frees what the soak counted, and what share of the 98 MiB is the alerts' are not known.
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. Probed before anything is built: a soak counting window objects and resident memory with and without the change, each alert announced before it runs. CHANGELOG; gate green. No commit, pull request or push by an agent.

### 2. New issue on fromtheoutfit/patchbay, filed after the gate's clean run

> **Title:** Instrument: an error for a call made from a thread the instrument cannot serve
>
> `Instrument.load_patch` at `eddba95` says: "PatchRejectedError when the instrument cannot load all of it, changing nothing." It names no error for a call the instrument cannot serve from the thread it was made on.
>
> ## The case
>
> patchbay-vital hosts the Vital synthesizer through pedalboard. On macOS, Vital answers a preset it cannot read with a modal alert, and AppKit opens a window on the process's main thread alone. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS 26.6.2, in the spec of patchbay-vital's issue #20 (`verification/probes-3-counts.txt`, `probes-3-crash-reports.txt`):
>
> - From a second thread AppKit refuses the alert's window (`NSInternalInconsistencyException: NSWindow should only be instantiated on the main thread!`, under `-[NSAlert init]`), and the load raises through pedalboard.
> - The plugin's parameters are then read stale, as they are after a good preset loaded from a second thread.
> - The process died at its next render, on the main thread, 11 of 11.
>
> What the adapter does meanwhile, on the branch of fromtheoutfit/patchbay-vital#26:
>
> - Its host writes a state on the process's main thread alone on macOS, by `pthread_main_np`, and raises its own `PluginThreadError` from any other thread, before the plugin is called.
> - `VitalInstrument.load_patch` from such a thread raises `PatchRefusedError`, which is core's `PatchRejectedError`, chained from that error. Its reason says the call came from a thread the plugin cannot be loaded from, that the patch passed the adapter's own checks, and that it was not given to Vital. Nothing is changed or published.
> - `VitalInstrument.__init__` raises `PluginThreadError` itself. `set` and `render` check no thread, and neither was measured from a second thread.
> - On every other platform there is no thread rule, and nothing was probed there.
>
> So a core caller on a worker thread, an async executor or an agent loop, catches `PatchRejectedError` for a patch that may load from the right thread, and cannot tell it from a patch the instrument judged.
>
> ## The question
>
> Should core name an error for a call made from a thread the instrument cannot serve, and for which methods?

### 3. Reply to the review of PR 26, for the owner to post

Not posted by an agent. The two numbers are filled in as each issue is filed.

> Revised in `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`. Each finding was checked against the code at `9bc336c` before it was decided. Everything measured is on Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS 26.6.2, and the transcripts named are in that spec's `verification/`.
>
> 1. **Real but narrower.** `_reached` already turns pedalboard's `RuntimeError`, `ValueError` and `TypeError` into `PluginStateError`, so those three did reach `_unplanted`; `KeyboardInterrupt`, `MemoryError` and the watch's own errors did not. **Fixed:** the marker is set back on every way out of a write, the error leaving as itself with any failure to set it back noted on it, and such an error while `load_patch` sends a text marks the instrument out of step (`host.py`, `instrument.py`; `test_an_error_from_outside_the_package_in_a_write_leaves_as_itself_and_the_marker_is_set_back`, `test_an_error_from_outside_the_package_mid_load_leaves_as_itself_and_the_step_is_lost`).
> 2. **Real**, for a bare `VitalHost`: the instrument resolves the map in `__init__`, so it could not reach this. **Fixed:** the lookup is settled only by a marker found or a `MapMismatchError` (`test_a_marker_lookup_that_fails_is_sought_again_at_the_next_load`).
> 3. **Real.** **Fixed:** `load_patch` raises `PatchRefusedError`, core's `PatchRejectedError`, chained from `PluginThreadError`, saying the patch passed the package's checks and was not given to Vital (`test_a_load_from_a_second_thread_changes_nothing_and_is_refused_as_a_patch`). Core's question is fromtheoutfit/patchbay#27.
> 4. **Real.** **Fixed:** `measure` asks the thread first, before it sets anything, and `_write` asks again (`test_a_measurement_from_a_second_thread_is_refused_before_any_parameter_is_set`, `test_a_state_write_from_a_second_thread_is_refused_by_the_write_itself`).
> 5. **Real but narrower:** it could be reached only through 4. Once every write is the main thread's, the one watch is entered by one thread at a time, and the callback writes nothing. **Fixed** without a lock: the watch refuses to be entered while it is in place (`test_the_watch_refuses_to_be_entered_while_it_is_in_place_and_puts_the_method_back`).
> 6. **Real**, for an interpreter embedded and started off the main thread; reasoned and not measured. **Fixed:** `pthread_main_np` (`test_on_macos_pthread_main_np_answers_the_main_thread_and_no_other`).
> 7. **Real.** In memory, with no Vital, a raising ctypes callback returned 0 and not 1000; what Vital does with 0 was not measured. **Fixed:** the callback notes the alert and fixes its button before anything that can fail, and an alert whose words were not read is still refused (`test_the_callback_notes_an_alert_whose_words_cannot_be_read_and_returns_the_first_button`, `test_an_alert_whose_words_could_not_be_read_is_the_package_s_error_chained_from_the_read`).
> 8. **Real.** **Fixed:** every child a test starts arms faulthandler's watchdog past its parent's limit, so it ends itself where pytest was killed outright. `signal.alarm` was probed too, and both ended a child blocked in Vital's alert and in AppKit's within 0.07 s of a 3 s limit (`alarm-probe.txt`); the watchdog is used as it is on every platform (`test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog`, in both modules).
> 9. **Real.** **Fixed:** the stand-in holds a lock, which the test checks and never a pid, at a 3 s limit, and "never started" and "did not end" fail by names of their own (`test_a_child_that_does_not_return_is_killed_at_its_limit_and_the_test_fails_by_name`).
> 10. **Does not hold.** Vital's parameter read held every value given for the switch as given, 0.5 and the float32s either side of it included; only Vital's own text rounds one, from 0.5 up to 1, so the marker is never planted on what the read holds (57 values, `midpoint-probe.txt`). **No change** to the rule; a test pins the probe's values (`test_the_marker_is_never_planted_where_vital_holds_a_switch_s_value`).
> 11. **Real**, and already a limit recorded in `vital/plugin-state.md`. **Deferred:** fromtheoutfit/patchbay-vital#27, unverified.
> 12. **Real but narrower:** `_floats` is not on the load path; each load decodes its text twice. **Declined:** a decode took a median of 0.60 ms on a median-sized installed preset and 5.19 ms on the largest, 10 MB (`costs.txt`).
> 13. **Does not hold as stated:** the validator, which runs first, refuses at 9994 levels, 3 below the 9997 of the second decode, on Python 3.12.16, so no text it passes reaches a `RecursionError` there (`costs.txt`). **Fixed all the same:** one guarded settings helper, the preset-file standard's one decoder (`test_the_settings_helper_refuses_a_text_one_level_past_the_decoder_s_limit`).
> 14. **Real.** **Fixed:** one `PluginStateError` carrying the alert's words and pedalboard's, chained from pedalboard's error (`test_an_alert_and_a_pedalboard_refusal_are_one_error_carrying_both`).
> 15. **Does not hold as stated:** `host.py` imports pedalboard, whose native module links AppKit, Cocoa, Foundation and libobjc itself (`otool -L`), and the watch then builds in 0.123 ms. **Declined** (`costs.txt`).
> 16. **Real.** **Fixed** in `agent-os/standards/vital/instrument.md`: the split by entry point and the split by outcome are given apart, and 51 of the 64 are not held as given.
> 17. **Real.** **Fixed:** the README, the CHANGELOG and the docstrings name the platform each measurement was made on, and say of any other only that nothing was probed there.

## Base proposals: the texts sent upstream

Shown to the owner whole and approved on 2026-11-17; the new issue's proposal 2 then gained, at
the owner's word, "its `verification/bare-citations.txt`, which lists the 25", since
`cited-names.txt` does not record whether a citation named its spec. Each is filed as written
here and read back against it.

### A paragraph added to fromtheoutfit/patchbay-standards#44, for proposals 1 and 2

Inserted after its last "Revised" paragraph, before its first section; its earlier text kept.

> Revised 2026-11-17, a second time (after the review of patchbay-vital's PR 26, `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`): proposal 3's refinement gains two items, each to be taken or declined on its own, approved by the owner on 2026-11-17. The evidence is in that spec folder on patchbay-vital's branch `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, uncommitted when this was revised; the owner's push puts it there. The text above, this morning's revision included, is unchanged.
>
> - **Item A: every child a test starts ends itself at a watchdog past its parent's limit.** A child the test kills at its limit is killed only while the test's process lives. A test runner killed outright, by an editor's stop button, `kill` or an outer timeout, leaves the child running, and a child blocked inside a third party's call holds what it holds: in the case seen, a modal window on the screen.
>   - The child's first statements, before anything that could block is imported, arm a watchdog that needs no interpreter lock. In Python, `faulthandler.dump_traceback_later(<seconds>, exit=True)`: a C thread that writes every thread's stack to stderr and exits the process with status 1.
>   - The watchdog's limit is a named constant past the parent's, and a test asserts the one is greater. While the parent lives, its kill comes first and the test fails by the parent's name.
>   - "The child ended itself" is three things together: exit status 1, a stderr line beginning `Timeout (`, and the parent not having killed it. Status 1 alone is also what an uncaught error gives. The header is CPython's and not documented as a format, so a test on a stand-in child its parent never kills is the one that fails if it changes. Each failure message carries the child's stderr, where the watchdog's stack shows where it was stuck.
>   - `signal.alarm`, with SIGALRM's default action, also ends a blocked child without the interpreter, and is not used: it is not on every platform.
>   - **Why.** The case seen is a child blocked in a third party's call that holds the interpreter lock: Vital's modal alert, waited on through pedalboard, during which no Python thread and no Python signal handler runs. A watcher written in Python cannot end such a child; a C thread or the kernel can. Both mechanisms ended a child blocked in Vital's alert and one blocked in AppKit's own, the watchdog 0.052 to 0.070 s past a 3 s limit and SIGALRM 0.016 to 0.040 s past, their parent killing neither.
>   - **Verified against** patchbay-vital's `tests/integration/test_vital_instrument.py` and `tests/unit/test_host.py` (each: `_armed`, `_ended_itself`, `_child_failed`, `test_a_child_its_parent_never_kills_ends_itself_at_its_watchdog`, `test_a_child_ended_itself_only_by_all_three_checks`; and `test_each_child_s_watchdog_is_past_its_parent_s_limit`, `test_the_real_alert_child_s_watchdog_is_past_its_parent_s_limit`), that spec's `verification/alarm-probe.txt`, and MR16 to MR20 in its `verification/mutation.txt`.
> - **Item B: a test that asserts a killed child is gone checks something the child held, never its pid.** Once the child is reaped its pid is free, and another process may have it, so a pid that exists proves nothing either way.
>   - The child takes a lock the kernel lets go only when the process is gone, an exclusive `fcntl.flock` on a file the test made, and writes that it started. After the kill the test reads the file and takes the lock without waiting.
>   - "The child never started" and "the child did not end" are two failures, each by a name of its own: the first where the file does not say it started, the second where the lock is still held.
>   - The limit gives any interpreter's start room before the kill; where the platform has no such lock, the test skips by name.
>   - **Why.** patchbay-vital's stand-in test read its child's pid from a file after killing it at 1 s, which a slow start can beat, and checked the pid with `os.kill(pid, 0)`, which a reused pid can fool.
>   - **Verified against** patchbay-vital's `tests/integration/test_vital_instrument.py` (`_NEVER_RETURNS`, `test_a_child_that_does_not_return_is_killed_at_its_limit_and_the_test_fails_by_name`, at a 3 s limit), and MR21 and MR22 in that spec's `verification/mutation.txt`: a stand-in that never says it started, and one whose lock outlives it in a process it starts, each fail the test.
> - **index.yml.** The `testing/tests` description's third rule gains, for each item taken: every child a test starts ending itself at a watchdog past its parent's limit, judged by three checks; and a killed child's going held by what it held, never its pid.

### A paragraph added to fromtheoutfit/patchbay-standards#38, for proposal 5

Inserted after its last "Revised" paragraph, before its first section; its earlier text kept.
Its home is #38's proposal 2, "a transcript that says what tree it ran on shows that tree".

> Revised 2026-11-17, a second time (after the review of patchbay-vital's PR 26, `agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`): proposal 2's refinement gains one rule, approved by the owner on 2026-11-17. The evidence is in that spec folder on patchbay-vital's branch `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, uncommitted when this was revised; the owner's push puts it there. The text above is unchanged.
>
> - **The refinement, third.** A check that reads a kept transcript, by a script or by a reader, matches the transcript's own result lines, anchored where the line begins, and never their words anywhere in it. A transcript that embeds the scripts it ran embeds the text of every message those scripts can print, so the words of a failure stand in every transcript, passing or not.
> - **Why.** patchbay-vital's revision after the review of PR 26 ran four transcripts back to back under a script that stopped at the first whose tree had changed. It stopped after the first, whose own line says "cmp: the tree after the run is the tree before it": it had matched `THE TREE CHANGED DURING THE RUN` in the copy of the transcript wrapper embedded at the transcript's end. The tree had not changed. The check was anchored to the line `cmp: ` begins, and the other three were run on the same tree.
> - **Verified against** that spec's `verification/mutation.txt` (its line "cmp: the tree after the run is the tree before it", and the embedded wrapper's `echo "cmp: THE TREE CHANGED DURING THE RUN"`), its `tree-since-the-rerun.txt`, which shows the four runs printed one tree, and its `shape.md`, which records the false stop.

### A new issue on fromtheoutfit/patchbay-standards, for proposals 3 and 4

No open issue carries either: #39 is about a characterization test, #41 about a harness
extract, and #38's proposal 3 about where a refinement is filed.

> **Title:** Standards spec: a rewritten standard's citations searched for over the whole tree, and a mutant cited with the transcript that holds it (standards-retrospective.md)
>
> Two proposals from the retrospective of patchbay-vital's revision after the review of its PR 26 (`agent-os/specs/2026-11-17-1238-revision-after-pr-26-review/`), each to be taken or declined on its own, both approved by the owner on 2026-11-17. Each refines "A standard rewritten during a retrospective is verified against the shipped code and tests": what that verification covers for the names a standard cites. No open issue carries either: #38's proposal 3 is about where a refinement is filed, and #39 and #41 about a characterization test and a harness extract. No gate file changes.
>
> Depends on: fromtheoutfit/patchbay-vital, branch `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, which holds the evidence named below. The revision was uncommitted when this issue was filed; the owner's push puts it there.
>
> ## base/process/standards-retrospective.md, "Verify against the code, not against the spec"
>
> 1. **Every name a rewritten standard cites is searched for over the whole tree, and the listing is kept.** A retrospective that rewrites a standard checks each test, function, class, mutant and transcript the standard names, not only those the rewrite added.
>    - The search covers the whole tree as git lists it. A name looked for in one file and not found there is no finding.
>    - A name the project does not define is classed, never listed as "not found": a language built-in; a library's name, found by importing it; a literal the source holds as text; and otherwise found nowhere, listed with the standard's own words around it, so that a name cited as gone reads as such.
>    - The listing is kept in the spec's `verification/`, beside the evidence it checks.
>    - **Why.** In patchbay-vital's revision after the review of PR 26, a test name `vital/plugin-state.md` cited was searched for in one test module, not found, called stale to the owner, and replaced in an edit the owner approved. It was in another module, and the mutation transcript of the spec that wrote the citation shows it failing. The whole-tree search found it, and every other name cited. A first listing, which reported a built-in, a library's name and a container's magic bytes as "not found" alike, was replaced by one that classes them; both are kept.
>    - **Verified against** that spec's `verification/cited-names.txt` and `cited-names-first.txt`, and its `shape.md`, Decision 21.
> 2. **A mutant is cited with the transcript that holds it.** A standard that names a mutant as evidence names, in the same sentence, the spec whose mutation transcript holds it: "the instrument spec's ML2", "MR3 in the revision after the review of PR 26's `mutation.txt`". A spec names its mutants afresh, so one name means another mutant in another spec.
>    - **Why.** In patchbay-vital, `MR1` is a set that stores the curve's float32 in the spec of its issue #8, and a write's error from outside the package that skips setting the marker back in the revision after the review of PR 26; `ME1`, `MM1` and `MG3` each name one mutant in the spec of its issue #8 and another in the spec of its issue #20. `vital/instrument.md` cited 25 mutants or ranges of them with no spec, and a reader had to find each by what it breaks.
>    - **Verified against** that spec's `verification/cited-names.txt`, which names the specs that hold each mutant cited, its `verification/bare-citations.txt`, which lists the 25, and patchbay-vital's `agent-os/standards/vital/instrument.md`, where every mutant now names its spec.
>
> ## index.yml
>
> The `process/standards-retrospective` description gains, for each proposal taken: every name a rewritten standard cites searched for over the whole tree, classed where it is not the project's, the listing kept; and a mutant cited with the transcript that holds it.
>
> ## Consuming projects left behind
>
> None known. patchbay-vital does both as of this revision; the other consuming projects' standards were not searched.
>
> ## Rules
>
> Shaped with /agent-os:shape-spec in plan mode, questions asked and answered. Each rule verified against the shipped files named above, never against this issue's text. CHANGELOG entry. Gate green, gate-run.txt. No commit, PR or push by an agent.

## What was built

- **`src/patchbay_vital/host.py`.** `Alert` is a record with what reading its texts raised.
  `_AppKitWatch` is built from three calls, `install`, `texts` and `on_main`; `_appkit_watch`
  and `_alert_watch` make them from the runtime and the C library, `pthread_main_np` among them.
  The watch refuses a nested entry, and its callback notes the alert and fixes its button
  before reading the texts. `VitalHost._on_a_writing_thread` runs first in `load_state` and
  `measure` and again in `_write`. `_write` raises one error for an alert and a pedalboard
  refusal together. `_set_back` sets the marker back on every way out of a write. `_marker` is
  settled only by a lookup that found it or by `MapMismatchError`. `_settings` reads a text's
  settings for `_planted` and `_floats` through the guarded decoder. The module docstring says
  all of this.
- **`src/patchbay_vital/instrument.py`.** `_text_of` and `_sent` split the old `_send`.
  `load_patch` refuses a `PluginThreadError` as `PatchRefusedError`, rolls back a
  `PluginStateError` as before through `_rolled_back`, re-raises any other `VitalError`, and
  marks the instrument out of step on any other error from inside the loads through
  `_lose_step`. The docstrings say so.
- **`src/patchbay_vital/preset.py`:** `decoded`, which `decode_end` reads through.
  **`src/patchbay_vital/errors.py`:** `PluginThreadError`'s docstring and the module's.
- **Tests.** `tests/unit/test_host.py` gains the thread, watch, callback, alert, marker,
  decoder and midpoint tests, and the watchdog's `_armed`, `_ended_itself` and `_child_failed`
  with its stand-in test. `tests/unit/test_instrument.py` gains the foreign-error and thread
  tests, the thread test renamed. `tests/unit/builders.py`'s stand-in watch follows the real
  one. `tests/integration/test_vital_instrument.py` gains the watchdog, the judge and the
  lock-based stand-in. 902 tests where PR 26's head had 859: 685 unit and 217 integration.
- **Docs:** `README.md` and `CHANGELOG.md`.
- **Records outside this folder:** a dated note at the end of the issue #20 spec's `shape.md`.

## What the transcripts show

Each is kept in `verification/`, made on a still tree, its tree and machine printed. Figures
here are the transcripts' own.

- **`midpoint-probe.txt`** (finding 10): 57 values of `filter_1_on`, ten listed and 47 found
  by bisection. Every verdict of the shipped rule is right; Vital's parameter read held each
  value as given, and its own text rounds one below 0.5 to 0 and from 0.5 to 1. The
  boundaries lie between 0 and the least float32, between the float32 below 0.5 and 0.5, and
  between the float32 below 1 and 1. No window showed. Through the instrument each value loads,
  and the model and `get` hold it as given.
- **`alarm-probe.txt`** (finding 8): four children, each blocked in an alert nothing answered,
  each ended by its own mechanism, the parent killing none: SIGALRM 0.016 and 0.040 s past a
  3 s limit, faulthandler's watchdog 0.052 and 0.070 s past.
- **`costs.txt`** (findings 12, 13, 15): a decode took a median of 0.60 ms on a median-sized
  installed preset and 5.19 ms on the largest; the watch built in a median of 0.123 ms; the
  decoder refused first at 9997 directly, 9994 through the validator and 9997 under 800 more
  frames, on Python 3.12.16; and pedalboard's native module links AppKit, Cocoa, Foundation,
  CoreFoundation and libobjc.
- **The single rerun on the final tree, 2026-11-17 15:39 to 16:41 EST:**
  - `mutation.txt`: 39 mutants, issue #20's 16 adapted to the moved code, each saying how,
    and MR1 to MR23. Each was caught by every test named for it. MW4's real alert ran from
    15:47:00 to 15:47:19.
  - `marker-count.txt`: the marker read the text's value after 154 of 154 loads under each
    history; all 903 floats and every section the same with the check as without, 77 of 77.
  - `rollback-count.txt`: 77 of 77 on every count. The refused call took 93.6 to 615.9 ms, a
    median of 180.4, where issue #20's took 81.6 to 580.3, a median of 171.8; no standard or doc
    cites that timing.
  - `remedy-run.txt`: 335 of 335 returned, none died, none killed; 3, 28, 221, 64 and 19 by
    outcome; 0 disagree with run 4; beside issue #20's remedy run, 0 texts moved. No child's
    window. A window of another process new since the run began showed at 80 of 17,631 polls:
    the owner's own use of the machine, as the owner said it would be.
- **`tree-since-the-rerun.txt`:** the four printed one tree, before and after alike. Ten paths
  differ from it now, none code: the six verification transcripts written after it and the
  four standards whose mutant citations and headers were corrected.
- **`cited-names.txt`:** every name the four standards cite. 191 test names, all found. Every
  function and class name is defined in `src` or `tests`, or is a built-in, a library's name or
  a literal, but `_VOLUME_FLOOR`, which the standard cites as a constant the tests had until the
  revision after PR 14's sixth review. Every mutant and transcript cited is in some spec's
  `verification/`.
- **`bare-citations.txt`:** before the citation fix, 25 mutants or ranges cited with no spec in
  `vital/instrument.md` and 1 in `vital/preset-file.md`; now 0 in all four.
- **`gate-run.txt`:** see the Verification Gate below.

### Runs that went wrong, each kept

- **The rerun's run script stopped wrongly after the mutation run.** Its check matched
  `THE TREE CHANGED DURING THE RUN` in the copy of `transcript.sh` the transcript embeds; the
  transcript's own line says the tree after the run is the tree before it. The script, which
  is not a transcript, was corrected to read the anchored line `cmp: ` begins, the mutation run
  was not run again, and the other three ran on the same tree. It is the case of base proposal
  5.
- **`cited-names-first.txt`** reported a built-in, a library's name and a literal as not found
  alike, and searched two mutation transcripts alone; `cited-names.txt` classes them and
  searches all.
- **`bare-citations-first.txt`** was given its eight arguments as one under zsh and stopped
  before counting anything.
- **`gate-run-first.txt`** passed, exit 0 and 902 passed, and lost the wrapper's embedded
  scripts to an empty list under `set -u` in macOS's bash; the wrapper was corrected and the
  gate run once more for `gate-run.txt`.
- **A miscount told to the owner and corrected:** the owner was told that the citation fix had
  named the spec of "16 more bare citations, all but three in `instrument.md`". There were 26
  bare citations in all, 25 in `instrument.md` and 1 in `preset-file.md`: the three edits the
  owner approved covered MR5, MR6, MR3 and MR15, and the other 22 were all in `instrument.md`,
  in 15 sentences, `MS1 to MS4` among them, which the approved wording had left bare.

## Where PR 26's description no longer reads true

The owner writes the description. Each line: what it says, what is so now, and where it is
shown.

- "A load is the main thread's, on macOS. From any other thread `load_state` raises
  `PluginThreadError`": every state write is the process's main thread's, by `pthread_main_np`;
  `load_state` and `measure` raise it, and `load_patch` refuses as `PatchRefusedError` chained
  from it (`host.py`, `instrument.py`; Decisions 4 and 5).
- "On macOS where the runtime or AppKit cannot be reached, `VitalHost` refuses to load": or
  `pthread_main_np`.
- "`-[NSAlert runModal]` is replaced by a function that notes the alert's two texts": a callback
  that notes the alert, then its texts; the watch refuses a nested entry; an alert whose words
  could not be read, or one with a pedalboard refusal, is still refused (Decision 6).
- "A write that left it there raises `PluginStateError`" (the marker): and the marker is set
  back however the write ends, and is sought again after any error but a map mismatch
  (Decisions 2 and 3).
- "`instrument.py` changes in its docstrings alone": it changes in code too (Decisions 2 and 4).
- Decision "`PluginThreadError` is not a `PluginStateError`": still so, but `load_patch` now
  raises the patch error chained from it (Decision 4).
- "The remedy is macOS's alone. Elsewhere ... the README, the CHANGELOG and the docstrings say
  the block still stands there", and the Limits' "The block stands on every platform but
  macOS": they now say nothing answers the alert there and nothing was probed, so such a preset
  may block there.
- "Tests: 859, where `main` has 803. 649 are unit tests and 210 are integration tests": 902, 685
  and 217 (`gate-run.txt`).
- The stand-in test "holds that limit": at 3 s, by a lock, beside a watchdog in every child and
  a stand-in watchdog test in each module (Decision 7).
- "Locally `scripts/gate.sh` exits 0 with 859 passed": 902 passed (`gate-run.txt`). "CI's gate
  passes at `9bc336c`" and "At `9bc336c` it reports 651 passed and 208 skipped": CI has not run
  on this revision.
- "The rollback, counted ... The refused call takes 81.6 to 580.3 ms, a median of 171.8": 93.6
  to 615.9 ms, a median of 180.4, every count the same (`rollback-count.txt`).
- "Mutation (`mutation.txt`): 16 mutants": 39, all caught (`mutation.txt`).
- "The evidence and the committed code (`tree-since-the-evidence.txt`)": the four runs are made
  again on this revision's final tree and tied to it by `tree-since-the-rerun.txt`.
- "Filed here: #25", and the upstream list (#45, #44, #38): add #27 here, fromtheoutfit/patchbay#27,
  #44 and #38 revised again, and #46 new.
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

**Results (2026-11-17):** `scripts/gate.sh` exits 0 on branch
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, all six
steps, 902 tests passed and none skipped, with Vital and its presets installed, at 16:56 EST on
the final tree (`verification/gate-run.txt`, the tree before and after by blob, unchanged). Its
first try, `gate-run-first.txt`, passed the same and lost the wrapper's embedded scripts. No gate
file changed, and no file was added, removed or renamed under `scripts`, `src`, `tests` or
`agent-os/standards`, so the negative harness was not rerun (Decision 15). Written since the gate
ran: this file, the two gate records, the bare-citation transcripts, and nothing outside this
folder.

**Docs (step 7):** checked, and each reads true after the change.
- `README.md`, "A patch Vital cannot use" and "Known limits": each section names what it was
  measured on, Vital 1.6.4 through pedalboard 0.9.26 on arm64, macOS 26.6.2, and says of other
  platforms only that nothing was probed there and nothing answers the alert. The thread bullet
  gives the patch error, and a bullet says what an error from outside the package does.
- The module docstrings of `host.py`, `instrument.py` and `errors.py`, and the docstrings of
  every function changed, `load_patch`'s and `PluginThreadError`'s among them.
- `CHANGELOG.md`: the revision's entry, and issue #20's entry corrected where it said the block
  still stands elsewhere and that a load from another thread is the thread's error.
- The search for "any platform", "every platform" and "always" in the README, the CHANGELOG and
  the docstrings, each hit with what became of it:
  - `instrument.py`, `load_patch`: "On every platform but macOS no alert is answered: a patch
    ... blocks" became that each was measured on macOS 26.6.2 alone, no alert is answered
    elsewhere and nothing was probed there, so such a patch may block. "kills the calling
    process on any platform" became "was seen to kill the calling process".
  - `host.py:73`, the module docstring: kept as a fact of the code, a write made as it always
    was, from any thread, now with "nothing was probed off macOS ... may block there".
  - `host.py:746`, `load_state`: kept as a fact of the code, now with "nothing was probed there".
  - `host.py:142`, `:203` and `:219`: facts of the code (`fenv_t`'s room, `_NoWatch`, the watch
    built from stand-in calls on any platform); stayed.
  - `CHANGELOG.md:37` ("an alert's words always reach the error") and `:422` (`to_preset`
    always returns a preset the plugin holds): claims about the code, not a platform; stayed.
  - `instrument.py:201` (`name` is always "Vital"), `grisu2.py:4`, `patch.py:23`, `preset.py:255`
    and `parameters.py:19`, `:138`, `:302`, `:322`: about names and numbers, not a platform;
    stayed.
  - The README had no hit before; its new "On any other platform nothing answers the alert, so
    such a patch may block the calling process there" says only what the code does and that
    nothing was probed.
- Every standard that names what changed: the four rewritten in the retrospective below, each
  name they cite searched for (`cited-names.txt`). `vital/measures.md` and
  `vital/parameter-map.md` name nothing this changes. `CLAUDE.md` and `agent-os/product/` name
  nothing this changes.
- The issue #20 spec's `shape.md`, its dated note.

**Version (step 8):** `CHANGELOG.md` under `[Unreleased]`, `### Changed`, "Revision after the
review of PR 26", each finding's outcome; issue #20's entry under `### Fixed` reads as the
revision leaves it. The version stays 0.0.1; no release is cut.

## Standards Retrospective

Step 9, always last, per `agent-os/standards/base/process/standards-retrospective.md`, written
from the shipped diff and the kept transcripts. These edits are their own change set, apart
from the feature's: `agent-os/standards/vital/plugin-state.md`, `vital/instrument.md`,
`vital/preset-tests.md`, `vital/preset-file.md` and `agent-os/standards/index.yml`'s `vital:`
section. The `base:` section is untouched.

- `vital/plugin-state.md`: the watch bullet (the callback, an unread alert, an alert with a
  refusal, the nested entry, the three calls, `pthread_main_np`, issue #27 on the window
  limit, "may block" for "still blocks"); the main-thread bullet (every state write the process's
  main thread's, the helper and `_write`, `set` and `render` unchecked and unmeasured from a
  second thread, the embedded case reasoned and not measured); the marker bullet (set back
  however the write ends, sought again, the midpoint probe, the guarded settings read); "51 of
  the 64 are not held as given"; the header's evidence. The citation of
  `test_a_load_from_another_thread_is_no_state_error`, taken for stale while drafting, stays,
  beside the renamed instrument test (Decision 21).
- `vital/instrument.md`: the guard line's two splits of the 64 apart (finding 16); the thread
  bullet (the patch error, chained, the checks first, Decision 14 reversed for `load_patch`);
  the lost-step bullet (an error from outside the package); every mutant cited with its spec,
  25 in all; the header's evidence.
- `vital/preset-tests.md`: the last bullet keeps the rule of a child the test can kill, and a
  new bullet gives every child its watchdog past its parent's limit, the three checks, one judge
  in each module, the stand-in's lock and its 3 s limit, SIGALRM probed and not used; the
  header's evidence.
- `vital/preset-file.md`: `preset.decoded`, which `decode_end` reads through, used by the host's
  settings read; `MR15` with its spec; the header's evidence.
- `agent-os/standards/index.yml`: the `vital:` entries `instrument`, `plugin-state` and
  `preset-tests`.

Each verified against the shipped code, tests and transcripts it names, every name cited
searched for over the tree (`cited-names.txt`) and every mutant cited with its spec
(`bare-citations.txt`); every figure cited checked against the rerun, which gave the same as
issue #20's runs but for two timings no standard cites. The owner approved the edits shown old
beside new on 2026-11-17, and the three mutant citations, and was shown the rest of the
citation fix as a list.

The four questions:
1. **A pattern no standard covered:** a child that ends itself at a watchdog past its parent's
   limit, judged by three checks; a killed child's going held by its lock; a decoder guard kept
   though another refuses first, its margin measured. Written in the project standards above,
   and the first two proposed for the base.
2. **A standard proved stale:** the main-thread bullet and the marker bullet as the code now
   reads; "still blocks" off macOS, never probed; the guard line's mixed splits; 25 mutant
   citations that named no spec. Corrected above; the last proposed for the base as a rule.
3. **A deliberate deviation:** the same three functions written in two test modules, as no
   module can import from the other suite, with each docstring naming the other (Decision 18).
   Not a standard change: a candidate for the batch below.
4. **Something a standard points at moved:** the instrument's thread test renamed;
   `decode_end` reads through `decoded`; `_send` split into `_text_of` and `_sent`, which no
   standard named. Each standard that names one says so now.

### Standards retrospective (proposed, base)

Presented to the owner on 2026-11-17, all five approved, each filed only after the gate's clean
run, each read back from GitHub against the text recorded above.

1. `base/testing/tests.md`: every child a test starts ends itself at a watchdog past its
   parent's limit, judged by three checks, SIGALRM not used. Verified against
   `tests/integration/test_vital_instrument.py` and `tests/unit/test_host.py` (`_armed`,
   `_ended_itself`, the stand-in watchdog tests), `alarm-probe.txt` and MR16 to MR20. Proposed,
   not applied; filed as fromtheoutfit/patchbay-standards#44, revised in place, item A.
2. `base/testing/tests.md`: a test that asserts a killed child is gone checks what the child
   held, never its pid. Verified against
   `test_a_child_that_does_not_return_is_killed_at_its_limit_and_the_test_fails_by_name`, MR21
   and MR22. Proposed, not applied; filed as fromtheoutfit/patchbay-standards#44, revised in
   place, item B.
3. `base/process/standards-retrospective.md`: every name a rewritten standard cites is searched
   for over the whole tree, classed where it is not the project's, and the listing kept.
   Verified against `cited-names.txt`, `cited-names-first.txt` and Decision 21. Proposed, not
   applied; filed as fromtheoutfit/patchbay-standards#46, proposal 1.
4. `base/process/standards-retrospective.md`: a mutant is cited with the transcript that holds
   it. Verified against `cited-names.txt`, `bare-citations.txt` and `vital/instrument.md`.
   Proposed, not applied; filed as fromtheoutfit/patchbay-standards#46, proposal 2.
5. `base/process/verification-gate.md`: a check that reads a kept transcript matches its
   anchored result lines, never their words anywhere in it. Verified against `mutation.txt`,
   `tree-since-the-rerun.txt` and "Runs that went wrong" above. Proposed, not applied; filed as
   fromtheoutfit/patchbay-standards#38, revised in place.

**A candidate for the standards batch, recorded and not filed, at the owner's word:** test
support shared between the unit and integration suites has no home in the layout. Here it is
written twice, one judge a module (Decision 18). fromtheoutfit/patchbay-standards#40 proposes
values two test directories share through `tests/conftest.py`, which does not cover a shared
function.

Proposals sent upstream: fromtheoutfit/patchbay-standards#44, fromtheoutfit/patchbay-standards#38, fromtheoutfit/patchbay-standards#46

## Revised 2026-11-18, after the second review of PR 26

The second review of PR 26, at `c8ed333`, changed code on the path of the four evidence runs
this revision made on its final tree, so all four were run again on the final tree of the
revision that answered it,
`agent-os/specs/2026-11-18-0651-revision-after-pr-26-second-review/verification/`:
`remedy-run.txt`, `rollback-count.txt` and `marker-count.txt` from the scripts embedded here, at
the blobs listed here, and `mutation.txt` with this revision's 39 mutants, each adapted where
the code it changes has moved, beside that revision's own 15, named MQ1 to MQ15. The transcripts
here stay as they ran.

That revision also replaces one reading made here. This revision's plan read the owner's "inside
the send" as "from the first `load_state` on", so that an error from outside the package which
struck inside `load_state` before the plugin was reached marked the instrument out of step: "the
instrument cannot tell those two apart". The second review's finding 4 showed that this
contradicts `load_patch`'s own docstring. The host now counts state writes begun
(`VitalHost.writes_begun`), and the instrument loses step, or rolls back, only where that count
has moved. Decision 2 here is left as written, and that revision's `shape.md` says why.
