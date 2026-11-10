"""The generator fits a scale and a curve exactly or names the parameter; what it writes reads back.

Measurements here are built the way the plugin reports them (the host spec's
`verification/probes.txt`): preset values by `fma32` on the census's grid, display texts printed
to six significant digits with the plugin's suffix.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from patchbay import ParameterId, PresetKey, Unit

from patchbay_vital.census import (
    GRID,
    dump_map,
    fit_record,
    fit_scale,
    main,
)
from patchbay_vital.errors import CensusError
from patchbay_vital.float32 import fma32
from patchbay_vital.host import HostMeasurement
from patchbay_vital.parameters import DisplayCurve, NormalizedScale, ParameterMap


def _measurement(
    label: str,
    scale: NormalizedScale,
    show: Callable[[float], str],
    preset_default: float | None = None,
) -> HostMeasurement:
    """Measure a parameter on a scale as the host does, its texts printed by `show`."""
    presets = tuple(scale.to_preset(point) for point in GRID)
    return HostMeasurement(
        host_id=label.lower().replace(" ", "_"),
        label=label,
        preset_key=PresetKey(label.lower().replace(" ", "_")),
        preset_default=presets[0] if preset_default is None else preset_default,
        presets=presets,
        texts=tuple(show(preset) for preset in presets),
    )


def _printed(curve: DisplayCurve, suffix: str, factor: float = 1.0) -> Callable[[float], str]:
    """Print a preset value as the plugin does: the curve's value in its unit, six digits."""
    return lambda preset: f"{curve.to_display(preset) / factor:.6g}{suffix}"


_LINEAR = NormalizedScale(kind="linear", minimum=-7.0, maximum=9.0)


def test_a_linear_scale_is_found_exactly() -> None:
    """Every grid point is its normalized value's fused multiply-add, so the scale is linear."""
    measured = _measurement("LFO 1 Frequency", _LINEAR, str)
    assert fit_scale(measured) == _LINEAR


def test_an_indexed_scale_is_found_exactly() -> None:
    """Grid points rounded to whole numbers between the bounds are an indexed scale."""
    indexed = NormalizedScale(kind="indexed", minimum=1.0, maximum=32.0)
    assert fit_scale(_measurement("Polyphony", indexed, str)) == indexed


def test_a_scale_that_is_neither_is_named() -> None:
    """One grid point off by a float32 step and the census refuses rather than guess."""
    measured = _measurement(
        "Volume", NormalizedScale(kind="linear", minimum=0.0, maximum=10.0), str
    )
    off = list(measured.presets)
    off[3] = fma32(GRID[3], 10.0, 0.0) + 2.0**-20
    with pytest.raises(CensusError) as caught:
        fit_scale(measured._replace(presets=tuple(off)))
    assert caught.value.label == "Volume"


@pytest.mark.parametrize(
    ("curve", "suffix", "factor", "unit"),
    [
        (DisplayCurve(kind="exponential_inverted", multiply=1.0), " secs", 1.0, Unit.seconds),
        (DisplayCurve(kind="exponential", multiply=1.0), " secs", 1.0, Unit.seconds),
        (DisplayCurve(kind="linear", multiply=100.0), "%", 1.0, Unit.percent),
        (
            DisplayCurve(kind="linear", multiply=1.0, offset=-60.0),
            " semitones",
            1.0,
            Unit.semitones,
        ),
        (DisplayCurve(kind="exponential", multiply=1.0), " ms", 0.001, Unit.seconds),
        (DisplayCurve(kind="linear", multiply=1.0), " c", 0.01, Unit.semitones),
    ],
)
def test_a_curve_and_its_unit_are_found_from_the_texts(
    curve: DisplayCurve, suffix: str, factor: float, unit: Unit
) -> None:
    """The shortest constants that print every text, in patchbay's unit (ms are s, c semitones)."""
    measured = _measurement("Some Time", _LINEAR, _printed(curve, suffix.strip(), factor))
    record = fit_record(measured, _LINEAR, None)
    assert record.curve == curve
    assert (record.parameter.unit, record.host_unit) == (unit, suffix.strip())


def test_quartic_square_root_and_quadratic_curves_are_told_apart() -> None:
    """An envelope's time is the preset value to the fourth, a volume the root less 80 dB."""
    attack = NormalizedScale(kind="linear", minimum=0.0, maximum=2.378420114517212)
    volume = NormalizedScale(kind="linear", minimum=0.0, maximum=7399.4404296875)
    level = NormalizedScale(kind="linear", minimum=0.0, maximum=1.0)
    for scale, curve, suffix in (
        (attack, DisplayCurve(kind="quartic", multiply=1.0), "secs"),
        (volume, DisplayCurve(kind="square_root", multiply=1.0, offset=-80.0), "dB"),
        (level, DisplayCurve(kind="quadratic", multiply=1.0), ""),
    ):
        measured = _measurement("Curve", scale, _printed(curve, suffix))
        assert fit_record(measured, scale, None).curve == curve


def test_the_label_names_a_unit_the_display_does_not_print() -> None:
    """Vital shows a tempo with no suffix; its label says what it is."""
    scale = NormalizedScale(kind="linear", minimum=0.3333333432674408, maximum=5.0)
    tempo = _measurement(
        "Beats Per Minute", scale, _printed(DisplayCurve(kind="linear", multiply=60.0), "")
    )
    assert fit_record(tempo, scale, None).parameter.unit is Unit.bpm


@pytest.mark.parametrize(
    "texts",
    [("1 secs",) * 5 + ("1 furlongs",) * 6, ("1 fortnights",) * 11],
    ids=["mixed", "unknown"],
)
def test_texts_in_no_one_known_unit_are_named(texts: tuple[str, ...]) -> None:
    """A suffix the table does not hold, or two at once, is refused rather than read as a name."""
    measured = _measurement("Odd", _LINEAR, str)._replace(texts=texts)
    with pytest.raises(CensusError) as caught:
        fit_record(measured, _LINEAR, None)
    assert caught.value.label == "Odd"


def test_no_curve_that_fits_is_named() -> None:
    """Texts no curve with short constants prints are refused, not fitted loosely."""
    measured = _measurement("Wobbly", _LINEAR, str)._replace(
        texts=tuple(f"{i * i * i}" for i in range(11))
    )
    with pytest.raises(CensusError):
        fit_record(measured, _LINEAR, None)


_TWO = NormalizedScale(kind="indexed", minimum=0.0, maximum=1.0)


@pytest.mark.parametrize(
    ("names", "kind"),
    [
        (("Off", "On"), "boolean"),
        (("0", "60"), "boolean"),  # bypass shows numbers
        (("Shelf", "Notch"), "choice"),  # eq_band_mode keeps its names
    ],
)
def test_a_parameter_of_two_values_is_a_switch_or_a_choice(
    names: tuple[str, str], kind: str
) -> None:
    """A switch reads Off and On or numbers; any other pair of names is a choice of two."""
    record = fit_record(_measurement("Two", _TWO, str), _TWO, names)
    assert record.parameter.kind == kind
    assert record.parameter.choices == (names if kind == "choice" else None)


def test_a_choice_is_its_index_from_the_scale_s_minimum() -> None:
    """Delay tempo's presets run from 4; its value is the index from 0, its names in order."""
    scale = NormalizedScale(kind="indexed", minimum=4.0, maximum=6.0)
    names = ("1/1", "1/2", "1/4")  # a name like 4/1 is not a number with a unit
    record = fit_record(_measurement("Delay Tempo", scale, str, preset_default=5.0), scale, names)
    assert (record.parameter.kind, record.parameter.minimum, record.parameter.maximum) == (
        "choice",
        0.0,
        2.0,
    )
    assert record.parameter.default.value == 1.0
    assert record.from_normalized(1.0) == 2.0  # noqa: PLR2004 - the last index


def test_empty_and_repeated_names_are_told_apart_and_kept_beside() -> None:
    """Core's choices are distinct and non-empty; the plugin's own names stay in the record."""
    scale = NormalizedScale(kind="indexed", minimum=0.0, maximum=4.0)
    names = ("None", "FM <- Osc", "FM <- Osc", "", "")
    record = fit_record(_measurement("Distortion Type", scale, str), scale, names)
    assert record.parameter.choices == (
        "None",
        "FM <- Osc_1",
        "FM <- Osc_2",
        "option_3",
        "option_4",
    )
    assert record.choice_labels == names


def test_numbers_on_an_indexed_scale_are_continuous() -> None:
    """Transposes and voices are whole numbers with a unit, not a choice of their names."""
    scale = NormalizedScale(kind="indexed", minimum=-48.0, maximum=48.0)
    measured = _measurement("Oscillator 1 Transpose", scale, lambda p: f"{p:.6g}")
    names = tuple(f"{i}" for i in range(-48, 49))
    record = fit_record(measured, scale, names)
    assert (record.parameter.kind, record.scale.kind, record.parameter.unit) == (
        "continuous",
        "indexed",
        Unit.none,
    )


def test_the_written_map_reads_back_as_built_one_record_a_line() -> None:
    """The committed text is the map's own JSON, laid out so a diff shows one record per line."""
    scale = NormalizedScale(kind="linear", minimum=8.0, maximum=136.0)
    curve = DisplayCurve(kind="linear", multiply=1.0, offset=-60.0)
    records = tuple(
        fit_record(_measurement(label, scale, _printed(curve, " semitones")), scale, None)
        for label in ("Filter 1 Cutoff", "Filter 2 Cutoff")
    )
    built = ParameterMap(
        instrument="Vital", vital_version="1.6.4", host="pedalboard 0.9.26", parameters=records
    )
    text = dump_map(built)
    assert ParameterMap.model_validate_json(text) == built
    assert len(text.splitlines()) == 2 + len(records)
    assert built.find(ParameterId("filter_2_cutoff")).host_id == "filter_2_cutoff"


def test_the_census_names_a_plugin_it_cannot_load_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No plugin at the path: exit 1, the reason on stderr, neither output written."""
    parameters, keys = tmp_path / "parameters.json", tmp_path / "settings_keys.txt"
    status = main(
        [
            "--plugin",
            str(tmp_path / "Vital.vst3"),
            "--parameters",
            str(parameters),
            "--settings-keys",
            str(keys),
        ]
    )
    assert status == 1
    assert "nothing at the path" in capsys.readouterr().err
    assert not parameters.exists()
    assert not keys.exists()
