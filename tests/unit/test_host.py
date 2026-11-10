"""What the host does with no plugin needed to show it, so CI, which has no Vital, holds it too.

A path that gives no Vital is refused as the package, by name. The floating-point guard every call
into the plugin goes through is found where the tests run, and gives the environment back however
the block changed it. What the host does with a loaded Vital is
`tests/integration/test_vital_plugin.py`'s.
"""

import ctypes
import ctypes.util
import math
import platform
import types
from pathlib import Path

import pytest

from patchbay_vital import host
from patchbay_vital.errors import PluginLoadError
from patchbay_vital.host import DEFAULT_PATH, VitalHost, _c_library, _environment_kept

_FE_UPWARD = {"x86_64": 0x800, "AMD64": 0x800, "arm64": 0x400000, "aarch64": 0x400000}
"""`FE_UPWARD` from `<fenv.h>` by machine: x86's rounding-control bits, arm64's FPCR RMode bits.

The test shows each takes effect, Python's own addition rounding up under it.
"""


def test_the_default_is_vital_s_own_install_path() -> None:
    """Without a path the host looks where Vital's installer puts it on macOS, and nowhere else."""
    assert Path("/Library/Audio/Plug-Ins/VST3/Vital.vst3") == DEFAULT_PATH


def test_a_path_with_nothing_there_is_named(tmp_path: Path) -> None:
    """Nothing is searched for: a path with nothing at it is refused, saying so."""
    absent = tmp_path / "Vital.vst3"
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(absent)
    assert caught.value.path == str(absent)
    assert "nothing at the path" in caught.value.reason


@pytest.mark.parametrize("make", ["directory", "file"])
def test_a_path_the_host_cannot_load_is_named(tmp_path: Path, make: str) -> None:
    """A bundle with no plugin in it, or a file that is none, is the host's refusal, chained."""
    path = tmp_path / "Nothing.vst3"
    if make == "directory":
        path.mkdir()
    else:
        path.write_text("not a plugin", encoding="utf-8")
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(path)
    assert caught.value.path == str(path)
    assert isinstance(caught.value.__cause__, ImportError)


def test_the_two_functions_are_found_where_the_tests_run() -> None:
    """The guard has a library holding `fegetenv` and `fesetenv` here, whatever the platform.

    On glibc that is the maths library; the C library, which loads, has neither.
    """
    library = _c_library()
    assert library is not None
    assert hasattr(library, "fegetenv")
    assert hasattr(library, "fesetenv")


_BOTH = types.SimpleNamespace(fegetenv=None, fesetenv=None)
_NEITHER = types.SimpleNamespace()


@pytest.mark.parametrize(
    ("found", "libraries", "chosen"),
    [
        # glibc: the C library loads without them, the maths library holds them.
        ({"c": "libc", "m": "libm"}, {"libc": _NEITHER, "libm": _BOTH}, _BOTH),
        # A name that does not load is passed over too, and the UCRT is tried last.
        ({"c": "libc", "m": "libm"}, {"libm": _NEITHER, "ucrtbase": _BOTH}, _BOTH),
        # No library holding both: the host then refuses to load.
        ({"c": "libc"}, {"libc": _NEITHER}, None),
    ],
)
def test_a_library_without_the_two_functions_is_passed_over(
    monkeypatch: pytest.MonkeyPatch,
    found: dict[str, str],
    libraries: dict[str, object],
    chosen: object,
) -> None:
    """The first library that loads and holds both is the one, so the choice shows on any host."""

    def load(name: str) -> object:
        if name not in libraries:
            raise OSError(name)
        return libraries[name]

    monkeypatch.setattr(ctypes.util, "find_library", found.get)
    monkeypatch.setattr(ctypes, "CDLL", load)
    assert _c_library() is chosen


def _added(one: float, tiny: float) -> float:
    """Add at run time, under whatever rounding the process has, where the compiler cannot fold."""
    return one + tiny


def test_the_environment_comes_back_however_the_block_changed_it() -> None:
    """Upward rounding set inside the guard holds there, and is gone once the guard closes.

    The library is the guard's own, so this saves and restores the real environment once, with no
    plugin to change it.
    """
    upward = _FE_UPWARD.get(platform.machine())
    if upward is None:
        pytest.skip(f"no FE_UPWARD known for the machine {platform.machine()!r}")
    library = _c_library()
    assert library is not None
    original = library.fegetround()
    one, tiny = 1.0, 2.0**-60
    try:
        with _environment_kept():
            assert library.fesetround(upward) == 0
            assert _added(one, tiny) == math.nextafter(1.0, 2.0)
        assert library.fegetround() == original
        assert _added(one, tiny) == 1.0
    finally:
        library.fesetround(original)


def test_without_the_two_functions_the_host_refuses_to_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where no library holds them, the host is refused before the plugin is loaded, saying why."""
    monkeypatch.setattr(host, "_LIBC", None)
    with pytest.raises(PluginLoadError) as caught:
        VitalHost(tmp_path)
    assert caught.value.path == str(tmp_path)
    assert "fegetenv and fesetenv" in caught.value.reason
