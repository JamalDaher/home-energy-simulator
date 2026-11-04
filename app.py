"""Streamlit dashboard for hourly energy simulation."""
import inspect
import pandas as pd
import streamlit as st
from home_energy_simulator import SystemConfig, demo_profiles, simulate, totals
from home_energy_simulator.solar import SolarConfig, solar_factors
from datetime import date
from home_energy_simulator.loads import Appliance, default_appliances, hourly_load_kw, daily_energy_kwh

st.set_page_config(page_title="Home Energy Simulator", layout="wide")
st.markdown(
    """
    <style>
    /* Tighten Streamlit's default empty area above the dashboard. */
    div[data-testid="stMetric"] {background:rgba(105,132,160,.09);border:1px solid rgba(105,132,160,.2);border-radius:14px;padding:16px}
    div[data-testid="stMetric"] label {font-weight:650}
    .stAppViewContainer .block-container {max-width:1500px}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.7rem}
    [data-testid="stDataFrame"] {max-width:100%;overflow-x:auto}
    @media(max-width:768px) {
      div[data-testid="stMetric"] {padding:10px;border-radius:10px}
      div[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size:1.35rem}
      .stAppViewContainer .block-container {padding-left:.85rem;padding-right:.85rem}
    }
    .sim-section-anchor {display:block;height:1px;scroll-margin-top:72px}
    /* Keep anchored accordion titles below Streamlit's top toolbar. */
    [data-testid="stExpander"] {scroll-margin-top:72px}
    div[data-testid="stExpander"] {border-radius:14px;overflow:hidden;margin-bottom:12px}
    div[data-testid="stExpander"] details summary {font-weight:650;font-size:1.08rem}
    .stAppViewContainer .block-container {
        padding-top: 1.25rem;
        position: relative;
    }
    /* Target a point above the scrollable document so browser anchor
       navigation clamps to scroll position zero, even with Streamlit's
       internal content padding and sticky header offsets. */
    #simulator-top {
        position: absolute;
        top: -10000px;
        left: 0;
        width: 1px;
        height: 1px;
        scroll-margin-top: 0;
    }
    @media (max-width: 768px) {
        .stAppViewContainer .block-container {
            padding-top: 0.75rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.html('<span id="simulator-top" aria-hidden="true"></span>')
st.title("Home Energy Simulator · v1.2")
# Render the fixed shortcut with st.html rather than Markdown, whose HTML
# sanitization/rendering can prevent positioned links from appearing.
back_to_top_html = """
<style>
  .sim-back-to-top {
    position: fixed !important;
    right: 24px !important;
    bottom: 104px !important;
    z-index: 2147483000 !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 999px;
    background: #263b54;
    color: #fff !important;
    font-size: 26px;
    font-weight: 700;
    text-decoration: none !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.3);
    transition: opacity 180ms ease, visibility 180ms ease;
  }
  .sim-back-to-top.is-hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }
  .sim-back-to-top:hover, .sim-back-to-top:focus-visible {
    background: #365779;
    outline: 2px solid #fff;
  }
  @media (max-width: 768px) {
    .sim-back-to-top { right: 12px !important; bottom: 96px !important; }
  }
</style>
<a class="sim-back-to-top" href="#simulator-top"
   title="Back to top" aria-label="Back to top">↑</a>
"""
# Streamlit versions supporting inline JavaScript can follow the actual
# main scroll container. On older versions keep the working button visible.
if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
    st.html(back_to_top_html + """
<script>
(() => {
  const button = document.querySelector('.sim-back-to-top');
  if (!button) return;
  const findScroller = () =>
    document.querySelector('[data-testid="stAppViewContainer"] [data-testid="stMain"]')
    || document.querySelector('[data-testid="stAppViewContainer"]')
    || document.scrollingElement;
  const scroller = findScroller();
  const position = () => Math.max(
    scroller?.scrollTop || 0,
    document.scrollingElement?.scrollTop || 0,
    window.scrollY || 0
  );
  const update = () => button.classList.toggle('is-hidden', position() < 240);
  update();
  scroller?.addEventListener('scroll', update, {passive: true});
  window.addEventListener('scroll', update, {passive: true});
})();
</script>
""", unsafe_allow_javascript=True)
else:
    st.html(back_to_top_html)
st.caption("Solar · Battery · Generator · Outage resilience · Cost comparison | Educational engineering model")
st.html("""
<style>
.sim-nav {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:10px 0 18px}
.sim-nav-group{grid-column:1/-1;font-size:.78rem;font-weight:750;letter-spacing:.035em;opacity:.75;padding:7px 2px 0;margin-top:3px}
.sim-nav-group:first-child{margin-top:0}
.sim-nav a {display:block;text-decoration:none!important;border:1px solid rgba(116,144,172,.3);
  background:rgba(116,144,172,.08);border-radius:10px;padding:11px 10px;color:inherit!important;
  font-size:.92rem;font-weight:600;line-height:1.3;transition:background .15s,border-color .15s}
.sim-nav a:hover,.sim-nav a:focus-visible {background:rgba(116,144,172,.19);border-color:rgba(116,144,172,.65)}
.sim-nav a[aria-current="location"] {background:rgba(116,144,172,.24);border-color:rgba(116,144,172,.85);box-shadow:inset 0 0 0 1px rgba(116,144,172,.45)}
@media(prefers-reduced-motion:reduce){.sim-nav a{transition:none}}
.sim-nav a small {display:block;font-size:.72rem;opacity:.65;margin-top:4px;font-weight:400}
@media(max-width:1050px){.sim-nav{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:650px){.sim-nav{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:440px){.sim-nav{grid-template-columns:1fr 1fr;gap:7px}.sim-nav a{padding:10px;font-size:.82rem}}
</style>
<nav aria-label="Simulator sections" class="sim-nav">
<div class="sim-nav-group">1 · Plan your loads</div>
<a href="#loads">⚡ Household loads<small>Appliances & daily demand</small></a>
<a class="sim-nav-advanced" href="#critical-loads">🛡️ Critical circuits<small>Backup load priorities</small></a>
<div class="sim-nav-group">2 · Configure equipment</div>
<a class="sim-nav-advanced" href="#battery-bank">🔋 Battery bank<small>Storage & runtime</small></a>
<a class="sim-nav-advanced" href="#hvac">❄️ HVAC sizing<small>Startup & generator loads</small></a>
<a class="sim-nav-advanced" href="#generator-fuel">⛽ Generator fuel<small>Consumption & cost</small></a>
<div class="sim-nav-group">3 · Simulate & compare</div>
<a href="#outage">🏠 Outage simulator<small>Whole-home resilience</small></a>
<a class="sim-nav-advanced" href="#fuel-aware-outage">🕒 Fuel-aware outage<small>Multi-day backup</small></a>
<a href="#backup-comparison">⚖️ Compare systems<small>Generator, battery & hybrid</small></a>
<a class="sim-nav-advanced" href="#optimization">📈 Optimization<small>Compare configurations</small></a>
<div class="sim-nav-group">4 · Save & export</div>
<a href="#workspace">📁 Workspace<small>Scenarios & reports</small></a>
</nav>
""")


# Navigation targets are rendered immediately before their Streamlit expanders.
# On Streamlit builds that support st.html JavaScript, open the corresponding
# native <details> element before scrolling to its section.
nav_expansion_script = """
<script>
(() => {
  const ids = new Set([
    'critical-loads', 'battery-bank', 'outage', 'hvac',
    'generator-fuel', 'fuel-aware-outage', 'backup-comparison',
    'optimization', 'workspace'
  ]);
  function markActive(id) {
    document.querySelectorAll('.sim-nav a[href^="#"]').forEach(link => {
      if (link.hash.slice(1) === id) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function openSection(id) {
    if (!ids.has(id)) return;
    markActive(id);
    const anchor = document.getElementById(id);
    if (!anchor) return;
    const blocks = [...document.querySelectorAll('[data-testid="stExpander"]')];
    // Find the first expander AFTER the target anchor, not a nested expander.
    const target = blocks.find(block =>
      anchor.compareDocumentPosition(block) & Node.DOCUMENT_POSITION_FOLLOWING
    );
    const details = target?.querySelector('details');
    if (details && !details.open) details.open = true;
    // Allow the expanded content to settle before positioning the section.
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    requestAnimationFrame(() => requestAnimationFrame(() =>
      anchor.scrollIntoView({block:'start', behavior: reducedMotion ? 'instant' : 'smooth'})
    ));
  }
  document.addEventListener('click', event => {
    const link = event.target.closest?.('.sim-nav a[href^="#"]');
    if (!link) return;
    const id = decodeURIComponent(link.hash.slice(1));
    if (!ids.has(id)) {
      // Household loads is a native Streamlit heading, not an expander.
      markActive(id);
      return;
    }
    event.preventDefault();
    if (location.hash !== '#' + id) history.pushState(null, '', '#' + id);
    openSection(id);
  });
  function followHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (ids.has(id)) requestAnimationFrame(() => openSection(id));
    else if (id === 'loads') markActive(id);
  }
  window.addEventListener('hashchange', followHash);
  window.addEventListener('popstate', followHash);
  followHash();
})();
</script>
"""
if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
    st.html(nav_expansion_script, unsafe_allow_javascript=True)


with st.sidebar:
    st.header("Configure your system")
    advanced_view = st.toggle(
        "Show advanced tools", value=False, key="show_advanced_navigation",
        help="Show every dashboard shortcut. All simulation tools remain available below."
    )
    st.caption("Simple view highlights the most common tasks." if not advanced_view
               else "Advanced view shows all simulation shortcuts.")
    st.caption("Start with your power mode, then open only the equipment settings you need.")
    st.subheader("1 · Power mode")
    generator_only = st.checkbox("Generator-only mode", value=False,
                                 help="Run on generator power without grid, solar, or battery contribution.")
    grid = st.checkbox("Grid available", value=False, disabled=generator_only)
    gen_enabled = st.checkbox("Generator enabled", value=False, disabled=generator_only)
    st.divider()
    st.subheader("2 · Generator")
    with st.expander("Generator model, power & fuel", expanded=generator_only or gen_enabled):
        st.caption("Select your generator, fuel and continuous running rating.")
        st.caption("Choose a model and fuel, then enter its running power.")
        # Fuel-specific ratings are entered by the user; no manufacturer data is assumed.
        if "generator_power_setting" not in st.session_state:
            st.session_state.generator_power_setting = 5.0
        if "generator_fuel_ratings" not in st.session_state:
            st.session_state.generator_fuel_ratings = {}
        profile_name = st.selectbox("Generator profile",
            ["Manual / custom", "FIRMAN T07571", "FIRMAN W03386"])
        fuels = (["Gasoline", "Propane", "Natural gas"] if profile_name == "FIRMAN T07571"
                 else ["Gasoline"] if profile_name == "FIRMAN W03386"
                 else ["Gasoline", "Propane", "Natural gas", "Diesel"])
        selected_fuel = st.selectbox("Generator fuel", fuels, key="generator_selected_fuel")
        if profile_name == "Manual / custom":
            gen_kw = st.slider("Generator power (kW)", 0.0, 20.0,
                               st.session_state.generator_power_setting, 0.5)
            st.session_state.generator_power_setting = gen_kw
        else:
            profile_key = f"{profile_name}:{selected_fuel}"
            rated_kw = st.number_input("Verified continuous running rating (kW)",
                min_value=0.0, max_value=20.0,
                value=float(st.session_state.generator_fuel_ratings.get(profile_key, 0.0)),
                step=0.1, key=f"gen_rating_{profile_key}",
                help="Use the nameplate/manual continuous rating for this fuel, not peak surge power.")
            st.session_state.generator_fuel_ratings[profile_key] = rated_kw
            gen_kw = rated_kw
            if (gen_enabled or generator_only) and not gen_kw:
                st.warning("Enter a verified continuous rating for the selected fuel.")
        st.caption(f"{profile_name} · {selected_fuel} · {gen_kw:.1f} kW running")
        if gen_kw <= 0:
            st.caption("Enter a positive running rating to model generator output.")
        elif not gen_enabled and not generator_only:
            st.caption("Generator is off in the main simulation; comparisons can still enable it.")
        with st.expander("Fuel use & runtime estimate", expanded=False):
            st.caption("Optional planning inputs, not verified manufacturer consumption curves.")
            fuel_units = "gal" if selected_fuel in ("Gasoline", "Diesel") else (
                "lb" if selected_fuel == "Propane" else "ft³")
            fuel_available = st.number_input(f"Available fuel ({fuel_units})", min_value=0.0,
                                              value=0.0, step=1.0, key=f"fuel_amount_{selected_fuel}")
            fuel_rate = st.number_input(f"Estimated consumption at chosen load ({fuel_units}/hour)",
                                         min_value=0.0, value=0.0, step=0.1,
                                         key=f"fuel_rate_{profile_name}_{selected_fuel}")
            profile_fuel_price = st.number_input(f"Fuel price ($/{fuel_units})", min_value=0.0,
                value=0.0, step=0.01, key=f"profile_price_{profile_name}_{selected_fuel}")
            if fuel_rate > 0:
                st.metric("Estimated runtime", f"{fuel_available / fuel_rate:.1f} hours")
                if profile_fuel_price > 0:
                    st.metric("Fuel inventory value", f"${fuel_available * profile_fuel_price:,.2f}")
                st.caption("Constant consumption assumed. Actual fuel rate varies with load, "
                           "temperature, engine condition and fuel supply.")
            else:
                st.info("Enter a positive consumption rate to estimate runtime.")
            st.caption("For multi-day outage modeling, enable profile linking in the fuel calculator.")
    st.divider()
    st.subheader("3 · Solar panels")
    with st.expander("Solar array and location", expanded=False):
        st.caption("Set your solar capacity and optional seasonal conditions.")
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
    st.divider()
    st.subheader("4 · Battery storage")
    with st.expander("Battery and inverter settings", expanded=False):
        st.caption("Set storage capacity, inverter power and starting charge.")
        battery = st.slider("Battery capacity (kWh)", 0.0, 60.0, 14.0, 0.5, disabled=generator_only)
        inverter = st.slider("Battery inverter limit (kW)", 0.0, 20.0, 5.0, 0.5, disabled=generator_only)
        initial = st.slider("Initial battery charge (%)", 10, 100, 50, disabled=generator_only)

# Keep all simulation tools available; only reduce the number of shortcuts.
# This CSS is injected after sidebar widgets so changing the toggle reruns it.
if not advanced_view:
    st.html("""<style>
    /* Simple mode should feel like four quick actions, not a ten-tool catalog. */
    .sim-nav .sim-nav-group, .sim-nav a.sim-nav-advanced {display:none!important}
    .sim-nav {grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
    .sim-nav a {padding:14px 12px}
    @media(max-width:650px) {
      .sim-nav {grid-template-columns:repeat(2,minmax(0,1fr))}
    }
    </style>""")

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
st.markdown("### Your energy system")
st.caption("A quick summary of your setup. Change equipment in the sidebar.")
mode_label = "Generator only" if generator_only else (
    "Grid + backup" if grid else "Off-grid / outage"
)
overview_a, overview_b, overview_c, overview_d = st.columns(4)
overview_a.metric("Operating mode", mode_label)
overview_b.metric("Solar array", f"{solar:.1f} kW")
overview_c.metric("Battery storage", f"{battery:.1f} kWh")
overview_d.metric("Generator", f"{gen_kw:.1f} kW" if gen_enabled else "Disabled")
if generator_only:
    st.caption("Generator-only mode bypasses solar and battery contributions.")
elif not grid and not gen_enabled and battery <= 0 and solar <= 0:
    st.warning("No power sources are enabled. Household demand will be unserved.")
st.divider()

with st.expander("View system connection diagram", expanded=False):
    # A schematic of configured sources, not measured real-time power flow.
    st.markdown("#### How your system connects")
    st.caption("A simplified power-flow diagram, not electrical installation instructions.")
    solar_active = solar > 0 and not generator_only
    battery_active = battery > 0 and inverter > 0 and not generator_only
    generator_active = gen_enabled and gen_kw > 0
    grid_active = grid and not generator_only
    def source_card(label, detail, active):
        state = "active" if active else "inactive"
        status = "Enabled" if active else "Off"
        return (f'<div class="sim-flow-source {state}"><strong>{label}</strong>'
                f'<span>{detail}</span><small>{status}</small></div>')
    flow_sources_html = "".join([
        source_card("☀️ Solar", f"{solar:.1f} kW", solar_active),
        source_card("🔋 Battery", f"{battery:.1f} kWh · {inverter:.1f} kW inverter", battery_active),
        source_card("⛽ Generator", f"{gen_kw:.1f} kW", generator_active),
        source_card("🔌 Grid", "Utility connection", grid_active),
    ])
    st.html("""
    <style>
    .sim-flow-grid{display:grid;grid-template-columns:minmax(0,2fr) 40px minmax(0,1fr);
    gap:12px;align-items:center;margin:12px 0 24px}
    .sim-flow-sources{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .sim-flow-source,.sim-flow-home{border:1px solid rgba(116,144,172,.35);border-radius:13px;
    padding:14px;display:flex;flex-direction:column;gap:5px;min-width:0;background:rgba(116,144,172,.08)}
    .sim-flow-source strong,.sim-flow-home strong{font-size:.96rem}
    .sim-flow-source span,.sim-flow-home span{font-size:.8rem;opacity:.8;overflow-wrap:anywhere}
    .sim-flow-source small{font-size:.73rem;font-weight:650}
    .sim-flow-source.inactive{opacity:.43}
    .sim-flow-source.active{border-color:rgba(60,160,120,.7);background:rgba(60,160,120,.09)}
    .sim-flow-arrow{text-align:center;font-size:1.7rem;opacity:.7}
    .sim-flow-home{min-height:115px;justify-content:center;align-items:center;text-align:center}
    @media(max-width:650px){.sim-flow-grid{grid-template-columns:1fr;gap:6px}
    .sim-flow-arrow{transform:rotate(90deg)}.sim-flow-source{padding:10px}}
    </style>
    <div class="sim-flow-grid">
    <div class="sim-flow-sources">""" + flow_sources_html + """</div>
    <div class="sim-flow-arrow" aria-hidden="true">➜</div>
    <div class="sim-flow-home"><strong>🏠 Household loads</strong>
    <span>Hourly appliance demand</span></div>
    </div>
    """)
st.html('<span id="critical-loads" class="sim-section-anchor"></span>')
with st.expander("Essential circuits", expanded=False):
    st.caption("Estimate which circuits can operate together during a grid outage. "
               "This planning worksheet does not change the 24-hour simulation.")
    if "critical_circuits" not in st.session_state:
        st.session_state.critical_circuits = [
            {"Circuit": "Refrigerator", "Running W": 150, "Startup W": 900, "Essential": True},
            {"Circuit": "Freezer", "Running W": 120, "Startup W": 720, "Essential": True},
            {"Circuit": "Lighting", "Running W": 200, "Startup W": 200, "Essential": True},
            {"Circuit": "Internet / electronics", "Running W": 100, "Startup W": 100, "Essential": True},
            {"Circuit": "Central AC / heat pump", "Running W": 3500, "Startup W": 9000, "Essential": False},
            {"Circuit": "Water heater", "Running W": 4500, "Startup W": 4500, "Essential": False},
        ]
    circuit_rows = st.data_editor(
        pd.DataFrame(st.session_state.critical_circuits), num_rows="dynamic",
        hide_index=True, use_container_width=True, key="critical_circuit_editor",
        column_config={
            "Circuit": st.column_config.TextColumn("Circuit / appliance", required=True),
            "Running W": st.column_config.NumberColumn("Running W", min_value=0, required=True),
            "Startup W": st.column_config.NumberColumn("Startup W", min_value=0, required=True),
            "Essential": st.column_config.CheckboxColumn("Essential"),
        },
    )
    if circuit_rows.isna().any().any():
        st.warning("Complete every circuit field to calculate a valid backup estimate.")
    elif (circuit_rows["Startup W"] < circuit_rows["Running W"]).any():
        st.warning("Startup watts should not be lower than running watts.")
    else:
        selected = circuit_rows.loc[circuit_rows["Essential"].astype(bool)]
        running_w = float(selected["Running W"].sum())
        # Conservative single-largest-start assumption, not simultaneous motor starts.
        largest_surge = float((selected["Startup W"] - selected["Running W"]).max()) if len(selected) else 0.0
        startup_w = running_w + largest_surge
        c1, c2, c3 = st.columns(3)
        c1.metric("Essential running load", f"{running_w / 1000:.2f} kW")
        c2.metric("Estimated startup requirement", f"{startup_w / 1000:.2f} kW")
        c3.metric("Selected circuits", len(selected))
        available_kw = gen_kw if generator_active else 0.0
        if generator_active:
            if startup_w / 1000 > available_kw:
                st.warning(f"Estimated startup requirement exceeds the configured {available_kw:.1f} kW generator. "
                           "Consider load sequencing or a larger appropriately rated unit.")
            else:
                st.success("Selected loads fit within the configured generator power estimate.")
        else:
            st.info("Enable a generator in the sidebar to compare against its rated power.")
        st.markdown("#### Sequential circuit startup")
        st.caption("Starts one selected circuit at a time, with previously started circuits "
                   "continuing at their running wattage. Compare two startup orders.")
        order_choice = st.radio(
            "Startup order", ["Highest startup watts first", "Worksheet order"],
            horizontal=True, key="critical_startup_order",
        )
        sequence = selected.copy()
        if order_choice == "Highest startup watts first":
            sequence = sequence.sort_values("Startup W", ascending=False, kind="stable")
        sequence_rows = []
        already_running = 0.0
        for _, circuit in sequence.iterrows():
            surge_peak = already_running + float(circuit["Startup W"])
            already_running += float(circuit["Running W"])
            sequence_rows.append({
                "Circuit": str(circuit["Circuit"]),
                "Startup peak (W)": round(surge_peak),
                "Running total after start (W)": round(already_running),
                "Within generator rating": bool(generator_active and surge_peak <= gen_kw * 1000),
            })
        if sequence_rows:
            peak_w = max(row["Startup peak (W)"] for row in sequence_rows)
            st.metric("Peak sequential startup demand", f"{peak_w / 1000:.2f} kW")
            st.dataframe(pd.DataFrame(sequence_rows), hide_index=True, use_container_width=True)
            if generator_active and peak_w > gen_kw * 1000:
                st.warning("At least one startup step exceeds the configured generator rating.")
            elif generator_active:
                st.success("Every modeled sequential startup step fits the configured generator rating.")
            st.download_button("Download startup sequence CSV",
                               pd.DataFrame(sequence_rows).to_csv(index=False).encode("utf-8"),
                               "critical_load_startup_sequence.csv", "text/csv")
        else:
            st.info("Mark at least one circuit as essential to create a startup sequence.")
        st.caption("This simplified model assumes no overlapping starts, instantaneous steady-state "
                   "running loads, and a generator rating available for startup. Verify real surge "
                   "duration, power factor, derating, load shedding, and transfer equipment with a qualified electrician.")
        st.caption("Assumes one additional motor starts while other selected loads run. "
                   "Real startup overlap, power factor, fuel derating and transfer equipment require verification.")
    st.download_button("Download circuit worksheet CSV", circuit_rows.to_csv(index=False).encode("utf-8"),
                       "critical_load_circuits.csv", "text/csv")

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
st.markdown("### Daily energy overview")
st.caption("Summary of the selected 24-hour scenario. Energy values are kWh.")
a, b, c, d = st.columns(4)
a.metric("Demand", f"{summary['demand_kwh']:.1f} kWh")
b.metric("Solar generated", f"{summary['solar_kwh']:.1f} kWh")
c.metric("Generator", f"{summary['generator_kwh']:.1f} kWh")
d.metric("Unserved", f"{summary['unmet_kwh']:.1f} kWh")
df = pd.DataFrame(rows).set_index("hour")
served_kwh = max(0.0, summary["demand_kwh"] - summary["unmet_kwh"])
served_pct = 100 * served_kwh / summary["demand_kwh"] if summary["demand_kwh"] > 0 else 100.0
if summary["demand_kwh"] <= 0:
    st.info("No household demand is configured. Add appliances to see how your system performs.")
elif summary["unmet_kwh"] <= 1e-6:
    st.success("Your system covers all modeled household demand for this 24-hour scenario.")
else:
    st.warning(
        f"Your system covers {served_pct:.1f}% of modeled demand. "
        f"About {summary['unmet_kwh']:.1f} kWh is not supplied over 24 hours. "
        "Try reducing loads or increasing available generation or storage."
    )
st.progress(min(1.0, max(0.0, served_pct / 100)), text=f"Household energy supplied: {served_pct:.1f}%")
st.caption("These results describe one modeled day, not a guarantee of outage runtime or equipment compatibility.")
flow_tab, dispatch_tab, battery_tab, detail_tab = st.tabs(
    ["Power flow", "Energy dispatch", "Battery state", "Hourly data"]
)
with flow_tab:
    st.caption("24-hour energy contributions. Battery discharge and solar generation are shown separately; "
               "not all generated energy necessarily serves household loads.")
    flow_sources = [
        ("Solar generated", float(df["solar_kwh"].sum())),
        ("Battery delivered", float(df["battery_delivered_kwh"].sum())),
        ("Generator supplied", float(df["generator_kwh"].sum())),
        ("Grid supplied", float(df["grid_kwh"].sum())),
    ]
    flow_total = sum(value for _, value in flow_sources)
    flow_cols = st.columns(4)
    for column, (label, value) in zip(flow_cols, flow_sources):
        with column:
            st.metric(label, f"{value:.1f} kWh")
    st.markdown("**Supply contributions (relative share)**")
    if flow_total > 0:
        for label, value in flow_sources:
            st.caption(f"{label}: {value:.1f} kWh ({value / flow_total:.0%} of reported supply)")
            st.progress(min(1.0, value / flow_total))
    else:
        st.info("No energy supply was recorded for this scenario.")
    left, middle, right = st.columns([2, 1, 2], vertical_alignment="center")
    with left:
        st.markdown("**Available energy sources**")
        st.caption("Solar · Battery · Generator · Grid")
    with middle:
        st.markdown("### →")
    with right:
        st.markdown("**Household demand**")
        st.metric("Served energy", f"{served_kwh:.1f} kWh")
        st.metric("Unserved energy", f"{summary['unmet_kwh']:.1f} kWh")
    st.caption("This is an energy summary, not an electrical wiring diagram or an instantaneous "
               "power-flow calculation. Supply totals may include charging and conversion effects.")
with dispatch_tab:
    st.caption("Hourly supply contributions, demand, and unmet load.")
    st.line_chart(df[["demand_kwh", "solar_kwh", "battery_delivered_kwh",
                      "generator_kwh", "grid_kwh", "unmet_kwh"]])
with battery_tab:
    st.caption("Battery state of charge through the simulation.")
    st.line_chart(df[["soc"]])
with detail_tab:
    st.dataframe(df, use_container_width=True)
st.download_button("Download simulation CSV", df.to_csv().encode("utf-8"),
                   "energy_simulation.csv", "text/csv")
st.info("Load is synthetic. Solar model is approximate clear-sky geometry, not measured weather. Longitude is recorded but hours use local solar time; no time-zone or equation-of-time correction. No surge loads, temperature, fuel or shading modeled.")


st.html('<span id="battery-bank" class="sim-section-anchor"></span>')
with st.expander("Battery bank designer", expanded=False):
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


st.html('<span id="outage" class="sim-section-anchor"></span>')
with st.expander("Outage simulation", expanded=False):
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


st.html('<span id="hvac" class="sim-section-anchor"></span>')
with st.expander("Heating, cooling & generator sizing", expanded=False):
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


st.html('<span id="generator-fuel" class="sim-section-anchor"></span>')
with st.expander("Generator fuel & runtime", expanded=False):
    st.caption("Two fuel input sources are available: a load-dependent detailed fuel curve below, or the generator profile in the sidebar. Choose which one drives the integrated outage simulation.")
    from home_energy_simulator.fuel import FuelModel
    with st.expander("Detailed fuel curve inputs", expanded=False):
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
    st.markdown("#### Choose fuel settings for outage simulation")
    st.caption("The sidebar worksheet is the quick constant-rate option. The detailed curve above models consumption at different generator loads.")
    link_profile_fuel = st.checkbox(
        "Use sidebar generator profile (constant consumption)",
        value=False, key="link_generator_profile_fuel",
        help="Uses the profile's user-entered constant consumption estimate. "
             "Disable to use the detailed fuel curve above.",
    )
    profile_fuel_error = None
    profile_inventory_internal = None
    if link_profile_fuel:
        profile_rate = float(fuel_rate)
        profile_amount = float(fuel_available)
        if selected_fuel == "Diesel":
            profile_fuel_error = "Diesel is not supported by the outage fuel model."
        elif gen_kw <= 0:
            profile_fuel_error = "Enter a positive generator continuous running rating."
        elif profile_rate <= 0:
            profile_fuel_error = "Enter a positive consumption rate in the profile fuel worksheet."
        elif selected_fuel == "Propane":
            st.caption("Propane profile quantities are in pounds; the outage engine uses liquid gallons.")
            propane_lb_per_gal = st.number_input(
                "Propane conversion (lb per liquid gallon)", min_value=0.1,
                value=4.2, step=0.1,
                help="Approximate conversion; verify against fuel temperature and supplier data.")
            profile_rate_internal = profile_rate / propane_lb_per_gal
            profile_inventory_internal = profile_amount / propane_lb_per_gal
            profile_kind = "propane"
        elif selected_fuel == "Natural gas":
            profile_rate_internal = profile_rate  # profile ft³/h; fuel engine uses ft³/h
            profile_inventory_internal = profile_amount
            profile_kind = "natural_gas"
        else:
            profile_rate_internal = profile_rate  # gasoline profile gallons/h
            profile_inventory_internal = profile_amount
            profile_kind = "gasoline"
        if profile_fuel_error:
            st.error(profile_fuel_error)
        else:
            st.info("Profile-linked outage mode assumes constant fuel consumption while generating. "
                    "The entered fuel quantity is finite; no automatic refill is assumed.")
    st.markdown("#### Active outage fuel assumptions")
    if link_profile_fuel and not profile_fuel_error:
        st.success("Using sidebar generator profile for integrated outage calculations.")
        st.caption(f"Fuel: {selected_fuel} | Generator: {gen_kw:.1f} kW | "
                   f"Fuel available: {fuel_available:.2f} {fuel_units} | "
                   f"Constant burn: {fuel_rate:.2f} {fuel_units}/h | "
                   f"Price: ${profile_fuel_price:.2f}/{fuel_units}")
        st.caption("Detailed calculator inputs below remain independent planning estimates.")
    elif link_profile_fuel:
        st.warning("Sidebar profile selected, but inputs are invalid. Outage results are blocked.")
    else:
        st.info("Using the detailed fuel curve and inventory below for integrated outage calculations.")
        st.caption(f"Fuel: {fuel_kind.replace('_', ' ').title()} | "
                   f"Rated: {rated_fuel_kw:.1f} kW | "
                   f"Idle/full rates: {idle_rate:.2f}/{full_rate:.2f} {fuel_unit}/h | "
                   f"Inventory: {'unlimited' if not use_finite_fuel else str(inventory) + ' ' + fuel_unit}")
    st.markdown("#### Detailed fuel curve estimate")
    fuel_model = FuelModel(fuel_kind, rated_fuel_kw, idle_rate * fuel_to_internal,
                           full_rate * fuel_to_internal, fuel_price / fuel_to_internal)
    fuel_result = fuel_model.estimate(load_fuel_kw, operation_hours,
                                      inventory * fuel_to_internal if use_finite_fuel else None)
    fm1, fm2, fm3, fm4 = st.columns(4)
    fm1.metric("Estimated fuel rate", f"{fuel_result['fuel_rate_per_hour'] / fuel_to_internal:.2f} {fuel_unit}/h")
    fm2.metric("Fuel needed", f"{fuel_result['fuel_needed'] / fuel_to_internal:.1f} {fuel_unit}")
    fm3.metric("Fuel cost (full duration)", f"${fuel_result['fuel_cost']:,.2f}")
    fm4.metric("Estimated runtime with inventory",
               "Not limited" if fuel_result["available_runtime_hours"] is None else f"{fuel_result['available_runtime_hours']:.1f} hours")
    if use_finite_fuel and fuel_result["supplied_hours"] < operation_hours:
        st.warning(f"Inventory covers approximately {fuel_result['supplied_hours']:.1f} of {operation_hours:.1f} planned hours.")
    st.info("Linear idle-to-full-load consumption is illustrative. Use manufacturer-measured fuel rates. Natural gas is entered as gaseous liters at consistent reference conditions; internal calculations use cubic feet. The separate outage simulator uses a fixed hourly fuel-rate model.")


st.html('<span id="fuel-aware-outage" class="sim-section-anchor"></span>')
with st.expander("Multi-day outage with fuel limits", expanded=False):
    st.caption("Uses the household load, solar, battery and generator settings, with the fuel source selected in the generator fuel calculator.")
    outage_fuel_model = fuel_model
    outage_fuel_inventory = inventory * fuel_to_internal if use_finite_fuel else None
    outage_fuel_unit = fuel_unit
    outage_fuel_conversion = fuel_to_internal
    if link_profile_fuel and not profile_fuel_error:
        outage_fuel_model = FuelModel(profile_kind, max(gen_kw, 0.1),
                                      profile_rate_internal, profile_rate_internal,
                                      profile_fuel_price * (propane_lb_per_gal if selected_fuel == "Propane" else 1.0))
        outage_fuel_inventory = profile_inventory_internal
        outage_fuel_unit = fuel_units
        outage_fuel_conversion = (profile_inventory_internal / fuel_available
                                  if fuel_available > 0 else
                                  (1.0 / propane_lb_per_gal if selected_fuel == "Propane" else 1.0))
    elif link_profile_fuel:
        st.error("Invalid linked profile; outage results will be withheld.")
    integrated = simulate_outage(
        SystemConfig(solar_kw=solar, battery_kwh=battery, inverter_kw=inverter,
                     initial_soc=initial / 100, generator_enabled=gen_enabled,
                     generator_kw=gen_kw, grid_available=False),
        loads, sun, days=outage_days, fuel_model=outage_fuel_model,
        fuel_available=outage_fuel_inventory,
    ) if (not (link_profile_fuel and profile_fuel_error) and (not gen_enabled or gen_kw <= (gen_kw if link_profile_fuel else rated_fuel_kw))) else None
    if integrated is None:
        st.error("Set the fuel model's continuous generator rating at least as high as the generator power in the sidebar.")
    else:
        im1, im2, im3, im4 = st.columns(4)
        im1.metric("Demand served", f"{integrated.fraction_demand_served:.1%}")
        im2.metric("Fuel consumed", f"{integrated.generator_fuel_used / outage_fuel_conversion:.2f} {outage_fuel_unit}")
        im3.metric("Fuel remaining", "Unlimited" if integrated.generator_fuel_remaining is None else
                   f"{integrated.generator_fuel_remaining / outage_fuel_conversion:.2f} {outage_fuel_unit}")
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
            if outage_fuel_inventory is not None:
                st.caption("Running hours are modeled hourly intervals with generator output, not continuous runtime. "
                           "Fuel inventory may limit operation; see unmet demand and the hourly chart below.")
            else:
                st.caption("Fuel supply is assumed unlimited. Enter a finite fuel inventory above to estimate "
                           "runtime constraints for the selected household loads.")
            st.caption("Fuel use and costs follow the generator fuel model settings above, "
                       "including rated output, idle/full-load rates, and fuel price.")
        st.markdown("#### Outage power availability timeline")
        st.caption("Hourly model output; generator fuel exhaustion is inferred from modeled fuel "
                   "availability, not an independently measured shutdown time.")
        timeline = integrated_df.copy()
        timeline["Generator supplying power"] = timeline["generator_kwh"] > 0
        timeline["Demand unmet"] = timeline["unmet_kwh"] > 0
        if "battery_kwh" in timeline.columns:
            timeline["Battery supplying power"] = timeline["battery_kwh"] > 0
        if "solar_kwh" in timeline.columns:
            timeline["Solar supplying power"] = timeline["solar_kwh"] > 0
        st.dataframe(timeline[[c for c in [
            "Generator supplying power", "Battery supplying power",
            "Solar supplying power", "Demand unmet", "generator_fuel_used",
            "unmet_kwh"] if c in timeline.columns]],
            use_container_width=True)
        if outage_fuel_inventory is not None and integrated.generator_fuel_remaining is not None:
            if integrated.generator_fuel_remaining <= 0:
                st.warning("The modeled fuel inventory is depleted by the end of the outage.")
            else:
                st.caption("Fuel remains at the end of the modeled outage.")
        if profile_name != "Manual / custom":
            st.caption(f"Generator profile: {profile_name} ({selected_fuel}), "
                       f"configured continuous rating {gen_kw:.1f} kW. "
                       "The outage fuel curve and inventory are controlled by the "
                       "Generator Fuel & Runtime Calculator above; they are not "
                       "automatically copied from the profile runtime worksheet.")
        st.markdown("#### Backup endurance")
        st.caption("Fuel inventory and battery charge over the outage. Hour 1 is the first modeled interval.")
        endurance = pd.DataFrame(index=integrated_df.index)
        if outage_fuel_inventory is not None:
            endurance[f"Fuel remaining ({outage_fuel_unit})"] = (
                integrated_df["generator_fuel_remaining"].astype(float) / outage_fuel_conversion
            )
        if "soc" in integrated_df.columns and battery > 0 and not generator_only:
            endurance["Battery charge (%)"] = integrated_df["soc"].astype(float) * 100.0
        if not endurance.empty:
            # Separate charts preserve each quantity's units and avoid misleading dual axes.
            if f"Fuel remaining ({outage_fuel_unit})" in endurance:
                st.line_chart(endurance[[f"Fuel remaining ({outage_fuel_unit})"]])
            if "Battery charge (%)" in endurance:
                st.line_chart(endurance[["Battery charge (%)"]])
            st.download_button("Download endurance timeline CSV",
                               endurance.to_csv().encode("utf-8"),
                               "outage_endurance_timeline.csv", "text/csv")
        else:
            st.info("Enter finite generator fuel or enable battery storage to plot endurance.")
        if outage_fuel_inventory is not None and gen_enabled and gen_kw > 0:
            fuel_left = integrated_df["generator_fuel_remaining"].astype(float)
            empty_hours = fuel_left.le(1e-9)
            if empty_hours.any():
                first_empty = int(empty_hours[empty_hours].index[0]) + 1
                st.warning(f"Modeled fuel inventory reaches zero by the end of hour {first_empty}. "
                           "Generator output may stop earlier if less than a full hour's fuel remains.")
            else:
                st.caption("No complete fuel depletion within the simulated interval. "
                           "The generator may still be unable to run another full hour.")
        if integrated.first_unserved_hour is not None:
            st.caption(f"First hour with unmet household demand: {integrated.first_unserved_hour + 1}. "
                       "This may be caused by generation limits, startup assumptions, or fuel shortage; "
                       "it does not necessarily mark fuel exhaustion.")
        st.line_chart(integrated_df[["generator_kwh", "generator_fuel_used", "unmet_kwh"]])
        st.download_button("Download integrated outage CSV", integrated_df.to_csv().encode("utf-8"),
                           "integrated_outage.csv", "text/csv")
        st.info("Fuel is burned only during modeled generator output. An hour is skipped if insufficient fuel remains for the entire hour; partial-hour generation, starting surges and actual fuel curves are not modeled.")


st.html('<span id="backup-comparison" class="sim-section-anchor"></span>')
with st.expander("Compare backup systems", expanded=False):
    st.caption("Compare three configurations against the same household loads and outage duration. "
               "Grid power is disabled for every scenario. This is a modeled comparison, not equipment sizing approval.")
    st.caption("Generator-only: generator, no solar or battery. Battery-only: battery, no solar or generator. "
               "Hybrid: generator, solar and battery using the sidebar capacities.")
    st.markdown("#### Equipment and installation cost assumptions")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        generator_cost = st.number_input("Generator purchase + installation ($)",
                                         min_value=0.0, value=0.0, step=100.0,
                                         key="comparison_generator_cost")
    with cc2:
        battery_cost = st.number_input("Battery + inverter installed ($)",
                                       min_value=0.0, value=0.0, step=100.0,
                                       key="comparison_battery_cost")
    with cc3:
        solar_cost = st.number_input("Solar array installed ($)",
                                     min_value=0.0, value=0.0, step=100.0,
                                     key="comparison_solar_cost")
    st.caption("Enter incremental costs for each component. Defaults of $0 mean costs have not "
               "been provided, not that equipment is free. Fuel costs use the selected outage "
               "fuel model; maintenance, replacement, financing, taxes and grid savings are excluded.")
    st.markdown("#### Long-term ownership assumptions")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        outages_per_year = st.number_input("Similar outages per year", min_value=0.0,
            value=1.0, step=0.5, key="comparison_outages_per_year")
    with lc2:
        generator_maintenance = st.number_input("Generator annual maintenance ($)",
            min_value=0.0, value=0.0, step=25.0, key="comparison_generator_maintenance")
    with lc3:
        solar_battery_maintenance = st.number_input("Solar and battery annual maintenance ($)",
            min_value=0.0, value=0.0, step=25.0, key="comparison_solar_battery_maintenance")
    st.caption("Projections repeat the modeled outage and fuel price. Excludes replacement, "
               "inflation, financing, discounting, taxes, incentives and grid savings.")
    comparison_enabled = st.button("Compare backup configurations", key="run_backup_comparison")
    if comparison_enabled:
        if link_profile_fuel and profile_fuel_error:
            st.error("Correct the linked generator fuel settings before comparing systems.")
        elif gen_kw > 0 and not link_profile_fuel and gen_kw > rated_fuel_kw:
            st.error("The fuel-model continuous rating must cover the selected generator capacity.")
        else:
            comparison_specs = [
                ("Generator only", 0.0, 0.0, 0.0, True),
                ("Battery only", 0.0, battery, inverter, False),
                ("Hybrid solar + battery + generator", solar, battery, inverter, True),
            ]
            comparison_results = []
            for label, cmp_solar, cmp_battery, cmp_inverter, cmp_generator in comparison_specs:
                result = simulate_outage(
                    SystemConfig(
                        solar_kw=cmp_solar, battery_kwh=cmp_battery,
                        inverter_kw=cmp_inverter,
                        initial_soc=initial / 100 if cmp_battery > 0 else 0.0,
                        minimum_soc=0.1 if cmp_battery > 0 else 0.0,
                        generator_enabled=cmp_generator and gen_kw > 0,
                        generator_kw=gen_kw, grid_available=False,
                    ),
                    loads, sun, days=outage_days,
                    fuel_model=outage_fuel_model,
                    fuel_available=outage_fuel_inventory,
                )
                comparison_results.append({
                    "Configuration": label,
                    "Demand served (%)": round(result.fraction_demand_served * 100, 1),
                    "First unmet hour": ("None" if result.first_unserved_hour is None
                                         else str(result.first_unserved_hour + 1)),
                    "Generator hours": result.generator_hours,
                    f"Fuel used ({outage_fuel_unit})": round(
                        result.generator_fuel_used / outage_fuel_conversion, 2),
                    "Fuel cost ($)": round(result.generator_fuel_cost, 2),
                    "Annual operating cost ($)": round(
                        result.generator_fuel_cost * outages_per_year
                        + (generator_maintenance if cmp_generator else 0.0)
                        + (solar_battery_maintenance if cmp_battery > 0 or cmp_solar > 0 else 0.0), 2),
                    "Equipment + installation ($)": round(
                        (generator_cost if cmp_generator else 0.0)
                        + (battery_cost if cmp_battery > 0 else 0.0)
                        + (solar_cost if cmp_solar > 0 else 0.0), 2),
                    "Modeled outage cost ($)": round(
                        (generator_cost if cmp_generator else 0.0)
                        + (battery_cost if cmp_battery > 0 else 0.0)
                        + (solar_cost if cmp_solar > 0 else 0.0)
                        + result.generator_fuel_cost, 2),
                    "Final battery charge (%)": round(result.final_soc * 100, 1)
                    if cmp_battery > 0 else None,
                })
            comparison_df = pd.DataFrame(comparison_results)
            for years in (5, 10, 20):
                comparison_df[f"{years}-year ownership ($)"] = (
                    comparison_df["Equipment + installation ($)"]
                    + years * comparison_df["Annual operating cost ($)"]
                ).round(2)
            st.session_state["backup_comparison_results"] = comparison_df
    # Session state can retain older comparison tables after a deployment.
    from home_energy_simulator.comparison_cache import is_current_comparison_table
    cached_comparison = st.session_state.get("backup_comparison_results")
    if cached_comparison is not None and not is_current_comparison_table(cached_comparison):
        del st.session_state["backup_comparison_results"]
        st.info("Previous comparison results use an older or incomplete format. "
                "Click Compare backup configurations to recalculate.")

    if "backup_comparison_results" in st.session_state:
        summary_df = st.session_state["backup_comparison_results"]
        st.markdown("#### Comparison results")
        if generator_cost <= 0 or (battery > 0 and battery_cost <= 0) or (solar > 0 and solar_cost <= 0):
            st.warning("Some equipment costs are zero or unspecified. Cost rankings may be misleading.")
        if battery <= 0:
            st.info("Battery capacity is zero; battery-only cannot supply power.")
        if solar <= 0:
            st.info("Solar capacity is zero; hybrid has no solar generation.")
        best_coverage = summary_df.loc[summary_df["Demand served (%)"].idxmax()]
        summary_cols = st.columns(2)
        summary_cols[0].metric("Highest demand coverage", str(best_coverage["Demand served (%)"]) + "%")
        summary_cols[0].caption(str(best_coverage["Configuration"]))
        if (generator_cost > 0 and (battery <= 0 or battery_cost > 0)
                and (solar <= 0 or solar_cost > 0)):
            cheapest = summary_df.loc[summary_df["10-year ownership ($)"].idxmin()]
            summary_cols[1].metric("Lowest 10-year cost", "$" + format(cheapest["10-year ownership ($)"], ",.0f"))
            summary_cols[1].caption(str(cheapest["Configuration"]))
        else:
            summary_cols[1].metric("10-year cost ranking", "Incomplete")
            summary_cols[1].caption("Enter equipment prices to compare ownership costs.")
        overview_tab, cost_tab, details_tab = st.tabs([
            "Power reliability", "Ownership costs", "Detailed results"
        ])
        with overview_tab:
            st.dataframe(summary_df[[
                "Configuration", "Demand served (%)", "First unmet hour",
                "Generator hours", "Final battery charge (%)"
            ]], hide_index=True, use_container_width=True)
            st.bar_chart(summary_df.set_index("Configuration")[["Demand served (%)"]])
        with cost_tab:
            st.dataframe(summary_df[[
                "Configuration", "Annual operating cost ($)", "5-year ownership ($)",
                "10-year ownership ($)", "20-year ownership ($)"
            ]], hide_index=True, use_container_width=True)
            st.bar_chart(summary_df.set_index("Configuration")[["10-year ownership ($)"]])
            with st.expander("Upfront equipment and outage fuel costs", expanded=False):
                st.dataframe(summary_df[[
                    "Configuration", "Equipment + installation ($)",
                    "Fuel cost ($)", "Modeled outage cost ($)"
                ]], hide_index=True, use_container_width=True)
        with details_tab:
            st.dataframe(summary_df, hide_index=True, use_container_width=True)
            st.download_button("Download full comparison CSV",
                               summary_df.to_csv(index=False).encode("utf-8"),
                               "backup_system_comparison.csv", "text/csv")
        st.caption("Results are from the last comparison run. Rerun after changing inputs. "
                   "Generator scenarios use the selected capacity regardless of the dashboard toggle. "
                   "Cost projections exclude replacement, inflation, financing and grid savings; "
                   "hourly dispatch does not model starting surges or transfer equipment.")

st.html('<span id="optimization" class="sim-section-anchor"></span>')
with st.expander("Find a better system configuration", expanded=False):
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


st.html('<span id="workspace" class="sim-section-anchor"></span>')
with st.expander("Saved scenarios & reports", expanded=False):
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

# Provide enough scroll runway for anchors near the end of the page even when
# every engineering tool is collapsed. Without this, the browser hits the
# bottom of the document before the target can reach the top of the viewport.
st.html('<div aria-hidden="true" class="sim-scroll-runway"></div><style>.sim-scroll-runway{height:65vh;pointer-events:none}@media(max-width:768px){.sim-scroll-runway{height:75vh}}</style>')
