"""The parameter map: each parameter Vital's VST3 exposes, by its preset key, with its scales.

One record per hosted parameter, measured from the plugin by `patchbay_vital.census` and committed
as data, `data/parameters.json`, read here into models on first use. A record holds core's
`Parameter`, whose id is the preset key a `.vital` file knows the value by and whose bounds and
default are in the unit the plugin displays, and the two conversions between the numbers involved:

- `NormalizedScale`, the host's normalized value in `[0, 1]` and the preset's value: `linear`, the
  preset value is `r * span + minimum` rounded once to float32 (`float32.fma32`, as Vital's build
  computes it), or `indexed`, the same rounded to a whole number;
- `DisplayCurve`, the preset's value and the displayed one: `multiply * skew(preset) + offset`,
  the skew one of the six measured at 1.6.4. A value a parameter holds goes to the display and back
  to that display exactly, and to the same preset value but where a curve's offset absorbs it:
  below `volume`'s 2 ** -43 neighbouring presets share a display. A displayed value goes to the
  float32 nearest the curve's inverse, an indexed scale's a whole number, which need not be one
  the scale holds, below that floor or for an arbitrary display; a set then holds the scale's
  value at `to_normalized`'s result, as Vital does (the host spec's `verification/probes.txt`,
  probe 4; issue #13's spec, `verification/sweep.txt` and `verification/plugin-probe.txt`). A
  choice or a boolean takes a whole index and nothing else, core's rule for them.

Every range, kind and constant is the plugin's own, measured, never written from Vital's source.
pedalboard's key for a parameter is `host_id`, which only `patchbay_vital.host` interprets. The
map records the machine it was measured on: its scales are the plugin's build's, and the host
refuses the map on another. A record holds together in float32: its bounds and default, computed
exactly by the census through this platform's `pow`, `log2` and `sqrt`, come back to the scale's
ends and the preset default through the curve, so a libm an ulp apart still reads the map.
`settings_keys.txt`, the key list the format reads, is derived from this map: its ids but the
per-slot ones, and `PRESET_ONLY_KEYS`, which keeps a key no hosted parameter has, so a census on a
Vital that dropped one forgets nothing.
"""

import functools
import importlib.resources
import math
from bisect import bisect_left
from collections.abc import Callable
from fractions import Fraction
from typing import Literal, Self

from patchbay import Parameter, ParameterId, PatchbayModel, PresetKey
from pydantic import Field, field_validator, model_validator

from patchbay_vital.errors import ParameterRangeError, UnknownParameterError
from patchbay_vital.float32 import fma32, round_to_float32, to_float32
from patchbay_vital.preset import SLOT_KEY

PRESET_ONLY_KEYS = frozenset({PresetKey("chorus_damping")})
"""Keys a preset holds that no hosted parameter does: `chorus_damping`, written by Vital 0.6.x and
dropped on load by 1.6.4, which has no such parameter (the host spec's verification/probes.txt).
A key a newer Vital drops joins it in a spec: the census refuses a key list that would forget one,
naming it (`census.key_list`)."""

type ScaleKind = Literal["linear", "indexed"]
type CurveKind = Literal[
    "linear", "quadratic", "quartic", "square_root", "exponential", "exponential_inverted"
]

_DATA = "data/parameters.json"


def _is_float32(value: float) -> bool:
    """Say whether a float is a float32 exactly, as every value the plugin holds is."""
    return to_float32(value) == value


def _round_half_away(value: float) -> float:
    """Round to a whole number, a half away from zero, as `std::round` does.

    The census's grid does land on a half: 0.5 on every boolean's scale and 0.25 on a scale of two
    steps compute to exactly 0.5, and the plugin holds 1 there, which the committed map's exact fit
    of every grid point shows. `round`, a half to even, would give 0 and fit no boolean. Vital
    rounds so (`value_bridge.h` 116 at 636ca0e, cited for corroboration).
    """
    return math.copysign(math.floor(abs(value) + 0.5), value)


@functools.lru_cache(maxsize=4096)
def _span(minimum: float, maximum: float) -> float:
    """Return the float32 difference of two bounds, computed once per pair of bounds."""
    return round_to_float32(Fraction(maximum) - Fraction(minimum))


class NormalizedScale(PatchbayModel, frozen=True):
    """How the host's normalized value in `[0, 1]` becomes a preset value, and back.

    `minimum` and `maximum` are the preset values at 0 and 1, each a float32. Linear: the preset
    value is `fma32(r, span, minimum)`, `span` the float32 difference of the two. Indexed: the
    same, rounded to a whole number.
    """

    kind: ScaleKind
    minimum: float
    maximum: float

    @property
    def span(self) -> float:
        """The float32 difference of the bounds, as the plugin computes it.

        Computed once per pair of bounds and kept by them, never on the model, so a copy with
        another bound has its own span.
        """
        return _span(self.minimum, self.maximum)

    def to_preset(self, normalized: float) -> float:
        """Return the preset value the plugin holds for a normalized value."""
        value = fma32(to_float32(normalized), self.span, self.minimum)
        return _round_half_away(value) if self.kind == "indexed" else value

    def to_normalized(self, preset: float) -> float:
        """Return the normalized value the host sets for a preset value.

        For a value the scale holds, `to_preset` of the result is that value again: the float32
        nearest `(preset - minimum) / span` lands on it (probe 4, P3).
        """
        return round_to_float32((Fraction(preset) - Fraction(self.minimum)) / Fraction(self.span))

    @model_validator(mode="after")
    def _bounds_are_float32_and_ordered(self) -> Self:
        if not (_is_float32(self.minimum) and _is_float32(self.maximum)):
            msg = f"the bounds are float32 values, given {self.minimum!r} and {self.maximum!r}"
            raise ValueError(msg)
        if not self.minimum < self.maximum:
            msg = f"minimum {self.minimum!r} is not below maximum {self.maximum!r}"
            raise ValueError(msg)
        if self.kind == "indexed" and not (self.minimum.is_integer() and self.maximum.is_integer()):
            msg = "an indexed scale runs between whole numbers"
            raise ValueError(msg)
        return self


def _square(value: float) -> float:
    return value * value


def _power_of_two(exponent: float) -> float:
    """Return two to a power, infinity where a double cannot hold it."""
    try:
        return math.pow(2.0, exponent)
    except OverflowError:
        return math.inf


def _root(value: float) -> float:
    return math.sqrt(max(value, 0.0))


def _log2(value: float) -> float:
    return math.log2(value) if value > 0 else -math.inf


_SKEWS: dict[str, tuple[Callable[[float], float], Callable[[float], float]]] = {
    "linear": (lambda x: x, lambda y: y),
    "quadratic": (_square, _root),
    "quartic": (lambda x: _square(_square(x)), lambda y: _root(_root(y))),
    "square_root": (_root, _square),
    "exponential": (_power_of_two, _log2),
    "exponential_inverted": (lambda x: _power_of_two(-x), lambda y: -_log2(y)),
}
"""Each curve's skew and its inverse, as the census measured the plugin's display to follow."""


class DisplayCurve(PatchbayModel, frozen=True):
    """How a preset value becomes the value displayed: `multiply * skew(preset) + offset`."""

    kind: CurveKind
    multiply: float
    offset: float = 0.0

    def to_display(self, preset: float) -> float:
        """Return the displayed value of a preset value."""
        return self.multiply * _SKEWS[self.kind][0](preset) + self.offset

    def to_preset(self, display: float) -> float:
        """Return the float32 preset value nearest the one a displayed value comes from."""
        return to_float32(_SKEWS[self.kind][1]((display - self.offset) / self.multiply))

    @field_validator("multiply", mode="after")
    @classmethod
    def _multiply_is_not_zero(cls, multiply: float) -> float:
        if multiply == 0:
            msg = "a curve's multiply is not zero"
            raise ValueError(msg)
        return multiply


@functools.lru_cache(maxsize=4096)
def _displayed_ends(
    kind: CurveKind, multiply: float, offset: float, minimum: float, maximum: float
) -> tuple[float, float]:
    curve = DisplayCurve(kind=kind, multiply=multiply, offset=offset)
    low, high = sorted((curve.to_display(minimum), curve.to_display(maximum)))
    return low, high


def displayed_ends(curve: DisplayCurve, scale: NormalizedScale) -> tuple[float, float]:
    """Return the scale's ends as the curve displays them through this platform's libm, in order.

    The one place a record's displayed ends are computed: `MappedParameter.to_preset` bounds by
    them and the census writes a parameter's bounds from them. Computed once per curve and scale,
    kept by their values.
    """
    return _displayed_ends(curve.kind, curve.multiply, curve.offset, scale.minimum, scale.maximum)


class MappedParameter(PatchbayModel, frozen=True):
    """One hosted parameter: core's `Parameter` by its preset key, and how to reach its value.

    `parameter` is in display units; `scale` and `curve` turn a normalized value into a preset value
    and a preset value into a displayed one, and back; `preset_default` is the value the plugin
    starts from. `host_id` is pedalboard's key, and `host_unit` the unit the plugin prints, which a
    record's unit renames (`ms` is seconds, `c` semitones). A choice's or a boolean's value is its
    index, the preset value less the scale's minimum. `choice_labels` holds the plugin's own
    names where they were empty or repeated and `parameter.choices` had to tell them apart.
    """

    parameter: Parameter
    host_id: str = Field(min_length=1)
    scale: NormalizedScale
    curve: DisplayCurve
    preset_default: float
    host_unit: str
    choice_labels: tuple[str, ...] | None = None

    @property
    def id(self) -> ParameterId:
        """The parameter's id, which is its preset key."""
        return self.parameter.id

    @property
    def preset_key(self) -> PresetKey:
        """The key a preset holds this parameter's value under."""
        return PresetKey(self.parameter.id)

    def to_display(self, preset: float) -> float:
        """Return the displayed value of a preset value, inside the host's range or not."""
        return self.curve.to_display(preset)

    def to_preset(self, display: float) -> float:
        """Return the float32 preset value nearest a display's curve inverse, within the scale.

        On an indexed scale that is a whole number, as the plugin holds it. It need not be one the
        scale holds, below `volume`'s 2 ** -43, where presets share a display, or for an arbitrary
        display value; where it is not, a set of `to_normalized`'s result holds a neighbour, as
        Vital does (issue #13). ParameterRangeError when the value is outside the parameter's
        bounds, or is not a whole index where the parameter is a choice or a boolean. The bounds
        are the parameter's own and the scale's ends displayed through this platform's libm, the
        same on the machine the map was measured on and a double ulp apart on another.
        """
        parameter, scale = self.parameter, self.scale
        low, high = displayed_ends(self.curve, scale)
        low, high = min(low, parameter.minimum), max(high, parameter.maximum)
        whole = parameter.kind == "continuous" or display.is_integer()
        if not (low <= display <= high and whole):
            raise ParameterRangeError(self.id, parameter.minimum, parameter.maximum, display)
        preset = min(max(self.curve.to_preset(display), scale.minimum), scale.maximum)
        return _round_half_away(preset) if scale.kind == "indexed" else preset

    def to_normalized(self, display: float) -> float:
        """Return the normalized value the host sets for a displayed value.

        ParameterRangeError when the value is outside the parameter's bounds.
        """
        return self.scale.to_normalized(self.to_preset(display))

    def from_normalized(self, normalized: float) -> float:
        """Return the displayed value of a normalized one.

        ParameterRangeError when the normalized value is outside `[0, 1]`.
        """
        if not 0.0 <= normalized <= 1.0:
            raise ParameterRangeError(self.id, 0.0, 1.0, normalized)
        return self.to_display(self.scale.to_preset(normalized))

    @model_validator(mode="after")
    def _the_parameter_reaches_the_scale(self) -> Self:
        parameter, scale, curve = self.parameter, self.scale, self.curve
        ends = {curve.to_preset(parameter.minimum), curve.to_preset(parameter.maximum)}
        if ends != {scale.minimum, scale.maximum}:
            msg = (
                f"bounds {parameter.minimum!r} and {parameter.maximum!r} do not reach the scale's "
                f"{scale.minimum!r} and {scale.maximum!r}"
            )
            raise ValueError(msg)
        default = self.preset_default
        if not (_is_float32(default) and scale.minimum <= default <= scale.maximum):
            msg = f"the default {default!r} is not a float32 in the scale's range"
            raise ValueError(msg)
        if curve.to_preset(parameter.default.value) != default:
            msg = f"the default {parameter.default.value!r} does not reach {default!r}"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _a_choice_or_boolean_is_an_index(self) -> Self:
        parameter, scale, curve = self.parameter, self.scale, self.curve
        if parameter.kind != "continuous":
            index = (curve.kind, curve.multiply, curve.offset) == ("linear", 1.0, -scale.minimum)
            if scale.kind != "indexed" or not index:
                msg = f"a {parameter.kind} is an index: an indexed scale shown less its minimum"
                raise ValueError(msg)
        labels = self.choice_labels
        if labels is not None and len(labels) != len(parameter.choices or ()):
            msg = "choice labels are the plugin's names for every choice"
            raise ValueError(msg)
        return self


class ParameterMap(PatchbayModel, frozen=True):
    """Every hosted parameter of one plugin version, sorted by id, as measured with one host.

    `machine` is `platform.machine()` where the census ran, the plugin's build the scales are exact
    for; the host refuses the map on another.
    """

    instrument: str = Field(min_length=1)
    vital_version: str = Field(min_length=1)
    host: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    parameters: tuple[MappedParameter, ...]

    def ids(self) -> tuple[ParameterId, ...]:
        """Every parameter's id, in order."""
        return tuple(record.id for record in self.parameters)

    def find(self, parameter_id: ParameterId) -> MappedParameter:
        """Return the record for an id; UnknownParameterError when the map has none."""
        index = bisect_left(self.parameters, parameter_id, key=lambda record: record.id)
        if index < len(self.parameters) and self.parameters[index].id == parameter_id:
            return self.parameters[index]
        raise UnknownParameterError(parameter_id, self.instrument)

    def settings_keys(self) -> tuple[PresetKey, ...]:
        """Return the format's key list: the ids but the per-slot ones, and the preset-only keys."""
        keys = {
            record.preset_key for record in self.parameters if not SLOT_KEY.fullmatch(record.id)
        }
        return tuple(sorted(keys | PRESET_ONLY_KEYS))

    @field_validator("parameters", mode="after")
    @classmethod
    def _sorted_and_distinct(
        cls, records: tuple[MappedParameter, ...]
    ) -> tuple[MappedParameter, ...]:
        ids = [record.id for record in records]
        if ids != sorted(set(ids)):
            msg = "the records are sorted by id, each id once"
            raise ValueError(msg)
        if len({record.host_id for record in records}) != len(records):
            msg = "each host id belongs to one record"
            raise ValueError(msg)
        return records


@functools.cache
def parameter_map() -> ParameterMap:
    """Return the committed map, read and validated on the first call."""
    text = importlib.resources.files("patchbay_vital").joinpath(_DATA).read_text(encoding="utf-8")
    return ParameterMap.model_validate_json(text)
