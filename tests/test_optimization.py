import pytest
from home_energy_simulator.model import SystemConfig
from home_energy_simulator.fuel import FuelModel
from home_energy_simulator.optimization import UnitCosts, optimize_system

DARK = [0.0] * 24
LOAD = [1.0] * 24
BASE = SystemConfig(solar_kw=0, battery_kwh=0, inverter_kw=5)
COST = UnitCosts(1000, 500, 200)


def search(**overrides):
    params = dict(baseline=BASE, daily_load_kw=LOAD, daily_sun_factors=DARK,
                  solar_options=[0], battery_options=[0], generator_options=[0, 2],
                  costs=COST, days=1)
    params.update(overrides)
    return optimize_system(**params)


def test_reliable_candidate_first():
    results = search()
    assert len(results) == 2
    assert results[0].generator_kw == 2
    assert results[0].demand_served == pytest.approx(1)
    assert results[1].unmet_kwh == pytest.approx(24)


def test_no_solar_at_night_and_costs():
    results = search(solar_options=[0, 4], generator_options=[2])
    assert results[0].solar_kw == 0
    assert results[0].capital_cost == 400


def test_solar_reduces_unmet_energy():
    results = search(solar_options=[0, 2], generator_options=[0],
                     daily_sun_factors=[1] * 24)
    assert results[0].solar_kw == 2
    assert results[0].demand_served == pytest.approx(1)


def test_battery_initial_energy():
    baseline = SystemConfig(solar_kw=0, battery_kwh=0, inverter_kw=5,
                            initial_soc=1, minimum_soc=0, discharge_efficiency=1)
    results = search(baseline=baseline, battery_options=[0, 24],
                     generator_options=[0])
    assert results[0].battery_kwh == 24
    assert results[0].unmet_kwh == 0


def test_fuel_budget_changes_reliability():
    fuel = FuelModel("gasoline", 2, 1, 1, 4)
    results = search(fuel_model=fuel, fuel_available=3)
    assert results[0].generator_kw == 2
    assert results[0].generator_hours == 3
    assert results[0].fuel_used == pytest.approx(3)
    assert results[0].fuel_cost == pytest.approx(12)
    assert results[0].demand_served == pytest.approx(3 / 24)


def test_duplicate_candidates_removed():
    assert len(search(solar_options=[0, 0], generator_options=[2, 2])) == 1


@pytest.mark.parametrize("changes", [
    {"solar_options": []},
    {"battery_options": [-1]},
    {"generator_options": [float("nan")]},
    {"min_demand_served": 1.1},
    {"max_candidates": 1},
])
def test_invalid_search(changes):
    with pytest.raises(ValueError):
        search(**changes)


def test_invalid_costs():
    with pytest.raises(ValueError):
        UnitCosts(-1, 0, 0)


def test_generator_fuel_rating_must_cover_candidates():
    with pytest.raises(ValueError):
        search(fuel_model=FuelModel("gasoline", 1, 0.2, 1))
