"""Educational HVAC starting-surge and backup-source screening.

This checks nominal running and transient power only, not voltage dip,
alternator response, compressor locked-rotor behavior or safe interconnection.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class HVACLoad:
    running_kw: float = 3.5
    starting_multiplier: float = 3.0
    soft_start_reduction: float = 0.0

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.running_kw, self.starting_multiplier, self.soft_start_reduction)):
            raise ValueError("Inputs must be finite")
        if self.running_kw < 0 or self.starting_multiplier < 1:
            raise ValueError("Running power must be nonnegative and multiplier >= 1")
        if not 0 <= self.soft_start_reduction <= 1:
            raise ValueError("Soft-start reduction must be between 0 and 1")

    @property
    def starting_kw(self) -> float:
        return self.running_kw * self.starting_multiplier

    @property
    def soft_start_kw(self) -> float:
        # Reduction applies only to incremental surge, never below running power.
        return self.running_kw + (self.starting_kw - self.running_kw) * (1 - self.soft_start_reduction)


@dataclass(frozen=True)
class SourceRating:
    running_kw: float
    surge_kw: float

    def __post_init__(self):
        if not isfinite(self.running_kw) or not isfinite(self.surge_kw):
            raise ValueError("Source ratings must be finite")
        if self.running_kw < 0 or self.surge_kw < self.running_kw:
            raise ValueError("Surge rating must be at least running rating >= 0")


@dataclass(frozen=True)
class SizingResult:
    required_running_kw: float
    required_start_kw: float
    running_margin_kw: float
    starting_margin_kw: float
    running_fits: bool
    starting_fits: bool

    @property
    def nominally_fits(self) -> bool:
        return self.running_fits and self.starting_fits


def evaluate_hvac(
    hvac: HVACLoad,
    source: SourceRating,
    other_running_kw: float = 0.0,
    use_soft_start: bool = False,
) -> SizingResult:
    """Assume HVAC starts while other loads are already running.

    Do not combine generator and inverter ratings; evaluate each separately.
    """
    if not isfinite(other_running_kw) or other_running_kw < 0:
        raise ValueError("Other running load must be finite and nonnegative")
    required_running = other_running_kw + hvac.running_kw
    required_start = other_running_kw + (hvac.soft_start_kw if use_soft_start else hvac.starting_kw)
    return SizingResult(
        required_running_kw=required_running,
        required_start_kw=required_start,
        running_margin_kw=source.running_kw - required_running,
        starting_margin_kw=source.surge_kw - required_start,
        running_fits=required_running <= source.running_kw,
        starting_fits=required_start <= source.surge_kw,
    )
