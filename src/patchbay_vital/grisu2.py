"""A double written exactly as nlohmann::json writes it, which is how Vital writes a preset.

Vital serializes a preset with nlohmann::json, whose floats come from the Grisu2 algorithm and a
format of its own. Python's `repr` gives the shortest digits, and Grisu2 does not always: it gives
up one digit of brevity near the edge of a value's rounding interval, and breaks an exact tie the
other way. So a file cannot be written back byte for byte through `repr`. This module is a port of
nlohmann's `detail::to_chars`, checked against the library itself (this spec's
`verification/probes.txt`) and held to its output by `tests/data/grisu2-vectors.txt`.

Ported from include/nlohmann/detail/conversions/to_chars.hpp of nlohmann/json, under this license:

    MIT License

    Copyright (c) 2013-2023 Niels Lohmann

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import math
import struct
from fractions import Fraction

from patchbay_vital.errors import MalformedPresetError

_WORD = 64  # the significand width, in bits, of the algorithm's fixed-point numbers
_ROUND_HALF = 1 << (_WORD - 1)
_WORD_MASK = (1 << _WORD) - 1
_EXPONENT_BITS, _SIGNIFICAND_BITS, _EXPONENT_MASK = 52, 52, 0x7FF
_DENORMAL_EXPONENT, _BIAS = -1074, 1075

# The cached powers of ten: every eighth one from 1e-300 to 1e324, and how one is chosen.
_MIN_DECIMAL, _MAX_DECIMAL, _DECIMAL_STEP = -300, 324, 8
_ALPHA = -60
_LOG10_2_NUMERATOR, _LOG10_2_SHIFT = 78913, 18

# Where the decimal point goes: plain digits for a point between these, an exponent outside them.
_MIN_POINT, _MAX_POINT = -4, 15
_TWO_DIGITS = 10

type _Fp = tuple[int, int]
"""A number as a 64-bit significand and a binary exponent: `f * 2 ** e`."""


def _normalize(f: int, e: int) -> _Fp:
    """Shift a significand left until its top bit is set."""
    shift = _WORD - f.bit_length()
    return f << shift, e - shift


def _power_of_ten(k: int) -> tuple[int, int, int]:
    """Return 10 ** k as a normalized significand rounded to 64 bits, its exponent, and k."""
    value = Fraction(10) ** k
    e = value.numerator.bit_length() - value.denominator.bit_length() - _WORD
    significand = value / Fraction(2) ** e
    while significand >= 1 << _WORD:
        significand /= 2
        e += 1
    while significand < 1 << (_WORD - 1):
        significand *= 2
        e -= 1
    f = round(significand)
    return (1 << (_WORD - 1), e + 1, k) if f == 1 << _WORD else (f, e, k)


_CACHED_POWERS = tuple(
    _power_of_ten(k) for k in range(_MIN_DECIMAL, _MAX_DECIMAL + 1, _DECIMAL_STEP)
)


def _cached_power(e: int) -> tuple[int, int, int]:
    """Return the cached power that scales a number of binary exponent `e` into the window."""
    f = _ALPHA - e - 1
    scaled = abs(f * _LOG10_2_NUMERATOR) >> _LOG10_2_SHIFT
    k = (scaled if f >= 0 else -scaled) + (f > 0)
    return _CACHED_POWERS[(-_MIN_DECIMAL + k + _DECIMAL_STEP - 1) // _DECIMAL_STEP]


def _multiply(x: _Fp, y: _Fp) -> _Fp:
    """Multiply two fixed-point numbers, keeping the top 64 bits, rounded half up."""
    return ((x[0] * y[0] + _ROUND_HALF) >> _WORD) & _WORD_MASK, x[1] + y[1] + _WORD


def _boundaries(value: float) -> tuple[_Fp, _Fp, _Fp]:
    """Return a positive double and the two midpoints to its neighbours, at one exponent."""
    bits = int.from_bytes(struct.pack(">d", value))
    biased = (bits >> _EXPONENT_BITS) & _EXPONENT_MASK
    fraction = bits & ((1 << _SIGNIFICAND_BITS) - 1)
    f, e = (
        (fraction, _DENORMAL_EXPONENT)
        if biased == 0
        else (fraction | (1 << _SIGNIFICAND_BITS), biased - _BIAS)
    )
    upper = _normalize(2 * f + 1, e - 1)
    lower_is_closer = fraction == 0 and biased > 1
    lower_f, lower_e = (4 * f - 1, e - 2) if lower_is_closer else (2 * f - 1, e - 1)
    return _normalize(f, e), (lower_f << (lower_e - upper[1]), upper[1]), upper


def _round_toward_value(digits: list[int], distance: int, delta: int, rest: int, ten: int) -> None:
    """Lower the last digit while that brings the decimal nearer the value and stays in range."""
    while (
        rest < distance
        and delta - rest >= ten
        and (rest + ten < distance or distance - rest > rest + ten - distance)
    ):
        digits[-1] -= 1
        rest += ten


def _generate_digits(low: int, value: int, high: int, e: int) -> tuple[list[int], int]:
    """Return the digits of a short decimal between `low` and `high`, and the power they stop at."""
    delta, distance, shift = high - low, high - value, -e
    one = 1 << shift
    integral, fractional = high >> shift, high & (one - 1)
    digits: list[int] = []
    remaining = len(str(integral))
    power = 10 ** (remaining - 1)
    while remaining > 0:
        digit, integral = divmod(integral, power)
        digits.append(digit)
        remaining -= 1
        rest = (integral << shift) + fractional
        if rest <= delta:
            _round_toward_value(digits, distance, delta, rest, power << shift)
            return digits, remaining
        power //= 10
    places = 0
    while True:
        fractional *= 10
        digits.append(fractional >> shift)
        fractional &= one - 1
        places += 1
        delta *= 10
        distance *= 10
        if fractional <= delta:
            _round_toward_value(digits, distance, delta, fractional, one)
            return digits, -places


def _grisu2(value: float) -> tuple[list[int], int]:
    """Return a positive double's digits and the power of ten the last of them stands for."""
    w, lower, upper = _boundaries(value)
    f, e, k = _cached_power(upper[1])
    scaled = _multiply(w, (f, e))
    low = _multiply(lower, (f, e))
    high = _multiply(upper, (f, e))
    digits, stop = _generate_digits(low[0] + 1, scaled[0], high[0] - 1, high[1])
    return digits, -k + stop


def _exponent(e: int) -> str:
    """Write an exponent as nlohmann does: `e`, a sign, at least two digits."""
    magnitude = abs(e)
    return f"e{'-' if e < 0 else '+'}{'0' if magnitude < _TWO_DIGITS else ''}{magnitude}"


def _place_point(digits: str, exponent: int) -> str:
    """Write digits times 10 ** exponent in the form nlohmann chooses for their magnitude."""
    k, n = len(digits), len(digits) + exponent
    if k <= n <= _MAX_POINT:
        return f"{digits}{'0' * (n - k)}.0"
    if 0 < n <= _MAX_POINT:
        return f"{digits[:n]}.{digits[n:]}"
    if _MIN_POINT < n <= 0:
        return f"0.{'0' * -n}{digits}"
    return f"{digits[0]}{'.' + digits[1:] if k > 1 else ''}{_exponent(n - 1)}"


def format_float(value: float) -> str:
    """Return a finite double as nlohmann::json's `dump` writes it.

    MalformedPresetError for NaN or an infinity, which a preset cannot hold: a model on
    `PatchbayModel` refuses both, so only a direct call can reach this.
    """
    if not math.isfinite(value):
        msg = f"{value!r} is not a number a preset can hold"
        raise MalformedPresetError(msg)
    sign = "-" if math.copysign(1.0, value) < 0 else ""
    if value == 0:
        return f"{sign}0.0"
    digits, exponent = _grisu2(abs(value))
    return sign + _place_point("".join(map(str, digits)), exponent)
