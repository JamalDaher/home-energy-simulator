# Generator fuel and runtime calculator (v0.7)

Estimates fuel consumption from a user-entered generator continuous power rating, idle fuel consumption and full-load fuel consumption. A **linear interpolation** estimates consumption at a chosen steady load. This is a simplified planning assumption, not a calibrated generator efficiency curve.

Supported fuels and units:
- Gasoline: gallons
- Propane: gallons (liquid volume)
- Natural gas: cubic feet

Enter rates and prices for the **same selected unit**. Rates are not automatically converted between fuels, and there are no built-in manufacturer claims. Price and available fuel are optional. The calculator estimates hours of continuous operation, fuel required, fuel cost and inventory-limited runtime.

Natural gas service is normally continuous rather than a stored tank: leave available inventory unchecked to estimate consumption and cost without a finite-runtime claim. For gasoline/propane, usable stored fuel may be less than nominal capacity.

This independent steady-state calculator does **not** yet alter the existing multi-day outage dispatch, which retains its separate fixed liters/hour model. Actual generator performance depends on load, altitude, temperature, fuel type, maintenance, transient behavior and manufacturer specifications. Never connect a portable generator to household wiring without professionally installed transfer equipment.
