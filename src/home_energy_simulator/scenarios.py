"""Portable, validated JSON scenario files. No server-side user storage."""
import json
from dataclasses import asdict, dataclass
from math import isfinite
from .model import SystemConfig

SCHEMA_VERSION = 1
MAX_BYTES = 100_000


@dataclass(frozen=True)
class Scenario:
    name: str
    config: SystemConfig
    loads_kw: list[float]
    sun_factors: list[float]
    days: int = 3

    def __post_init__(self):
        if not isinstance(self.name, str) or not 1 <= len(self.name.strip()) <= 100:
            raise ValueError("Scenario name must be 1–100 characters")
        if type(self.days) is not int or not 1 <= self.days <= 365:
            raise ValueError("Days must be between 1 and 365")
        if len(self.loads_kw) != 24 or len(self.sun_factors) != 24:
            raise ValueError("Profiles must contain 24 hourly values")
        if any(type(v) not in (int, float) or not isfinite(v) or v < 0
               for v in self.loads_kw):
            raise ValueError("Loads must be finite nonnegative numbers")
        if any(type(v) not in (int, float) or not isfinite(v) or not 0 <= v <= 1
               for v in self.sun_factors):
            raise ValueError("Sun factors must be finite values between 0 and 1")
        values = asdict(self.config)
        if any(type(v) not in (int, float, bool) or
               (type(v) is not bool and not isfinite(v)) for v in values.values()):
            raise ValueError("Configuration must contain finite numbers")


def scenario_to_json(scenario: Scenario) -> str:
    return json.dumps({"schema_version": SCHEMA_VERSION, "name": scenario.name,
                       "config": asdict(scenario.config), "loads_kw": scenario.loads_kw,
                       "sun_factors": scenario.sun_factors, "days": scenario.days},
                      indent=2, allow_nan=False)


def scenario_from_json(data: str | bytes) -> Scenario:
    if isinstance(data, bytes):
        if len(data) > MAX_BYTES:
            raise ValueError("Scenario file too large")
        try:
            data = data.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("Scenario must be UTF-8 JSON") from exc
    if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Scenario file too large or invalid")
    try:
        obj = json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON value")))
        if not isinstance(obj, dict) or obj.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported scenario schema version")
        raw = obj["config"]
        if not isinstance(raw, dict) or set(raw) != set(SystemConfig.__dataclass_fields__):
            raise ValueError("Configuration fields do not match schema")
        for key, field in SystemConfig.__dataclass_fields__.items():
            if key in ("generator_enabled", "grid_available"):
                if type(raw[key]) is not bool:
                    raise ValueError("Boolean configuration field required")
            elif type(raw[key]) not in (int, float) or not isfinite(raw[key]):
                raise ValueError("Numeric configuration field must be finite")
        return Scenario(name=obj["name"], config=SystemConfig(**raw),
                        loads_kw=obj["loads_kw"], sun_factors=obj["sun_factors"],
                        days=obj["days"])
    except (KeyError, TypeError, json.JSONDecodeError, OverflowError) as exc:
        raise ValueError("Invalid scenario JSON structure") from exc
