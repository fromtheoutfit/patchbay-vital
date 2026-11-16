# References for the revision after PR 23's second review

## Similar Implementations

### The revision after PR 23's first review

- **Location:** `agent-os/specs/2026-11-16-1334-revision-after-pr-23-review/`
- **Relevance:** the round the second review read. Both correctness findings are against what it
  shipped and what it wrote down.
- **Key patterns:**
  - Decision 1 (the keep rule, narrowed) and Decision 2 (one load rule): the rules findings A
    and B are judged by.
  - `verification/mutation.txt`: the harness (`mutate.sh`, `mutate.py`, printed whole in the
    transcript), a scratch copy outside the tree, one mutant per rule, each failing a named
    test. MD1 there is the mutant the owner named for finding B.
  - `verification/load-and-set-sample.txt`: 110,000 displays, `preset_of` compared with
    `MappedParameter.to_preset` directly, no instrument. It stands as it is.
  - `verification/overlap-probe-2.txt`: what was measured with `mpe_enabled` off and on, and
    with `velocity_track` at 100 % and MPE off. The MPE and velocity wording is reworded to it.
  - `shape.md`, "Drafts for the owner": drafts shown whole, filed at the owner's word after the
    gate's clean run, each read back with `gh api`; a body revised in place under a dated
    heading with its text kept.

### The instrument spec (issue #8)

- **Location:** `agent-os/specs/2026-11-15-1448-the-instrument/`
- **Relevance:** the spec PR 23 ships, and where the upgraded floats were measured.
- **Key patterns:**
  - `verification/probes-2.txt`, section 9c: the 46 floats on 11 presets that
    `tests/data/upgraded-floats.txt` records.
  - Draft 4, the 0.1.0 proposal, held in its `shape.md` until the PR merges and revised in
    place under dated notes.

### Core at eddba95

- **Location:** `.venv/lib/python3.12/site-packages/patchbay/contracts.py`
- **Relevance:** `Instrument.get`'s clause, "the value given itself at a bound, and at any value
  `get` has returned for it that `set` takes", which the keep rule exists to meet; and the errors
  `set`, `render` and `load_patch` name, which the issue for core quotes.
