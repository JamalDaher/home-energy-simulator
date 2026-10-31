"""Multi-day outage simulation using the hourly dispatch engine.

All input loads and solar factors are hourly average values; each step is one hour.
"""
from dataclasses import dataclass
from .model import SystemConfig, simulate, totals
from .fuel import FuelModel
from math import isfinite

@dataclass(frozen=True)
class OutageResult:
    hours_simulated: int
    hours_fully_served: int
    first_unserved_hour: int | None
    total_unserved_kwh: float
    fraction_demand_served: float
    generator_hours: int
    generator_fuel_liters: float
    final_soc: float
    rows: list[dict]
    generator_fuel_used: float = 0.0
    generator_fuel_remaining: float | None = None
    generator_fuel_unit: str = "liters"
    generator_fuel_cost: float = 0.0

def simulate_outage(
    config: SystemConfig,
    daily_load_kw: list[float],
    daily_sun_factors: list[float],
    days: int = 3,
    generator_fuel_liters_per_hour: float = 0.0,
    generator_fuel_available_liters: float | None = None,
    fuel_model: FuelModel | None = None,
    fuel_available: float | None = None,
) -> OutageResult:
    """Repeat 24-hour profiles and track generator fuel and battery SOC.

    Fuel burn is a fixed rate whenever the generator delivers energy, not a
    load-dependent fuel curve. A partially sufficient final hour of fuel is
    treated as unavailable. Grid is forcibly disabled.
    """
    if type(days) is not int or days < 1 or days > 365:
        raise ValueError("Days must be an integer from 1 to 365")
    if len(daily_load_kw) != 24 or len(daily_sun_factors) != 24:
        raise ValueError("Provide exactly 24 hourly load and sunlight values")
    if generator_fuel_liters_per_hour < 0:
        raise ValueError("Fuel consumption must not be negative")
    if generator_fuel_available_liters is not None and generator_fuel_available_liters < 0:
        raise ValueError("Fuel available must not be negative")
    if fuel_model is not None:
        if config.generator_enabled and config.generator_kw > fuel_model.generator_rated_kw:
            raise ValueError("Generator power exceeds the fuel model rated power")
        if fuel_available is not None and (not isfinite(fuel_available) or fuel_available < 0):
            raise ValueError("Fuel inventory must be finite and nonnegative")
    # Reuse dispatch model one hour at a time to carry SOC across days.
    stored_soc = config.initial_soc if config.battery_kwh > 0 else 0.0
    remaining_fuel = fuel_available if fuel_model is not None else generator_fuel_available_liters
    total_fuel_used = 0.0
    rows = []
    gen_hours = 0
    for hour in range(days * 24):
        fuel_per_hour = generator_fuel_liters_per_hour
        can_run = config.generator_enabled and config.generator_kw > 0
        if fuel_model is None:
            if remaining_fuel is not None and fuel_per_hour > 0:
                can_run = can_run and remaining_fuel + 1e-10 >= fuel_per_hour
            elif remaining_fuel is not None and fuel_per_hour == 0:
                can_run = False  # finite fuel requires an explicit burn rate
        step_config = SystemConfig(
            solar_kw=config.solar_kw,
            battery_kwh=config.battery_kwh,
            minimum_soc=config.minimum_soc if config.battery_kwh > 0 else 0.0,
            initial_soc=max(config.minimum_soc, stored_soc) if config.battery_kwh > 0 else 0.0,
            charge_efficiency=config.charge_efficiency,
            discharge_efficiency=config.discharge_efficiency,
            inverter_kw=config.inverter_kw,
            generator_kw=config.generator_kw,
            generator_enabled=can_run,
            grid_available=False,
        )
        hour_load = daily_load_kw[hour % 24]
        hour_sun = daily_sun_factors[hour % 24]
        step = simulate(step_config, [hour_load], [hour_sun])[0]
        if fuel_model is not None and step["generator_kwh"] > 0:
            required_fuel = fuel_model.rate_at_load(step["generator_kwh"])
            if remaining_fuel is not None and required_fuel > remaining_fuel + 1e-10:
                # No partial-hour generation: recompute dispatch without generator.
                step_config = SystemConfig(
                    solar_kw=config.solar_kw, battery_kwh=config.battery_kwh,
                    minimum_soc=config.minimum_soc if config.battery_kwh > 0 else 0.0,
                    initial_soc=max(config.minimum_soc, stored_soc) if config.battery_kwh > 0 else 0.0,
                    charge_efficiency=config.charge_efficiency,
                    discharge_efficiency=config.discharge_efficiency,
                    inverter_kw=config.inverter_kw, generator_kw=config.generator_kw,
                    generator_enabled=False, grid_available=False,
                )
                step = simulate(step_config, [hour_load], [hour_sun])[0]
        hour_fuel = (fuel_model.rate_at_load(step["generator_kwh"])
                     if fuel_model is not None and step["generator_kwh"] > 0
                     else fuel_per_hour if step["generator_kwh"] > 0 else 0.0)
        total_fuel_used += hour_fuel
        stored_soc = step["soc"]
        if step["generator_kwh"] > 0:
            gen_hours += 1
            if remaining_fuel is not None:
                remaining_fuel = max(0.0, remaining_fuel - hour_fuel)
        step["hour"] = hour
        step["day"] = hour // 24 + 1
        step["generator_fuel_used"] = hour_fuel
        step["generator_fuel_remaining"] = remaining_fuel
        rows.append(step)
    summary = totals(rows)
    demand = summary["demand_kwh"]
    first = next((r["hour"] for r in rows if r["unmet_kwh"] > 1e-9), None)
    return OutageResult(
        hours_simulated=len(rows),
        hours_fully_served=sum(r["unmet_kwh"] <= 1e-9 for r in rows),
        first_unserved_hour=first,
        total_unserved_kwh=summary["unmet_kwh"],
        fraction_demand_served=max(0.0, min(1.0, 1 - summary["unmet_kwh"] / demand)) if demand else 1.0,
        generator_hours=gen_hours,
        generator_fuel_liters=round(gen_hours * generator_fuel_liters_per_hour, 3),
        final_soc=stored_soc,
        rows=rows,
        generator_fuel_used=round(total_fuel_used, 3),
        generator_fuel_remaining=remaining_fuel,
        generator_fuel_unit=fuel_model.unit if fuel_model is not None else "liters",
        generator_fuel_cost=round(total_fuel_used * fuel_model.price_per_unit, 2) if fuel_model is not None else 0.0,
    )
