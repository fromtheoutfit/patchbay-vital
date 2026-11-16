# Standards for the revision after PR 23's review

The following standards apply to this work, as they read when the spec was shaped (before the
retrospective). If this spec changed or proposed a change to any of them, `shape.md`'s Standards
Retrospective says which and why — this file is the snapshot, not the current text.

---

## base/python/toolchain

# Toolchain

Every patchbay Python package does each job with one tool and configures every tool in
`pyproject.toml`. This standard says which tool does which job, what each tool's configuration
says and in what order the gate runs them, and every rule names the file of a consuming project it
is verified against. It was written from patchbay (`fromtheoutfit/patchbay`) at `73a583a`, whose
toolchain spec and its revision after the review of patchbay PR 4 record each choice as a Decision
with its reason; the probes it cites are recorded by the spec of issue #4 in `patchbay-standards`.
"The gate's tool steps" and the `files` rule of "mypy" were read again at `3f910d8`, after
patchbay's revision after the review of its PR 9, by the gate spec of issues #17, #19 and #20,
which reran their probes. "Dependencies" and the suppression rules of "ruff" and "mypy" were read
again at `7471387`, after patchbay's contracts spec and its revision after the review of its PR 11,
by the spec of issue #21, which reran the probes they rest on (its `verification/probes.txt`).

Where a tool's pin lives, the locked mode the tools run under, uv's own pin in `[tool.uv]
required-version`, which sections of `pyproject.toml` are the gate's and which the package's, the
`uv sync --locked` that opens the first tool's step and how CI installs the toolchain are
`base/process/verification-gate.md`'s ("Pinned", "CI", "In a consuming project"). This standard
cites them and does not restate them.

## One tool per job

- **uv owns the environment, the dependencies, the lockfile and the build.** `uv.lock` is the one
  lockfile and is committed, `.gitignore` leaving its `uv.lock` line commented out, and no file of
  another installer exists: no `requirements*.txt`, no other lockfile, no `tox.ini`. Verified
  against `pyproject.toml` (`[build-system]`, `[tool.uv]`, `[dependency-groups]`), `uv.lock`,
  `.gitignore` and the tracked files.
- **ruff lints and formats**: `ruff check` is the linter and `ruff format` the formatter, and there
  is no black, isort, flake8 or pylint. **mypy checks the types. pytest runs the tests**, and
  hypothesis generates and shrinks the inputs of property tests, run by pytest with no step of its
  own. **pre-commit runs the hooks at commit**, and no gate step runs it. Verified against the
  `[dependency-groups] dev` section of `pyproject.toml`, whose comment beside each pin names its
  job, and the comment over `[tool.ruff]`.
- **Every tool runs as `uv run --locked <tool>`**, so each is the version `uv.lock` resolves, with
  the one rule set in `pyproject.toml`, and a lockfile that no longer matches a pin fails the
  command. Plain `uv run` re-locks instead: with a pin edited and `uv lock` not run, it rewrites
  `uv.lock` to the new pin and runs (probed). This holds of the gate's steps in `scripts/gate.sh`,
  the hook entries in `.pre-commit-config.yaml`, and the two commands a person runs for the hooks,
  `uv run --locked pre-commit install` and `uv run --locked pre-commit run --all-files`, which the
  project's `README.md` and the header of `.pre-commit-config.yaml` name. There is no exception.
  Verified against those three files and the probes.

## pyproject.toml is the only config file

- **Every tool is configured under `[tool.*]` in `pyproject.toml` and nowhere else**: no
  `setup.py`, `setup.cfg`, `requirements*.txt`, `tox.ini`, `.flake8`, `mypy.ini`, `pytest.ini` or
  `.ruff.toml`. Verified against the header of `pyproject.toml`, which says so, and the tracked
  files.
- **Two exceptions sit beside it, each for a reason.** `.pre-commit-config.yaml`, because
  pre-commit cannot read its hooks from `pyproject.toml`: it registers hooks and configures no
  tool, ruff's version being `uv.lock`'s and its rules `[tool.ruff]`'s, as its header says.
  `.python-version`, the interpreter uv chooses and fetches, which `uv sync` reads and `uv init`
  writes: it holds the floor (below) and nothing else. Verified against both files, the project's
  `README.md`, which says `uv sync` reads `.python-version`, and the probes.
- **`uv.lock` configures nothing**: it is the resolution of what `pyproject.toml` requires.
  Verified against `uv.lock`.

## The build

- **`[build-system]` is `requires = ["uv_build>=X.Y.Z,<X.(Y+1).0"]` with
  `build-backend = "uv_build"`, the range `uv init` writes, and the range contains the uv that
  `[tool.uv] required-version` pins.** uv then builds the package with the backend bundled in
  itself, in `uv build` and in the editable build `uv sync` makes. A bump of `required-version`
  inside the range changes nothing; a bump past its upper bound moves the range in the same spec,
  which is the gate's, since `[tool.uv]` is a gate file. Verified against `pyproject.toml`
  (patchbay: `uv_build>=0.13.7,<0.14.0` beside `required-version = "==0.13.7"`).
- **Outside the range, uv builds another way, and nothing fails online.** uv 0.13.7 uses its
  bundled backend when the range contains the running uv or a version its source declares
  compatible (`0.9.30`, `0.10.12`, `0.11.33`, `0.12.24`), the second with a warning, `does not
  contain the current uv version`. For any other range, and for a `==` that is not the running uv,
  it builds through PEP 517 with a uv_build package from the index: online that build succeeds,
  offline it fails. So the range is held by reading `pyproject.toml` in the spec that moves the
  pin, not by the gate. Verified against uv's source at `0.13.7` (`check_direct_build`) and the
  probes, offline and online, of `uv build` and `uv sync`.
- **The upper bound stays, and the pin is not a literal `==`.** uv_build follows uv's versioning
  policy, and uv's documentation gives the upper bound as what keeps the package building as new
  versions are released; a frontend other than uv, such as `python -m build`, always uses the
  uv_build package, a release the range admits. A `==` builds through PEP 517 from the index as
  soon as it is not the running uv, and the range is what `uv init` writes and what patchbay ships.
  Verified against `pyproject.toml` and the probes.
- **`[tool.uv.build-backend] module-name` names the import package when it is not the distribution
  name.** Without it uv_build looks for the module the distribution name gives and the build fails:
  patchbay's distribution is `patchbay-core`, its import `patchbay`, and without the key uv_build
  expects `src/patchbay_core/__init__.py`. Verified against `pyproject.toml`.
- **`license` is an SPDX expression, and `license-files` is stated**, `license-files = ["LICENSE"]`.
  uv_build applies no default license glob: a wheel built without the key carries
  `License-Expression` and no license text. Verified against `pyproject.toml` and patchbay's
  `verification/wheel-license.txt` in the spec of its PR 4 revision, the wheel before and after;
  patchbay's `tests/unit/test_package.py` holds the installed metadata to `License-File: LICENSE`
  at every gate run.

## Python 3.12 is the floor

- **The floor is stated in four places, with one value**: `requires-python = ">=3.12"` in
  `[project]`, `.python-version` (`3.12`), `target-version = "py312"` in `[tool.ruff]` and
  `python_version = "3.12"` in `[tool.mypy]`. The two tool keys are stated, so a rule set never
  silently follows a raised floor. Verified against `pyproject.toml` and `.python-version`.
- **The floor is the family's**: every patchbay package states 3.12. Raising it is a change to this
  standard first, landed in `patchbay-standards` by its own spec; from a project it starts as a
  proposal its retrospective sends upstream (`base/process/standards-retrospective.md`). Each
  project then raises it in the gate spec that follows the sync bringing that change in, changing
  all four places together, since two of them are `[tool.*]` sections. Verified against
  `pyproject.toml` and `.python-version`, which state the value this standard gives.
- **The code is written for the floor and nothing below it.** Under `select = ["ALL"]` and that
  `target-version`, ruff refuses a version branch for an interpreter below the floor (UP036) and an
  import from `typing_extensions` of a name `typing` has at the floor (UP035). A backport of a
  standard-library module, `tomli` for `tomllib`, is a dependency, and fails the Decision
  "Dependencies" below asks for, since the standard library can. Verified against `pyproject.toml`
  and the probes.

## Dependencies

- **Adding a dependency is a Decision in the spec that adds it**, in that spec's `shape.md`: what
  it does, why the standard library cannot, and its license. This holds for `[project]
  dependencies` and for every dependency group. Verified against the header of `pyproject.toml`,
  and patchbay's toolchain spec, whose Decisions give all three for each of its five dev tools.
- **A dependency is added by the spec that uses it**, never ahead of it. Verified against
  `pyproject.toml`: patchbay's three runtime dependencies came with the code that imports them,
  numpy and pydantic with its contracts spec and pydantic-core with that spec's revision, each a
  Decision in its spec's `shape.md`; typer, which its product stack names for the CLI, is not
  declared, since nothing in it has a CLI yet.
- **A runtime dependency is a range: the version the gate ran as its floor, the next major as its
  ceiling** (`pydantic>=2.14.3,<3`), since an adapter installs the package beside its own
  dependencies, and an exact pin would refuse every other version. The dev group's entries stay
  exact (below). Verified against `[project] dependencies` in `pyproject.toml` and the comment
  over it.
- **A package the code imports directly is declared, even when another dependency brings it in**:
  patchbay's `errors.py` imports pydantic-core's `ErrorDetails`, which pydantic does not re-export,
  so `pydantic-core>=2.50.4,<3` is declared beside the pydantic that requires it. Verified against
  `pyproject.toml` and `src/patchbay/errors.py`; probe f of issue #21's spec.
- **The spec that adds a runtime dependency shows the lock's change in its `verification/`**: the
  lock gained the dependency and the dependencies it brings, and changed no resolution of a tool
  the gate runs, a package a tool shares with it (`typing-extensions`) included. Declaring a
  package the lock already holds changes only the package's own entry, its `dependencies` and its
  `requires-dist`. Verified against the `verification/uv-lock-diff.txt` of patchbay's contracts spec
  (additions only: annotated-types, numpy, pydantic, pydantic-core and typing-inspection) and of
  its revision (patchbay-core's own entry gaining pydantic-core, twice).
- **Every entry of the dev group is pinned exactly, with the date it was published beside it.** The
  pins of the tools the gate runs are `verification-gate.md`'s; the group's other entries take the
  same form (patchbay's hypothesis, run by pytest, and pre-commit, run by no gate step). Verified
  against `[dependency-groups] dev` in `pyproject.toml`.

## ruff

- **`[tool.ruff]` states `target-version`, the floor, and `line-length = 100`**: wide enough that
  a typed signature or a pydantic field with its description stays on one line, narrow enough to
  read in a split editor and a GitHub diff. The width is the family's, as the floor is: changed
  here first, then in each project's gate spec after the sync that brings it in. Verified against
  `pyproject.toml`.
- **`[tool.ruff.lint]` selects every rule, `select = ["ALL"]`, and the ignore list is what the
  tree and ruff taught.** Run `ALL` over the tree with the list empty. A rule the tree trips is
  fixed in the code where the rule is right, and ignored only where it is wrong for the tree. A
  conflict ruff warns of, between two rules or between a rule and the formatter, is ignored too,
  so the choice is the project's and written down rather than ruff's and silent. One comment per
  entry says why. Nothing is listed from memory: a rule the tree has not tripped and ruff has not
  warned of is not ignored (patchbay's first run gave neither ISC001 nor PLR2004, and it lists
  neither). When patchbay's contracts revision took the `test_` prefix off its contract tests, D401,
  which waives a function named `test_*`, reported their docstrings, and they were rewritten in
  the imperative, "Check that ...", not ignored. Verified against `[tool.ruff.lint]` in
  `pyproject.toml`, its comment, `src/patchbay/testing/contract_tests.py` and the probes, probe b
  of issue #21's spec among them.
- **patchbay's list has six entries, each for a reason that holds of any patchbay package**, and a
  package lists each when its own run gives it:
  - Conflicts ruff warns of. `D203` and `D213`: `ruff check` and `ruff format` warn that D203 and
    D211, and D212 and D213, are incompatible, and drop D203 and D213 themselves; the ignore makes
    the choice explicit, no blank line before a class docstring and a multi-line docstring's
    summary on its first line. `COM812`: `ruff format` warns that it conflicts with the formatter,
    which owns trailing commas.
  - Findings the tree trips. `CPY001`, on every file: the license is the repository's `LICENSE`,
    and a copyright header in every file is noise every diff pays for. Under `"tests/**"` in
    `[tool.ruff.lint.per-file-ignores]`, `S101`, since `assert` is how a pytest test states its
    expectation, and `INP001`, since `tests/` is a tree pytest collects from `testpaths`, not a
    package, and has no `__init__.py`.

  Verified against `pyproject.toml` and the probes.
- **A suppression on one line names its code, `# noqa: <code>`, never a blanket `# noqa`.** Under
  `ALL`, PGH004 refuses a blanket `# noqa` even where it suppresses a finding, and RUF100 refuses a
  `# noqa` whose code suppresses nothing. A suppression loosens the rule for that line and is
  reviewed as the loosening it is (`verification-gate.md`, "A failing step is fixed at its cause").
  Verified against `select` in `pyproject.toml` and the probes.
- **A suppression sits only where the code cannot change, with its reason beside it**, on its line
  or in the comment directly above, since no tool checks the reason and the reviewer reads it
  there. patchbay's `src/` holds four, each coded: `# noqa: BLE001` on the event bus's catch of
  every subscriber's `Exception`, the behaviour `base/python/events.md` requires;
  `# type: ignore[attr-defined]` on the base-init marker; and `# type: ignore[assignment]` on each
  of the two `__hash__: ClassVar[None] = None` (`base/python/models.md`). A third party's method is
  wrapped, never overridden with its signature copied (`base/python/models.md`), so PLR0913 has no
  case: the three `# noqa: PLR0913` patchbay's contracts spec put on copied signatures went with
  the copies in its revision. Verified against `src/patchbay/events.py` and
  `src/patchbay/models.py`, and the suppressions counted in issue #21's
  `verification/patchbay-evidence.txt`; probe b of that spec.
- **The ignore list grows only in the gate's own spec**, `[tool.ruff]` being a gate file
  (`verification-gate.md`, "The gate's own files change only in their own spec").

## mypy

- **`[tool.mypy]` is `strict = true` over `files = ["src", "tests"]`**, so the tests are typed to
  the package's bar, with `python_version` the floor, `warn_unreachable = true`, since code the
  checker proves unreachable is a bug and strict does not turn it on, and `implicit_reexport =
  false` stated though strict implies it, so a name is exported only by `__all__` or an explicit
  `from x import y as y`. Verified against `pyproject.toml`.
- **`files` is what a bare `uv run --locked mypy` walks**; the gate gives mypy git's list instead
  ("The gate's tool steps"). There is no `exclude_gitignore`: under it mypy's walk skipped a
  tracked file `.gitignore` matches, and in a linked worktree, where `.git` is a file, checked a
  module that only `.git/info/exclude` hides. Verified against `[tool.mypy]` in `pyproject.toml`
  (patchbay at `3f910d8`), its test p and the probes.
- **An untyped third-party package gets its own override**: a `[[tool.mypy.overrides]]` block with
  `module = ["name.*"]`, `ignore_missing_imports = true` and a comment naming the package and why;
  never a global `ignore_missing_imports`. patchbay's runtime dependencies, numpy, pydantic and
  pydantic-core, are typed, it has no override, and the rule is the comment in its `[tool.mypy]`.
  Verified against `pyproject.toml` and the clean mypy run in issue #21's
  `verification/patchbay-evidence.txt`.
- **A `# type: ignore` names its code, `# type: ignore[<code>]`, as a `noqa` does**: under
  `select = ["ALL"]` ruff's PGH003 refuses a blanket one, and strict's `warn_unused_ignores`
  refuses a coded one that suppresses nothing. In `src/` one sits only where the code cannot change
  ("ruff", above); in a test one may hold a refusal mypy must keep making
  (`base/testing/tests.md`). Verified against `src/patchbay/models.py`, the six in `tests/unit/`
  and `pyproject.toml`; probes b and c of issue #21's spec.

## pytest and hypothesis

- **`[tool.pytest.ini_options]` is `testpaths = ["tests"]` and
  `addopts = "-q --strict-markers --strict-config"`**: `-q` because a person reads the gate's
  transcript, `--strict-markers` so an unregistered marker, a typo, fails rather than silently
  selecting nothing, and `--strict-config` so a key pytest does not know fails the run rather than
  being ignored with a warning. Verified against `pyproject.toml` and the probes.
- **Every marker is registered under `markers` with its meaning**: patchbay's `integration`,
  "needs a running instrument; not selected by the gate until a spec says so". Verified against
  `pyproject.toml`.
- **Nothing else is set until a spec needs it**: patchbay has no `filterwarnings` and no
  `xfail_strict`. Verified against `pyproject.toml`.
- **hypothesis has no section**: it reads no settings from `pyproject.toml`, its profiles are code,
  and its `.hypothesis/` directory is ignored. Verified against `pyproject.toml` and `.gitignore`.

## pre-commit

- **`.pre-commit-config.yaml` holds two `repo: local` hooks, in this order: `ruff check --fix`,
  then `ruff format`**, ruff's recommended order, since a fix can change the formatting. Each
  `entry` is `uv run --locked ruff …` with `language: system` and `types_or: [python, pyi]`, so the
  hook runs the gate's ruff, at the version `uv.lock` resolves, with the gate's rules: one pin and
  one rule set. The `ruff-pre-commit` mirror is not used, since it would state ruff's version a
  second time. Verified against `.pre-commit-config.yaml`.
- **Each hook sets `require_serial: true`**, since two `uv run` calls syncing the same `.venv`
  would race, and **`minimum_pre_commit_version` is the dev group's pre-commit pin**. Verified
  against `.pre-commit-config.yaml` and `pyproject.toml`.
- **The hooks run ruff and nothing else, never mypy or pytest**: a hook is for what a commit can
  fix in a second, and the gate is the check. The person committing installs the git hook once,
  with `uv run --locked pre-commit install`. Verified against `.pre-commit-config.yaml` and the
  project's `README.md`.

## The gate's tool steps

- **After the gate's first step and before `scripts/sync-standards.sh --check`, the gate runs one
  step per tool, in this order: format, lint, types, tests.** Format before lint, so a formatting
  failure is reported before a lint finding the formatter would have changed; lint before types,
  since it is faster and its findings cheaper; tests last among the tools, since a type error
  usually explains a failing test. hypothesis runs inside `pytest`, and pre-commit in no step. Each
  tool runs as `uv run --locked <tool>`, and the first tool's step opens with `uv sync --locked`,
  both `verification-gate.md`'s. Verified against `scripts/gate.sh` (patchbay: steps 2 to 5 of
  six).
- **ruff and mypy are given git's list; pytest walks, after a refusal.** The command lines are
  `uv run --locked ruff format --check -- <the .py and .pyi files git lists>`, then
  `uv run --locked ruff check -- <the same>`, then
  `uv run --locked mypy -- <those under src/ and tests/>`, each path checked on the disk: the
  listing rule's first form (`verification-gate.md`, "One script"), so a tracked file `.gitignore`
  matches is read and git alone decides what `.gitignore`, `.git/info/exclude` and the global
  excludes file hide. Walking, ruff (`respect-gitignore`) and mypy (`exclude_gitignore`) skip a
  force-added file `.gitignore` still matches. Then `uv run --locked pytest`, which walks
  `testpaths`: pytest has no form that reads a list without also loading the `conftest.py` of each
  directory it collects from, so its step first refuses, by name, any `.py` file git ignores under
  `tests/` and an ignored `conftest.py` at the root (the refusal form). Verified against
  `scripts/gate.sh` steps 2 to 5 and tests p and q (patchbay at `3f910d8`), and the probes.

## In this repository

`patchbay-standards` has no package: no `pyproject.toml`, no `uv.lock`, no Python under `src/` or
`tests/`. This standard does not apply here, and no file here verifies it. Its rules were read from
patchbay at `73a583a`, the tool steps and mypy's `files` again at `3f910d8`; a spec that changes one
reads it again from a consuming project's shipped files, and reruns the probes a rule rests on.
"Dependencies" and the suppression rules were read again at `7471387`. The one Python tool this
repository's gate runs, pymarkdown through `uvx`, takes the no-manifest form of
`verification-gate.md`. Step 5a of this repository's `shape-spec.md` lists this standard with the
note that it applies to consuming projects; a spec shaped here records it under "Core Architecture"
as not applying and does not copy it into `standards.md`.

## In a consuming project

This standard is synced in as `agent-os/standards/base/python/toolchain.md`. Every rule above is
the project's, verified against the project's own files it names. The project's `shape-spec.md`
lists it in Step 5a, the tier every spec includes without asking, with its full content in that
spec's `standards.md`.

---

## base/python/layout

# Layout

Where everything in a patchbay package lives: its modules, the subpackage its consumers' tests use,
what its `__init__.py` holds, and the one direction its modules import in. Every rule names the file
of a consuming project it is verified against, the test that holds it and the probe a rule about a
tool's behaviour rests on. Written from fromtheoutfit/patchbay at `7471387`, the merge of its PR 11,
whose contracts spec and that spec's revision record each choice as a Decision; the evidence is in
the `verification/` of the spec of issue #21 in `patchbay-standards` and of its revision after the
review of PR 25, patchbay's own probes cited by name and the ones those specs added by letter. The
toolchain spec of issue #4 deferred its `__init__.py` rules here.

Where a test file lives is `base/testing/tests.md`'s; how a name is re-exported so mypy sees it is
`base/python/typing.md`'s.

## The package

- **`src/<package>/` holds one module per concern.** patchbay's core holds four: `contracts.py`,
  the protocol an adapter implements; `models.py`, the values that cross a boundary; `events.py`,
  the events, their bus and its subscriptions; `errors.py`, the exceptions. Verified against
  `src/patchbay/` and the docstring of `src/patchbay/__init__.py`.
- **What a consumer's tests use is a `testing/` subpackage, shipped in the wheel**, a module per
  thing it holds: patchbay's `patchbay.testing` holds the contract tests (`contract_tests.py`),
  the reference implementation they are proven against (`fake.py`) and a subscriber that records
  what it receives (`recording.py`). The root does not re-export it and no module outside it
  imports it, so importing the package loads none of it; a consumer imports it by name. It imports
  no pytest (`base/testing/tests.md`). Verified against `src/patchbay/testing/`, its
  `__init__.py`'s docstring, `src/patchbay/__init__.py`, and the wheel's files and the modules an
  import of the package loads, in the `verification/patchbay-evidence.txt` of the spec of issue #21.
- **No two modules of the package share a basename**, its subpackages' included, so the test
  module each takes its name from (`base/testing/tests.md`, the mirror) is one no other test module
  has, and mypy, which reads `tests/` with no `__init__.py`, never meets two modules of one name.
  The named exception is `__init__.py`, one per package, whose tests take their names from what
  they hold (`base/testing/tests.md`). patchbay's seven, `contracts`, `errors`, `events`, `models`,
  `contract_tests`, `fake` and `recording`, are seven names. Verified against `src/patchbay/` and
  `tests/unit/`; probe n.

## `__init__.py`

- **A package's `__init__.py` holds its re-exports and `__all__`, the root's `__version__` too, and
  nothing else**: no definition and no logic. A module the root imports for itself is bound to a
  private name (`import importlib.metadata as _metadata`), so every public name the root binds is
  an export. `testing/__init__.py` holds re-exports and `__all__` alone. Verified against
  `src/patchbay/__init__.py`, `src/patchbay/testing/__init__.py` and `tests/unit/test_package.py`
  (`test_public_names_are_in_all`).
- **`__version__` is read from the installed distribution's metadata**,
  `importlib.metadata.version("<distribution>")`, so `pyproject.toml` is the one place the version
  is written. Nothing falls back around it: where no distribution is installed, as from a bare
  `src/` on `sys.path`, `importlib.metadata` raises `PackageNotFoundError` and the import fails,
  rather than the package inventing a version. Verified against `src/patchbay/__init__.py`, its
  docstring, and `tests/unit/test_version.py` (`test_version_matches_pyproject`).
- **A test holds the root's surface to `__all__`**: every name the root binds without a leading
  underscore is in `__all__`; every name in `__all__` is bound, and listed once; and each is the
  very object its module defines, not a copy or a second type. Submodules are left out of the
  first: importing `patchbay.errors` binds `errors` on the package, the import system's doing and
  not an export, and `from patchbay import *` does not import them. Verified against
  `tests/unit/test_package.py` (`test_public_names_are_in_all`, `test_every_name_in_all_resolves`,
  `test_the_package_re_exports_the_contract_surface`).

## One direction of import

- **The modules import in one direction, from the errors module up to the root, and are built in
  that order with the gate green after each.** The errors module is the leaf and imports nothing
  from its package (`base/python/errors.md`). In patchbay, `models.py` imports `errors.py`;
  `events.py` imports both; `contracts.py` imports `events.py` and `models.py`; the `testing`
  modules import those; `__init__.py` imports the four. They were built in that order, errors,
  models, events, contracts, the `testing` subpackage with the fake, the contract tests, then
  `__init__.py`, with the gate green after each, at 28, 103, 127, 131, 162, 186 and 188 tests: a
  module cannot pass mypy before what it imports exists. Verified against the imports of each
  module in `src/patchbay/` and the contracts spec's `shape.md` ("Results").
- **A protocol that a module's own API takes lives in that module, beside the API**, so no two
  modules import each other: `Subscriber` is defined in `events.py`, beside the
  `EventBus.subscribe` that takes it, and `contracts.py` re-exports it (`base/python/typing.md`,
  "Re-exports"). `Subscriber` is bounded by `Event`: placed in `contracts.py`, it would have
  `contracts.py` import `Event` from `events.py`, and `events.py` import `Subscriber` from
  `contracts.py` for `subscribe`. Verified against
  `src/patchbay/events.py`, `src/patchbay/contracts.py` and `tests/unit/test_contracts.py`
  (`test_subscriber_is_the_events_module_s_own`).

## In this repository

This repository has no package, so this standard does not apply here; its `shape-spec.md` lists it
in Step 5a for consuming projects.

## In a consuming project

Synced in as `agent-os/standards/base/python/layout.md`, its rules the project's, verified against
the project's own files; Step 5a includes it in every spec, with its full content in that spec's
`standards.md`.

---

## base/python/typing

# Typing

A patchbay package is typed so that mypy, strict over the package and its tests, refuses what the
contracts forbid before a test runs. This standard says how keys, protocols, generics and re-exports
are written for mypy to hold them, and which annotation form pydantic needs. Every rule names the
file of a consuming project it is verified against, the test that holds it and the probe a rule
about a tool's behaviour rests on. Written from fromtheoutfit/patchbay at `7471387`, the merge of
its PR 11, whose contracts spec and that spec's revision record each choice as a Decision; the
evidence is in the `verification/` of the spec of issue #21 in `patchbay-standards` and of its
revision after the review of PR 25, patchbay's own probes cited by name and the ones those specs
added by letter.

mypy's configuration, strict with `implicit_reexport = false`, is `base/python/toolchain.md`'s. How
mypy reads a model's frozenness is `base/python/models.md`'s, and the variance of the subscriber
protocol `base/python/events.md`'s.

## Keys

- **Distinct keys are distinct `NewType`s**, so mypy refuses one where the other is expected, and a
  plain `str` where either is: patchbay's `ParameterId`, the key a host knows a parameter by, and
  `PresetKey`, the key a preset file knows a value by. Each is a `str` at runtime, so a key costs
  nothing to build or to serialize. Verified against `src/patchbay/models.py` and
  `tests/unit/test_models.py` (`test_a_preset_key_is_not_a_parameter_id`, whose coded ignore holds
  mypy's refusal); probe `typing_probe.py` E and F.

## Protocols

- **A protocol's data member is a read-only property**, so an implementation may give it as a
  plain attribute or as a property: `Instrument.name`. Verified against `src/patchbay/contracts.py`
  and `tests/unit/test_contracts.py` (`test_an_object_with_every_member_is_an_instrument`, whose
  `_Silent` gives `name` as a class attribute); probe `runtime.py` 7.
- **A protocol method's parameters are positional-only**, so an implementation names its own:
  every method of `Instrument`, and `Subscriber.__call__`. Verified against
  `src/patchbay/contracts.py`, `src/patchbay/events.py` and `tests/unit/test_contracts.py`; probe
  `typing_probe.py` H.
- **A protocol is checked at runtime with `isinstance`, which asks only whether every member's name
  is there**, under `@runtime_checkable`; a member's signature is mypy's to hold, and its
  behaviour the contract suite's (`base/testing/tests.md`). `issubclass` is refused for a protocol
  with a data member, by mypy statically and by Python at runtime, and is not used. Verified
  against `src/patchbay/contracts.py` and `tests/unit/test_contracts.py`
  (`test_an_object_with_every_member_is_an_instrument`,
  `test_an_object_missing_a_member_is_not_an_instrument`,
  `test_issubclass_is_refused_for_a_protocol_with_a_data_member`); probe `runtime.py` 7.

## Generics

- **Generics use PEP 695's syntax**: a type parameter list on the class or function,
  `class Subscriber[E: Event]`, `def _refusing[**P, R]`, `def of_type[E: Event]`, and the `type`
  statement for an alias, `type ContractTest = Callable[[Instrument, EventBus], None]`. There is
  no `TypeVar`, `ParamSpec`, `Generic` or `TypeAlias` in `src/` or `tests/`. Under
  `select = ["ALL"]` at the 3.12 floor, ruff asks for it: UP046 for a `Generic` class, UP047 for a
  function over a `TypeVar`, UP040 for a `TypeAlias`. Verified against `src/patchbay/events.py`,
  `src/patchbay/models.py`, `src/patchbay/testing/contract_tests.py` and
  `src/patchbay/testing/recording.py`; probe m.

## Re-exports

- **A module re-exports a name by listing it in its `__all__`**, never by importing it alone: under
  `implicit_reexport = false` mypy refuses `from module import name` for a name the module imports
  but does not list, and `--implicit-reexport` lifts the refusal. `patchbay.contracts` imports
  `Subscriber` from `patchbay.events` and lists it in its `__all__`, and every name the package's
  root exports is in the root's `__all__` (`base/python/layout.md`). Verified against
  `src/patchbay/contracts.py`, `src/patchbay/__init__.py`, `pyproject.toml` (`[tool.mypy]`) and
  `tests/unit/test_contracts.py` (`test_subscriber_is_the_events_module_s_own`); probe k.

## Annotations pydantic reads

- **A module whose annotations pydantic reads carries no `from __future__ import annotations`**:
  every module that defines a model. With it, ruff under `select = ["ALL"]` reports an import used
  only in a field's annotation (TC003 for the standard library) and asks for it under
  `if TYPE_CHECKING:`, where pydantic cannot reach it, and the model moved so is not fully defined
  at its first use. Without it, ruff reads the annotation as evaluated at runtime and asks nothing.
  Verified against `src/patchbay/` and `tests/` (no module carries the import); probe l.

## In this repository

This repository has no package, so this standard does not apply here; its `shape-spec.md` lists it
in Step 5a for consuming projects.

## In a consuming project

Synced in as `agent-os/standards/base/python/typing.md`, its rules the project's, verified against
the project's own files; Step 5a includes it in every spec, with its full content in that spec's
`standards.md`.

---

## base/python/models

# Models

Every value that crosses a patchbay package's boundary is a pydantic model on one base. This
standard says what that base guarantees and how each guarantee is kept: frozen, closed, finite and
strict, refusing as the package, read-only inside, and computing alike. Every rule names the file of
a consuming project it is verified against, the test that holds it and the probe a rule about a
tool's behaviour rests on. Written from fromtheoutfit/patchbay at `7471387`, the merge of its PR 11,
whose contracts spec and that spec's revision record each choice as a Decision; the evidence is in
the `verification/` of the spec of issue #21 in `patchbay-standards` and of its revision after the
review of PR 25, patchbay's own probes cited by name and the ones those specs added by letter.

How mypy reads a model's frozenness is here; the type system's other rules, the future import a
model's module never carries among them, are `base/python/typing.md`'s. What the package's errors
are, and what escapes them, is `base/python/errors.md`'s; an event is a model with rules of its own
in `base/python/events.md`.

## One base

- **Every model derives from one public base, the package's own**: patchbay's `PatchbayModel`, in
  `models.py` and in the root's `__all__`, from which every model and every event derives. A model
  that derives from it has every guarantee below, whichever module defines it. Verified against
  `src/patchbay/models.py`, `src/patchbay/events.py`, `src/patchbay/__init__.py` and
  `tests/unit/test_models.py` (`test_a_model_on_patchbay_model_refuses_as_patchbay_at_any_depth`).
- **The base is frozen by the class keyword `frozen=True`, and every subclass writes the keyword
  again on its class line.** mypy, with no pydantic plugin loaded (`[tool.mypy]` names none), reads
  frozen from the keyword and not from `model_config`: given the keyword it refuses an assignment
  to a field and a subclass that leaves the keyword out ("Non-frozen dataclass cannot inherit from
  a frozen dataclass"); given `model_config` alone it accepts an assignment pydantic refuses at
  runtime. The class keyword and `model_config` merge at runtime. There is no exception: every
  event's class line carries it too. Verified against `src/patchbay/models.py` and
  `src/patchbay/events.py` (every class line), `pyproject.toml` (`[tool.mypy]`),
  `tests/unit/test_models.py` (`test_a_frozen_model_is_unchanged_by_a_refused_assignment`) and
  `tests/unit/test_events.py` (`test_an_event_is_frozen`), each holding mypy's refusal with a coded
  ignore; probes `typing_probe.py` C and D, `frozen_kw.py`, `frozen_kw2.py` and `config_form.py`.
- **The base's `model_config` is closed, finite and strict**: `extra="forbid"`,
  `allow_inf_nan=False` and `strict=True`. A field the model does not declare, NaN and an infinity
  are refused, and no value is converted from another type: `"0.5"` is not 0.5, `1` is not `True`,
  a list is not a tuple and a `str` is not an enum. Strict admits three things, by pydantic's
  design: an int for a float; a dict for a nested model, every field inside it validated by the
  nested model's own config, so as strictly where the nested model is on the base too, and laxly
  where it is not, strict outside or not; and `model_validate_strings`, whose purpose is parsing
  strings. Every model a model holds is on the base, so strict holds at every depth. A model's own
  `model_config` adds to the base's and relaxes none of it: patchbay's `Patch` adds base64 for
  bytes, `RenderResult` arbitrary types for its array. Verified against `src/patchbay/models.py`
  and `tests/unit/test_models.py` (`test_every_entry_point_refuses_with_patchbay_validation_error`,
  `test_strict_refuses_a_conversion`, `test_strict_admits_an_int_for_a_float_and_json_forms`);
  probes `runtime.py` 5, `strict_nested.py` (1, strict inside; 2, a lax model inside a strict one
  admitting `'0.5'`) and `config_form.py`.

## Refusing as the package

- **A model's own entry points refuse with the package's validation error, chained from
  pydantic's.** The constructor, `model_validate`, `model_validate_json` (bad JSON included),
  `model_validate_strings`, the JSON-data entry point below, assignment and deletion each raise
  `PatchbayValidationError` from pydantic's `ValidationError`, which is a `ValueError` and so never
  escapes as one (`base/python/errors.md`). Verified against `src/patchbay/models.py`
  (`_refusals`) and `tests/unit/test_models.py`
  (`test_every_entry_point_refuses_with_patchbay_validation_error`); probe `runtime.py` 6.
- **Validation pydantic runs on behalf of something else is that thing's, and raises pydantic's
  error**: a `TypeAdapter` over a model, or a plain `BaseModel` that holds one as a field. A model
  that derives from the base is not something else: it refuses as the package at any depth.
  `model_copy(update=...)` validates nothing and is not a way in. No hook covers every path:
  pydantic-core collects a `ValueError` raised inside a validator, with its path, beside the outer
  model's own refusals, and lets any other exception through unwrapped, which ends the outer
  validation at the first nested refusal and loses the outer path and the outer refusals. So the
  package's error is raised around the entry points, never from inside a validator. Verified
  against `src/patchbay/models.py` (its docstring) and `tests/unit/test_models.py`
  (`test_validation_run_for_something_else_raises_pydantic_s_error`,
  `test_a_model_on_patchbay_model_refuses_as_patchbay_at_any_depth`); probe a (a1, a2, a5).
- **A validator raises `ValueError`**, which pydantic collects with the field's path; a validator
  that calls code raising the package's error catches it and raises `ValueError` from it
  (patchbay's `Parameter._default_is_a_value`). Verified against `src/patchbay/models.py`,
  `src/patchbay/events.py` and `tests/unit/test_models.py`
  (`test_a_parameter_that_does_not_hold_together_is_refused`); probe a (a1).
- **pydantic's validating classmethods are wrapped, never restated.** In the base, under
  `if not TYPE_CHECKING:`, each of `model_validate`, `model_validate_json` and
  `model_validate_strings` is `classmethod(_refusing(BaseModel.<name>.__func__))`, where
  `_refusing[**P, R]` is a `functools.wraps` decorator that raises a refusal as the package's
  error. mypy, which skips the block, checks every call against pydantic's own `Self`-typed
  signatures, so a misspelled keyword is a type error; at runtime the wrapper forwards whatever it
  is given, so a keyword a later pydantic adds reaches pydantic, and `inspect.signature` of each
  equals pydantic's. Nothing is copied, so ruff's PLR0913 has no case (`base/python/toolchain.md`,
  "ruff"). Verified against `src/patchbay/models.py` and `tests/unit/test_models.py`
  (`test_the_validating_classmethods_keep_pydantic_s_signatures`,
  `test_a_keyword_reaches_pydantic_through_the_wrapper`); probes `footing.py` A and
  `footing_typing.py`.
- **The base's own `__init__` carries pydantic's base-init marker**,
  `__pydantic_base_init__ = True`, with its coded `# type: ignore[attr-defined]` and the reason in
  the comment above it. The override validates exactly what `BaseModel.__init__` does. Without the
  marker, pydantic builds a nested model by calling that `__init__` with the parsed input in Python
  mode: strict then refuses a valid JSON enum string one level down, and a nested refusal escapes
  the outer validation without the outer path or the outer refusals. Verified against
  `src/patchbay/models.py` and `tests/unit/test_models.py`
  (`test_a_patch_round_trips_through_json_byte_for_byte`); probes `models_init.py` and a (a3, a4).

## Python input and JSON data

- **Python input is Python's types, strictly; data in JSON's form goes through one entry point on
  the base**, patchbay's `from_json_data(data)`, for what `json.loads`, a YAML or a TOML parser
  gives. It validates `json.dumps(data)` with `model_validate_json`, so the data meets pydantic's
  JSON rules exactly: an enum by its value, bytes as base64 where the model reads them so, a time
  as an ISO string, an array for a tuple. Strict still refuses `"0.5"` for a float, `1` for `True`
  and NaN. A value JSON cannot hold, a set, a `datetime` or a circular reference, is refused as the
  package's error with one detail at the root, chained from `json`'s `TypeError` or `ValueError`.
  The name keeps out of pydantic's `model_` namespace, where a later pydantic method could land.
  Verified against `src/patchbay/models.py`, `tests/unit/test_models.py`
  (`test_from_json_data_takes_json_s_own_forms`, `test_from_json_data_is_still_strict`,
  `test_from_json_data_refuses_data_json_cannot_hold`, `test_a_patch_comes_back_from_its_json_data`)
  and `tests/unit/test_events.py` (`test_an_event_comes_back_from_its_json_data`); probe
  `footing.py` E.

## Frozen inside

- **A mapping field is sorted by key and held as a `MappingProxyType`**, by an after-validator,
  with a wrap serializer that hands pydantic a plain dict: pydantic validates a `Mapping` to a
  `dict` that a frozen model still lets anyone change, and cannot serialize a proxy without the
  serializer. The same model then writes the same JSON whatever order it was built in. Verified
  against `src/patchbay/models.py` (`Patch`) and `tests/unit/test_models.py`
  (`test_a_patch_s_mappings_are_read_only`, `test_a_patch_has_one_json_whatever_order_it_was_built_in`);
  probe `runtime.py` 1 and 2.
- **An array field is copied, marked unwriteable, and checked for its dtype, its shape and finite
  values**, an arbitrary-type field being only an `isinstance` check; and the model defines `__eq__`
  with `np.array_equal`, since `==` on two arrays has no truth value. Verified against
  `src/patchbay/models.py` (`RenderResult`) and `tests/unit/test_models.py`
  (`test_a_render_result_holds_a_read_only_copy`, `test_a_render_result_refuses_audio_of_another_shape`,
  `test_a_render_result_refuses_audio_that_is_not_finite`, `test_render_results_compare_by_their_arrays`);
  probe `runtime.py` 4.
- **A model that cannot be hashed says so the way Python does**, `__hash__: ClassVar[None] = None`,
  with its coded `# type: ignore[assignment]` and the reason in the comment above it: pydantic's
  frozen hash would raise on a mapping or an array from inside. Verified against
  `src/patchbay/models.py` (`Patch`, `RenderResult`) and `tests/unit/test_models.py`
  (`test_a_patch_is_not_hashable`, `test_a_render_result_is_not_hashable`); probe `runtime.py` 1
  and 4.
- **Bytes go into JSON as base64** (`ser_json_bytes` and `val_json_bytes`), since pydantic's default,
  UTF-8, fails on bytes that are not text. Verified against `src/patchbay/models.py` (`Patch`) and
  `tests/unit/test_models.py` (`test_a_patch_round_trips_through_json_byte_for_byte`); probe
  `runtime.py` 3.
- **An id is non-empty wherever it appears**, a mapping's key included, written
  `Annotated[ParameterId, Field(min_length=1)]` where a field's `Field` cannot reach it. Verified
  against `src/patchbay/models.py`, `src/patchbay/events.py`, `tests/unit/test_models.py`
  (`test_a_patch_s_parameter_ids_are_not_empty`) and `tests/unit/test_events.py`
  (`test_a_changed_parameter_is_named`); probe `footing.py` D.

## Computing alike

- **A quantity every implementation must compute alike is one method on the model, in exact
  arithmetic**, so it is an int for every valid input, never an overflow or an infinity: patchbay's
  `RenderRequest.samples(pattern)`, the length of every render, and `sample_at(pattern, beat)`,
  where a note falls, each in `fractions.Fraction` and rounded half to even. An implementation
  calls the method and never restates the formula. A float derived from one divides an int by an
  int (`RenderResult.audio_seconds`), which Python rounds correctly and which overflows only where
  the quotient passes the largest float, as an array's length over a positive rate never does.
  Verified against
  `src/patchbay/models.py`, `src/patchbay/testing/fake.py` and
  `src/patchbay/testing/contract_tests.py`, which call them, and `tests/unit/test_models.py`
  (`test_samples_is_an_int_however_long_the_render`, `test_samples_rounds_half_to_even`,
  `test_sample_at_places_a_beat_by_the_rule_that_fixes_the_length`,
  `test_sample_at_is_an_int_at_any_tempo`, `test_audio_seconds_holds_at_any_rate`); probes
  `footing.py` B and s.

## In this repository

This repository has no package, so this standard does not apply here; its `shape-spec.md` lists it
in Step 5a for consuming projects.

## In a consuming project

Synced in as `agent-os/standards/base/python/models.md`, its rules the project's, verified against
the project's own files; Step 5a includes it in every spec, with its full content in that spec's
`standards.md`.

---

## base/python/errors

# Errors

A patchbay package reports every failure as an exception of its own, carrying the fields that say
what failed. This standard says how the package's exceptions are arranged, what each carries and
what may leave a public method. Every rule names the file of a consuming project it is verified
against, the test that holds it and the probe a rule about a tool's behaviour rests on. Written from
fromtheoutfit/patchbay at `7471387`, the merge of its PR 11, whose contracts spec and that spec's
revision record each choice as a Decision; the evidence is in the `verification/` of the spec of
issue #21 in `patchbay-standards` and of its revision after the review of PR 25, patchbay's own
probes cited by name and the ones those specs added by letter.

Where a model's refusal comes from is `base/python/models.md`'s, and what the event bus raises and
lets through is `base/python/events.md`'s; this standard names both and restates neither.

## One root

- **A package's exceptions have one root, and every exception the package raises derives from
  it**: patchbay's `PatchbayError`, so a caller catches every failure the package reports with one
  `except`. The root derives from `Exception`, and no exception's MRO holds a built-in narrower
  than `Exception`, so a caller's `except ValueError` or `except KeyError` never catches the
  package's error by accident: `PatchbayValidationError` is not a `ValueError`, though the pydantic
  error it stands in for is. The one exception is the contract suite's violation,
  `ContractViolationError`, an `AssertionError`: it is a failed assertion to pytest, raised by a
  test and never by the package's API (`base/testing/tests.md`). Verified against
  `src/patchbay/errors.py`, `src/patchbay/testing/contract_tests.py` and
  `tests/unit/test_errors.py` (`test_error_is_a_patchbay_error_and_no_builtin_subtype`).
- **Every exception's name ends in `Error`**, the root's included, as ruff's N818 asks under
  `select = ["ALL"]`. Verified against `src/patchbay/errors.py`,
  `src/patchbay/testing/contract_tests.py` and `pyproject.toml` (`[tool.ruff.lint]`, whose ignore
  list does not hold N818); probe j.

## Fields and messages

- **An error takes its fields as constructor arguments, keeps each as an attribute of the same
  name, and passes them to `Exception.__init__` in the same order**, so `args` holds them, and
  `copy` and pickling, which rebuild an exception by calling its class with its `args`, rebuild it.
  An error that passed a message instead cannot be copied or unpickled. Its message is `__str__`,
  built from the fields. The root takes no fields. Verified against `src/patchbay/errors.py` and
  `tests/unit/test_errors.py` (`test_fields_are_attributes`, `test_error_is_rebuilt_from_its_args`,
  `test_message_is_built_from_the_fields`); probe f (f3).
- **A field is typed as the plain value it is**: an id or a unit as `str`, a bound or a value as
  `float`. The errors module then imports nothing from its own package, and every other module can
  import it: it is the leaf the package's modules are built up from (`base/python/layout.md`). A
  third party's type a field carries is imported from the package that defines it, which the
  manifest declares: `PatchbayValidationError.details` holds pydantic-core's `ErrorDetails`, which
  pydantic does not re-export (`base/python/toolchain.md`, "Dependencies"). Verified against
  `src/patchbay/errors.py`, whose one import is `pydantic_core`, and `pyproject.toml`
  (`[project] dependencies`); probe f (f2).
- **No field takes the name of a third party's method on the error it stands in for.** A
  validation error's refusals are `.details`: pydantic's `ValidationError.errors` is a method, and
  a tuple of that name fails code ported from it with "'tuple' object is not callable", where a
  missing attribute fails it by name. A failure that carries exceptions holds them as
  `.exceptions`, the name `ExceptionGroup` gives them. Verified against `src/patchbay/errors.py`
  and `tests/unit/test_errors.py` (`test_no_field_is_named_like_pydantic_s_errors_method`); probe
  f (f2).

## What escapes

- **No built-in exception leaves a public method.** A lookup that fails is the package's not-found
  error, `ParameterNotFoundError(parameter_id, instrument)`, never `KeyError`; a value a parameter
  does not take is `ValueOutOfRangeError` or `UnitMismatchError`, never `ValueError`; a refused
  model input is the package's validation error (`base/python/models.md`). Two named exceptions,
  each passing an exception the package did not raise: validation pydantic runs on behalf of
  something else raises pydantic's error (`base/python/models.md`), and a `BaseException` that is
  not an `Exception` passes through the bus where a subscriber raised it
  (`base/python/events.md`). Verified against `src/patchbay/errors.py`,
  `src/patchbay/testing/fake.py` (`_parameter`), `src/patchbay/testing/contract_tests.py`
  (`an_unknown_id_raises_parameter_not_found`, `a_value_out_of_range_raises_value_out_of_range`)
  and `tests/unit/testing/test_fake.py`
  (`test_get_of_an_unknown_id_names_the_id_and_the_instrument`).
- **An error raised in place of another is chained from it**, `raise ... from error`, so the cause
  stays on `__cause__`: the validation error from pydantic's, the JSON-data refusal from `json`'s,
  the bus's failure from the first subscriber's exception, a refused patch from the check that
  refused it. The one exception is `from None` where the replaced error is the lookup's own
  `KeyError`, which says nothing the not-found error does not. An error with no cause, a patch for
  another instrument, is raised plainly. Verified against `src/patchbay/models.py`,
  `src/patchbay/events.py`, `src/patchbay/testing/fake.py` (`_parameter`, `_check_whole`),
  `tests/unit/test_models.py` (`test_every_entry_point_refuses_with_patchbay_validation_error`,
  `test_from_json_data_refuses_data_json_cannot_hold`) and `tests/unit/test_events.py`
  (`test_a_failing_subscriber_hides_the_event_from_no_other`).

## In this repository

This repository has no package, so this standard does not apply here; its `shape-spec.md` lists it
in Step 5a for consuming projects.

## In a consuming project

Synced in as `agent-os/standards/base/python/errors.md`, its rules the project's, verified against
the project's own files; Step 5a includes it in every spec, with its full content in that spec's
`standards.md`.

---

## vital/instrument

# The instrument

What `VitalInstrument` promises beyond core's protocol, and what a later Vital feature must not
break. A rule here is about Vital as an instrument; what the hosted plugin does is
`vital/plugin-state.md`'s, the map's conversions `vital/parameter-map.md`'s, and how a test asserts
audio `vital/measures.md`'s. Written from `src/patchbay_vital/instrument.py`, `patch.py`, `midi.py`
and `start.py`; the evidence is the `verification/` of the spec of issue #8
(`agent-os/specs/2026-11-15-1448-the-instrument/`), every measurement in it made on Vital 1.6.4
through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2): `probes.txt`, `probes-2.txt`,
`contract-run.txt`, `carrying-count.txt`, `off-grid-count.txt` and `mutation.txt`. Each rule names
the test that holds it; a unit test runs over a fake plugin, so CI holds it, and a test of
`tests/integration/test_vital_instrument.py` runs against the installed Vital.

## The model

- **The model is the source of truth, and the plugin's state never becomes it.** The instrument
  holds a `VitalPreset`: `get` reads it, `patch` carries it, `set` writes through to it and to the
  plugin, `load_patch` replaces it and sends its text. Not even the first model comes from the
  plugin: the instrument starts on the preset the package ships. Verified against
  `test_it_starts_on_the_start_preset_loaded_into_the_plugin_twice`, which gives the plugin a state
  of its own first, and `test_the_next_instrument_starts_clean`.
- **The plugin's own view is a diagnostic read, used by tests alone.** `instrument.host.state()` is
  what the plugin holds; a test reads it to hold the plugin to the model, and no method of the
  instrument reads it. `instrument.preset` is the model. Verified against
  `test_after_a_set_at_each_bound_the_plugin_holds_the_model_s_float` (1,806 bounds, counted) and
  ML1 in `mutation.txt`.
- **The start preset is generated, never edited, and cannot drift.** `data/start.vital` holds the
  map's 903 defaults, 64 empty slots and media of the package's own, each from a formula: a ramp as
  each wavetable, two-point lines, a 16-sample ramp. The census writes it beside the map and the key
  list, all three together or none. It holds none of Vital's presets, wavetables, samples or LFO
  shapes; shipping it is the owner's licence call of 2026-11-15, revisited before any release.
  Verified against `tests/unit/test_start.py` (every float, every section rebuilt from its formula
  there, the file byte for byte through the format),
  `test_the_three_committed_files_are_what_the_census_writes_from_the_committed_map`,
  `test_the_census_regenerates_the_three_committed_files`,
  `test_a_rename_failing_at_the_start_preset_puts_the_key_list_and_the_map_back` and MS1, MS2 and
  MC1.

## What a set holds

- **A set holds the value Vital holds for the display given, the map's `to_preset`, and no other
  rule.** `get` then returns that value's display and `ParameterChanged.new` carries it. It need not
  be the held value nearest the one given: `beats_per_minute` given 216.85141355537831 holds
  216.8514347076416. A second rule beside the map's is what issue #16 removed. Verified against
  `test_a_set_holds_the_value_vital_holds_which_need_not_be_the_nearest`, in both test modules, its
  expected value from primitives, and MR1.
- **A bound comes back exactly.** Verified against
  `test_every_bound_of_every_parameter_comes_back_exactly`, 1,806 counted, and core's
  `get_after_set_returns_what_was_set`.
- **A value between steps is taken and the nearest step held,** a half away from zero. 29 continuous
  parameters are stepped, and not all in whole numbers: `chorus_voices` runs in fours and
  `oversampling` in powers of two. Core's `Parameter` does not show a step. Verified against
  `test_a_value_between_steps_is_taken_and_the_nearest_step_held`.
- **A set of the value a parameter already shows keeps what it holds,** in the model and the plugin,
  and is still published, `old` equal to `new`. A preset holds floats no set lands on, 22 of the 903
  defaults and 2,201 of the 57,671 floats of the installed presets, and a set of such a float's own
  display would hold a neighbour. Verified against
  `test_a_set_of_the_value_already_shown_keeps_what_is_held`, 22 counted, `off-grid-count.txt` and
  MK1.
- **One case of core's clause is not met, and a characterization test holds it.** A float off the
  grid, once another value has been set, is not got back by a set of the display `get` first
  returned for it: the parameter holds the neighbour. Verified against
  `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour` and, against the
  installed Vital, `test_an_off_grid_float_set_back_after_another_value_holds_its_neighbour_on_vital`,
  each naming by its title the issue drafted for core; that spec's `shape.md` gives the number it
  was filed under.

## A patch

- **A float is carried in exactly one place.** In `values`, as the display that carries it, where
  the display passes `Parameter.check` and converts back to the very float, checked for that float
  as the patch is built; otherwise in `opaque["preset"]`, as itself. Never both: a patch that
  carries one parameter twice is refused by name. So every entry of `values` is one `set` takes.
  Verified against `test_a_float_is_in_values_or_in_the_entry_and_never_in_both`,
  `test_a_float_its_display_cannot_carry_rides_in_the_entry_though_it_is_in_range`,
  `test_a_parameter_carried_in_both_places_is_refused_by_name` and MP1, MP2 and MP3.
- **A preset comes back byte for byte,** through a patch and through the patch's JSON, a key it
  lacks staying absent. Verified against
  `test_a_built_preset_comes_back_byte_for_byte_through_a_patch_and_through_json`,
  `test_a_factory_preset_round_trips_through_a_patch`,
  `test_a_pack_preset_round_trips_through_a_patch`,
  `test_each_installed_preset_loads_through_a_patch_and_comes_back_byte_for_byte` and
  `carrying-count.txt`: 77 texts, 59,477 floats, 35 of them in the entry.
- **A float outside its parameter's bounds is shown truly, refused on set, and carried.** `get`
  returns 141.44 for `flanger_dry_wet` at 0.7072; it is absent from `values`; a set of a value in
  range brings it in. Verified against
  `test_a_preset_holding_a_float_outside_its_bounds_is_shown_refused_on_set_and_carried`.
- **`opaque` has fixed keys, and any other is refused by name:** `preset`, `settings.<name>`,
  `line_mapping.<slot>`, `tuning`. Verified against `test_what_opaque_holds_is_under_its_fixed_keys`
  and `test_an_opaque_key_that_is_no_entry_of_a_vital_patch_is_refused_by_name`.
- **A patch of values alone is the start preset with those values.** Entries without a `preset`
  entry are refused. Verified against
  `test_a_patch_of_values_alone_loads_as_the_start_preset_with_those_values`, in both test modules,
  `test_an_entry_without_the_preset_entry_it_belongs_to_is_refused` and MP5.
- **A patch is taken whole or refused, and the refusal names the first entry to refuse,** in a fixed
  order: the instrument's name, the `opaque` keys sorted, the `values` sorted by id, the preset they
  make. A refused patch leaves the model, the plugin and the bus as they were. Verified against
  `test_the_first_value_to_refuse_is_the_first_by_id`,
  `test_a_patch_refused_part_way_leaves_the_model_the_plugin_and_the_bus_as_they_were`, which unlike
  core's contract test carries its sections, and MP6.

## What the instrument does about Vital's loads

What Vital does with a load, measured, is `vital/plugin-state.md`'s. These are the instrument's
rules on it.

- **A preset seen to block, to be ignored or to keep old sections is refused before the plugin is
  called.** The guard refuses a `synth_version` that is no version or is newer than the plugin's,
  `wavetables` and `lfos` that are not arrays of three and of eight objects, a `sample` without its
  four keys, and a float with no finite display. Verified against
  `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called`, fifteen
  shapes, `test_the_guard_passes_what_vital_was_seen_to_load` and MG1 to MG4.
- **The guard judges a section's shape, never its inside, so a malformed section can still hang the
  process.** The instrument's docstring and the README say so in those words. Measured on Vital
  1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2): three texts pass the guard
  and never return. The remedy is issue #20's, a load that cannot block. Verified against
  `test_the_guard_does_not_read_inside_a_section` and `probes.txt` section 5.
- **Every load is made twice.** A measured workaround with no known cause, on Vital 1.6.4 through
  pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Verified against
  `test_one_load_after_a_set_leaves_the_off_grid_floats_off_and_a_second_holds_them`, which a Vital
  needing one load or three fails by name, and ML2 and MV1.
- **For a preset older than the plugin, the model keeps the file's floats.** Vital upgrades it, so
  `get` can report the file's value where Vital plays another, which for a choice is another setting
  by name: 46 floats on 11 of the 75 installed presets, measured on Vital 1.6.4 through pedalboard
  0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). Stated as that, never as rounding. What the model
  should hold is issue #22's to decide. Verified against
  `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none` and
  `tests/data/upgraded-floats.txt`.
- **When the plugin refuses a text after the checks pass, the model's own text is sent again.** The
  call is refused as a patch, chained from the host's error, and the plugin holds the model's
  floats. Verified against
  `test_a_load_the_plugin_refuses_puts_the_model_s_text_back_and_is_refused_as_a_patch` and ML1.

## Events and errors

- **Checks, then the plugin, then the model, then one event.** A refused call publishes nothing and
  changes nothing; a carried-out one publishes once, after the change. Building the instrument
  publishes nothing. `PatchLoaded.parameter_count` is the number of values in the patch given.
  Verified against core's contract tests,
  `test_a_subscriber_that_raises_leaves_the_set_made_and_published`,
  `test_parameter_count_is_the_number_of_values_in_the_patch_given` and ME1 and ML3.
- **Nothing but the package's errors leaves the instrument, each core's own too.** What
  `Parameter.check` raises is raised again as the package's, with core's fields and core's error its
  cause. Verified against `test_every_refusal_is_the_package_s_error_and_core_s`,
  `test_a_set_it_refuses_is_the_package_s_error_with_core_s_fields_and_core_s_error_its_cause` and
  MP7.

## A render

- **A render has declared limits, named constants with their source,** and one past them is refused
  naming the limit and its value: `MAX_SAMPLES`, 2 ** 24, a length Vital gives, and a rate from
  1,000 to 768,000 Hz, the range measured. Verified against
  `test_a_render_past_a_limit_is_refused_naming_the_limit_and_its_value`,
  `test_the_longest_render_is_given_and_one_sample_more_is_refused` and MN2 and MN3.
- **A render of no samples is an empty result, the plugin not called,** as core's reference gives
  it. Verified against `test_a_render_of_no_samples_is_an_empty_result_and_the_plugin_is_not_called`
  and MN1.
- **A render that reaches full scale carries one warning saying the peak and where; the audio is
  never clipped here.** At full scale counts. Vital gives samples up to 2.1. Verified against
  `test_a_render_that_reaches_full_scale_carries_one_warning_saying_the_peak_and_where`,
  `test_a_render_whose_largest_sample_is_exactly_full_scale_carries_the_warning`,
  `test_a_render_that_clips_carries_one_warning_and_the_event_carries_it` and MN4.
- **A render of most presets opens with the preset sounding though no note was played.** The warning
  counts that sound. On the start preset it is a transient of about 0.02; on installed presets it
  reaches full scale, measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). Held as it is until issue #21, a render that does not open so, changes it. Verified
  against `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding`, which
  names the issue,
  `test_a_render_of_no_notes_on_the_start_preset_is_its_small_transient_and_no_warning` and
  `probes.txt` sections 4 and 4b.
- **A note's bytes are core's `Note` as it is, and its time is half a sample past its sample.** The
  time of the sample itself lands one sample early on some samples. A note that starts at the
  render's length is left out, and a note-off there too. Verified against `tests/unit/test_midi.py`,
  its bytes written out, `test_a_note_lands_on_the_sample_core_s_rule_gives_it`, at a sample where
  the two differ, `probes.txt` section 1 and MM1 to MM4.

## The contract suite

- **A contract run is named for what it runs against.** `test_contract_against_vital` runs core's
  thirteen against the installed Vital; `test_contract_against_a_fake_plugin` runs them over a real
  `VitalHost` on a fake plugin, which CI can. A pass over the fake plugin is not a pass against
  Vital, and the local run is the only one against Vital. Verified against both tests and
  `contract-run.txt`.
- **Each integration module loads Vital once; each test gets a new bus and a new instrument.**
  Building the instrument loads the start preset, so no test's state reaches the next, in the model
  or the plugin. No `conftest.py` holds the fixtures: the gate's negative test q writes one.
  Verified against `tests/integration/test_vital_instrument.py` (`vital`, `bus`, `instrument`) and
  `test_the_next_instrument_starts_clean`, which compares the plugin's 903 floats.

---

## vital/parameter-map

# The parameter map

How the map between Vital's VST3 parameters and a preset's keys is made, held and converted. A rule
here is about Vital's parameters; what any adapter's models do is `base/python/models.md`'s.
Written from `src/patchbay_vital/parameters.py`, `float32.py`, `census.py` and
`data/parameters.json`; the evidence is the `verification/` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`), measured on Vital 1.6.4 through
pedalboard 0.9.26 on arm64, of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), of the revision after the second
review (`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), of the revision
after the third (`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`), of the spec
of issue #13 (`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`), of the
revision after PR 14's review (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`), of
the revision after its second review
(`agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`), of the spec of issue #15
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`), of the revisions after
PR 14's fourth, fifth and sixth reviews
(`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`,
`agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/` and
`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`), of the spec of issue #16
(`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`), of the revision after the
review of patchbay-vital's PR 19 (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/`)
and, for the census's third file and what an arbitrary display takes, of the spec of issue #8
(`agent-os/specs/2026-11-15-1448-the-instrument/`).

## Where it comes from

- **The map is measured from the plugin and committed as data, never written by hand or from Vital's
  source.** `census.py` sets each hosted parameter on a grid of normalized values, reads which state
  float moves and what the plugin displays, fits the scales and writes `data/parameters.json`; a
  parameter it cannot fit is `CensusError`, naming it, as are two parameters moving one preset
  value, a record the map's models refuse and ends that make no scale, and nothing is written;
  what is written is written whole or not at all, the key list, the map and the start preset
  (`vital/instrument.md`), which holds the map's defaults, all staged and then renamed over in
  turn, an earlier one put back when a later rename fails
  (`patchbay_vital.files.replace_files`), so the three never disagree. The scale is fitted by
  building the linear one once and the indexed one only where both ends are whole. Vital's source
  is GPLv3 and may be cited for corroboration, never copied. A new Vital is a new census in a
  spec. Verified against `census.py` (`build_map`, `fit_scale`, `_record`, `main`),
  `tests/unit/test_census.py` (`test_a_scale_that_is_neither_is_named`,
  `test_ends_that_make_no_scale_are_named`, `test_texts_in_no_one_known_unit_are_named`,
  `test_two_parameters_moving_one_preset_value_are_named`,
  `test_a_default_that_displays_as_no_number_is_named`,
  `test_a_key_list_that_cannot_be_written_leaves_the_map_unwritten`,
  `test_a_rename_failing_after_the_key_list_s_puts_the_key_list_back`,
  `test_a_rename_failing_at_the_start_preset_puts_the_key_list_and_the_map_back`,
  `test_the_three_committed_files_are_what_the_census_writes_from_the_committed_map`) and
  `tests/integration/test_vital_plugin.py`
  (`test_the_census_regenerates_the_three_committed_files`).
- **The map records the machine the census ran on and the plugin it measured, and is used with
  no other.** The scales are the plugin's build's: the arm64 build computes a scale with one fused
  multiply-add, and another build may round the product and the sum apart, which the exact fit
  would refuse rather than write; the records are one version's parameters, and another version
  may rename or rescale them. `ParameterMap.machine` is `platform.machine()` where the census
  ran, `instrument` and `vital_version` what the plugin reported, `host` the pedalboard it ran
  through; the host refuses the map where the machine, the instrument or the version differs,
  naming which, and compares the host not at all (`vital/plugin-state.md`); a new census is the
  remedy. Verified against `census.py` (`build_map`), `parameters.py` (`ParameterMap`),
  `host.py` (`_parameter_map`), `test_the_map_records_the_machine_the_census_ran_on` and
  `test_the_committed_map_holds_every_hosted_parameter`.
- **A parameter's id is its preset key; pedalboard's key is `host_id`, read only by `host.py`.** 256
  of the 903 differ (`envelope_1_attack` is `env_1_attack`), and the preset key is the one a file, a
  diff and the instrument share. Verified against `parameters.py` (`MappedParameter.id`,
  `ParameterMap.find`), `host.py` and `tests/unit/test_parameters.py`
  (`test_a_map_finds_a_record_by_its_preset_key`).
- **`settings_keys.txt` is derived from the map, and a census never forgets a key**: its ids but
  the per-slot ones, and `PRESET_ONLY_KEYS` (`chorus_damping`, which old presets hold and no
  parameter does). The census writes both files, and the start preset beside them, and a test
  holds each to the map. A key is
  known once Vital has written it, so a newer Vital that drops a parameter still has presets
  holding its key: the census refuses a list lacking a key the format knows now, `CensusError`
  naming up to four, and a spec adds them to `PRESET_ONLY_KEYS`, so the list stays derived from the
  map rather than kept as a union no map can check. Verified against `ParameterMap.settings_keys`,
  `census.py` (`key_list`, `main`), `test_the_format_s_key_list_is_derived_from_the_committed_map`,
  `test_the_committed_map_s_key_list_forgets_no_key_the_format_knows` and
  `test_a_key_list_that_would_forget_a_known_key_is_refused_and_nothing_written`.

## Two conversions

- **Normalized ↔ preset is `linear` or `indexed`, exact in float32.** The preset value is
  `r · span + minimum` rounded once to float32, a fused multiply-add as the arm64 build computes it
  (`float32.fma32`, in `Fraction` and integer rounding; separately rounded arithmetic is wrong on 252
  parameters); indexed rounds that to a whole number, a half away from zero, which the grid does
  land on: 0.5 on every boolean's scale computes to exactly 0.5 and the plugin holds 1 there, so
  `round`, a half to even, would fit no boolean. The span is computed once per pair of bounds and
  kept by them, never on the model, so a copy with another bound has its own. No tolerance
  anywhere. Back, `to_normalized` is the float32 nearest `(preset − minimum) / span`, unless
  `to_preset` of it misses the preset; then the float32 one step toward the preset
  (`float32.next_float32`), where that is in [0, 1] and lands on it, the scale rising with `r` so
  only that side can. On the 12 `env_N_delay` and `env_N_hold` records, at 126 powers of two each
  from 2 ** -125 to 1, the nearest multiplies back one float32 short, where the spacing halves, and
  only the step lands, so a set of 1.0 s holds 1.0 on Vital. The step is kept only inside [0, 1],
  where the host can set it, and that guard is reachable: on a scale from -1 to 2 ** 24 only the
  float32 above 1 lands on the maximum, so the maximum is not one the scale holds and its
  normalized value stays 1. `holds` says whether some normalized value in [0, 1] lands on a preset
  value, which `to_normalized` finds where any does; both read one private `_landing`, which
  computes the normalized value and where it lands once. `next_float32` narrows both its arguments
  to float32 first, as C's `nextafterf` receives them, and is the one way the package steps a
  float32; its tests check it against numpy's `nextafter`. Verified against `parameters.py`
  (`NormalizedScale`, `_landing`, `_round_half_away`, `_span`), `float32.py`,
  `tests/unit/test_float32.py` (`test_every_recorded_vector_is_the_plugin_s_value`,
  `test_a_float32_steps_to_its_neighbour_as_numpy_steps_it`), `tests/data/fma-vectors.txt`,
  `test_a_half_on_the_grid_goes_away_from_zero`,
  `test_a_scale_s_span_is_kept_by_its_bounds_so_a_copy_has_its_own`,
  `test_a_held_power_of_two_comes_back_through_the_normalized_path`,
  `test_a_scale_holds_its_values_and_none_past_its_ends` and
  `test_the_step_toward_a_preset_stays_where_the_host_can_set_it`.
- **Preset ↔ display is a curve: `multiply · skew(preset) + offset`**, the skew one of the six
  measured (linear, quadratic, quartic, square root, 2^x, 2^−x), its constants the shortest decimals
  that print every display text at six significant digits. A record's `Parameter` is in display
  units and its bounds and default are what the scale and curve compute, exactly on the machine
  that measured them; the model holds the record together in float32, the bounds and the default's
  display reaching the scale's ends and the preset default through the curve, so a libm whose
  `pow` is a double ulp apart still reads the map, and `to_preset` takes the parameter's own bounds
  and this platform's display of the scale's ends alike. Those displayed ends are computed in one
  place, `displayed_ends`, sorted whatever the curve's direction and kept by the curve's and the
  scale's values, which the census writes a parameter's bounds from and `to_preset` bounds by.
  Verified against `DisplayCurve`, `displayed_ends`, `MappedParameter`
  (`_the_parameter_reaches_the_scale`, `to_preset`), `census.py` (`_fit_curve`, `_record`) and
  `test_a_record_whose_parameter_is_not_its_scales_is_refused`,
  `test_a_record_holds_together_in_float32_so_a_libm_an_ulp_apart_still_reads_it`,
  `test_a_record_s_displayed_ends_are_the_scale_s_through_its_curve_in_order`,
  `test_a_curve_and_its_unit_are_found_from_the_texts`.
- **A displayed value comes back exactly, and so do the preset a parameter holds and the preset a
  display maps to, each through the normalized path, on every value; and the preset a display maps
  to is the held one but where neighbouring presets share a display, the one exception, stated over
  values, never a record's name.**

  **The rule.** `MappedParameter.to_preset` first takes the float32 nearest the curve's inverse,
  within the scale, and on an indexed scale the nearest whole number to it, a half away from zero.
  The answer is what a set of that value holds: the scale's value at `to_normalized`'s result,
  Vital's own rounding of it, which is the value itself wherever the scale holds it. There is one
  exception: the float32 on the other side of it, away from what the set holds, is the answer
  where what the set holds does not show the display exactly, that float32 does, and the scale
  holds it. So the answer is always a preset the scale holds, and a set of
  `to_normalized(display)` holds it (issue #16).

  So a set of any display a parameter shows holds a preset that shows it, on Vital as in the map.
  Only `volume`, at or below its 2 ** -43, has a float32 the scale skips for a display it shows,
  on 16,069,858 normalized values:
  - on 15,761,472 of them, what a set holds shows the display, so a set holds what it held before
    issue #15;
  - on the other 308,386, the values where a set before the fix showed a display one double off,
    the float32 on the other side is taken, the exception;
  - on no value does what a set holds fail to show the display with nothing on the other side to
    take (`UNHELD` 0 then, `FELL` 0 in issue #16's count).

  These are counted from `to_preset`'s own results in the revision after PR 14's fifth review,
  `agent-os/specs/2026-11-12-1852-revision-after-pr-14-fifth-review/verification/direct-count.txt`,
  run on arm64, macOS 26.6.2 (25G83), with `main` at commit `558b85b` and this branch's work tree
  on `d21f160`, each file read printed by blob. The shipped method is called on every float32
  normalized value of `volume`, the branch read from what it returns, and every count split value
  by value at a held preset of 2 ** -43. No value above 2 ** -43 leaves the curve's float32. The fourth review's
  `verification/sweep.txt` gave the same three counts, but as a numpy reproduction's.

  The code holds the rule in `to_preset` itself: what a set of the curve's float32 holds, with
  the exception tried only where that is not the float32 and does not show the display. The sixth
  review's
  `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/floor-pass.txt`
  calls `e852aac`'s shipped methods, which these counts describe, and the restructured ones,
  each imported from its own tree, on every float32 normalized
  value of `volume` below 2 ** -54 and at the envelope group's 143 held powers of two, and
  finds no `to_preset` or `to_normalized` changed; no other value can differ, by reading.

  What a set holds comes first, so where both it and the float32 on the other side show the
  display, it is taken (`test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`, at issue
  #13's value). The exception asks `NormalizedScale.holds` of the float32 on the other side. A
  float32 past an end the scale does not hold can show the display and still be one no normalized
  value in [0, 1] lands on, so it is refused and the display takes what a set holds, the float32
  below the end: `test_the_float32_past_an_end_the_scale_does_not_hold_is_not_taken`, on a
  constructed scale whose maximum is unheld. An end is not always held.

  **`holds` answers False for a value outside what the scale's ends land on,** `to_preset(0.0)`
  and `to_preset(1.0)`, before it lands the value. That covers an infinity, a NaN and a finite
  value too large for its quotient to be a float32, each of which raised a built-in
  (`test_a_scale_holds_no_value_that_is_not_finite`,
  `test_a_scale_holds_nothing_outside_what_its_ends_land_on`), so the exception never raises.
  - The check is against what the ends land on, never the bounds. From -16777216 to
    1.0000001192092896 the span rounds up and 1 lands on 2, past the maximum, which the scale
    holds (`test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum`). On all
    903 committed records 0 lands on the minimum and 1 on the maximum.
  - It rests on the scale's value rising with the normalized value
    (`test_a_scale_s_value_rises_with_the_normalized_value`). No committed scale runs the other
    way, and `holds` answers as it did before the check on every committed record: 13,397
    presets at the pinned values and 798,179 at the indexed whole numbers, their halves and
    past each end (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/verification/holds-check.txt`).
  - `holds` does not test the landing's normalized value again, as it did before the check.
    Within what the ends land on, a preset the landing reaches is reached from [0, 1]:
    `_landing` keeps its step there, and the float32 nearest the quotient is there by
    rounding, since what 1 lands on is at most `span * 2 ** -24` past `minimum + span`
    (`test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval`; the argument is
    Decision 10 of that revision's `shape.md`, and the test put back is M3, an equivalent, in
    its `verification/mutation.txt`).
  - The scale's own `to_normalized` and `to_preset` still raise a built-in on a value outside
    what the scale can take, finite or not: issue #18.

  `to_normalized` of a display is `scale.to_normalized(to_preset(display))`, the scale's own
  normalized value for the preset `to_preset` gives, by definition. It lands that preset a
  second time, so it costs about 27 µs a call on `volume` against `main`'s 8, measured on an
  Apple M4 Pro, arm64, 14 cores, under macOS 26.6.2 (25G83) with Python 3.12.16
  (`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/cost.txt`);
  no fast path is kept for it.

  The fourth review's `verification/plugin-probe.txt` shows a load of the curve's float32 held by
  Vital at that same value. The rule has no tie to break. It replaced the neighbour nearer the
  curve's inverse, whose exact ties only a sort's order decided.

  **An arbitrary display.** One no held preset shows exactly takes what a set of its float32
  holds, a held preset that shows another display: `beats_per_minute` at 216.85141355537831 takes
  3.6141905784606934, shown as 216.8514347076416. Before issue #16 the rule had a third branch
  there, which kept the curve's float32, one the scale need not hold, so a model that stored it
  disagreed with what Vital held after a set. The sweep and the direct count reach only displays
  some held preset shows, so an arbitrary display is held by tests and by a sample:
  - `test_an_arbitrary_display_takes_what_a_set_of_it_holds`, at the two `tempo_displays` of
    `tests/data/pinned-values.txt`, on `beats_per_minute`'s scale and curve, built in the test
    module as `_TEMPO`. It reverses `test_an_arbitrary_display_keeps_the_curve_s_float32`, issue
    #16's characterization, on purpose.
  - `test_any_display_in_range_maps_to_a_preset_a_set_of_it_holds`, on every hand-built record,
    and `test_every_committed_record_maps_any_display_to_a_preset_a_set_of_it_holds`: the
    normalized value is in [0, 1], the forward scale lands it on `to_preset`'s value, and that
    value is what the test works out a set holds, or the float32 on the other side where that
    shows the display and what the set holds does not. The helper checks the exception both
    ways: where the map takes what a set holds and that does not show the display, the other
    side must not be one the rule would take. A draw over a parameter's bounds does not reach
    a display a held preset shows, so the two properties pass a `to_preset` without its
    exception; the pinned displays hold it, through the same helper, in
    `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds` (M5 in the
    `verification/mutation.txt` of the revision after the review of patchbay-vital's PR 19).
  - A sample, never a count, since a group's displays are doubles and cannot be enumerated:
    200,000 displays a continuous group, uniform over its bounds (`numpy.random.default_rng(16)`),
    11,000,000 over 55 groups, each through `main`'s shipped methods and the spec's. 2,041,885
    give another preset than `main`'s, on 31 groups. On every one `main`'s preset was not held,
    the new one is, and the normalized value a set sends is the same. Of 20,000 over `volume`'s
    range (seed 8), 1,108 change, the ones that took the third branch
    (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/verification/arbitrary-displays.txt`).
  - At `volume`'s floor the doubles can be enumerated, so they are counted: of the 23,726,567
    from -80 to the display at 2 ** -43, 344,580 give another preset than `main`'s. `main`'s
    showed the display and was not held; the new one is held and shows a display one double away.
  - Vital 1.6.4 holds the map's preset after a set of 200 seeded arbitrary displays on each of
    the 46 linear-scale groups, 9,200 sets, and held `main`'s value on none of the 2,085 that
    changed (that spec's `verification/plugin-probe.txt`).

  Which held preset an arbitrary display takes is decided: Vital's rounding, as here. Issue #8's
  spec declined the nearer held neighbour, which would be a second rule beside this one
  (`vital/instrument.md`, "What a set holds").

  **An indexed scale** goes through the same set path: its display goes to the nearest whole
  number, a half away from zero, as the plugin rounds, and the answer is what a set of that whole
  number holds. On every whole number of every one of the map's 351 indexed records that is the
  whole number itself, as on `main`: 398,563 calls, counted in full, over 21 distinct scales
  holding 371,476 whole numbers (that spec's `verification/indexed-count.txt`). On a scale wider
  than its float32s, which the map has none of, it is the nearest whole number the scale holds,
  not always the one asked for: on a constructed scale from -1 to 2 ** 24 the bound's display
  takes 16777215 (`test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds`).

  An indexed scale takes the exception too, but only where the float32 on the other side is
  itself a whole number: from 2 ** 23 up, where float32s are 1 apart. The map's widest indexed
  scale ends at 362,879, so no value of the map does. The branch is held by a test on a made-up
  record, an indexed scale from -2 ** 24 to 2 ** 24 under a linear curve of multiply 3 and
  offset 2 ** 54, where the held 8388610 comes back only through it
  (`test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display`; limited to
  linear scales, `to_preset` gives 8388612 there, MI1 in that revision's
  `verification/mutation.txt`).

  **The exception, in plain words.** `_assert_comes_back` runs every check exactly first, on every
  value. Only where the check that the display's preset is the held one fails does it ask
  `_unnamed_by_its_display`, and the value then passes only if that holds: the curve's own
  float32 for the display is not the held preset, so the display does not name it, and the
  display's preset is what a set of that float32 holds. The test works that value out from
  primitives (`_what_a_set_holds`: `curve.to_preset`, the float32 nearest the exact quotient,
  worked out with `Fraction`, the forward `scale.to_preset` at it and at the float32 either side,
  and `next_float32`), never from `MappedParameter.to_preset` or `to_normalized`, the scale's
  `to_normalized`, `holds` or `_landing`, so a wrong rule or a wrong landing in the map cannot
  agree with itself. Before issue #16 the helper called the scale's `to_normalized`, and a
  `_landing` that kept a missed step passed the property; it now fails it by name (issue #16's
  `verification/mutation.txt`).
  - It is asked on 570,997,534 values, all of `volume`'s, every one below 2 ** -54 at a held
    preset at or below 2 ** -43, and holds on each. There the display's preset is another held
    one that shows the display, and the display cannot say which of them was held. Counted with
    the shipped methods and the test module's own predicate, value by value, in
    `agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/verification/floor-pass.txt`,
    which also finds no value at or above 2 ** -54 asking it. The fourth review's reproduction,
    `agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/verification/sweep.txt`,
    gave the same total and no value of the other 68 groups asking it.
  - The float32 on the other side, which `to_preset` takes as its exception, is not
    excused: that count finds it on no value, so a record that needed it would fail the
    property. The test module's hand-built records are not counted.
  - `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds` offers it what it must
    refuse: at `_SHARED`, a `volume` value in binade -80, a held float32 three steps away that
    shows the display, the held float32 on the other side, and, at that float32's own display,
    which names it, the preset `_SHARED` held. Each refusal is held by a mutant (MA, MB and MP2
    to MP4 in the sixth review's `verification/mutation.txt`).
  - It replaced `_shares_its_display`, which asked whether the float32 next to the held preset
    toward the display's preset shows the display. On a monotone curve that holds wherever the
    display's preset shows it, the property's first assertion, so it bounded nothing (the sixth
    review's finding 1).

  **The pinned values.** The values that found each defect are written once, in
  `tests/data/pinned-values.txt`, each with its set and its name, and both test modules read it
  through `pytestconfig.rootpath` (`vital/measures.md`). They were the property's `@example`s;
  a decorator runs at import, before pytest's root is known, so
  `test_every_pinned_value_comes_back_on_every_record` runs them through `_assert_comes_back` on
  every hand-built record instead, and fails the regression only they reach whatever Hypothesis
  draws (MC in the sixth review's `verification/mutation.txt`).

  Verified against `MappedParameter.to_preset` and `to_normalized`,
  `NormalizedScale.to_normalized`, `NormalizedScale.holds`, `_assert_comes_back`,
  `_unnamed_by_its_display`, `_what_a_set_holds` and
  `test_a_value_the_parameter_holds_comes_back_exactly`,
  `test_every_committed_record_comes_back_exactly`,
  `test_a_display_excuses_only_what_a_set_of_its_own_float32_holds`,
  `test_every_pinned_value_comes_back_on_every_record`, `tests/data/pinned-values.txt`,
  `test_at_or_below_volume_s_floor_a_display_maps_to_a_held_preset`,
  `test_a_display_takes_what_a_set_of_the_curve_s_float32_holds`,
  `test_else_a_display_takes_the_float32_on_the_other_side`,
  `test_an_arbitrary_display_takes_what_a_set_of_it_holds`,
  `test_any_display_in_range_maps_to_a_preset_a_set_of_it_holds`,
  `test_every_committed_record_maps_any_display_to_a_preset_a_set_of_it_holds`,
  `test_the_doubles_beside_a_pinned_display_map_to_a_preset_a_set_of_them_holds`,
  `test_an_indexed_scale_wider_than_its_float32s_takes_what_a_set_holds`,
  `test_a_scale_holds_no_value_that_is_not_finite`,
  `test_a_scale_holds_nothing_outside_what_its_ends_land_on`,
  `test_a_scale_holds_what_its_top_lands_on_though_that_is_past_its_maximum`,
  `test_a_scale_s_value_rises_with_the_normalized_value`,
  `test_the_quotient_of_what_an_end_lands_on_is_in_the_unit_interval`,
  `test_an_indexed_scale_takes_its_other_side_where_that_alone_shows_the_display`,
  `test_a_value_between_an_indexed_scale_s_steps_goes_to_the_nearest_step`,
  `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`,
  `test_an_arbitrary_display_set_through_the_host_holds_the_map_s_preset`),
  `verification/census-run.txt`, the `verification/direct-count.txt`,
  `verification/indexed-count.txt`, `verification/arbitrary-displays.txt`,
  `verification/plugin-probe.txt` and `verification/mutation.txt` of issue #16's spec
  (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`), and the
  `verification/sweep.txt`, `verification/plugin-probe.txt` and `verification/mutation.txt` of the
  revision after PR 14's fourth review, and the `verification/floor-pass.txt`,
  `verification/mutation.txt` and `verification/cost.txt` of the sixth. The defects were first
  found by the
  `verification/sweep.txt` of issue #13's spec and the `verification/sweep-first.txt` of the
  revision after PR 14's review.
- **A claim about every value a scale holds is counted over every float32 normalized value,
  exponent by exponent, and is never drawn uniformly.** 56% of the float32 values in [0, 1] lie at
  or below `volume`'s floor, yet they make up only about 1.5e-17 of the interval's length. So probe
  4's 2000 uniform draws a parameter never reached them, and Hypothesis's 32-bit floats did.

  **Each scale and curve group is counted once, by its first record.** Every method the count's
  paths call reads only the group's key: the parameter's kind and bounds, the scale's kind and
  bounds, and the curve's kind, multiply and offset. So a record's count is its group's. The
  revision after PR 14's fourth review also counted 14 records beside their groups: the three
  records with a curve offset and the 11 envelope delay and hold records that are not their group's
  first. All 14 matched their groups, each table whole with its closing line, the run time
  stripped (the fifth review's `verification/duplicates.txt`), so a later count leaves them out.

  **The 69 groups.** The count covers all 69 of the map's groups, 1,065,353,217 values each. For
  the `linear`, `quadratic`, `quartic` and `square_root` curves, 60 groups, it reproduces the map's
  arithmetic exactly in numpy. For the 9 `exponential` and `exponential_inverted` groups it calls
  the platform's own `pow` and `log2` value by value, as `DisplayCurve` does. That count is true of
  the machine it ran on, macOS 26.6.2 on arm64, whose libSystem 1351 holds the libm, and of
  another machine only as far as its libm gives the same values.
  Issue #16's spec ran it again with the rule as it now reads: each of the 69 groups' tables
  equals the fourth review's, and no value takes what a set holds where that does not show the
  display (its `verification/sweep.txt`, a reproduction's, checked on 200,010 values a group).

  **The check before counting.** Each group's reproduction is first checked against the shipped
  scalar methods on 200,010 values. The check covers every value it counts, the branch each value
  takes, and the tests' own excuse as it then read, `_shares_its_display`. A value it cannot
  certify exact goes to an
  exact scalar computation instead. The check is a sample: of `volume`'s 200,010 values, 2,989
  take the first branch and 69 the second (the fifth review's
  `verification/arbitrary-displays.txt`). So a count the reproduction gives is called the
  reproduction's, with this size beside it.

  **An exception** consulted only where its claim fails is counted by the failures it leaves,
  each split by the value it allowed. A value it allows that the count never finds is not
  allowed (the sixth review's second candidate). It is tested by what it refuses, never by
  what it passes: a predicate the property's own assertions imply, as `_shares_its_display`'s
  was, bounds nothing, however its count reads.

  **A rule's branches are each counted.** A branch no counted value reaches is either removed or
  held by a unit test, and the standard says which. `to_preset`'s third branch was held by a test
  until issue #16 removed it; what an arbitrary display takes now is held by the tests and the
  sample above.

  **A claim over values that cannot be enumerated is sampled and called a sample,** with its
  size, its generator and its seed beside it, and never called a count. A display is a double,
  so a group's arbitrary displays are sampled; where a range's doubles can be enumerated, as
  `volume`'s 23,726,567 at its floor, they are counted, and the transcript labels each part.

  **A fix is counted against the old code itself: the old tree's shipped methods and the new
  tree's, each imported from its own tree and called value by value.** A count a reproduction's
  own definition forces to 0 is not evidence, in any form: by a copied guard, as issue #15's spec
  counted `CHANGEDx` and `NCHANGEDx`, or by building the new result from the old one wherever the
  old one lands, as the fourth review's sweep did. Both pairs were 0 by construction and are
  retired.

  The revision after PR 14's fifth review counted directly (`verification/direct-count.txt`),
  over every float32 normalized value of `volume` and of `env_1_delay`, which stands for the 12
  envelope records by their one group key:
  - on `volume` the display's preset differs from `main`'s on 16,069,858 values, all at or below
    2 ** -43, and the normalized value a set sends on 308,386 of them;
  - on `env_1_delay` the normalized value differs at 126 held powers of two, and no display's
    preset differs;
  - nothing else differs on either record;
  - a control with two branches swapped moves the counts, so they are read from the result.

  Issue #16's spec counted the same way
  (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/verification/direct-count.txt`),
  `main` at `f533b1b` against its work tree, on arm64, macOS 26.6.2 (25G83). A display a held
  preset shows is where that change is meant to move nothing, so any difference stops the run:
  - on `volume`, all five calls give `main`'s value on every one of the 1,065,353,217 values,
    with 15,761,472 taking what a set holds and 308,386 the exception, as before;
  - on `env_1_delay`, the display, its preset and its normalized value are `main`'s on every
    value;
  - a control with the exception removed moves 99,796 values of binade -56.

  **A count calls only what can differ, and shows which.** Both trees' `parameters.py` and
  `float32.py` are parsed, each function's statements compared with its docstring dropped, and
  each call the count makes followed to every function it can reach. A call that reaches only
  statements the old tree has cannot differ and need not be called in both trees. In issue #16's
  count 46 of 48 functions and module values were `main`'s, and only `to_preset` and
  `to_normalized` of a display reached the other two, so the envelope record was counted on
  those. A method is never ruled out by an earlier count of another tree.

  **A change inside one branch is recounted where that branch runs.** The revision after the
  review of patchbay-vital's PR 19 changed `NormalizedScale.holds` alone, which `to_preset`
  calls only from its exception.
  - Parsing both trees showed every other function's statements the same as in the tree issue
    #16's count ran on, 47 of 48.
  - That count's classes then say where the exception is taken: the 308,386 OTHER values of
    `volume`, in binades -58 to -56, with none entering it and falling through.
  - Those three binades were recounted against `main`, 25,165,824 values, with no difference and
    the same 308,386 (`agent-os/specs/2026-11-15-0811-revision-after-pr-19-review/verification/direct-count.txt`).

  An earlier count's classes say where a branch runs only for a tree whose statements up to
  that branch are shown to be the ones it counted.

  **A count's cost is timed as the count will run,** every pool at its full size at once. Issue
  #16's timing ran 4 processes and estimated 4.25 hours for `volume`; the count ran 13, on 10
  performance cores and 4 efficiency ones, and took 5.25. A stop on a budget is checked against
  the clock while the run goes, not only against the estimate made before it.

  **The other 67 groups were not counted directly,** by the owner's decision at about 2.5 hours
  wall a group. Two things hold the claim there, that a quotient which lands is returned
  unchanged:
  - the unit test `test_a_quotient_that_lands_is_the_normalized_value_whatever_lands_beside_it`,
    which fails when the step is preferred (M15 in the fifth review's
    `verification/mutation.txt`);
  - the fourth review's sweep, a reproduction's, with its check against the shipped methods on
    200,010 values a group.

  Verified against the `verification/sweep.txt`, both its sections, and the
  `verification/sweep-afterwards.txt` of the revision after PR 14's fourth review, the
  `verification/direct-count.txt`, `verification/duplicates.txt`,
  `verification/arbitrary-displays.txt` and `verification/mutation.txt` of the revision after its
  fifth review, `tests/data/pinned-values.txt`, every value of which
  `test_every_pinned_value_comes_back_on_every_record` runs through the property's own assertions,
  issue #13's among them, and the `@example`s
  `test_a_value_the_parameter_holds_comes_back_exactly` keeps: 0.0, 1.0 and 5.2383727406426375e-33.

## Units and kinds

- **A unit is the display's suffix, renamed into `patchbay.Unit` by one table**: secs and s are
  seconds, ms seconds (÷1000), dB db, % percent, semitones and c (÷100) semitones, Hz hz, and x, v,
  voices and none none; `Beats Per Minute` is bpm by its label. An unknown suffix fails the census.
  Verified against `census.py` (`SUFFIX_UNITS`, `LABEL_UNITS`) and
  `test_the_label_names_a_unit_the_display_does_not_print`.
- **A switch is a boolean, other names a choice, other numbers continuous.** An indexed parameter of
  two values shown Off and On, or as numbers, is a boolean; one whose texts are other names is a
  choice, two names included (`eq_low_mode` is Shelf or High Pass); a numeric one (transposes,
  voices) is continuous on its indexed scale. A choice's value is its index, the preset value less
  the scale's minimum (`delay_tempo` starts at 4), and a choice or a boolean takes a whole index
  and nothing else, core's rule for them, so `to_preset` refuses a non-whole value as
  `ParameterRangeError`. Verified against `fit_record`, `MappedParameter.to_preset`,
  `test_a_parameter_of_two_values_is_a_switch_or_a_choice`,
  `test_a_choice_is_its_index_from_the_scale_s_minimum`,
  `test_a_choice_or_a_boolean_takes_a_whole_index_and_nothing_else` and
  `test_numbers_on_an_indexed_scale_are_continuous`.
- **Empty or repeated choice names are told apart by their index** (`option_<i>`, `<name>_<i>`),
  a made-up name lengthened by `_<i>` again while it is a kept name's or one already given, so no
  two choices share a name whatever the plugin's list; the plugin's own names are kept in
  `choice_labels`, so core's rule that choices are distinct and non-empty holds. Six parameters
  need it. Verified against `census.py` (`_choices`),
  `test_a_made_up_name_never_collides_with_a_given_one` and
  `test_the_committed_map_tells_its_choices_apart`.

---

## vital/measures

# Measures, not samples

How a test asserts what Vital rendered or holds. Written from
`tests/integration/test_vital_plugin.py`; the evidence is the `verification/probes.txt` and
`verification/host-probes.txt` of the spec of issue #7
(`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`) and the
`verification/plugin-probe.txt` of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`) and of
the revisions after PR 14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/`
and `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`), of the spec of issue
#15 (`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`) and of the revision
after PR 14's fourth review (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`);
the pinned values' file is the revision after its sixth review's
(`agent-os/specs/2026-11-13-0853-revision-after-pr-14-sixth-review/`), and its set of displays
the spec of issue #16's (`agent-os/specs/2026-11-14-1509-to-preset-returns-a-held-preset/`); the
instrument's measures are the spec of issue #8's (`agent-os/specs/2026-11-15-1448-the-instrument/`),
`verification/probes.txt` and `verification/probes-2.txt`.

- **Vital's audio is not sample-reproducible**, so no test compares samples: two renders in a row
  differ, and so do two instances in one state (spectral centroids 4657 and 4610 Hz). Verified
  against `verification/probes.txt` ("two renders in a row identical: False").
- **Every audio assertion is a measure against a named tolerance, and the constant's comment says
  which probe its number came from and what the probe measured**: the 20 ms RMS variation of a
  routed render above 0.5 where the probe measured 1.351, the quiet before a note under 1e-6 where it
  measured 0. A tolerance with no source is a guess. Verified against the constants at the head of
  `tests/integration/test_vital_plugin.py` and `test_a_routing_only_in_the_preset_text_is_heard`,
  `test_a_note_sounds_from_its_time_and_not_before`.
- **A measure is the probe's own computation, written once**, so the test measures what the probe
  did: `_variation` is the probes' 20 ms RMS coefficient of variation over 0.2-1.4 s. Verified
  against `tests/integration/test_vital_plugin.py` (`_variation`) and `verification/probes.txt`
  (`variation`).
- **A measure over part of a render is taken under a window, never by a bare cut.** A segment cut
  out of a sounding note starts and ends on a step, and the step's own spectrum is in the measure:
  cut at sample 7,200 with no window, the low cutoff's centroid ran from 674 to 1,931 Hz over 20
  renders and its ratio to the high cutoff's fell to 1.19. Over the held note under a Hann window it
  is 320.56 Hz on all 20, and the ratio 7.331. The window's bounds are named constants beside the
  tolerance, with a comment saying why they sit inside the held note and clear of its start and end.
  Verified against `tests/integration/test_vital_instrument.py` (`_centroid`, `_held`, `_HELD_FROM`,
  `_HELD_TO`, `_CENTROID_RATIO`), `test_the_spectral_centroid_moves_with_the_cutoff`, `probes.txt`
  section 7 of the spec of issue #8, the bare cut, and `probes-2.txt` section 7b, the window.
- **A render is held to be audible before its spectrum is measured, and a measure guards its own
  division.** Each render's RMS over the held note is first above a named floor, so a silent render
  fails by name as silence and not as a centroid; and a measure that divides by a sum fails by name
  where the sum is nothing. Verified against `_rms`, `_AUDIBLE` and `_centroid`.
- **Where an event lands is an index, and is measured exactly.** A test that holds the time a note
  is sent at asserts the first sample that is not zero, after the opening is over, at a sample where
  the rule under test and the one it replaced differ: 100,003 at 48 kHz. Verified against
  `test_a_note_lands_on_the_sample_core_s_rule_gives_it` and MM1 in the `verification/mutation.txt`
  of the spec of issue #8.
- **What a render holds with no MIDI is measured against the preset it is on.** The opening sound is
  the preset's (`vital/plugin-state.md`), so a tolerance for quiet is taken past its measured end on
  the start preset, and a test of the opening itself names the preset it measured. Verified against
  `_OPENING_ENDS`, `_QUIET`, `_TRANSIENT`, `_OPENING_SOUND` and the tests that use them.
- **What Vital holds after a set is compared exactly with the value the map computes, and its
  display with the display set.** The map gives the preset a set holds, the scale's value at
  `to_normalized`'s result, and the test asserts that the state's float is that value, with no
  tolerance.
  - At `volume`'s pinned values at or below its floor it is `to_preset`'s value, one the scale
    holds and never the curve's own float32 (`record.curve.to_preset`), and its display is the
    display set. At issue #13's value that is what a set of the curve's float32 holds, and at the
    other three the float32 on its other side.
  - At the envelope records' pinned powers of two it is the power, a set of 1.0 s holding 1.0.
  - At an arbitrary display, one no held preset shows, it is `to_preset`'s value too, what a set
    of the display's float32 holds and never the curve's own float32, and its display is not the
    display set: `beats_per_minute`'s two pinned displays, and a display 37% of the way between
    the bounds on one record of each kind, scale and curve, a whole number where the record is
    not continuous.

  The expected value never comes from the method a test holds. Where a test needs what a set
  holds without asking the map, it works it out from primitives: the float32 nearest the exact
  quotient, with `Fraction`, and the forward `scale.to_preset` at it (`_nearest_quotient`). The
  load test's expected value followed a wrong `_landing` until issue #16 worked it out so.

  The pinned values are written once, in `tests/data/pinned-values.txt`: a `#` header saying
  what each set is and which spec measured it, then one `<set> <value> <name>` line a value. A
  value is a float32 normalized value, or, in a set of displays, a finite double. Each test
  module reads it through `pytestconfig.rootpath` with a reader of a few lines of its own, since
  it is the values, not the parsing, that must not be written twice. A missing file fails each
  test that reads it with the path, and a line that is not a value of a known set with the file
  and the line (ME, MF and MF2 in the sixth review's `verification/mutation.txt`, in both
  modules, the integration module's with Vital). Each reader also fails by name on a set that
  holds no value and on a normalized value outside [0, 1], so a test over an emptied set cannot
  pass by running nothing: the integration module's since issue #16 (MG1 and MG2 in its
  `verification/mutation.txt`), the unit module's since the revision after the review of
  patchbay-vital's PR 19 (MU1 and MU2 in its). That replaced two copies of the values
  held equal by a test reading the integration module's source, whose syntax-tree checks the
  fifth and sixth reviews each found gaps in.

  The test and the probe run one sequence, `initial` loaded before each set. `_held_after_a_set` is
  written once in the test module. The fourth and fifth reviews' probe imported it and the
  pinned values, then constants, and printed them by blob and source, so the test and the probe
  computed the same thing; a probe now reads the values from the file, as the tests do.

  Verified against `tests/integration/test_vital_plugin.py`
  (`test_at_or_below_volume_s_floor_a_set_holds_the_map_s_preset`,
  `test_a_held_power_of_two_set_through_the_host_is_held`,
  `test_an_arbitrary_display_set_through_the_host_holds_the_map_s_preset`,
  `test_a_value_set_through_the_host_is_the_one_the_state_holds`,
  `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`,
  `_held_after_a_set`, `_nearest_quotient`, `_pinned`), `tests/unit/test_parameters.py` (`_pinned`,
  `test_the_pinned_values_file_holds_three_named_sets`), `tests/data/pinned-values.txt`, the
  `verification/plugin-probe.txt` of the revision after PR 14's fourth review
  (`agent-os/specs/2026-11-12-1319-revision-after-pr-14-fourth-review/`), the
  `verification/mutation.txt` of the sixth, and the `verification/plugin-probe.txt` and
  `verification/mutation.txt` of issue #16's spec.

---

## vital/plugin-state

# The hosted plugin

What Vital does when hosted, and how this package holds it to that. A rule here is about Vital
through pedalboard; the general form of a measured third party is `base/testing/tests.md`'s.
Written from `src/patchbay_vital/state.py` and `host.py`; the evidence is the `verification/` of
the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`):
`probes.txt`, `host-probes.txt`, `float-environment.txt` and `probes-first-attempt.txt`; of its
revision after PR 9's CI run (`agent-os/specs/2026-11-10-0738-revision-after-pr-9-ci/`):
`linux-gate-run.txt` and `old-behaviour.txt`; of the revision after the review of PR 9
(`agent-os/specs/2026-11-10-1027-revision-after-pr-9-review/`), whose `shape.md` records the
reading of pedalboard 0.9.26's wrappers and its `old-behaviour.txt` the findings' tests failing on
the code as reviewed; of the revision after the second review
(`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`), whose `old-behaviour.txt`
does the same for its findings; of the revision after the third review
(`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`): `restore-probe.txt` and
`old-behaviour.txt`; and of the spec of issue #13
(`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`), the revisions after PR
14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
`agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`) and the spec of issue #15
(`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`): `plugin-probe.txt`; and of
the spec of issue #8 (`agent-os/specs/2026-11-15-1448-the-instrument/`): `probes.txt` and
`probes-2.txt`.

## The state

- **The plugin's state is a preset's text in three containers, read and written by our own codec**:
  a `.vstpreset` (`VST3`, class id, `Comp` and empty `Cont`), JUCE's `VstW` header, and a VST2
  `CcnK`/`FBCh` bank of one chunk holding the JSON, exactly as a `.vital` file writes it, then 17 NUL
  bytes and `JUCEPrivateData`. Every field is kept as read, so `wrap(unwrap(x)) == x`; anything else
  is `PluginStateError` naming the layer, a negative chunk size and a text that nests too deeply to
  read among them, the decoder's `RecursionError` turned into `ValueError` by `preset.decode_end`,
  the one place in the package that does it, so no built-in leaves the codec. Written from the
  bytes, not from any program's source. Verified against `state.py`, `tests/unit/test_state.py`
  (`test_wrap_reverses_unwrap`, `test_the_layers_are_where_the_plugin_put_them`,
  `test_each_layer_is_refused_by_name`, `test_a_text_that_is_not_one_object_is_refused`) and
  `test_the_codec_reads_and_writes_the_plugin_s_own_bytes`.
- **The state's text has one key a file lacks, `tuning`, held like any unread section**, as
  `VitalPreset.tuning`. Verified against `preset.py`, `format.py` and
  `tests/unit/test_format.py` (`test_a_plugin_state_comes_back_byte_for_byte`).
- **The containers around the text are read once, when the plugin loads, and every load reuses
  them.** A load changes the text and no container, so `load_state` reads nothing from the plugin
  first; a plugin whose state the codec cannot read is refused where it loads, `PluginLoadError`
  naming the path, chained. Verified against `host.py` (`__init__`, `load_state`),
  `tests/unit/test_host.py` (`test_a_load_reuses_the_containers_read_when_the_plugin_loaded`,
  `test_a_plugin_whose_state_the_codec_cannot_read_is_refused_at_load`) and
  `tests/integration/test_vital_plugin.py`
  (`test_the_fixture_as_state_reads_back_but_its_sample_delayed` and
  `test_every_installed_preset_loads_as_state`, each holding the containers after a load to the
  ones before it).
- **A preset loaded as state can be complete, routing and media included, but the plugin changes it.**
  It upgrades a preset older than 1.6.4 (keys added, sections re-encoded, floats moved); every load
  delays the embedded sample by 4 samples and re-quantizes it, a 16-bit value moving one step; a
  value off the host's grid snaps once after the host set that parameter. A load of the starting
  state and then, with no set between them, of a state holding `volume` at or below its floor at a
  float32 the scale does not hold, the curve's own for the display, moves that value to the
  normalized path's, while `chorus_feedback`'s off-grid 0.4000000059604645 in the same load is held
  as given: on Vital 1.6.4 through pedalboard 0.9.26 on arm64, at each of the four values of
  `tests/data/pinned-values.txt`'s `volume_floor` set (issue #15's probe transcript prints them as
  `_VOLUME_FLOOR`, the integration module's constant until the revision after PR 14's sixth review
  moved the values to the file), after each of the four histories the probe tried before the first
  load (a fresh instance, the census's sets, a set of each of the two, the measure's own sets). The
  state is written with the package's `dumps`, which gives the starting state's own text back byte
  for byte, so it differs from text Vital wrote only in `volume`'s value, and read with the host's
  `_floats`. It is an observation: nothing measured says why one value moves and the other does
  not, and the test that holds it does not rely on which history precedes it. So the plugin's state
  is never read back as the preset it was given; the instrument keeps the preset it loaded
  (`vital/instrument.md`). Verified against `test_the_fixture_as_state_reads_back_but_its_sample_delayed`,
  `test_every_installed_preset_loads_as_state`, `test_a_routing_only_in_the_preset_text_is_heard`
  and `test_a_load_holds_volume_s_unheld_float32_as_its_neighbour_and_chorus_feedback_as_given`,
  which holds the load's move, and the `verification/plugin-probe.txt` of the revisions after PR
  14's reviews (`agent-os/specs/2026-11-11-1555-revision-after-pr-14-review/` and
  `agent-os/specs/2026-11-11-2044-revision-after-pr-14-second-review/`) and of the spec of issue
  #15 (`agent-os/specs/2026-11-12-0937-map-inverses-land-on-held-presets/`), section 2; first seen
  in issue #13's (`agent-os/specs/2026-11-11-1449-volume-preset-through-the-set-path/`).
- **Vital reports no load it cannot use, and `load_state` raises for none.** Of 20 texts, each
  loaded in a process of its own, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2):
  - 11 never returned. Vital puts up a modal alert and its caller waits for ever, in AppKit's
    `NSAlert runModal` under Vital's `SynthProcessor::setStateInformation`, by a sample of the
    process. A text with no sections does it, and so does one whose fault is inside a section: three
    wavetables whose `groups` is a number.
  - A `synth_version` newer than the plugin's is ignored whole, with no error and the plugin
    unchanged.
  - `wavetables` or `lfos` as an empty array loads the floats and keeps the sections the plugin had.
  - A key the text lacks goes to its default, 132 of 132.

  So a text is judged before the plugin is given it (`vital/instrument.md`, the guard); a load
  that may not return is run only in a process of its own with a time limit, as a transcript; and
  no test sends one. A load that cannot block is issue #20's to make. Verified against
  `probes.txt` sections 5 and 5b, `instrument.py` (`check_loadable`) and
  `test_a_preset_the_plugin_was_seen_not_to_load_whole_is_refused_before_it_is_called`.
- **One load of a text is not enough, and two are: a measured fact, no cause known.** After a set of
  every parameter and a render, on the start preset, the fixture and the 75 installed presets: one
  load leaves 17 to 53 of the 903 floats off the text's on every text, 2,335 in all; two loads leave
  none on 66; a third holds the same 903 as the second on all 77. On a fresh instance with no set
  before it, one load of an older preset leaves floats off too, 7 to 18 on four of six tried. The
  sample's 4-sample delay is counted from the text each time, so two loads of one text hold the
  sample one load does. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). Verified against `probes.txt` sections 6, 9 and 9b and
  `test_one_load_after_a_set_leaves_the_off_grid_floats_off_and_a_second_holds_them`.
- **Vital upgrades a preset older than it as it loads, and no number of loads undoes it.** On 11 of
  the 75 installed presets, versions 0.6.1 to 1.0.0, 46 floats differ from the text's after two
  loads and after three: 29 are keys the text lacks set to other than the default (`chorus_cutoff`
  20 where the default is 60), 3 are `flanger_center` moved into its range, and 14 are floats inside
  their scale renumbered or rescaled (`osc_1_stack_style` 9 held as 10, `filter_1_style` 1 as 0).
  The map is 1.6.4's, so such a float means another setting in the file than in the plugin. Measured
  on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2). What the model
  holds for such a preset is issue #22's to decide. Verified against `probes-2.txt` section 9c,
  `tests/data/upgraded-floats.txt` and
  `test_two_loads_leave_only_what_vital_makes_of_an_older_preset_and_a_third_changes_none`.

## The process

- **Every call into the plugin keeps the process's floating-point environment.** Loading and
  rendering Vital turn on flush-to-zero for the whole process and leave it on, so every subnormal
  after them, in Python and numpy, is zero. `host.py` saves the environment with `fegetenv` before
  each call and restores it with `fesetenv` after, both from the first library that holds them: the
  C library on macOS, the maths library on glibc, whose C library has neither, each name looked up
  only once the one before it is passed over. It refuses to load where no library holds them. Every
  call into the plugin is its own guard, reads included and each read of a loop its own, so the
  Python work between two calls, the JSON a measurement parses among it, runs in the process's
  own environment and never in the one the plugin left: one guard around a loop would hand the
  second call the first's. The load's four calls are four guards too, with nothing in Python
  between them: pedalboard's `parameters` is Python that steps raw values and parses texts between
  its own native calls, and one guard from `VST3Plugin` on would enter it in the flush-to-zero the
  load left. A fake plugin that turns upward rounding on at every call holds both:
  after each public method the rounding mode is back, and no call finds the mode the one before
  it set. Verified against `host.py` (`_c_library`, `_environment_kept`, `_reached`, `_name_of`,
  `_text_for`, `VitalHost.__init__`), pedalboard 0.9.26's `AudioProcessorParameter.__init__` (read
  for the fact), `tests/unit/test_host.py` (`test_every_public_method_gives_the_environment_back`,
  `test_every_call_into_the_plugin_is_entered_in_the_process_s_own_environment`) and
  `test_the_process_keeps_its_floating_point_environment`.
- **The guard is held by unit tests that need no plugin**, so CI, which has no Vital, runs it: the
  lookup on the platform the tests run on, a library without the two functions passed over, and one
  real save and restore that upward rounding set inside it does not survive. A guard proven only
  beside the plugin went untested where the plugin is absent, and failed there. Verified against
  `tests/unit/test_host.py` (`test_the_two_functions_are_found_where_the_tests_run`,
  `test_a_library_without_the_two_functions_is_passed_over`,
  `test_the_environment_comes_back_however_the_block_changed_it`,
  `test_without_the_two_functions_the_host_refuses_to_load`) and the revision's
  `verification/linux-gate-run.txt`.
- **pedalboard's Python parameter wrappers are held, one mapping per host; its native parameter
  objects never are.** A native object held across state loads crashed the process. The wrappers
  pedalboard's public mapping gives fetch the native parameter afresh on every attribute access,
  which is what makes holding them safe, and pedalboard caches them itself while rebuilding the
  mapping on each read of `parameters`, about 3 ms for 903, so the host reads it once. pedalboard
  adds that mapping to its native class at import, which its stubs do not show, so the loaded
  plugin is cast once to a private protocol of what `host.py` uses. Verified against `host.py`
  (`VitalHost.__init__`, `_HostedPlugin`, `_HostedParameter`), pedalboard 0.9.26's
  `AudioProcessorParameter.__getattr__` and `_get_parameters` (read for the fact), and
  `verification/probes-first-attempt.txt`.
- **What pedalboard raises never leaves the host, from any method that reaches it.** A read, a
  value or a state the plugin refuses is `PluginStateError`, a render `PluginRenderError`, each
  chained from pedalboard's `RuntimeError`, `ValueError` or `TypeError`, through the one guard
  every reach goes through; pedalboard's `preset_data` setter raises a bare `RuntimeError` on
  bytes it cannot take. A restore the plugin refuses in a measurement is `PluginStateError` too,
  the read's failure kept in its context chain. Verified against `host.py` (`_PEDALBOARD_ERRORS`,
  `_reached`, every `with _reached(...)`), `test_what_pedalboard_raises_is_the_package_s_error`,
  `test_every_reach_the_plugin_refuses_is_the_package_s_error` and
  `test_a_restore_the_plugin_refuses_is_the_package_s_error_after_the_read_s`.
- **Nor does a built-in's error leave the host.** A normalized value that is no number is
  `ParameterRangeError`, `math.isfinite`'s `TypeError` chained, and a bool is refused by name, as a
  render's length is, before anything is set; a host id `display_texts` does not host is
  `UnknownParameterError`, core's field a plain string; a state holding no `settings` object is
  `PluginStateError`, its text already one JSON object by the codec's validator. Verified against
  `host.py` (`_normalized`, `display_texts`, `_floats`),
  `test_a_normalized_value_that_is_no_number_is_refused_as_the_package`,
  `test_display_texts_for_a_host_id_not_hosted_is_named` and
  `test_a_state_holding_no_settings_object_is_the_package_s_error`.
- **The plugin is found at the path given, or at `DEFAULT_PATH`, and nowhere else**; nothing there,
  something the host cannot load, or a plugin not named Vital is `PluginLoadError`. Verified against
  `tests/unit/test_host.py`.
- **The map is used only on the machine, and with the plugin and version, it was measured
  from.** Its scales are the plugin's build's and its records that version's
  (`vital/parameter-map.md`); the host compares the map's `machine` with `platform.machine()`,
  then its `instrument` and `vital_version` with what the plugin reports, and raises one
  `MapMismatchError` naming the first that differs, its value in the map and the one found, at the
  first method that needs the map, never at load or in `measure`, so the census still runs there
  and a new map is the remedy. The map's `host`, pedalboard's version, is provenance and is not
  compared: the scales are the plugin's. Verified against `host.py` (`_parameter_map`),
  `errors.py` (`MapMismatchError`),
  `test_the_map_is_refused_on_another_machine_where_it_is_first_used` and
  `test_the_map_is_refused_on_another_vital_version_where_it_is_first_used`.
- **A measurement puts each parameter back and loads the starting state once, however its reads
  end.** Each parameter's grid is under a `try/finally` that sets it back to the normalized value it
  had, so the next is measured from the starting state; that is exact but for a float32 step on 22
  of 1.6.4's 903 (`env_1_decay_power` -2.0 comes back -2.0000005), the normalized value not
  reaching every preset value. The whole loop is under a `try/finally` that loads the starting
  state once, which puts those 22 back exactly and, as every load does, delays the sample by 4
  samples: a load after every parameter was 903 loads, 20.9 s a census against 14.4 s. A grid row
  holding other float keys than the starting state's is `CensusError` naming the parameter before
  any key is indexed. Verified against `host.py` (`measure`, `_moving_key`),
  `verification/restore-probe.txt`,
  `test_a_measurement_restores_the_state_however_it_ends`,
  `test_a_measurement_puts_each_parameter_back_and_loads_the_state_once`,
  `test_a_parameter_that_changes_the_preset_s_keys_is_named` and
  `test_the_census_regenerates_the_three_committed_files`.

## A render

- **A render asks pedalboard for one sample more than it wants and returns the first `samples`**,
  contiguous, pedalboard returning `int(duration · rate)` samples; fewer than asked, or another
  shape, is `PluginRenderError`, as is a length or a rate that is not a positive whole number, a
  bool included, refused before the plugin is called. A MIDI time is seconds from the render's
  start. Verified against `host.py` (`render`, `_whole`), `tests/unit/test_host.py`
  (`test_a_render_is_the_first_samples_asked_for_in_one_block`,
  `test_a_render_length_or_rate_that_is_not_a_positive_whole_number_is_refused`),
  `test_a_render_is_the_length_asked_for_and_finite` and
  `test_a_note_sounds_from_its_time_and_not_before`.
- **A render with no MIDI holds the preset's own sound, not a fixed transient.** On Vital's own
  starting state and on the start preset it is a transient that peaks near 0.02 and whose last
  non-zero sample is 4,889 at most. On the 75 installed presets the largest peak is 2.1, the
  plugin's ceiling: one reaches full scale as loaded and 17 with `volume` at its maximum, 51 peak
  above 0.02, and 32 stay at or above 0.001 for a second or more. It recurs at every render, and it
  is larger with the reset the host makes and not absent without it: Plucked String peaks at 0.21
  with one and 0.012 without. The host spec measured the starting state alone and called it a
  transient of 0.022. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro,
  macOS 26.6.2). A render that does not open so is issue #21's to make. Verified against
  `probes.txt` sections 4 and 4b,
  `test_a_render_of_no_notes_on_the_start_preset_is_its_small_transient_and_no_warning` and
  `test_a_render_of_no_notes_on_an_installed_preset_opens_with_the_preset_sounding`, which holds
  today's behaviour by name.
- **A MIDI time lands one sample early on some samples; half a sample past lands on the sample.**
  The time of sample n itself, n over the rate, lands on n - 1 at 100,003, 1,000,003 and 4,000,001
  at 48 kHz and on 4 of 120 drawn; `(n + 0.5) / rate` lands on n at every value tried, five past 12
  million among them. A sample, not a count; a model that holds the time as a float32 predicted
  misses that did not happen. Measured on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4
  Pro, macOS 26.6.2). Verified against `probes.txt` section 1, `midi.py` and
  `test_a_note_lands_on_the_sample_core_s_rule_gives_it`.
- **Vital gives samples past full scale, up to 2.1, and 2 ** 24 samples in one render,** every one
  finite, in 1.3 s, on Vital 1.6.4 through pedalboard 0.9.26 on arm64 (Apple M4 Pro, macOS 26.6.2).
  Verified against `probes.txt` sections 2 and 3,
  `test_a_render_that_clips_carries_one_warning_and_the_event_carries_it` and
  `test_the_longest_render_is_given_and_one_sample_more_is_refused`.
- **Each integration module loads Vital once**, about two seconds a load. In `test_vital_plugin.py`
  a function-scoped fixture loads the initial state's text before each test, the sample's 4-sample
  delay on a load being nothing a test there depends on. In `test_vital_instrument.py` each test
  builds a new instrument, which loads the start preset twice, so the plugin holds the start's 903
  floats whatever the test before it set. Where the map was measured on another machine each module
  skips by name (`vital/preset-tests.md`). Verified against `tests/integration/test_vital_plugin.py`
  (`vital`, `initial`, `host`), `tests/integration/test_vital_instrument.py` (`vital`, `instrument`)
  and `test_the_next_instrument_starts_clean`.

---

## vital/preset-file

# The preset file

What a `.vital` file holds and how this package holds it. A rule here is about Vital's file; what
any adapter's models do is `base/python/models.md`'s. Written from `src/patchbay_vital/preset.py` and
`format.py`; the evidence is the `verification/discovery.md` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), measured over 75 installed presets and two
saves from Vital 1.6.4, for the plugin state's `tuning` and the derived key list the
`verification/` of the spec of issue #7 (`agent-os/specs/2026-11-09-1907-the-host-and-the-parameter-map/`),
and for the files module the revisions after PR 9's three reviews, the second at
`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/` and the third at
`agent-os/specs/2026-11-10-1438-revision-after-pr-9-third-review/`.

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
  silently, and a key it drops stays known: the census refuses to forget it, and a spec adds it to
  the keys only presets hold. The list is deliberately plain and is derived from the parameter map:
  its keys but the per-slot ones, and the keys only presets hold (`vital/parameter-map.md`).
  Verified against
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
  byte-for-byte; re-encoding parsed JSON is not. A section is checked to be one JSON value and
  nothing after it; one that nests too deeply to read is refused through `preset.decode_end`,
  the one place the decoder's `RecursionError` becomes `ValueError`, which the plugin state's
  codec uses too. Verified against `format.py`, `preset.py` (`_json_section`, `decode_end`),
  `tests/unit/test_preset.py` (`test_a_section_that_nests_too_deeply_is_refused_as_the_package`,
  `test_the_decoder_s_end_names_what_nests_too_deeply`) and
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
  through it too, one concern per module (`base/python/layout.md`): `replace_files` stages every
  file's temporary before renaming any, and puts an earlier file back from the bytes it held when
  a later rename fails, so several files change together or not at all. Only a file a later rename
  could force back is read, during staging, so the last is never read and `dump` needs no read
  permission. Once every file is renamed nothing can fail: each directory is flushed once, after
  every rename, as a best effort, so a flush that fails neither undoes a replacement nor reports
  it as failed; a file system that cannot flush a directory (EINVAL, ENOTSUP, EOPNOTSUPP, EBADF) is
  passed over, and any other failure, the files replaced but maybe not durable, is logged as a
  warning through the module's logger naming the directory and the errno, never raised and never
  silent. Verified against `files.py`, `format.py` (`dump`), `tests/unit/test_files.py`
  (`test_a_failed_write_leaves_the_file_as_it_was_and_no_temporary`,
  `test_writing_over_a_file_keeps_its_permissions`, `test_writing_through_a_symlink_keeps_the_link`,
  `test_several_files_are_staged_before_any_is_renamed`,
  `test_a_rename_failing_after_an_earlier_one_puts_the_earlier_file_back`,
  `test_a_file_that_did_not_exist_is_removed_again_when_a_later_rename_fails`,
  `test_every_directory_is_synced_once_after_every_rename`,
  `test_a_directory_that_cannot_be_synced_leaves_every_file_replaced`,
  `test_only_a_file_a_later_rename_could_force_back_is_read`,
  `test_a_file_that_cannot_be_read_is_still_replaced`).
- **Two presets are the same when they write the same bytes**, so `diff` tells `0.0` from `-0.0`,
  which compare equal. Verified against `format.py` (`_same`) and
  `test_a_diff_is_empty_exactly_when_the_presets_write_the_same`.

---

## vital/preset-tests

# Testing against Vital's presets

What this repository's tests may hold of Vital's and how they read the rest. The general form, a
test over an instrument's installed content, is proposed upstream; what is here is the part about
Vital. Written from `tests/integration/test_factory_round_trip.py`, `test_vital_plugin.py` and
`tests/data/`; the evidence
is the `verification/probes.txt` of the spec of issue #2
(`agent-os/specs/2026-11-09-1509-the-vital-format/`), for the skip on another machine the
revision after the second review of PR 9 (`agent-os/specs/2026-11-10-1307-revision-after-pr-9-second-review/`),
and for the start preset and the instrument's tests the spec of issue #8
(`agent-os/specs/2026-11-15-1448-the-instrument/`).

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
- **The preset the package ships is Vital's default values with media of the package's own.**
  `src/patchbay_vital/data/start.vital` holds each parameter's default, which the parameter map
  ships already as an interoperability fact, and a wavetable, LFO and warp shapes and a sample each
  generated from a formula, none of them Vital's. A test rebuilds every section from its formula, so
  the file cannot come to hold anything else. Shipping it is the owner's licence call of 2026-11-15,
  not legal advice, revisited before any release. Verified against `src/patchbay_vital/start.py` and
  `tests/unit/test_start.py`.
- **A count measured over the installed presets may be committed; a preset may not.**
  `tests/data/upgraded-floats.txt` holds 46 floats by preset name and key, what Vital makes of 11
  older presets as it loads them, and no preset's content beyond those floats. Its header says what
  was measured, on which Vital, host and machine, and its reader fails by name on a line that is not
  one. Committing it, preset names, keys and 46 measured values and no preset's content, is the
  owner's call of 2026-11-16, not legal advice, recorded here beside the manifest and the start
  preset and revisited before any release to PyPI. Verified against
  `tests/integration/test_vital_instrument.py` (`_upgraded`,
  `test_what_the_data_file_of_upgraded_floats_holds`).
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
  `test_the_fixture_as_state_reads_back_but_its_sample_delayed`),
  `tests/integration/test_vital_instrument.py` (the `vital` fixture) and
  `src/patchbay_vital/data/parameters.json`.
- **No test gives Vital a text it may not return from.** Vital answers a preset it cannot read with
  a modal alert and never returns (`vital/plugin-state.md`), so every load a test sends passes the
  instrument's guard first, and a load that blocks is run only in a transcript, in a process of its
  own with a time limit. A test that hung would hang the gate. Verified against
  `tests/integration/test_vital_instrument.py`, whose loads go through `load_patch`, the
  instrument's construction or a text `check_loadable` passed, and `probes.txt` section 5 of the
  spec of issue #8.

---

## base/testing/tests

# Tests

How a test in a patchbay package is written and where it lives, and how the contract suite, the
tests every implementation of a package's protocol runs, is written and proven. Every rule names the
file of a consuming project it is verified against, the test that holds it and the probe a rule
about a tool's behaviour rests on. Written from fromtheoutfit/patchbay at `7471387`, the merge of
its PR 11, whose contracts spec and that spec's revision record each choice as a Decision; the
evidence is in the `verification/` of the spec of issue #21 in `patchbay-standards` and of its
revision after the review of PR 25, patchbay's own probes cited by name and the ones those specs
added by letter. The toolchain spec of issue #4 deferred its test-file rules here.

pytest's and hypothesis's configuration, the `"tests/**"` per-file ignores and mypy's `files` are
`base/python/toolchain.md`'s. Where the `testing` subpackage lives is `base/python/layout.md`'s.

## Test files

- **The tests mirror the source, one test module per module**: `src/<package>/<module>.py` is
  tested by `tests/unit/test_<module>.py`, and `src/<package>/testing/<module>.py` by
  `tests/unit/testing/test_<module>.py`. Two named exceptions: the root `__init__.py` is tested by
  `test_package.py`, its surface and its distribution's metadata, and `test_version.py`, its
  version; `testing/__init__.py`, which holds re-exports alone, has no test module. No two modules
  of the package share a basename (`base/python/layout.md`), so the mirror never gives two test
  modules one name. Verified against `src/patchbay/` and `tests/unit/`.
- **Every module under `tests/` has a basename no other module there has, `conftest.py` included,
  and `tests/` has no `__init__.py`**: `tests/` is a tree pytest collects from `testpaths`, not a
  package, and mypy, given `src` and `tests`, refuses two modules of one name as a duplicate, two
  test files or two `conftest.py` alike, though pytest loads both of the latter. Verified against
  `tests/unit/`, the comment on INP001 in `pyproject.toml`'s per-file ignores, and the gate's mypy
  step; probes n and q.
- **`tests/` holds one `conftest.py` at most, in the directory that holds every test taking its
  fixtures**, the fixtures function-scoped so every test starts fresh: a second is a duplicate
  module to mypy (above). patchbay's is `tests/unit/testing/conftest.py`, whose `bus` and
  `instrument` the contract tests and the fake's tests both take, and there is no other. Verified
  against `tests/unit/testing/conftest.py`, `tests/unit/testing/test_contract_tests.py` and
  `tests/unit/testing/test_fake.py`; probe q.

## Inside a test

- **A test reads the repository's files from pytest's root**, `pytestconfig.rootpath`, the
  directory pytest took its own configuration from, never a path counted up from the test file.
  Verified against `tests/unit/test_version.py` (`test_version_matches_pyproject`).
- **A property test's strategy generates only inputs the property holds of, and a known
  counterexample is pinned with `@example`**, so it is tried on every run, not only when the search
  finds it. Verified against `tests/unit/test_version.py`
  (`test_release_pattern_rejects_a_non_numeric_segment`, its strategy filtered and its `@example`
  the Arabic-Indic ten) and `tests/unit/test_models.py` (`_FINITE`).
- **A pattern a value is held to spells its digits `[0-9]`, never `\d`**, which matches any Unicode
  decimal digit, ARABIC-INDIC DIGIT ONE among them; and a character ruff finds confusable is
  written as its escape, as RUF001 (in a string) and RUF003 (in a comment) ask, the rules kept:
  each reports the character itself and neither its escape. Verified against
  `tests/unit/test_version.py` (`_RELEASE` and its comment); probes f (o1), o (the character) and
  p (its escape).
- **A test that holds a refusal mypy must keep making carries a coded `# type: ignore[<code>]` on
  the refused line**, and strict's `warn_unused_ignores` fails the gate the day mypy stops refusing
  and the ignore suppresses nothing (`base/python/toolchain.md`, "mypy"). patchbay's tests hold six:
  a `PresetKey` where a `ParameterId` is expected (`arg-type`); `issubclass` of `Instrument`
  (`misc`); an assignment to a frozen model (`misc`); an assignment to a frozen event (`misc`); an
  item assigned into a `Patch`'s mapping (`index`); and a subscription of types mypy refuses
  (`call-overload`). Verified
  against `tests/unit/test_models.py` (`test_a_preset_key_is_not_a_parameter_id`,
  `test_a_frozen_model_is_unchanged_by_a_refused_assignment`, `test_a_patch_s_mappings_are_read_only`),
  `tests/unit/test_contracts.py` (`test_issubclass_is_refused_for_a_protocol_with_a_data_member`)
  and `tests/unit/test_events.py` (`test_an_event_is_frozen`, `_subscribe_unchecked`); probe c.

## The contract suite

- **The contract tests ship in the package that defines the protocol, in its `testing`
  subpackage, as plain functions `<property>(instrument, bus) -> None`**, taking an instrument that
  publishes on `bus`, both fresh for the test, and listed once in one tuple a consumer
  parametrizes over: patchbay's `CONTRACT_TESTS`, typed `tuple[ContractTest, ...]`, run as
  `@pytest.mark.parametrize("contract_test", CONTRACT_TESTS, ids=lambda test: test.__name__)`.
  Verified against `src/patchbay/testing/contract_tests.py` and
  `tests/unit/testing/test_contract_tests.py` (`test_contract`).
- **No contract test's name starts with `test_`**, so pytest never collects one a consumer imports
  by name: it runs from the tuple, once. Each docstring is imperative, "Check that ...", as ruff's
  D401 asks once the prefix that waived it is gone. Verified against
  `src/patchbay/testing/contract_tests.py` and `tests/unit/testing/test_contract_tests.py`
  (`test_the_contract_tests_are_never_collected_by_pytest`); probes e and b.
- **A contract test fails with an `AssertionError` subclass carrying fields**, patchbay's
  `ContractViolationError(test, expected, actual)`, its message built from them
  (`base/python/errors.md`): a failed assertion to pytest. It never uses `assert`, which
  `python -O` strips, and never imports pytest, a development dependency an installed package
  cannot count on. An exception the test does not expect propagates as itself. Verified against
  `src/patchbay/testing/contract_tests.py`, `src/patchbay/testing/__init__.py` and
  `tests/unit/testing/test_contract_tests.py`
  (`test_a_contract_violation_is_an_assertion_error_with_fields`); probe d.
- **Each contract test works out what it expects from the instrument's parameters and the contract
  alone**, never from an implementation's code. Values are set at a parameter's bounds, so an
  instrument that stores what it is given gets back exactly that; a value past a bound is the next
  float beyond it, `math.nextafter`, since at 2**53 and at the largest float `bound + 1.0` is the
  bound itself, and a bound with no finite float beyond it gets no candidate there. A ratio's
  candidates stay in `[0, 1]`, and a choice or a boolean adds `minimum + 0.5`. Verified against
  `src/patchbay/testing/contract_tests.py` (`_other_value`, `_out_of_range`) and
  `tests/unit/testing/test_contract_tests.py`
  (`test_a_correct_instrument_with_the_widest_bounds_passes`); probes f (f1) and `mutations.py`.
- **Each contract test is proven by the reference implementation broken its way**, and the proof
  asserts the reason the test gives, not only that it fails: the violation names the test, and its
  `expected` starts with the reason. A test holds the table of broken implementations to the
  suite, each contract test once and nothing else. Verified against
  `tests/unit/testing/test_contract_tests.py` (`test_every_contract_test_has_a_broken_fake`,
  `test_each_contract_test_catches_its_broken_fake`).
- **A correct implementation at the edges passes every contract test**: patchbay's reference fake,
  widened through its `parameters()` with one parameter up to 2**53 and one over every finite
  float. Put back to the arithmetic it replaced, `bound + 1.0`, two contract tests fail it with "no
  exception". Verified against `tests/unit/testing/test_contract_tests.py` (`_WideRange`,
  `test_a_correct_instrument_with_the_widest_bounds_passes`); probe `mutations.py`.
- **The suite holds the protocol's promises, a refusal's among them**: a call the instrument
  refuses changes nothing and publishes nothing; a call it carries out publishes its event once; a
  patch bad only at its last entry in key order is refused whole, changing and publishing nothing,
  which catches an implementation that loads one value at a time; and a render no implementation
  could produce raises the package's render error, never a built-in exception or exhausted
  memory. Verified against `src/patchbay/testing/contract_tests.py`
  (`a_patch_refused_part_way_changes_nothing`, `an_impossible_render_raises_render_failed`, and
  the eleven beside them) and `tests/unit/testing/test_contract_tests.py` (`_LoadsUntilARefusal`,
  `_RendersAnyLength`).
- **The suite runs with function-scoped `bus` and `instrument` fixtures in the `conftest.py` beside
  the tests that run it**, the instrument built on the bus, and runs unchanged against whatever
  instrument the fixture returns. Verified against `tests/unit/testing/conftest.py` and
  `tests/unit/testing/test_contract_tests.py` (`test_contract`).

## In this repository

This repository has no package, so this standard does not apply here; Step 5b of its `shape-spec.md`
leaves it out.

## In a consuming project

Synced in as `agent-os/standards/base/testing/tests.md`, its rules the project's, verified against
the project's own files; Step 5b surfaces it from the index for a spec that writes or changes a
test.

---

## base/python/events

# Events

What a patchbay package has done, it says after doing it, as an event published on a bus. This
standard says what an event is, how the bus delivers it, and what a subscriber and a subscription
are. Every rule names the file of a consuming project it is verified against, the test that holds it
and the probe a rule about a tool's behaviour rests on. Written from fromtheoutfit/patchbay at
`7471387`, the merge of its PR 11, whose contracts spec and that spec's revision record each choice
as a Decision; the evidence is in the `verification/` of the spec of issue #21 in
`patchbay-standards` and of its revision after the review of PR 25, patchbay's own probes cited by
name and the ones those specs added by letter.

An event is a model, and every rule of `base/python/models.md` holds of it; where `Subscriber`
lives, beside the bus, is `base/python/layout.md`'s; the errors the bus raises are
`base/python/errors.md`'s.

## The event

- **An event is a frozen model on the package's base**, `Event`, every event type its subclass with
  `frozen=True` on its class line. Its payload is typed fields on its own class, never a dict.
  Beside the payload every event carries `name`, `version` (the payload's shape, `1` or more, so a
  subscriber can tell a later shape), `at`, `source` (what built it) and `correlation_id` (the
  call it belongs to), the last two non-empty. Verified against `src/patchbay/events.py` and
  `tests/unit/test_events.py` (`test_each_event_names_itself_in_past_tense_dotted_form`,
  `test_an_event_says_where_it_came_from`, `test_an_event_is_frozen`,
  `test_an_event_round_trips_through_json`).
- **An event's name is dotted lowercase words, in the past tense, fixed per class by a `Literal`
  default**: `parameter.changed`, `patch.loaded`, `render.completed`. Two words or more, each a
  lowercase letter then letters, digits or underscores; a class cannot be built under another
  name. The shape is validated; the tense is the reviewer's to hold, no check reading it. Verified
  against `src/patchbay/events.py` (`_NAME`, each subclass's `name`) and `tests/unit/test_events.py`
  (`test_an_event_s_name_is_fixed_by_its_class`, `test_an_event_s_name_is_dotted_lowercase_words`,
  `test_a_name_with_digits_and_underscores_is_an_event_s_name`).
- **An event is stamped with the UTC time it was built**, `at` defaulting to `datetime.now(UTC)`.
  A time given for `at` is judged by its zone's answer for no particular instant,
  `tzinfo.utcoffset(None) == timedelta(0)`, not by its offset at the time given, and is held as
  `datetime.UTC` at the same instant, so a time read back from JSON, whose zone pydantic parses as
  its own, is held the same way. UTC, `timezone.utc`, `ZoneInfo("UTC")` and pydantic's parsed `Z`
  answer zero and are accepted. A naive time is refused, and so are a fixed zone at another offset
  and a zone whose offset changes, such as Europe/London, which answers `None`, in every season:
  whether an event is valid never depends on when it was built. The check reads the zone's answer
  and not every instant's offset, so a `tzinfo` that answers zero for no instant and another offset
  at a real one is accepted, and converted at that instant's offset. Verified against
  `src/patchbay/events.py` (`_in_utc`) and `tests/unit/test_events.py`
  (`test_an_event_is_stamped_in_utc_when_built`, `test_an_event_s_time_is_refused_unless_utc`, its
  London cases in January and July, `test_a_time_in_utc_is_held_as_datetime_utc`,
  `test_an_event_round_trips_through_json`); probes `footing.py` C and r.

## The bus

- **The bus is synchronous and in-process**: `publish` calls every subscriber whose type the event
  is, in the order they subscribed, and returns once all have run. It never alters an event: each
  subscriber receives the very object published. Verified against `src/patchbay/events.py`
  (`EventBus`) and `tests/unit/test_events.py`
  (`test_publish_delivers_to_every_subscriber_once_in_subscription_order`,
  `test_subscribe_by_type_receives_only_that_type`, `test_subscribe_to_the_base_event_is_every_event`,
  `test_publish_with_no_subscribers_does_nothing`).
- **A publish delivers over a snapshot of the subscriptions it began with**, so a subscription
  made or cancelled during a publish takes effect from the next event. Verified against
  `src/patchbay/events.py` and `tests/unit/test_events.py`
  (`test_a_subscriber_added_during_a_publish_starts_with_the_next_event`,
  `test_a_cancel_during_a_publish_takes_effect_from_the_next_event`).
- **A subscriber that raises hides the event from no other.** The bus runs every subscriber, then
  raises one error carrying each failure in the order raised, chained from the first: patchbay's
  `SubscriberFailedError(event_name, exceptions)`. It catches `Exception` only, under the one
  coded `# noqa: BLE001` with its reason beside it (`base/python/toolchain.md`, "ruff"): a
  `BaseException` that is not an `Exception`, `KeyboardInterrupt` and its kind, stops delivery where
  it is raised. Verified against `src/patchbay/events.py` (`_deliver`) and
  `tests/unit/test_events.py` (`test_a_failing_subscriber_hides_the_event_from_no_other`,
  `test_a_base_exception_stops_delivery_where_it_is_raised`); probe b.

## Subscribing

- **`subscribe` refuses a bad subscription where it is made**: an event type that is neither
  `None`, for every event, nor a subclass of `Event`, and a subscriber that cannot be called, each
  raise the package's error, patchbay's `SubscriptionRejectedError`, with nothing subscribed. A
  bad subscription then fails once, where it is made, and not at every publish after it. The
  types already say so to mypy; the check says so to a caller mypy never saw. Verified against
  `src/patchbay/events.py` and `tests/unit/test_events.py`
  (`test_a_bad_subscription_is_refused_where_it_is_made`).
- **`subscribe` returns a `Subscription`**, which says what it delivers and to whom:
  - `cancel()` ends it from the next event, and a second `cancel()` does nothing;
  - it is a context manager that cancels on leaving the block, whether the block returned or
    raised, and what the block raised goes on;
  - the bus drops a cancelled subscription, so it holds the subscriber no longer and the
    subscriber can be collected;
  - each `subscribe` is a subscription of its own, so one subscriber subscribed twice receives
    twice and is cancelled one subscription at a time.

  Verified against `src/patchbay/events.py` (`Subscription`, `EventBus._remove`) and
  `tests/unit/test_events.py` (`test_a_subscription_says_what_it_delivers_and_to_whom`,
  `test_cancel_ends_delivery_and_a_second_cancel_does_nothing`,
  `test_a_subscription_is_a_context_manager_that_cancels_on_exit`,
  `test_a_cancelled_subscriber_is_no_longer_held_by_the_bus`,
  `test_each_subscribe_is_its_own_subscription`).
- **The subscriber protocol is generic and contravariant**: `Subscriber[E: Event]`, a
  `runtime_checkable` protocol whose one member is `__call__(self, event: E, /) -> None`. A
  subscriber for one type takes that type, and a handler of the base event serves for any type:
  mypy accepts `subscribe(ParameterChanged, handler)` for a handler taking a `ParameterChanged` and
  refuses that handler where every event is wanted. The event is positional-only, so a subscriber
  names its parameter as it likes, and any function will do. `subscribe` has two overloads,
  `(type[E], Subscriber[E])` and `(None, Subscriber[Event])`. Verified against
  `src/patchbay/events.py` and `tests/unit/test_events.py` (`test_a_function_is_a_subscriber`);
  probe `typing_probe.py` G, H and I.

## In this repository

This repository has no package, so this standard does not apply here; Step 5b of its `shape-spec.md`
leaves it out.

## In a consuming project

Synced in as `agent-os/standards/base/python/events.md`, its rules the project's, verified against
the project's own files; Step 5b surfaces it from the index for a spec that adds an event or touches
the bus.

---

## base/process/verification-gate

# Verification Gate

The gate is the definition of done in every patchbay repository. It is the final task of every spec,
included without asking, whether or not `/agent-os:shape-spec` shaped the work, and a spec is not
complete until every step of it passes. A spec with a red step, a skipped step or an unrecorded
retrospective is unfinished work, however small the change; a one-file fix is exactly the kind of
work that quietly invents a pattern, so the gate runs on it too.

This standard fixes the shape of the gate: what every repository's gate does and in what order.
The runnable step list is each repository's own, named in its `scripts/gate.sh` and in the gate
task of its `shape-spec.md`; this standard names no step and no tool. A consuming project's tool
steps, and the order they run in, are `base/python/toolchain.md`'s.

## One script

- **`scripts/gate.sh` runs every runnable step, in a fixed order, as one command**, and exits 1
  at the first step that fails, after a line on stderr naming the step and its reason,
  `FAIL  step N/M: <reason>`, whatever status the tool returned. Later steps do not run: a failing
  step 1 is reported before step 2 has a chance to pass, so a green run means every step ran and
  every step passed. The script takes no argument; any argument is usage, the usage line on stderr
  and exit 2 with no step run, and a script that cannot enter the repository root says so on
  stderr and exits 2 likewise. A transcript or a wrapper then has three statuses to tell apart: 0,
  every step passed; 1, a step failed and is named; 2, the script was not run as the gate.
- **Every step reports by name.** Each step prints a numbered banner, and what passed is named
  (`ok   <what>`) or what failed is named with its reason and the offending path; a bare exit code
  is not a report. The script ends by naming the step that follows it, so a reader of the
  transcript knows the run was not the whole gate.
- **A step that installs its pinned tools fails as itself.** The install is checked on its own,
  before any tool checks the tree, with a reason of its own: a lockfile that no longer matches its
  manifest, a manifest or lockfile the runner cannot read, a package that will not build, a runner
  missing from `PATH` or not at its pinned version, a pin that names no published version. A
  failed install is then never reported as the first tool's finding, and each tool's reason is
  about that tool alone. A tool run afterwards under the runner's locked mode repeats a check the
  install has passed.
- **A step that reads files from the tree reads the files git lists**: the tracked files plus the
  untracked ones git does not ignore, at the top of a git work tree that is the repository root.
  An ignored stray such as `.DS_Store` is never seen, and a file a spec adds before it is staged
  is. `find`, and a tool that walks a directory without reading `.gitignore`, see the stray, so a
  local run and CI's clean checkout can disagree. The step takes one of three forms:
  - **It reads git's list**, `git ls-files --cached --others --exclude-standard`, one call for
    both sets unless the step treats them apart, `-z` keeping paths verbatim (a list read by line
    takes `core.quotePath=false`), and checks each path on the disk: a listed path missing from the
    disk, or a symlink to nothing, fails the step by name. That clause binds this form; a tool that
    walks the disk is not asked to see a file that is not there, since an earlier step that lists
    the same files checks each one.
  - **It runs a tool that reads `.gitignore` itself** and is given no path git ignores.
  - **It runs a tool that walks a directory and reads files no list given to it holds back**: the
    step first refuses, by name, any file git ignores there that the tool would read, so its walk
    reads only what git lists. pytest loads the `conftest.py` of every directory it collects from,
    and one at the root, whatever `--ignore` names.
- **The first step makes the forms agree.** It asks git two things and compares no paths: that
  this directory is inside a work tree, `git rev-parse --is-inside-work-tree` printing `true`, and
  that it is the top, `git rev-parse --show-cdup` empty. `--show-cdup` alone prints nothing in
  `.git/` and in a bare repository too, where `--is-inside-work-tree` prints `false`. A path typed
  in another case, or spelled `C:/` rather than `/c/`, names the same directory, and comparing
  `pwd -P` with `--show-toplevel` as strings refuses the real root. A tree whose work-tree top is
  not the repository root, a copy without `.git` inside another repository's work tree or under its
  `.git/` included, fails the step by name: never listed against the outer repository, never a bare
  exit. It then refuses every tracked file a committed `.gitignore` matches under the paths the
  gate's listings read, `git ls-files --cached --ignored --exclude-per-directory=.gitignore --
  <those paths>`, naming each under one FAIL line: a file force-added, or added before its
  pattern, is in git's list though the repository says it is ignored, and a tool that reads
  `.gitignore` itself skips it, so with none every form reads one set of files. Only committed
  `.gitignore` files count, so every clone of a commit gets the same answer: `.git/info/exclude`
  and the global excludes file are the machine's, and a file no step reads never fails the gate.
  The fix is a `!` pattern, or untracking the file; a `!` pattern cannot re-include a file under an
  ignored directory, so the directory's contents are ignored (`dir/*`) rather than the directory.
- **A listing git cannot make fails its step by name.** Each listing is written to a file and git's
  own status checked: `git ls-files -z … > <file>.raw && LC_ALL=C sort -zu <file>.raw > <file>`,
  and the step fails by name when that fails ("git could not list the files under scripts/").
  Neither a pipe nor a process substitution keeps git's status: without `pipefail` a pipe's is the
  last command's, and a process substitution's is lost either way, so a corrupt index otherwise
  reads as an empty listing. `-u` lists each path once, since a path in merge conflict is in the
  index once per stage. The files go in a directory `mktemp -d` makes, checked before it is used and
  removed on exit; a step that cannot make it fails by name.
- **The script runs from the repository root** wherever it is invoked from, and assumes nothing
  the repository does not already provide.

## Pinned

- **A tool's version is pinned exactly, in one place, with the date it was published beside
  it.** In a repository with no package manifest the pin is in the script, one named variable
  per tool, and the tool runs through a runner that executes it without installing it into the
  project. In a repository with a manifest the pin is in the manifest's development dependency
  group, exact, and resolved in the lockfile, and the gate runs every tool under the runner's
  locked mode: a pin edited without re-locking fails the step rather than rewriting the lockfile,
  so the gate writes nothing but ignored files and caches. A type checker or a test runner needs
  the project installed, which a runner that installs nothing cannot give it. The runner is one
  the repository already assumes, and nothing else is installed to run the gate. A pin is bumped
  deliberately, in the gate's own spec, and the gate rerun. The pins are gate files either way: in
  the script, as part of it; in a manifest, the pins of the tools the gate runs and what the
  lockfile resolves for them, while the group's other entries, a test library a feature spec adds
  among them, are the project's.
- **The runner's own version is pinned too.** Where the manifest can pin it and the runner then
  refuses any other version on every command that reads the project's settings, it is pinned
  there, once: a local run and CI use the same runner, and CI reads the version from the manifest,
  as "CI" below says.
  Otherwise CI pins it, through the action's input, and a local run uses the runner on `PATH`.
- **A rule set lives in a versioned config file at the repository root, named in the script, or
  in the manifest's tool sections.** In the second case those sections, with the tool pins above,
  are the gate's, and the rest of the manifest is the project's, changing in any spec; the file's
  header says which is which. Either way a config the tool cannot parse fails the step, and
  the header says which step reads the rule set and that it changes only in the gate's own spec.

## The fixed order

The runnable steps come first, in the order the script runs them. Three judgment steps follow, in
this order, and nothing in the script runs them; the script's closing line names them, and the gate
task of `shape-spec.md` lists them after the runnable steps:

- **Docs**: the documentation the change touches reads true after it. The README, the repository's
  `CLAUDE.md`, the header comments and pointers in the files changed, and every standard that names
  them are read against the shipped change, and what was checked is recorded in the spec's
  `shape.md`.
- **Version**: the change is recorded under `[Unreleased]` in `CHANGELOG.md`, and the version is
  bumped where a repository has one. Recorded in `shape.md`.
- **The standards retrospective**, per `base/process/standards-retrospective.md`: the four
  questions answered against the diff, the answer recorded in the spec's `shape.md` under
  `## Standards Retrospective`. "No changes" is valid; silence is not. It is always last.

A spec whose `shape.md` records the green run but not the three judgment steps has not finished the
gate.

## A failing step is fixed at its cause

- **The cause is fixed and the whole gate rerun from step 1.** A fix that lets the step pass
  without fixing what it reported is not a fix. Skipping the step, loosening the rule set,
  excluding the file it named or editing the script to pass each change a gate file, which the
  section below forbids inside a spec; a suppression comment placed in the file the step named
  loosens the rule for that file alone and is reviewed as the loosening it is.
- **A step that cannot pass on the shipped tree is a defect in the tree**, not a reason to bypass
  the step. The first spec in `patchbay-standards` added the one blank line `README.md` lacked
  after its heading rather than exclude the file; that is the whole of the rule.

## Every step that can fail is proven to fail

- **A step is shown to discriminate by a negative test**: a copy of the tree, broken in one way,
  that must fail that step with the named reason and the expected exit status, with the steps after
  it never reached. A step that has never been seen to fail is not known to check anything.
- **A rule set and a pin are each shown to be read, and the install to fail as itself.** A rule
  set is shown read by three cases: a changed value applied, so the clean tree now fails the
  step, and a value the tool cannot use and a file it cannot parse, each failing the step by name.
  Not every tool refuses a key it does not know: pymarkdown under `--strict-config` takes a
  misspelled key as absent and applies the default, where pytest under `--strict-config` refuses
  one (exit 4). So the changed value, which every tool applies, is what shows the file is read. A
  pin is shown read by a version that cannot install: in a lockfile, a pin edited and the
  lockfile left; in the script, a version never published; for a runner the manifest pins, a
  version that is not the one running. Each fails the install by its own reason before any tool
  runs, and the case where the first tool fails shows the install passing first.
- **The spec that adds or changes a step ships its negative test**, and keeps the transcript in
  that spec's `verification/` folder. The tests are a script in the repository beside the gate's,
  not run by the gate, so a rerun is the same test. They run on a temporary copy outside the
  tree, never on the tree itself, and are rerun whenever the gate's files change, and whenever a
  spec adds, removes or renames a file under a directory the tests copy, since a case can rest on
  what that directory holds.
- **A case states what it rests on.** A case whose expectation depends on what a copied directory
  holds sets the whole of that directory, not a part of it. A case that removed some files from
  its copy of `base/` and wrote an index for the rest went stale when a later spec added a standard
  there, and nobody saw it, since that spec changed no gate file and reran no test. A case that
  needs one named file there stops the harness by name when the file is absent.
- **The harness proves itself as it goes.** Its scratch directory comes from `mktemp -d` under a
  hard failure, is refused when empty or when it lies at or under the repository, and only then is
  the trap that removes it set, so a harness whose `mktemp` failed can remove nothing in the tree.
  A setup step that fails stops the harness by name (exit 2) rather than letting a case fail for
  the wrong reason. Every run names the status it expects and prints the one it got, and a run
  that expects a failure also names the reason its output must hold, the failing line with its
  path where one is printed: a script that gives one status for several reasons cannot otherwise
  be told apart from itself with the guard under test deleted. A run that fails at a step also
  holds its output to no later step's banner, so the steps after it are shown never reached, not
  assumed, and a passing run may name lines its output must hold, in order. The named lines are
  found one by one and say nothing of what else was printed, so a case whose reason is the whole
  of what a step must report also asserts that nothing else is reported: the entries the step
  lists are exactly the ones named. A case that says a line is printed once holds it to an exact
  count. A mismatch of any of these is marked `UNEXPECTED`, and the harness exits 1 at the end
  naming the counts, so a transcript's last line says whether every case behaved and a case that
  passed when it should have failed, or failed for another reason, is never read as a pass.
- **A change to the harness's assertions is shown to discriminate, as a step is.** The proof is a
  copy with the guard under test deleted, or put back as it was, run through the cases that cover
  it, which must come back `UNEXPECTED` with the harness exiting 1; the transcript is kept in the
  spec's `verification/`. An assertion no mutation trips is not known to assert anything.
- **A kept transcript holds one run of the harness and ends on that run's count.** The last line
  says whether every case behaved only while it is that run's: a second run appended after it
  makes the last line the second run's. An earlier run kept as evidence, a failing run before a
  fix, goes in a file of its own.
- **Every spec keeps its green run** as `verification/gate-run.txt` in its spec folder, so the
  claim "gate green" has the transcript beside it. The first line of the transcript gives the date
  and the branch the run was made on, and the run is the last thing done before the work is
  handed over: an edit after the run is not covered by it. A transcript recorded before this rule
  stays as it was recorded.
- **A step that refuses an untracked file by design cannot pass on the tree before the owner
  stages it**, and an agent never stages (`base/process/ownership.md`). This repository's index
  check refuses an untracked file under `base/`, so a spec that adds a standard records two runs
  in `gate-run.txt`: the tree's, which fails that step naming the new file, and a green run on a
  scratch copy of the tree with the file git-added. The hand-over says the owner's `git add` turns
  the tree's run green.

## CI

- **The gate's workflow runs the same script, and checks nothing the script does not.** One
  workflow for the gate, one job, on every pull request and every push to the default branch:
  check out the repository, install the runner the script already assumes and, in a repository
  with a lockfile, the locked toolchain, as a step of its own from the project's directory, then
  run `scripts/gate.sh`. That install is the one the script's own install step makes, so a failure
  there is one the gate would report, met before the gate starts. No linter,
  formatter, matrix or check is configured in it; a step the script does not run is not a gate
  step, and a check CI runs that the script does not is a gate a developer cannot run. A
  repository may have other workflows for other work; this rule is about the gate's. The judgment
  steps are never run by a machine.
- **Every action is pinned to a commit**, the full SHA in `uses:` with the tag it was taken from
  in a comment beside it, and the runner's own version is pinned, so CI runs what the gate was
  proven with: through the action's input, or, where the manifest pins the runner, by the action
  reading it from the manifest in the project's directory, with no input, so the version is
  written once. A failed lookup is loud, not a drift: the action installs its latest runner,
  which the manifest's pin refuses at the locked install, its first command that reads the
  project's settings, unless it is the pinned version. The
  image is a named release, not `latest`. The job has a timeout, keeps no credential in the
  checkout, and caches nothing but what a key that changes with the lockfile holds: the same key
  restores what the same lockfile resolves to, and a changed lockfile misses it, so the cache is
  not a moving part. A repository with no lockfile has nothing to key a cache on and caches
  nothing. A pin is bumped deliberately, in the gate's own spec, and the workflow rerun.
- **The workflow fails when the script fails**, because the script is one `run` step and a `run`
  step that exits non-zero fails the job. Before any push, the spec that adds or changes the
  workflow replays the job's `run` steps, read from the workflow file, on a copy of the tree with
  one script broken, and shows the job stops at that step with its exit status. That proves the
  job's control flow on the toolchain at hand, not the hosted run: the hosted run on the pull
  request is the proof of the workflow itself, and the spec records its run id and conclusion in
  `verification/` once it exists. What the script does on the hosted toolchain is the script's
  own portability, proven by its negative tests.

## The gate's own files change only in their own spec

- **The gate script, every script it runs, the tool pins (in the script, or in a manifest's
  development group with what the lockfile resolves for them), the rule-set config (a file, or a
  manifest's tool sections), the CI workflow and the gate task text in `shape-spec.md` are never
  changed as a side effect of a spec whose feature is something else**, and never from inside a
  retrospective. A gate that rewrites its own terms during the process it governs is what this
  rule exists to prevent.
- **A change to the gate is its own spec**, whose feature is the gate: on its own branch, with the
  owner, carrying the negative test for every step it adds or changes. A finding against a gate
  file made during some other spec is recorded in that spec's retrospective as a proposal and
  waits for the gate's spec.

## In this repository

The runnable steps are three: every shell script under `scripts/` parses, the Markdown files under
`base/` and `README.md` lint clean against the pinned rule set, and `index.yml` lists exactly the
tracked files under `base/`. `scripts/gate.sh` carries the exit contract above (tests e, f and x)
and names the tool, its pin and its config. Steps 1 and 2 read git's list from a temporary file,
each path once, and fail by name when git cannot list or no temporary directory can be made (tests
w and y). Step 1 first refuses a tree whose work-tree top is not the repository root, asked of git
(test w: the copy entered in upper case among it, one under another repository's `.git/` and one
in a bare repository), then every tracked file a committed `.gitignore` matches under `scripts/`,
`base/` and `README.md`, the paths its listings read (test y), then parses a file ending in `.sh`
or starting with a bash shebang; any other file fails the step by name, since only shell scripts
live under `scripts/` (test w). Step 2 passes pymarkdown the `.md` files of its list, since
pymarkdown walks a directory without reading `.gitignore` (test y), and, before pymarkdown
lints, installs the pin as itself: `uvx` missing from `PATH`, or a pin `uvx` cannot install, fails
the step by name, and pymarkdown's own reason is about findings and the rule set it reads (tests z
and e). `uvx` has no form that installs without running, so the install
check runs `pymarkdown version`, which checks nothing in the tree, and a pymarkdown that will not
start fails there by the same reason. This repository has no package manifest, so pymarkdown's
pin is `PYMARKDOWN_VERSION` in the script, with its date, run through `uvx`, and the rule set is
`.pymarkdown.yaml`, shown read by a changed value applied and by an unparsable value and an
unparsable file each refused (test i). `scripts/check-index.sh` is the third step: it runs only in
a git work tree whose top is the repository root, asked of git as step 1 asks it (test m), reads
the tracked list with `git ls-files`, each path once (test h), and fails by name when git cannot
list (test m), refuses an untracked file under `base/` and a tracked one missing from the disk,
sorts every list after its last transform and checks both sorted before `comm`, and holds
`agent-os/standards/index.yml` to be a symlink to `../../index.yml`.
`scripts/gate-negative-tests.sh` holds every negative test, nineteen for the gate's scripts (a to
n but j, with c as c1 to c3, and w, x, y and z), eight for `scripts/sync-standards.sh` (o to v,
`base/process/standards-sync.md`) and the CI replay (j), in the harness shape above, and is parsed
by step 1, not run by the gate.
`.github/workflows/gate.yml` is the gate's workflow, pinned to `actions/checkout` v7.0.1 and
`astral-sh/setup-uv` v10.3.3 by commit and to uv 0.13.7 through setup-uv's input, there being no
manifest to read it from, on `ubuntu-24.04` with a ten-minute timeout, no persisted credential and
no cache, there being no lockfile to key one on; a local run uses the uv on `PATH`. Every spec
folder under `agent-os/specs/` holds its `verification/gate-run.txt`; the spec that built the gate
holds its six negative tests as recorded, the spec that last changed the harness (the revision
after the review of PR 23) holds the current transcripts, j's included, with the mutations that
show its guards covered, and the gate spec (issue #3) holds the hosted runs that proved the
workflow, by id.

`scripts/gate.sh` here and in a consuming project share one skeleton: the `cd` and usage checks,
the `step`, `fail`, `git_list`, `listed`, `fail_list` and `present` helpers, step 1 with its root
guard, its temporary directory and its refusal of a tracked file a `.gitignore` ignores, and the
closing line. They differ only in their step lists, the pins those steps need and the paths each
spells from its root, the refusal's pathspec among them. A spec that changes the skeleton here
records the `diff -u` against a consuming project's `scripts/gate.sh` in its `verification/`, and
the project takes the change in its own gate spec after the sync that brings this standard in; the
revision after the review of PR 23 holds the current diff, against patchbay at `3f910d8`, which
names the hunks patchbay takes.

## In a consuming project

This standard is synced in as `agent-os/standards/base/process/verification-gate.md`. The
project's `scripts/gate.sh` runs its own step list on the skeleton above, with the exit contract
and the same first step: the work-tree top refused unless git says it is the root, a tracked file
a committed `.gitignore` matches refused under the paths its listings read, then every shell
script under `scripts/` parsed as git lists them, a file ending in `.sh` or starting with a bash
shebang, any other file refused by name. Every later step that reads files from the tree reads the
files git lists, in one of the three forms above.
Its `shape-spec.md` lists those steps in the gate task, followed by Docs, Version and the standards
retrospective; its gate workflow runs the script and checks nothing the script does not; its
`CLAUDE.md` names the script as the definition of done. `scripts/sync-standards.sh --check` is one
of its steps, and that script is a gate file the sync itself replaces from the pinned commit, never
a hand edit; its gate workflow checks `patchbay-standards` out beside the project under the
workspace, at the commit in `agent-os/standards/base/.version` by the pin step
`base/process/standards-sync.md` names, and its negative tests stand the sibling up by the fixture
named there.

A consuming project is a uv package, with a manifest and a lockfile, so its gate takes the
manifest's forms above. Its tools are pinned exactly in the `[dependency-groups] dev` section of
`pyproject.toml`, each with its publish date, resolved in `uv.lock` and run as
`uv run --locked <tool>`. The `[tool.*]` sections of `pyproject.toml` are the gate's, holding its
rule set and, in `[tool.uv] required-version`, uv's own pin, and so are the tool pins in
`[dependency-groups] dev` with what `uv.lock` resolves for them; `[project]`, `[build-system]` and
the rest of `[dependency-groups]` are the package's, and the file's header says which is which.
The step that runs the first tool opens with `uv sync --locked`, which installs exactly what
`uv.lock` names and fails the step as the sync, with its own reason, on a stale lockfile, a
manifest or lockfile uv cannot read, a package that will not build or a uv that is not the
required version; the tools after it run under `--locked`. Its gate workflow installs uv with
`astral-sh/setup-uv` pinned by commit, its `working-directory` the project's checkout and no
`version`, so it reads `required-version` from `pyproject.toml` there, with its cache on and
`cache-dependency-glob: uv.lock`; then runs `uv sync --locked` from the project's directory as a
step of its own; then the gate.
