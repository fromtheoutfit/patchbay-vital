# Revision after the review of PR 6

## Context

The owner's review of PR 6 at `6d7f747`
(https://github.com/fromtheoutfit/patchbay-vital/pull/6#issuecomment-6751377414) lists sixteen
findings: ten correctness and six cleanup. Each was checked while shaping against the code, the
tools and the real files, and all hold, #6's evidence being weaker than stated. This revision makes
`load`, `dump` and `diff` keep the promises their docs and the error standard make, so PR 6 is sound
before anything builds on it. No gate file changes.

## Decisions

1. **The scope is the review's sixteen findings**, at the owner's word.
2. **A new spec folder on this branch**, so PR 6 carries it. The reviewed folder stays its record.
3. **#6: `license` stays refused**, at the owner's word. The string sits among config-file strings
   (`errors.txt`, `ttwt_language`), 0 of 77 presets hold it, and the pack catalogue has no such
   field; known means Vital has been seen to write it. A preset carrying it raises
   `UnknownSettingError` naming the key.
4. **#9: only what follows the object is refused**, at the owner's word: one `\n` is allowed, nothing
   else, and `"preset_name":null` is refused. Interior whitespace still loads and is documented as
   normalized. **#14 is declined:** `json.decoder.WHITESPACE` is outside `json`'s `__all__`.
5. **#5 is fixed here**, by a small base on `PatchbayModel` whose pickling carries each proxy as a
   dict and whose deep copy is a shallow one, everything held being immutable (prototyped). Core's
   `Patch` has the same bug and `base/python/models.md` prescribes the proxy, so the retrospective
   proposes the fix upstream.
6. **#3: `dump` writes a temporary file beside the target, keeps the target's mode, then
   `os.replace`s it**, removing the temporary on failure.
7. **#4: `diff` compares floats as written**, the sign of zero included, so `is_empty` means the two
   presets write the same bytes. Model `==` stays Python's.
8. **#11: `settings` and `modulations` are walked by span in the first pass**, one decode fewer. The
   model's own validation stays, so its guarantee does not depend on who built it.
9. **#15: `tests/unit/builders.py`**, a plain module of the shared strategies and builders, at the
   owner's word. `tests/unit/conftest.py` would collide with harness case q, and a function-scoped
   fixture fails hypothesis's health check under `@given`. `base/testing/tests.md` does not place
   helpers in `conftest.py`, so no proposal follows from it.

## Tasks

### Task 1: Save spec documentation

`agent-os/specs/{YYYY-MM-DD-HHMM}-revision-after-pr-6-review/`: `plan.md`, `shape.md` (first
Decision cites the review), `standards.md` (core five, `process/verification-gate`,
`process/standards-retrospective`, `process/ownership`, `testing/tests`, at `e31f7db`),
`references.md` (the reviewed spec; patchbay's `Patch` at `dd2bcad`).

### Task 2: `src/patchbay_vital/preset.py` (#1, #5, #7, #12, #15's serializers)

- A text type refusing what UTF-8 cannot hold, on every metadata field and `source` (#1).
- One annotated read-only mapping type carrying the sort, the proxy and the serializer, used by
  `values` and `opaque`, replacing the two identical serializers (#15).
- The picklable, deep-copyable base under `VitalSettings` and `VitalPreset` (#5).
- `_json_section` uses a NaN-refusing decoder, its span the whole text (#7); `format.py` shares the
  decoder.
- `SLOT_KEY` built from `SLOT_FIELDS` and `NEWER_SLOT_FIELDS`, no named groups (#12).
- `PresetDiff.is_empty`'s docstring says "write the same bytes".

### Task 3: `src/patchbay_vital/format.py` (#2, #3, #4, #8, #9, #10, #11, #13)

- `load` and `dump`: a path `pathlib` refuses (`ValueError`) is `PresetFileError` (#2); atomic write
  (#3).
- `diff` compares floats sign-aware, in settings and slots (#4).
- An unknown key in a routing entry, and a non-float under an unknown name, are
  `UnknownSettingError`; a non-float under a known key stays malformed (#8).
- Only one `\n` may follow the object; a metadata `null` is malformed (#9); the docstring says
  interior whitespace is normalized.
- `join_modulations` raises `MalformedPresetError`, chained, for a slot the model refuses (#10).
- `_members` takes per-key readers, so `settings` and `modulations` are decoded by span once (#11).
- The metadata names derive from `VitalPreset.model_fields` (#13).

### Task 4: `src/patchbay_vital/grisu2.py` (#16)

Drop `_WORD_MASK` from `_multiply`; one constant for 52. `tests/data/grisu2-vectors.txt` holds it.

### Task 5: Tests

`tests/unit/builders.py` holds `FLOATS`, `KEYS`, the empty slot and the preset builder, imported by
`test_format.py` and `test_preset.py` (#15). New: a surrogate refused by the model and by `loads`, and
the false docstring corrected (#1); a NUL path (#2); a failed write leaving the original and no
temporary, the mode kept (#3); the property `diff(a, b).is_empty == (dumps(a) == dumps(b))` including
`-0.0` (#4); pickle, `deepcopy` and `model_copy(deep=True)` (#5); `NaN` and whitespace in a section
(#7); the two format changes named (#8); `null` and each trailing text (#9); interior whitespace
normalized; a half-routed `join_modulations` (#10); `SLOT_KEY` matching every field (#12).

### Task 6 (FINAL): Verification gate

1-6. `scripts/gate.sh`: shell scripts parse; `uv sync --locked` then ruff format; ruff check; mypy;
pytest; `scripts/sync-standards.sh --check`. Exit 0, `verification/gate-run.txt` with date and
branch, the last act before hand-over. `tests/` changes under a directory the harness copies, so
`scripts/gate-negative-tests.sh` and `j` rerun, one transcript each.
7. **Docs**, recorded in `shape.md`.
8. **Version**: `[Unreleased]` in `CHANGELOG.md`; the version stays 0.0.1.
9. **Standards retrospective**, last, from the shipped diff. `agent-os/standards/vital/preset-file.md`
   follows the rules this changes, listed apart. Base proposal expected: `base/python/models.md`, a
   read-only mapping must still pickle and deep-copy, presented to the owner and filed with no
   attribution; core's `Patch` named in it.

Then stop and print `git status --short`. No stage, commit or push.

## Verification

- `scripts/gate.sh` exits 0 with the 75 round trips run, not skipped.
- The negative suite and `j` each end `0 unexpected`.
- Each reproduced finding has a test that failed at `6d7f747`'s behaviour and passes now.
