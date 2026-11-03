"""Streamlit dashboard for hourly energy simulation."""
import pandas as pd
import streamlit as st
from home_energy_simulator import SystemConfig, demo_profiles, simulate, totals
from home_energy_simulator.solar import SolarConfig, solar_factors
from datetime import date
from home_energy_simulator.loads import Appliance, default_appliances, hourly_load_kw, daily_energy_kwh

st.set_page_config(page_title="Home Energy Simulator", layout="wide")
st.title("Home Energy Simulator · v1.0")
st.caption("Solar · Battery · Generator · Outage resilience · Cost comparison | Educational engineering model")
st.markdown(
    "**Jump to section:** "
    "[Household Loads](#loads) · [Battery Bank](#battery-bank) · "
    "[Outage Simulator](#outage) · [HVAC Sizing](#hvac) · "
    "[Generator Fuel](#generator-fuel) · [Fuel-Aware Outage](#fuel-aware-outage) · "
    "[Optimization](#optimization) · [Scenario Workspace](#workspace)"
)


with st.sidebar:
    st.header("System configuration")
    generator_only = st.checkbox("Generator-only mode", value=False,
                                 help="Run on generator power without grid, solar, or battery contribution.")
    grid = st.checkbox("Grid available", value=False, disabled=generator_only)
    gen_enabled = st.checkbox("Generator enabled", value=False, disabled=generator_only)
    # Keep optional settings in session state when their widgets are hidden.
    if "generator_power_setting" not in st.session_state:
        st.session_state.generator_power_setting = 5.0
    if gen_enabled or generator_only:
        gen_kw = st.slider("Generator power (kW)", 0.0, 20.0,
                           st.session_state.generator_power_setting, 0.5)
        st.session_state.generator_power_setting = gen_kw
    else:
        gen_kw = st.session_state.generator_power_setting
    st.divider()
    solar = st.slider("Solar array (kW)", 0.0, 20.0, 4.8, 0.2, disabled=generator_only)
    use_solar = st.checkbox("Use location and seasonal solar model", value=True, disabled=generator_only)
    solar_defaults = {
        "latitude": 34.27, "longitude": -88.41, "day": date.today(),
        "tilt": 30, "azimuth": 180, "clouds": 1.0,
    }
    if "seasonal_settings" not in st.session_state:
        st.session_state.seasonal_settings = solar_defaults.copy()
    settings = st.session_state.seasonal_settings
    if use_solar and not generator_only:
        latitude = st.number_input("Latitude (degrees)", -90.0, 90.0, settings["latitude"], 0.1)
        longitude = st.number_input("Longitude (degrees)", -180.0, 180.0, settings["longitude"], 0.1)
        day = st.date_input("Simulation date", value=settings["day"])
        tilt = st.slider("Panel tilt (degrees)", 0, 90, settings["tilt"])
        azimuth = st.slider("Panel azimuth (180° = south)", 0, 360, settings["azimuth"])
        clouds = st.slider("Clear-sky multiplier", 0.0, 1.0, settings["clouds"], 0.05)
        st.session_state.seasonal_settings = dict(
            latitude=latitude, longitude=longitude, day=day,
            tilt=tilt, azimuth=azimuth, clouds=clouds,
        )
    else:
        latitude, longitude, day = settings["latitude"], settings["longitude"], settings["day"]
        tilt, azimuth, clouds = settings["tilt"], settings["azimuth"], settings["clouds"]
    battery = st.slider("Battery capacity (kWh)", 0.0, 60.0, 14.0, 0.5, disabled=generator_only)
    inverter = st.slider("Battery inverter limit (kW)", 0.0, 20.0, 5.0, 0.5, disabled=generator_only)
    initial = st.slider("Initial battery charge (%)", 10, 100, 50, disabled=generator_only)

if generator_only:
    grid = False
    gen_enabled = True
    solar = 0.0
    battery = 0.0
    inverter = 0.0
    st.sidebar.info("Generator-only mode: grid, solar, and battery are excluded. Generator capacity and load determine unmet demand.")

config = SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                      initial_soc=initial/100, generator_enabled=gen_enabled,
                      generator_kw=gen_kw, grid_available=grid)
st.header("Household Load Designer", anchor="loads")
st.caption("Edit appliance running watts, schedules and duty cycles to model hourly average demand.")
if "appliances" not in st.session_state:
    st.session_state.appliances = [
        dict(name=a.name, running_watts=float(a.running_watts), quantity=a.quantity,
             start_hour=a.start_hour, end_hour=a.end_hour, duty_cycle=float(a.duty_cycle))
        for a in default_appliances()
    ]
edited = st.data_editor(
    pd.DataFrame(st.session_state.appliances),
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    column_config={
        "name": st.column_config.TextColumn("Appliance", required=True),
        "running_watts": st.column_config.NumberColumn("Running watts", min_value=0.0, step=50.0, required=True),
        "quantity": st.column_config.NumberColumn("Quantity", min_value=1, max_value=100, step=1, required=True),
        "start_hour": st.column_config.NumberColumn("Start hour (0–23)", min_value=0, max_value=23, step=1, required=True),
        "end_hour": st.column_config.NumberColumn("End hour (1–24)", min_value=1, max_value=24, step=1, required=True),
        "duty_cycle": st.column_config.NumberColumn("Duty cycle (0–1)", min_value=0.0, max_value=1.0, step=0.05, required=True),
    },
    key="appliance_editor",
)
appliances = []
errors = []
for i, record in enumerate(edited.to_dict("records"), start=1):
    try:
        if any(pd.isna(value) for value in record.values()):
            raise ValueError("All fields are required")
        appliances.append(Appliance(
            name=str(record["name"]),
            running_watts=float(record["running_watts"]),
            quantity=int(record["quantity"]),
            start_hour=int(record["start_hour"]),
            end_hour=int(record["end_hour"]),
            duty_cycle=float(record["duty_cycle"]),
        ))
    except (ValueError, TypeError) as exc:
        errors.append(f"Row {i}: {exc}")
if errors:
    st.error("Invalid appliance entries: " + "; ".join(errors))
    st.stop()
loads = hourly_load_kw(appliances)
st.metric("Estimated daily consumption", f"{daily_energy_kwh(appliances):.1f} kWh")
st.line_chart(pd.DataFrame({"Household load (kW)": loads}))
_, demo_sun = demo_profiles()
sun = solar_factors(SolarConfig(latitude_deg=latitude, longitude_deg=longitude,
                               array_kw=solar, tilt_deg=tilt, azimuth_deg=azimuth,
                               cloud_factor=clouds), day) if use_solar and not generator_only else demo_sun
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
st.header('LiFePO4 Battery Bank Designer', anchor="battery-bank")
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


st.divider()
st.header("Whole-Home Outage Simulator", anchor="outage")
st.caption("Repeat a synthetic 24-hour household load and the selected solar profile over multiple outage days. The grid is always off.")
from home_energy_simulator.outage import simulate_outage
oc1, oc2, oc3 = st.columns(3)
with oc1:
    outage_days = st.slider("Outage duration (days)", 1, 14, 3)
with oc2:
    outage_fuel_kind = st.selectbox(
        "Outage generator fuel type", ["gasoline", "propane", "natural_gas"],
        format_func=lambda x: {"gasoline": "Gasoline", "propane": "Propane", "natural_gas": "Natural gas"}[x],
    )
    outage_unit = "liters" if outage_fuel_kind == "natural_gas" else "gallons"
    outage_rate_display = st.number_input(
        f"Generator fuel use ({outage_unit}/hour running)",
        min_value=0.1, value=60.0 if outage_fuel_kind == "natural_gas" else 0.5,
        step=1.0 if outage_fuel_kind == "natural_gas" else 0.1,
        key=f"outage_rate_{outage_fuel_kind}",
    )
with oc3:
    outage_available_display = st.number_input(
        f"Generator fuel available ({outage_unit})",
        min_value=0.0, value=1200.0 if outage_fuel_kind == "natural_gas" else 10.0,
        step=10.0 if outage_fuel_kind == "natural_gas" else 1.0,
        key=f"outage_inventory_{outage_fuel_kind}",
    )
# The legacy fixed-rate outage engine accepts quantities named 'liters'.
# Convert liquid US gallons to liters; gaseous liters remain volume-based model units.
outage_to_internal = 3.785411784 if outage_fuel_kind != "natural_gas" else 1.0
hourly_fuel = outage_rate_display * outage_to_internal
fuel_available = outage_available_display * outage_to_internal
outage = simulate_outage(
    SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                 initial_soc=initial / 100, generator_enabled=gen_enabled,
                 generator_kw=gen_kw, grid_available=False),
    loads, sun, days=outage_days,
    generator_fuel_liters_per_hour=hourly_fuel,
    generator_fuel_available_liters=fuel_available,
)
o1, o2, o3, o4 = st.columns(4)
o1.metric("Hours fully supplied", f"{outage.hours_fully_served}/{outage.hours_simulated}")
o2.metric("Demand served", f"{outage.fraction_demand_served:.1%}")
o3.metric("Generator operating hours", f"{outage.generator_hours}")
o4.metric("Fuel consumed", f"{outage.generator_fuel_liters / outage_to_internal:.1f} {outage_unit}")
if outage.first_unserved_hour is None:
    st.success("All modeled load supplied for the selected outage duration.")
else:
    st.warning(f"First unmet demand in hour {outage.first_unserved_hour + 1} (day {outage.first_unserved_hour // 24 + 1}).")
outage_df = pd.DataFrame(outage.rows).set_index("hour")
st.line_chart(outage_df[["demand_kwh", "solar_kwh", "battery_delivered_kwh", "generator_kwh", "unmet_kwh"]])
st.download_button("Download outage CSV", outage_df.to_csv().encode("utf-8"),
                   "outage_simulation.csv", "text/csv")
st.info("Illustrative hourly averages only. Fuel burn is fixed per running hour; no starting surges, generator minimum loading, battery BMS, temperature, shading, weather forecasts, or equipment interconnection constraints are modeled.")


st.divider()
st.header("HVAC & Generator Sizing (v0.6)", anchor="hvac")
st.caption("Nominal running and startup capacity screening. Enter equipment-specific ratings before drawing conclusions.")
from home_energy_simulator.hvac import HVACLoad, SourceRating, evaluate_hvac
hc1, hc2, hc3 = st.columns(3)
with hc1:
    hvac_running = st.number_input("HVAC running power (kW)", min_value=0.0, value=3.5, step=0.1)
    hvac_multiplier = st.number_input("Starting-to-running multiplier", min_value=1.0, value=3.0, step=0.25)
with hc2:
    other_running = st.number_input("Other simultaneous running load (kW)", min_value=0.0, value=2.0, step=0.1)
    soft_reduction = st.slider("Estimated soft-start surge reduction (%)", 0, 100, 60, 5)
with hc3:
    gen_surge = st.number_input("Generator surge rating (kW)", min_value=float(gen_kw), value=max(float(gen_kw), float(gen_kw) * 1.2), step=0.5)
    inv_surge = st.number_input("Inverter surge rating (kW)", min_value=float(inverter), value=max(float(inverter), float(inverter) * 1.5), step=0.5)
hvac_spec = HVACLoad(hvac_running, hvac_multiplier, soft_reduction / 100)
generator_rating = SourceRating(gen_kw if gen_enabled else 0.0, gen_surge if gen_enabled else 0.0)
inverter_rating = SourceRating(inverter, inv_surge)
st.metric("Estimated HVAC startup demand", f"{hvac_spec.starting_kw:.1f} kW")
st.metric("With estimated soft-start", f"{hvac_spec.soft_start_kw:.1f} kW")
sizing_rows = []
for source_name, source_rating in [("Generator", generator_rating), ("Battery inverter", inverter_rating)]:
    for use_soft in (False, True):
        result = evaluate_hvac(hvac_spec, source_rating, other_running, use_soft_start=use_soft)
        sizing_rows.append({
            "Source": source_name,
            "Soft-start": "Yes" if use_soft else "No",
            "Running demand (kW)": round(result.required_running_kw, 2),
            "Starting demand (kW)": round(result.required_start_kw, 2),
            "Running margin (kW)": round(result.running_margin_kw, 2),
            "Starting margin (kW)": round(result.starting_margin_kw, 2),
            "Nominal capacity check": "Within ratings" if result.nominally_fits else "Exceeds rating",
        })
st.dataframe(pd.DataFrame(sizing_rows), hide_index=True, use_container_width=True)
st.warning("Within ratings does NOT guarantee a compressor will start. Motor starting current, surge duration, voltage dip, generator transient response, power factor and transfer equipment are not modeled. Never backfeed a home; consult a qualified electrician.")


st.divider()
st.header("Generator Fuel & Runtime Calculator (v0.7)", anchor="generator-fuel")
st.caption("Independent steady-load planning estimate; not yet connected to outage dispatch.")
from home_energy_simulator.fuel import FuelModel
fc1, fc2, fc3 = st.columns(3)
with fc1:
    fuel_kind = st.selectbox("Generator fuel type", ["gasoline", "propane", "natural_gas"],
                             format_func=lambda x: {"gasoline": "Gasoline", "propane": "Propane", "natural_gas": "Natural gas"}[x])
    fuel_unit = "liters" if fuel_kind == "natural_gas" else "gallons"
    fuel_to_internal = 1.0 / 28.316846592 if fuel_kind == "natural_gas" else 1.0
    rated_fuel_kw = st.number_input("Generator continuous rating (kW)", min_value=0.1, value=10.0, step=0.5)
    load_fuel_kw = st.number_input("Steady electrical output (kW)", min_value=0.0,
                                  max_value=float(rated_fuel_kw), value=min(5.0, float(rated_fuel_kw)), step=0.5)
with fc2:
    idle_rate = st.number_input(f"Idle fuel rate ({fuel_unit}/hour)", min_value=0.0, value=0.5 if fuel_kind != "natural_gas" else 850.0, step=0.1)
    full_rate = st.number_input(f"Full-load fuel rate ({fuel_unit}/hour)", min_value=float(idle_rate),
                                value=max(float(idle_rate), 2.0 if fuel_kind != "natural_gas" else 3680.0), step=0.1)
    fuel_price = st.number_input(f"Fuel price ($/{fuel_unit})", min_value=0.0, value=3.0 if fuel_kind != "natural_gas" else 0.0007, step=0.0001)
with fc3:
    operation_hours = st.number_input("Planned operating hours", min_value=0.0, value=72.0, step=1.0)
    use_finite_fuel = st.checkbox("Limit by available fuel inventory", value=fuel_kind != "natural_gas")
    inventory = st.number_input(f"Available fuel ({fuel_unit})", min_value=0.0, value=20.0, step=1.0,
                                disabled=not use_finite_fuel)
fuel_model = FuelModel(fuel_kind, rated_fuel_kw, idle_rate * fuel_to_internal,\n                       full_rate * fuel_to_internal, fuel_price / fuel_to_internal)
fuel_result = fuel_model.estimate(load_fuel_kw, operation_hours,\n                                  inventory * fuel_to_internal if use_finite_fuel else None)
fm1, fm2, fm3, fm4 = st.columns(4)
fm1.metric("Estimated fuel rate", f"{fuel_result['fuel_rate_per_hour'] / fuel_to_internal:.2f} {fuel_unit}/h")
fm2.metric("Fuel needed", f"{fuel_result['fuel_needed'] / fuel_to_internal:.1f} {fuel_unit}")
fm3.metric("Fuel cost (full duration)", f"${fuel_result['fuel_cost']:,.2f}")
fm4.metric("Estimated runtime with inventory",
           "Not limited" if fuel_result["available_runtime_hours"] is None else f"{fuel_result['available_runtime_hours']:.1f} hours")
if use_finite_fuel and fuel_result["supplied_hours"] < operation_hours:
    st.warning(f"Inventory covers approximately {fuel_result['supplied_hours']:.1f} of {operation_hours:.1f} planned hours.")
st.info("Linear idle-to-full-load consumption is illustrative. Use manufacturer-measured fuel rates. Natural gas is entered as gaseous liters at consistent reference conditions; internal calculations use cubic feet. The separate outage simulator uses a fixed hourly fuel-rate model.")


st.divider()
st.header("Integrated Fuel-Aware Outage (v0.8)", anchor="fuel-aware-outage")
st.caption("Uses the household load, solar, battery and generator settings above, with load-dependent fuel consumption from the v0.7 fuel model.")
integrated = simulate_outage(
    SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                 initial_soc=initial / 100, generator_enabled=gen_enabled,
                 generator_kw=gen_kw, grid_available=False),
    loads, sun, days=outage_days, fuel_model=fuel_model,
    fuel_available=inventory * fuel_to_internal if use_finite_fuel else None,
) if not gen_enabled or gen_kw <= rated_fuel_kw else None
if integrated is None:
    st.error("Set the fuel model's continuous generator rating at least as high as the generator power in the sidebar.")
else:
    im1, im2, im3, im4 = st.columns(4)
    im1.metric("Demand served", f"{integrated.fraction_demand_served:.1%}")
    im2.metric("Fuel consumed", f"{integrated.generator_fuel_used / fuel_to_internal:.2f} {fuel_unit}")
    im3.metric("Fuel remaining", "Unlimited" if integrated.generator_fuel_remaining is None else
               f"{integrated.generator_fuel_remaining / fuel_to_internal:.2f} {fuel_unit}")
    im4.metric("Generator fuel cost", f"${integrated.generator_fuel_cost:,.2f}")
    if integrated.first_unserved_hour is not None:
        st.warning(f"First unmet demand in hour {integrated.first_unserved_hour + 1}.")
    else:
        st.success("All modeled demand served throughout the outage.")
    integrated_df = pd.DataFrame(integrated.rows).set_index("hour")
    if generator_only:
        st.subheader("Generator-only runtime & operating cost")
        generator_hours = int((integrated_df["generator_kwh"] > 0).sum())
        modeled_hours = len(integrated_df)
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Generator running hours", f"{generator_hours} of {modeled_hours} h")
        g2.metric("Fuel used", f"{integrated.generator_fuel_used:.2f} {integrated.generator_fuel_unit}")
        g3.metric("Fuel cost", f"${integrated.generator_fuel_cost:,.2f}")
        g4.metric("Fuel remaining", "Unlimited" if integrated.generator_fuel_remaining is None
                  else f"{integrated.generator_fuel_remaining:.2f} {integrated.generator_fuel_unit}")
        if use_finite_fuel:
            st.caption("Running hours are modeled hourly intervals with generator output, not continuous runtime. "
                       "Fuel inventory may limit operation; see unmet demand and the hourly chart below.")
        else:
            st.caption("Fuel supply is assumed unlimited. Enter a finite fuel inventory above to estimate "
                       "runtime constraints for the selected household loads.")
        st.caption("Fuel use and costs follow the generator fuel model settings above, "
                   "including rated output, idle/full-load rates, and fuel price.")
    st.line_chart(integrated_df[["generator_kwh", "generator_fuel_used", "unmet_kwh"]])
    st.download_button("Download integrated outage CSV", integrated_df.to_csv().encode("utf-8"),
                       "integrated_outage.csv", "text/csv")
    st.info("Fuel is burned only during modeled generator output. An hour is skipped if insufficient fuel remains for the entire hour; partial-hour generation, starting surges and actual fuel curves are not modeled.")


st.divider()
st.header("System Optimization (v0.9)", anchor="optimization")
st.caption("Compare discrete solar, battery and generator sizes for one repeated-day outage scenario.")
from home_energy_simulator.optimization import UnitCosts, optimize_system
opt1, opt2, opt3 = st.columns(3)
with opt1:
    solar_choices = st.multiselect("Solar capacities (kW)", [0.0, 2.4, 4.8, 7.2, 9.6], default=[0.0, 4.8, 9.6])
    battery_choices = st.multiselect("Battery capacities (kWh)", [0.0, 7.0, 14.0, 28.0, 42.0], default=[0.0, 14.0, 28.0])
with opt2:
    generator_choices = st.multiselect("Generator capacities (kW)", [0.0, 3.0, 5.0, 8.0, 10.0], default=[0.0, 5.0, 10.0])
    target_served = st.slider("Minimum energy demand served (%)", 0, 100, 99)
with opt3:
    solar_unit_cost = st.number_input("Solar installed cost ($/kW)", min_value=0.0, value=1500.0, step=100.0)
    battery_unit_cost = st.number_input("Battery installed cost ($/kWh)", min_value=0.0, value=500.0, step=50.0)
    generator_unit_cost = st.number_input("Generator installed cost ($/kW)", min_value=0.0, value=300.0, step=50.0)
use_opt_fuel = st.checkbox("Include load-dependent generator fuel cost and inventory",
                           value=True, key="opt_fuel")
if st.button("Compare system configurations", type="primary"):
    try:
        opt_fuel_model = None
        if use_opt_fuel:
            opt_fuel_model = FuelModel(fuel_kind, max(max(generator_choices), 0.1),
                                       idle_rate, full_rate, fuel_price) if generator_choices else None
        opt_results = optimize_system(
            SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                         initial_soc=initial / 100, grid_available=False),
            loads, sun, solar_choices, battery_choices, generator_choices,
            UnitCosts(solar_unit_cost, battery_unit_cost, generator_unit_cost),
            days=outage_days, min_demand_served=target_served / 100,
            fuel_model=opt_fuel_model,
            fuel_available=inventory if use_opt_fuel and use_finite_fuel else None,
        )
        st.session_state["opt_results"] = opt_results
        st.session_state["opt_target"] = target_served / 100
        st.session_state["opt_unit"] = opt_fuel_model.unit if opt_fuel_model else "not modeled"
    except ValueError as exc:
        st.error(str(exc))
if "opt_results" in st.session_state:
    results_opt = st.session_state["opt_results"]
    target_opt = st.session_state["opt_target"]
    feasible = [c for c in results_opt if c.demand_served >= target_opt]
    st.metric("Configurations evaluated", len(results_opt))
    if feasible:
        best = feasible[0]
        st.success(f"Lowest modeled cost meeting target: {best.solar_kw:g} kW solar, "
                   f"{best.battery_kwh:g} kWh battery, {best.generator_kw:g} kW generator "
                   f"— ${best.total_cost:,.0f} total modeled cost, {best.demand_served:.1%} demand served.")
    else:
        st.warning("No candidate meets the requested energy-served target; showing highest-serving options first.")
    opt_table = pd.DataFrame([{
        "Solar (kW)": c.solar_kw, "Battery (kWh)": c.battery_kwh,
        "Generator (kW)": c.generator_kw, "Demand served (%)": round(c.demand_served * 100, 2),
        "Unmet (kWh)": c.unmet_kwh, "Capital cost ($)": c.capital_cost,
        "Outage fuel cost ($)": c.fuel_cost, "Total modeled cost ($)": c.total_cost,
        "Fuel used": c.fuel_used,
    } for c in results_opt])
    st.dataframe(opt_table, hide_index=True, use_container_width=True)
    st.download_button("Download optimization CSV", opt_table.to_csv(index=False).encode("utf-8"),
                       "system_optimization.csv", "text/csv")
st.info("This is a discrete comparison for a single illustrative outage, not lifetime cost optimization or a statistical reliability estimate. Fuel rates, installation costs and weather are assumptions; electrical feasibility is not checked.")


st.divider()
st.header("Scenario Workspace & PDF Reports (v1.0)", anchor="workspace")
st.caption("Save a snapshot as JSON, reload it for independent analysis, and export a PDF report. Files remain on your device; nothing is saved to a server.")
from home_energy_simulator.scenarios import Scenario, scenario_to_json, scenario_from_json
from home_energy_simulator.reports import outage_pdf

scenario_name = st.text_input("Scenario name", value="Residential backup study")
try:
    current_scenario = Scenario(
        name=scenario_name,
        config=SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                            initial_soc=initial / 100, generator_enabled=gen_enabled,
                            generator_kw=gen_kw, grid_available=False),
        loads_kw=list(loads), sun_factors=list(sun), days=outage_days,
    )
    st.download_button("Save current scenario (.json)",
                       scenario_to_json(current_scenario).encode("utf-8"),
                       file_name="home_energy_scenario.json", mime="application/json")
except ValueError as exc:
    st.error(f"Cannot save current scenario: {exc}")
    current_scenario = None

uploaded_scenario = st.file_uploader("Load a saved scenario (.json)", type=["json"])
selected_scenario = current_scenario
if uploaded_scenario is not None:
    try:
        selected_scenario = scenario_from_json(uploaded_scenario.getvalue())
        st.success(f"Loaded scenario: {selected_scenario.name} (runs independently of current sidebar inputs)")
    except ValueError as exc:
        selected_scenario = None
        st.error(f"Cannot load scenario: {exc}")

if selected_scenario is not None:
    try:
        report_outage = simulate_outage(
            selected_scenario.config, selected_scenario.loads_kw,
            selected_scenario.sun_factors, days=selected_scenario.days,
        )
        rp1, rp2, rp3 = st.columns(3)
        rp1.metric("Scenario demand served", f"{report_outage.fraction_demand_served:.1%}")
        rp2.metric("Unserved energy", f"{report_outage.total_unserved_kwh:.1f} kWh")
        rp3.metric("Generator operating hours", report_outage.generator_hours)
        report_df = pd.DataFrame(report_outage.rows).set_index("hour")
        st.line_chart(report_df[["demand_kwh", "solar_kwh", "generator_kwh", "unmet_kwh"]])
        st.download_button("Download outage analysis PDF",
                           outage_pdf(selected_scenario, report_outage),
                           file_name="home_energy_outage_report.pdf", mime="application/pdf")
    except ValueError as exc:
        st.error(f"Unable to simulate scenario: {exc}")
st.info("Scenario JSON stores system settings and hourly load/solar profiles, not fuel-model settings. PDF reports therefore use the legacy unlimited-fuel dispatch model; use the Integrated Fuel-Aware Outage panel for fuel-limited analysis.")
