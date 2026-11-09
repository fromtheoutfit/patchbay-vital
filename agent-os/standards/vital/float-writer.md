# The float writer

How a float in a `.vital` file is written, so a preset comes back byte for byte. Written from
`src/patchbay_vital/grisu2.py`; the evidence is the `verification/probes.txt` of the spec of issue
#2 (`agent-os/specs/2026-11-09-1509-the-vital-format/`).

- **Vital writes through nlohmann::json, so a float is written by a port of its `to_chars`**: the
  Grisu2 digits and nlohmann's format, a point up to 15 integer digits and from 1e-05 an exponent
  `e-05` or `e+15` of at least two digits. Vital links the library (its symbols are in the binary).
  Verified against `src/patchbay_vital/grisu2.py` and `tests/unit/test_grisu2.py`
  (`test_a_value_is_written_in_nlohmann_s_form`).
- **`repr` is not the writer.** It gives the shortest digits, and Grisu2 does not always. Python
  rounds an exact tie to even where the files round it up (`81.63211059570313`, 32 tokens in the
  corpus), and near the edge of a value's rounding interval Grisu2 gives one digit more
  (`0.26310688257217407`). Writing through `repr` changes 27 of the 75 installed presets. Verified
  against `verification/probes.txt`.
- **A rule fitted to the corpus is not the writer either.** "Shortest digits, ties up" matched every
  value in 77 files and disagrees with Grisu2 on up to 0.42% of other float32s, because the corpus
  happens to hold none of them. The check on a port is the library, not the data. Verified against
  `verification/probes.txt` and `verification/discovery.md`'s addendum.
- **The port is held to the library's own output by `tests/data/grisu2-vectors.txt`**, values and
  the strings nlohmann wrote for them, the longer-than-shortest values and the ties among them, so
  the unit suite needs no compiler. A change to the port reruns the comparison against nlohmann.
  Verified against `tests/unit/test_grisu2.py`
  (`test_every_recorded_value_is_written_as_nlohmann_wrote_it`).
- **nlohmann's MIT notice stays in `grisu2.py`'s docstring**, the terms under which it is a port.
