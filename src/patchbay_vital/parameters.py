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
  exactly; an arbitrary display value comes back as the nearest one the parameter holds (the host
  spec's `verification/probes.txt`, probe 4).

Every range, kind and constant is the plugin's own, measured, never written from Vital's source.
pedalboard's key for a parameter is `host_id`, which only `patchbay_vital.host` interprets.
`settings_keys.txt`, the key list the format reads, is derived from this map: its ids but the
per-slot ones, and `PRESET_ONLY_KEYS`.
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
dropped on load by 1.6.4, which has no such parameter (the host spec's verification/probes.txt)."""

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

    Vital rounds an indexed value so (`value_bridge.h` 116 at 636ca0e, cited for corroboration);
    the census's grid never lands on a half, and a value set from an index never does.
    """
    return math.copysign(math.floor(abs(value) + 0.5), value)


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
        """The float32 difference of the bounds, as the plugin computes it."""
        return round_to_float32(Fraction(self.maximum) - Fraction(self.minimum))

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
        """Return the preset value nearest a displayed value.

        ParameterRangeError when the value is outside the parameter's bounds.
        """
        parameter = self.parameter
        if not parameter.minimum <= display <= parameter.maximum:
            raise ParameterRangeError(self.id, parameter.minimum, parameter.maximum, display)
        preset = self.curve.to_preset(display)
        return min(max(preset, self.scale.minimum), self.scale.maximum)

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
    def _the_parameter_is_what_the_scales_compute(self) -> Self:
        parameter, scale = self.parameter, self.scale
        ends = sorted((self.to_display(scale.minimum), self.to_display(scale.maximum)))
        if [parameter.minimum, parameter.maximum] != ends:
            msg = (
                f"bounds {parameter.minimum!r} and {parameter.maximum!r}, not the scales' {ends!r}"
            )
            raise ValueError(msg)
        default = self.preset_default
        if not (_is_float32(default) and scale.minimum <= default <= scale.maximum):
            msg = f"the default {default!r} is not a float32 in the scale's range"
            raise ValueError(msg)
        if parameter.default.value != self.to_display(self.preset_default):
            msg = f"the default {parameter.default.value!r} is not the curve's"
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
    """Every hosted parameter of one plugin version, sorted by id, as measured with one host."""

    instrument: str = Field(min_length=1)
    vital_version: str = Field(min_length=1)
    host: str = Field(min_length=1)
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
