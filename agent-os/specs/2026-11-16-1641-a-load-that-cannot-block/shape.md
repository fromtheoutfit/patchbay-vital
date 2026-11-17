# A load that cannot block (issue #20) — Shaping Notes

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #20, "The host: a preset Vital cannot read blocks the calling process for ever", whole
(`gh issue view 20 --comments`; it has no comments). `VitalHost.load_state` raises for no preset
Vital cannot use: given a text it cannot read, Vital 1.6.4 puts up a modal alert and never
returns to its caller. The instrument's guard refuses every shape of text seen to do it and
cannot judge the inside of a section. The issue names two candidate remedies for this spec to
probe, a trial load in a child process and a watchdog that ends the alert's modal loop, and
asks one more question: can a load Vital silently ignores, the newer version or an alert
dismissed, be detected afterwards by a cheap check through the diagnostic read.

**This spec probes before it builds.** It stops and presents after the probes, before any
remedy is written.

The branch is
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`. Nothing is
committed, pushed or opened as a pull request by an agent.

## The owner's rules for this spec

2026-11-16, from the prompt that started it, in the owner's words.

"Implement GitHub issue #20 (gh issue view 20 --comments) with /agent-os:shape-spec. Ask me the
questions it has. The issue is the spec's scope; shape.md's first Decision cites it.

One uncommitted change is on this branch from main: the record of fromtheoutfit/patchbay#26 in
agent-os/specs/2026-11-15-1448-the-instrument/shape.md. Leave it as it is and list it apart
from this spec's change sets at the end."

"This spec probes before it builds. Stop and present after the probes, before any remedy is
written, with for each candidate what was measured, what it costs a load, and what it leaves
uncovered:

- A trial load in a child process with a time limit: per-load cost with a fresh child and
  with one kept up; whether a text the child loads can still block the parent; what happens to
  the child's own alert; how the float environment guard and the two-load rule apply.
- A watchdog that ends the alert's modal loop: whether it can be done from Python at all, on
  which platforms, and what state the plugin is in afterwards.
- Anything else the probes suggest, named as such.
- The issue's second question: whether a load Vital silently ignores (a newer synth_version;
  an alert dismissed) can be detected afterwards through the diagnostic read, and at what
  cost.
- What each remedy does to the instrument's promises: load_patch raising the package's patch
  error and changing nothing; the lost-step state; the model as the source of truth.

On conflict:

- The issue wins over this prompt.
- No test may hang the gate. Every load that may block is made in a process of its own with a
  time limit, as a probe kept in a transcript, never as a test; a test of the remedy uses a
  stand-in that blocks, or a child the test itself can kill.
- The alert windows appear on the owner's screen: say before each probe run how many will
  show and for how long, and start such a run only at my word.
- A remedy that only works on macOS is said to be so, with what other platforms then get.
- No gate file changes; if the remedy needs one (a new dependency's pin, a pytest setting),
  stop: that is a gate spec first.
- Counted where it can be, a labelled sample where it cannot; expected values from
  primitives; every transcript on a still tree with its tree and machine printed.

Gate green, gate-run.txt with date and branch, present-and-file, then stop and print
git status --short. Do not commit, push, or open a PR."

## What shaping read

With nothing written to the tree and no window opened. None of this is evidence for a claim in
a doc or a standard: the probes measure each, and a figure is quoted from a kept transcript.

- **pedalboard holds the GIL through a state load.** In pedalboard 0.9.26's `ExternalPlugin.h`,
  shipped in the wheel and read for the fact with nothing copied, the `preset_data` setter
  calls the plugin with no release of the GIL. So while the alert waits, no Python thread and no
  Python signal handler runs: a watchdog "from another thread", as the issue words it, cannot be
  a Python thread.
- **`ctypes` reaches the Objective-C runtime and AppKit with the standard library alone** on
  this machine (arm64, macOS 26.6.2, Python 3.12.16): `-[NSAlert runModal]`,
  `-[NSApplication abortModal]` and `-performSelector:withObject:afterDelay:inModes:` are found,
  and `method_setImplementation` exists. No dependency is needed to probe a remedy inside the
  process.
- **The texts' sizes.** The 75 installed presets of `tests/data/factory-manifest.txt` are
  119,040 to 10,126,117 bytes, the median 753,731; the start preset is 60,875 and the fixture
  60,856.
- **The negative harness copies `scripts`, `src`, `tests` and `agent-os/standards`**
  (`scripts/gate-negative-tests.sh`), so a remedy that adds a file under one of them means one
  rerun of it. The instrument spec's rerun took 43 minutes for every test but j.

## The owner's answers in shaping

2026-11-16, by AskUserQuestion. The option chosen is named; the owner's own words are quoted.

- **Visuals:** "None (Recommended)".
- **References** (all four chosen): the #8 probe scripts; `host.py`'s fenv guard; the fake
  plugins; `load_patch`'s rollback.
- **Product alignment**, to "Aligned as read (Recommended)": "1, with two conditions. Whatever
  mechanism the remedy uses (a child process, a call into a system framework) is recorded in
  agent-os/standards/vital/plugin-state.md, written from the shipped code, not in tech-stack.md.
  If the probes point to a remedy that needs a new dependency, stop and say so before anything
  else: that is a gate spec first, and tech-stack.md gains its line there, not here."
- **Standards** (all four groups chosen): `vital/plugin-state`, `vital/instrument` and
  `vital/measures`; `base/testing/tests` and `base/process/verification-gate`;
  `vital/preset-tests`; `base/process/standards-retrospective` and `base/process/ownership`.
- **The plan** was approved as written, `plan.md`.

## Decisions

1. **The scope is issue #20,** fromtheoutfit/patchbay-vital#20, whole: a load that cannot block,
   its two candidates probed, and its second question answered. The issue wins over the prompt.
2. **Probes, then a stop, then the remedy.** No remedy code, test or doc is written before the
   owner chooses at the stop.
3. **Facts come from probes.** Nothing is read from Vital's source, which is GPLv3.
   pedalboard's shipped header is read for a fact, as earlier specs read its Python.
4. **Every load that may block is made in a child process under a time limit of 3 s,** counted
   from the child saying it is about to load, as a probe kept in a transcript. "A process of its
   own" is read as: a child the run can kill, never the run's own process. A kept child takes
   many loads, each under its own limit, since a child kept up is a candidate to measure.
5. **Alert windows are announced and waited for.** Before each probe run the owner is told how
   many alerts will show and for how long, and the run starts only at the owner's word.
6. **No gate file changes and no new dependency.** The probes and any remedy use the standard
   library. A remedy that needs a dependency stops the spec: a gate spec comes first.
7. **The mechanism is recorded in `agent-os/standards/vital/plugin-state.md`, from the shipped
   code,** and not in `tech-stack.md`. Nothing under `agent-os/product/` is touched.
8. **No test may hang the gate.** A test of the remedy uses a stand-in that blocks, or a child
   the test itself can kill under a time limit. No test gives Vital, in the test's own process,
   a text it may not return from.
9. **A remedy that only works on macOS is said to be so,** with what other platforms then get.
   Only arm64 macOS with a logged-in screen can be probed here, and a claim that rests on that
   says so.
10. **Counted where it can be, a labelled sample where it cannot;** expected values from
    primitives; every transcript on a still tree, its tree and machine printed before and after.
11. **An issue or a base proposal this spec drafts is shown whole and filed only at the owner's
    word,** after the gate's clean run, with no attribution.
12. **The uncommitted record of fromtheoutfit/patchbay#26** in
    `agent-os/specs/2026-11-15-1448-the-instrument/shape.md` is left as it is and listed apart
    from this spec's change sets at the end.

## Context

- **Visuals:** None.
- **References:** the probe scripts of the instrument spec; `host.py`'s floating-point guard;
  the fake plugins of the unit tests; `load_patch`'s rollback; pedalboard 0.9.26's shipped
  header, for one fact. `references.md`.
- **Product alignment:** the remedy is the adapter's own, in the host. `mission.md` and
  `tech-stack.md` are not touched. Anything the probes show core's contract cannot promise is
  drafted as an issue for fromtheoutfit/patchbay and shown to the owner, not filed.

## Standards Applied

**Core (always applied):**

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**

- `vital/plugin-state` — holds the measured fact the remedy changes, and will hold the
  mechanism.
- `vital/instrument` — the guard, the two-load rule, the rollback and the lost step, the model
  as the source of truth.
- `vital/measures` — counted, an expected value from primitives, a tolerance with its probe.
- `vital/preset-tests` — "no test giving Vital a text it may not return from", which the tests
  of the remedy keep or restate.
- `base/testing/tests` — where a test lives, the mirror, one `conftest.py` at most.
- `base/process/verification-gate` — the gate run and its transcript; the harness rerun when a
  file is added under a directory it copies; no gate file changed outside a gate spec.
- `base/process/standards-retrospective` — the gate's last step; a base change proposed, never
  edited here.
- `base/process/ownership` — no commit, push or pull request by an agent.

## The probes

Five kept transcripts, each on a still tree with its tree and machine printed before and after,
each ending "the tree after the run is the tree before it". Vital 1.6.4 through pedalboard 0.9.26
on arm64 (Apple M4 Pro, macOS 26.6.2), in a logged-in session with a screen. A load that may
block was made in a child the run could kill, given 3 s from the child's word.

| Transcript | Run on | What it is |
|---|---|---|
| `verification/probes-1-costs.txt` | 2026-11-16 16:47 | Run 1: what a trial in a child costs; what a read after a load detects |
| `verification/probes-2-alert.txt` | 2026-11-16 16:55 | Run 2: the alert itself; a load under each of two watches |
| `verification/probes-3-counts.txt` | 2026-11-16 18:55 | Run 3: the loads from a second thread; stopped at the first text that killed its child |
| `verification/probes-3-crash-reports.txt` | 2026-11-16 19:00 | What macOS's crash reports say of run 3's 13 dead children, read after it |
| `verification/probes-4-counts.txt` | 2026-11-16 19:45 | Run 4: the wide counts under the watch, a crash counted as a verdict |

The texts of runs 3 and 4 are 335: the 20 of the instrument spec's section 5, and 315 generated,
each the start preset with one value inside one section replaced by another JSON type, removed,
or its array made one entry shorter or longer, to 8 levels below the section, each array through
its first entry. The package's writer can write 284 of them and the guard passes 252 of those.
Each changes one value: a text with two faults, or a fault in a later entry, was not tried.

### Three behaviours, not two

Run 4, each text in a fresh child, the start preset loaded twice and then the text twice:

| What Vital does | Texts of 335 | The writer can write and the guard passes |
|---|---|---|
| Its alert: the block | 249 | 190 |
| The child dies of a signal: the crash | 3 | 2 |
| Neither | 83 | below, "The silent class" |

- **The verdict is the text's, not the instance's.** The same in the fresh child and on one
  instance after each of three histories (the start preset twice; every parameter set to an end
  of its range, a short render and the start preset twice; an older installed preset twice) on
  334 of 335. The one that differs, `lfos[0].powers: removed`, alerts on both loads in a fresh
  child and on the first alone after each history. Counted from the transcript's table, the
  first load's verdict is the same in all four on 335 of 335.
- **pedalboard raises on none of them:** 0 of 1,328 reported text-and-source pairs. An alert
  that is ended leaves the load returning with no error.

### The alert itself (run 2, 2a and 2b)

- 3 of 3 unwatched loads on the main thread did not return within 3 s. Each child was gone 11 ms
  after the kill.
- **Nothing in Python runs while the alert waits.** A thread wrote a tick every 100 ms and a
  `signal.setitimer` handler an alarm every 250 ms: 10 and 4 in the second before the load, 0
  and 0 after it began. pedalboard 0.9.26's `preset_data` setter holds the GIL through the
  plugin's call (its shipped `ExternalPlugin.h`, read for the fact).
- The alert is one window of about 294 by 246 at layer 0, on screen from about 130 ms after the
  load began until the kill. Its process was the front application at 0 polls: it does not take
  the focus.

### A trial load in a child process (run 1)

- **A fresh child:** 2,379 ms from start to verdict on the start preset (the median of 10; 2,332
  to 2,462), of which `VitalHost()` is 2,193 ms; 2,928 ms on the largest installed preset, 10.1
  MB. A labelled sample.
- **A child kept up:** ready 2,308 ms after it was started; 497 MiB resident once ready and 967
  MiB after 231 trials. Its round trip is the two loads themselves: less the same two loads
  made in-process, a median of 0.0 ms over the 77 texts and at most 6.8 ms. So a trial costs
  one more double load: 8.9 ms on the start preset, 496 ms on the largest.
- **Replacing a kept child after a kill:** it answered 2,283 ms after it was started (run 2).
- **The floating-point environment:** the parent's `fegetenv` bytes the same after a trial as
  before it on 231 of 231; the child's own after its two loads through `VitalHost` on 231 of
  231.
- **A time limit:** the slowest single load of the 77 good texts is 245 ms.
- **Its own alert** is as above: on screen until the child is killed.
- **Whether a text it passes can still block the parent:** none seen. The first load's verdict
  is the same in a fresh child and after three histories on 335 of 335.
- **The two-load rule applies to it.** `random_values` one entry longer returns clean from its
  first load in all 14 of its children and dies in its second; a trial of one load would pass
  it every time.
- **The crash, which only it reaches at all:** see "The crash" below. Of the three texts, two
  die in the first load of every child. The third slipped once.

### A watchdog that ends the alert's modal loop (run 2, 2d)

- **From Python at all:** not from a thread and not from a signal handler, by the counts above.
  Yes from a timer armed beforehand: an `NSTimer` of interval 0 on the main run loop, in
  `NSModalPanelRunLoopMode` alone, whose target is the application and whose selector is
  `abortModal`, made through `ctypes` and the Objective-C runtime with the standard library
  alone. Whether it fired is read from the timer afterwards.
- On the 11 texts that never returned in section 5: the load returned on 11, in 79 to 92 ms;
  the timer fired on 11; pedalboard raised on 0. On 154 loads of the 77 good texts it fired on
  0. Arming it and taking it down costs a median of 78.6 microseconds a load.
- A window of the child of 4 by 4 (once 6 by 6, once 6 by 4) was on screen at 2 to 4 polls per
  child. The alert's own size was seen at none.
- Its wide counts were not made: runs 3 and 4 used the other watch.
- macOS only: it is AppKit's. Nothing was probed on another platform or in a process with no
  screen.

### Something else the probes suggested: the alert answered before it opens (runs 2 and 4)

For the length of the load, `-[NSAlert runModal]` is replaced by a function that records the
call and the alert's two texts and returns `NSAlertFirstButtonReturn` at once; then the method
is put back.

- On the 11 texts: returned on 11 in 56 to 80 ms, an alert answered on 11, pedalboard raised on
  0, **no window of the child on screen at any poll.** The alert's words, the same pair on all
  11: "Error opening preset" / "There was an error open the preset. Preset file is corrupted."
- On 154 loads of the 77 good texts it answered 0. Putting it in and taking it out costs a
  median of 31.5 microseconds a load (18.7 to 47.7), and the method is the application's own
  again afterwards.
- **The wide counts (run 4):** 383 children, none killed by the run, so no load failed to
  return; no window of any child at any poll, and no window of any other process new since the
  run began at any of 80,333 polls. A load in which an alert was answered took 7.2 to 91.3 ms
  in the fresh children, a median of 44.8.
- **What it leaves in the process (the soak, a labelled sample):** 500 rounds of an alerting
  text and the start preset twice, in 8.9 s. An alert was answered on 500 of 500 and on 0 of the
  1,000 good loads. The application's own count of its windows went from 0 to 500, while the
  window server listed none of the process's, on screen or off: one unshown window object for
  each answered alert. Resident memory went from 603 to 701 MiB over the 1,500 loads; the
  alerts' share of that was not separated from the loads'. A good text then loaded and a note
  rendered at 100.0% of its RMS before.
- It replaces a method for the whole process while a load runs. macOS only.

### The plugin's state after a load a watch ended

The same under both watches on the 11 (run 2), and counted wide under the second (run 4, the
history `older`).

- **It is left part-loaded.** Of the 249 texts that alert, both markers were already at the
  text's value on 246, and at least one section had been changed by the load on 245.
- **The next load of a good text on the same instance works.** After the start preset loaded
  twice, every one of the 903 floats is the start's and every section that of a plain double
  load: 332 of 332 texts whose child reported, in each of the four sources. After one load
  alone, the 903 floats were already the start's on 11 of 11 (run 2).
- A note rendered afterwards has 100.0% of its RMS before, 11 of 11 under each watch. The same
  text loaded again is ended again, 11 of 11.
- This was measured with the start preset as what is put back. An installed preset as the model
  is the remedy's own count to make.

### Something else run 2 suggested, and run 3 ruled out: the load from a second thread

Run 2's 2c saw an unwatched load return: a blocking text loaded from a thread that is not the
main one raised. Run 3 made it again, wider, the owner off the keyboard and mouse.

- 11 of 11 returned, in 42 to 60 ms, each raising `PluginStateError: plugin state: Caught an
  unknown exception! (from RuntimeError: Caught an unknown exception!)`. No window at any poll.
- **What raised it:** AppKit's `NSInternalInconsistencyException: NSWindow should only be
  instantiated on the main thread!`, thrown under `-[NSAlert init]`, called from Vital's
  `juce::OSXMessageBox::getRawResult` under `juce::AlertWindow::showNativeDialogBox` under
  `SynthProcessor::setStateInformation`, on all 11, as the Objective-C runtime's exception
  preprocessor recorded it on the throwing thread. It is the same alert, refused there.
- **The host's parameter reads go stale.** After such a load the state's text shows the text's
  floats taken on 8 of the 11, but `host.get` had not moved on any, markers 0 of 2. The same
  on the control text: a good text loaded from a second thread leaves them stale too.
- A good text then loads on the main thread, 11 of 11.
- **The process does not survive.** 11 of 11 children died of SIGTRAP at the render that
  followed, on the main thread, in AppKit's
  `___NSAssertMainEventQueueIsCurrentEventQueue_block_invoke` under pedalboard's event pump, by
  the system's crash reports. The control child, whose load did not raise, rendered at 100.00%.
- So a load is made on the main thread or not at all.

### The crash

Three of the 335 texts kill the process inside Vital's own reading of the text. Each is an
array one entry longer than the start preset holds.

| Text | Dies in | Where, by the crash reports | The guard today |
|---|---|---|---|
| `custom_warps`: one entry more (4) | its first load | `LineGenerator::render` under `LineGenerator::fromJson` under `LoadSave::jsonToState` | passes |
| `random_values`: one entry more (4) | its second load | `va::Value::set` under `LoadSave::jsonToState`; once in the plugin's destructor | passes |
| `wavetables`: one entry more (4) | its first load | `WavetableCreator::jsonToState` under `LoadSave::jsonToState` | refuses |

- Each killed all 14 of its children (the fresh one, the three histories' instances, 10 more
  fresh ones): 42 deaths, SIGSEGV 38 and SIGBUS 4.
- **`random_values` is the case a trial cannot fully vouch for.** Its first load returns with no
  alert in all 14. In 13 the second load kills. In 1 of its 11 fresh children both loads
  returned and the child reported, then died at exit in the plugin's destructor.
- The system wrote a crash report for 16 of the 42, so the places above rest on those 16.
- The other arrays made one entry longer or shorter did not crash; `verification/arrays-seen.txt`
  lists each with its verdict, and the arrays not tried.

### The silent class, and the issue's second question

Run 1 on the 77 good texts and section 5's four; run 4 on the 83 texts that raise no alert and
kill no child, each loaded twice over an older installed preset so that a section kept from
before is told from one that was read.

- **A load ignored whole is detected by a marker.** One parameter is set first to a value the
  text does not hold. After the two loads every marker had moved, and read the text's value
  exactly, on 77 of 77 good texts, and on 77 of 77 when the text was loaded over itself. On
  `synth_version` 99.0.0, 0 of 2 moved. Planting and reading two markers costs a median of 156
  microseconds, and the two-load result is the same with them as without: none of the 903
  floats off on 66 texts and 46 on 11, text by text, 77 of 77.
- **An alert that was ended is not detected by a read.** The floats are already the text's
  (above). The watch itself is what tells.
- **A section can be read back only where the state holds it as the text does.** On the 77 good
  texts that is `custom_warps`, `lfos`, `modulations` and `random_values`. `sample` differs on
  77 and `wavetables` on 75.
- **Of the 83:** 1 is ignored whole (`synth_version` 99.0.0). Of the 82 that load: a changed
  section is kept from the preset before on 9; made into something the read cannot name on 41;
  read as the unchanged one on 16; not told apart on 3; held as the text gives it on 10; and 3
  change no section. A check of the four sections flags 32 of the 82, for a state read and a
  parse of 0.9 to 54 ms. `wavetables` and `sample` cannot be checked, so the 31 texts where one
  of those was made into something are not told from a faithful load.

### Four mislabels in the transcripts, each the driver's and none the measurement's

The transcripts stay as they were written. The fourth is in a transcript of the remedy, not of
the probes, and is kept here with the others at the owner's word.

1. **Run 2, 2d and 2e.** Each child's "the screen" line says its times are "after the load
   began". They are measured from the child's last said load, the text's second, not its first.
   The counts of polls and the window sizes are not affected.
2. **Run 3.** Its stop line says "A LOAD DID NOT RETURN within 3 s" for text 27. The same line
   says "killed by the run: False; its exit -11": the child died of SIGSEGV during the load.
3. **Run 4.** For `random_values` one of the 10 more fresh children is given the verdict `!!`,
   "the child died before the text's first load was said". The driver drops a dead child's
   result and reads an empty list of pending loads so. That child had reported both loads
   returned and died at exit: its crash report's stack is the plugin's destructor. So the
   summary's "in some and not others: 0" counts deaths at any time; by death during a load,
   that text is 10 of its 11 fresh children.
4. **`marker-count.txt`.** Its line "the check's share, the medians apart" (409 and 601
   microseconds) is not the difference of the two medians printed beside it: the driver took
   the upper of the two middle values there. The medians are 43.0 ms with the check and 42.6
   without under one history, 53.7 and 53.9 under the other: the check's cost is inside the
   spread of a load's time, and that run does not measure it. Run 1's 156 microseconds for two
   markers, the text's decode apart, is the one figure that was measured.

### An observation, no cause claimed

In run 4 the pass that sets every parameter to an end of its range before each text took about
10.2 s a text, the child idle in pedalboard's event pump at one sample of it. Issue #8's probe
set and got all 903 in 55 ms.

## The owner's answers during the probes

2026-11-16, by AskUserQuestion. In the owner's words.

**Run 2**, to "Start run 2": "1. Start run 2 now; I will keep off the keyboard and mouse until
you say it has finished. Conditions:
- The transcript prints its tree and machine, and for each load whether it returned, after
  how long, and whether its child was killed.
- If any load returns in a way that looks like a dismissal by hand (an unwatched alert that
  returns before its 3 s kill), say so and rerun that part at my word; do not explain it away.
- When the run ends, show that no Python child of it is still alive and no alert is left on
  screen, before presenting figures.
- For each watch, report what state the plugin was in after a load it ended: whether the
  next load of a good text on the same instance works, and what the diagnostic read holds."

**The unwatched load that returned (2c)**, to "At the head of run 3": "1. Conditions for the
second-thread part:
- Say before it starts the worst-case number of alerts and how long each can stay up; any
  load that has not returned in 3 s is killed, and the 335-text pass stops at its first.
- For each of the 11 texts in a fresh child: returned or not, after how long, what was
  raised with its full text, and whether any window showed at any poll.
- After each load that raised: the plugin's state by the diagnostic read, as run 2 reported
  it for the watches (floats taken, sections changed), then whether a good text loads and
  a note renders as before.
- Say what raised it if the probes can show it (a stack or sample of the child at the
  raise), and whether the child survives it every time: a crash or abort in any child is
  counted and reported, not retried.
- This is named in the presentation as a remedy the probes suggested, not one of the
  issue's two.
- The 2d/2e mislabel goes in shape.md as you proposed; the transcript stays as it is."

**Run 3**, to "Start run 3": "1. Start run 3 now, under caffeinate; the laptop is plugged in
with the lid open. Conditions:
- Say in the terminal when the second-thread part has ended, with its clock time, so I know
  when I can use the machine again. Until then I keep off the keyboard and mouse.
- The transcript prints its tree and machine at the start and the tree again at the end; if
  the tree moved, rerun and do not explain.
- If the run stops at a load that did not return, report that text and what was on screen,
  and ask before running anything further.
- For the soak: after the 500 answered alerts, the process's memory and open windows beside
  what they were before, and whether a good text then loads and a note renders as before.
- At the end, show that no child is alive and no window is left, then stop and present every
  candidate before any remedy is written."

**After run 3 stopped**, to "Run 4, crashes counted": "1. Start run 4 now, under caffeinate,
laptop plugged in with the lid open. Conditions:
- A child that dies during a load is a verdict with its signal, counted, not retried within
  the pass. Where a one-instance pass restarts after a text that killed it, the transcript
  marks the restart, since the texts after it meet a shorter history.
- Every text that crashed in any pass is then loaded again in 10 fresh children each, and
  the count of crashes of 10 is reported: a text that crashes only sometimes is the case a
  trial load cannot vouch for, and I want to know whether any exists.
- For each text, the verdicts across the fresh child and the three histories are set side
  by side, and every text whose verdict differs between them is listed by name, not only
  counted.
- The crash reports' stacks are grouped by where in Vital they crashed, with how many texts
  each group holds.
- The soak and the silent class are measured as run 3 planned them.
- The transcript prints its tree and machine at the start and the tree again at the end; if
  the tree moved, rerun and do not explain. At the end, show no child alive and no window
  left, then stop and present every candidate before any remedy is written.
- The presentation says, for each candidate, which of the three behaviours it covers: the
  block, the silent ignore, the crash."

## The owner's answers after the probes

2026-11-16, at the stop, by AskUserQuestion. In the owner's words.

**The block**, to "Answer the alert": "1. Conditions:
- The method is replaced only for the length of the state write and restored in a finally,
  as the float environment guard is; a unit test with a stand-in holds that it is restored
  when the write raises, and that nothing is replaced outside a write.
- If the replaced method is entered by anything other than the load's own alert during the
  write, say what happens; if that cannot be told apart, say so in the standard as a limit.
- The rollback after an answered alert is shown with an installed preset as the model, not
  only the start preset: all 903 floats and every section back after the two loads, counted
  over the 75 installed presets locally, as a kept transcript.
- If the rollback itself fails, the instrument has lost step, as today; a test holds it.
- The main-thread refusal is the package's own named error, raised before the plugin is
  called, changing nothing; a unit test holds it with a stand-in host on a second thread.
- On a platform that is not macOS, and in a process with no screen, the host does what it
  does today; README, CHANGELOG and plugin-state.md say the block still stands there, and
  the standard records what was not probed.
- plugin-state.md records the measured costs as limits: one unshown window object and the
  memory growth per refused load (from the soak's figures), and the process-wide swap.
- No test sends Vital a text that may block. The remedy's tests use a stand-in that blocks
  or a child the test can kill; the 249 stay in the transcript.
- Standard library only, through ctypes. If it turns out to need anything else, stop: that
  is a gate spec first."

**The crash**, to "Guard the two, draft an issue": "1. Conditions:
- Before writing the guard, list from run 4's transcript every array the 315 texts made one
  entry longer and one entry shorter, with each one's verdict, and every array in a preset
  the package can see that was not tried either way. The untried ones are named in the
  drafted issue; none is guarded on a guess.
- The guard refuses any length but the one Vital holds, shorter as well as longer, if the
  transcript shows a shorter one is not loaded faithfully; if it shows a shorter one loads
  whole, say so and leave it.
- "Present" is counted: how many of the 75 installed presets hold custom_warps and
  random_values, and in what shape. All 75 still pass the guard, as a test over the
  committed manifest locally and the fixture in CI.
- The tests need no Vital: the guard is given the preset and refuses before the plugin is
  called. No test sends Vital a text that crashed it; those stay in the transcript.
- random_values is recorded in plugin-state.md as it was measured: the first load returns,
  the second kills, and once in 11 the child died only at exit. That is further evidence
  for the two-load rule and is said there.
- The drafted issue states the counts (3 of 335, where in Vital each crashed, 16 of 42
  crash reports written), that the texts tried changed one value each, and the trial
  child's measured cost and its one slip, as the candidate that issue would probe. I read
  it whole before it is filed.
- README, CHANGELOG and the instrument's docstring say plainly that a text Vital crashes on
  kills the calling process, and that only the shapes found are refused."

**The silent ignore**, to "The marker check": "1. Conditions:
- The marker is a host matter only: it is set on the plugin, never in the model, publishes
  no event, and is not visible through get or patch at any point. A unit test holds that
  the model and the bus are untouched by it on a load that succeeds and on one that fails.
- The marker's value is one the parameter holds exactly and differs from the text's own
  value for that parameter by more than a set can blur; how it is chosen when the text holds
  the first choice is stated and tested, with expected values from primitives.
- Counted locally over the 75 installed presets and the fixture: the marker moves on every
  good load and the two-load result is the same with the check as without it (all 903
  floats and every section), as a kept transcript.
- A load that left the marker raises PluginStateError saying the load was ignored, and
  goes through the same rollback as an answered alert. If the rollback's own load leaves
  the marker too, the instrument has lost step; a test holds both with a stand-in plugin
  that ignores loads.
- The check runs on every platform, since it needs no AppKit; say so, and say it was
  measured on macOS only.
- The section check is recorded in plugin-state.md as measured and not built: 32 of 82
  flagged, its cost, and that wavetables and sample cannot be read back. The 82 silent
  texts and what Vital made of them are named as a second open class in the issue drafted
  under the crash question, or in one of its own if that reads better; I read it first.
- The docs say plainly what remains: a text Vital loads in part, keeping sections it had,
  is not detected."

## Decisions made on the probes

13. **The block is remedied in the host, on macOS, by answering the alert before it opens.**
    For the length of each state write `-[NSAlert runModal]` returns at once, put back in a
    `finally`; a write in which an alert was answered raises `PluginStateError` with the alert's
    own words, and `load_patch`'s rollback applies. Through `ctypes`, standard library alone.
14. **A load is made on the main thread or refused,** on macOS, by an error of its own,
    `PluginThreadError`, before the plugin is called. It is not a `PluginStateError`, so
    `load_patch` does not answer it with a rollback: nothing was touched.
15. **Elsewhere the host does what it does today.** On a platform that is not macOS the block
    stands, and the docs say so. Nothing was probed there, nor in a process with no screen.
16. **A load is checked with a marker,** in the host: one parameter is set before the write to
    an end of its range the text does not hold, and read after it. A write that left it there
    raises `PluginStateError` saying the load was ignored. The model, the bus, `get` and `patch`
    never see it.
17. **The guard also refuses `custom_warps` and `random_values` that are not arrays of three
    objects,** where the preset holds them: longer kills the process, and shorter or empty is
    not loaded as given. Only what `verification/arrays-seen.txt` shows was tried.
18. **The trial child is not built.** It is the one candidate that reaches a crash, at 2.4 s a
    load fresh or a second Vital kept up, and it slipped once in 11. It goes to an issue.
19. **One issue is drafted for what stays open,** shown to the owner whole and filed only at the
    owner's word: the texts not yet found that crash Vital, with the arrays not tried; and the
    silent class, a text loaded in part. The section check is recorded as measured and not built.
20. **Files are changed, none added,** under `src`, `tests`, `scripts` and
    `agent-os/standards`: the watch lives in `host.py` beside the floating-point guard it is
    shaped like. So the gate's negative harness is not rerun. If a file has to be added, it is
    rerun and this decision corrected.

## The remedy as built, and the evidence on it

Built 2026-11-17 as Decisions 13 to 20 say. Changed, none added: `host.py`, `errors.py`,
`patch.py`, `instrument.py`, `__init__.py`; `tests/unit/` (`test_host.py`, `test_instrument.py`,
`test_errors.py`, `test_package.py`, `builders.py`); `tests/integration/`
(`test_vital_instrument.py`, `test_factory_round_trip.py`); `README.md` and `CHANGELOG.md`.

### What the owner should know of the build

- **The marker needs the map.** The host finds the marker's hosted parameter and the text's key
  for it through the map, so where the map is not the plugin's (another machine, another Vital)
  a load is made unchecked, as before. The check needs no AppKit; the committed map is arm64's.
- **`PluginThreadError` is its own class under `VitalHostError`,** not a `PluginStateError`.
  `load_patch` answers a state error with a rollback; a load refused for its thread touched
  nothing, and a rollback from that thread would be refused too and mark the instrument lost.
- **A deviation from the plan:** "the new tests failing on the code before the remedy" cannot be
  shown. They import names that code lacks and are not collected: 3 errors at collection, which
  `mutation.txt` records. In its place each rule of the remedy is broken once.

### The evidence, each a kept transcript on a still tree, run 2026-11-17 08:46 to 09:35 EST

| Transcript | What it shows |
|---|---|
| `verification/arrays-seen.txt` | Run before the guard was written. 12 arrays made one entry longer and one shorter, with each verdict; 6 of the 18 arrays in the 77 texts on hand never tried; `custom_warps` and `random_values` held by the start preset and the fixture as arrays of 3 objects and by none of the 75 installed presets; the guard as it stood passing 77 of 77 |
| `verification/mutation.txt` | The copy unchanged: 649 passed. 16 mutants, each one change to the shipped source: 16 caught by every test named for them |
| `verification/marker-count.txt` | The fixture, the start preset and the 75 installed presets, under two histories |
| `verification/rollback-count.txt` | Each of those 77 as the instrument's model, then a patch of it Vital answers with its alert |
| `verification/remedy-run.txt` | Run 4's 335 texts through the package as shipped, each in a child |
| `verification/silent-and-loaded.txt` | Read from run 4's and the remedy run's tables, no plugin: of the 83 texts that raised no alert, which the shipped guard refuses, which still load, and what Vital made of those |

- **The marker (`marker-count.txt`).** After each of 154 checked loads it read the text's value,
  under each history, and no load raised. With the check as without it: all 903 floats the same
  on 77 of 77 texts and every section the same on 77 of 77, under each history. Floats not the
  text's after two checked loads: none on 66 texts and 46 on 11, issue #8's count.
- **The rollback (`rollback-count.txt`).** 77 of 77 models: `PatchRefusedError`, chained from
  `PluginStateError`, with Vital's words. After it the plugin against what the model's own double
  load had left: all 903 floats the same on 77 of 77, every section the same on 77 of 77, and the
  model the preset still on 77 of 77. No child died and no window showed. The refused call,
  with the two loads that put the model back, took 81.6 to 580.3 ms, a median of 171.8.
- **The 335 texts (`remedy-run.txt`).** No load failed to return, no child died and no window
  showed. Beside run 4's verdict for each text there is no disagreement:

  | Run 4 saw the text | The shipped package | Texts |
  |---|---|---|
  | kill its child | refused by the guard | 3 |
  | raise Vital's alert | refused by the guard | 28 |
  | raise Vital's alert | refused once the alert was answered | 221 |
  | raise no alert | refused by the guard | 19 |
  | raise no alert | loaded | 64 |

  After a refusal the plugin held every float and every section as before: 50 of 50 the guard
  refused, 180 of 180 refused through the instrument, and 41 of 41 through the host once the
  start preset was loaded twice. No text reached the marker's refusal there: the one text Vital
  ignores, the guard refuses first. The marker's refusal against Vital is the integration
  test's, in a child.
- **What still loads (`silent-and-loaded.txt`).** Of the 83 texts that raised no alert, the
  shipped guard refuses 19, the one ignored whole among them, and 64 still load: 54 given to the
  instrument as a patch, and 10 the package's writer cannot write, given to the host. Of the 64:
  10 hold the changed section as the text gives it and 3 change no section; 15 hold it as the
  unchanged one; 1 keeps it from the preset before; and 35 hold something the read cannot name,
  25 a wavetable, 6 a custom warp, 2 an lfo and 2 the sample. The transcript names each.
- **The whole suite,** run after them: 859 passed in 90 s, the two tests that give Vital a text it
  does not take among them, each in a child given 20 s.

### The four evidence runs and the final tree

`mutation.txt`, `marker-count.txt`, `rollback-count.txt` and `remedy-run.txt` ran on the tree
each prints, from 08:46 to 09:35 EST, **before issue #25 had a number.** The four print one
tree. What was written to the tree after them:

- the three standards and the index, the retrospective's;
- the number, into the README, the changelog, two standards and three docstrings: the module's
  in `host.py`, the module's and `load_patch`'s in `instrument.py`, and `check_loadable`'s in
  `patch.py`;
- beyond the number, one correction made while the docs were read for step 7. The README's
  bullet on a load Vital ignores, and the same bullet of `instrument.py`'s docstring, now say
  that the guard refuses a preset newer than the plugin first and the marker stands behind it,
  as the owner had the issue say. No statement of code changed.

**`verification/tree-since-the-evidence.txt` is what ties the four to the final tree,** at the
owner's word and under the owner's conditions, which are quoted below. It ran on 2026-11-17 at
10:38 EST on a still tree, loads no plugin and runs no test.

- **Every path that differs between the two trees is listed: 15 of the 34 either tree names.**
  - Code, 3: `host.py`, `instrument.py` and `patch.py`.
  - Not code, 12: the README, the changelog, the three standards and the index, and 6 in this
    spec's folder, this file and five transcripts copied in since.
  - Anything else: 0.
  - The other 9 files under `src/` and `tests/` have the same blob in both trees.
- **The three code files have equal syntax trees, docstrings left out:** 3 of 3, the lines of
  text that differ printed for each. A file's text then is a copy set aside before the number
  was written, and is used because its blob is the one the four transcripts print.
- **The method is stated in the transcript.** Each text is parsed whole by `ast.parse`, which
  keeps no comment and no layout. The string Python keeps as `__doc__` is dropped from the
  module and from each class and function, by `ast.get_docstring`'s rule. What is left is
  compared as `ast.dump` writes it, without line numbers.
- **It is shown to tell,** on copies of `host.py` as it was then. A docstring changed and a
  comment added compare equal. A number changed, the words of a raised message changed and a
  statement added each differ.
- **Nothing reads a docstring.** All 35 `.py` files git lists under `src/` and `tests/` were
  parsed and searched for `__doc__`, for calls that read a docstring or a source, for imports
  of `inspect`, `pydoc` and `doctest`, and for a string used as a value that could name a file
  that differs. Found, and neither a reader: `census.py` gives its own module docstring to its
  argument parser, and `census.py` does not differ; `test_package.py` imports `inspect` and
  uses `signature` and `Parameter` of it. The gate's pytest runs with `-p no:doctest`.
- **After that transcript only this folder changes:** the transcript itself, copied in, this
  file's records, and `gate-run.txt`. The gate's transcript prints the tree it ran on, and the
  gate's results, below, compare the two.

**The first try of that script ended in STOP and was not kept.** Recorded here at the owner's
word. It was run by hand to see that the script ran, not through the wrapper that writes a
transcript, so no file holds it; what follows is what it printed, read at the time.

- **What it stopped on.** Its sections 1 to 5 gave what the kept run gives: 15 paths differing,
  3 of them code, none of another kind, and 3 of 3 syntax trees equal. Its section 6, the
  search for readers, printed 5 hits and counted 2 of them as strings that name a file that
  differs. That count not being 0, it printed STOP and exited 1.
- **The two it counted** are bare strings, each a note written as a statement under a constant:
  - `src/patchbay_vital/census.py`, line 75, under the table of suffixes and units, whose
    words end "(the host spec's shape.md, Decision 13)";
  - `tests/unit/test_parameters.py`, line 261, under `_SHARED`, whose words hold "(the sixth
    review's shape.md)".

  Each holds `shape.md`. The search matched a file that differs by its name alone, and this
  file's name is `shape.md`.
- **What was narrowed, and why.** The search now tells a string that is a value from a string
  that is a whole statement, and counts only a value towards "could read a file that
  differs". A string that is a whole statement, and not the first of its body, is kept nowhere
  by Python, not as `__doc__` and not as anything a call can be given. Only a reader of the
  source's own text could see it, and the search looks for those apart: none. Such strings are
  still printed and counted, as what they are: 80 in the 35 files, 3 of them holding one of
  the five things sought.
- **The syntax-tree comparison was not changed.** Sections 3 and 5, with the five controls,
  are the same code in the try and in the kept run, and the comparison keeps those strings
  and compares them.
- **One more run was replaced.** The first run in transcript form ended as the kept one does,
  exit 0, and printed the interpreter's whole path, the home directory in it. That line was
  changed to say whether the interpreter is the repository's own, and the run made again
  whole; the second overwrote the first.
- **The owner's rule, from here on:** "a first try that stops is kept beside the one that
  replaces it, as gate-negative-tests-first.txt was."

### An observation that now has its place

The fourth mislabel, in `marker-count.txt`, is with the other three, above. The 10 s a text
that run 4's `sets` pass took is the render: `marker-count.txt` times the
history's 903 sets at 27.1 to 45.1 ms and its render of 4,800 samples, made after every
parameter is set to an end of its range, at 10,054 to 10,419 ms, over 154 renders. A fact about
a render, for issue #21, and no cause is claimed.

**Issue #21 was revised in place on 2026-11-17,** at the owner's word, its body kept and a
section added at its end. Read back from GitHub, the body is the text sent, character for
character, and begins with the body as it was. The section:

> ## Revised 2026-11-17
>
> After every parameter is set to an end of its range, a render of 4,800 samples took 10,054 to
> 10,419 ms over 154 renders, where the 903 sets before it took 27 to 45 ms. Measured on Vital
> 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2) by the spec of issue #20:
> `agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/verification/marker-count.txt`, on
> branch `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`.
>
> No cause is claimed. Whether it is the same mechanism as the opening sound or a separate one is
> for this issue's spec to probe.

## The issue drafted for what stays open

Drafted 2026-11-17 for this repository. Shown to the owner whole, twice, and filed at the owner's word.
It carries no attribution. Every figure is from a kept transcript of this spec.

**Filed 2026-11-17 as fromtheoutfit/patchbay-vital#25,** as it reads below. Read back from
GitHub, the title is the title sent and the body the text below, character for character.

> **Title:** The host: a preset Vital dies on kills the calling process, and one it loads in part
> goes unseen
>
> `VitalHost.load_state` now answers Vital's alert and refuses a load Vital ignores (#20). Two
> things a preset can still do are past it. **A preset Vital dies on kills the calling process,
> and a preset Vital loads in part is taken as loaded.** The instrument refuses the three shapes
> seen to kill and no others, and nothing read back from the plugin shows a wavetable or a sample
> that Vital kept or remade.
>
> ## Evidence
>
> `agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/verification/`, on branch
> `bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`: Vital
> 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). 335 texts, 20 written by
> hand and 315 that change one value inside one section of the start preset, each loaded twice
> in a process of its own under a time limit (`probes-4-counts.txt`).
>
> **The crash**
>
> - **3 of the 335 killed their process,** inside Vital's own reading of the text. Each is a
>   section one entry longer than Vital holds:
>
>   | The text | Dies in | Where, by the system's crash reports |
>   |---|---|---|
>   | `custom_warps` of four | its first load | `LineGenerator::render` under `LineGenerator::fromJson` under `LoadSave::jsonToState` |
>   | `random_values` of four | its second load | `va::Value::set` under `LoadSave::jsonToState`; once in the plugin's destructor |
>   | `wavetables` of four | its first load | `WavetableCreator::jsonToState` under `LoadSave::jsonToState` |
>
> - Each killed all 14 of its children: one fresh, three on instances with a history, ten more
>   fresh. 42 deaths, SIGSEGV 38 and SIGBUS 4. macOS wrote a crash report for 16 of the 42, and
>   the places above rest on those 16.
> - `random_values` of four returns clean from its first load in all 14, and dies in its second
>   in 13. In 1 of its 11 fresh children both loads returned and the child died at exit.
> - **The texts changed one value each.** None had two faults, and none a fault past an array's
>   first entry.
> - Of the 18 arrays the 77 presets on hand hold, 12 were made one entry longer and one shorter,
>   and none but those three killed (`arrays-seen.txt`). **Six were never tried either way:**
>   `modulations[].line_mapping.points` and `.powers`;
>   `wavetables[].groups[].components[].keyframes[].line.points` and `.powers`;
>   `wavetables[].groups[].components[].keyframes[].points` and `.powers`.
>
> **The silent class**
>
> - 83 of the 335 raise no alert and kill nothing. One is ignored whole, a `synth_version` newer
>   than the plugin's: the guard refuses that version before the plugin is called, and behind
>   the guard the host's marker refuses a load that was ignored. The other 82 load. By the state
>   read after each, loaded over an older installed preset:
>   - 10 hold the changed section as the text gives it, and 3 change no section;
>   - 16 hold it as the unchanged one: the change was read past;
>   - 9 keep it from the preset before;
>   - 41 hold something the read cannot name, 28 of them a wavetable and 3 a sample;
>   - on 3 the read cannot tell a kept section from an unchanged one.
> - **Through the package as shipped, 64 of the 83 still load** (`remedy-run.txt`,
>   `silent-and-loaded.txt`). The guard refuses 19, the one ignored whole among them. Of the 64,
>   54 load as a patch through the instrument, and 10 are texts the package's writer cannot
>   write, which only the host can be given. By the same read, of the 64:
>   - 10 hold the changed section as the text gives it, and 3 change no section;
>   - 15 hold it as the unchanged one;
>   - 1 keeps it from the preset before;
>   - 35 hold something the read cannot name: 25 a wavetable, 6 a custom warp, 2 an lfo and 2
>     the sample.
> - Only `custom_warps`, `lfos`, `modulations` and `random_values` come back from the plugin as
>   a good text gives them, on 77 of 77 good texts. `sample` differs on 77 and `wavetables` on
>   75. So a check of those four after a load flags 32 of the 82, for a state read and a parse
>   of 0.9 to 54 ms, and cannot see the 31 where a wavetable or a sample was made into something.
>
> ## What exists today
>
> `patch.check_loadable` refuses `custom_warps` and `random_values` that are not arrays of three
> objects, where a preset holds them, as it refuses `wavetables` that are not three and `lfos`
> that are not eight. None of the 75 presets Vital installs holds either. No test sends Vital a
> text that killed it: those are in the transcript. The README, the CHANGELOG and the
> instrument's docstring say that a text Vital dies on kills the calling process and that only
> the shapes found are refused.
>
> ## Candidate remedies, for this spec to probe
>
> - **A trial load in a child process,** the one candidate that reaches a crash at all. Measured
>   in #20's spec (`probes-1-costs.txt`, `probes-2-alert.txt`): a fresh child for each load costs
>   2,379 ms, 2,193 of it Vital loading. A child kept up costs one more double load (8.9 ms on
>   the start preset, 496 ms on a 10 MB preset), holds 497 MiB once ready and 967 MiB after 231
>   trials, and takes 2,283 ms to replace after it is killed. A text's verdict did not depend on
>   the instance's history: the first load's was the same in a fresh child and after three
>   histories on 335 of 335. **It slipped once:** `random_values` of four passed both loads in 1
>   of 11 fresh children. A trial of one load passes it every time.
> - **A wider guard,** shape by shape: the six arrays not yet tried, texts with two faults, and
>   faults past an array's first entry.
> - **A check of the four readable sections after a load,** for part of the silent class.
>   Nothing reads back a wavetable or a sample.
>
> ## Questions for this spec
>
> - Can a wavetable or a sample that Vital kept or remade be told at all: by a render, or by the
>   state read twice?
> - What does a caller get when a trial child dies: the package's patch error, as for an
>   answered alert?
>
> ## Rules
>
> Shaped in plan mode with `/agent-os:shape-spec`. It does not come before the first experiment
> that puts an agent in front of the instrument: that experiment changes parameter values and
> writes no section, and every text seen to kill or to load in part has a fault inside a
> section. It comes before any experiment in which an agent writes a wavetable, an lfo shape or
> a sample. Every load that may kill or block is made in a process of its own with a time
> limit, as a probe kept in a transcript, never as a test in the gate's own process. The
> measured facts are in `agent-os/standards/vital/plugin-state.md`; the remedy changes them.
> CHANGELOG; gate green. No commit, pull request or push by an agent.

The sentences on where it sits are the owner's, word for word (2026-11-17).

## The owner's answers on the evidence, the standards and the issue

2026-11-17, by AskUserQuestion. In the owner's words.

**The evidence runs**, to "Start them": "1. Start them, under caffeinate, laptop plugged in with
the lid open. Conditions:
- Run the mutation run first, and say in the terminal when its one alert is about to open
  and when it has been killed, with the clock time. I will not click it. After that I use
  the machine normally.
- If any run stops at a load that did not return, report the text and what was on screen
  and ask before running anything further, the test suite included.
- Each transcript prints its tree and machine at the start and the tree at the end; if the
  tree moved, rerun and do not explain.
- The 335-text run through the shipped package reports each text's outcome beside run 4's
  verdict for it: refused by the guard, raised after an answered alert, raised by the
  marker, loaded, or died, and every text where the two disagree is listed by name.
- The rollback run reports, for each of the 77 models, all 903 floats and every section
  after the rollback against a plain double load of that model.
- The two new integration tests each have a time limit of their own and a child they can
  kill; say what that limit is and show that neither can hang the gate.
- At the end, no child alive and no window left, then stop with the counts, the standards
  edits and the drafted issue whole."

The one alert, by design, was under mutant MW4: it began at 08:46:57 and its child was killed at
08:47:15, both said in the terminal.

**The project standards** (`vital/plugin-state.md`, `vital/instrument.md`, `vital/preset-tests.md`,
all three chosen): "1, 2 and 3 approved, each its own change set, index.yml in step. Before
writing:
- plugin-state.md, "what a load can still do", and instrument.md's guard bullet: say how many
  of the 82 silent texts get past the shipped guard. remedy-run.txt has 19 texts with no alert
  refused by the guard and 64 loaded, so the open class through the package is 64, not 82.
  Give the breakdown of what Vital made of those 64, from the transcript.
- plugin-state.md: the breakdown of the 82 must add to 82 and use the same classes and counts
  as the drafted issue (10, 3, 16, 9, 41, 3 there). If the two differ, the transcript decides
  and both are made to match it.
- plugin-state.md, the main-thread bullet: say that a load from a second thread was not
  probed off macOS, where the host allows it, and that the stale parameter reads seen on
  macOS would make the marker refuse a good load there if they occur.
- plugin-state.md, the marker bullet: state no cost for the check beyond the probe's own
  figure with its transcript named, since marker-count.txt does not measure it. The fourth
  mislabel goes in shape.md with the other three.

The drafted issue, before I read it again to file:
- "a synth_version newer than the plugin's, which the host's marker now refuses": the guard
  refuses it first and the marker stands behind it; say it so.
- The silent class gains the same 64 and its breakdown.
- Leave the sentence on where it sits among the issues to me.

Issue #21: add the render fact to its body in place, with a "Revised 2026-11-17" paragraph:
after every parameter is set to an end of its range, a render of 4,800 samples took 10,054
to 10,419 ms over 154 renders, with the transcript named and no cause claimed."

**When the issue is filed**, to "Now, before the gate": "1, once I have read the revised draft
above. Check before filing that it has: the guard refusing the newer synth_version first with
the marker behind it; the 64 silent texts that get past the shipped guard, with their breakdown;
and counts that match plugin-state.md.

Its placement sentence, for the Rules section:
"It does not come before the first experiment that puts an agent in front of the
instrument: that experiment changes parameter values and writes no section, and every text
seen to kill or to load in part has a fault inside a section. It comes before any
experiment in which an agent writes a wavetable, an lfo shape or a sample."

After filing, read it back from GitHub against shape.md's text, write its number into the
README, the CHANGELOG, the docstrings and the standards, and say which files changed."

**Where the issue sits**: "4. Not before the first experiment, with its reason and its limit.
The sentence: [the same sentences as above]."

**The render fact, for issue #21**: "3. Revise issue #21's body in place, not by comment. Add a
paragraph headed "Revised 2026-11-17" with: after every parameter is set to an end of its range,
a render of 4,800 samples took 10,054 to 10,419 ms over 154 renders, where the 903 sets took 27
to 45 ms; the transcript's path and branch; and that no cause is claimed. Say there that it is
for #21's spec to probe whether it is the same mechanism as the opening sound or a separate
one. Read the body back from GitHub afterwards, and record in this spec's shape.md that
#21 was revised and with what."

**Filing the issue**, to "File it as shown": "File it as shown, after checking that the
trial-child bullet's passage ("the instance's history ... A trial of one load passes it every
time") appears once in shape.md's text, not twice. Read it back from GitHub against shape.md's
text and tell me its number.

Do not write the number anywhere yet. Where it goes, and what that does to the transcripts'
tree, is your next question; I answer it there."

The passage was found once in the text to be filed and once in this file, in one bullet.

**The evidence and the final tree**, to "Keep them, show the difference": "2. Conditions:
- The kept transcript lists every file that differs between the tree the four runs printed
  and the final tree, not only the ones you expect. Any file under src/ or tests/ in that
  list has its syntax tree compared with docstrings left out, and the comparison is shown
  equal file by file. The README, the CHANGELOG, the standards and the spec folder are named
  as not code.
- The comparison's own method is stated in the transcript (what is parsed, what is dropped),
  and it is shown to fail on a copy with one changed statement, so an equal result means
  something.
- If any syntax tree differs, or any file outside that list changed, stop: that is a rerun
  of the four at my word, not an explanation.
- No test reads a docstring; say how that was checked.
- shape.md records that the four transcripts ran on the tree before the number was written,
  and names this transcript as what ties them to the final tree.
- The gate then runs on the final tree as usual, with the full suite."

**The base proposals**, by AskUserQuestion after the gate's clean run, the texts to be sent
shown whole.

To the three that refine an open issue, all three chosen: "1, 2 and 3, each by revising its
open issue in place with a "Revised 2026-11-17" paragraph,
never by comment. Conditions:
- Each revision names this spec and branch as its evidence and keeps the issue's earlier
  text; read each body back from GitHub afterwards.
- Proposal 1 is worded for any third party's code, with Vital as the one case seen, and
  says the limit is named in the test and held by a stand-in that never returns.
- Proposal 3 keeps both arms as written: rerun, or the tying transcript with every
  differing path and a failing control. It does not make the tying transcript the default.
- #38 gains two refinements from this spec: keep them as two separate dated items under one
  revision so each can be taken or declined on its own when the batch is written.
- shape.md records the three as sent, with the issue numbers."

To the fourth, the platform rule, "Send the platform rule": "1. Conditions:
- Before filing a new issue, check the open proposals on patchbay-standards and the base
  rule on the native-code float environment guard. If one of them already covers platform
  mechanisms, revise that issue in place with a "Revised 2026-11-17" paragraph and do not
  file a new one; say which you did.
- The proposal cites both cases in this package: the alert watch and the float environment
  guard's two libraries.
- It says three things: the mechanism's selection is itself unit-tested on every platform
  with a stand-in; the platform that has it is tested against the real thing where the gate
  runs there; the docs say plainly what every other platform gets and what was not probed.
- No attribution; read the body back from GitHub; shape.md records its number."

To "may I file them as shown": "1. File as shown, read each back from GitHub, record the
numbers in shape.md. The new issue stands with the alert watch as its one case; do not add the
float environment guard.

One addition to shape.md, not to any issue: the tie transcript's first try ended in STOP and
was not kept. Record what it stopped on (the two bare strings it counted), what was narrowed
in the reader search and why, and that the syntax-tree comparison was not changed. From here
on a first try that stops is kept beside the one that replaces it, as
gate-negative-tests-first.txt was.

Then stop and print git status --short."

**How the second and third of those were read together.** They differ on one point: the second
has the proposal cite the float environment guard's two libraries beside the alert watch, and
the third, given after it, has the new issue stand with the alert watch as its one case and
the guard not added. The third was followed, as the later word and the one that names the
point. The check the second asks for was made first, below. If the second was meant, the
issue is revised in place.

## Decisions made on those answers

21. **The three project standards are edited as approved, with the owner's four corrections,**
    each its own change set, the `vital:` entries of `index.yml` in step. What still loads
    through the shipped guard was counted first, `verification/silent-and-loaded.txt`: 64 of
    the 83, not 82.
22. **The issue is filed before the gate, once the owner has read the revised draft,** so that
    the README, the CHANGELOG, the docstrings and the standards name it by number. It does not
    come before the first agent experiment, in the owner's sentences.
23. **Issue #21 is revised in place,** not commented on, with the render fact and no cause.
24. **The issue is filed as shown,** fromtheoutfit/patchbay-vital#25, once the passage on the
    trial child was found once in the text and once in this file.
25. **The four evidence transcripts are kept, and a transcript of its own ties them to the final
    tree:** `verification/tree-since-the-evidence.txt`, under the owner's six conditions. A
    syntax tree that differs, or a path that is neither code nor one of the four kinds named,
    is a rerun of the four at the owner's word. Neither was found.
26. **The number is written into the README, the changelog, the docstrings and the standards,**
    as the owner's answer of the same hour asked, and nowhere else in the code.
27. **All four base proposals go upstream, as shown:** three by a "Revised 2026-11-17" paragraph
    in the open issue each refines, never by comment, and the platform rule as a new issue with
    the alert watch as its one case.
28. **A first try that stops is kept beside the one that replaces it, from here on.** The tie
    transcript's first try was not, and is recorded under "The four evidence runs and the final
    tree".

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

**The negative harness is not rerun.** No gate file changed, and no file was added, removed or
renamed under `scripts`, `src`, `tests` or `agent-os/standards`, the four directories every
case copies: git's status names every path there as modified, none as new or deleted.

**Results (2026-11-17):** `scripts/gate.sh` exits 0 on branch
`bugfix/20-the-host-a-preset-vital-cannot-read-blocks-the-calling-process-for-ever`, all six
steps, 859 tests passed and none skipped, in 89 s, Vital installed. The record is
`verification/gate-run.txt`: the date and the branch on its first lines, the machine before and
after, the tree before and after by blob, compared with `cmp`. It ran once, at 10:42 EST, last:
after the standards' edits, the number, and every other transcript.

- **The gate ran on the code the tie transcript read.** By the blobs the two print, the 19 paths
  outside this folder are the same paths with the same blobs in both, the 12 under `src/` and
  `tests/` among them. In this folder three paths differ between the two: this file and
  `plan.md`, written between them (in `plan.md`, two phrases naming the owner), and the tie
  transcript itself, copied in.
- **The copy differs from what was printed in one substitution:** the home directory is written
  `~`, on the two lines where the sync's own check prints the sibling checkout's path.
- **The suite's three tests that reach a real alert ran under the watch, in children,** and
  nothing showed on screen.
- **Written after the gate's run:** this paragraph, and the record of the base proposals below
  with their issues.
- No gate file changed: `scripts/`, `.github/`, `uv.lock` and `pyproject.toml` are as `main` has
  them.

**Docs (step 7):** checked on 2026-11-17, each against the shipped code.

- `README.md`, "A patch Vital cannot use": the alert answered on macOS and blocking elsewhere,
  with nothing measured there or in a process with no screen; the load from a second thread;
  the newer preset the guard refuses first and the marker behind it; the crash and the part
  load, each naming issue #25. "Known limits" names the two issues that still wait, #21 and
  #22, and no longer #20.
- `CHANGELOG.md`: step 8, below.
- `CLAUDE.md`: nothing there names what changed.
- The docstrings: `host.py` (the module's section "A load", `load_state`, `MARKER`,
  `_planted`, the three watches), `instrument.py` (the module's "A patch Vital cannot use" and
  "Known limits", `__init__`, `load_patch`), `patch.py` (`check_loadable`), `errors.py`
  (`PluginStateError`, `PluginThreadError`), and the headers of the test modules changed.
- `agent-os/product/` is untouched, as the owner decided at shaping.
- Issue #21, revised in place on 2026-11-17 and read back. Issue #25, filed on 2026-11-17 and
  read back against this file's text.
- A search of the README, the changelog, `src/`, `tests/` and the `vital` standards finds
  no pointer left to "the issue the spec drafted", and #20 named nowhere as still open.
- The standards that name what changed are the retrospective's, below.

**Version (step 8):** `CHANGELOG.md`, `[Unreleased]`, `### Fixed`, first entry: a preset Vital
cannot read no longer blocks the calling process on macOS, issue #20, with what stays, issue
#25's. Under `### Added`, the instrument's entry keeps the limit it recorded for #20 and says
what this spec has since done about it. The version stays 0.0.1; no release is cut.

## Standards Retrospective

Step 9, last. Per `agent-os/standards/base/process/standards-retrospective.md`, from the shipped
code, the tests and the kept transcripts, never from the plan. The three project edits were
shown to the owner on 2026-11-17 and approved with four corrections before any was written
("The owner's answers on the evidence, the standards and the issue"). Each added sentence was
then checked against the shipped files. Every test, identifier, path and transcript the added
lines cite exists, by a search of `tests/`, `src/` and the `verification/` folders: 25 tests, 15
identifiers, 15 transcripts and 4 paths. All 119 tests the three files cite, old lines and new,
exist by name. The mutants they name are in the `mutation.txt` each is said to be in.

**The four questions, against the diff.**

1. **A pattern no standard covers: three.**
   - The watch that answers Vital's alert, through `ctypes` and the Objective-C runtime, in the
     host alone. Now `vital/plugin-state.md`'s.
   - The marker that shows a load Vital ignored. Now `vital/plugin-state.md`'s, with what the
     instrument owes it in `vital/instrument.md`.
   - A test that gives a third party a text it may not return from, in a child it can kill. Now
     `vital/preset-tests.md`'s, and proposed for `base/`, below.
   - **They landed late, and by the owner's condition.** The mechanism could not be named
     before the probes chose it, and the owner had it "recorded in
     agent-os/standards/vital/plugin-state.md, written from the shipped code".
2. **A standard proved stale: three sentences.**
   - `vital/plugin-state.md`: "11 never returned", of 20 texts, is now 249 of 335, with 3 that
     kill and 83 that raise no alert. "A load that cannot block is issue #20's to make" is made,
     on macOS.
   - `vital/instrument.md`: "a malformed section can still hang the process" holds off macOS
     alone.
   - `vital/preset-tests.md`: "No test gives Vital a text it may not return from" gains its
     condition, the test's own process.
3. **A deliberate deviation: none from a standard.** One from the plan, recorded under "What
   the owner should know of the build": the new tests cannot be shown failing on the code
   before the remedy, and each rule of the remedy is broken once in its place.
4. **Something a standard points at moved: nothing.** No file was added, removed or renamed
   under `src/`, `tests/` or `scripts/`. `test_the_guard_does_not_read_inside_a_section` keeps
   its name and changed what it holds, on purpose; `vital/instrument.md` says what it holds
   now.

The retrospective's files are change sets apart from the feature's, each standard its own with
its `index.yml` entry, as the owner asked:

- `agent-os/standards/vital/plugin-state.md`, with its entry.
  - What Vital does with a text it cannot use, counted over 335 texts: 249 raise the alert, 3
    kill the process, one is ignored whole and 82 load, not all as given.
  - A state is written under a watch that answers the alert, on macOS: the method replaced for
    the length of the write and put back however it ends, with its limits stated.
  - A load is the main thread's on macOS, with what was not probed elsewhere.
  - A load is checked with a marker that is the plugin's alone, at the one cost a probe
    measured.
  - What a load can still do: the crash and the part load, issue #25's, with the 64 texts that
    still load through the shipped guard.
  - Verified against `src/patchbay_vital/host.py`, the tests it names, MW1 to MW4 and the
    transcripts it names.
- `agent-os/standards/vital/instrument.md`, with its entry.
  - The guard also refuses `custom_warps` and `random_values` that are not arrays of three
    objects, where a preset holds them, and a shape is guarded only once a transcript shows what
    Vital does with it.
  - What gets past the guard Vital answers with its alert, and the host answers that on macOS.
  - A load answered with the alert, or ignored, meets the rollback that was there.
  - A load from another thread changes nothing and is no state error.
  - The marker never reaches the model, and the lost step covers all three ways.
  - Verified against `src/patchbay_vital/patch.py` (`check_loadable`),
    `src/patchbay_vital/instrument.py` (`load_patch`), the tests it names, MG1 to MG3,
    `rollback-count.txt`, `remedy-run.txt` and `silent-and-loaded.txt`.
- `agent-os/standards/vital/preset-tests.md`, with its entry — no test gives Vital, in the
  test's own process, a text it may not return from; one that must gives it in a child it can
  kill under a time limit a stand-in holds; none gives Vital a text that killed it. Verified
  against `tests/integration/test_vital_instrument.py` (`_in_a_child` and the three tests that
  use it), `tests/unit/test_host.py`
  (`test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back`) and MW4.
- `agent-os/standards/index.yml` — the `vital:` section alone: three descriptions kept in step.
  The `base:` section is the sync's and is untouched; `scripts/sync-standards.sh --check` says
  identical.

Proposals sent upstream: fromtheoutfit/patchbay-standards#45; fromtheoutfit/patchbay-standards#44 and #38, each revised in place

### Standards retrospective (proposed, base)

Presented to the owner on 2026-11-17, four proposals in two questions, the texts to be sent
shown whole; all four approved, to be filed as shown. Filed on 2026-11-17 after the gate's
clean run, with no attribution, each read back from GitHub against the text sent and found the
same, character for character.

- **Wording checked first** against the open issues on `patchbay-standards` #44, #38, #34, #39,
  #41 and #24. Three refine a proposal already open and are revised into its issue in place;
  none contradicts one.
- **#44 and #38 each gain one "Revised 2026-11-17" paragraph** at the top, after the earlier
  revisions, naming this spec and this branch, and each "Depends on" line gains this branch.
  Every line of each earlier body is there, in order. #38's paragraph holds its two
  refinements as two separate items, each with its own reason and its own verification.
- **The check the owner asked for before a new issue.** The synced base standards say nothing
  of a platform, of native code or of the float environment: that guard's rule is not in
  `base/` yet. Of the 21 open issues, four speak of a platform at all: #38 (the machine a
  transcript prints), #35 and #36 (measured data and its machine) and #34. #34's third
  proposal is the nearest: the float environment guard, whose two functions come from the
  first library that holds them. It is a rule for that guard, and states none for a mechanism
  one platform alone has. So a new issue was filed, fromtheoutfit/patchbay-standards#45, with
  the alert watch as its one case, as the owner's last answer has it.

- `base/testing/tests.md`, "Inside a test" — **a test that must give a third party an input it
  may not return from gives it in a child process the test starts and can kill, under a time
  limit that a test on a stand-in holds.** Refines fromtheoutfit/patchbay-standards#44, its
  third proposal, whose "no test gives a third party an input it may not return from" becomes
  "in the test's own process". The limit is a named constant. At the limit the child is killed
  and the test fails by name. A test on a stand-in that never returns shows that it does, so
  "no test can hang the gate" is itself tested. An input seen to kill the third party stays a
  transcript's. Verified against `tests/integration/test_vital_instrument.py` (`_in_a_child`,
  `_CHILD_SECONDS`,
  `test_a_child_that_does_not_return_is_killed_at_its_limit_and_the_test_fails_by_name`,
  `test_a_patch_vital_answers_with_its_alert_is_refused_and_the_plugin_put_back`),
  `tests/unit/test_host.py`
  (`test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back`) and
  `verification/mutation.txt`, MW4. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#44, revised in place.
- `base/process/verification-gate.md` — **a kept transcript is never corrected: a label its
  driver got wrong is recorded beside it, and no figure is quoted from that line.** Refines
  fromtheoutfit/patchbay-standards#38, its second proposal. The record names the transcript and
  the line, says what the line claims and what the figures printed beside it show, and the
  transcript stays as it ran. Verified against "Four mislabels in the transcripts", above, and
  the four transcripts it names: `probes-2-alert.txt`, `probes-3-counts.txt`,
  `probes-4-counts.txt` and `marker-count.txt`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#38, revised in place.
- `base/process/verification-gate.md` — **evidence kept before a later edit is run again, or
  tied to the final tree by a transcript of its own.** Refines
  fromtheoutfit/patchbay-standards#38, its second proposal. A transcript's claim covers the
  tree it prints. Where files change after it, the spec runs it again, or keeps a transcript
  that lists every path that differs between the two trees by blob, names each as code or not,
  compares each code file then and now as syntax trees with docstrings left out, shows that
  comparison failing on a copy with one statement changed, and shows that nothing reads a
  docstring. One code difference, or one path of no named kind, is a rerun, not an
  explanation. Verified against `verification/tree-since-the-evidence.txt` and "The four
  evidence runs and the final tree", above. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#38, revised in place.
- `base/testing/tests.md`, "Inside a test" — **a mechanism one platform alone has is held by
  unit tests on every platform, and its documentation says what the others get.** The code
  picks the mechanism once, behind a private protocol: the platform's own, and a stand-in that
  does nothing elsewhere. Each branch has a unit test that patches the platform's name and the
  library lookup and needs no such platform. The real mechanism has one test, in a child,
  skipped by name elsewhere. The README, the changelog and the docstring say what the other
  platforms get and that nothing was probed there. Verified against `src/patchbay_vital/host.py`
  (`_AlertWatch`, `_NoWatch`, `_AppKitWatch`, `_alert_watch`), `tests/unit/test_host.py`
  (`test_off_macos_no_alert_is_watched`,
  `test_on_macos_a_library_that_is_not_found_leaves_no_watch`,
  `test_without_the_runtime_the_host_refuses_to_load`,
  `test_where_no_alert_is_answered_a_load_is_made_from_any_thread`,
  `test_the_watch_answers_a_real_alert_at_once_and_puts_the_method_back`) and the README's "A
  patch Vital cannot use". Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#45.
