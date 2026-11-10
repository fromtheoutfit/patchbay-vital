# References for the host and the parameter map

## Similar Implementations

### The format layer

- **Location:** `src/patchbay_vital/format.py`, `src/patchbay_vital/preset.py`
- **Relevance:** `tuning` joins the file's model as an opaque section, and the host's state is the
  file's text.
- **Key patterns:** reading by span with `raw_decode` so unread sections stay the text the file held;
  a model's refusal reported as the package's error, chained; mappings sorted and read-only.

### The format spec

- **Location:** `agent-os/specs/2026-11-09-1509-the-vital-format/`
- **Relevance:** the same discovery-then-shape order, and a third party's behaviour held by recorded
  vectors.
- **Key patterns:** `verification/discovery.md` before the shape; `tests/data/grisu2-vectors.txt`
  holding the port with no compiler, as `tests/data/fma-vectors.txt` holds `fma32` with no plugin;
  the manifest-driven integration test that cannot pass on zero cases.

### patchbay-core at `dd2bcad`

- **Location:** `.venv/lib/python3.12/site-packages/patchbay/` (`models.py`, `errors.py`,
  `contracts.py`, `testing/contract_tests.py`)
- **Relevance:** the map's records hold core's `Parameter`; the protocol errors Spec B must raise are
  core's; the contract tests set every parameter at its bounds.
- **Key patterns:** `Parameter`'s rules (choices distinct and non-empty, a choice or boolean in unit
  none from 0), `PatchbayModel.from_json_data` for data in JSON's form.

### The negative-test harness

- **Location:** `scripts/gate-negative-tests.sh`
- **Relevance:** it copies `src/`, `tests/`, `pyproject.toml` and `uv.lock`, all of which this spec
  changes, so it reruns.
- **Key patterns:** one transcript per run, ending on its count.

### The spike

- **Location:** `~/Code/Audio/vital-spike/` (`spike.py`, `dump_params.py`, `vital_params.json`)
- **Relevance:** the 2026-11-03 spike that found 903 parameters and no routing through the host; the
  discovery probes ran in its venv.
- **Key patterns:** none carried over; its parameter dump keyed by pedalboard's names is what the
  census replaces with measured preset keys.
