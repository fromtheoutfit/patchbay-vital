# References for the Instrument (issue #8)

## The issue and core

- **Issue #8,** the scope: https://github.com/fromtheoutfit/patchbay-vital/issues/8, its body
  and its one comment.
- **Core at `eddba95`,** as `[tool.uv.sources]` pins it, read from the installed package:
  `contracts.py` (`Instrument` and its docstrings), `models.py`, `events.py`, `errors.py` and
  `testing/`.
- **Core's review of its PR 19,** fromtheoutfit/patchbay at `eddba95`,
  `agent-os/specs/2026-11-11-0935-get-revision-after-pr-19-review/shape.md`: why `get` says
  "a value the parameter holds", and the three findings it left to this spec.

## Similar Implementations

### Core's fake and its conftest

- **Location:** `patchbay/testing/fake.py` and `tests/unit/testing/conftest.py` at `eddba95`.
- **Relevance:** the reference implementation of the protocol this spec implements, and the
  shape of the fixtures the contract tests run with.
- **Key patterns:** the whole patch checked before anything changes; the change made, then one
  event published under a fresh correlation id; a render longer than a declared limit refused
  before anything is allocated; a note's samples from `sample_at`, its end clamped to the
  render's length; a render of zero samples returned empty.
- **What differs here:** the fixtures live in the test modules, since negative test q writes a
  `conftest.py` of its own.

### The hosted plugin's integration module

- **Location:** `tests/integration/test_vital_plugin.py`.
- **Relevance:** how a test runs against the installed Vital.
- **Key patterns:** one Vital a module and the starting state reloaded per test; a skip by name
  with no Vital or on another machine; every audio assertion a measure with a named tolerance
  and its probe; an expected value worked out from primitives (`_nearest_quotient`); the state's
  floats read with the host's own `_floats`.

### The host's fake plugin

- **Location:** `tests/unit/test_host.py`, `_FakePlugin` and the `fake` fixture.
- **Relevance:** a real `VitalHost` over a stand-in for pedalboard's plugin, so CI, which has no
  Vital, runs the host. The instrument's unit tests do the same with a fake hosting all 903
  parameters, so the instrument reaches its plugin only through `VitalHost` there too.
- **Key patterns:** `pedalboard.VST3Plugin` and `platform.machine` replaced through
  `monkeypatch`; the containers a state is wrapped in.

### The last spec folder

- **Location:** `agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`.
- **Relevance:** how evidence is recorded now.
- **Key patterns:** each transcript opens with its date, branch and machine, prints the tree
  before and after by blob and compares them, prints the machine again, and embeds its scripts;
  it is written outside the tree and copied in afterwards; `gate-run.txt` is the last thing
  done.

### The host spec's probes

- **Location:** `agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/verification/`,
  `probes.txt` and `host-probes.txt`.
- **Relevance:** the measurements this spec starts from and the measures it reuses.
- **Key patterns:** `centroid`, the mean of the channels, the magnitude of the real FFT and its
  frequency-weighted mean; the transient's peak per 10 ms frame; where a note lands, by the
  first sample past a threshold; a render's length against the duration asked for.
