"""Every error has one root, carries its fields, and survives being copied or pickled."""

import copy
import pickle

import pytest
from patchbay import (
    ParameterNotFoundError,
    PatchbayError,
    PatchRejectedError,
    RenderFailedError,
    UnitMismatchError,
    ValueOutOfRangeError,
)

from patchbay_vital.errors import (
    CensusError,
    MalformedPresetError,
    MapMismatchError,
    ParameterRangeError,
    ParameterUnitError,
    PatchRefusedError,
    PluginLoadError,
    PluginRenderError,
    PluginStateError,
    PluginThreadError,
    PresetFileError,
    RenderRefusedError,
    UnknownParameterError,
    UnknownSettingError,
    VitalError,
    VitalFormatError,
    VitalHostError,
)

_ERRORS = (
    UnknownSettingError("nope"),
    MalformedPresetError("not JSON"),
    PresetFileError("presets/a.vital", "no such file"),
    PluginLoadError("/nowhere/Vital.vst3", "no such plugin"),
    PluginStateError("no VST3 header"),
    PluginRenderError("6 samples of 7"),
    MapMismatchError("machine", "arm64", "x86_64"),
    PluginThreadError("Thread-1 (work)"),
    UnknownParameterError("nope", "Vital"),
    ParameterRangeError("volume", 0.0, 1.0, 1.5),
    CensusError("Filter 1 Cutoff", "no curve fits"),
    ParameterUnitError("volume", "db", "percent"),
    PatchRefusedError("volume: 7.0 is past its maximum"),
    RenderRefusedError("16777217 samples is past the limit of 16777216"),
)


@pytest.mark.parametrize("error", _ERRORS, ids=lambda error: type(error).__name__)
def test_error_is_under_the_root_and_no_narrower_builtin(error: VitalError) -> None:
    """Every error is under the package's root and patchbay's, and no built-in but Exception."""
    assert isinstance(error, VitalError)
    assert isinstance(error, PatchbayError)
    assert not isinstance(error, ValueError | KeyError | OSError | LookupError)


@pytest.mark.parametrize("error", _ERRORS, ids=lambda error: type(error).__name__)
def test_error_is_rebuilt_from_its_args(error: VitalError) -> None:
    """Copying and pickling call the class with its args, so both give the same error back."""
    for rebuilt in (copy.copy(error), pickle.loads(pickle.dumps(error))):  # noqa: S301 - our own bytes
        assert type(rebuilt) is type(error)
        assert rebuilt.args == error.args
        assert str(rebuilt) == str(error)


def test_each_part_has_its_own_branch() -> None:
    """A preset's failures are format errors and the plugin's host errors, and neither the other."""
    for format_error in _ERRORS[:3]:
        assert isinstance(format_error, VitalFormatError)
        assert not isinstance(format_error, VitalHostError)
    for host_error in _ERRORS[3:8]:
        assert isinstance(host_error, VitalHostError)
        assert not isinstance(host_error, VitalFormatError)


def test_a_protocol_failure_is_core_s_error_too() -> None:
    """A caller holding core's types catches them: the contract tests among such callers."""
    unknown = UnknownParameterError("nope", "Vital")
    assert isinstance(unknown, ParameterNotFoundError)
    assert (unknown.parameter_id, unknown.instrument) == ("nope", "Vital")
    out_of_range = ParameterRangeError("volume", 0.0, 1.0, 1.5)
    assert isinstance(out_of_range, ValueOutOfRangeError)
    fields = (out_of_range.parameter_id, out_of_range.minimum, out_of_range.maximum)
    assert (*fields, out_of_range.given) == ("volume", 0.0, 1.0, 1.5)
    wrong_unit = ParameterUnitError("volume", "db", "percent")
    assert isinstance(wrong_unit, UnitMismatchError)
    assert (wrong_unit.parameter_id, wrong_unit.expected, wrong_unit.given) == (
        "volume",
        "db",
        "percent",
    )
    refused = PatchRefusedError("volume: 7.0 is past its maximum")
    assert isinstance(refused, PatchRejectedError)
    assert refused.reason == "volume: 7.0 is past its maximum"
    no_render = RenderRefusedError("16777217 samples is past the limit of 16777216")
    assert isinstance(no_render, RenderFailedError)
    assert no_render.reason == "16777217 samples is past the limit of 16777216"


def test_a_protocol_failure_says_what_core_s_error_says() -> None:
    """Each takes core's message, so a caller reading either type's text reads the same."""
    assert str(ParameterUnitError("volume", "db", "percent")) == str(
        UnitMismatchError("volume", "db", "percent")
    )
    assert str(PatchRefusedError("no such section")) == str(PatchRejectedError("no such section"))
    assert str(RenderRefusedError("too long")) == str(RenderFailedError("too long"))


def test_fields_are_attributes() -> None:
    """Each error keeps its arguments under their own names."""
    assert UnknownSettingError("nope").key == "nope"
    assert MalformedPresetError("not JSON").reason == "not JSON"
    error = PresetFileError("presets/a.vital", "no such file")
    assert (error.path, error.reason) == ("presets/a.vital", "no such file")
    load = PluginLoadError("/nowhere/Vital.vst3", "no such plugin")
    assert (load.path, load.reason) == ("/nowhere/Vital.vst3", "no such plugin")
    assert PluginStateError("no VST3 header").reason == "no VST3 header"
    assert PluginRenderError("6 samples of 7").reason == "6 samples of 7"
    census = CensusError("Filter 1 Cutoff", "no curve fits")
    assert (census.label, census.reason) == ("Filter 1 Cutoff", "no curve fits")
    mismatch = MapMismatchError("vital_version", "1.6.4", "1.7.0")
    assert (mismatch.what, mismatch.measured, mismatch.found) == ("vital_version", "1.6.4", "1.7.0")
    assert PluginThreadError("Thread-1 (work)").thread == "Thread-1 (work)"


def test_a_load_from_another_thread_is_no_state_error() -> None:
    """It is the host's, and not `PluginStateError`: an instrument answers that with a rollback.

    Nothing was touched when it is raised, so there is nothing to put back.
    """
    error = PluginThreadError("Thread-1 (work)")
    assert isinstance(error, VitalHostError)
    assert not isinstance(error, PluginStateError)
    assert str(error) == "a state is loaded from the main thread only, not from 'Thread-1 (work)'"


def test_a_reason_is_said_after_what_failed() -> None:
    """The three errors that carry a reason alone share one shape: the failure, then the reason."""
    assert str(MalformedPresetError("not JSON")) == "malformed preset: not JSON"
    assert str(PluginStateError("no VST3 header")) == "plugin state: no VST3 header"
    assert str(PluginRenderError("6 samples of 7")) == "plugin render: 6 samples of 7"


@pytest.mark.parametrize("error", _ERRORS, ids=lambda error: type(error).__name__)
def test_message_is_built_from_the_fields(error: VitalError) -> None:
    """A message names what failed, every field that is text in it."""
    for field in error.args:
        if isinstance(field, str):
            assert field in str(error)
