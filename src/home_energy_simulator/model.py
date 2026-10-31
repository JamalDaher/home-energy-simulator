"""Hourly solar, battery, generator, and grid energy simulation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class SystemConfig:
    solar_kw: float = 4.8
    battery_kwh: float = 14.0
    minimum_soc: float = 0.1
    initial_soc: float = 0.5
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    inverter_kw: float = 5.0
    generator_kw: float = 0.0
    generator_enabled: bool = False
    grid_available: bool = False

    def __post_init__(self):
        if min(self.solar_kw, self.battery_kwh, self.inverter_kw, self.generator_kw) < 0:
            raise ValueError("Power and capacity cannot be negative")
        if not 0 <= self.minimum_soc <= self.initial_soc <= 1:
            raise ValueError("Invalid state-of-charge limits")
        if not 0 < self.charge_efficiency <= 1 or not 0 < self.discharge_efficiency <= 1:
            raise ValueError("Efficiencies must be between 0 (exclusive) and 1")

def demo_profiles():
    loads = [0.65]*6 + [1.1,1.4,1.2,1.0,0.9,1.0,1.2,1.3,1.2,1.1,1.5,2.1,2.8,2.6,2.1,1.6,1.1,0.8]
    sun = [0]*6 + [0.08,0.2,0.4,0.65,0.85,0.95,1,0.95,0.85,0.65,0.4,0.2,0.08] + [0]*5
    return loads, sun

def simulate(config, loads_kw, sun_factors):
    if len(loads_kw) != len(sun_factors):
        raise ValueError("Profiles must be equal length")
    if any(x < 0 for x in loads_kw) or any(not 0 <= x <= 1 for x in sun_factors):
        raise ValueError("Invalid profile values")
    stored = config.battery_kwh * config.initial_soc
    floor = config.battery_kwh * config.minimum_soc
    rows = []
    for hour, (load, factor) in enumerate(zip(loads_kw, sun_factors)):
        pv = config.solar_kw * factor
        direct = min(load, pv)
        remainder = load - direct
        battery = min(remainder, config.inverter_kw, max(0, stored-floor)*config.discharge_efficiency)
        stored -= battery/config.discharge_efficiency
        remainder -= battery
        generator = min(remainder, config.generator_kw) if config.generator_enabled else 0
        remainder -= generator
        grid = remainder if config.grid_available else 0
        remainder -= grid
        surplus = pv-direct
        charge = min(surplus, max(0,config.battery_kwh-stored)/config.charge_efficiency)
        stored += charge*config.charge_efficiency
        rows.append(dict(hour=hour,demand_kwh=load,solar_kwh=pv,solar_used_kwh=direct,
                         battery_delivered_kwh=battery,generator_kwh=generator,grid_kwh=grid,
                         unmet_kwh=max(0,remainder),curtailed_solar_kwh=surplus-charge,
                         soc=stored/config.battery_kwh if config.battery_kwh else 0))
    return rows

def totals(rows):
    keys = ("demand_kwh","solar_kwh","solar_used_kwh","battery_delivered_kwh",
            "generator_kwh","grid_kwh","unmet_kwh","curtailed_solar_kwh")
    return {key:round(sum(row[key] for row in rows),3) for key in keys}
