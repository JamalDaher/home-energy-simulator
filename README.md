# Home Energy Simulator

An open-source Python portfolio project for modeling hourly residential solar generation, battery storage, generator backup, and grid electricity.

## Features

- Deterministic hourly energy dispatch: solar → battery → generator → grid
- Battery capacity, minimum state-of-charge, inverter limit, and round-trip losses
- Streamlit dashboard with charts and downloadable CSV
- Command-line interface with JSON summary
- Automated unit tests and GitHub Actions CI

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -e ".[web,dev]"
# macOS/Linux:
.venv/bin/python -m pip install -e ".[web,dev]"
```

Run the dashboard:

```bash
python -m streamlit run app.py
```

Run a CLI simulation:

```bash
home-energy --solar-kw 4.8 --battery-kwh 14 --generator --generator-kw 5
```

Run tests:

```bash
python -m pytest -q
```

## Repository layout

```text
app.py                           Streamlit UI
src/home_energy_simulator/       Simulation engine and CLI
tests/                           Unit tests
.github/workflows/ci.yml         GitHub Actions test workflow
pyproject.toml                   Python package configuration
```

## Modeling assumptions

Each step represents one hour. All power ratings are in kW and energy flows are in kWh. Solar availability and load profiles are synthetic illustrative inputs, not actual weather or household measurements. The generator is dispatched only after available solar and battery energy. The grid, if enabled, supplies any remaining demand. Battery charge/discharge efficiency is applied separately. This is not an electrical engineering installation design.

## Roadmap

- Weather-derived solar generation and seasonal scenarios
- Real CSV load profile uploads
- Generator fuel consumption and operating costs
- 48 V LiFePO4 battery configuration
- Outage resilience and Monte Carlo scenarios
- More rigorous validation and energy-balance testing

## License

MIT. See [LICENSE](LICENSE).
