import pytest
from home_energy_simulator.hvac import HVACLoad, SourceRating, evaluate_hvac


def test_starting_multiplier():
    h = HVACLoad(3.5, 3)
    assert h.starting_kw == pytest.approx(10.5)
    assert h.soft_start_kw == pytest.approx(10.5)


def test_soft_start_reduces_incremental_surge_only():
    h = HVACLoad(3, 4, 0.5)
    assert h.starting_kw == pytest.approx(12)
    assert h.soft_start_kw == pytest.approx(7.5)


def test_soft_start_never_below_running():
    assert HVACLoad(4, 5, 1).soft_start_kw == pytest.approx(4)


def test_generator_fits_running_but_not_start():
    r = evaluate_hvac(HVACLoad(4, 3), SourceRating(8, 10), 2)
    assert r.running_fits
    assert not r.starting_fits
    assert not r.nominally_fits


def test_soft_start_changes_result():
    h = HVACLoad(4, 3, 0.75)
    source = SourceRating(8, 10)
    assert not evaluate_hvac(h, source, 2).nominally_fits
    assert evaluate_hvac(h, source, 2, use_soft_start=True).nominally_fits


def test_boundary_equal_capacity_fits():
    r = evaluate_hvac(HVACLoad(2, 2), SourceRating(3, 5), 1)
    assert r.nominally_fits
    assert r.running_margin_kw == pytest.approx(0)
    assert r.starting_margin_kw == pytest.approx(0)


def test_zero_load():
    assert evaluate_hvac(HVACLoad(0), SourceRating(0, 0)).nominally_fits


@pytest.mark.parametrize("kwargs", [
    {"running_kw": -1}, {"starting_multiplier": 0.5},
    {"soft_start_reduction": -0.1}, {"soft_start_reduction": 1.1},
    {"running_kw": float("nan")}, {"starting_multiplier": float("inf")},
])
def test_invalid_hvac(kwargs):
    with pytest.raises(ValueError):
        HVACLoad(**kwargs)


@pytest.mark.parametrize("running,surge", [(-1, 2), (4, 3), (float("nan"), 5), (1, float("inf"))])
def test_invalid_source(running, surge):
    with pytest.raises(ValueError):
        SourceRating(running, surge)


def test_invalid_other_load():
    with pytest.raises(ValueError):
        evaluate_hvac(HVACLoad(), SourceRating(10, 15), -1)
