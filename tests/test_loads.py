import pytest
from home_energy_simulator.loads import Appliance, hourly_load_kw, daily_energy_kwh, default_appliances


def test_all_day_constant_load():
    loads = hourly_load_kw([Appliance("router", 100)])
    assert len(loads) == 24
    assert loads == pytest.approx([0.1] * 24)
    assert daily_energy_kwh([Appliance("router", 100)]) == pytest.approx(2.4)


def test_daytime_schedule():
    loads = hourly_load_kw([Appliance("AC", 2000, start_hour=8, end_hour=18)])
    assert sum(loads) == pytest.approx(20)
    assert loads[7] == 0
    assert loads[8] == 2
    assert loads[18] == 0


def test_overnight_schedule_wraps_midnight():
    loads = hourly_load_kw([Appliance("lights", 100, start_hour=22, end_hour=6)])
    assert sum(loads) == pytest.approx(0.8)
    assert loads[23] == pytest.approx(0.1)
    assert loads[3] == pytest.approx(0.1)
    assert loads[12] == 0


def test_quantity_and_duty_cycle():
    loads = hourly_load_kw([Appliance("fans", 100, quantity=3, duty_cycle=0.5)])
    assert loads[0] == pytest.approx(0.15)


def test_multiple_appliances_add():
    loads = hourly_load_kw([Appliance("a", 100), Appliance("b", 200)])
    assert loads[12] == pytest.approx(0.3)


def test_empty_profile_is_zero():
    assert hourly_load_kw([]) == [0.0] * 24


@pytest.mark.parametrize("kwargs", [
    {"name": ""}, {"running_watts": -1}, {"running_watts": float("nan")},
    {"quantity": 0}, {"quantity": 1.5}, {"start_hour": -1},
    {"end_hour": 25}, {"start_hour": 5, "end_hour": 5},
    {"duty_cycle": -0.1}, {"duty_cycle": 1.1},
])
def test_invalid_appliances(kwargs):
    params = dict(name="test", running_watts=100)
    params.update(kwargs)
    with pytest.raises(ValueError):
        Appliance(**params)


def test_defaults_are_nonnegative_and_24_hours():
    loads = hourly_load_kw(default_appliances())
    assert len(loads) == 24
    assert all(x >= 0 for x in loads)
    assert sum(loads) > 0
