# Home Energy Simulator v1.0 — portfolio release

## Capabilities
- Hourly solar, battery, generator and grid dispatch
- LiFePO4 bank sizing, household appliance load design, HVAC startup screening
- Multi-day outage simulation, optional load-dependent generator fuel estimates
- Discrete capacity/cost optimization with scenario-specific energy-served target
- Portable scenario JSON snapshots and downloadable PDF outage summaries

## Scenario workflow
1. Run `python -m streamlit run app.py` and configure the system in the sidebar and household loads.
2. In **Scenario Workspace & PDF Reports**, enter a name and download a JSON snapshot.
3. Upload that JSON file to reproduce its original load and solar profile in an independent outage run. The uploaded scenario does **not** change current sidebar widgets.
4. Download the PDF report or inspect the chart.

**Scope:** Scenario JSON v1 stores the system configuration, 24 hourly loads, 24 hourly sun factors and number of days. It does not yet store fuel-model settings, optimization candidates or original appliance rows. The PDF workspace uses the unlimited-fuel legacy outage mode. Fuel-limited results remain in the dedicated integrated outage panel.

## Engineering assumptions
These are educational calculations with hourly average inputs and repeated daily profiles. The software does not calculate electrical code compliance, motor transients, true weather variability, battery BMS limits, transfer-switch design, lifecycle costs or statistically validated reliability. Do not use it to specify equipment or install a power system without professional review.

## Quality gates
`python -m pytest -q` runs automated regression tests in GitHub Actions. Use `pip install -e ".[web,dev]"` for the dashboard and development dependencies. No persistent database or remote storage is used for scenario files.
