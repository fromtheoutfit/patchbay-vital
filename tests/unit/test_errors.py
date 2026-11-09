"""Every error has one root, carries its fields, and survives being copied or pickled."""

import copy
import pickle

import pytest
from patchbay import PatchbayError

from patchbay_vital.errors import (
    MalformedPresetError,
    PresetFileError,
    UnknownSettingError,
    VitalFormatError,
)

_ERRORS = (
    UnknownSettingError("nope"),
    MalformedPresetError("not JSON"),
    PresetFileError("presets/a.vital", "no such file"),
)


@pytest.mark.parametrize("error", _ERRORS, ids=lambda error: type(error).__name__)
def test_error_is_a_format_error_and_no_narrower_builtin(error: VitalFormatError) -> None:
    """Every error is under the package's root and patchbay's, and no built-in but Exception."""
    assert isinstance(error, VitalFormatError)
    assert isinstance(error, PatchbayError)
    assert not isinstance(error, ValueError | KeyError | OSError | LookupError)


@pytest.mark.parametrize("error", _ERRORS, ids=lambda error: type(error).__name__)
def test_error_is_rebuilt_from_its_args(error: VitalFormatError) -> None:
    """Copying and pickling call the class with its args, so both give the same error back."""
    for rebuilt in (copy.copy(error), pickle.loads(pickle.dumps(error))):  # noqa: S301 - our own bytes
        assert type(rebuilt) is type(error)
        assert rebuilt.args == error.args
        assert str(rebuilt) == str(error)


def test_fields_are_attributes() -> None:
    """Each error keeps its arguments under their own names."""
    assert UnknownSettingError("nope").key == "nope"
    assert MalformedPresetError("not JSON").reason == "not JSON"
    error = PresetFileError("presets/a.vital", "no such file")
    assert (error.path, error.reason) == ("presets/a.vital", "no such file")


def test_message_is_built_from_the_fields() -> None:
    """A message names what failed."""
    assert "nope" in str(UnknownSettingError("nope"))
    assert "not JSON" in str(MalformedPresetError("not JSON"))
    message = str(PresetFileError("presets/a.vital", "no such file"))
    assert "presets/a.vital" in message
    assert "no such file" in message
