# Revision after the Review of PR 9 — Shaping Notes

Shaped 2026-11-10 in plan mode with this repository's customized `/agent-os:shape-spec`. The owner
answered seven design questions, one confirmation of Steps 2 to 5, and the retrospective's
proposals.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

The owner's review of PR 9 at `eb95567`
(https://github.com/fromtheoutfit/patchbay-vital/pull/9#issuecomment-6770350222): 24 findings,
two reproduced by running the code, the rest from reading it. Each was checked while shaping
against the code, pedalboard 0.9.26's source and the installed plugin; all hold, finding 13's
remedy being the docs rather than the code (below). On the same branch, so PR 9 carries it.
CHANGELOG entry, gate green, `verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** the review's 24 findings, in the owner's words "read through the first round
  of Review on PR 9 and address the issues".
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission is unchanged.
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership`,
  `testing/tests`, `vital/plugin-state`, `vital/parameter-map` and `vital/preset-file`. Snapshot in
  `standards.md`, base at `e31f7db`.

## What was checked while shaping

- **pedalboard 0.9.26's wrappers** (`_pedalboard.py`, read for the facts): `parameters` rebuilds
  its mapping on each read (about 3 ms for 903) from wrappers it caches itself in
  `__python_parameter_cache__`; a wrapper's construction scans 1001 raw values; and every attribute
  access on a wrapper fetches the native parameter afresh through `__get_cpp_parameter`. The first
  probe's crash (`probes-first-attempt.txt`) came from the typed `_parameters` objects, the native
  ones. So holding the wrappers is safe and the docs were wrong, not the code (finding 13).
- **A Vital load is 2.2 s**; the gate's pytest was 65 s for 417 tests, about 14 loads (finding 19).
- **pedalboard accepts empty and odd MIDI bytes** here without error; its `preset_data` setter
  raises a bare `RuntimeError` ("Failed to set preset data for plugin"), which `load_state` let
  out (finding 3).
- **`functools.cached_property` on a frozen `PatchbayModel`** under pydantic 2.14.3: works, equality
  after one side cached is `True`, JSON round trip intact (finding 17).
- **core's `Parameter.check`** refuses a non-whole value for a choice or a boolean (finding 1).

## Decisions

1. **Scope:** all 24 findings; 16 declined with its reason; 24 is the owner's at commit time.
2. **#13:** keep `self._hosted`; correct `host.py`'s docstring and `vital/plugin-state.md`: the
   Python wrappers are held and are safe because each re-fetches the native parameter per access;
   the native objects are never held. (Owner: "Correct the docs and standard".)
3. **#11:** `MappedParameter`'s validator checks the round trip in float32: the curve's `to_preset`
   of each bound lands on the scale's ends and of the default's display on `preset_default`.
   **Found while building:** on a libm an ulp apart the committed bound can sit one double ulp past
   this platform's display of the scale's end, so `to_preset` takes both the parameter's own bounds
   and this platform's ends, equal on the measuring machine. (Owner: "Check the round trip in
   float32".)
4. **#12:** `ParameterMap.machine` (`platform.machine()`, `"arm64"`); the census writes it; the host
   raises `MachineMismatchError` where the map is first used, never at load or in `measure`, so the
   census runs on a new machine with no map of its own. (Owner: "Record the machine; the host
   refuses a mismatch".)
5. **#19:** one module-scoped `VitalHost` per integration module, a function-scoped fixture loading
   the initial state's text before each test. The gate's pytest went from 65 s to 39 s. (Owner:
   "Module-scoped, reset per test".)
6. **#8:** `OpaqueChange.where: Literal["settings", "preset"]`. (Owner.)
7. **#16: declined.** The validator's decode is the model holding its own invariant
   (`base/python/models`, "Refusing as the package"); the census runs once per Vital version and
   its ~10k `state()` calls are 2.5 ms each. (Owner: "Decline with the reason".)
8. **#20:** a new module `src/patchbay_vital/files.py` holding `replace_file`. In the owner's words:
   "'Replace a file whole or not at all' is a file-system concern, and layout.md says one concern per
   module; two importers is what makes it a module rather than a private helper. Tiny module, right
   home."
9. **#5:** `samples` and `sample_rate` go through `operator.index`, so a numpy integer is taken and
   a float refused by name before the plugin is called.
10. **#15:** `render` asks for one sample more, refuses fewer than asked, and returns the first
    `samples` contiguous.
11. **#4:** two hosted parameters moving one preset value are refused in `build_map` naming both,
    before the map's own validator would; that validator's refusal is still wrapped, naming "the
    map".
12. **#21:** a private `_ReasonError` base with a class-attribute prefix; names, fields, `args` and
    messages unchanged, held by `test_a_reason_is_said_after_what_failed`.
13. **#24:** the owner's at commit time. This revision's retrospective edits are listed apart below.

## The 24 findings

| # | Finding | Outcome |
|---|---|---|
| 1 | Indexed scales and non-whole choices | Fixed: rounds on an indexed scale, refuses a non-whole index |
| 2 | Deep nesting escapes as `RecursionError` | Fixed in `_object_end` |
| 3 | pedalboard's exceptions not wrapped | Fixed: `PluginStateError` / `PluginRenderError`, chained |
| 4 | The census lets `PatchbayValidationError` through | Fixed (Decision 11) |
| 5 | `render` only checks `< 1` | Fixed (Decision 9) |
| 6 | `measure` restores state only on success | Fixed: `try/finally` |
| 7 | Negative container sizes accepted | Fixed, by name |
| 8 | Two diff entries can both be named `tuning` | Fixed: `OpaqueChange.where` (Decision 6) |
| 9 | Choice-name disambiguation can collide | Fixed: lengthened until unique |
| 10 | Windows rounding-mode constant | Fixed: `0x200` on Windows AMD64, skip elsewhere there |
| 11 | Exact float equality against libm results | Fixed (Decision 3) |
| 12 | The census assumes Vital's arm64 build | Fixed (Decision 4) |
| 13 | Parameter objects are held | Docs and standard corrected (Decision 2) |
| 14 | The floating-point guard is opt-in per call site | Fixed: every reach guarded, held by a fake plugin |
| 15 | The render duration depends on pedalboard's truncation | Fixed (Decision 10) |
| 16 | The state's JSON decoded three times | Declined (Decision 7) |
| 17 | `span` recomputed on every conversion | Fixed: `cached_property` |
| 18 | `find_library` eager at import | Fixed: each name looked up lazily |
| 19 | Function-scoped host fixture | Fixed (Decision 5) |
| 20 | `main` writes with plain `write_text` | Fixed: `files.replace_file`, key list first (Decision 8) |
| 21 | Three reason-only errors repeat a body | Fixed (Decision 12) |
| 22 | `_BOOLEAN` reused to mean two points | Fixed: `_TWO_POINTS` |
| 23 | `fit_scale`'s message uses the double span | Fixed: the float32 span |
| 24 | Retrospective edits in the feature's commits | The owner's at commit time (Decision 13) |

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** N/A.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a; `errors` names findings 2 and 3 (a built-in escaping a public
  method), `layout` places `files.py`, `models` keeps the validator finding 16 would have dropped

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `src/` and `tests/` changing under what
  it copies and `files.py` and `test_files.py` added there
- `base/process/standards-retrospective` and `base/process/standards-index` — three project
  standards rewritten, two base proposals
- `base/process/ownership` — the owner commits; the issues filed carry no attribution
- `base/testing/tests` — `test_files.py` mirrors `files.py`; the fake plugin is a unit test's
- `vital/plugin-state`, `vital/parameter-map`, `vital/preset-file` — the rules the findings touch

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes — `bash -n` on every shell script under
`scripts/` as git lists them, with no tracked file a `.gitignore` ignores; `uv sync --locked`, then
`uv run --locked ruff format --config pyproject.toml --check`,
`uv run --locked ruff check --config pyproject.toml`,
`uv run --locked mypy --config-file pyproject.toml` and
`uv run --locked pytest -c pyproject.toml -p no:doctest` under `pyproject.toml`'s `[tool.*]` rule set
and `uv.lock`'s pins; and `scripts/sync-standards.sh --check` against `../patchbay-standards` at the
commit in `agent-os/standards/base/.version` — and the three judgment steps are recorded, in this
order: Docs, Version, then the standards retrospective below.

**Results (2026-11-10):** exit 0 on branch
`feature/7-the-host-and-the-parameter-map-load-vital-through-pedalboard-map-all-903-parameters-to-preset-keys-and-pass-cores-contract-tests-as-a-real-instrument`,
`verification/gate-run.txt`, 451 tests in 39 s, the plugin's integration tests among them and not
skipped (417 in 65 s before this revision).
- **The census regenerates the committed map** with the `machine` field, byte for byte, and the
  key list unchanged: run to a scratch directory and compared with `cmp` before the gate.
- **The old behaviour:** `verification/old-behaviour.txt`, this revision's unit tests against `src/`
  at `eb95567`, 20 failing, each a finding's; `test_errors.py` and `test_host.py` import
  `MachineMismatchError`, new here, so they do not collect against the old code and their findings'
  tests run only on the new.
- **The negative harness:** no gate file changed, but `src/` and `tests/` changed under what it
  copies and `files.py` and `test_files.py` were added there, so it was rerun on the final tree.
  `verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
  `verification/ci-negative-test.txt` `3 runs, 0 unexpected`.
- **CI's own run** of this revision exists only after the owner's push.

**Docs (step 7):** checked against the shipped files, and each reads true:
- `README.md`: the module list names `files.py`; the example runs as written.
- `src/patchbay_vital/host.py`: the module docstring says the wrappers are held and why that is
  safe, that nothing pedalboard raises leaves the host, that a render asks one sample more, and that
  the map is refused on another machine; `render`, `set`, `load_state`, `measure` and
  `parameter_ids` name what they do and raise.
- `src/patchbay_vital/parameters.py`: the module docstring says the record holds together in
  float32 and what the machine is for; `to_preset` says what it rounds and refuses.
- `src/patchbay_vital/state.py`, `census.py`, `errors.py`, `files.py`, `preset.py`
  (`OpaqueChange`) and `format.py` (`dump`, `_opaque_changes`): each says what this revision
  made it do.
- `CLAUDE.md` and `agent-os/product/`: unchanged; none names what changed.
- The three project standards: rewritten in the retrospective below.

**Version (step 8):** this spec's entry under `### Changed` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** a guard around native code held by a fake that perturbs the
   environment on every call (below, and `vital/plugin-state`); data measured from a native build
   recording its machine and refused on another (below, and `vital/parameter-map`); a record held
   together in float32 so another libm reads it (`vital/parameter-map`); a diff entry saying which
   level holds it (`vital/preset-file`); a file-system helper as its own module
   (`vital/preset-file`, and `base/python/layout` already says one concern per module).
2. **A standard wrong or stale:** `vital/plugin-state` said pedalboard's parameter objects are
   never held, which the code and pedalboard's source prove wrong of the wrappers, and said a
   render asks half a sample more; both corrected.
3. **A deliberate deviation:** none. Finding 16 is declined, not a deviation: the standard the
   reviewer's suggestion would have bent, `base/python/models`, is kept.
4. **A pointer moved:** `format._replace_file` is `files.replace_file`; `vital/preset-file` follows.

The retrospective's own change set, to commit apart from the fixes:

- `agent-os/standards/vital/plugin-state.md` — the codec refuses a negative size and deep nesting;
  every reach of the plugin guarded, held by the fake; the wrappers held and the native objects
  never, with pedalboard's reading; nothing pedalboard raises leaving the host; the map refused on
  another machine; a measurement restoring the state however it ends; a render asking one sample
  more and returning the first asked for; the integration module loading Vital once. Verified
  against `host.py`, `state.py`, `tests/unit/test_host.py`, `tests/unit/test_state.py` and
  `tests/integration/test_vital_plugin.py`, the tests named in each rule.
- `agent-os/standards/vital/parameter-map.md` — the census refusing two parameters on one key and
  a refused record, writing whole or not at all; the map recording its machine; the record held in
  float32; an indexed value to the nearest step; a choice taking a whole index only; a made-up
  choice name never colliding. Verified against `parameters.py`, `census.py`,
  `tests/unit/test_parameters.py` and `tests/unit/test_census.py`, the tests named in each rule.
- `agent-os/standards/vital/preset-file.md` — `OpaqueChange.where`; `files.replace_file`. Verified
  against `preset.py`, `format.py`, `files.py`, `tests/unit/test_format.py` and
  `tests/unit/test_files.py`.
- `agent-os/standards/index.yml` — the `vital:` section's three descriptions follow; the `base:`
  section is the sync's and unchanged (gate step 6).

**Which side each rule fell on, and why.** What Vital's plugin, map and file do stayed in
`vital/`. Two rules read true of any adapter hosting native code and went upstream: the fake that
perturbs the environment, as a revision of the proposal that already covers the guard, and the
measured data's machine, as an issue of its own.

Proposals sent upstream: fromtheoutfit/patchbay-standards#34; fromtheoutfit/patchbay-standards#35

### Standards retrospective (proposed, base)

Both approved by the owner, 2026-11-10, with AskUserQuestion.

- `base/testing/tests.md` — a second revision of `fromtheoutfit/patchbay-standards#34`'s third
  proposal (the floating-point environment): every public method that reaches the native code does
  so inside the guard, and one unit test holds all of them with a fake of the native object that
  perturbs the environment on every call. Verified against `src/patchbay_vital/host.py` and
  `tests/unit/test_host.py` (`test_every_public_method_gives_the_environment_back`). Proposed, not
  applied; filed by editing #34's body in place with a "Revised again 2026-11-10" paragraph and a
  bullet added to proposal 3, as the last revision did.
- `base/python/models.md` or `base/testing/tests.md` — data measured from a native build records
  `platform.machine()` and the adapter refuses it on another machine where the data is first used,
  never at load, so the generator still runs there. Verified against
  `src/patchbay_vital/parameters.py` (`ParameterMap.machine`), `census.py` (`build_map`),
  `host.py` (`_parameter_map`), `errors.py` (`MachineMismatchError`) and the tests
  `test_the_map_is_refused_on_another_machine_where_it_is_first_used`,
  `test_the_map_records_the_machine_the_census_ran_on` and
  `test_the_committed_map_holds_every_hosted_parameter`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#35.
