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
