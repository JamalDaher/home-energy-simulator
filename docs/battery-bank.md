# Battery bank designer

The battery bank module models a series/parallel arrangement of identical LiFePO4 modules.

Example: four 12.8 V, 280 Ah modules in series yield 51.2 V nominal, 280 Ah and 14.336 kWh nominal stored energy. With 80% usable depth of discharge and 92% inverter efficiency, estimated usable AC energy is approximately 10.55 kWh.

## Assumptions and safety

- Calculations use nominal voltage; actual voltage changes with state of charge and load.
- Runtime assumes constant AC load and efficiency. It excludes inverter idle losses, temperature, aging, voltage sag and surge demands.
- The DC power estimate uses the module discharge current rating, not wiring, fuses or inverter ratings.
- **Do not assume that 12 V batteries can be placed in series.** Manufacturer approval for series operation, matched modules, BMS compatibility, appropriate protection and an electrician's design review are required.
- This is an educational sizing tool, not wiring or installation guidance.
