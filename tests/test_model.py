"""Unit tests for energy flow and input validation."""
import pytest
from home_energy_simulator import SystemConfig, demo_profiles, simulate, totals

def test_demo_profile_is_24_hours():
    loads, sun = demo_profiles()
    assert len(loads) == len(sun) == 24

def test_solar_serves_load():
    rows = simulate(SystemConfig(solar_kw=2, battery_kwh=0), [1], [1])
    assert rows[0]["solar_used_kwh"] == 1
    assert rows[0]["unmet_kwh"] == 0

def test_no_generation_unserved():
    rows = simulate(SystemConfig(solar_kw=0, battery_kwh=0), [2], [0])
    assert rows[0]["unmet_kwh"] == 2

def test_generator_serves_remaining_load():
    cfg = SystemConfig(solar_kw=0, battery_kwh=0, generator_kw=3, generator_enabled=True)
    assert simulate(cfg, [2], [0])[0]["generator_kwh"] == 2

def test_grid_serves_remaining_load():
    cfg = SystemConfig(solar_kw=0, battery_kwh=0, grid_available=True)
    assert simulate(cfg, [2], [0])[0]["grid_kwh"] == 2

def test_battery_respects_minimum_soc():
    cfg = SystemConfig(solar_kw=0, battery_kwh=10, initial_soc=0.5, minimum_soc=0.1)
    row = simulate(cfg, [20], [0])[0]
    assert row["soc"] >= 0.1 - 1e-9

def test_reject_invalid_profiles():
    with pytest.raises(ValueError):
        simulate(SystemConfig(), [1], [0, 1])

def test_totals_match_demand():
    rows = simulate(SystemConfig(), *demo_profiles())
    assert totals(rows)["demand_kwh"] == pytest.approx(sum(r["demand_kwh"] for r in rows), abs=0.001)
