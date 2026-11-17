# patchbay-vital

patchbay adapter for Vital: the `.vital` preset format, the VST3 parameter map and unit
conversions, and sound-design semantics as data.

This is an experiment, not a product. The distribution name is `patchbay-vital` and the import name
is `patchbay_vital`. It reads, writes and compares a `.vital` preset file, maps each of the 903
parameters Vital's VST3 exposes to its preset key with exact conversions between the host's
normalized value, the preset's value and the value Vital displays, and, with the `host` extra, hosts
Vital, loads a preset into it whole and drives it as a `patchbay.Instrument`: parameters read and
set in the units Vital displays, a preset loaded and given back as a patch, a pattern rendered to
audio. The sound-design semantics join with the spec that adds them
(`agent-os/product/mission.md`).

```python
from patchbay import ParameterId
from patchbay_vital import diff, dump, load, parameter_map

preset = load("Plucked String.vital")   # typed models, every unread section kept as it was
dump(preset, "copy.vital")              # byte for byte what Vital wrote
diff(preset, load("copy.vital")).is_empty

attack = parameter_map().find(ParameterId("env_1_attack"))
attack.parameter.unit                   # Unit.seconds, as Vital displays it
attack.to_normalized(0.5)               # the host's value for half a second
```

```python
from patchbay import EventBus, Note, ParameterId, Pattern, Quantity, RenderRequest, Unit
from patchbay_vital.instrument import VitalInstrument   # needs patchbay-vital[host]

vital = VitalInstrument(EventBus())         # Vital at its default path, on the start preset
vital.set(ParameterId("filter_1_on"), Quantity(value=1.0, unit=Unit.none))
vital.set(ParameterId("filter_1_cutoff"), Quantity(value=12.0, unit=Unit.semitones))
vital.get(ParameterId("filter_1_cutoff"))   # what Vital holds for it, in semitones
patch = vital.patch()                       # the whole preset as a core Patch; load_patch takes it back
note = Note(pitch=60, velocity=100, start_beats=0.0, duration_beats=3.0, channel=0)
pattern = Pattern(tempo_bpm=120.0, bars=1, beats_per_bar=4, notes=(note,))
result = vital.render(pattern, RenderRequest(sample_rate=48000, tail_seconds=0.5))
result.audio.shape                          # (2, 120000) float32; result.warnings says if it clipped
```

```python
from patchbay_vital.host import VitalHost   # needs patchbay-vital[host]

host = VitalHost()                          # /Library/Audio/Plug-Ins/VST3/Vital.vst3, or a path
host.load_state(open("Plucked String.vital", "rb").read())   # routing, wavetables and all
audio = host.render([(bytes([0x90, 60, 100]), 0.0)], 48000, 48000)   # (2, 48000) float32
```

## The instrument

`patchbay_vital.instrument.VitalInstrument` implements `patchbay-core`'s `Instrument` protocol and
passes core's thirteen contract tests against the installed Vital. It is registered as the entry
point `vital` in the `patchbay.instruments` group, a callable that takes the `EventBus` the
instrument publishes on. **That entry point is provisional:** core reads no entry point yet and has
not said what the group holds.

- **It starts on a preset this package ships, not on Vital's own Init.** `data/start.vital` holds
  Vital's default value for each of the 903 parameters, which the parameter map ships already, with
  media generated here: a plain ramp as each oscillator's wavetable, straight lines as the LFO
  shapes, a 16-sample ramp as the sample. Vital's own starting state cannot be shipped, its wavetable
  and its noise sample being Vital's, and is not the same from one instance to the next. So every
  instrument starts on the same preset on every machine, and a patch that names values and nothing
  else means that preset with those values. The census writes the file beside the map.
- **The model is the source of truth.** The instrument holds the preset it was given and answers
  from it; what the plugin holds is never read back as the instrument's state.
- **A value is held as Vital holds it.** After `set`, `get` returns the value Vital holds for the one
  given, which need not be the nearest value it can hold; a bound is held exactly; a value between a
  stepped parameter's steps is taken and the nearest step held. A patch's value is taken the same
  way, but where the value is exactly the display of a float, which it then names: so a patch the
  instrument gave restores every float it carried.
- **A patch names every parameter the preset holds a float for** in `values`, but for a float no
  display names, one outside its parameter's bounds among them, which rides in `opaque` as itself
  and is still read with `get`.
- **Each note sounds for its own length.** Two notes of one pitch that overlap on one channel would
  both stop at the first one's end on Vital, so the later is sent on a channel of its own.
- **If the plugin does not take a load and then does not take the instrument's own preset, build
  a new instrument.** Its state is then unknown, and the instrument refuses every later call that
  would reach it.

**A patch Vital cannot use.** Vital reports none. What the instrument does about each kind, on
Vital 1.6.4 through pedalboard 0.9.26 on arm64 (issue #20;
`agent-os/specs/2026-11-16-1641-a-load-that-cannot-block/shape.md` holds the measurements):

- **One Vital cannot read** it answers with a modal alert, and never returns to its caller. On
  macOS the instrument answers that alert before it opens: `load_patch` raises
  `PatchRefusedError` with Vital's own words and loads its own preset again. **On any other
  platform nothing answers the alert, and such a patch still blocks the calling process.**
  Nothing was measured there, nor in a process with no screen.
- **From a thread that is not the main one,** on macOS, a load is refused with
  `PluginThreadError` and nothing is touched. The alert cannot open there, and the process was
  seen to die at its next render.
- **One Vital ignores is refused too.** A preset newer than the plugin, which Vital ignores
  whole, `load_patch` refuses before Vital is given it. Behind that, the instrument sets a marker
  on the plugin before each load and reads it afterwards, and a load that left the marker is
  refused. The marker never shows in `get`, `patch` or an event.
- **A patch Vital crashes on kills the calling process** (issue #25). Three shapes were found,
  each a section one entry longer than Vital holds, and `load_patch` refuses those. Only the
  shapes found are refused.
- **A patch Vital loads in part is not detected** (issue #25). Where it keeps a wavetable or a
  sample it had, or makes something else of the one given, nothing read back from the plugin
  tells.

Known limits, each measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64. The first two each
wait on an issue of their own and come before the first experiment that puts an agent in front of
the instrument, in this order; the third is a workaround no issue owns
(`agent-os/specs/2026-11-15-1448-the-instrument/shape.md` holds the measurements):

- **A render of most presets opens with the preset sounding though no note was played** (issue
  #21). On the start preset this is a transient of about 2% of full scale that is over in about a
  tenth of a second; on presets Vital installs it reaches full scale and can last seconds.
- **On a preset older than the plugin, a few parameters can be reported by `get` with the file's
  value where Vital plays its upgraded one,** and for a choice that can be a different setting by
  name (issue #22): of the 75 presets Vital installs, 11 hold 46 such values,
  `osc_1_stack_style` and `filter_1_style` among them. Setting a parameter to the value `get`
  shows puts Vital back on it for 42 of the 46. It is refused for 3, `flanger_center` on Touch
  Tone, Memory Leak and Oolacile Evil Dubstep Bass, where the file's value is outside the
  parameter's bounds. It changes nothing for 1, `modulation_10_amount` on Oolacile Evil Dubstep
  Bass, which holds a value no set lands on: Vital goes on playing about 0.075 where `get` shows
  about 0.2.
- **Every load is made twice,** a measured workaround with no known cause: one load leaves 17 to 53
  of a preset's 903 floats off the text's, and a second holds them.

## Layout

- `src/patchbay_vital/`: the package, src layout, typed (`py.typed`). `preset.py` holds the models,
  `format.py` reads, writes and compares a file, `grisu2.py` writes a float as Vital does, `errors.py`
  holds the exceptions, `float32.py` computes in single precision as Vital does, `parameters.py`
  holds the parameter map's models and scales and reads `data/parameters.json`, the map the census
  measured, and `settings_keys.txt` lists every float key Vital has been seen to write, derived from
  the map. `files.py` replaces files whole or not at all, for `format.py` and the census.
  `start.py` holds the preset the instrument starts on, `data/start.vital`, and writes it from a
  map; `patch.py` carries a preset in a core `Patch` and back, byte for byte; `midi.py` builds a
  pattern's MIDI as bytes. `state.py` reads and writes the containers around the plugin's state;
  `host.py` hosts Vital through pedalboard, `census.py` measures it and writes the map, the key
  list and the start preset, and `instrument.py` is the instrument, all three needing the `host`
  extra and none imported by the package itself.
  `__init__.py` holds the re-exports, `__version__`, read from the installed package's metadata so
  `pyproject.toml` is the one place the version is written, and `__all__`. The package is imported
  installed (`uv sync`): from a bare `src/` on `sys.path` the import fails rather than invent a
  version.
- `tests/`: pytest's tree. Not a package (no `__init__.py`), so one basename per test file across it,
  which mypy holds. `unit/` mirrors `src/`. `integration/` round-trips every preset Vital installed
  under `~/Music/Vital` against `data/factory-manifest.txt`, through the file's own writer and
  through a patch, and hosts the installed plugin: the census regenerates the committed map, the key
  list and the start preset, the presets load as its state, its renders are measured, and
  `test_vital_instrument.py` runs core's thirteen contract tests and the instrument's own against
  it; each skips, saying so, where what it needs is absent, CI among them. CI still runs the
  contract tests, over a fake plugin in `unit/test_instrument.py`, which is not a pass against
  Vital. `data/` holds no preset of Vital's, whose license forbids that: its one `.vital` is a 1.6.4
  save with the media replaced; `fma-vectors.txt` holds the plugin's own values that `float32.py`
  is held to, `pinned-values.txt` the normalized values and the displays both test modules hold
  the map and Vital at, written once, and `upgraded-floats.txt` the 46 floats Vital changes as it
  loads an installed preset older than it.
- `pyproject.toml`: the one configuration file. Every tool the gate runs is configured under
  `[tool.*]` there and nowhere else, with no `setup.py`, `setup.cfg`, `requirements*.txt`,
  `tox.ini`, `.flake8`, `mypy.ini`, `pytest.ini`, `.ruff.toml` or `uv.toml`. The `[tool.*]` sections
  (the rule set, `[tool.uv]`, which pins uv itself, and `[tool.uv.sources]`, which pins the commit
  `patchbay-core` is taken from) and the dev group's pins of the tools the
  gate runs (ruff, mypy and pytest), with what `uv.lock` resolves for them, are the gate's and change
  only in the gate's own spec; `[project]`, `[build-system]` and the dev group's other entries
  (hypothesis, packaging, pedalboard and pre-commit) are the package's. `uv.lock` is the resolution
  of the pins.
  The wheel carries `LICENSE` (`license-files`). It declares the `patchbay-core` range and not the
  source, and `patchbay-core` is on no index, so the wheel installs only where that package can be
  resolved; from a checkout, `uv sync` is the way in.
- `.pre-commit-config.yaml`: hook registration only, the one file pre-commit cannot do without; it
  configures no tool.
- `scripts/`: `gate.sh` (the verification gate), `gate-negative-tests.sh` (the tests that prove each
  gate step can fail, not run by the gate) and `sync-standards.sh` (installed and replaced by the
  standards sync, never hand-edited).
- `agent-os/product/`: `mission.md` and `tech-stack.md`, the decisions the specs implement.
- `agent-os/standards/`: `base/`, the base standards synced from `patchbay-standards` and pinned to
  the commit in `base/.version`, read-only here; `index.yml`, whose `base:` section is the sync's and
  whose other sections are this repository's own.
- `agent-os/specs/`: one folder per spec, with its plan, shaping notes, the standards as they read
  when it was shaped, and `verification/` holding the gate transcripts.
- `.claude/commands/agent-os/`: the Agent OS commands; `shape-spec.md` is customized for this
  repository's gate, the rest are stock.
- `.github/workflows/gate.yml`: CI, which installs the locked toolchain and runs the gate, and
  checks nothing the gate does not.
- `CLAUDE.md`: the rules for an agent working here, `## Git` and `## Ownership` first.

## Install

```sh
uv sync
```

uv and git are the tools this repository assumes, `uv sync` calling git to fetch `patchbay-core`.
uv at 0.13.7: `pyproject.toml`'s `[tool.uv]
required-version` pins it, so any other uv refuses every command that reads this project's settings
(`uv sync` and `uv run` among them), and CI's setup-uv reads the same key to install it. `uv sync`
reads `.python-version` (3.12), fetches uv's own build of that interpreter
(`[tool.uv] python-preference`) into uv's Python directory (`uv python dir`) if it is not there,
creates `.venv/` and installs into it the package, its runtime dependencies, `pydantic` and
`patchbay-core` (fetched from GitHub at the commit `[tool.uv.sources]` pins, so the first sync needs
the network) and the
locked dev toolchain: ruff, mypy, pytest,
hypothesis, packaging, pedalboard and pre-commit, each pinned exactly in `pyproject.toml`'s
`[dependency-groups] dev` with the date it was published. `uv.lock` resolves them. Outside the
repository uv writes only that interpreter and its own cache. Run a tool as `uv run --locked <tool>`,
as the gate does.

A consumer installs `patchbay-vital` for the format, the map and the carrying of a preset in a
patch, and `patchbay-vital[host]` for the instrument and to host
Vital. **Licence:** this package is MIT; pedalboard, the host, is GPLv3, so it comes only with the
`host` extra, `host.py` is the one module that imports it, and nothing of pedalboard's is in this
repository. That is the owner's decision, not legal advice, and is revisited before any release to
PyPI. So is shipping the start preset, `data/start.vital`: it holds Vital's default values, which
the parameter map ships already, and media generated by this package, and none of Vital's presets,
wavetables, samples or LFO shapes. And so is committing `tests/data/upgraded-floats.txt`
(2026-11-16), which the package does not ship: the names of 11 presets Vital installs, keys and 46
measured values, and no preset's content. Vital itself is installed separately and is not
redistributed here.

## The gate

```sh
scripts/gate.sh
```

Six runnable steps, in order, stopping at the first failure (exit 1; exit 2 on usage or when the
script cannot enter the repository root):

1. `bash -n` on every shell script under `scripts/` as git lists them, tracked or untracked and not
   ignored, at a work-tree top that is the repository root; a tracked file a `.gitignore` ignores, a
   file there that is neither `.sh` nor bash-shebanged, a listed path missing from the disk, a
   symlink to nothing and a listing git cannot make (a corrupt index) each fail the step by name.
2. `uv sync --locked`, then `uv run --locked ruff format --config pyproject.toml --check` over the
   `.py` and `.pyi` files git lists: no `uv.toml` at the root, the locked toolchain syncs, and every
   file is formatted as ruff format writes it.
3. `uv run --locked ruff check --config pyproject.toml` over the same files: no violation of
   `[tool.ruff.lint]`, which selects every rule and ignores only what this tree proved wrong, each
   with its reason.
4. `uv run --locked mypy --config-file pyproject.toml` over the `.py` and `.pyi` files git lists
   under `src/` and `tests/`: no type error under `strict`.
5. `uv run --locked pytest -c pyproject.toml -p no:doctest`: every test under `tests/` passes, once
   no `.py` file there, and no `conftest.py` at the root, is one git ignores.
6. `scripts/sync-standards.sh --check`: `agent-os/standards/base/`, the `base:` section of
   `agent-os/standards/index.yml` and the sync script itself are byte-identical to
   `patchbay-standards` at the pinned commit.

Step 2 opens with `uv sync --locked`, which installs exactly what `uv.lock` names and fails the step
as the sync, before any tool runs, when a pin was edited in `pyproject.toml` without `uv lock` (the
lockfile is never rewritten), when uv cannot read either file, fetch a locked package or build the
package from them, when the running uv is not the required one, or when uv warns it cannot use a setting in `[tool.uv]`; so
the gate writes nothing but the ignored `.venv/` and
caches. Steps 2 to 5 then run each tool under `--locked`, the one `uv.lock` names, and read only the
files git lists: ruff, mypy and pytest are told by flag to read `pyproject.toml` alone, and ruff and
mypy are given git's list itself, so git alone decides what is ignored; pytest, which loads the `conftest.py` of every
directory it collects from, walks `tests/` only once nothing it would read is ignored. Step 6 reads
the sibling checkout at `../patchbay-standards`, so clone `patchbay-standards` beside this repository
first; CI checks it out there at the pinned commit, installs uv with `astral-sh/setup-uv` at the
version `[tool.uv] required-version` pins, runs `uv sync --locked` and then the script. Three
judgment steps follow the script and are recorded in each spec's `shape.md`: Docs, Version and the
standards retrospective. The rule is `agent-os/standards/base/process/verification-gate.md`.

`scripts/gate-negative-tests.sh` runs each failure case on a scratch copy (`all` adds the CI replay);
its transcripts live in the spec that last changed a gate file.

## pre-commit

```sh
uv run --locked pre-commit install           # once, to run the hooks on every commit
uv run --locked pre-commit run --all-files   # the hooks over the tree, with or without the git hook
```

The hooks are `ruff check --fix` and `ruff format`, run through `uv run --locked`, so they are the
gate's ruff with the gate's rules; never mypy or pytest, which are the gate's. The hook is a
convenience for the person committing; `scripts/gate.sh` is the check.

## Syncing the standards

```sh
scripts/sync-standards.sh                 # move the pin to patchbay-standards' origin/main
scripts/sync-standards.sh --check         # the drift check, as the gate runs it
scripts/sync-standards.sh --index-only    # regenerate the base: section of index.yml alone
```

The pin is the commit in `agent-os/standards/base/.version`. A sync forward is its own change set,
titled `chore: sync base standards to <sha>`. No file under `base/` and no `base:` entry is edited
here: a change to a base standard is proposed in a spec's retrospective, presented to the owner, and
filed as an issue on `patchbay-standards`, whose own spec lands it as a pull request. The rule is
`agent-os/standards/base/process/standards-sync.md`.

## Specs

Work is shaped with `/agent-os:shape-spec` in plan mode and ends with the gate. `CLAUDE.md` holds the
rules an agent follows here, `## Git` and `## Ownership` first: a person owns every commit, pull request and
merge.
