# The .vital Format — Shaping Notes

Shaped 2026-11-09 in plan mode with this repository's customized `/agent-os:shape-spec`. Discovery
ran first and the owner saw its findings before any model was proposed; the shape was then put to
the owner with the evidence for each choice. The spec paused for gate spec #4, which landed
`patchbay-core` and the `integration` marker.

## Core Architecture (Non-Negotiable)

- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models` and
  `base/python/errors` — included without asking (Step 5a); their full text in `standards.md`.

## Scope

Issue #2: parse a `.vital` file into typed models, write it back, diff two presets, and prove the
round trip on every preset Vital installs. No plugin hosting, audio, agent or CLI. CHANGELOG entry,
gate green, `verification/gate-run.txt`. No stage, commit or push by an agent.

## Shaping answers

- **Step 1, scope:** issue #2, amended by discovery and the owner's answers below.
- **Step 2, visuals:** none.
- **Step 3, references:** `references.md`.
- **Step 4, product context:** the mission's "reading, writing and comparing a preset file".
- **Step 5, standards:** the core five, and `process/verification-gate`,
  `process/standards-retrospective`, `process/standards-index`, `process/ownership` and
  `testing/tests`. Snapshot at `e31f7db` in `standards.md`.

## Decisions

1. **The scope is issue #2**: https://github.com/fromtheoutfit/patchbay-vital/issues/2.
2. **`VitalSettings.values: Mapping[PresetKey, float]`**, held to `settings_keys.txt`, 456 lines,
   plain and sorted, at the owner's word. *Known* means Vital has ever written the key, not that every
   file has it; an unknown key stays `UnknownSettingError` and is added in a spec. The list is the
   seed of the next spec's two-namespace map, which makes it structured. Evidence
   (`verification/discovery.md`): every scalar in 77 files is a float; 456 keys, 398 in every file.
3. **`Modulation` holds its per-slot settings by a reversible join**, at the owner's word.
   `modulations` is always all 64 slots, empty ones with whatever floats they carry. `ramp_up` and
   `ramp_down` are `None` where the file lacks that key and are written only when present, each
   independently. `split(join(x)) == x` is a property test over arbitrary slot contents. An empty
   slot's source and destination are `None`, `base/python/models.md` refusing an empty key.
4. **Unknown keys:** an unknown float in `settings` is `UnknownSettingError`; an unknown structured
   section there is kept opaque; an unknown top-level key is refused. **The last deviates from the
   issue's "any unknown section"**, at the owner's word, keeping the typed envelope closed and
   `opaque` one flat mapping.
5. **`opaque: Mapping[PresetKey, bytes]`** holds each section's JSON text as read, `Patch.opaque`'s
   form. Evidence: 98% of the corpus's bytes, up to 10 MB, and the issue's "byte-for-byte".
6. **The claim is `dumps(loads(text)) == text` for every manifest file, with no exceptions**, through
   a port of nlohmann's Grisu2, at the owner's word. Vital links nlohmann::json; `repr` changes 27 of
   the 75 files. `trailing_newline` keeps the 3 that end in one. The port matches the library on
   1,286,646 compared values (`verification/probes.txt`).
7. **`PresetFileError(path, reason)`** joins the issue's errors, `base/python/errors.md` letting no
   `OSError` leave `load` or `dump`. A model built directly refuses as `PatchbayValidationError`
   (`base/python/models.md`); `loads` reports the same refusal as `MalformedPresetError`.
8. **Corpus:** 75 files in `tests/data/factory-manifest.txt`, grouped Factory (7) and packs (68), at
   the owner's word. The walk excludes `User/`, where Vital keeps a person's saves, the owner's two
   init saves among them.
9. **Fixture: `tests/data/init-media-replaced.vital`.** A factory preset cannot be committed (Vital's
   EULA, updated 2024-02-29; a public repository), and the owner's init saves embed Vital's defaults.
   So: the owner's `init-a.vital` from 1.6.4, its 909 settings and structure kept, its sample,
   wavetable audio, LFO shapes and custom warps replaced by values written for the test (a sine, a
   16-sample ramp, a two-point shape), and `preset_name` set to `fixture`. No original `wave_data`,
   "White Noise" or default LFO remains. `random_values` (`{"seed": 4}`) was kept, as a default
   seed and not media.
10. **`pydantic>=2.14.3,<3` joins `[project] dependencies`.** What it does: the field types and
    validators of `preset.py`. Why the standard library cannot: it is the base every model stands
    on. License: MIT. `patchbay-core` brings it in, and `base/python/toolchain.md` has a package
    imported directly declared. Not in the plan; `uv.lock` adds no package.
11. **No CLI yet**, and the contract tests from `patchbay.testing` do not run: there is no `Instrument`
    until the host spec.
12. **Correction to the discovery report:** "shortest digits, ties up" described the corpus and not
    the writer (`verification/discovery.md`, addendum). The owner decided on the port knowing it.

## Context

- **Visuals:** None.
- **References:** `references.md`.
- **Product alignment:** the mission's first bullet.

## Standards Applied

**Core (always applied):**
- `base/python/toolchain`, `base/python/layout`, `base/python/typing`, `base/python/models`,
  `base/python/errors` — Step 5a

**Feature-specific:**
- `base/process/verification-gate` — the harness reruns, `tests/` gaining files it copies
- `base/process/standards-retrospective` — the first project standards, and which side each fell on
- `base/process/standards-index` — this repository's own `vital:` section
- `base/process/ownership` — the owner commits
- `base/testing/tests` — the mirror, property tests, and files read from pytest's root

## Verification Gate

Spec is not complete until `scripts/gate.sh` passes and the three judgment steps are recorded, in
this order: Docs, Version, then the standards retrospective below.

**Results (2026-11-09):** exit 0 on branch
`feature/2-the-vital-format-parse-write-diff-and-round-trip-every-factory-preset`,
`verification/gate-run.txt`, 194 tests, the 75 round trips among them and not skipped. No gate file
changed; `tests/` gained files under a directory the harness copies, so it was rerun:
`verification/gate-negative-tests.txt` ends `141 runs, 0 unexpected` and
`verification/ci-negative-test.txt` `3 runs, 0 unexpected`. `verification/probes.txt` holds the port
against nlohmann::json 3.11.3 (1,286,646 values, 0 differing, the cached powers identical to the
header's) and each integration claim shown to fail: with no install 1 passed and 76 skipped, a
removed file and a new pack each named, 27 files differing through `repr`, 3 with no newline. CI has
no presets, so the integration tests skip there, and the hosted run of this branch exists only after
the owner's push.

**Docs (step 7):** checked and reads true against the shipped files:
- `README.md`: no longer says no adapter code ships; a usage example; Layout names the modules, the
  key list, `tests/integration/` and `tests/data/`; Install names `pydantic`.
- `src/patchbay_vital/__init__.py`'s docstring, and each new module's.
- `agent-os/product/tech-stack.md`: `pydantic`, and the `patchbay-core` line, whose "first whose
  package code imports it" is now true.
- `pyproject.toml`: the `pydantic` entry with its reason.
- `CLAUDE.md`, unchanged: this spec touches none of what it describes.
- `verification/discovery.md`: the record moved in, with the addendum correcting its float rule.

**Version (step 8):** this spec's entry under `### Added` in `[Unreleased]`, `CHANGELOG.md`. The
version stays 0.0.1, no release being cut.

## Standards Retrospective

Step 9, always last. Answered from the shipped diff.

1. **A pattern no standard covers:** several, the first spec about a domain. Sorted below.
2. **A standard wrong or stale:** none.
3. **A deliberate deviation:** none from a standard. Decision 4 departs from the issue's text, and is
   recorded there.
4. **A pointer moved:** none.

**Which side each rule fell on, and why.** The test: would a second adapter, for an instrument that
is not Vital, need this rule?

| Rule | Side | Why |
|---|---|---|
| Where each part of a `.vital` file lives; every scalar a float | `vital/preset-file` | Vital's file format; another instrument's file has its own |
| Known keys mean Vital has ever written them; `settings_keys.txt` | `vital/preset-file` | The list and its meaning are Vital's growth over its versions |
| 64 slots kept; per-slot floats joined by position | `vital/preset-file` | How Vital splits a routing across its JSON |
| Unknown float or top-level key refused, unknown section kept | `vital/preset-file` | Follows from which parts of this file are typed |
| Sections held as the file's text | `vital/preset-file` | The rule is this file's; `Patch.opaque` is already core's |
| A float through a port of nlohmann's Grisu2; never `repr` | `vital/float-writer` | Only an instrument that writes through nlohmann needs it |
| No Vital media committed; the fixture's media replaced | `vital/preset-tests` | Vital's EULA and Vital's defaults |
| The manifest, `~/Music/Vital`, `User/` left out | `vital/preset-tests` | The paths are Vital's; the general form went upstream |
| A test over installed content: manifest as count, never zero | upstream, `base/testing/tests` | Any adapter whose instrument ships content it may not redistribute |
| A port is compared with its original, held by vectors | upstream, `base/testing/tests` | Any adapter that reproduces another program's output |
| An adapter's error root under core's; a reader's refusal chained | upstream, `base/python/errors` | Every adapter meets it, and `errors.md` only had core's case |

- `agent-os/standards/vital/preset-file.md`, `float-writer.md` and `preset-tests.md` — new, this
  repository's first project standards, each rule verified against the shipped module and test it
  names, and against no text of this spec's. Their own change set, listed apart when reported.
- `agent-os/standards/index.yml` — the `vital:` section added for the three; the `base:` section is
  the sync's and unchanged.

Proposals sent upstream: fromtheoutfit/patchbay-standards#32

### Standards retrospective (proposed, base)

- `base/testing/tests.md` — a test over an instrument's installed content: a committed manifest is the
  count, the cases parametrized from it so they cannot pass on zero, skipping with a reason, a file
  missing or unlisted failing by name. Verified against
  `tests/integration/test_factory_round_trip.py` and `verification/probes.txt`. Proposed, not applied;
  filed as fromtheoutfit/patchbay-standards#32.
- `base/testing/tests.md` — a port of a third party's behaviour is compared with that program at a
  named version and held by recorded vectors; agreement with a corpus is not evidence. Verified
  against `src/patchbay_vital/grisu2.py`, `tests/unit/test_grisu2.py` and `verification/probes.txt`.
  Proposed, not applied; filed as fromtheoutfit/patchbay-standards#32.
- `base/python/errors.md` — an adapter's root derives from core's, and a reader reports a model's
  refusal as its own error, chained. Verified against `src/patchbay_vital/errors.py`, `format.py`
  and `test_a_refusal_is_chained_from_what_it_stands_in_for`. Proposed, not applied; filed as
  fromtheoutfit/patchbay-standards#32.
