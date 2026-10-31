"""Streamlit dashboard for hourly energy simulation."""
import pandas as pd
import streamlit as st
from home_energy_simulator import SystemConfig, demo_profiles, simulate, totals
from home_energy_simulator.solar import SolarConfig, solar_factors
from datetime import date

st.set_page_config(page_title="Home Energy Simulator", layout="wide")
st.title("Home Energy Simulator")
st.caption("Illustrative hourly solar, battery and backup-power model — not an electrical design tool.")

with st.sidebar:
    st.header("System configuration")
    solar = st.slider("Solar array (kW)", 0.0, 20.0, 4.8, 0.2)
    use_solar = st.checkbox("Use location and seasonal solar model", value=True)
    latitude = st.number_input("Latitude (degrees)", -90.0, 90.0, 34.27, 0.1)
    longitude = st.number_input("Longitude (degrees)", -180.0, 180.0, -88.41, 0.1)
    day = st.date_input("Simulation date", value=date.today())
    tilt = st.slider("Panel tilt (degrees)", 0, 90, 30)
    azimuth = st.slider("Panel azimuth (180° = south)", 0, 360, 180)
    clouds = st.slider("Clear-sky multiplier", 0.0, 1.0, 1.0, 0.05)
    battery = st.slider("Battery capacity (kWh)", 0.0, 60.0, 14.0, 0.5)
    inverter = st.slider("Battery inverter limit (kW)", 0.0, 20.0, 5.0, 0.5)
    initial = st.slider("Initial battery charge (%)", 10, 100, 50)
    grid = st.checkbox("Grid available", value=False)
    gen_enabled = st.checkbox("Generator enabled", value=False)
    gen_kw = st.slider("Generator power (kW)", 0.0, 20.0, 5.0, 0.5,
                       disabled=not gen_enabled)

config = SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                      initial_soc=initial/100, generator_enabled=gen_enabled,
                      generator_kw=gen_kw, grid_available=grid)
loads, demo_sun = demo_profiles()
sun = solar_factors(SolarConfig(latitude_deg=latitude, longitude_deg=longitude,
                               array_kw=solar, tilt_deg=tilt, azimuth_deg=azimuth,
                               cloud_factor=clouds), day) if use_solar else demo_sun
rows = simulate(config, loads, sun)
summary = totals(rows)
a,b,c,d = st.columns(4)
a.metric("Demand", f"{summary['demand_kwh']:.1f} kWh")
b.metric("Solar generated", f"{summary['solar_kwh']:.1f} kWh")
c.metric("Generator", f"{summary['generator_kwh']:.1f} kWh")
d.metric("Unserved", f"{summary['unmet_kwh']:.1f} kWh")
df = pd.DataFrame(rows).set_index("hour")
st.subheader("Hourly energy dispatch")
st.line_chart(df[["demand_kwh","solar_kwh","battery_delivered_kwh",
                  "generator_kwh","grid_kwh","unmet_kwh"]])
st.subheader("Battery state of charge")
st.line_chart(df[["soc"]])
st.download_button("Download simulation CSV", df.to_csv().encode("utf-8"),
                   "energy_simulation.csv", "text/csv")
st.info("Load is synthetic. Solar model is approximate clear-sky geometry, not measured weather. Longitude is recorded but hours use local solar time; no time-zone or equation-of-time correction. No surge loads, temperature, fuel or shading modeled.")


st.divider()
st.header('LiFePO4 Battery Bank Designer')
st.caption('Nominal educational estimates only; verify manufacturer series/parallel approval and electrical protections.')
from home_energy_simulator.battery import BatteryBank
bc1,bc2,bc3 = st.columns(3)
with bc1:
    module_v = st.number_input('Module nominal voltage (V)', min_value=1.0, value=12.8, step=0.1)
    module_ah = st.number_input('Module capacity (Ah)', min_value=1.0, value=280.0, step=10.0)
with bc2:
    series = st.number_input('Modules in series', min_value=1, max_value=16, value=4)
    parallel = st.number_input('Parallel strings', min_value=1, max_value=16, value=1)
with bc3:
    dod = st.slider('Usable depth of discharge (%)', 10, 100, 80)
    eff = st.slider('Inverter efficiency (%)', 50, 100, 92)
bank = BatteryBank(module_voltage=module_v, module_ah=module_ah, series=series,
                   parallel=parallel, usable_depth_of_discharge=dod/100,
                   inverter_efficiency=eff/100)
summary_bank = bank.summary()
x,y,z = st.columns(3)
x.metric('Nominal voltage', f"{summary_bank['nominal_voltage_v']:.1f} V")
y.metric('Stored energy', f"{summary_bank['nominal_energy_kwh']:.2f} kWh")
z.metric('Usable AC energy', f"{summary_bank['usable_ac_energy_kwh']:.2f} kWh")
load_for_runtime = st.number_input('Constant AC load for runtime estimate (kW)', min_value=0.1, value=1.0, step=0.1)
try:
    st.metric('Estimated runtime', f'{bank.runtime_hours(load_for_runtime):.1f} hours')
except ValueError as exc:
    st.warning(str(exc))
