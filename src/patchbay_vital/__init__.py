"""patchbay-vital: the patchbay adapter for Vital.

No adapter code ships yet, so the package holds its version and nothing else. Each module joins it
with the spec that adds it, and this file re-exports what an adapter's consumer uses.

`__version__` is the one in pyproject.toml, read from the installed distribution's metadata so
there is one place it is written. Import the package installed (`uv sync`): from a bare src/ on
sys.path there is no distribution to read, so importlib.metadata raises PackageNotFoundError
rather than the package inventing a version.
"""

import importlib.metadata as _metadata

__version__ = _metadata.version("patchbay-vital")

__all__ = ["__version__"]
