"""Series/parallel LiFePO4 bank sizing and nominal energy estimates."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BatteryBank:
    module_voltage: float = 12.8
    module_ah: float = 280.0
    series: int = 4
    parallel: int = 1
    usable_depth_of_discharge: float = 0.80
    inverter_efficiency: float = 0.92
    module_max_discharge_a: float = 100.0

    def __post_init__(self):
        if self.module_voltage <= 0 or self.module_ah <= 0 or self.module_max_discharge_a <= 0:
            raise ValueError("Module ratings must be positive")
        if type(self.series) is not int or type(self.parallel) is not int or self.series < 1 or self.parallel < 1:
            raise ValueError("Series and parallel counts must be positive integers")
        if not 0 < self.usable_depth_of_discharge <= 1 or not 0 < self.inverter_efficiency <= 1:
            raise ValueError("Fractions must be between 0 and 1")

    @property
    def nominal_voltage(self):
        return self.module_voltage * self.series

    @property
    def capacity_ah(self):
        return self.module_ah * self.parallel

    @property
    def module_count(self):
        return self.series * self.parallel

    @property
    def nominal_energy_kwh(self):
        return self.nominal_voltage * self.capacity_ah / 1000

    @property
    def usable_ac_energy_kwh(self):
        return self.nominal_energy_kwh * self.usable_depth_of_discharge * self.inverter_efficiency

    @property
    def nominal_dc_power_limit_kw(self):
        return self.nominal_voltage * self.module_max_discharge_a * self.parallel / 1000

    def runtime_hours(self, load_kw: float) -> float:
        if load_kw <= 0:
            raise ValueError("Load must be positive")
        if load_kw > self.nominal_dc_power_limit_kw * self.inverter_efficiency:
            raise ValueError("Load exceeds estimated battery discharge power limit")
        return self.usable_ac_energy_kwh / load_kw

    def summary(self):
        return {
            "module_count": self.module_count,
            "nominal_voltage_v": round(self.nominal_voltage, 2),
            "capacity_ah": round(self.capacity_ah, 2),
            "nominal_energy_kwh": round(self.nominal_energy_kwh, 3),
            "usable_ac_energy_kwh": round(self.usable_ac_energy_kwh, 3),
            "nominal_dc_power_limit_kw": round(self.nominal_dc_power_limit_kw, 3),
        }
