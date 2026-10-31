import pytest
from home_energy_simulator.fuel import FuelModel


@pytest.mark.parametrize("fuel", ["gasoline", "propane", "natural_gas"])
def test_supported_fuels(fuel):
    assert FuelModel(fuel, 10, 0.5, 2).unit


def test_interpolation_and_cost():
    model = FuelModel("gasoline", 10, 0.5, 2.5, 3)
    assert model.rate_at_load(0) == pytest.approx(0.5)
    assert model.rate_at_load(5) == pytest.approx(1.5)
    assert model.rate_at_load(10) == pytest.approx(2.5)
    result = model.estimate(5, 10)
    assert result["fuel_needed"] == pytest.approx(15)
    assert result["fuel_cost"] == pytest.approx(45)


def test_finite_inventory_runtime():
    result = FuelModel("propane", 5, 0.25, 1.25, 2).estimate(2.5, 10, 3)
    assert result["available_runtime_hours"] == pytest.approx(4)
    assert result["supplied_hours"] == pytest.approx(4)
    assert result["fuel_used_with_inventory"] == pytest.approx(3)
    assert result["cost_with_inventory"] == pytest.approx(6)


def test_zero_fuel_rate_unbounded_runtime():
    result = FuelModel("natural_gas", 5, 0, 0).estimate(3, 12, 0)
    assert result["available_runtime_hours"] is None
    assert result["supplied_hours"] == 12


@pytest.mark.parametrize("kwargs", [
    {"fuel_type": "diesel"}, {"generator_rated_kw": 0},
    {"idle_rate_per_hour": -1}, {"full_load_rate_per_hour": -1},
    {"price_per_unit": -1}, {"idle_rate_per_hour": 3, "full_load_rate_per_hour": 2},
    {"generator_rated_kw": float("inf")},
])
def test_invalid_config(kwargs):
    base = dict(fuel_type="gasoline", generator_rated_kw=5, idle_rate_per_hour=0.5,
                full_load_rate_per_hour=2)
    base.update(kwargs)
    with pytest.raises(ValueError):
        FuelModel(**base)


@pytest.mark.parametrize("output,hours,available", [
    (-1, 1, None), (6, 1, None), (1, -1, None),
    (1, 1, -1), (float("nan"), 1, None), (1, float("inf"), None),
])
def test_invalid_estimate(output, hours, available):
    model = FuelModel("gasoline", 5, 0.5, 2)
    with pytest.raises(ValueError):
        model.estimate(output, hours, available)
