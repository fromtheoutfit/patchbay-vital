"""A path that gives no Vital is refused as the package, by name, with no plugin needed to show it.

What the host does with a loaded Vital is `tests/integration/test_vital_plugin.py`'s.
"""

from pathlib import Path

import pytest

from patchbay_vital.errors import PluginLoadError
from patchbay_vital.host import DEFAULT_PATH, VitalHost


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
