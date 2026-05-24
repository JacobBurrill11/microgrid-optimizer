import sys
import time
import json
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core.simulation import run_simulation_stream, BATTERY_CAPACITY_KWH
from data.weather import CITIES

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Microgrid AI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
    }
    .agent-header { font-size: 0.75rem; font-weight: 700; margin-bottom: 2px; }
    .agent-body   { font-size: 0.82rem; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "results": [],
        "running": False,
        "replaying": False,
        "stream_gen": None,
        "replay_data": [],
        "replay_idx": 0,
        "use_real_weather": True,
        "city": "San Francisco, CA",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Agent styling ─────────────────────────────────────────────────────────────

AGENT_STYLES = {
    "Forecaster":          {"color": "#1E90FF", "bg": "#E8F4FD"},
    "Demand Manager":      {"color": "#FF8C00", "bg": "#FFF3E0"},
    "Storage Strategist":  {"color": "#228B22", "bg": "#E8F5E9"},
    "Grid Broker":         {"color": "#8B00FF", "bg": "#F3E5F5"},
}

PEAK_RISK_BADGE = {
    "low":    ('<span style="background:#d4edda;color:#155724;padding:2px 10px;'
               'border-radius:12px;font-size:0.8rem;font-weight:700;">LOW</span>'),
    "medium": ('<span style="background:#fff3cd;color:#856404;padding:2px 10px;'
               'border-radius:12px;font-size:0.8rem;font-weight:700;">MEDIUM</span>'),
    "high":   ('<span style="background:#f8d7da;color:#721c24;padding:2px 10px;'
               'border-radius:12px;font-size:0.8rem;font-weight:700;">HIGH</span>'),
}

# Imported from core.simulation — do not redefine here

# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_agent(log: str) -> str:
    for name in AGENT_STYLES:
        if name.lower() in log.lower():
            return name
    return "Unknown"


def _bubble_html(log: str, hour: int) -> str:
    agent = _detect_agent(log)
    style = AGENT_STYLES.get(agent, {"color": "#888", "bg": "#f0f0f0"})
    body = log.split("] ", 1)[-1] if "] " in log else log
    return (
        f'<div style="background:{style["bg"]};border-left:4px solid {style["color"]};'
        f'border-radius:6px;padding:8px 12px;margin:4px 0;color:#1a1a1a;">'
        f'<div class="agent-header" style="color:{style["color"]}">'
        f'{agent} · Hour {hour:02d}:00</div>'
        f'<div class="agent-body" style="color:#1a1a1a;">{body}</div></div>'
    )


def _json_path() -> Path:
    return Path(__file__).parent.parent / "output" / "simulation_results.json"

# ── Advance simulation by one step ───────────────────────────────────────────

def _advance():
    if st.session_state.running and st.session_state.stream_gen:
        try:
            result = next(st.session_state.stream_gen)
            st.session_state.results.append(result)
        except StopIteration:
            st.session_state.running = False
            st.session_state.stream_gen = None
        except Exception as e:
            st.error(f"Simulation error at hour {len(st.session_state.results)}: {e}")
            st.session_state.running = False
            st.session_state.stream_gen = None

    elif st.session_state.replaying:
        idx = st.session_state.replay_idx
        data = st.session_state.replay_data
        if idx < len(data):
            st.session_state.results.append(data[idx])
            st.session_state.replay_idx += 1
        else:
            st.session_state.replaying = False

_advance()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚡ Microgrid Controls")
    st.divider()

    busy = st.session_state.running or st.session_state.replaying

    city = st.selectbox(
        "Simulation city",
        options=list(CITIES.keys()),
        index=list(CITIES.keys()).index(st.session_state.city),
        disabled=busy,
    )
    st.session_state.city = city

    use_real_weather = st.toggle(
        "Use real weather (Open-Meteo)",
        value=st.session_state.use_real_weather,
        disabled=busy,
    )
    st.session_state.use_real_weather = use_real_weather

    if st.button("▶ Run New Simulation", type="primary", disabled=busy, use_container_width=True):
        lat, lon = CITIES[city]
        st.session_state.results = []
        st.session_state.running = True
        st.session_state.replaying = False
        st.session_state.stream_gen = run_simulation_stream(
            use_real_weather=use_real_weather,
            city_name=city,
            latitude=lat,
            longitude=lon,
        )
        st.rerun()

    json_exists = _json_path().exists()
    if st.button(
        "⟳ Replay Saved Results",
        disabled=busy or not json_exists,
        use_container_width=True,
        help="Animates the last saved simulation hour-by-hour" if json_exists else "No saved results yet",
    ):
        with open(_json_path()) as f:
            st.session_state.replay_data = json.load(f)
        st.session_state.results = []
        st.session_state.replay_idx = 0
        st.session_state.replaying = True
        st.session_state.running = False
        st.session_state.stream_gen = None
        st.rerun()

    if st.session_state.replaying:
        st.session_state.replay_speed = st.slider(
            "Replay speed (s / hour)", 0.5, 3.0, 1.0, 0.25
        )

    if st.session_state.running:
        st.info(f"Running… hour {len(st.session_state.results)}/24")
    elif st.session_state.replaying:
        st.info(f"Replaying… hour {len(st.session_state.results)}/{len(st.session_state.replay_data)}")

    st.divider()
    st.markdown("**Agent Color Key**")
    for name, s in AGENT_STYLES.items():
        st.markdown(
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'background:{s["color"]};border-radius:2px;margin-right:6px;"></span>'
            f'<span style="font-size:0.85rem">{name}</span>',
            unsafe_allow_html=True,
        )

# ── Header ────────────────────────────────────────────────────────────────────

results = st.session_state.results

st.markdown("# ⚡ Microgrid AI Dashboard")
weather_label = "🌐 Live weather (Open-Meteo)" if use_real_weather else "🔁 Simulated weather"
active_city = results[0]["city"] if results else st.session_state.city
st.caption(f"{weather_label}  ·  📍 {active_city}")

# ── KPI row ───────────────────────────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)

with k1:
    net = sum(r["financials"]["net_usd"] for r in results)
    st.metric("Total Net Profit", f"${net:.2f}")
    st.caption("Revenue from grid sales minus cost of grid purchases")

with k2:
    if results:
        last = results[-1]
        soc = (last["battery_level_kwh"] / BATTERY_CAPACITY_KWH) * 100
        st.metric("Battery SOC", f"{soc:.1f}%", delta=last["storage_action"].capitalize())
    else:
        st.metric("Battery SOC", "—")

with k3:
    total_solar = sum(r["solar_forecast_kw"] for r in results)
    total_wind = sum(r["wind_forecast_kw"] for r in results)
    st.metric("Renewables Generated", f"{total_solar + total_wind:.1f} kWh")

with k4:
    fossil_total = sum(r.get("fossil_fuel_kw", 0) for r in results)
    st.markdown("**Fossil Fuel Activated**")
    if not results:
        st.markdown('<span style="color:#888;font-size:1.1rem;">—</span>', unsafe_allow_html=True)
    else:
        color = "#DC143C" if fossil_total > 0 else "#228B22"
        label = f"{fossil_total:.1f} kWh used" if fossil_total > 0 else "None used ✓"
        st.markdown(
            f'<span style="color:{color};font-size:1.1rem;font-weight:700;">{label}</span>',
            unsafe_allow_html=True,
        )

st.divider()

if st.session_state.running:
    hour_done = len(results)
    st.progress(hour_done / 24, text=f"Running hour {hour_done + 1}/24 — agents analyzing...")
elif st.session_state.replaying:
    total = len(st.session_state.replay_data)
    done = len(results)
    st.progress(done / max(total, 1), text=f"Replaying hour {done}/{total}")

# ── Middle section: chat + energy/battery charts ──────────────────────────────

chat_col, chart_col = st.columns([1, 1.4])

with chat_col:
    st.subheader("Agent Chat Feed")
    if not results:
        st.caption("Run or replay a simulation to see agents talk.")
    else:
        chat_container = st.container(height=480)
        with chat_container:
            for r in reversed(results):
                soc_pct = (r["battery_level_kwh"] / BATTERY_CAPACITY_KWH) * 100
                label = (
                    f"Hour {r['hour']:02d}:00  ·  {r['peak_risk'].upper()} risk  "
                    f"·  Battery {soc_pct:.0f}%  ·  ${r['financials']['net_usd']:+.3f}"
                )
                with st.expander(label, expanded=(r is results[-1])):
                    bubbles = "".join(_bubble_html(log, r["hour"]) for log in r["agent_logs"])
                    st.markdown(bubbles, unsafe_allow_html=True)

with chart_col:
    hours_x = [r["hour"] for r in results]

    # Energy balance chart
    fig_energy = go.Figure()
    if results:
        fig_energy.add_trace(go.Scatter(
            x=hours_x, y=[r["solar_forecast_kw"] for r in results],
            name="Solar", stackgroup="gen", fillcolor="rgba(255,215,0,0.6)",
            line=dict(color="#FFD700"),
        ))
        fig_energy.add_trace(go.Scatter(
            x=hours_x, y=[r["wind_forecast_kw"] for r in results],
            name="Wind", stackgroup="gen", fillcolor="rgba(32,178,170,0.6)",
            line=dict(color="#20B2AA"),
        ))
        fig_energy.add_trace(go.Scatter(
            x=hours_x, y=[r.get("fossil_fuel_kw", 0) for r in results],
            name="Fossil Fuel", stackgroup="gen", fillcolor="rgba(139,69,19,0.5)",
            line=dict(color="#8B4513"),
        ))
        fig_energy.add_trace(go.Scatter(
            x=hours_x, y=[r["demand_forecast_kw"] for r in results],
            name="Demand", line=dict(color="#DC143C", dash="dash", width=2),
        ))
    fig_energy.update_layout(
        title="Energy Balance: Generation vs Demand",
        xaxis_title="Hour of Day", yaxis_title="Power (kW)",
        height=280, margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_energy, use_container_width=True)

    # Battery SOC chart
    fig_battery = go.Figure()
    if results:
        fig_battery.add_trace(go.Scatter(
            x=hours_x, y=[r["battery_level_kwh"] for r in results],
            name="Battery", mode="lines+markers",
            line=dict(color="#4682B4", width=2), marker=dict(size=5),
        ))
    fig_battery.add_hline(y=BATTERY_CAPACITY_KWH * 0.10, line_dash="dash", line_color="red",
                           annotation_text="10% min", annotation_position="right")
    fig_battery.add_hline(y=BATTERY_CAPACITY_KWH * 0.95, line_dash="dash", line_color="orange",
                           annotation_text="95% max", annotation_position="right")
    fig_battery.update_layout(
        title="Battery State of Charge",
        xaxis_title="Hour of Day", yaxis_title="Battery (kWh)",
        yaxis=dict(range=[0, BATTERY_CAPACITY_KWH * 1.05]),
        height=280, margin=dict(l=40, r=60, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_battery, use_container_width=True)

# ── Bottom row: profit + price charts ────────────────────────────────────────

profit_col, price_col = st.columns(2)

with profit_col:
    fig_profit = go.Figure()
    if results:
        net_per_hour = [r["financials"]["net_usd"] for r in results]
        cumulative = list(itertools.accumulate(net_per_hour))
        final_positive = cumulative[-1] >= 0
        fill_color = "rgba(0,128,0,0.15)" if final_positive else "rgba(220,20,60,0.15)"
        line_color = "#228B22" if final_positive else "#DC143C"
        fig_profit.add_trace(go.Scatter(
            x=hours_x, y=cumulative,
            name="Net Profit", fill="tozeroy", fillcolor=fill_color,
            line=dict(color=line_color, width=2),
        ))
    fig_profit.add_hline(y=0, line_dash="dash", line_color="gray",
                          annotation_text="break-even")
    fig_profit.update_layout(
        title="Cumulative Net Profit",
        xaxis_title="Hour of Day", yaxis_title="Cumulative Net ($)",
        height=300, margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_profit, use_container_width=True)

with price_col:
    fig_price = go.Figure()
    if results:
        fig_price.add_trace(go.Scatter(
            x=hours_x, y=[r["grid_price_per_kwh"] for r in results],
            name="Grid Price", line=dict(color="#FF8C00", width=2),
        ))
    # Peak TOU window shading (5 PM–8 PM = hours 17–20)
    fig_price.add_vrect(
        x0=17, x1=20,
        fillcolor="rgba(255,100,0,0.1)", layer="below", line_width=0,
        annotation_text="Peak TOU", annotation_position="top left",
    )
    fig_price.update_layout(
        title="Grid Electricity Price (TOU)",
        xaxis_title="Hour of Day", yaxis_title="Price ($/kWh)",
        height=300, margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_price, use_container_width=True)

# ── Trigger next rerun AFTER all content has rendered ────────────────────────

if st.session_state.running or st.session_state.replaying:
    if st.session_state.replaying:
        time.sleep(st.session_state.get("replay_speed", 1.0))
    st.rerun()
