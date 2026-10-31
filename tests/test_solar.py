"""Solar model validation and qualitative behavior."""
from datetime import date
import pytest
from home_energy_simulator.solar import SolarConfig, hourly_pv_kw, solar_factors

def test_24_nonnegative_hours():
    output = hourly_pv_kw(SolarConfig(), date(2026, 6, 21))
    assert len(output) == 24
    assert all(v >= 0 for v in output)

def test_nighttime_is_zero():
    output = hourly_pv_kw(SolarConfig(), date(2026, 6, 21))
    assert output[0] == output[23] == 0

def test_zero_array():
    assert hourly_pv_kw(SolarConfig(array_kw=0), date(2026, 6, 21)) == [0]*24

def test_clouds_reduce_generation():
    day = date(2026, 6, 21)
    clear = sum(hourly_pv_kw(SolarConfig(cloud_factor=1), day))
    cloudy = sum(hourly_pv_kw(SolarConfig(cloud_factor=0.5), day))
    assert cloudy == pytest.approx(clear * 0.5)

def test_summer_more_than_winter_at_mississippi_latitude():
    cfg = SolarConfig()
    assert sum(hourly_pv_kw(cfg, date(2026, 6, 21))) > sum(hourly_pv_kw(cfg, date(2026, 12, 21)))

def test_invalid_latitude():
    with pytest.raises(ValueError):
        SolarConfig(latitude_deg=91)

def test_factors_bounded():
    factors = solar_factors(SolarConfig(), date(2026, 6, 21))
    assert all(0 <= x <= 1 for x in factors)

def test_south_facing_beats_north_in_summer():
    day = date(2026, 6, 21)
    south = sum(hourly_pv_kw(SolarConfig(tilt_deg=35, azimuth_deg=180), day))
    north = sum(hourly_pv_kw(SolarConfig(tilt_deg=35, azimuth_deg=0), day))
    assert south > north
