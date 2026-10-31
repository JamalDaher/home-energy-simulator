"""Integration tests for hourly fuel-aware outage dispatch."""
import pytest
from home_energy_simulator.model import SystemConfig
from home_energy_simulator.fuel import FuelModel
from home_energy_simulator.outage import simulate_outage

LOAD = [2.0] * 24
DARK = [0.0] * 24
GEN = SystemConfig(solar_kw=0, battery_kwh=0, generator_enabled=True, generator_kw=4)
MODEL = FuelModel("gasoline", 4, 0.5, 1.5, 3)


def test_load_dependent_burn_and_cost():
    r = simulate_outage(GEN, LOAD, DARK, days=1, fuel_model=MODEL)
    assert r.generator_hours == 24
    assert r.generator_fuel_used == pytest.approx(24)
    assert r.generator_fuel_cost == pytest.approx(72)
    assert r.generator_fuel_unit == "gallons"
    assert r.total_unserved_kwh == 0


def test_fuel_exhaustion_disables_generator():
    r = simulate_outage(GEN, LOAD, DARK, days=1, fuel_model=MODEL, fuel_available=3)
    assert r.generator_hours == 3
    assert r.generator_fuel_used == pytest.approx(3)
    assert r.generator_fuel_remaining == pytest.approx(0)
    assert r.first_unserved_hour == 3
    assert r.rows[3]["generator_kwh"] == 0


def test_insufficient_fuel_for_full_hour():
    r = simulate_outage(GEN, LOAD, DARK, days=1, fuel_model=MODEL, fuel_available=0.5)
    assert r.generator_hours == 0
    assert r.generator_fuel_used == 0
    assert r.total_unserved_kwh == pytest.approx(48)


def test_solar_displaces_generator_fuel():
    solar_config = SystemConfig(solar_kw=2, battery_kwh=0, generator_enabled=True, generator_kw=4)
    r = simulate_outage(solar_config, LOAD, [1] * 24, days=1, fuel_model=MODEL, fuel_available=1)
    assert r.generator_hours == 0
    assert r.generator_fuel_used == 0
    assert r.generator_fuel_remaining == 1


def test_natural_gas_units():
    gas = FuelModel("natural_gas", 4, 10, 30, 0.02)
    r = simulate_outage(GEN, LOAD, DARK, days=1, fuel_model=gas)
    assert r.generator_fuel_unit == "cubic feet"
    assert r.generator_fuel_used == pytest.approx(480)
    assert r.generator_fuel_cost == pytest.approx(9.6)


def test_legacy_fixed_fuel_unchanged():
    r = simulate_outage(GEN, LOAD, DARK, days=1,
                        generator_fuel_liters_per_hour=2, generator_fuel_available_liters=4)
    assert r.generator_hours == 2
    assert r.generator_fuel_liters == 4
    assert r.generator_fuel_used == 4


def test_invalid_generator_rating():
    with pytest.raises(ValueError):
        simulate_outage(GEN, LOAD, DARK, fuel_model=FuelModel("gasoline", 2, 0.5, 1))


def test_invalid_fuel_inventory():
    with pytest.raises(ValueError):
        simulate_outage(GEN, LOAD, DARK, fuel_model=MODEL, fuel_available=-1)
