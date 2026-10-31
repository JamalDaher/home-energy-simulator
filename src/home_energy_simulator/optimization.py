"""Exhaustive, deterministic screening of candidate backup-energy configurations.

Costs are user assumptions, not quotes; reliability is for the selected outage
scenario only. The search never changes the dispatch model's physics.
"""
from dataclasses import dataclass, replace
from itertools import product
from math import isfinite

from .model import SystemConfig
from .outage import simulate_outage
from .fuel import FuelModel


@dataclass(frozen=True)
class UnitCosts:
    solar_per_kw: float
    battery_per_kwh: float
    generator_per_kw: float

    def __post_init__(self):
        if any(not isfinite(x) or x < 0 for x in (
            self.solar_per_kw, self.battery_per_kwh, self.generator_per_kw
        )):
            raise ValueError("Unit costs must be finite and nonnegative")


@dataclass(frozen=True)
class Candidate:
    solar_kw: float
    battery_kwh: float
    generator_kw: float
    capital_cost: float
    fuel_cost: float
    total_cost: float
    demand_served: float
    unmet_kwh: float
    generator_hours: int
    fuel_used: float


def optimize_system(
    baseline: SystemConfig,
    daily_load_kw: list[float],
    daily_sun_factors: list[float],
    solar_options: list[float],
    battery_options: list[float],
    generator_options: list[float],
    costs: UnitCosts,
    days: int = 3,
    min_demand_served: float = 0.99,
    fuel_model: FuelModel | None = None,
    fuel_available: float | None = None,
    max_candidates: int = 2000,
) -> list[Candidate]:
    """Return all candidates, feasible first, then least total modeled cost.

    Capital cost is proportional to installed capacity; fuel cost covers only
    this outage scenario. Infeasible candidates are sorted by reliability.
    """
    if not isfinite(min_demand_served) or not 0 <= min_demand_served <= 1:
        raise ValueError("Reliability target must be in [0, 1]")
    option_groups = (solar_options, battery_options, generator_options)
    if any(not options for options in option_groups):
        raise ValueError("Each candidate dimension must have at least one option")
    if any(not isfinite(x) or x < 0 for options in option_groups for x in options):
        raise ValueError("Candidate capacities must be finite and nonnegative")
    if not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError("max_candidates must be a positive integer")
    unique_groups = [sorted(set(options)) for options in option_groups]
    combinations = len(unique_groups[0]) * len(unique_groups[1]) * len(unique_groups[2])
    if combinations > max_candidates:
        raise ValueError("Candidate search exceeds max_candidates limit")
    if fuel_model is not None and max(unique_groups[2]) > fuel_model.generator_rated_kw:
        raise ValueError("Fuel model rating must cover every generator candidate")
    results = []
    for solar_kw, battery_kwh, generator_kw in product(*unique_groups):
        config = replace(
            baseline, solar_kw=solar_kw, battery_kwh=battery_kwh,
            generator_kw=generator_kw, generator_enabled=generator_kw > 0,
            initial_soc=baseline.initial_soc if battery_kwh > 0 else 0,
            minimum_soc=baseline.minimum_soc if battery_kwh > 0 else 0,
            grid_available=False,
        )
        outage = simulate_outage(
            config, daily_load_kw, daily_sun_factors, days=days,
            fuel_model=fuel_model, fuel_available=fuel_available,
        )
        capital = (solar_kw * costs.solar_per_kw
                   + battery_kwh * costs.battery_per_kwh
                   + generator_kw * costs.generator_per_kw)
        fuel_cost = outage.generator_fuel_cost
        results.append(Candidate(
            solar_kw=solar_kw, battery_kwh=battery_kwh, generator_kw=generator_kw,
            capital_cost=round(capital, 2), fuel_cost=fuel_cost,
            total_cost=round(capital + fuel_cost, 2),
            demand_served=outage.fraction_demand_served,
            unmet_kwh=outage.total_unserved_kwh,
            generator_hours=outage.generator_hours,
            fuel_used=outage.generator_fuel_used,
        ))
    return sorted(results, key=lambda c: (
        c.demand_served < min_demand_served,
        c.total_cost if c.demand_served >= min_demand_served else -c.demand_served,
        c.total_cost, c.solar_kw, c.battery_kwh, c.generator_kw,
    ))
