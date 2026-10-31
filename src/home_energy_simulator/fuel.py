"""Load-dependent fuel use and runtime estimates for a generator.

All rates are user-supplied illustrative inputs, not manufacturer specifications.
"""
from dataclasses import dataclass
from math import isfinite


FUEL_UNITS = {"gasoline": "gallons", "propane": "gallons", "natural_gas": "cubic feet"}


@dataclass(frozen=True)
class FuelModel:
    fuel_type: str
    generator_rated_kw: float
    idle_rate_per_hour: float
    full_load_rate_per_hour: float
    price_per_unit: float = 0.0

    def __post_init__(self):
        if self.fuel_type not in FUEL_UNITS:
            raise ValueError("Unsupported fuel type")
        values = (self.generator_rated_kw, self.idle_rate_per_hour,
                  self.full_load_rate_per_hour, self.price_per_unit)
        if not all(isfinite(v) for v in values):
            raise ValueError("All inputs must be finite")
        if self.generator_rated_kw <= 0 or min(values[1:]) < 0:
            raise ValueError("Rated power must be positive and rates/prices nonnegative")
        if self.full_load_rate_per_hour < self.idle_rate_per_hour:
            raise ValueError("Full-load fuel rate must not be below idle fuel rate")

    @property
    def unit(self) -> str:
        return FUEL_UNITS[self.fuel_type]

    def rate_at_load(self, output_kw: float) -> float:
        """Linear interpolation between idle and rated output, inclusive."""
        if not isfinite(output_kw) or not 0 <= output_kw <= self.generator_rated_kw:
            raise ValueError("Output must be within generator continuous rating")
        fraction = output_kw / self.generator_rated_kw
        return self.idle_rate_per_hour + fraction * (
            self.full_load_rate_per_hour - self.idle_rate_per_hour
        )

    def estimate(self, output_kw: float, hours: float, fuel_available: float | None = None) -> dict:
        if not isfinite(hours) or hours < 0:
            raise ValueError("Hours must be finite and nonnegative")
        if fuel_available is not None and (not isfinite(fuel_available) or fuel_available < 0):
            raise ValueError("Fuel available must be finite and nonnegative")
        rate = self.rate_at_load(output_kw)
        consumed = rate * hours
        runtime = None if fuel_available is None or rate == 0 else fuel_available / rate
        supplied_hours = hours if fuel_available is None or rate == 0 else min(hours, runtime)
        return {
            "fuel_rate_per_hour": rate,
            "fuel_needed": consumed,
            "fuel_cost": consumed * self.price_per_unit,
            "available_runtime_hours": runtime,
            "supplied_hours": supplied_hours,
            "fuel_used_with_inventory": rate * supplied_hours,
            "cost_with_inventory": rate * supplied_hours * self.price_per_unit,
        }
