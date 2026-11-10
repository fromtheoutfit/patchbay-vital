"""The parameter map's generator: measure each hosted parameter, fit its scales, write the data.

Run once per Vital version, with the `host` extra, from the repository root, and commit what it
writes: `uv run --locked python -m patchbay_vital.census --parameters
src/patchbay_vital/data/parameters.json --settings-keys src/patchbay_vital/settings_keys.txt`.
`--plugin PATH` names the plugin; without it the host's `DEFAULT_PATH` is the one place looked at.
Both outputs are named, so nothing is written anywhere unasked.

The fitting is exact where the plugin is: a scale is `linear` or `indexed` only when every grid
point equals what `float32.fma32` computes, with no tolerance. A curve is fitted to the plugin's
display text, printed to six significant digits, so its constants are the shortest decimals that
reproduce every text at that precision. A unit is the text's suffix renamed into patchbay's
(`SUFFIX_UNITS`), the one label rule aside (`LABEL_UNITS`); an indexed parameter of two values
shown as Off and On or as numbers is a boolean, one whose texts are other names a choice, any other
continuous on its indexed scale. A
parameter that fits none of this is `CensusError`, naming it: the map is never written with a guess.
Every rule here came from the measurements in the host spec's `verification/probes.txt`; none was
written from Vital's source.
"""

import argparse
import math
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from patchbay import Parameter, PatchbayValidationError, Quantity, Unit

from patchbay_vital.errors import CensusError, VitalError
from patchbay_vital.float32 import fma32
from patchbay_vital.host import DEFAULT_PATH, HostMeasurement, VitalHost
from patchbay_vital.parameters import (
    CurveKind,
    DisplayCurve,
    MappedParameter,
    NormalizedScale,
    ParameterMap,
)

GRID = (0.0, 0.1, 0.13, 0.25, 0.3, 0.37, 0.5, 0.7, 0.75, 0.9, 1.0)
"""The normalized values each parameter is measured at: both ends, and points that tell the scale
kinds and the curves apart (0.13 and 0.37 land between an indexed scale's steps)."""

SUFFIX_UNITS: dict[str, tuple[Unit, float]] = {
    "": (Unit.none, 1.0),
    "secs": (Unit.seconds, 1.0),
    "s": (Unit.seconds, 1.0),
    "ms": (Unit.seconds, 0.001),
    "dB": (Unit.db, 1.0),
    "%": (Unit.percent, 1.0),
    "semitones": (Unit.semitones, 1.0),
    "c": (Unit.semitones, 0.01),
    "Hz": (Unit.hz, 1.0),
    "x": (Unit.none, 1.0),
    "v": (Unit.none, 1.0),
    "voices": (Unit.none, 1.0),
}
"""Each suffix the plugin prints, the unit it becomes and the factor from the printed number to it:
milliseconds are seconds and cents semitones, `patchbay.Unit` holding neither (the host spec's
shape.md, Decision 13)."""

LABEL_UNITS = {"Beats Per Minute": Unit.bpm}
"""A unit the plugin's label names where its display prints none."""

CURVE_KINDS: tuple[CurveKind, ...] = (
    "linear",
    "quadratic",
    "quartic",
    "square_root",
    "exponential",
    "exponential_inverted",
)
"""The curves the census tries, in this order; the first that reproduces every text is taken."""

_MAX_NAMED = 400
"""An indexed parameter with more steps than this is numeric: its names are not read one by one."""

_DIGITS = 6
"""The plugin prints a displayed number to six significant digits."""

_OFF_ON = ("Off", "On")
"""What a switch displays; another pair of names is a choice of two, which keeps them."""

_NUMBER = re.compile(r"(-?[0-9]+(?:\.[0-9]+)?(?:e[-+][0-9]+)?) ?(.*)")
_BOOLEAN = 2


def _number(text: str) -> tuple[float, str] | None:
    """Return a display text's number and suffix, or None when it is a name."""
    match = _NUMBER.fullmatch(text)
    if match is None or match.group(2) not in SUFFIX_UNITS:
        return None
    return float(match.group(1)), match.group(2)


def _half_digit(value: float) -> float:
    """Return how far a value may be from a printed number and print as it.

    Half the step of the last of six significant digits, and a millionth of the value more: the
    plugin computes what it prints in float32, a little off the double computed here.
    """
    if value == 0:
        return 0.5 * 10.0 ** -(_DIGITS + 1)
    return 0.5 * 10.0 ** (math.floor(math.log10(abs(value))) - (_DIGITS - 1)) + 1e-6 * abs(value)


def fit_scale(measurement: HostMeasurement) -> NormalizedScale:
    """Return the scale every grid point of a measurement lies on exactly; CensusError if none."""
    presets = measurement.presets
    minimum, maximum = presets[0], presets[-1]
    for kind in ("linear", "indexed"):
        try:
            scale = NormalizedScale(kind=kind, minimum=minimum, maximum=maximum)
        except PatchbayValidationError:  # bounds this kind cannot have rule it out
            continue
        if [scale.to_preset(point) for point in GRID] == list(presets):
            return scale
    plain = [fma32(point, maximum - minimum, minimum) for point in GRID]
    msg = f"neither linear nor indexed: {list(presets)} against {plain}"
    raise CensusError(measurement.label, msg)


def _fit_curve(label: str, presets: Sequence[float], numbers: Sequence[float]) -> DisplayCurve:
    """Return the first curve whose shortest constants reproduce every displayed number."""
    for kind in CURVE_KINDS:
        skewed = [DisplayCurve(kind=kind, multiply=1.0).to_display(p) for p in presets]
        if not all(math.isfinite(x) for x in skewed) or len(set(skewed)) < _BOOLEAN:
            continue
        multiply, offset = _least_squares(skewed, numbers)
        for digits in range(1, _DIGITS + 3):
            curve = _shortest(kind, multiply, offset, digits, numbers)
            if curve is not None and all(
                abs(curve.to_display(p) - y) <= _half_digit(y)
                for p, y in zip(presets, numbers, strict=True)
            ):
                return curve
    msg = f"no curve reproduces {list(numbers)} from {list(presets)}"
    raise CensusError(label, msg)


def _least_squares(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Return the slope and intercept of the line nearest the points."""
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    spread = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / spread
    return slope, mean_y - slope * mean_x


def _shortest(
    kind: CurveKind, multiply: float, offset: float, digits: int, numbers: Sequence[float]
) -> DisplayCurve | None:
    """Return the curve with its constants rounded to `digits` significant digits, if valid."""
    scale = max(abs(y) for y in numbers)
    rounded_offset = 0.0 if abs(offset) <= _half_digit(scale) else float(f"{offset:.{digits}g}")
    rounded_multiply = float(f"{multiply:.{digits}g}")
    if rounded_multiply == 0:
        return None
    return DisplayCurve(kind=kind, multiply=rounded_multiply, offset=rounded_offset)


def _choices(names: Sequence[str]) -> tuple[str, ...]:
    """Tell empty and repeated names apart by their index, so core's rule holds (Decision 8)."""
    return tuple(
        f"option_{index}" if not name else f"{name}_{index}" if names.count(name) > 1 else name
        for index, name in enumerate(names)
    )


def fit_record(
    measurement: HostMeasurement, scale: NormalizedScale, names: Sequence[str] | None
) -> MappedParameter:
    """Return a measured parameter's record; `names` are an indexed one's texts at each index.

    CensusError when its texts mix suffixes, a suffix is not in `SUFFIX_UNITS`, or no curve fits.
    """
    label = measurement.label
    span = int(scale.maximum - scale.minimum) if scale.kind == "indexed" else None
    index = DisplayCurve(kind="linear", multiply=1.0, offset=0.0 - scale.minimum)  # never -0.0
    named = names is not None and any(_number(name) is None for name in names)
    if span == 1 and (not named or tuple(names or ()) == _OFF_ON):
        return _record(
            measurement,
            scale,
            curve=index,
            kind="boolean",
            unit=Unit.none,
            host_unit="",
            choices=None,
        )
    if names is not None and named:
        choices = _choices(names)
        labels = tuple(names) if choices != tuple(names) else None
        return _record(
            measurement,
            scale,
            curve=index,
            kind="choice",
            unit=Unit.none,
            host_unit="",
            choices=choices,
            labels=labels,
        )
    parsed = [_number(text) for text in measurement.texts]
    suffixes = {item[1] for item in parsed if item is not None}
    if None in parsed or len(suffixes) != 1:
        msg = f"texts {list(measurement.texts)} are not numbers in one known unit"
        raise CensusError(label, msg)
    (suffix,) = suffixes
    unit, factor = SUFFIX_UNITS[suffix]
    unit = LABEL_UNITS.get(label, unit)
    numbers = [item[0] * factor for item in parsed if item is not None]
    curve = _fit_curve(label, measurement.presets, numbers)
    return _record(
        measurement,
        scale,
        curve=curve,
        kind="continuous",
        unit=unit,
        host_unit=suffix,
        choices=None,
    )


def _record(  # noqa: PLR0913 - every fact a record is built from, each given by name at the call
    measurement: HostMeasurement,
    scale: NormalizedScale,
    *,
    curve: DisplayCurve,
    kind: str,
    unit: Unit,
    host_unit: str,
    choices: tuple[str, ...] | None,
    labels: tuple[str, ...] | None = None,
) -> MappedParameter:
    """Build a record whose parameter is what its scale and curve compute.

    CensusError, chained, when the record does not hold together as the map's models require.
    """
    ends = sorted((curve.to_display(scale.minimum), curve.to_display(scale.maximum)))
    default = Quantity(value=curve.to_display(measurement.preset_default), unit=unit)
    try:
        parameter = Parameter.model_validate(
            {
                "id": measurement.preset_key,
                "label": measurement.label,
                "kind": kind,
                "unit": unit,
                "minimum": ends[0],
                "maximum": ends[1],
                "default": default,
                "choices": choices,
            }
        )
        return MappedParameter(
            parameter=parameter,
            host_id=measurement.host_id,
            scale=scale,
            curve=curve,
            preset_default=measurement.preset_default,
            host_unit=host_unit,
            choice_labels=labels,
        )
    except PatchbayValidationError as error:
        raise CensusError(measurement.label, str(error)) from error


def build_map(host: VitalHost) -> ParameterMap:
    """Measure every parameter the host exposes and return the map of them, sorted by id."""
    records = []
    for measurement in host.measure(GRID):
        scale = fit_scale(measurement)
        names = None
        if scale.kind == "indexed" and scale.maximum - scale.minimum <= _MAX_NAMED:
            steps = range(int(scale.minimum), int(scale.maximum) + 1)
            points = [scale.to_normalized(float(step)) for step in steps]
            names = host.display_texts(measurement.host_id, points)
        records.append(fit_record(measurement, scale, names))
    return ParameterMap(
        instrument=host.name,
        vital_version=host.version,
        host=host.host,
        parameters=tuple(sorted(records, key=lambda record: record.id)),
    )


def dump_map(parameter_map: ParameterMap) -> str:
    """Return the map's committed text: its fields, a record a line, so a diff is per record."""
    header = parameter_map.model_dump_json(exclude={"parameters"})
    lines = ",\n".join(record.model_dump_json() for record in parameter_map.parameters)
    return f'{header[:-1]},"parameters":[\n{lines}\n]}}\n'


def main(argv: Sequence[str] | None = None) -> int:
    """Measure the plugin and write the map and the key list; 1, saying why, when it cannot."""
    parser = argparse.ArgumentParser(prog="python -m patchbay_vital.census", description=__doc__)
    parser.add_argument("--plugin", type=Path, default=DEFAULT_PATH, help="Vital's VST3 bundle")
    parser.add_argument("--parameters", type=Path, required=True, help="the map to write")
    parser.add_argument("--settings-keys", type=Path, required=True, help="the key list to write")
    arguments = parser.parse_args(argv)
    try:
        built = build_map(VitalHost(arguments.plugin))
    except VitalError as error:
        sys.stderr.write(f"census: {error}\n")
        return 1
    text = dump_map(built)
    if ParameterMap.model_validate_json(text) != built:
        sys.stderr.write("census: the map does not read back as written\n")
        return 1
    arguments.parameters.write_text(text, encoding="utf-8")
    arguments.settings_keys.write_text("\n".join(built.settings_keys()) + "\n", encoding="utf-8")
    sys.stdout.write(
        f"{len(built.parameters)} parameters of {built.instrument} {built.vital_version}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
