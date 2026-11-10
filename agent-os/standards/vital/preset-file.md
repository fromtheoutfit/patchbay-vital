# The preset file

What a `.vital` file holds and how this package holds it. A rule here is about Vital's file; what
any adapter's models do is `base/python/models.md`'s. Written from `src/patchbay_vital/preset.py` and
`format.py`; the evidence is the `verification/discovery.md` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), measured over 75 installed presets and two
saves from Vital 1.6.4, and for the plugin state's `tuning` and the derived key list the
`verification/` of the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`).

## Where each part lives

- **A file is one JSON object of metadata and `settings`, and `settings` holds everything else**:
  float scalars, the routing list `modulations`, and the structured sections `wavetables`, `lfos`,
  `sample`, `custom_warps` and `random_values`. None of those is at the top level. Verified against
  `format.py` (`_read_settings`) and `tests/unit/test_format.py`
  (`test_a_1_6_4_preset_reads_as_its_models`).
- **Every scalar in `settings` is a JSON float**, written with a point, and each is exactly a float32
  widened to a double. An int, a string, a bool or a null there is malformed. Verified against
  `format.py` and `test_a_malformed_preset_is_refused_as_the_package`.
- **The plugin's state is the same text with one more top-level key, `tuning`, an object held as
  its text, like an unread section**, in `VitalPreset.tuning`: written back at its sorted place when
  present, absent from every `.vital` file seen and not added to one, compared by `diff` by name and
  size after the sections, its `OpaqueChange.where` `preset` where a section under `settings` is
  `settings`, so a section there named `tuning`, which an unknown section may be, is told from it.
  Anything but an object under the key is malformed. Verified against `preset.py`, `format.py` and
  `test_a_plugin_state_comes_back_byte_for_byte`,
  `test_a_file_without_a_tuning_is_written_without_one`,
  `test_a_tuning_that_is_not_an_object_is_malformed`,
  `test_a_diff_reports_the_tuning_after_the_sections`,
  `test_a_section_under_settings_named_tuning_is_told_from_the_preset_s`.
- **Metadata is strings: `author`, `comments`, `macro1` to `macro4`, `preset_style`,
  `synth_version`, and `preset_name`, which files before 1.6.4 lack.** `preset_style` is a plain
  string: a save names none, and writes `""`. Verified against `preset.py` (`VitalPreset`) and
  `test_a_file_without_the_newer_keys_comes_back_without_them`.

## Known keys

- **A float key is known when Vital has ever been seen to write it, not when every file has it.**
  `settings_keys.txt` lists them, one a line, sorted. A key a file lacks is simply absent, because
  Vital adds keys as it grows; `settings` holds 723 keys at 0.6.1 and 909 at 1.6.4, and `chorus_damping`
  appears only in the oldest. A newer Vital's new key is added to the list in a spec, not carried
  silently. The list is deliberately plain and is derived from the parameter map: its keys but the
  per-slot ones, and the keys only presets hold (`vital/parameter-map.md`). Verified against
  `src/patchbay_vital/settings_keys.txt`, `preset.py` (`KNOWN_SETTINGS`),
  `tests/unit/test_preset.py` (`test_the_known_keys_are_a_plain_sorted_list`) and
  `tests/unit/test_parameters.py` (`test_the_format_s_key_list_is_derived_from_the_committed_map`).
- **A key Vital is not known to write is `UnknownSettingError`, naming it, whatever its value's type
  and wherever it is: in `settings`, in a routing entry or at the top level. The one exception is
  an unknown structured section under `settings`, which is kept.** So a change of format is noticed
  as one, with its key, and a new section still round-trips. A non-float under a *known* key is
  malformed. `license` is a string in the Vital binary and no file has been seen with the key, so it
  is not known. Verified against `format.py` and `test_an_unknown_float_is_named`,
  `test_a_new_key_in_a_routing_entry_is_named`, `test_a_non_float_under_an_unknown_name_is_named`,
  `test_an_unknown_top_level_key_is_named`, `test_an_unknown_section_is_kept_and_written_back`.

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
- **After the object a file may hold one newline and nothing else, and a metadata key is a string or
  absent, never `null`.** Those would be lost on writing with nothing to say so. Whitespace inside the
  object is read and normalized, carrying no data, and a file Vital saved has none. Verified against
  `format.py` (`_parse`), `test_a_malformed_preset_is_refused_as_the_package` and
  `test_whitespace_inside_a_preset_is_read_and_not_written_back`.
- **`dump` replaces a file whole or not at all**, through a temporary beside it, keeping its
  permissions and writing through a symlink, because a preset can be a person's only copy. The
  replacing is `files.replace_file`, a module of its own because the census writes its two outputs
  through it too, one concern per module (`base/python/layout.md`). Verified against `files.py`,
  `format.py` (`dump`), `tests/unit/test_files.py`, `test_a_failed_write_leaves_the_file_as_it_was`,
  `test_writing_over_a_file_keeps_its_permissions` and `test_writing_through_a_symlink_keeps_the_link`.
- **Two presets are the same when they write the same bytes**, so `diff` tells `0.0` from `-0.0`,
  which compare equal. Verified against `format.py` (`_same`) and
  `test_a_diff_is_empty_exactly_when_the_presets_write_the_same`.
