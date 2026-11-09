# Mission

patchbay is headless control of software instruments from Python. This repository is its adapter
for Vital: what a program needs to know about that one instrument, as code and as data. It plugs
into `patchbay-core`, whose contracts every adapter implements.

## What the adapter is

- The `.vital` format: reading, writing and comparing a preset file.
- The map between Vital's VST3 parameters and a preset's keys, and the unit conversions between
  them, so a value means the same thing on either side.
- Sound-design semantics as data: what a parameter does to the sound, written down where a program
  can read it.

## What the adapter is not

- No agent code. What decides which sound to make lives elsewhere; this repository describes the
  instrument.
- No audio analysis. Listening to what the instrument rendered is not the adapter's job.
- Not a product. An experiment in controlling instruments without their screens, kept honest by
  the gate and the standards.
