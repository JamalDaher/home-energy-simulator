"""Battery bank arithmetic and safety-boundary tests."""
import pytest
from home_energy_simulator.battery import BatteryBank

def test_four_12v_modules_form_51_2v_bank():
    bank = BatteryBank()
    assert bank.nominal_voltage == pytest.approx(51.2)

def test_four_modules_nominal_energy():
    assert BatteryBank().nominal_energy_kwh == pytest.approx(14.336)

def test_parallel_doubles_capacity():
    a = BatteryBank(parallel=1)
    b = BatteryBank(parallel=2)
    assert b.capacity_ah == 2 * a.capacity_ah
    assert b.module_count == 2 * a.module_count

def test_usable_energy_less_than_nominal():
    bank = BatteryBank()
    assert bank.usable_ac_energy_kwh < bank.nominal_energy_kwh

def test_runtime_at_1kw():
    bank = BatteryBank()
    assert bank.runtime_hours(1) == pytest.approx(bank.usable_ac_energy_kwh)

def test_reject_zero_load():
    with pytest.raises(ValueError):
        BatteryBank().runtime_hours(0)

def test_reject_oversized_load():
    with pytest.raises(ValueError):
        BatteryBank().runtime_hours(100)

def test_reject_invalid_count():
    with pytest.raises(ValueError):
        BatteryBank(series=0)

def test_reject_fractional_count():
    with pytest.raises(ValueError):
        BatteryBank(series=1.5)

def test_reject_invalid_efficiency():
    with pytest.raises(ValueError):
        BatteryBank(inverter_efficiency=1.1)
