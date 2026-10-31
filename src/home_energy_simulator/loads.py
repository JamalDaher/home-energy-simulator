"""Configurable household appliance load profiles.

Hourly average demand is derived from rated running watts, quantity, operating
hours and duty fraction. No starting surges or correlated thermostat behavior.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Appliance:
    name: str
    running_watts: float
    quantity: int = 1
    start_hour: int = 0
    end_hour: int = 24
    duty_cycle: float = 1.0

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Appliance name cannot be blank")
        if not isfinite(self.running_watts) or self.running_watts < 0:
            raise ValueError("Running watts must be finite and nonnegative")
        if type(self.quantity) is not int or self.quantity < 1:
            raise ValueError("Quantity must be a positive integer")
        if not (0 <= self.start_hour < 24 and 0 <= self.end_hour <= 24):
            raise ValueError("Hours must be between 0 and 24")
        if self.start_hour == self.end_hour:
            raise ValueError("Start and end cannot match; use 0 to 24 for all day")
        if not isfinite(self.duty_cycle) or not 0 <= self.duty_cycle <= 1:
            raise ValueError("Duty cycle must be between 0 and 1")

    def active_at(self, hour: int) -> bool:
        if not 0 <= hour < 24:
            raise ValueError("Hour must be from 0 to 23")
        if self.start_hour < self.end_hour:
            return self.start_hour <= hour < self.end_hour
        return hour >= self.start_hour or hour < self.end_hour

    @property
    def active_kw(self) -> float:
        return self.running_watts * self.quantity * self.duty_cycle / 1000


def hourly_load_kw(appliances: list[Appliance]) -> list[float]:
    """Return 24 hourly average demand values in kW."""
    return [
        sum(appliance.active_kw for appliance in appliances if appliance.active_at(hour))
        for hour in range(24)
    ]


def daily_energy_kwh(appliances: list[Appliance]) -> float:
    return sum(hourly_load_kw(appliances))


def default_appliances() -> list[Appliance]:
    """Illustrative electric-home defaults; replace with measured equipment data."""
    return [
        Appliance("Central AC / heat pump", 3500, start_hour=8, end_hour=23, duty_cycle=0.45),
        Appliance("Refrigerator", 150, duty_cycle=0.40),
        Appliance("Freezer", 120, duty_cycle=0.45),
        Appliance("Electric water heater", 4500, start_hour=6, end_hour=9, duty_cycle=0.25),
        Appliance("Electric range / cooking", 2000, start_hour=17, end_hour=19, duty_cycle=0.40),
        Appliance("Lighting", 200, start_hour=17, end_hour=23, duty_cycle=0.75),
        Appliance("Internet / electronics", 100),
        Appliance("Laundry", 1200, start_hour=12, end_hour=14, duty_cycle=0.50),
    ]
