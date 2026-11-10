"""The generator fits a scale and a curve exactly or names the parameter; what it writes reads back.

Measurements here are built the way the plugin reports them (the host spec's
`verification/probes.txt`): preset values by `fma32` on the census's grid, display texts printed
to six significant digits with the plugin's suffix.
"""

import platform
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

import pytest
from patchbay import ParameterId, PresetKey, Unit

from patchbay_vital import census
from patchbay_vital.census import (
    GRID,
    build_map,
    dump_map,
    fit_record,
    fit_scale,
    main,
)
from patchbay_vital.errors import CensusError
from patchbay_vital.float32 import fma32
from patchbay_vital.host import HostMeasurement, VitalHost
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


def test_ends_that_make_no_scale_are_named() -> None:
    """Ends in the wrong order make no scale of either kind: the parameter is named, chained."""
    backwards = _measurement("Backwards", _LINEAR, str)._replace(
        presets=tuple(reversed(_measurement("Backwards", _LINEAR, str).presets))
    )
    with pytest.raises(CensusError) as caught:
        fit_scale(backwards)
    assert caught.value.label == "Backwards"
    assert "its ends make no scale" in caught.value.reason
    assert caught.value.__cause__ is not None


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


def test_the_refusal_quotes_the_scale_s_own_values() -> None:
    """The values a refusal is compared against are the scale's `to_preset`: float32 span."""
    scale = NormalizedScale(kind="linear", minimum=2.0**-30, maximum=1.0)  # a span no float32 holds
    measured = _measurement("Odd Span", scale, str)
    off = list(measured.presets)
    off[3] = 0.26
    with pytest.raises(CensusError) as caught:
        fit_scale(measured._replace(presets=tuple(off)))
    assert str(caught.value).endswith(f"against {[scale.to_preset(point) for point in GRID]}")


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


@pytest.mark.parametrize(
    ("names", "choices"),
    [
        (("A", "A", "A_1"), ("A_0", "A_1_1", "A_1")),
        (("", "option_0"), ("option_0_0", "option_0")),
    ],
)
def test_a_made_up_name_never_collides_with_a_given_one(
    names: tuple[str, ...], choices: tuple[str, ...]
) -> None:
    """A name made from an index is lengthened until it is no given name's and no other's."""
    scale = NormalizedScale(kind="indexed", minimum=0.0, maximum=float(len(names) - 1))
    record = fit_record(_measurement("Named", scale, str), scale, names)
    assert record.parameter.choices == choices
    assert record.choice_labels == names


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


def test_a_default_that_displays_as_no_number_is_named() -> None:
    """A default the curve sends past a double is the parameter's refusal, not a traceback."""
    curve = DisplayCurve(kind="exponential", multiply=1.0)
    measured = _measurement("Vast", _LINEAR, _printed(curve, ""), preset_default=2000.0)
    with pytest.raises(CensusError) as caught:
        fit_record(measured, _LINEAR, None)
    assert caught.value.label == "Vast"


class _FakeHost:
    """A host that answers the census with measurements given, no plugin behind it."""

    name, version, host = "Vital", "1.6.4", "pedalboard 0.9.26"

    def __init__(self, measurements: Sequence[HostMeasurement]) -> None:
        self._measurements = tuple(measurements)

    def measure(self, grid: Sequence[float]) -> tuple[HostMeasurement, ...]:
        assert tuple(grid) == GRID
        return self._measurements

    def display_texts(self, _host_id: str, points: Sequence[float]) -> tuple[str, ...]:
        return tuple(str(point) for point in points)


def _host(*measurements: HostMeasurement) -> VitalHost:
    return cast("VitalHost", _FakeHost(measurements))


def test_two_parameters_moving_one_preset_value_are_named() -> None:
    """The second to move a key the first moved is refused, naming both."""
    first = _measurement("Filter 1 Cutoff", _LINEAR, str)
    second = _measurement("Filter 1 Cutoff Again", _LINEAR, str)._replace(
        preset_key=first.preset_key
    )
    with pytest.raises(CensusError) as caught:
        build_map(_host(first, second))
    assert caught.value.label == "Filter 1 Cutoff Again"
    assert "'Filter 1 Cutoff' moves" in caught.value.reason


def test_the_map_records_the_machine_the_census_ran_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """The scales are the plugin's build's, so the map says which machine measured them."""
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    built = build_map(_host(_measurement("Filter 1 Cutoff", _LINEAR, str)))
    assert built.machine == "arm64"


def test_the_written_map_reads_back_as_built_one_record_a_line() -> None:
    """The committed text is the map's own JSON, laid out so a diff shows one record per line."""
    scale = NormalizedScale(kind="linear", minimum=8.0, maximum=136.0)
    curve = DisplayCurve(kind="linear", multiply=1.0, offset=-60.0)
    records = tuple(
        fit_record(_measurement(label, scale, _printed(curve, " semitones")), scale, None)
        for label in ("Filter 1 Cutoff", "Filter 2 Cutoff")
    )
    built = ParameterMap(
        instrument="Vital",
        vital_version="1.6.4",
        host="pedalboard 0.9.26",
        machine="arm64",
        parameters=records,
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


def _main(tmp_path: Path, keys: Path) -> tuple[int, Path]:
    arguments = ["--plugin", str(tmp_path), "--parameters", str(tmp_path / "map.json")]
    return main([*arguments, "--settings-keys", str(keys)]), tmp_path / "map.json"


def test_the_census_writes_both_files_and_names_a_parameter_it_cannot_fit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both outputs are written from one measured host; a second that cannot fit writes neither."""
    good = _measurement("Filter 1 Cutoff", _LINEAR, str)
    monkeypatch.setattr(census, "VitalHost", lambda _path: _host(good))
    status, parameters = _main(tmp_path, tmp_path / "keys.txt")
    assert status == 0
    assert "1 parameters of Vital 1.6.4" in capsys.readouterr().out
    assert (tmp_path / "keys.txt").read_text(
        encoding="utf-8"
    ) == "chorus_damping\nfilter_1_cutoff\n"
    assert ParameterMap.model_validate_json(parameters.read_text(encoding="utf-8")).machine
    bad = good._replace(label="Fortnightly", texts=("1 fortnights",) * len(GRID))
    monkeypatch.setattr(census, "VitalHost", lambda _path: _host(bad))
    status, _ = _main(tmp_path / "second", tmp_path / "second" / "keys.txt")
    assert status == 1
    assert "cannot fit 'Fortnightly'" in capsys.readouterr().err
    assert not (tmp_path / "second").exists()


def test_a_key_list_that_cannot_be_written_leaves_the_map_unwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The key list is written first, so a failure there leaves the map as it was."""
    monkeypatch.setattr(
        census, "VitalHost", lambda _path: _host(_measurement("Filter 1 Cutoff", _LINEAR, str))
    )
    (tmp_path / "map.json").write_text("as it was", encoding="utf-8")
    status, parameters = _main(tmp_path, tmp_path / "nowhere" / "keys.txt")
    assert status == 1
    assert "census: cannot write" in capsys.readouterr().err
    assert parameters.read_text(encoding="utf-8") == "as it was"


def test_a_rename_failing_after_the_key_list_s_puts_the_key_list_back(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The key list and the map change together or not at all: neither is left disagreeing."""
    monkeypatch.setattr(
        census, "VitalHost", lambda _path: _host(_measurement("Filter 1 Cutoff", _LINEAR, str))
    )
    keys = tmp_path / "keys.txt"
    keys.write_text("old keys", encoding="utf-8")
    (tmp_path / "map.json").write_text("old map", encoding="utf-8")
    renames: list[str] = []
    replace = Path.replace

    def failing_second(self: Path, target: Path) -> Path:
        renames.append(target.name)
        if len(renames) == 2:  # noqa: PLR2004 - the map's rename, after the key list's
            msg = f"cannot rename over {target.name}"
            raise OSError(msg)
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_second)
    status, parameters = _main(tmp_path, keys)
    assert status == 1
    assert "census: cannot write: cannot rename over map.json" in capsys.readouterr().err
    assert renames[:2] == ["keys.txt", "map.json"]
    assert keys.read_text(encoding="utf-8") == "old keys"
    assert parameters.read_text(encoding="utf-8") == "old map"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["keys.txt", "map.json"]
