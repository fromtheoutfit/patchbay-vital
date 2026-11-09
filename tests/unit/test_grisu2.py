"""A double is written exactly as nlohmann::json writes it, and reads back as the same double."""

import math
import struct

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from patchbay_vital.errors import MalformedPresetError
from patchbay_vital.grisu2 import format_float

_RECORDED = 500  # a floor on the vectors: an emptied file must not pass


def test_every_recorded_value_is_written_as_nlohmann_wrote_it(pytestconfig: pytest.Config) -> None:
    """The vectors are nlohmann's own output (the spec's verification/probes.txt)."""
    path = pytestconfig.rootpath / "tests" / "data" / "grisu2-vectors.txt"
    vectors = [line.split() for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(vectors) >= _RECORDED
    for bits, token in vectors:
        assert format_float(struct.unpack(">d", bytes.fromhex(bits))[0]) == token


@pytest.mark.parametrize(
    ("value", "token"),
    [
        (0.0, "0.0"),
        (-0.0, "-0.0"),
        (100.0, "100.0"),
        (0.0001, "0.0001"),
        (0.00001, "1e-05"),
        (1.5e-07, "1.5e-07"),
        (123456789012345.0, "123456789012345.0"),
        (1e15, "1e+15"),
        (1e16, "1e+16"),
        (-31.220474243164063, "-31.220474243164063"),  # an exact tie, which repr rounds to even
        (81.632110595703125, "81.63211059570313"),  # another, from a shipped preset
        (0.263106882572174072265625, "0.26310688257217407"),  # one digit longer than the shortest
    ],
)
def test_a_value_is_written_in_nlohmann_s_form(value: float, token: str) -> None:
    """Each of nlohmann's forms: a point, a padded zero, an exponent, a tie, a longer value."""
    assert format_float(value) == token


@given(st.floats(allow_nan=False, allow_infinity=False))
@example(5e-324)
@example(1.7976931348623157e308)
def test_a_written_double_reads_back_the_same(value: float) -> None:
    """Whatever digits Grisu2 chooses, they name the same double, sign of zero included."""
    written = float(format_float(value))
    assert written == value
    assert math.copysign(1.0, written) == math.copysign(1.0, value)


@given(st.floats(allow_nan=False, allow_infinity=False, width=32))
def test_a_written_float32_reads_back_the_same(value: float) -> None:
    """Every value Vital holds is a float32 widened to a double."""
    assert float(format_float(value)) == value


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf], ids=str)
def test_a_value_a_preset_cannot_hold_is_refused(value: float) -> None:
    """NaN and the infinities are refused as the package's error, naming the value."""
    with pytest.raises(MalformedPresetError, match=repr(value)):
        format_float(value)
