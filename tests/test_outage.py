"""Outage behavior, energy accounting and fuel limits."""
import pytest
from home_energy_simulator.model import SystemConfig
from home_energy_simulator.outage import simulate_outage

NIGHT = [0.0] * 24
ONE_KW = [1.0] * 24

def test_no_sources_has_unserved_load():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=0), ONE_KW, NIGHT, days=2)
    assert r.total_unserved_kwh == pytest.approx(48)
    assert r.first_unserved_hour == 0
    assert r.hours_simulated == 48

def test_grid_forcibly_disabled():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=0, grid_available=True), ONE_KW, NIGHT)
    assert r.total_unserved_kwh == pytest.approx(24)

def test_generator_serves_load():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=0, generator_enabled=True, generator_kw=2), ONE_KW, NIGHT)
    assert r.total_unserved_kwh == pytest.approx(0)
    assert r.generator_hours == 24

def test_generator_fuel_limit():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=0, generator_enabled=True, generator_kw=2),
                        ONE_KW, NIGHT, generator_fuel_liters_per_hour=2, generator_fuel_available_liters=6)
    assert r.generator_hours == 3
    assert r.generator_fuel_liters == pytest.approx(6)
    assert r.first_unserved_hour == 3

def test_battery_soc_carries_over_days():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=10, initial_soc=1, minimum_soc=0,
                                      discharge_efficiency=1, inverter_kw=5), ONE_KW, NIGHT, days=2)
    assert r.hours_fully_served == 10
    assert r.first_unserved_hour == 10
    assert r.final_soc == pytest.approx(0)

def test_solar_serves_daytime_load():
    r = simulate_outage(SystemConfig(solar_kw=2, battery_kwh=0), ONE_KW, [1.0] * 24)
    assert r.total_unserved_kwh == 0

def test_reject_wrong_profile_length():
    with pytest.raises(ValueError):
        simulate_outage(SystemConfig(), [1] * 23, NIGHT)

def test_reject_negative_fuel():
    with pytest.raises(ValueError):
        simulate_outage(SystemConfig(), ONE_KW, NIGHT, generator_fuel_available_liters=-1)

def test_reject_zero_days():
    with pytest.raises(ValueError):
        simulate_outage(SystemConfig(), ONE_KW, NIGHT, days=0)

def test_zero_demand():
    r = simulate_outage(SystemConfig(solar_kw=0, battery_kwh=0), [0] * 24, NIGHT)
    assert r.fraction_demand_served == 1
    assert r.first_unserved_hour is None
