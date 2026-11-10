# Discovery — the host and the parameter map

The two discovery questions of issue #7, run 2026-11-09 in plan mode and presented to the owner
before any model or module was proposed. The probes were heredocs in the spike's venv; none wrote a
file. Their consolidated re-run in this repository's locked environment, one run, is
`verification/probes.txt` (Task 3).

Probe environment: `~/Code/Audio/vital-spike/.venv` (Python 3.14.7, pedalboard 0.9.26 — latest on
PyPI, 2026-10-07 — mido 1.3.3, numpy 2.5.4); Vital 1.6.4 VST3 at
`/Library/Audio/Plug-Ins/VST3/Vital.vst3` (bundle `audio.vital.synth`, none under
`~/Library/Audio/Plug-Ins/VST3`); macOS arm64. Presets from `~/Music/Vital` against the manifest
(75; `User/` not read). No file written by the probes. Vital source read for facts only, at
`636ca0ef517a4db087a6a08a6a8a5e704e21f836` (2022-04-20; older than 1.6.4, so the plugin is the
authority): `src/plugin/value_bridge.h` 71-81 (text), 91-104 (discrete/boolean), 107-119
(normalized ↔ engine), 134-151 (skew); `src/common/synth_parameters.h` 26-53 (`ValueDetails`, seven
`ValueScale` kinds); `src/common/synth_parameters.cpp` 44-55 (prefixes), 535-602 (group naming).

## Q1 — a .vital preset can be the plugin's state

- `raw_state` (JUCE `VC2!` XML, JUCE base64) and `preset_data` (`.vstpreset`: `VST3`, v1, class id
  `56535456697461766974616C00000000`, `Comp` + empty `Cont`) carry the same component bytes:
  `VstW` (BE 8, 1, 0) + `CcnK` byteSize 178835 `FBCh` v2 `Vita` fxVersion 0x10604 numPrograms 0,
  128 zero bytes, chunk size + chunk = **the preset JSON exactly as a .vital file writes it**
  (`text == json.dumps(obj, sort_keys=True, separators=(",",":"))` → True) + 17 NULs +
  `JUCEPrivateData`.
- One extra top-level key, `tuning` (`{"default": true, "mapping_name": "", "reference_midi_note":
  0.0, "scale": [13 floats], "scale_start_midi_note": 60, "tuning_name": ""}`). The plugin takes a
  state without it, and with nothing, a NUL, or the full trailer after the JSON. `raw_state` set
  works too.
- Setting `preset_data`: median 41 ms, max 1.1 s over 75; pedalboard's values follow (Plucked
  String: `oscillator_1_level` 0.707107→0.671951, `volume` 0.739656→0.816667, `filter_1_switch`
  0→1). A `raw_value` set reaches the state at once.
- JSON-only routing audible: init + slot 1 `lfo_1 → osc_1_level`, amount −1, 20 ms RMS over
  0.2-1.4 s: cv **1.3509** (min 0.0000, max 0.1372) vs control (same amount, empty slot) **0.0176**,
  init 0.0176; max |routed − control| 0.539.
- Caveats: (1) **upgrade on load** — all 75 installed presets ≤ 1.0.0 (50 at 1.0.0); each reads back
  with keys added to 909, `synth_version` 1.6.4, `wavetables`/`sample` re-encoded, `chorus_damping`
  dropped (3), floats moved 1-99+ ulps (437 by 1 … 22 by ≥ 99); (2) **every load delays the sample
  by 4 samples** (leading zeros 4 → 8 → 12 → 16), so no state is a set→get fixed point; but for
  `sample`, init is a fixed point and 68 of 75 old presets are after their first upgrade, 7 move 1-7
  ulps in one gain key; (3) **off-grid snap** — 22 init defaults are off the normalized grid
  (`chorus_feedback` 0.4: engine(default_raw) = 0.39999998); after a host set of that parameter the
  next load lands 0.40000006556510925, a second load 0.4000000059604645; without a prior host set
  loads are exact.
- The committed fixture (`tests/data/init-media-replaced.vital`) loaded as state reads back equal
  but `sample`, with `tuning` added.
- Out-of-range file values: `flanger_dry_wet` 0.7072 (range 0..0.5) in ~25 presets, kept after
  load; `compressor_*_upper_ratio` 1.0025-1.0063 (range 0..1), clamped to 1.0 in two, kept in one;
  `flanger_center` 0.0 and −15.36 in 0.6.4 presets (range 8..136), upgraded to 53.69 / 38.33.

## Q2 — normalized ↔ preset: two kinds, exact

- **Map complete, one-to-one:** 903 parameters, each moving exactly one state float, 903 distinct
  keys, every state float covered. 647 keep their name, 256 renamed (pedalboard's id is the
  snake-cased display name: `envelope_1_attack` ↔ `env_1_attack`; `oscillator`↔`osc`,
  `random_lfo`↔`random`, `*_switch`↔`*_on`, `*_mix`↔`*_dry_wet`, `macro_<n>`↔`macro_control_<n>`,
  compressor band keys lose `compressor_`, …). 448 modulation parameters:
  `modulation_<1..64>_{amount,bipolar,bypass,power,stereo,ramp_up,ramp_down}`. Of
  `settings_keys.txt`'s 456 only `chorus_damping` has no parameter. 2983 hosted parameters, the
  other 2080 JUCE's `MIDI CC <ch>|<n>`, hidden by pedalboard.
- **Linear 552** = float32(r·span + min) with span = float32(max − min), **one rounding**: on 249
  parameters only the fused multiply-add matches. **Indexed 351** = that rounded to a whole number:
  242 booleans named Off/On (pedalboard `is_boolean` false for all), 79 named choices, 25 numeric
  (transposes −48..48, −60..36, voices, polyphony 1..32, oversampling, pitch-bend range, `bypass`),
  5 wide (`effect_chain_order` 0..362879, `*_transpose_quantize` 0..8191). **No parameter unfit**,
  every grid point exact.
- **Display = multiply · skew(preset) + offset:** linear 375, exponential 2^x 142 (incl. 128 ramps),
  inverted 2^−x 18, quartic 30 (envelope secs), quadratic 11, square root 1 (`volume`, −80 dB);
  cubic none. Units seen: none, %, dB, secs/s, semitones, ms, Hz, x, v, voices, c. E.g.
  `filter_1_cutoff` 8..136, display = p − 60 semitones; `envelope_1_attack` 0..2.37842, p⁴ secs;
  `lfo_1_frequency` −7..9, 2^−p secs; `chorus_mix` 0..1, ×100 %.
- Six choices break `Parameter`'s rule: `filter_{1,2,fx}_style` (5-8 named `''`),
  `osc_{1,2,3}_distortion_type` (`FM <- Osc`, `RM <- Osc` twice each).

## Probe 4 — get-after-set exactness

552 continuous (linear 352, exponential 141, inverted 17, quartic 30, quadratic 11, square root 1).
P0 bounds recovered exactly, all 552. P1 values a parameter holds (2000 each): 1,104,000 / 1,104,000
exact, every curve; all 4466 distinct file floats exact. P2 random display values: 0 / 552,000
exact, linear included (float32 quantization). P3 r = f32((x−min)/span) lands exactly: 1,104,000 /
1,104,000. P4 through the plugin: 300 / 300.

## Also recorded

Load 1.15-1.20 s; pedalboard's `parameters` first access 1.08 s more (wrapper set+get 7.7 µs,
typed `_parameters` 0.8 µs). `get_plugin_names_for_file` → `['Vital']`. Rates 1 kHz-768 kHz render
the requested length, finite. 2 s at 48 kHz: 82, 78, 78, 78, 78 ms; 108 ms at 192 kHz. Instances
independent; fresh ones differ only in their random White Noise `sample`; same bytes → same state.
Audio not sample-reproducible (consecutive renders differ; two instances: centroid 4641 vs 4652
Hz). Centroid with filter 1 on: 302 Hz at cutoff 46.4, 2307 Hz at 110.4. pedalboard is GPLv3 and
ships `py.typed` + stubs; mido 1.3.3 MIT.

## Transcripts as presented

Question 1, the state's layout (probe 1c-1d):

```
VstW header: b'VstW' (8, 1, 0)
CcnK: b'CcnK' byteSize 178835 b'FBCh' version 2 b'Vita' fxVersion 0x10604 numPrograms 0
future all zero: True
chunk head b'{"author":"","comments":"","macro1":"MACRO 1","macro2":"MACR'
JSON ends at 178651 of 178683
after JSON: 32 bytes: b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00JUCEPrivateData'
state JSON top-level keys: ['author', 'comments', 'macro1', 'macro2', 'macro3', 'macro4', 'preset_name', 'preset_style', 'settings', 'synth_version', 'tuning']
settings members: 909
structured members of settings: ['custom_warps', 'lfos', 'modulations', 'random_values', 'sample', 'wavetables']
same text as sorted, no-whitespace dump? True
```

Question 1, a routing only in the JSON (probe 1k):

```
init render: shape (2, 96000) float32 peak 0.3584; same state rendered twice, max |difference| 0
slot 1 as the plugin reports it after loading the routed state: {'destination': 'osc_1_level', 'source': 'lfo_1'} | pedalboard modulation_1_amount raw 0.0
  init                               20 ms RMS over 0.2-1.4 s: cv 0.0176, min 0.1409, max 0.1482
  amount -1, no route (control)      20 ms RMS over 0.2-1.4 s: cv 0.0176, min 0.1409, max 0.1482
  lfo_1 -> osc_1_level, amount -1    20 ms RMS over 0.2-1.4 s: cv 1.3509, min 0.0000, max 0.1372
  max |routed - control| 0.539, max |control - init| 0.0327
```

Question 1, the 75 presets as state (probe 1g):

```
presets: 75 synth_version: {'1.0.0': 50, '0.6.1': 1, '0.9.1': 1, '0.9.0': 2, '0.8.6': 10, '0.8.1': 4, '0.6.4': 2, '0.8.5': 4, '0.8.4': 1}
summary: {'differs': 75, 'plugin adds keys': 75, 'some float differs': 74, 'metadata synth_version differs': 75, 'plugin drops keys': 3} | of 1.6.4 presets: {}
differing floats by float32 ulps (99 means 99+): {1: 437, 2: 220, 3: 54, 4: 59, 5: 12, 6: 13, 7: 8, 8: 20, 10: 5, 11: 1, 12: 10, 13: 1, 14: 4, 15: 2, 16: 6, 20: 1, 22: 1, 31: 1, 56: 1, 64: 1, 67: 1, 74: 1, 82: 1, 99: 22}
keys the plugin drops: {'chorus_damping': 3}
structured sections that differ (presets): {'sample': 75, 'wavetables': 75}
set time: median 41.5 ms, max 1114.6 ms
```

Question 2, the census (probes 2e-2f):

```
parameters whose value moves with the grid in exactly one key: 903 of 903; keys distinct: 903; key == pedalboard id: 647
state floats no parameter maps to: []
settings_keys.txt keys no parameter maps to: ['chorus_damping'] | per-slot keys mapped: 448
normalized -> preset value: linear (one float32 rounding of r*span+min): 552 | indexed (that, rounded to a whole number): 351 | neither: []
display = multiply * skew(preset value) + offset, by kind: {'linear': 375, 'exponential': 142, 'exponential_inverted': 18, 'quartic': 30, 'quadratic': 11} (+ square_root 1: volume, probe 2e)
```

Probe 4, get after set:

```
P0 bounds: display(bound) -> preset recovers the bound exactly; failures: []
P1 values the parameter can hold: linear 704000, quadratic 22000, quartic 60000, square_root 2000, exponential 282000, exponential_inverted 34000 exact; not exact 0
P2 random display values: exact 0 for every curve (linear 352000, quadratic 11000, quartic 30000, square_root 1000, exponential 141000, exponential_inverted 17000 not exact)
P3 normalized r = f32((x-min)/span) lands the plugin exactly on x: {True: 1104000}
P4 through the plugin (60 parameters × 5): (state == x, state == engine(r)): {(True, True): 300}
```
