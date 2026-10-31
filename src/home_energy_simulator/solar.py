"""Transparent clear-sky-inspired PV estimation, not measured weather data."""
from dataclasses import dataclass
from datetime import date
from math import acos, asin, cos, pi, radians, sin

@dataclass(frozen=True)
class SolarConfig:
    latitude_deg: float = 34.27
    longitude_deg: float = -88.41
    array_kw: float = 4.8
    tilt_deg: float = 30.0
    azimuth_deg: float = 180.0  # 180 = south, 90 = east
    performance_ratio: float = 0.80
    cloud_factor: float = 1.0

    def __post_init__(self):
        if not -90 <= self.latitude_deg <= 90:
            raise ValueError("Latitude out of range")
        if not -180 <= self.longitude_deg <= 180:
            raise ValueError("Longitude out of range")
        if self.array_kw < 0 or not 0 <= self.tilt_deg <= 90:
            raise ValueError("Invalid array size or tilt")
        if not 0 <= self.azimuth_deg <= 360:
            raise ValueError("Azimuth out of range")
        if not 0 <= self.performance_ratio <= 1 or not 0 <= self.cloud_factor <= 1:
            raise ValueError("Factors must be between 0 and 1")

def hourly_pv_kw(config: SolarConfig, day: date) -> list[float]:
    """24 approximate hourly AC power values in local solar time.

    Uses declination and solar-hour angle with a simple irradiance proxy.
    Assumes 1 kW/m² direct-normal clear-sky irradiance, no diffuse light,
    and fixed performance ratio. Not suitable for design or financial guarantees.
    """
    n = day.timetuple().tm_yday
    decl = radians(23.44 * sin(2 * pi * (284 + n) / 365))
    lat = radians(config.latitude_deg)
    tilt = radians(config.tilt_deg)
    az = radians(config.azimuth_deg)
    result = []
    for hour in range(24):
        angle = radians(15 * (hour + 0.5 - 12))
        east = -cos(decl) * sin(angle)
        north = cos(lat) * sin(decl) - sin(lat) * cos(decl) * cos(angle)
        up = sin(lat) * sin(decl) + cos(lat) * cos(decl) * cos(angle)
        incidence = up * cos(tilt) + (north * cos(az) + east * sin(az)) * sin(tilt)
        result.append(config.array_kw * config.performance_ratio *
                      config.cloud_factor * max(0.0, incidence) if up > 0 else 0.0)
    return result

def solar_factors(config: SolarConfig, day: date) -> list[float]:
    """Hourly factors compatible with the energy simulation engine."""
    if config.array_kw == 0:
        return [0.0] * 24
    return [min(1.0, x / config.array_kw) for x in hourly_pv_kw(config, day)]
