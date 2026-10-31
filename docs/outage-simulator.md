# Whole-home outage simulator (v0.4)

The outage engine repeats a 24-hour hourly-average load profile and solar profile for a selected number of days (1–365). It reuses the existing solar/battery/generator dispatch model while carrying battery state of charge forward across hours and days. The grid is forced off.

## Outputs
- Hours with all modeled demand supplied
- First hour with unmet demand (zero-indexed in API)
- Total unmet energy and fraction of demand supplied
- Generator operating hours and estimated fuel consumed
- Hourly dispatch records for charting and CSV export

## Important limitations
- Load profile is synthetic, not measured household usage; solar profile is approximate geometry rather than forecast weather.
- Fuel burn is a **constant liters/hour when producing energy**, not a manufacturer fuel curve. Fuel capacity is optional in the API; dashboard specifies a finite supply.
- Fuel below one complete running-hour is treated as unavailable. There is no generator startup delay, fuel reserve, minimum loading, or automatic transfer behavior.
- Battery charge and discharge are bounded by the existing hourly engine, which does not model all real inverter or BMS constraints.
- No HVAC compressor startup surge or simultaneous peak loads. **Do not use these estimates to size a real transfer switch, generator wiring, or protective devices.** Consult a licensed electrician and equipment documentation.
