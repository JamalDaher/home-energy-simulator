import json
import pytest
from home_energy_simulator.model import SystemConfig
from home_energy_simulator.scenarios import Scenario, scenario_to_json, scenario_from_json


def sample():
    return Scenario("Backup study", SystemConfig(solar_kw=4.8), [1.0] * 24,
                    [0.5] * 24, days=2)


def test_roundtrip():
    assert scenario_from_json(scenario_to_json(sample())) == sample()
    assert scenario_from_json(scenario_to_json(sample()).encode()) == sample()


def test_reject_unsupported_version():
    data = json.loads(scenario_to_json(sample()))
    data["schema_version"] = 99
    with pytest.raises(ValueError):
        scenario_from_json(json.dumps(data))


def test_reject_bad_profiles():
    with pytest.raises(ValueError):
        Scenario("bad", SystemConfig(), [1] * 23, [0] * 24)
    with pytest.raises(ValueError):
        Scenario("bad", SystemConfig(), [1] * 24, [float("nan")] * 24)


def test_reject_invalid_name_and_days():
    with pytest.raises(ValueError):
        Scenario("", SystemConfig(), [1] * 24, [0] * 24)
    with pytest.raises(ValueError):
        Scenario("name", SystemConfig(), [1] * 24, [0] * 24, days=0)


def test_reject_unknown_config_fields():
    data = json.loads(scenario_to_json(sample()))
    data["config"]["extra"] = 2
    with pytest.raises(ValueError):
        scenario_from_json(json.dumps(data))


def test_reject_nonfinite_config():
    data = json.loads(scenario_to_json(sample()))
    data["config"]["solar_kw"] = float("nan")
    with pytest.raises(ValueError):
        scenario_from_json(json.dumps(data))


def test_reject_large_file():
    with pytest.raises(ValueError):
        scenario_from_json(b"x" * 100001)


def test_reject_invalid_json():
    with pytest.raises(ValueError):
        scenario_from_json("{")
