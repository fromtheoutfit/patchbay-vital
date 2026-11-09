# The preset file

What a `.vital` file holds and how this package holds it. A rule here is about Vital's file; what
any adapter's models do is `base/python/models.md`'s. Written from `src/patchbay_vital/preset.py` and
`format.py`; the evidence is the `verification/discovery.md` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), measured over 75 installed presets and two
saves from Vital 1.6.4.

## Where each part lives

- **A file is one JSON object of metadata and `settings`, and `settings` holds everything else**:
  float scalars, the routing list `modulations`, and the structured sections `wavetables`, `lfos`,
  `sample`, `custom_warps` and `random_values`. None of those is at the top level. Verified against
  `format.py` (`_read_settings`) and `tests/unit/test_format.py`
  (`test_a_1_6_4_preset_reads_as_its_models`).
- **Every scalar in `settings` is a JSON float**, written with a point, and each is exactly a float32
  widened to a double. An int, a string, a bool or a null there is malformed. Verified against
  `format.py` and `test_a_malformed_preset_is_refused_as_the_package`.
- **Metadata is strings: `author`, `comments`, `macro1` to `macro4`, `preset_style`,
  `synth_version`, and `preset_name`, which files before 1.6.4 lack.** `preset_style` is a plain
  string: a save names none, and writes `""`. Verified against `preset.py` (`VitalPreset`) and
  `test_a_file_without_the_newer_keys_comes_back_without_them`.

## Known keys

- **A float key is known when Vital has ever been seen to write it, not when every file has it.**
  `settings_keys.txt` lists them, one a line, sorted. A key a file lacks is simply absent, because
  Vital adds keys as it grows; `settings` holds 723 keys at 0.6.1 and 909 at 1.6.4, and `chorus_damping`
  appears only in the oldest. A newer Vital's new key is added to the list in a spec, not carried
  silently. The list is deliberately plain: the two-namespace map makes it structured. Verified
  against `src/patchbay_vital/settings_keys.txt`, `preset.py` (`KNOWN_SETTINGS`) and
  `tests/unit/test_preset.py` (`test_the_known_keys_are_a_plain_sorted_list`).
- **An unknown float in `settings` or an unknown top-level key is `UnknownSettingError`, naming it;
  an unknown structured section under `settings` is kept.** So a change of format is noticed where
  it would change meaning, and a new section still round-trips. Verified against `format.py` and
  `test_an_unknown_float_is_named`, `test_an_unknown_top_level_key_is_named`,
  `test_an_unknown_section_is_kept_and_written_back`.

## Modulations

- **A slot is split across the file: `source`, `destination` and an optional `line_mapping` in the
  routing list, its floats as `modulation_<slot>_<field>` scalars**, matched by position.
  `Modulation` holds both, and `settings_keys.txt` holds none of the per-slot keys. Five fields are
  in every file; `ramp_down` and `ramp_up` only from 1.6.4, each `None` where the file lacks its key
  and written only when present. Verified against `format.py` (`join_modulations`,
  `split_modulations`) and `test_split_reverses_join_over_arbitrary_slot_contents`.
- **A preset has exactly 64 slots, used or not, and every one is kept.** Used slots can have gaps
  between them, so position is the slot, and an empty slot can still hold a non-zero amount, so it
  is not dropped. An empty slot's source and destination are `""` in the file and `None` on the
  model. Verified against `preset.py` (`Modulation`, `VitalPreset`) and
  `test_a_value_left_on_an_empty_slot_survives`.

## What is left unread

- **A section this package does not interpret is held as the text the file held, as bytes**, in
  `VitalPreset.opaque`, the form `patchbay.Patch.opaque` takes, and `line_mapping` the same way. They
  are 98% of a preset's bytes, base64 inside JSON, up to 10 MB. Keeping the text is what makes them
  byte-for-byte; re-encoding parsed JSON is not. Verified against `format.py` and
  `tests/integration/test_factory_round_trip.py`.
- **The file writes keys sorted at every depth, no whitespace, UTF-8 raw**, and three of Vital's own
  presets end in a newline, which `trailing_newline` keeps. `dumps(loads(text)) == text` for a file
  Vital saved. How a float is written is `vital/float-writer.md`'s. Verified against `format.py`
  (`dumps`), `test_a_trailing_newline_survives` and the integration test.
