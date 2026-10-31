# System optimization (v0.9)

An exhaustive, deterministic **scenario comparison**, not an electrical system design or globally optimal sizing method. The search evaluates combinations of solar kW, battery kWh and generator kW using the existing hourly outage simulator. It ranks candidates meeting the requested fraction of energy served by lowest modeled capital + outage fuel cost. Candidates below the target follow, sorted by fraction served (highest first). The target measures **energy served**, not probability of survival or statistical reliability.

The capital model uses user-entered linear $/kW solar, $/kWh battery and $/kW generator assumptions. The fuel cost covers **one modeled outage**; no lifetime, maintenance, installation fixed costs, degradation, financing, replacement, taxes or grid-bill savings are included. Solar profiles are repeated daily and are not weather forecasts. No physical constraints, inverter resizing, generator charging, motor surge or installation approvals are optimized.

Candidate generation uses user-selected discrete capacity steps, deduplicates values and rejects more than 2,000 combinations by default. All candidates share the baseline inverter, battery charge limits and efficiencies. An optional fuel model can be used with fuel inventory; its rated kW must cover every generator candidate. With no fuel model, generator operation has no modeled fuel cost or inventory limit, which may make generator configurations appear unrealistically cheap.

Use the Streamlit System Optimization panel to edit ranges, capital assumptions and the energy-served target. Review both the recommended feasible candidate and the full comparison table before interpreting results.
