# Testing against Vital's presets

What this repository's tests may hold of Vital's and how they read the rest. The general form, a
test over an instrument's installed content, is proposed upstream; what is here is the part about
Vital. Written from `tests/integration/test_factory_round_trip.py`, `test_vital_plugin.py` and
`tests/data/`; the evidence
is the `verification/probes.txt` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), and for the skip on another machine the
revision after the second review of PR 9 (`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`).

- **No preset, sample, wavetable, or LFO of Vital's is committed.** Vital's EULA (updated 2024-02-29)
  bars redistributing "presets, samples, wavetables, skins, LFOs or other media created from any
  unaltered VITAL AUDIO content", and this repository is public. A preset that embeds Vital's
  defaults counts: a saved Init carries its White Noise sample and Init wavetables. Verified against
  `tests/data/`.
- **The unit suite's one real file is a save from Vital 1.6.4 with its media replaced**,
  `tests/data/init-media-replaced.vital`: its structure and 909 settings are the save's, and its
  sample, wavetable audio and LFO shapes were written for the test, so the suite holds the current
  key set with none of Vital's media. Verified against `tests/unit/test_format.py`
  (`test_a_preset_comes_back_byte_for_byte`, `test_a_1_6_4_preset_reads_as_its_models`).
- **The installed presets are read from `~/Music/Vital` against
  `tests/data/factory-manifest.txt`**, Vital's own seven and the packs' 68, grouped and reported
  apart. `User/` is where Vital keeps a person's saves, so the walk leaves it out. A file listed and
  missing, or present and unlisted, fails by name, and changing the manifest is a deliberate commit.
  Verified against `tests/integration/test_factory_round_trip.py`
  (`test_the_installed_presets_are_the_manifest_s`) and `verification/probes.txt`.
- **A test of the hosted plugin runs where Vital is installed at the host's `DEFAULT_PATH` and skips
  by name elsewhere**, CI among the places, and skips naming both machines where the committed
  map was measured on another machine than the tests run on: the host would refuse the map there
  and the census test would compare the other machine's name, and a new census is the remedy,
  not a failing test. It reads the same manifest and the same fixture, the fixture loaded as the
  plugin's state. What the plugin reports about itself, its parameters'
  names, ranges and display texts, is an interoperability fact and is committed as the parameter
  map; the plugin's own state, which embeds its default media, is never committed. Verified against
  `tests/integration/test_vital_plugin.py` (the `vital` and `host` fixtures,
  `test_every_installed_preset_loads_as_state`,
  `test_the_fixture_as_state_reads_back_but_its_sample_delayed`) and
  `src/patchbay_vital/data/parameters.json`.
