# References for the Revision after PR 14's Fifth Review

## The review

- **Location:** https://github.com/fromtheoutfit/patchbay-vital/pull/14#issuecomment-6835661576,
  "Review of the fourth-review revision (`3569cca`, `d21f160`)" (2026-11-12 20:53Z).
- **Relevance:** the scope: six checks and ten findings.

## The issues

- **#15**, the map's two inverses, which this branch fixes, and **#13**, the property it first
  corrected. PR 14 closes both.
- **#8**, whose findings 1 (the neighbour for an arbitrary display) and 3 (whether
  `VitalInstrument.set` keeps a stored value) stay open.

## Similar Implementations

### The fourth-review sweep

- **Location:**
  `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/verification/sweep.txt`.
  Its `sweep.py` and `sweep_exponential.py` are embedded in the transcript.
- **Relevance:** the every-float32 count whose two zero columns this revision retires, and whose
  branch counts it attributes to the reproduction.
- **Key patterns:**
  - the binades as bit-pattern ranges (`SPANS`), counted in chunks on a process pool;
  - `sample()`, the 200,010 values each group is checked on;
  - `group_key`, the fields every method the paths call reads;
  - the tree printed before and after the run and compared with `cmp`.
- **What changes:** the direct count calls the shipped scalar methods themselves, `main`'s and
  this branch's, and reproduces nothing.

### The fourth-review duplicates check

- **Location:** the same folder, `verification/sweep-afterwards.txt`, section 1 (`duplicates.py`).
- **Relevance:** rerun here comparing each table whole.
- **What changes:** the closing line of each table is compared, its run time stripped.

### The fourth-review mutation and probe

- **Location:** the same folder, `verification/mutation.txt` (`mutate.sh`) and
  `verification/plugin-probe.txt` (`plugin_probe.py`).
- **Relevance:** `_resolve` changes, so M0 to M14 and the probe are rerun; new mutants are added
  beside them.
- **Key patterns:** a scratch copy of the tree, one mutant at a time, its diff, the tests that
  fail and the exit status; the probe's one sequence at the pinned values.

### The unit tests the new ones sit beside

- **Location:** `tests/unit/test_parameters.py`:
  `test_the_step_toward_a_preset_stays_where_the_host_can_set_it` (a constructed scale whose
  maximum is unheld), `test_a_scale_holds_its_values_and_none_past_its_ends`,
  `test_the_integration_module_pins_the_same_values`, and the helpers `_record` and
  `_what_a_set_holds`.
- **Relevance:** the shape of a test on a constructed scale, and the AST test this revision
  widens.
