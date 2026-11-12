"""Single-precision arithmetic as Vital's own build does it, exactly.

Vital holds a parameter's value as a float32 and turns a normalized value `r` into it as
`r * span + minimum`, which its arm64 build fuses into one multiply-add, rounded once. Where that
and two separately rounded operations differ, the fused value is the one the plugin reports: on
252 parameters of the census's grid, and separate rounding alone matches none (the host spec's
`verification/probes.txt`; Decision 7 of its shape.md). Python 3.12 has no `math.fma`, and a
double computed first and then narrowed rounds twice, so `fma32` computes the exact value as a
`Fraction` and rounds it to the nearest float32 once, ties to even, in integer arithmetic.
`math.fma` replaces it when the package's floor reaches Python 3.13.

A float32 is returned as the Python float that holds it exactly: every float32 is a double.
Rounding follows IEEE 754's round to nearest: a magnitude past the largest float32 by half its
step or more is infinity, and one below the smallest subnormal by more than half of it is zero.
`next_float32` steps from one float32 to the next, on its bits, the one way the package and its
tests step a float32.
"""

import math
import struct
from fractions import Fraction

_MANTISSA_BITS = 24
"""A float32's significand, the leading bit included."""

_MIN_NORMAL_EXPONENT = -126
"""The exponent of the smallest normal float32, 2 ** -126."""

_SUBNORMAL_QUANTUM = _MIN_NORMAL_EXPONENT - (_MANTISSA_BITS - 1)
"""The exponent of the smallest subnormal float32, 2 ** -149, the step below every normal."""

_OVERFLOW = Fraction(2**128)
"""The magnitude a rounded float32 reaches only by overflowing: 2 ** 128 is past the largest."""

_FLOAT32 = struct.Struct("<f")
_BITS = struct.Struct("<I")
"""A float32 and its bits, read through each other to step from one float32 to the next."""


def round_to_float32(value: Fraction) -> float:
    """Return the float32 nearest `value`, ties to the even significand, as a Python float."""
    if value == 0:
        return 0.0
    magnitude = abs(value)
    exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    if Fraction(2) ** exponent > magnitude:
        exponent -= 1
    quantum = max(exponent - (_MANTISSA_BITS - 1), _SUBNORMAL_QUANTUM)
    significand = round(magnitude / Fraction(2) ** quantum)  # Fraction rounds half to even
    if significand * Fraction(2) ** quantum >= _OVERFLOW:
        return math.copysign(math.inf, value)
    return math.copysign(math.ldexp(significand, quantum), value)


def to_float32(value: float) -> float:
    """Return the float32 nearest a double; a zero, an infinity or a NaN is returned as it is.

    A `Fraction` has no negative zero, so a zero keeps its sign by not becoming one.
    """
    if value == 0 or not math.isfinite(value):
        return value
    return round_to_float32(Fraction(value))


def fma32(factor: float, multiplier: float, addend: float) -> float:
    """Return `factor * multiplier + addend` computed exactly and rounded once to float32."""
    return round_to_float32(Fraction(factor) * Fraction(multiplier) + Fraction(addend))


def next_float32(value: float, toward: float) -> float:
    """Return the float32 next to `value` in the direction of `toward`, as C's `nextafterf` does.

    `value` is a float32, as every value the plugin holds is; a double that is not one is first
    rounded to the nearest. `toward` equal to it is returned; from a zero the step is the smallest
    subnormal of `toward`'s sign, and from an infinity the largest float32; a NaN gives a NaN. The
    step is made on the float32's bits, so it is exact.
    """
    start = to_float32(value)
    if math.isnan(start) or math.isnan(toward):
        return math.nan
    if start == toward:
        return toward
    if start == 0:
        return math.copysign(math.ldexp(1.0, _SUBNORMAL_QUANTUM), toward)
    bits: int = _BITS.unpack(_FLOAT32.pack(start))[0]
    bits += 1 if (start < toward) == (start > 0) else -1
    stepped: float = _FLOAT32.unpack(_BITS.pack(bits))[0]
    return stepped
