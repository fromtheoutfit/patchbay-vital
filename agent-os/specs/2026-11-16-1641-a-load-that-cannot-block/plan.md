# A load that cannot block (issue #20)

## Context

`VitalHost.load_state` raises for no preset Vital cannot use. Given a text it cannot read, Vital
1.6.4 puts up a modal alert and never returns, so the calling process waits for ever. The
instrument's guard (`patch.check_loadable`) refuses every shape seen to do it, but not a fault
inside a section: three texts the writer can write pass the guard and block (the instrument
spec's `verification/probes.txt`, section 5). Issue #20 owns the remedy and comes before the
first experiment that puts an agent in front of the instrument. Its body names two candidates to
probe and one more question: can a load Vital silently ignores be detected afterwards through
the diagnostic read.

**This spec probes before it builds.** The plan below fixes the probes and the stop after them.
The remedy's tasks are written into `plan.md` only after the owner has chosen at that stop.
Nothing is committed, pushed or opened as a pull request by an agent.

What shaping read, with nothing written to the tree and no window opened:

- pedalboard 0.9.26's `ExternalPlugin.h`, shipped in the wheel and read for the fact, copying
  nothing: the `preset_data` setter calls the plugin without releasing the GIL. So while the
  alert waits no Python thread and no Python signal handler runs. A watchdog "from another
  thread" cannot be Python's; the probes show this rather than assume it.
- `ctypes` reaches the Objective-C runtime and AppKit on this machine with the standard library
  alone: `-[NSAlert runModal]`, `-[NSApplication abortModal]` and
  `-performSelector:withObject:afterDelay:inModes:` are found, and `method_setImplementation`
  exists. No new dependency is needed to probe either in-process variant.
- The 75 installed presets are 119,040 to 10,126,117 bytes (median 753,731); the start preset is
  60,875. A time limit has to be measured against the largest.
- The gate's negative harness copies `scripts`, `src`, `tests` and `agent-os/standards`, so a
  remedy that adds a file there means one rerun of it, about 45 minutes and 3 for case j.

## Decisions from shaping (each recorded in shape.md, the owner's words where given)

1. **The scope is issue #20** (`gh issue view 20`), whole: a load that cannot block, the two
   candidates probed, and its second question answered. The issue wins over the prompt.
2. **Probes, then a stop, then the remedy.** No remedy code, test or doc is written before the
   owner chooses at the stop.
3. **Facts come from probes.** Nothing is read from Vital's source (GPLv3). pedalboard's shipped
   header is read for a fact, as earlier specs did.
4. **Every load that may block is made in a child process under a time limit of 3 s,** counted
   from the child saying it is about to load, as a probe kept in a transcript. My reading of "a
   process of its own": a child the run can kill, never the run's own process. A kept child
   takes many loads, each under its own limit, since "one kept up" is a candidate to measure.
5. **Alert windows are announced and waited for.** Before each probe run I say how many alerts
   will show and for how long, and start it only at the owner's word.
6. **No gate file changes and no new dependency.** The probes and any remedy use the standard
   library (`subprocess`, `ctypes`). The owner's words: "If the probes point to a remedy that
   needs a new dependency, stop and say so before anything else: that is a gate spec first, and
   tech-stack.md gains its line there, not here."
7. **The mechanism is recorded in `agent-os/standards/vital/plugin-state.md`, written from the
   shipped code, not in tech-stack.md.** `agent-os/product/` is not touched.
8. **No test may hang the gate.** A test of the remedy uses a stand-in that blocks, or a child
   the test itself can kill under a time limit. No test gives Vital, in the test's own process,
   a text it may not return from.
9. **A remedy that only works on macOS is said to be so,** with what other platforms then get.
   Only arm64 macOS with a logged-in screen can be probed here; that is stated wherever a claim
   rests on it.
10. **Counted where it can be, a labelled sample where it cannot;** expected values from
    primitives; every transcript on a still tree, its tree and machine printed before and after.
11. **An issue or a base proposal this spec drafts is shown whole and filed only at the owner's
    word,** after the gate's clean run, with no attribution.
12. **The uncommitted record of fromtheoutfit/patchbay#26** in
    `agent-os/specs/2026-11-15-1448-the-instrument/shape.md` is left as it is and listed apart
    from this spec's change sets at the end.
13. Visuals: none. References: the #8 probe scripts, `host.py`'s fenv guard, the fake plugins,
    `load_patch`'s rollback. Standards: the core tier, `vital/plugin-state`, `vital/instrument`,
    `vital/measures`, `vital/preset-tests`, `base/testing/tests`,
    `base/process/verification-gate`, `base/process/standards-retrospective`,
    `base/process/ownership`.

## Task 1: Save spec documentation

Create `agent-os/specs/<date>-<HHMM>-a-load-that-cannot-block/` (the timestamp when this task
runs) with:

- **plan.md**: this plan. Extended after the stop with the remedy's tasks as decided.
- **shape.md**: the shape-spec template. Its first Decision cites issue #20. It holds the
  prompt's rules and the owner's answers in the owner's own words.
- **standards.md**: the thirteen standards of Decision 13, each file's full text as it reads
  now, concatenated from the files, not retyped.
- **references.md**: the four references, with what is borrowed from each.
- **verification/**: the probe transcripts, later `gate-run.txt`. No `visuals/`.

## Task 2: The probes

Scripts live in the scratchpad (`<scratchpad>/i20/`), with `transcript.sh`, `tree.sh` and
`machine.sh` taken from the instrument spec's `probes.txt`. Each transcript is written outside
the tree, embeds its scripts, prints the tree and the machine before and after, and is copied
into `verification/` when it ends. Nothing in the tree is edited while one runs. The probes read
the 75 installed presets under `~/Music/Vital` and write nothing there. A child ends itself
after its limit even if its parent has died (`faulthandler.dump_traceback_later(..., exit=True)`,
a timer that needs no GIL), so no run can leave an alert on the screen.

**Run 1, `probes-1-costs.txt`: costs and detection, on texts that return. About 5 minutes.
Alerts expected: none. At worst 4, one at a time, 3 s each,** if a text section 5 saw return
blocks here.

- 1a. A fresh child, start to verdict, on the start preset, 10 times, and on the smallest, the
  median and the largest installed preset: interpreter and imports, `VitalHost()`, two loads,
  exit. A labelled sample.
- 1b. A child kept up: its start-up once, its memory, then each of the 77 texts (the start
  preset, the fixture, the 75) three times: the round trip against the same two loads made
  in-process, by text size. Counted over the 77.
- 1c. The float environment: the parent's `fegetenv` bytes before and after each trial, and the
  child's own environment after its loads through `VitalHost`. Counted over the 77.
- 1d. Two loads in-process by text size, for a time limit: the slowest, and its ratio to size.
- 1e. The second question, on texts that return. For each of the 77: one parameter is first set
  to a value the text does not hold, the text is loaded twice, then (i) does that parameter read
  the text's value, (ii) how many of the 903 floats are not the text's, against issue #8's
  counts (0 on 66, 46 on 11), (iii) which sections are not the text's, by name, (iv) what each
  check costs. Then the four texts section 5 saw return wrong (`synth_version` 99.0.0;
  `wavetables` empty; `lfos` empty; `wavetables` one empty object), each in a child: which
  check flags each.

**Run 2, `probes-2-alert.txt`: the alert itself and the two in-process variants. About 4
minutes. Alerts expected: 4 that stay 3 s each, one at a time, then up to 11 flashes, then
none. At worst 6 of 3 s:** a variant is stopped at its first load that does not return.
A second process polls the window list (`CGWindowListCopyWindowInfo`, by owner pid) and the
front application 20 times a second, so what showed, for how long and whether it took the focus
is measured, not recalled.

- 2a. Baseline, two texts (no section at all; three wavetables whose `groups` is a number): a
  Python thread ticking every 100 ms and a `signal.setitimer` handler in the child, counted
  before and during the wait; the alert's time on screen; what a kill does to it. (2 alerts.)
- 2b. A kept child killed mid-alert, and the cost of the child that replaces it. (1 alert.)
- 2c. A blocking text loaded from a thread that is not the main one: returns, blocks or
  crashes. (1 alert at most.)
- 2d. **The watchdog as a timer:** before the load, an `NSTimer` on the main run loop in
  `NSModalPanelRunLoopMode` alone that calls `abortModal`; after it, whether the timer fired.
  On each of the 11 blocking texts, a child each: did the load return, in how long, did
  pedalboard raise, what showed. Then, in the same child: floats and sections changed against
  before; the start preset loaded twice and how many of the 903 floats are then not the
  start's; a render of one note, its RMS over the held note against a fresh host's; the same
  text again; a good text. Control over the 77 good texts: how many times the timer fired.
- 2e. **Something else the probes suggest, named as such: the alert answered before it
  opens.** For the length of the load, `-[NSAlert runModal]` is replaced by a function that
  records the call, reads the alert's text and returns at once; then it is put back. The same
  measurements and the same control as 2d, and what replacing and restoring costs a load.

**Run 3, `probes-3-counts.txt`: the wide counts, under whichever variant run 2 showed to
return. About 20 to 40 minutes. Alerts expected: none. At worst 1 of 3 s:** the run stops at
the first load that does not return, which is then a finding. Its design is confirmed with the
owner after run 2, with that run's figures; if neither variant works it is redesigned and
presented first.

- 3a. A generated set of malformed texts, its size printed: the start preset with each value
  inside each section (`wavetables`, `lfos`, `sample`, `custom_warps`, `random_values`,
  `modulations`) replaced by another JSON type or removed, to a stated depth, plus section 5's
  20. For each: can the writer write it, does the guard pass it.
- 3b. **Whether a text the child passes can still block the parent.** Each text's verdict in a
  fresh child against its verdict in a process with each of three histories (the start preset
  loaded twice; a set of all 903 and a render; an older installed preset loaded). Counted: the
  same on how many, and each that differs. Also whether any text passes the first of its two
  loads and alerts on the second.
- 3c. **How large the silent class is.** Of the texts that raise no alert: loaded whole, ignored
  whole, sections kept, or something else, by the diagnostic read; and which of 1e's checks
  flags each. This is the second question's answer over a counted set, not two examples.
- 3d. After an alert answered, the model's text loaded twice: the 903 floats and the sections
  against a normal double load, over every text that alerted. A soak of 1,000 alternating
  loads in one child: memory before and after, no crash. A labelled sample.

## Task 3: Stop and present

Before any remedy is written. For each candidate, from the kept transcripts only:

- **A trial load in a child process with a time limit:** per-load cost fresh and kept up;
  whether a text the child loads can still block the parent; what happens to the child's own
  alert; how the float environment guard and the two-load rule apply.
- **A watchdog that ends the alert's modal loop:** whether it can be done from Python at all,
  on which platforms, and what state the plugin is in afterwards.
- **Anything else the probes suggest,** named as such (2e, and whatever else turns up).
- **The second question:** whether a silently ignored load, or an alert dismissed, is detected
  through the diagnostic read, and at what cost.
- For each: what was measured, what it costs a load, what it leaves uncovered (a process with
  no screen; a load off the main thread; other platforms, none of which can be probed here),
  and what it does to the instrument's promises: `load_patch` raising the package's patch error
  and changing nothing; the lost-step state; the model as the source of truth.

Then the owner chooses, by AskUserQuestion. The outlines below say what each candidate would
touch. They are not a choice.

- **In-process (2d or 2e), macOS:** `host.py`'s state writes go through the watch, and an alert
  becomes `PluginStateError`, chained into `load_patch`'s existing rollback (`PatchRefusedError`,
  the model's text sent again; the lost step if that is refused too). Other platforms get what
  the owner decides: the trial child, or the limit stated as it is today.
- **A trial child:** a module of its own (the child's entry point), started by the host or the
  instrument, kept up or fresh as measured; `load_patch` refuses on its verdict before the
  plugin is called.
- **A check after the load** for the silent class, if the probes show one that is cheap and
  exact.

## Task 4 onward: the remedy, as decided at the stop

Written into `plan.md` then. Whatever is chosen:

- Code under `src/patchbay_vital/`, one module per concern, only the package's errors leaving,
  each call into the plugin still its own floating-point guard.
- Tests mirror the source. Unit tests run where no Vital is, on a stand-in that blocks or
  alerts; a test of a macOS mechanism runs in a child it can kill and skips by name elsewhere;
  a test against Vital that may block does the same. `test_the_guard_does_not_read_inside_a_section`
  names #20 and changes on purpose.
- A kept transcript, `remedy-run.txt`: section 5's 11 blocking texts and run 3's set against the
  shipped remedy, each in a child under the limit, on a still tree.
- Docs that must read true afterwards: `host.py`, `instrument.py` (known limits, `load_patch`),
  `patch.py` (`check_loadable`), `errors.py`, the README's known limits, `CHANGELOG.md`.
- If a file is added, removed or renamed under `scripts`, `src`, `tests` or
  `agent-os/standards`: `scripts/gate-negative-tests.sh` rerun once before the gate, its
  estimate written first, its transcripts kept.
- ruff format, ruff check and a line-length pass over every changed file before the first kept
  run.

## The remedy, as the owner decided at the stop (2026-11-16)

Added after the probes. `shape.md` holds the probes, the owner's answers in the owner's own words and
Decisions 13 to 20. Four probe runs were made, not three: run 3 stopped at the first text that
killed its child, and run 4 made the wide counts with a crash counted as a verdict.

### Task 4: the arrays tried, before the guard is written

`verification/arrays-seen.txt`, from run 4's transcript and the 77 texts on hand: each array made
one entry longer or shorter with its verdict; each array never tried; how `custom_warps` and
`random_values` are held. Done before any guard code.

### Task 5: the host (`src/patchbay_vital/host.py`, `errors.py`)

- **The alert answered.** On macOS, for the length of each state write, `-[NSAlert runModal]` is
  replaced by a function that records the alert's two texts and returns at once, and is put back
  in a `finally`. A write in which an alert was answered raises `PluginStateError` with Vital's
  words. Through `ctypes`, standard library alone; the host refuses to load on macOS where the
  runtime cannot be reached, as it does for the floating-point functions.
- **The main thread.** On macOS a load from any other thread raises `PluginThreadError`, a new
  error under `VitalHostError`, before the plugin is called.
- **The marker.** Before the write the host sets `filter_1_on` to the end of its range the text
  does not hold, the maximum unless the text's value is in the upper half; after it, a marker
  still there raises `PluginStateError` saying the load was ignored. On any failure a marker
  still planted is set back. Where the map is not the plugin's the load is made unchecked.
- Elsewhere than macOS the write is made as today.

### Task 6: the guard (`src/patchbay_vital/patch.py`)

`check_loadable` also refuses `custom_warps` and `random_values` that the preset holds and that
are not arrays of three objects, by `start.py`'s `WARPS` and `RANDOMS`.

### Task 7: the instrument (`src/patchbay_vital/instrument.py`)

No new path: an answered alert and an ignored load arrive as `PluginStateError` and meet the
rollback that is there. `PluginThreadError` leaves `load_patch` as itself, nothing touched. The
docstrings say what is remedied, where, and what stays: the crash, the silent class, other
platforms.

### Task 8: tests, none of which gives Vital a text it may not return from

- `tests/unit/test_host.py`: a stand-in watch holds that the method is replaced only during a
  write and put back when the write raises; an answered alert is `PluginStateError` with its
  words; a load from a second thread is `PluginThreadError`, the plugin not called; the marker's
  value from primitives, its move, an ignored load, the put-back; the real AppKit watch in a
  child the test can kill, skipped by name off macOS.
- `tests/unit/test_instrument.py`: the model and the bus untouched by the marker on a load that
  succeeds and one that fails; an alert and an ignored load each roll back and are refused as a
  patch; each, when the rollback fails too, leaves the instrument out of step; a load from a
  second thread changes nothing; the guard's two new shapes; all 77 still pass the guard.
- `tests/unit/test_errors.py`, `test_package.py`: the new error.
- `tests/integration/`: against Vital, in a child the test can kill, an alerting text is refused
  and the plugin put back; a load Vital ignores is refused.

### Task 9: evidence on the shipped code, each a kept transcript on a still tree

Each run that loads a text that may block is announced with its worst case and started only at
the owner's word.

- `verification/marker-count.txt`: over the fixture and the 75 installed presets, the marker
  moves on every good load and the two-load result is the same with the check as without it,
  all 903 floats and every section.
- `verification/rollback-count.txt`: with each of the 75 installed presets as the model, an
  alerting patch is refused and the plugin holds all 903 floats and every section as before it.
- `verification/remedy-run.txt`: the 335 texts through the shipped code, each in a child under
  the limit: none blocks, and what each is refused as.
- `verification/old-behaviour.txt`: the new tests failing on the code before the remedy, on a
  scratch copy outside the tree.

### Task 10: docs and the drafted issue

README, CHANGELOG, the docstrings of `host.py`, `instrument.py`, `patch.py` and `errors.py`.
One issue drafted in `shape.md` for what stays open (the crash's open class with the arrays not
tried and the trial child as its candidate; the silent class), shown whole, filed at the owner's
word.

## Final task: Verification gate

Run the full gate, in order. The spec is not complete until every step passes.

1. `bash -n` on every shell script under `scripts/` as git lists them, at a work-tree top that
   is the repository root, with no tracked file a `.gitignore` ignores.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check` over
   the `.py` and `.pyi` files git lists.
3. `uv run --locked ruff check --config pyproject.toml` over the same files.
4. `uv run --locked mypy --config-file pyproject.toml` over the files git lists under `src/` and
   `tests/`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`: every test under `tests/` passes.
6. `scripts/sync-standards.sh --check` against `../patchbay-standards` at the pinned commit.
7. **Docs:** the documentation the change touches reads true after it; what was checked is
   recorded in `shape.md`.
8. **Version:** the change is under `[Unreleased]` in `CHANGELOG.md`; recorded in `shape.md`.
9. **Standards retrospective,** always last, per
   `agent-os/standards/base/process/standards-retrospective.md`. `vital/plugin-state.md`
   records the mechanism and the new measured facts, from the shipped code and the kept
   transcripts; `vital/instrument.md` and `vital/preset-tests.md` where the remedy changes their
   rules; `index.yml`'s `vital:` entries in step. Each project edit is shown to the owner before
   it is written and is its own change set. A base change is a proposal under
   `### Standards retrospective (proposed, base)`, never an edit. `Proposals sent upstream:` is
   always recorded.

`scripts/gate.sh` runs steps 1 to 6 as one command. Its green run is kept as
`verification/gate-run.txt`, first line the date and the branch, and is the last thing run
before hand-over. A failing step is fixed at its cause and the whole gate rerun.

Then, in this order:

1. **Present and file.** Each base proposal to the owner by AskUserQuestion (multi-select, at
   most three to a question, a "None of these" option), checked against the open issues on
   fromtheoutfit/patchbay-standards first; the approved ones filed as one issue there, or
   revised into an open one in place, no attribution, read back, the number written beside
   each; each declined one marked so. Any issue this spec drafted for this repository or for
   fromtheoutfit/patchbay is shown whole and filed only at the owner's word.
2. **Stop and print `git status --short`,** with the change sets listed apart: the feature; each
   retrospective edit; and, separately, the earlier record of fromtheoutfit/patchbay#26 in the
   instrument spec's `shape.md`.

## Verification

- The three probe transcripts, each ending "the tree after the run is the tree before it".
- `remedy-run.txt`: no load in it fails to return under the shipped remedy, counted.
- The new tests fail on the code before the remedy (kept as a transcript) and pass after.
- `scripts/gate.sh` exit 0, kept as `gate-run.txt`; the harness's count if it was rerun.
- `git status --short` at the end names only this spec's files and the one earlier change.
