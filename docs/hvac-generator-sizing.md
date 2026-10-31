# HVAC & generator sizing screen (v0.6)

This educational screen compares HVAC running power plus other simultaneously running loads against a source's continuous rating, and compares HVAC starting demand plus other running loads against the source's short-term surge rating.

Inputs:
- HVAC running kW and starting multiplier (illustrative defaults; **not** nameplate data)
- Optional soft-start reduction applied only to incremental startup surge
- Other simultaneously running loads in kW
- Generator continuous and surge kW, and inverter continuous and surge kW, evaluated separately

A positive margin is a nominal capacity headroom, **not proof that the equipment will start**. Actual starting characteristics require measured current or manufacturer's locked-rotor/start specifications, power factor, voltage, duration, motor load and the generator/inverter transient response. Soft-start performance is device- and installation-specific. No source synchronization, generator/inverter parallel operation, automatic transfer, wiring, breaker selection or electrical protection is modeled.

**Safety:** Never backfeed a house or connect a portable generator without properly installed, code-compliant transfer equipment. A qualified electrician should assess equipment compatibility and safe installation.
