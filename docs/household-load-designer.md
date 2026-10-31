# Household Load Designer (v0.5)

The load designer produces a 24-hour average kW profile from an editable list of appliances. Each appliance has running watts, quantity, start and end hour, and duty cycle. End hour is exclusive; schedules may cross midnight. Use 00:00–24:00 for an all-day load.

The generated profile feeds both the existing daily dispatch chart and the multi-day outage simulator. The latter repeats the same daily schedule across all simulated days.

## Limitations
Defaults are **illustrative estimates**, not measurements of any particular home. Appliance running watts and duty cycle should be replaced with nameplate or measured data. A 45% duty cycle means the appliance contributes 45% of rated running power on average during scheduled hours, not that the appliance is physically operating at 45% power.

The hourly model **does not capture motor/compressor starting surge, coincident peaks, thermostat/weather effects, power factor, voltage drops, generator transient response, or load-shedding controls**. It is not suitable for selecting electrical equipment or making wiring decisions.
