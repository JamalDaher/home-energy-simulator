# Home Energy Simulator

[**Launch Live Demo**](https://home-energy-simulator.streamlit.app) · [**GitHub Release v1.0.0**](https://github.com/JamalDaher/home-energy-simulator/releases/tag/v1.0.0)

**Version 1.0** — Python engineering portfolio application for exploring residential solar, LiFePO4 battery storage, generators and power-outage resilience.

## Features

- Hourly solar/battery/generator dispatch with state-of-charge tracking
- Seasonal solar geometry and editable household appliance schedules
- Battery bank design, HVAC starting-load screening, generator fuel/runtime estimates
- Multi-day outage modeling and load-dependent generator fuel consumption
- Discrete solar/battery/generator capacity comparison by modeled cost and energy served
- Interactive Streamlit charts, CSV exports, portable JSON scenarios and PDF outage reports
- Python CLI, automated pytest suite and GitHub Actions CI

## Quick start

Python 3.10+ required.

```bash
python -m venv .venv
# Activate your virtual environment, then:
python -m pip install -e ".[web,dev]"
python -m streamlit run app.py
```

CLI example:

```bash
home-energy --solar-kw 4.8 --battery-kwh 14 --generator --generator-kw 5
```

Run tests:

```bash
python -m pytest -q
```

## Example study

Model a 4.8 kW solar array, 14 kWh battery and 5 kW generator across a three-day outage. Edit appliance schedules and sunlight assumptions, compare generator fuel budgets, then use **System Optimization** to rank candidate system sizes. Save a scenario JSON snapshot and download a PDF summary from **Scenario Workspace & PDF Reports**.

The scenario workspace's PDF currently uses the unlimited-fuel legacy outage simulation; the separate fuel-aware outage panel provides finite-inventory analysis. See [v1 release guide](docs/v1-release.md) and [optimization assumptions](docs/system-optimization.md).

## Repository layout

- `app.py` — Streamlit dashboard
- `src/home_energy_simulator/` — tested simulation and reporting modules
- `tests/` — unit and regression tests
- `docs/` — modeling notes and release guide
- `.github/workflows/ci.yml` — automated test workflow

## Limitations

This is a **scenario-analysis and educational tool**, not a validated electrical design, equipment-sizing certification, weather forecast, financial investment model, or installation guide. Hourly averaged loads cannot represent motor-start surges, generator transients, BMS restrictions or wiring/transfer safety. Costs and fuel rates are user assumptions. The percentage of energy served in one simulated outage is **not** a probability of reliability.

## License

MIT. See [LICENSE](LICENSE).
