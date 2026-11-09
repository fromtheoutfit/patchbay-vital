# Issue #2: the .vital format

## Context

The VST3 exposes no modulation routing or wavetable selection; both live only in the preset file, so
the adapter must own that file before it can build a patch. This spec parses a `.vital` file into
typed models, writes it back, diffs two presets, and proves the round trip on every preset Vital
installed here. Pure Python over text: no hosting, audio, agent or CLI. Discovery came first and the
owner decided the shape from it; `patchbay-core` and the `integration` marker landed in #4.

## Decisions

1. **The scope is issue #2**, as discovery and the owner's answers amend it below.
2. **`VitalSettings.values: Mapping[PresetKey, float]`**, keys held to `settings_keys.txt`, 456 lines,
   plain and sorted. *Known* means Vital has ever written the key, not that every file has it, so an
   absent key is legal and an unknown one is `UnknownSettingError`, added in a spec. The list is the
   seed of the next spec's two-namespace map, which makes it structured. Evidence: every scalar in
   77 files is a float; 456 keys, 398 in every file; 723-909 settings by version.
3. **`Modulation` holds its per-slot settings, by a reversible join.** `modulations` is always all
   64 slots, empty ones included with whatever scalars they carry. `ramp_up` and `ramp_down` are
   `None` where the file lacks that key and are written only when present, each independently. An
   empty slot's source and destination are `None` (`models.md` forbids an empty key). Evidence: 64
   slots in 77 files; 3,312 empty, 19 with a non-zero amount; 7 presets with gaps; 5 fields through
   1.0.0, 7 at 1.6.4.
4. **Unknown keys:** an unknown float in `settings` is `UnknownSettingError`; an unknown structured
   section in `settings` is held opaque; an unknown top-level key is refused, a deviation from the
   issue's "any unknown section" that keeps the typed envelope closed.
5. **`opaque: Mapping[PresetKey, bytes]`** holds each section's JSON text as read, the form
   `patchbay.Patch.opaque` takes. `line_mapping` is bytes the same way.
6. **The claim is `dumps(loads(text)) == text` for every manifest file, no exceptions.** Floats go
   through a port of nlohmann's Grisu2 (Vital links nlohmann::json), which ties-up and `repr` do not
   reproduce in general; `trailing_newline` keeps the 3 Factory files that end in one.
7. **`PresetFileError(path, reason)`** joins the issue's errors, since `base/python/errors.md` lets no
   `OSError` leave `load` or `dump`. A model's own refusal stays `PatchbayValidationError`
   (`models.md`); `loads` raises it as `MalformedPresetError`.
8. **Corpus:** 75 files in a committed `tests/data/factory-manifest.txt`, grouped Factory (7) and
   packs (68); the test names any file missing or unlisted; the walk excludes `User/`.
9. **Fixture:** init-a with its sample, wavetable audio and LFO shapes replaced by values we write.
   A factory preset cannot be committed (Vital's EULA, updated 2024-02-29; a public repository).
10. **No CLI yet**, and the contract tests from `patchbay.testing` do not run: there is no
    `Instrument` until the host spec.

## Tasks

### Task 1: Save spec documentation

`agent-os/specs/{YYYY-MM-DD-HHMM}-the-vital-format/`: `plan.md`, `shape.md` (first Decision cites
the issue), `standards.md` (core five, `process/verification-gate`,
`process/standards-retrospective`, `process/standards-index`, `process/ownership`, `testing/tests`,
at `e31f7db`), `references.md` (patchbay's `models.py` and `errors.py` at `dd2bcad`;
`tests/unit/test_version.py`). `verification/discovery.md` is
`~/.claude/plans/issue-2-discovery-record.md` with this shaping's addendum: the 77-of-77 prototype,
and the correction that "ties up" described the corpus, not the writer.

### Task 2: Probe the float writer against nlohmann

Port `to_chars` (Grisu2 and its formatting). In a scratch directory, compile a small program against
nlohmann's `json.hpp` with clang++ and compare it with the port over every float token in the 77
files, over a million random float32s including the divergent binades, and over doubles and edge
cases. Into `verification/probes.txt`. A sample, the divergent values among it, becomes
`tests/data/grisu2-vectors.txt`, so the unit suite holds the port with no compiler. **If the port
disagrees with nlohmann, stop and report.**

### Tasks 3-9, in the order of `base/python/layout.md`, gate green after each

3. `errors.py`, `tests/unit/test_errors.py`: `VitalFormatError(PatchbayError)`,
   `UnknownSettingError(key)`, `MalformedPresetError(reason)`, `PresetFileError(path, reason)`.
4. `grisu2.py`, with nlohmann's MIT notice, `tests/unit/test_grisu2.py`: the vectors, the exponent
   forms, and a property that `float(format_float(x)) == x`.
5. `preset.py`, `settings_keys.txt`, `tests/unit/test_preset.py`: the models; mappings sorted and
   read-only with the wrap serializer, unhashable, base64 for bytes (`Patch`'s form); exactly 64
   slots; source and destination set together. Property tests of `Modulation` and settings.
   `settings_keys.txt` is the union over the 77 files less the slot and structured keys.
6. `format.py`, `tests/unit/test_format.py`: `loads`, `dumps`, `load`, `dump`, walking the top level
   and `settings` by span with `JSONDecoder.raw_decode`; duplicate keys, NaN, a non-float scalar, a
   wrong shape, bad UTF-8 or deep nesting are each `MalformedPresetError`, chained, with nothing
   from pydantic or json escaping. `join_modulations` and `split_modulations` are public in the
   module, with a property that `split(join(x)) == x` over arbitrary slot contents.
7. `diff(a, b) -> PresetDiff` with its change models, in deterministic order; opaque by name and size
   only. Properties: `diff(a, a)` is empty; `diff(a, b)` applied to `a` gives `b` for settings.
8. `tests/data/factory-manifest.txt` and the fixture, built by a throwaway script; its provenance in
   `shape.md`. `tests/integration/test_factory_round_trip.py`, marked `integration`: parametrized
   over the manifest so it never passes on zero cases, the manifest's length asserted at 7 + 68, a
   test naming missing and unlisted files, skipped with its reason where `~/Music/Vital` is absent.
9. `__init__.py` re-exports; `tests/unit/test_package.py` holds the surface.

### Task 10: Docs

`README.md` (no longer "no adapter code", the Layout's `tests/` and `data`),
`src/patchbay_vital/__init__.py`'s docstring, `agent-os/product/tech-stack.md`.

### Task 11 (FINAL): Verification gate

1-6. `scripts/gate.sh`: shell scripts parse; `uv sync --locked` then ruff format; ruff check; mypy;
pytest; `scripts/sync-standards.sh --check`. Exit 0, `verification/gate-run.txt` with date and branch,
the last act before hand-over. No gate file changes, but `tests/` gains files under a directory the
harness copies, so `scripts/gate-negative-tests.sh` and `j` rerun, one transcript each.
7. **Docs**, recorded in `shape.md`.
8. **Version**: `[Unreleased]` in `CHANGELOG.md`; the version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff. Rules about Vital's file are written
   under `agent-os/standards/vital/` and indexed in this repository's own `vital:` section; only a
   rule a second adapter would need goes upstream, presented to the owner and filed with no
   attribution. `shape.md` says explicitly which side each rule fell on and why.

Then stop and print `git status --short`. No stage, commit, push or PR.

## Verification

- `scripts/gate.sh` exits 0 with the integration tests run here (75 round trips), not skipped.
- `dumps(loads(text)) == text` on all 75, and on the fixture.
- `verification/probes.txt` shows the port and nlohmann agree on every compared value.
- The negative suite and `j` each end `0 unexpected`.
