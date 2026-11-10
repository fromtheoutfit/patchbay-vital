"""Rounding to float32 is IEEE's, and `fma32` gives the value Vital's own build reports."""

import math
import struct
from fractions import Fraction

import numpy as np
import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from patchbay_vital.float32 import fma32, round_to_float32, to_float32

_RECORDED = 2700  # a floor on the vectors: an emptied file must not pass
_PARAMETERS = 252  # the parameters they were measured on (the spec's verification/probes.txt)
_SMALLEST_SUBNORMAL = 2.0**-149
_LARGEST = float(np.finfo(np.float32).max)


def _numpy(value: float) -> float:
    """Narrow a double as numpy does, which rounds correctly; its overflow warning is expected."""
    with np.errstate(over="ignore"):
        return float(np.float32(value))


def _next_up(value: float) -> float:
    """Return the float32 after `value`, infinity after the largest."""
    with np.errstate(over="ignore"):
        return float(np.nextafter(np.float32(value), np.float32(np.inf)))


def _even(value: float) -> bool:
    """Say whether a float32's significand is even."""
    bits: int = struct.unpack(">I", struct.pack(">f", value))[0]
    return bits % 2 == 0


def _float32(token: str) -> float:
    """Read a float32 written as its eight hex digits."""
    value: float = struct.unpack(">f", bytes.fromhex(token))[0]
    return value


def _separately(factor: float, multiplier: float, addend: float) -> float:
    """Compute the sum in float32 with the product rounded first, as an unfused build does."""
    product = np.float32(factor) * np.float32(multiplier)
    return float(np.float32(product) + np.float32(addend))


@given(st.floats(allow_nan=False, allow_infinity=False))
@example(-0.0)  # a Fraction has no negative zero; the sign must survive
@example(_LARGEST)
@example(_LARGEST * (1 + 2.0**-25))  # past the largest by half its step: infinity
@example(-_SMALLEST_SUBNORMAL / 2)  # half the smallest subnormal, a tie to -0.0
@example(_SMALLEST_SUBNORMAL * 1.5)  # a subnormal tie, to the even 2 ** -148
@example(1 + 2.0**-24)  # halfway between 1 and the next float32: to 1, the even one
def test_a_double_rounds_as_numpy_rounds_it(value: float) -> None:
    """For every finite double, the nearest float32 is numpy's, signed zeros and infinities too."""
    ours, theirs = to_float32(value), _numpy(value)
    assert ours == theirs
    assert math.copysign(1.0, ours) == math.copysign(1.0, theirs)


@given(st.floats(width=32, allow_nan=False, allow_infinity=False, min_value=0.0))
@example(1.0)
@example(0.0)
@example(_LARGEST / 2)
def test_a_tie_goes_to_the_even_significand(below: float) -> None:
    """Halfway between two neighbouring float32s rounds to the one whose significand is even."""
    above = _next_up(below)
    if math.isinf(above):
        return
    rounded = round_to_float32((Fraction(below) + Fraction(above)) / 2)
    assert rounded in {below, above}
    assert _even(rounded)


@given(st.floats(width=32, allow_nan=False, allow_infinity=False))
def test_a_float32_is_its_own_rounding(value: float) -> None:
    """A value already a float32 comes back unchanged."""
    assert round_to_float32(Fraction(value)) == value


def test_an_infinity_or_a_nan_is_returned_as_it_is() -> None:
    """Nothing is rounded where there is nothing to round."""
    assert to_float32(math.inf) == math.inf
    assert to_float32(-math.inf) == -math.inf
    assert math.isnan(to_float32(math.nan))


def test_every_recorded_vector_is_the_plugin_s_value(pytestconfig: pytest.Config) -> None:
    """Each line is a parameter's normalized value, span, minimum and the value the plugin reported.

    The vectors are every grid point of the parameters on which a fused and a separately rounded
    multiply-add differ (the spec's verification/probes.txt), so on each parameter the separate
    computation misses at least one: the vectors tell the two apart.
    """
    path = pytestconfig.rootpath / "tests" / "data" / "fma-vectors.txt"
    lines = [line.split() for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) >= _RECORDED
    missed: set[str] = set()
    for key, *tokens in lines:
        factor, multiplier, addend, reported = (_float32(token) for token in tokens)
        assert fma32(factor, multiplier, addend) == reported, key
        if _separately(factor, multiplier, addend) != reported:
            missed.add(key)
    assert len(missed) == len({line[0] for line in lines}) == _PARAMETERS
