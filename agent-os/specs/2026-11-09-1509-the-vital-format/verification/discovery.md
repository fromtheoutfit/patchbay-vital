# Discovery record for issue #2


All figures measured 2026-11-09, read-only, Vital 1.6.4 installed, Python's `json` over the files.

## Where the presets are

- Data directory: `~/Music/Vital` (Vital.config `data_directory`). App bundle holds no presets.
- 75 `.vital` files, 93,082,828 bytes; size min 119,040, median 753,731, max 10,126,117.
- `Factory/Presets`: 7, all author Matt Tytel. 12 artist pack folders: 68.
- Init preset: no file anywhere. "Init Preset" / "Initialize Preset" are strings in the binary.
- Newest `synth_version` in the corpus is 1.0.0; no file written by 1.6.4 exists on this machine.
  Versions: 1.0.0 x50, 0.8.6 x10, 0.8.1 x4, 0.8.5 x4, 0.9.0 x2, 0.6.4 x2, 0.9.1, 0.6.1, 0.8.4.

## Top level

Nine keys, in all 75, all JSON strings except `settings`: `author`, `comments`, `macro1`..`macro4`,
`preset_style`, `settings` (object), `synth_version`. `comments` empty in 30. `preset_style` seen:
Bass 19, Sequence 13, Pad 11, Keys 9, Experiment 7, Percussion 6, Lead 5, SFX 3, Template 2.

`settings` holds BOTH the scalars and the four structured sections: `modulations`, `wavetables`,
`lfos`, `sample`. None of them is top-level.

## Settings

- Key union 776 = 772 scalars + 4 structured. 722 keys in every file; 54 in some.
- Key count tracks version: 723 (0.6.1, x1), 726 (0.6.4, x2), 774 (0.8.1, x4), 775 (x68).
- 57,671 scalar values: every one a JSON float token; no int, string, bool or null. Every one is
  exactly a float32 widened to a double.
- Seen values: only 0/1 on 361 keys, whole numbers on 94, fractional on 317. "Seen" undercounts
  the range. VST3 metadata marks all 903 "discrete", so it does not separate flags from enums.
- Ranges are Vital's internal units, not the VST3 display: `volume` 4077..7399 (VST3 -80..6.02 dB);
  `filter_1_cutoff` 8..136; `effect_chain_order` 0..338842; `osc_1_wave_frame` 0..256.

## Modulations

- `settings.modulations`: exactly 64 entries in all 75. 4,800 entries, 1,616 used, 3,184 empty
  (`source` and `destination` both `""`); no half-empty entry.
- List entry keys: `source`, `destination`, and `line_mapping` on 74 entries.
- amount / bipolar / bypass / power / stereo are NOT in the list. They are settings scalars
  `modulation_<1..64>_<field>`: 320 keys, all present in all 75.
- 7 presets have gaps between used slots. 19 empty slots hold a non-zero amount, 1 a bipolar of 1.
- 221 distinct destinations, all settings keys. Sources: macro_control_N 682, lfo_N 430, env_N 155,
  mod_wheel 90, velocity 79, random_N 73, stereo 40, note 22, random 16, lift 13, note_in_octave 8,
  aftertouch 7, pitch_wheel 1.

## Wavetables, LFOs, sample

Inline JSON with base64 strings inside it. Sizes of the compact JSON, bytes (min/median/max):

| Section | min | median | max | shape |
|---|---|---|---|---|
| wavetables | 12,667 | 176,365 | 4,195,833 | always 3; groups > components > keyframes |
| sample | 1,903 | 117,670 | 9,925,067 | length, name, sample_rate, samples, samples_stereo (16 files) |
| lfos | 863 | 927 | 11,626 | always 8; name, num_points, points, powers, smooth |

- wavetables + sample are 98% of all bytes in the corpus.
- `wave_data`: 412 strings, 10,924 chars, 8,192 bytes decoded, all canonical base64.
- `audio_file`: 65 strings, up to 1,398,104 chars. `samples`: decoded bytes = 2 x `length`.
- 8 component types: Wave Source 144, Audio File Source 65, Line Source 16, Wave Folder 7,
  Frequency Filter 6, Wave Warp 5, Phase Shift 3, Wave Window 2.

## Writer determinism

- No BOM, no CR, no duplicate key, no null at any depth; every object's keys sorted, at every depth.
- Compact separators; raw UTF-8 (1 file has non-ASCII).
- 68,969 float tokens. `repr` differs from the file on 32 (29 scalars, 1 line_mapping, 2 wavetable
  values), every one an exact decimal tie that the file rounds up and `repr` rounds to even.
- sort + compact + raw UTF-8 + shortest digits with ties up: 0 of 68,969 tokens mismatch; reproduces
  72 of 75 files byte for byte, and the other 3 but for a trailing `\n`.
- The 3 with a trailing newline: Factory FM Drum Circle, Shepard Tone Template, Text To Wavetable
  Template. Cause unknown.
- NOT observed: Vital writing the same preset twice. The evidence is that one pure function
  reproduces its output.

## Ten varied presets

Plucked String, Touch Tone, Railgun, Fleet, Thumpus, Memory Leak, Strings Section, Horror of
Melbourne 1, Honk Wub, Synthetic Quartet. Of 772 scalars, 426 identical across all ten, 346 vary;
adjacent pairs differ on 117-186 scalars.

## Key spelling against vital_params.json

903 VST3 parameters. Against the 75 files alone: 518 preset keys match exactly and 253 more map by
rule (name only; meaning and units not verified). Against init-a (1.6.4, below), which has exactly
903 float scalars: 647 match exactly and 256 map by the rules below, so every VST3 parameter has a
preset key. The one preset key with no VST3 name is `chorus_damping` (the 3 oldest presets).

| Preset | VST3 | Keys |
|---|---|---|
| `osc_N_X` | `oscillator_N_X` | 66 |
| `osc_N_on` | `oscillator_N_switch` | 3 |
| `osc_N_random_phase` | `oscillator_N_phase_randomization` | 3 |
| `osc_N_spectral_morph_{amount,spread,type}` | `oscillator_N_frequency_morph_*` | 9 |
| `osc_N_frame_spread` | `oscillator_N_unison_frame_spread` | 3 |
| `osc_N_unison_blend` | `oscillator_N_blend` | 3 |
| `env_N_X` | `envelope_N_X` | 54 |
| `random_N_X` | `random_lfo_N_X` | 24 |
| `random_N_keytrack_{transpose,tune}` | `random_lfo_N_{transpose,tune}` | 8 |
| `lfo_N_keytrack_{transpose,tune}` | `lfo_N_{transpose,tune}` | 16 |
| `lfo_N_delay_time` | `lfo_N_delay` | 8 |
| `lfo_N_fade_time` | `lfo_N_fade_in` | 8 |
| `X_on` | `X_switch` | 12 |
| `X_dry_wet` | `X_mix` | 5 |
| `compressor_{band,high,low}_{lower,upper}_{ratio,threshold}` | same, no `compressor_` | 12 |
| `macro_control_N` | `macro_N` | 4 |
| `reverb_{high,low}_shelf_{cutoff,gain}` | `reverb_{high,low}_{cutoff,gain}` | 4 |
| `delay_aux_{frequency,sync,tempo}` | `delay_{frequency,sync,tempo}_2` | 3 |
| `filter_X_blend_transpose` | `filter_X_comb_blend_offset` | 3 |
| `filter_X_keytrack` | `filter_X_key_track` | 3 |
| `chorus_{cutoff,spread}` | `chorus_filter_{cutoff,spread}` | 2 |

## The owner's 1.6.4 saves (User/Presets/init-a.vital, init-b.vital)

Saved by the owner from Vital 1.6.4 with Initialize Preset then Save As. 178,478 bytes each.

- **Determinism, observed:** the two files differ in 1 byte, the `a`/`b` of `preset_name`. With that
  value normalised they are byte-identical.
- **Writer rule holds:** sorted, compact, shortest digits with ties up reproduces both byte for byte.
  No trailing newline. Every float scalar is exactly a float32.
- **Top level has a tenth key:** `preset_name`, in neither version of the 75. `preset_style`,
  `author` and `comments` are `""`.
- **Settings: 909 keys against 775 at 1.0.0.** All 134 additions are new; nothing at 1.0.0 is gone
  (`Plucked String`: 0 keys missing from init). Corpus-wide union with init: 910 keys (904 float
  scalars, 6 structured).
  - `modulation_<1..64>_ramp_up` / `_ramp_down` (128), default -10.0 in all 128.
  - `osc_<1..3>_spectral_morph_phase` (3), default 0.5. `mpe_enabled` (1).
  - `custom_warps` (list of 3 LFO-shaped objects, 325 bytes) and `random_values` (list of 3
    `{"seed": 4}`, 34 bytes), both new, non-float structured sections.
- **Against the oldest (Touch Tone, 0.6.1):** init has 187 keys it lacks; it has `chorus_damping`,
  the one key init lacks. **Against 1.0.0:** all 50 files at 1.0.0 share one key set; init adds the 134.
- **So modulation has seven per-slot settings at 1.6.4:** amount, bipolar, bypass, power, stereo,
  ramp_up, ramp_down. 64 slots, 0 used in init.
- **Payloads:** sample "White Noise" (117,670 bytes, 44,100 at 44,100 Hz), three wavetables named
  "Init" (33,451 bytes), eight default LFOs (each identical to 425 LFOs in the corpus). The sample
  and `wave_data` hashes occur in none of the 75.
- **Manifest scope:** `User/` is where Vital puts a person's own saves; a glob of the root now finds
  77. The factory manifest's walk excludes `User/`.

## Constraints the findings raise

- Issue: `Modulation` carries amount etc. "as the file has them"; the file has them in `settings`,
  joined by slot number, and has a fifth field (bypass) the issue does not list.
- `models.md`: "an id is non-empty wherever it appears"; an empty slot's destination is `""`.
- Fixture: the Vital EULA (updated 2024-02-29) bars redistributing "presets, samples, wavetables,
  skins, LFOs or other media created from any unaltered VITAL AUDIO content distributed with the
  SOFTWARE PRODUCTS". This repository is public.
- patchbay-core: version 0.0.1 at main `dd2bcad69dadeb38c6e1e660b2e0ddced13861eb` (the checkout is on
  a fix branch; read through `git show main:`). Not on PyPI, no tags or releases; repo public.
  A resolvable source needs `[tool.uv.sources]`, inside the `[tool.*]` the repo calls gate-owned.
- `integration` marker: `--strict-markers` needs it registered; `toolchain.md` says under `markers`
  in `[tool.pytest.ini_options]`, also gate-owned.

## Owner's answers so far (2026-11-09)

- Corpus: all 75, Factory and packs reported apart, asserted against a committed
  `tests/data/factory-manifest.txt` of paths relative to the root; the test fails naming any listed
  file missing and any unlisted file present. The manifest's length is the count.
- 1.6.4 evidence: the two saves above, findings added to this record.
- Gate-owned entries: shape a small gate spec first (`[tool.uv.sources]` pin to patchbay at dd2bcad
  with its range, and the integration marker), land it, resume #2 on top. Its retrospective proposes
  upstream that `verification-gate.md` narrow which `[tool.*]` entries are gate files.
- Fixture: init-a with its media replaced. Its real 1.6.4 structure and 909 settings stay; the
  sample, wavetable audio and LFO shapes are values we write, so no Vital media is committed.

## Next for #2

After the gate spec is landed: the shape of VitalSettings for the owner, then #2's plan.

## Addendum from shaping (2026-11-09)

Measured read-only over the 75 files and the owner's two 1.6.4 saves (77).

- **A prototype of the design reproduced 77 of 77 files byte for byte**: the top level and `settings`
  walked by span, float scalars parsed, five sections kept as raw text, per-slot fields joined to the
  modulation list and split back. 93.4 MB loaded in 164 ms and dumped in 86 ms.
- Across 77 files: 9 top-level keys in all, `preset_name` in 2; 5 opaque sections (`custom_warps`,
  `lfos`, `random_values`, `sample`, `wavetables`); 456 non-modulation float keys, 398 in every file;
  64 slots always; 5 fields per slot through 1.0.0 and 7 at 1.6.4; 3,312 empty slots, none with
  `line_mapping`.
- Vital links nlohmann::json (`N8nlohmann6detail11parse_errorE` and others in the binary).
- **Correction to "Writer determinism" above.** "Shortest digits with ties up" describes the corpus,
  not the writer. nlohmann writes doubles with Grisu2, which is not always shortest:
  0.2631068825721741 comes out with 17 digits. The rule and Grisu2 agree on every value in the 77
  files and disagree on random float32s: 0.42% in [0.25, 0.5), 0.015-0.19% lower, none at 0.5 and
  above (40,000 per binade). The corpus's 3,776 distinct float32s would be expected to show 3.5 such
  values if their mantissas were uniform, and they are not: many carry trailing zero bits.

## Owner's decisions on the shape (2026-11-09)

- `VitalSettings` is a mapping held to a known-key list. Known means Vital has ever written the key,
  not that every file has it. Unknown keys stay an error, added in a spec. `settings_keys.txt` is a
  plain sorted list now and the seed of the next spec's two-namespace map.
- `Modulation` holds its per-slot settings by a reversible join: always all 64 slots, empty ones
  included with whatever scalars they carry; a property test proves `split(join(x)) == x`. The newer
  fields are `None` when the file lacks their keys and written back only when present.
- Unknown keys: strict for scalars, opaque for sections under `settings`, refused at the top level.
- The round trip is byte-identical for every manifest file, through a port of Grisu2.
