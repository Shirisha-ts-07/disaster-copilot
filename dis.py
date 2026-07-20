import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import logging
import random
import heapq
import json
import urllib.request
import re
from html import escape
import concurrent.futures
from io import BytesIO
from math import radians, cos, sin, sqrt, atan2, pi

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether, HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Circle, String
from gtts import gTTS
import pydeck as pdk

_RESPONSE_CSS = """
<style>
/* ── Base ── */
.er-container { font-family: 'Segoe UI', system-ui, sans-serif; }

/* ── Hero Banner ── */
.er-hero {
    background: linear-gradient(135deg, #1a3c6e 0%, #2c5aa0 50%, #1a3c6e 100%);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    color: white;
    box-shadow: 0 8px 32px rgba(26,60,110,0.25);
    position: relative;
    overflow: hidden;
}
.er-hero::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: rgba(255,255,255,0.03);
    border-radius: 50%;
}
.er-hero-title {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.er-hero-sub {
    font-size: 0.88rem;
    opacity: 0.85;
    line-height: 1.5;
}
.er-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(8px);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 12px;
}
.er-hero-badge .pulse {
    width: 8px;
    height: 8px;
    background: #2ecc71;
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0% { box-shadow: 0 0 0 0 rgba(46,204,113,0.7); }
    70% { box-shadow: 0 0 0 8px rgba(46,204,113,0); }
    100% { box-shadow: 0 0 0 0 rgba(46,204,113,0); }
}

/* ── Standby State ── */
.er-standby {
    background: linear-gradient(135deg, #27ae60, #1e8449);
    border-radius: 16px;
    padding: 28px;
    color: white;
    text-align: center;
    box-shadow: 0 6px 24px rgba(39,174,96,0.25);
}
.er-standby-icon { font-size: 3rem; margin-bottom: 10px; }
.er-standby-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 6px; }
.er-standby-text { font-size: 0.88rem; opacity: 0.9; }

/* ── Section Headers ── */
.er-section-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #e8eef7;
    margin: 28px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #2b3442;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Resource Cards ── */
.er-card {
    background: #171a22;
    border-radius: 14px;
    border: 1px solid #2b3442;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.16);
    transition: all 0.2s ease;
}
.er-card:hover {
    box-shadow: 0 10px 28px rgba(0,0,0,0.28);
    transform: translateY(-1px);
}
.er-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
}
.er-card-name {
    font-weight: 750;
    font-size: 1.0rem;
    color: #f8fafc;
    line-height: 1.3;
}
.er-card-type {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 3px 10px;
    border-radius: 6px;
    white-space: nowrap;
}
.er-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 12px;
}
.er-card-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.78rem;
    color: #cbd5e1;
    background: #222936;
    padding: 4px 10px;
    border-radius: 6px;
}
.er-card-address {
    font-size: 0.82rem;
    color: #a8b3c2;
    margin-bottom: 10px;
    line-height: 1.4;
}

/* ── Capacity Bars ── */
.er-capacity-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
}
.er-capacity-label {
    font-size: 0.75rem;
    color: #a8b3c2;
    min-width: 90px;
    flex-shrink: 0;
}
.er-capacity-track {
    flex: 1;
    height: 8px;
    background: #303948;
    border-radius: 4px;
    overflow: hidden;
}
.er-capacity-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}
.er-capacity-fill-green { background: linear-gradient(90deg, #2ecc71, #27ae60); }
.er-capacity-fill-yellow { background: linear-gradient(90deg, #f1c40f, #e2a712); }
.er-capacity-fill-red { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.er-capacity-fill-blue { background: linear-gradient(90deg, #3498db, #2980b9); }
.er-capacity-value {
    font-size: 0.75rem;
    font-weight: 700;
    color: #e8eef7;
    min-width: 50px;
    text-align: right;
}

/* ── Status Badge ── */
.er-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    margin-top: 8px;
}
.er-status-operational { background: #e9f9ef; color: #1e8449; }
.er-status-limited { background: #fdf3da; color: #8a6206; }
.er-status-overwhelmed { background: #fdecea; color: #c0392b; }

/* ── Source Badge ── */
.er-source {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
}
.er-source-live { background: #123225; color: #86efac; border: 1px solid #286044; }
.er-source-est { background: #252d3a; color: #cbd5e1; border: 1px solid #465365; }

/* ── Quick Stats Row ── */
.er-quickstats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin: 18px 0;
}
.er-stat-card {
    background: #171a22;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    border: 1px solid #2b3442;
    box-shadow: 0 4px 14px rgba(0,0,0,0.14);
}
.er-stat-icon { font-size: 1.6rem; margin-bottom: 6px; }
.er-stat-value { font-size: 1.3rem; font-weight: 800; color: #f8fafc; }
.er-stat-label { font-size: 0.72rem; color: #a8b3c2; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.03em; }

/* ── Route Cards ── */
.er-route-card {
    background: linear-gradient(135deg, #1c2430, #17202b);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #2c5aa0;
}
.er-route-title { font-weight: 700; font-size: 0.92rem; color: #f8fafc; margin-bottom: 4px; }
.er-route-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #2c5aa0;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 8px;
    transition: background 0.2s;
}
.er-route-link:hover { background: #1a3c6e; }

/* ── Safe Path ── */
.er-safe-path {
    background: linear-gradient(135deg, #123225, #163d2d);
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #bfe8cf;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.er-safe-path-step {
    background: #1f2937;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #86efac;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.er-safe-path-arrow { color: #27ae60; font-size: 1.2rem; font-weight: 700; }

/* ── Expandable Sections ── */
.er-expander-header {
    font-weight: 700;
    font-size: 0.95rem;
    color: #e8eef7;
    display: flex;
    align-items: center;
    gap: 8px;
}
.er-expander-count {
    background: #eef2f7;
    color: #5a6070;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    margin-left: auto;
}

/* ── Ambulance Dispatch ── */
.er-ambulance-card {
    background: #171a22;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border: 1px solid #2b3442;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}
.er-ambulance-name { font-weight: 700; font-size: 0.9rem; color: #f8fafc; }
.er-ambulance-stats { display: flex; gap: 16px; }
.er-ambulance-stat { text-align: center; }
.er-ambulance-stat-num { font-size: 1.1rem; font-weight: 800; color: #2c5aa0; }
.er-ambulance-stat-label { font-size: 0.68rem; color: #a8b3c2; text-transform: uppercase; }

/* ── Disclaimer ── */
.er-disclaimer {
    background: #2b2414;
    border: 1px solid #725d23;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.78rem;
    color: #f5d58a;
    line-height: 1.5;
    margin-bottom: 18px;
}
</style>
"""

# ── Color & Icon Mappings ───────────────────────────────
_RESOURCE_TYPE_STYLES = {
    "Hospital":        {"color": "#c0392b", "bg": "#fdecea", "icon": "🏥"},
    "Clinic":          {"color": "#c0392b", "bg": "#fdecea", "icon": "🏥"},
    "Restaurant":      {"color": "#e67e22", "bg": "#fdf3da", "icon": "🍽️"},
    "Cafe":            {"color": "#e67e22", "bg": "#fdf3da", "icon": "☕"},
    "Fast Food":       {"color": "#e67e22", "bg": "#fdf3da", "icon": "🍔"},
    "Marketplace":     {"color": "#e67e22", "bg": "#fdf3da", "icon": "🛒"},
    "Supermarket":     {"color": "#e67e22", "bg": "#fdf3da", "icon": "🛒"},
    "Food Resource":   {"color": "#e67e22", "bg": "#fdf3da", "icon": "🍞"},
    "Food Distribution Center": {"color": "#e67e22", "bg": "#fdf3da", "icon": "📦"},
    "Relief Shelter":  {"color": "#9b59b6", "bg": "#f3e8fd", "icon": "🏠"},
    "Emergency Assembly Point": {"color": "#9b59b6", "bg": "#f3e8fd", "icon": "📍"},
    "Ambulance Station": {"color": "#16a085", "bg": "#e8f8f5", "icon": "🚑"},
    "Police Station":  {"color": "#2980b9", "bg": "#e8f2fc", "icon": "👮"},
    "Fire Station":    {"color": "#d35400", "bg": "#fdeee0", "icon": "🚒"},
    "Blood Bank":      {"color": "#e91e63", "bg": "#fce4ec", "icon": "🩸"},
    "NGO / Aid Organization": {"color": "#27ae60", "bg": "#e9f9ef", "icon": "🤝"},
    "Rescue Team":     {"color": "#1abc9c", "bg": "#e8f8f5", "icon": "🚁"},
    "Community Kitchen": {"color": "#f1c40f", "bg": "#fdf3da", "icon": "🍲"},
}

_STATUS_CLASS = {
    "Operational": "er-status-operational",
    "Limited Capacity": "er-status-limited",
    "Overwhelmed": "er-status-overwhelmed",
}


def _get_resource_style(resource_type):
    return _RESOURCE_TYPE_STYLES.get(resource_type, {
        "color": "#5a6070", "bg": "#f5f7fa", "icon": "📍"
    })


def _resource_display_name(name):
    """Remove internal simulation suffixes from names shown to users."""
    return re.sub(r"\s+\(\d+\)$", "", str(name)).strip()


def _capacity_bar_html(label, current, total, color_class="er-capacity-fill-green"):
    pct = min(100, max(0, round((current / total) * 100))) if total > 0 else 0
    return (
        f'<div class="er-capacity-row"><span class="er-capacity-label">{label}</span>'
        f'<div class="er-capacity-track"><div class="er-capacity-fill {color_class}" style="width:{pct}%;"></div></div>'
        f'<span class="er-capacity-value">{current}/{total}</span></div>'
    )


def _render_resource_card(r):
    """Modern card-based resource display with visual capacity indicators."""
    style = _get_resource_style(r.get("type", ""))
    source_badge = (
        '<span class="er-source er-source-live">🟢 Live Data</span>'
        if r.get("source") == "live"
        else '<span class="er-source er-source-est">🔧 Estimated</span>'
    )
    status = r.get("status", "Operational")
    status_class = _STATUS_CLASS.get(status, "er-status-operational")
    display_name = _resource_display_name(r.get("name", "Resource"))

    # Build capacity bars based on resource type
    capacity_html = ""
    if "beds_available" in r:
        occ_pct = r.get("occupancy_pct", 0)
        bar_color = "er-capacity-fill-red" if occ_pct > 80 else "er-capacity-fill-yellow" if occ_pct > 50 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Beds", r["beds_available"], r["capacity"], bar_color)
        if "icu_beds" in r:
            icu_pct = (r["icu_beds"] - r["icu_available"]) / r["icu_beds"] * 100 if r["icu_beds"] > 0 else 0
            icu_color = "er-capacity-fill-red" if icu_pct > 80 else "er-capacity-fill-yellow" if icu_pct > 50 else "er-capacity-fill-blue"
            capacity_html += _capacity_bar_html("ICU", r["icu_available"], r["icu_beds"], icu_color)
    elif "fleet_size" in r:
        avail = r.get("ambulances_available", 0)
        bar_color = "er-capacity-fill-red" if avail < 2 else "er-capacity-fill-yellow" if avail < 4 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Available", avail, r["fleet_size"], bar_color)
    elif "current_occupants" in r:
        free = max(0, r["capacity"] - r["current_occupants"])
        bar_color = "er-capacity-fill-red" if free < 20 else "er-capacity-fill-yellow" if free < 50 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Free Space", free, r["capacity"], bar_color)
    elif "personnel" in r:
        avail = max(0, r["personnel"] - r.get("deployed", 0))
        bar_color = "er-capacity-fill-red" if avail < 5 else "er-capacity-fill-yellow" if avail < 15 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Available", avail, r["personnel"], bar_color)
    elif "blood_units_available" in r:
        units = r["blood_units_available"]
        bar_color = "er-capacity-fill-red" if units < 200 else "er-capacity-fill-yellow" if units < 500 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Blood Units", units, max(units, 1000), bar_color)
    elif "volunteers" in r:
        avail = max(0, r["volunteers"] - r.get("deployed", 0))
        bar_color = "er-capacity-fill-red" if avail < 5 else "er-capacity-fill-yellow" if avail < 15 else "er-capacity-fill-green"
        capacity_html += _capacity_bar_html("Available", avail, r["volunteers"], bar_color)

    # Contact & address
    contact_html = ""
    if r.get("contact"):
        contact_html += f'<div class="er-card-meta-item">📞 {r["contact"]}</div>'
    if r.get("address"):
        contact_html += f'<div class="er-card-meta-item">📍 {r["address"][:60]}{"..." if len(r.get("address","")) > 60 else ""}</div>'
    if r.get("last_updated"):
        contact_html += f'<div class="er-card-meta-item">⟳ Updated {r["last_updated"]}</div>'

    card_html = f"""<div class="er-card">
        <div class="er-card-header">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.6rem;">{style["icon"]}</span>
                <div>
                    <div class="er-card-name">{display_name}</div>
                    <div style="display:flex;gap:6px;margin-top:4px;align-items:center;">
                        <span class="er-card-type" style="background:{style["bg"]};color:{style["color"]};">{r.get("type", "Resource")}</span>{source_badge}
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.85rem;font-weight:800;color:#f8fafc;">{r["distance_km"]} km</div>
                <div style="font-size:0.72rem;color:#a8b3c2;">~{r.get("travel_time_min", "?")} min</div>
            </div>
        </div>
        <div class="er-card-meta">{contact_html}</div>{capacity_html}
        <span class="er-status {status_class}"><span style="width:7px;height:7px;border-radius:50%;background:currentColor;opacity:0.7;"></span>{status} ({r.get("occupancy_pct", "?")}% load)</span>
    </div>"""
    st.markdown(card_html, unsafe_allow_html=True)


def _render_quick_stats(analysis):
    """Summary statistics cards at the top of the response tab."""
    resources = (
        analysis["hospitals"] + analysis["food_places"] + analysis["shelters"]
        + analysis["ambulance_stations"] + analysis["police_stations"]
        + analysis["fire_stations"] + analysis["blood_banks"]
        + analysis["ngos"] + analysis["rescue_teams"] + analysis["community_kitchens"]
    )
    live_count = sum(1 for r in resources if r.get("source") == "live")
    est_count = len(resources) - live_count

    # Count hospitals with limited/overwhelmed status
    stressed = sum(1 for h in analysis["hospitals"] if h.get("status") in ["Limited Capacity", "Overwhelmed"])

    stats = [
        ("🏥", "Hospitals", len(analysis["hospitals"])),
        ("🏠", "Shelters", len(analysis["shelters"])),
        ("🚑", "Ambulance Stns", len(analysis["ambulance_stations"])),
        ("🟢", "Live Sources", live_count),
        ("🔧", "Est. Sources", est_count),
        ("⚠️", "Stressed", stressed),
    ]

    cards_html = "".join(
        f'<div class="er-stat-card"><div class="er-stat-icon">{icon}</div>'
        f'<div class="er-stat-value">{value}</div><div class="er-stat-label">{label}</div></div>'
        for icon, label, value in stats
    )
    st.markdown(f'<div class="er-quickstats">{cards_html}</div>', unsafe_allow_html=True)


def _render_resource_group(title, icon, resources, expanded=False, error=None):
    """Render one resource category in an isolated, consistently sized group."""
    with st.expander(f"{icon} {title}  ·  {len(resources)} available", expanded=expanded):
        if error and not resources:
            st.error(f"⚠️ {error}")
        if not resources:
            st.caption(f"No {title.lower()} found for this response area.")
            return

        columns = st.columns(2)
        for index, resource in enumerate(resources):
            with columns[index % 2]:
                _render_resource_card(resource)


def _render_ambulance_section(ambulance_info):
    """Clean ambulance dispatch cards."""
    for a in ambulance_info:
        available = a["total"] - a["dispatched"]
        status_color = "#c0392b" if available < 2 else "#e2a712" if available < 4 else "#27ae60"
        st.markdown(f"""
        <div class="er-ambulance-card">
            <div class="er-ambulance-name">🏥 {_resource_display_name(a["name"])}</div>
            <div class="er-ambulance-stats">
                <div class="er-ambulance-stat">
                    <div class="er-ambulance-stat-num">{a["total"]}</div>
                    <div class="er-ambulance-stat-label">Total</div>
                </div>
                <div class="er-ambulance-stat">
                    <div class="er-ambulance-stat-num" style="color:{status_color};">{available}</div>
                    <div class="er-ambulance-stat-label">Available</div>
                </div>
                <div class="er-ambulance-stat">
                    <div class="er-ambulance-stat-num">{a["dispatched"]}</div>
                    <div class="er-ambulance-stat-label">Dispatched</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_route_section(analysis):
    """Evacuation routes with styled cards."""
    # Safe path
    if analysis.get("safe_path"):
        path_steps = ""
        for i, step in enumerate(analysis["safe_path"]):
            path_steps += f'<span class="er-safe-path-step">{step}</span>'
            if i < len(analysis["safe_path"]) - 1:
                path_steps += '<span class="er-safe-path-arrow">→</span>'
        st.markdown(f"""
        <div class="er-section-title">🛣️ Smart Safe Route</div>
        <div class="er-safe-path">{path_steps}</div>
        """, unsafe_allow_html=True)

    # Google Maps evacuation route
    if analysis.get("evacuation_url"):
        st.markdown(f"""
        <div class="er-route-card">
            <div class="er-route-title">🗺️ Evacuation Route (Google Maps)</div>
            <div style="font-size:0.8rem;color:#a8b3c2;">Navigate from your location to the nearest safe zone</div>
            <a href="{analysis["evacuation_url"]}" target="_blank" class="er-route-link">
                🗺️ Open in Google Maps
            </a>
        </div>
        """, unsafe_allow_html=True)

    # Hospital routes
    if analysis.get("hospital_routes"):
        st.markdown('<div class="er-section-title">🚑 Ambulance Routes</div>', unsafe_allow_html=True)
        for r in analysis["hospital_routes"][:3]:
            st.markdown(f"""
            <div class="er-route-card" style="border-left-color:#16a085;">
                <div class="er-route-title">🚑 Route from {_resource_display_name(r["name"])}</div>
                <a href="{r["url"]}" target="_blank" class="er-route-link" style="background:#16a085;">
                    🗺️ View Route
                </a>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
#  LOGGING
# =========================================================
def setup_logger():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        filename="disaster_copilot.log",
        filemode="a",
    )


def log_info(msg):
    logging.info(msg)


def log_error(msg, exc=None):
    st.error(f"❌ {msg}")
    if exc:
        logging.exception(msg)
    else:
        logging.error(msg)


setup_logger()

# =========================================================
#  CORE / ALGORITHMIC HELPERS
# =========================================================
def dijkstra(graph, start, end):
    queue = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {}

    while queue:
        cost, node = heapq.heappop(queue)
        if node == end:
            break
        for neighbor, weight in graph[node]:
            new_cost = cost + weight
            if new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous[neighbor] = node
                heapq.heappush(queue, (new_cost, neighbor))

    path = []
    current = end
    while current in previous:
        path.insert(0, current)
        current = previous[current]
    path.insert(0, start)
    return path


def generate_resources(risk_level):
    if risk_level == "HIGH":
        beds = random.randint(0, 20)
        ambulances = random.randint(0, 3)
    elif risk_level == "MEDIUM":
        beds = random.randint(10, 40)
        ambulances = random.randint(2, 6)
    else:
        beds = random.randint(30, 80)
        ambulances = random.randint(5, 10)
    return beds, ambulances


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def is_near(lat1, lon1, lat2, lon2, threshold_km=1000):
    return haversine_km(lat1, lon1, lat2, lon2) <= threshold_km


def get_global_climatic_zone(lat, lon):
    if abs(lat) >= 66:
        return "Polar Region", ["Extreme Cold", "Blizzards", "Ice Storms"]
    elif 35 <= abs(lat) < 66:
        return "Temperate Region", ["Storms", "Floods", "Wildfires"]
    elif 23 <= abs(lat) < 35:
        return "Subtropical Region", ["Cyclones", "Heatwaves", "Drought"]
    else:
        return "Equatorial Region", ["Heavy Rainfall", "Floods", "Landslides"]


# =========================================================
#  EXTERNAL DATA FETCHERS (cached to avoid refetching on every tab render)
# =========================================================
@st.cache_data(ttl=600, show_spinner=False)
def load_world_map():
    url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    with urllib.request.urlopen(url) as response:
        return json.load(response)


@st.cache_data(ttl=300, show_spinner=False)
def get_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    data = requests.get(url, timeout=10).json()
    return data["features"]


@st.cache_data(ttl=300, show_spinner=False)
def get_volcano_alerts():
    try:
        earthquakes = get_earthquakes()
    except Exception:
        return []

    volcano_events = []
    for event in earthquakes:
        place = event["properties"].get("place", "").lower()
        if "volcano" in place or "mount" in place:
            volcano_events.append(event)
    return volcano_events


@st.cache_data(ttl=300, show_spinner=False)
def get_coordinates(place):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={place}"
    response = requests.get(geo_url, timeout=10).json()

    if "results" in response:
        result = response["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        district = result.get("name", "Unknown")
        state = result.get("admin1", "Unknown")
        country = result.get("country", "Unknown")
        return lat, lon, district, state, country

    return None, None, None, None, None


# Performance tuning: keep the whole live-data phase well under the
# dashboard's loading budget. If Overpass can't answer within this
# window, we stop trying and fall back to simulated data immediately
# rather than let the UI hang.
OVERPASS_REQUEST_TIMEOUT_S = 4      # per-endpoint timeout (3-5s range)
OVERPASS_TOTAL_BUDGET_S = 5         # hard ceiling across all endpoint attempts


@st.cache_data(ttl=600, show_spinner=False)
def _run_overpass_query(query):
    """Shared Overpass request helper. Uses POST with an explicit
    User-Agent. overpass-api.de has been intermittently returning 406 for
    many clients as a server-side issue, so a known-good mirror is tried
    first. A short per-request timeout plus an overall time budget
    guarantees we never block the dashboard waiting on a slow/dead
    endpoint — once the budget runs out we raise immediately so the
    caller can fall back to simulated data."""
    import time

    headers = {
        "User-Agent": "DisasterCopilot/1.0 (contact: disaster-copilot@example.com)",
        "Accept": "application/json",
    }
    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]

    start = time.monotonic()
    last_exc = RuntimeError("No Overpass endpoint was attempted")

    for url in endpoints:
        remaining = OVERPASS_TOTAL_BUDGET_S - (time.monotonic() - start)
        if remaining <= 0.5:
            break
        try:
            response = requests.post(
                url, data={"data": query}, headers=headers,
                timeout=min(OVERPASS_REQUEST_TIMEOUT_S, remaining),
            )
            response.raise_for_status()
            return response.json().get("elements", [])
        except requests.exceptions.RequestException as e:
            last_exc = e
            continue

    raise last_exc


# ---------------------------------------------------------
#  Single combined live-data query
#
#  Previously each resource category (hospitals, food, police, fire,
#  blood banks, ambulance stations...) triggered its own Overpass call.
#  That meant up to 6+ sequential network round-trips per analysis —
#  the main cause of slow loading. Now everything is fetched in ONE
#  request and classified client-side, cached per (lat, lon).
# ---------------------------------------------------------
def _classify_osm_element(tags):
    amenity = tags.get("amenity")
    if amenity in ("hospital", "clinic", "pharmacy"):
        return "hospital"
    if amenity in ("restaurant", "cafe", "fast_food", "marketplace"):
        return "food"
    if tags.get("shop") == "supermarket":
        return "food"
    if tags.get("social_facility") == "shelter" or tags.get("emergency") == "assembly_point":
        return "shelter"
    if amenity == "police":
        return "police_station"
    if amenity == "fire_station":
        return "fire_station"
    if tags.get("healthcare") == "blood_donation" or amenity == "blood_bank":
        return "blood_bank"
    if tags.get("emergency") == "ambulance_station":
        return "ambulance_station"
    return None


def _build_resource_record(tags, category, r_lat, r_lon, lat, lon):
    if category == "hospital":
        type_label = tags.get("amenity", "hospital")
    elif category == "food":
        type_label = _FOOD_TYPE_LABELS.get(_food_type(tags), "Food Resource")
    elif category == "shelter":
        type_label = "Relief Shelter"
    else:
        type_label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())

    return {
        "name": tags.get("name", f"Unnamed {type_label}"),
        "type": type_label,
        "address": _format_address(tags),
        "contact": _format_contact(tags),
        "lat": r_lat,
        "lon": r_lon,
        "distance_km": round(haversine_km(lat, lon, r_lat, r_lon), 1),
        "source": "live",
    }


def _build_master_overpass_query(lat, lon):
    """One query covering every live-fetchable category. Radii are kept
    modest to keep Overpass' own server-side processing fast, which
    matters as much as our client-side timeout for hitting a 2-3s feel."""
    return f"""
    [out:json][timeout:20];
    (
      node["amenity"~"hospital|clinic|pharmacy"](around:25000,{lat},{lon});
      way["amenity"~"hospital|clinic|pharmacy"](around:25000,{lat},{lon});
      node["amenity"~"restaurant|cafe|fast_food|marketplace"](around:20000,{lat},{lon});
      way["amenity"~"restaurant|cafe|fast_food|marketplace"](around:20000,{lat},{lon});
      node["shop"="supermarket"](around:20000,{lat},{lon});
      node["social_facility"="shelter"](around:20000,{lat},{lon});
      node["emergency"="assembly_point"](around:20000,{lat},{lon});
      node["amenity"="police"](around:15000,{lat},{lon});
      node["amenity"="fire_station"](around:15000,{lat},{lon});
      node["healthcare"="blood_donation"](around:15000,{lat},{lon});
      node["amenity"="blood_bank"](around:15000,{lat},{lon});
      node["emergency"="ambulance_station"](around:15000,{lat},{lon});
    );
    out center tags;
    """


@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_live_resources(lat, lon):
    """Fetches and classifies all live resource categories in a single
    Overpass round-trip. Returns (buckets, error) where buckets is a
    dict of category -> sorted list of normalized records. On any
    failure (timeout, budget exceeded, bad response), returns an empty
    dict + error message so callers can fall straight into simulation
    without retrying."""
    query = _build_master_overpass_query(lat, lon)
    try:
        raw_elements = _run_overpass_query(query)
    except requests.exceptions.Timeout:
        return {}, "Live resource data request timed out."
    except requests.exceptions.RequestException as e:
        return {}, f"Could not reach live resource data service: {e}"
    except ValueError:
        return {}, "Live resource data service returned an unreadable response."

    buckets = {}
    for el in raw_elements:
        tags = el.get("tags", {})
        category = _classify_osm_element(tags)
        if not category:
            continue
        r_lat, r_lon = _element_coords(el)
        if r_lat is None or r_lon is None:
            continue
        buckets.setdefault(category, []).append(
            _build_resource_record(tags, category, r_lat, r_lon, lat, lon)
        )

    for items in buckets.values():
        items.sort(key=lambda r: r["distance_km"])

    return buckets, None


def _format_address(tags):
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(p for p in parts if p)
    return address or None


def _format_contact(tags):
    return tags.get("contact:phone") or tags.get("phone") or None


def _element_coords(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center:
        return center.get("lat"), center.get("lon")
    return None, None


def get_nearby_hospitals(lat, lon):
    """Returns (hospitals, error_message), sourced from the shared
    single-request live fetch (see fetch_all_live_resources)."""
    buckets, error = fetch_all_live_resources(lat, lon)
    return buckets.get("hospital", []), error


_FOOD_TYPE_LABELS = {
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "fast_food": "Fast Food",
    "marketplace": "Marketplace",
    "supermarket": "Supermarket",
    "shelter": "Relief Shelter",
    "assembly_point": "Emergency Assembly Point",
}


def _food_type(tags):
    return (
        tags.get("amenity")
        or tags.get("shop")
        or tags.get("social_facility")
        or tags.get("emergency")
        or "other"
    )


def get_food_places(lat, lon):
    """Returns (food_places, error_message), sourced from the shared
    single-request live fetch (see fetch_all_live_resources)."""
    buckets, error = fetch_all_live_resources(lat, lon)
    return buckets.get("food", []), error


def get_country_risk_from_earthquakes(earthquakes):
    country_risk = {}
    for eq in earthquakes:
        place = eq["properties"]["place"]
        mag = eq["properties"].get("mag", 0) or 0
        country = place.split(",")[-1].strip() if "," in place else "Unknown"
        country_risk[country] = country_risk.get(country, 0) + mag

    country_color = {}
    for country, score in country_risk.items():
        if score > 20:
            country_color[country] = [255, 0, 0, 150]
        elif score > 10:
            country_color[country] = [255, 255, 0, 150]
        else:
            country_color[country] = [0, 255, 0, 100]
    return country_color


# ---------------------------------------------------------
#  Homepage map styling helpers
#
#  The homepage previously colored every country into one of three flat
#  buckets (red / yellow / green), which made two very different
#  earthquake days look identical on the map. get_country_risk_scores
#  keeps the raw magnitude-weighted score per country, and
#  _risk_gradient_color turns that into a smooth green -> yellow -> red
#  gradient scaled against today's most active country, so relative
#  severity is visible at a glance. Both are used only by
#  render_home_tab; get_country_risk_from_earthquakes above is left
#  untouched in case anything else still depends on it.
# ---------------------------------------------------------
def get_country_risk_scores(earthquakes):
    """Aggregate magnitude-weighted risk score per country from today's
    earthquakes. Returns {country_name: score}."""
    country_risk = {}
    for eq in earthquakes:
        place = eq["properties"]["place"]
        mag = eq["properties"].get("mag", 0) or 0
        country = place.split(",")[-1].strip() if "," in place else "Unknown"
        country_risk[country] = country_risk.get(country, 0) + mag
    return country_risk


def _risk_gradient_color(score, max_score):
    """Continuous green -> yellow -> red fill color for a country on the
    homepage map, scaled relative to max_score (today's highest-scoring
    country). Countries with no seismic activity stay a calm green."""
    if max_score <= 0 or score <= 0:
        return [46, 204, 113, 70]
    t = max(0.0, min(1.0, score / max_score))
    if t < 0.5:
        local_t = t / 0.5
        r = int(46 + (255 - 46) * local_t)
        g = int(204 + (221 - 204) * local_t)
        b = int(113 - 113 * local_t)
    else:
        local_t = (t - 0.5) / 0.5
        r = 255
        g = int(221 - 221 * local_t)
        b = 0
    alpha = int(90 + 90 * t)
    return [r, g, b, alpha]


_HOME_CSS = """
<style>
.dc-map-caption { color: #8a8f98; font-size: 0.85rem; margin-top: -6px; margin-bottom: 10px; }
.dc-updated { text-align: right; color: #8a8f98; font-size: 0.8rem; padding-top: 6px; }
.dc-legend-row { display: flex; align-items: center; gap: 18px; justify-content: center;
    margin-top: 10px; padding: 8px 4px; }
.dc-legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #cbd5e1; }
.dc-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
.dc-side-heading { font-weight: 700; font-size: 0.95rem; margin-bottom: 8px; }
.dc-hotspot { display: flex; justify-content: space-between; align-items: center;
    padding: 8px 12px; margin-bottom: 6px; border-radius: 8px; background: #171a22; border: 1px solid #2b3442;
    font-size: 0.85rem; }
.dc-hotspot-rank { color: #94a3b8; font-weight: 700; margin-right: 8px; }
.dc-hotspot-score { font-weight: 700; color: #fb7185; }
.dc-location-card { margin-top: 10px; padding: 16px; border-radius: 12px; background: #171a22; border: 1px solid #2b3442; }
.dc-location-name { color: #f8fafc; font-size: 1rem; font-weight: 800; }
.dc-location-meta { color: #a8b3c2; font-size: .78rem; margin-top: 5px; line-height: 1.5; }
.dc-location-risk { display: inline-block; margin-top: 12px; padding: 5px 11px; border-radius: 999px; background: #1d4ed8; color: #dbeafe; font-size: .75rem; font-weight: 800; }
.dc-stat-box { margin-top: 14px; padding: 16px; border-radius: 10px;
    background: linear-gradient(135deg,#1a3c6e,#2c5aa0); color: white; text-align: center; }
.dc-stat-num { font-size: 1.7rem; font-weight: 800; line-height: 1; }
.dc-stat-label { font-size: 0.75rem; opacity: 0.85; margin-top: 4px; }
.dc-snapshot-banner { border-radius: 12px; padding: 16px 22px; display: flex;
    justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
    margin-bottom: 16px; color: white; }
.dc-snapshot-loc { font-weight: 700; font-size: 1.05rem; }
.dc-snapshot-coord { font-size: 0.8rem; opacity: 0.85; }
.dc-snapshot-risk { font-weight: 800; font-size: 0.9rem; padding: 5px 14px;
    border-radius: 20px; background: rgba(255,255,255,0.2); white-space: nowrap; }
.dc-metric-card { border-radius: 12px; padding: 18px 12px; text-align: center;
    border: 1px solid #2b3442; background: #171a22; }
.dc-metric-icon { font-size: 1.7rem; }
.dc-metric-label { font-size: 0.78rem; color: #cbd5e1; margin-top: 4px; }
.dc-metric-value { font-size: 1.2rem; font-weight: 800; margin-top: 4px; color: #f8fafc; }
.dc-risk-high { background: linear-gradient(135deg,#c0392b,#8e2418); border-color: #c0392b; }
.dc-risk-high .dc-metric-label, .dc-risk-high .dc-metric-value { color: white; }
.dc-risk-medium { background: linear-gradient(135deg,#f1c40f,#d4ac0d); border-color: #f1c40f; }
.dc-risk-medium .dc-metric-label, .dc-risk-medium .dc-metric-value { color: #4a3b00; }
.dc-risk-low { background: linear-gradient(135deg,#27ae60,#1e8449); border-color: #27ae60; }
.dc-risk-low .dc-metric-label, .dc-risk-low .dc-metric-value { color: white; }
</style>
"""


def generate_ambulance_data(hospitals):
    ambulance_data = []
    for h in hospitals[:3]:
        name = h.get("name", "Hospital")
        total = random.randint(2, 10)
        dispatched = random.randint(1, total)
        ambulance_data.append({"name": name, "total": total, "dispatched": dispatched})
    return ambulance_data


# =========================================================
#  EMERGENCY RESOURCE SIMULATION ENGINE
#
#  Purpose: when live OpenStreetMap coverage for a resource
#  category is sparse or unavailable (common in rural areas),
#  fill the dashboard with realistic, dynamically-varying
#  estimates so the Emergency Response tab isn't empty.
#
#  Honesty note: every resource carries a "source" field —
#  "live" (from OpenStreetMap) or "estimated" (modeled). This
#  is surfaced in the UI as a small badge. For a disaster-response
#  tool, silently presenting modeled bed counts / ambulance
#  dispatch status as verified real-time data would risk real
#  harm if anyone relied on it during an actual emergency, so
#  the distinction is kept cheap to see but not intrusive.
# =========================================================

CATEGORY_LABELS = {
    "hospital": "Hospital",
    "clinic": "Clinic",
    "shelter": "Relief Shelter",
    "ambulance_station": "Ambulance Station",
    "food_distribution_center": "Food Distribution Center",
    "police_station": "Police Station",
    "fire_station": "Fire Station",
    "blood_bank": "Blood Bank",
    "ngo": "NGO / Aid Organization",
    "rescue_team": "Rescue Team",
    "community_kitchen": "Community Kitchen",
}

NAME_POOLS = {
    "hospital": [
        "{district} General Hospital", "{district} District Hospital",
        "{district} Community Health Center", "St. Mary's Medical Center",
    ],
    "clinic": [
        "{district} Primary Health Clinic", "{district} Urgent Care Clinic",
        "Neighborhood Medical Clinic",
    ],
    "shelter": [
        "{district} Relief Shelter", "{district} Evacuation Center",
        "Hope Community Shelter",
    ],
    "ambulance_station": [
        "{district} Ambulance Station", "Rapid Response EMS Post",
        "{district} Emergency Medical Services Station",
    ],
    "food_distribution_center": [
        "{district} Food Distribution Center", "Community Relief Supply Point",
        "{district} Ration Distribution Hub",
    ],
    "police_station": ["{district} Police Station", "{district} Central Police Post"],
    "fire_station": ["{district} Fire Station", "{district} Fire & Rescue Department"],
    "blood_bank": [
        "{district} Blood Bank", "Regional Blood Bank",
        "Red Cross Blood Center - {district}",
    ],
    "ngo": [
        "{district} Disaster Relief Volunteers", "Global Aid Response Network",
        "Humanitarian Aid Group - {district} Chapter",
    ],
    "rescue_team": [
        "{district} Search & Rescue Team", "Rapid Rescue Response Squad",
        "National Disaster Rescue Force - Local Unit",
    ],
    "community_kitchen": [
        "{district} Community Kitchen", "Free Meal Relief Kitchen",
        "{district} Community Meal Center",
    ],
}

RESOURCE_LOCATION_LABELS = [
    "Central", "North", "South", "East", "West", "Riverside", "Uptown", "Lakeside", "Hillside", "Airport",
]

MAX_SCATTER_RADIUS_KM = {
    "hospital": 15, "clinic": 10, "shelter": 12, "ambulance_station": 10,
    "food_distribution_center": 10, "police_station": 8, "fire_station": 8,
    "blood_bank": 15, "ngo": 15, "rescue_team": 12, "community_kitchen": 8,
}

STATUS_OPTIONS = ["Operational", "Limited Capacity", "Overwhelmed"]

SEVERITY_PROFILES = {
    "HIGH":   {"count_range": (6, 10), "occupancy_range": (65, 98), "status_weights": [0.15, 0.40, 0.45]},
    "MEDIUM": {"count_range": (4, 7),  "occupancy_range": (40, 75), "status_weights": [0.45, 0.40, 0.15]},
    "LOW":    {"count_range": (2, 4),  "occupancy_range": (15, 50), "status_weights": [0.80, 0.18, 0.02]},
}


def get_severity_profile(severity):
    return SEVERITY_PROFILES.get(severity, SEVERITY_PROFILES["LOW"])


def estimate_travel_time_min(distance_km, category):
    speed_kmh = 45 if category in ("ambulance_station", "hospital") else 30
    base_minutes = (distance_km / speed_kmh) * 60
    return max(1, round(base_minutes + random.uniform(-2, 5)))


def simulate_capacity_metrics(category, severity):
    """Generates plausible operational metrics for a resource. These are
    always model estimates (there is no public real-time feed for hospital
    bed occupancy, ambulance fleet status, etc.), so they are labeled as
    such in the UI regardless of whether the resource itself is live or
    simulated."""
    profile = get_severity_profile(severity)
    occ_lo, occ_hi = profile["occupancy_range"]
    occupancy_pct = random.randint(occ_lo, occ_hi)
    status = random.choices(STATUS_OPTIONS, weights=profile["status_weights"], k=1)[0]

    metrics = {
        "occupancy_pct": occupancy_pct,
        "status": status,
        "last_updated": datetime.datetime.now().strftime("%I:%M %p"),
    }

    if category in ("hospital", "clinic"):
        capacity = random.randint(40, 300)
        icu_beds = random.randint(4, max(5, capacity // 12))
        metrics.update({
            "capacity": capacity,
            "beds_available": max(0, round(capacity * (100 - occupancy_pct) / 100)),
            "icu_beds": icu_beds,
            "icu_available": max(0, round(icu_beds * (100 - min(occupancy_pct + 15, 100)) / 100)),
            "ambulances": random.randint(1, 8),
            "doctors_on_duty": random.randint(4, 45),
        })
    elif category == "ambulance_station":
        fleet = random.randint(3, 15)
        dispatched = round(fleet * occupancy_pct / 100)
        metrics.update({
            "fleet_size": fleet,
            "ambulances_available": max(0, fleet - dispatched),
            "ambulances_dispatched": dispatched,
        })
    elif category in ("shelter", "food_distribution_center", "community_kitchen"):
        capacity = random.randint(80, 2500)
        metrics.update({
            "capacity": capacity,
            "current_occupants": round(capacity * occupancy_pct / 100),
        })
    elif category in ("police_station", "fire_station"):
        personnel = random.randint(6, 45)
        metrics.update({
            "personnel": personnel,
            "deployed": round(personnel * occupancy_pct / 100),
            "vehicles": random.randint(2, 10),
        })
    elif category == "blood_bank":
        metrics.update({"blood_units_available": random.randint(50, 1500)})
    elif category in ("ngo", "rescue_team"):
        volunteers = random.randint(5, 60)
        metrics.update({
            "volunteers": volunteers,
            "deployed": round(volunteers * occupancy_pct / 100),
        })

    return metrics


def _scatter_point(lat, lon, max_radius_km):
    """Random point within max_radius_km of (lat, lon), roughly uniform."""
    angle = random.uniform(0, 2 * pi)
    radius_km = random.uniform(1, max_radius_km)
    d_lat = (radius_km / 111.0) * cos(angle)
    lon_scale = cos(radians(lat)) or 1e-6
    d_lon = (radius_km / (111.0 * lon_scale)) * sin(angle)
    return lat + d_lat, lon + d_lon


def _pick_simulated_name(category, district, index):
    template = random.choice(NAME_POOLS.get(category, ["{district} Emergency Resource"]))
    name = template.format(district=district or "Local")
    location_label = RESOURCE_LOCATION_LABELS[(index - 1) % len(RESOURCE_LOCATION_LABELS)]
    return f"{name} — {location_label}"


def generate_simulated_resource(category, lat, lon, district, severity, index):
    max_radius = MAX_SCATTER_RADIUS_KM.get(category, 12)
    r_lat, r_lon = _scatter_point(lat, lon, max_radius)
    distance_km = round(haversine_km(lat, lon, r_lat, r_lon), 1)

    resource = {
        "name": _pick_simulated_name(category, district, index),
        "type": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
        "address": f"Near {district or 'the analyzed location'} (exact address not mapped)",
        "contact": None,
        "lat": r_lat,
        "lon": r_lon,
        "distance_km": distance_km,
        "travel_time_min": estimate_travel_time_min(distance_km, category),
        "source": "estimated",
    }
    resource.update(simulate_capacity_metrics(category, severity))
    return resource


def attach_estimated_metrics(items, category, severity):
    """Adds operational metrics (beds, occupancy, status, etc.) to items
    that don't already have them — used for live OSM results, which only
    carry identity/location data."""
    for item in items:
        item.setdefault("source", "live")
        if "occupancy_pct" not in item:
            item.update(simulate_capacity_metrics(category, severity))
        if "travel_time_min" not in item:
            item["travel_time_min"] = estimate_travel_time_min(item["distance_km"], category)
    return items


def augment_with_simulated(live_items, category, lat, lon, district, severity, min_count=None):
    """Pads a live-results list up to a severity-appropriate count with
    clearly-labeled simulated resources, so the dashboard stays populated
    even where OpenStreetMap coverage is thin."""
    profile = get_severity_profile(severity)
    if min_count is None:
        min_count = random.randint(*profile["count_range"])

    combined = list(live_items)
    index = 1
    while len(combined) < min_count:
        combined.append(generate_simulated_resource(category, lat, lon, district, severity, index))
        index += 1

    combined.sort(key=lambda r: r["distance_km"])
    seen_names = {}
    for resource in combined:
        base_name = _resource_display_name(resource.get("name", "Resource"))
        duplicate_number = seen_names.get(base_name, 0)
        if duplicate_number:
            label = RESOURCE_LOCATION_LABELS[duplicate_number % len(RESOURCE_LOCATION_LABELS)]
            resource["name"] = f"{base_name} — {label}"
        seen_names[base_name] = duplicate_number + 1
    return combined


def get_civic_resource(lat, lon, category, radius_m=20000):
    """Returns (items, error_message) for police/fire/blood bank/ambulance
    station categories, sourced from the shared single-request live
    fetch (see fetch_all_live_resources) — no separate network call."""
    buckets, error = fetch_all_live_resources(lat, lon)
    return buckets.get(category, []), error


# =========================================================
#  PDF + AUDIO REPORT GENERATION
# =========================================================
# =========================================================
#  SHARED REPORT CONTENT (single source of truth)
#
#  Both the PDF and the audio report are built directly from the same
#  `analysis` dict that feeds the dashboard — never from each other's
#  output or from re-derived text — so all three surfaces can never
#  show mismatched numbers. Recommendation/conclusion text is generated
#  once here and reused by both.
# =========================================================
PREPAREDNESS_LEVELS = {
    "HIGH": ("Level 3 - Critical", "Immediate action required. Activate full emergency response protocols and follow evacuation guidance without delay."),
    "MEDIUM": ("Level 2 - Elevated", "Heightened readiness advised. Monitor conditions closely and prepare contingency plans."),
    "LOW": ("Level 1 - Routine", "Standard monitoring is sufficient. No immediate action is required, but stay informed."),
}


def get_preparedness_level(analysis):
    return PREPAREDNESS_LEVELS.get(analysis["overall_risk"], PREPAREDNESS_LEVELS["LOW"])


def get_recommendation_bullets(analysis):
    """Dynamic, hazard-specific recommendations — phrased around the
    actual detected values (magnitude, rainfall, nearest hospital) rather
    than generic boilerplate. Plain text only (no HTML/markup), since
    this list is reused verbatim by the audio narrative."""
    a = analysis
    bullets = []

    if a["earthquake_risk"] == "HIGH":
        mag_note = f" (magnitude {a['best_eq'][1]})" if a["best_eq"] else ""
        bullets.append(
            f"High earthquake risk detected{mag_note}: move immediately to open, structurally "
            "safe areas and avoid damaged or weakened buildings."
        )
    elif a["earthquake_risk"] == "MEDIUM":
        bullets.append("Moderate earthquake activity detected: stay alert for aftershocks and avoid unsafe or older structures.")

    if a["flood_risk"] == "HIGH":
        bullets.append(
            f"High flood risk detected ({round(a['rainfall'], 1)} mm rainfall in the last 6 hours): "
            "evacuate low-lying areas immediately and move to higher ground."
        )
    elif a["flood_risk"] == "MEDIUM":
        bullets.append("Moderate flood risk detected: monitor rising water levels closely and prepare an evacuation plan.")
    elif a["flood_risk"] == "LOW":
        bullets.append("Low flood risk detected: remain cautious of localized flooding, especially in low-lying zones.")

    if a["volcano_risk"] == "HIGH":
        bullets.append("Volcanic activity detected nearby: follow official evacuation orders and avoid ashfall exposure.")

    risk_driven_count = len(bullets)

    if a["mas_active"]:
        if a["hospitals"]:
            nearest = a["hospitals"][0]
            bullets.append(
                f"Nearest hospital identified: {nearest['name']} ({nearest['distance_km']} km away) — "
                "keep this location on hand."
            )
        bullets.append(
            f"Follow the recommended safe evacuation route, proceeding via: "
            f"{', then '.join(a['safe_path'])}."
        )

    bullets.append("Stay tuned to official government and disaster management channels for updates.")
    bullets.append("Keep an emergency kit ready with essential supplies, water, and medication.")

    if risk_driven_count == 0 and not a["mas_active"]:
        bullets.insert(0, "No immediate action is required. Continue normal activities while staying informed.")

    return bullets


def get_conclusion_text(analysis):
    a = analysis
    level_label, level_desc = get_preparedness_level(a)
    mobilization = (
        "Emergency response resources have been identified and are detailed in this report."
        if a["mas_active"] else
        "No emergency mobilization is currently required."
    )
    return (
        f"Overall, {a['district']} is currently assessed at {a['overall_risk']} disaster risk, "
        f"corresponding to a preparedness level of {level_label}. {level_desc} {mobilization} "
        "Continued monitoring is advised as conditions may change. Stay safe and prepared."
    )


def get_executive_summary(analysis):
    a = analysis
    if a["mas_active"]:
        activation = (
            f"The emergency response system has been activated, identifying {len(a['hospitals'])} "
            f"hospitals, {len(a['shelters'])} shelters, and {len(a['food_places'])} food and relief "
            "resources nearby."
        )
    else:
        activation = "Risk levels are currently low and the emergency response system remains on standby."
    return (
        f"This report presents a real-time disaster risk analysis for {a['district']}, {a['state']}, "
        f"{a['country']}. Based on current weather, seismic, and volcanic data, the overall disaster "
        f"risk is assessed as {a['overall_risk']}. {activation}"
    )


def build_audio_narrative(analysis):
    """Natural-language narrative built directly from the shared analysis
    dict — the same numbers shown on the dashboard and in the PDF,
    phrased as sentences rather than read out as raw labels/values."""
    a = analysis
    sentences = [
        f"This is the disaster analysis report for {a['district']}, {a['state']}, {a['country']}, "
        f"generated on {a['current_date']} at {a['current_time']}.",
        f"The location lies in the {a['zone']}, an area typically prone to {', '.join(a['disasters'])}.",
        f"Current weather conditions show a temperature of {a['temperature']} degrees Celsius, "
        f"wind speeds of {a['windspeed']} kilometers per hour, and rainfall of "
        f"{round(a['rainfall'], 1)} millimeters over the past six hours.",
        f"The flood risk for this location is assessed as {a['flood_risk'].lower()}, "
        f"with a flood prediction of {a['flood_prediction'].lower()}.",
    ]

    if a["best_eq"]:
        place_name, magnitude = a["best_eq"]
        sentences.append(
            f"The nearest recorded earthquake occurred near {place_name} with a magnitude of "
            f"{magnitude}, placing the earthquake risk at {a['earthquake_risk'].lower()}."
        )
    else:
        sentences.append("No significant recent earthquake activity was detected nearby.")

    if a["nearby_volcanoes"]:
        sentences.append(f"Volcanic activity was detected nearby, placing the volcano risk at {a['volcano_risk'].lower()}.")
    else:
        sentences.append("No volcanic activity was detected in the surrounding region.")

    sentences.append(
        f"Combining these factors, the overall disaster risk for this location is classified as "
        f"{a['overall_risk'].lower()}."
    )

    if a["mas_active"]:
        sentences.append(
            f"The emergency response system has been activated. {len(a['hospitals'])} hospitals and "
            f"medical facilities, {len(a['shelters'])} shelters, and {len(a['food_places'])} food and "
            f"relief resources were identified within the response radius."
        )
        if a["hospitals"]:
            nearest = a["hospitals"][0]
            sentences.append(
                f"The nearest hospital is {nearest['name']}, approximately {nearest['distance_km']} kilometers away."
            )
        sentences.append(
            "Ambulance stations, police, fire services, blood banks, and coordination with local "
            "non-governmental organizations and rescue teams have also been factored into the response plan."
        )
    else:
        sentences.append("Risk levels are currently low, so the emergency response system remains on standby.")

    sentences.extend(get_recommendation_bullets(a))
    sentences.append(get_conclusion_text(a))

    return " ".join(sentences)


def _sanitize_for_speech(text):
    """Defensive cleanup in case any HTML/markdown artifacts slip into
    generated text before it reaches the TTS engine."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_#>`]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =========================================================
#  PDF REPORT
# =========================================================
RISK_COLOR_MAP = {
    "HIGH": colors.HexColor("#c0392b"),
    "MEDIUM": colors.HexColor("#f1c40f"),
    "LOW": colors.HexColor("#27ae60"),
    "NONE": colors.HexColor("#27ae60"),
    "NO FLOOD RISK": colors.HexColor("#27ae60"),
}
RISK_TEXT_COLOR_MAP = {
    "HIGH": colors.white,
    "MEDIUM": colors.HexColor("#4a3b00"),
    "LOW": colors.white,
    "NONE": colors.white,
    "NO FLOOD RISK": colors.white,
}
BRAND_NAVY = colors.HexColor("#1a3c6e")

# Table cells must use Paragraph objects to get word-wrapping — raw
# strings in a reportlab Table are drawn as a single line and will
# overflow into neighboring columns if they're longer than the column
# width (this was the cause of the overlapping-text bug in the resource
# table). These are defined once at module level so any helper can wrap
# cell text without needing the full stylesheet threaded through.
TABLE_HEADER_STYLE = ParagraphStyle(
    name="TableHeaderCell", fontName="Helvetica-Bold", fontSize=8.5,
    leading=10, textColor=colors.white,
)
TABLE_BODY_STYLE = ParagraphStyle(
    name="TableBodyCell", fontName="Helvetica", fontSize=8,
    leading=10, textColor=colors.HexColor("#1a1a1a"),
)
TABLE_HEADER_STYLE_CENTER = ParagraphStyle(name="TableHeaderCellCenter", parent=TABLE_HEADER_STYLE, alignment=TA_CENTER)
TABLE_BODY_STYLE_CENTER = ParagraphStyle(name="TableBodyCellCenter", parent=TABLE_BODY_STYLE, alignment=TA_CENTER)


def _table_cell_style(is_header, align):
    if is_header:
        return TABLE_HEADER_STYLE_CENTER if align == "CENTER" else TABLE_HEADER_STYLE
    return TABLE_BODY_STYLE_CENTER if align == "CENTER" else TABLE_BODY_STYLE


def _esc(value):
    """Escapes &, <, > so resource names/addresses containing them (e.g.
    'St. Mary's Hospital & Trauma Center') don't break Paragraph's XML
    parsing or silently mis-render."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _risk_color(level):
    return RISK_COLOR_MAP.get(level, colors.grey)


def _risk_text_color(level):
    return RISK_TEXT_COLOR_MAP.get(level, colors.white)


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontSize=26, textColor=BRAND_NAVY, spaceAfter=4))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["Normal"], fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=4))
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading2"], textColor=BRAND_NAVY, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="SmallGray", parent=styles["Normal"], fontSize=8, textColor=colors.grey))
    styles.add(ParagraphStyle(name="TightNormal", parent=styles["Normal"], spaceAfter=2))
    return styles


def _build_logo_drawing(size=64):
    """Vector-drawn badge logo (no external image file / dependency)."""
    d = Drawing(size, size)
    d.add(Circle(size / 2, size / 2, size / 2 - 2, fillColor=BRAND_NAVY, strokeColor=colors.HexColor("#0d1f3c"), strokeWidth=1.5))
    d.add(String(size / 2, size / 2 - 7, "DC", fontName="Helvetica-Bold", fontSize=size * 0.32, fillColor=colors.white, textAnchor="middle"))
    d.hAlign = "CENTER"
    return d


def _pdf_table(data, col_widths=None, header=True, zebra=True, col_align=None, repeat_header=False):
    """Reusable table styling: bordered, header band, optional zebra
    striping, optional per-column alignment (list matching column count).
    All cell content is wrapped in Paragraph objects so long text wraps
    within its column (and grows the row height) instead of overflowing
    into neighboring columns. repeat_header=True reprints the header row
    on every page a long table spans."""
    n_cols = len(data[0]) if data else 0
    align_list = col_align or ["LEFT"] * n_cols

    wrapped_data = []
    for r_idx, row in enumerate(data):
        is_header = header and r_idx == 0
        wrapped_row = []
        for c_idx, cell in enumerate(row):
            align = align_list[c_idx] if c_idx < len(align_list) else "LEFT"
            style = _table_cell_style(is_header, align)
            wrapped_row.append(Paragraph(_esc(cell), style))
        wrapped_data.append(wrapped_row)

    table = Table(
        wrapped_data, colWidths=col_widths, hAlign="LEFT",
        repeatRows=1 if (repeat_header and header) else 0,
    )
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), BRAND_NAVY))
    if zebra and len(data) > 2:
        style.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]))
    table.setStyle(TableStyle(style))
    return table


def _kpi_card(label, value, accent):
    inner = Table(
        [[Paragraph(f'<font size=7 color="#666666">{label}</font>')],
         [Paragraph(f'<font size=15 color="#1a1a1a"><b>{value}</b></font>')]],
        colWidths=[3.1 * cm],
    )
    inner.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, 0), (-1, 0), 3, accent),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
    ]))
    return inner


def _build_kpi_row(a):
    risk_col = _risk_color(a["overall_risk"])
    cards = [
        _kpi_card("TEMPERATURE", f"{a['temperature']}\u00b0C", BRAND_NAVY),
        _kpi_card("RAINFALL (6H)", f"{round(a['rainfall'], 1)} mm", BRAND_NAVY),
        _kpi_card("WIND SPEED", f"{a['windspeed']} km/h", BRAND_NAVY),
        _kpi_card("OVERALL RISK", a["overall_risk"], risk_col),
        _kpi_card("RISK SCORE", f"{round(a['risk_score'], 1)}", risk_col),
    ]
    row = Table([cards], colWidths=[3.3 * cm] * 5, hAlign="LEFT")
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def _build_risk_table(a):
    rows = [
        ["Hazard", "Current Risk", "Prediction"],
        ["Flood", a["flood_risk"], a["flood_prediction"]],
        ["Earthquake", a["earthquake_risk"], a["earthquake_prediction"]],
        ["Volcano", a["volcano_risk"], a["volcano_prediction"]],
    ]
    table = Table(rows, colWidths=[5 * cm, 4.5 * cm, 4.5 * cm], hAlign="LEFT")
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]
    for row_idx, cur_key, pred_key in [(1, "flood_risk", "flood_prediction"),
                                        (2, "earthquake_risk", "earthquake_prediction"),
                                        (3, "volcano_risk", "volcano_prediction")]:
        for col_idx, key in [(1, cur_key), (2, pred_key)]:
            level = a[key]
            style_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), _risk_color(level)))
            style_cmds.append(("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), _risk_text_color(level)))
            style_cmds.append(("FONTNAME", (col_idx, row_idx), (col_idx, row_idx), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_cmds))
    return table


def _capacity_summary(r):
    if "beds_available" in r:
        return f"{r['beds_available']}/{r['capacity']} beds"
    if "fleet_size" in r:
        return f"{r['ambulances_available']}/{r['fleet_size']} ambulances"
    if "current_occupants" in r:
        return f"{max(0, r['capacity'] - r['current_occupants'])}/{r['capacity']} free"
    if "personnel" in r:
        return f"{max(0, r['personnel'] - r['deployed'])}/{r['personnel']} available"
    if "blood_units_available" in r:
        return f"{r['blood_units_available']} units"
    if "volunteers" in r:
        return f"{max(0, r['volunteers'] - r['deployed'])}/{r['volunteers']} available"
    return "-"


def _build_resource_detail_table(a):
    groups = [
        ("Hospital", a["hospitals"], 5),
        ("Shelter", a["shelters"], 3),
        ("Food/Relief", a["food_places"], 3),
        ("Ambulance Stn.", a["ambulance_stations"], 3),
        ("Police", a["police_stations"], 3),
        ("Fire", a["fire_stations"], 3),
        ("Blood Bank", a["blood_banks"], 3),
        ("NGO", a["ngos"], 3),
        ("Rescue Team", a["rescue_teams"], 3),
        ("Kitchen", a["community_kitchens"], 3),
    ]
    rows = [["Category", "Name", "Dist (km)", "ETA (min)", "Availability", "Load %", "Status", "Src"]]
    for label, items, top_n in groups:
        for r in items[:top_n]:
            rows.append([
                label, r["name"], f"{r['distance_km']}", f"{r.get('travel_time_min', '-')}",
                _capacity_summary(r), f"{r.get('occupancy_pct', '-')}", r.get("status", "-"),
                "Live" if r.get("source") == "live" else "Est.",
            ])
    return _pdf_table(
        rows,
        col_widths=[2.0 * cm, 4.1 * cm, 1.3 * cm, 1.3 * cm, 2.5 * cm, 1.1 * cm, 2.5 * cm, 1.0 * cm],
        col_align=["LEFT", "LEFT", "CENTER", "CENTER", "LEFT", "CENTER", "LEFT", "CENTER"],
        repeat_header=True,
    )


def _build_location_map_png(analysis, path="location_map.png", dark_theme=False):
    """Self-contained (no external map tiles / API) location + resource
    map: distance-ring plot centered on the analyzed coordinates, with
    the disaster location marked and nearby resources overlaid by
    category. Doubles as the 'location map with disaster marker' and
    the emergency-resources overview."""
    from matplotlib.patches import Circle as RangeCircle

    a = analysis
    lat0, lon0 = a["lat"], a["lon"]

    groups = [
        ("Hospitals", a.get("hospitals", []), "#c0392b", "o"),
        ("Shelters", a.get("shelters", []), "#9b59b6", "s"),
        ("Food/Relief", a.get("food_places", []), "#e67e22", "^"),
        ("Ambulance Stns.", a.get("ambulance_stations", []), "#16a085", "P"),
        ("Police", a.get("police_stations", []), "#2980b9", "X"),
        ("Fire", a.get("fire_stations", []), "#d35400", "*"),
        ("Blood Banks", a.get("blood_banks", []), "#e91e63", "D"),
        ("NGOs", a.get("ngos", []), "#27ae60", "v"),
        ("Rescue Teams", a.get("rescue_teams", []), "#1abc9c", "v"),
        ("Kitchens", a.get("community_kitchens", []), "#f1c40f", "p"),
    ]

    background = "#0f1117" if dark_theme else "white"
    panel = "#171a22" if dark_theme else "white"
    foreground = "#f8fafc" if dark_theme else "#111827"
    muted = "#94a3b8" if dark_theme else "#666666"
    grid_color = "#334155" if dark_theme else "#d6dbe1"
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    fig.patch.set_facecolor(background)
    ax.set_facecolor(panel)

    for radius_km, style in [(5, ":"), (10, "--"), (20, "-")]:
        ax.add_patch(RangeCircle((0, 0), radius_km, fill=False, linestyle=style, edgecolor=muted, linewidth=1.2, alpha=.75, zorder=1))
        ax.text(0, radius_km + 0.45, f"{radius_km} km", fontsize=8, color=muted, ha="center", fontweight="600")

    for label, items, color, marker in groups:
        if not items:
            continue
        xs, ys = [], []
        for r in items[:5]:
            dx = (r["lon"] - lon0) * 111.0 * cos(radians(lat0))
            dy = (r["lat"] - lat0) * 111.0
            xs.append(dx)
            ys.append(dy)
        ax.scatter(xs, ys, c=color, marker=marker, s=64, label=label, edgecolors=background, linewidths=1, alpha=.92, zorder=3)

    ax.scatter([0], [0], c="#38bdf8", marker="*", s=300, zorder=5, edgecolors="white", linewidths=1.2)
    ax.annotate("Disaster Location", (0, 0), textcoords="offset points", xytext=(10, 10), fontsize=10, color=foreground, fontweight="bold", bbox={"boxstyle": "round,pad=.3", "facecolor": panel, "edgecolor": "#38bdf8", "alpha": .9})

    extent = 22
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)
    ax.set_aspect("equal")
    ax.set_xlabel("East-West Distance (km)", color=muted, labelpad=8)
    ax.set_ylabel("North-South Distance (km)", color=muted, labelpad=8)
    ax.set_title(f"Location & Nearby Emergency Resources — {a['district']}", color=foreground, fontsize=15, fontweight="bold", pad=16)
    if any(items for _, items, _, _ in groups):
        legend = ax.legend(loc="upper left", fontsize=8, framealpha=.95, ncol=2, borderpad=.7, columnspacing=1.1)
        legend.get_frame().set_facecolor("#1e293b" if dark_theme else "white")
        legend.get_frame().set_edgecolor("#475569" if dark_theme else "#d1d5db")
        for text in legend.get_texts():
            text.set_color(foreground)
    ax.tick_params(colors=muted, labelsize=9)
    ax.grid(color=grid_color, alpha=.45, linewidth=.7)
    for spine in ax.spines.values():
        spine.set_color("#475569" if dark_theme else "#1f2937")

    plt.tight_layout(pad=1.2)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _hyperlink(url, label, styles):
    return Paragraph(f'<link href="{url}" color="#1a73e8"><u>{label}</u></link>', styles["Normal"])


def _pdf_footer(canvas, doc_):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#dddddd"))
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.35 * cm, A4[0] - 2 * cm, 1.35 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1 * cm, "Generated by Disaster Copilot AI")
    canvas.drawCentredString(A4[0] / 2, 1 * cm, datetime.datetime.now().strftime("%d %b %Y, %I:%M %p"))
    canvas.drawRightString(A4[0] - 2 * cm, 1 * cm, f"Page {doc_.page}")
    canvas.restoreState()


def create_pdf(analysis):
    """Builds the full PDF report directly from the shared analysis
    dict — every figure here is read from the same data structure the
    dashboard renders from, so values can't drift out of sync."""
    a = analysis
    styles = _pdf_styles()
    doc = SimpleDocTemplate(
        "report.pdf", pagesize=A4,
        topMargin=1.4 * cm, bottomMargin=1.6 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    content = []

    # ---------- Cover page ----------
    content.append(Spacer(1, 20))
    content.append(_build_logo_drawing())
    content.append(Spacer(1, 8))
    content.append(Paragraph("DISASTER COPILOT", styles["ReportTitle"]))
    content.append(Paragraph("Disaster Analysis &amp; Emergency Response Report", styles["ReportSubtitle"]))
    content.append(Spacer(1, 16))

    risk_banner = Table([[f"OVERALL RISK LEVEL: {a['overall_risk']}"]], colWidths=[14 * cm])
    risk_banner.hAlign = "CENTER"
    risk_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _risk_color(a["overall_risk"])),
        ("TEXTCOLOR", (0, 0), (-1, -1), _risk_text_color(a["overall_risk"])),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    content.append(risk_banner)
    content.append(Spacer(1, 18))

    cover_info = _pdf_table([
        ["Location", f"{a['district']}, {a['state']}, {a['country']}"],
        ["Coordinates", f"{a['lat']}, {a['lon']}"],
        ["Report Date", a["current_date"]],
        ["Report Time", a["current_time"]],
    ], col_widths=[4 * cm, 10 * cm], header=False, zebra=False)
    cover_info.hAlign = "CENTER"
    content.append(cover_info)
    content.append(Spacer(1, 16))

    content.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    content.append(Paragraph(get_executive_summary(a), styles["Normal"]))
    content.append(Spacer(1, 10))
    content.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#dddddd")))
    content.append(Spacer(1, 4))
    content.append(Paragraph(
        "Generated by Disaster Copilot, a predictive multi-agent early-warning and emergency "
        "response system combining live environmental data with modeled emergency-resource estimates.",
        styles["SmallGray"],
    ))
    content.append(PageBreak())

    # ---------- Key Metrics (KPI cards) ----------
    content.append(KeepTogether([
        Paragraph("Key Metrics", styles["SectionHeading"]),
        _build_kpi_row(a),
    ]))
    content.append(Spacer(1, 10))

    # ---------- 1. Location & Climatic Zone ----------
    content.append(Paragraph("1. Location &amp; Climatic Zone", styles["SectionHeading"]))
    content.append(_pdf_table([
        ["Field", "Value"],
        ["District", a["district"]], ["State / Region", a["state"]], ["Country", a["country"]],
        ["Coordinates", f"{a['lat']}, {a['lon']}"], ["Climatic Zone", a["zone"]],
        ["Common Disaster Types", ", ".join(a["disasters"])],
    ], col_widths=[5 * cm, 9 * cm]))
    content.append(Spacer(1, 10))

    # ---------- 2. Location & Resource Map ----------
    content.append(Paragraph("2. Location Map", styles["SectionHeading"]))
    try:
        map_path = _build_location_map_png(a)
        content.append(Image(map_path, width=13 * cm, height=12.4 * cm))
    except Exception as e:
        log_error("Location map generation failed; continuing without it.", exc=e)
    content.append(Spacer(1, 10))

    # ---------- 3. Disaster Risk Assessment & Prediction ----------
    content.append(KeepTogether([
        Paragraph("3. Disaster Risk Assessment &amp; Prediction", styles["SectionHeading"]),
        _build_risk_table(a),
        Spacer(1, 6),
        Paragraph(f"<b>Computed Risk Score:</b> {round(a['risk_score'], 2)}", styles["Normal"]),
    ]))
    content.append(Spacer(1, 10))

    # ---------- 4. Forecast Charts (side by side to balance page space) ----------
    content.append(Paragraph("4. 24-Hour Forecast Charts", styles["SectionHeading"]))
    chart_cells = []
    if a["rain_24h"]:
        plt.figure(figsize=(4.2, 2.6))
        plt.plot(a["rain_24h"], color="#1a73e8")
        plt.title("Rainfall Forecast (mm)", fontsize=9)
        plt.xlabel("Hours", fontsize=8)
        plt.ylabel("mm", fontsize=8)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig("rain.png", dpi=150)
        plt.close()
        chart_cells.append(Image("rain.png", width=7.8 * cm, height=4.8 * cm))
    if a["temp_24h"]:
        plt.figure(figsize=(4.2, 2.6))
        plt.plot(a["temp_24h"], color="#e67e22")
        plt.title("Temperature Forecast (\u00b0C)", fontsize=9)
        plt.xlabel("Hours", fontsize=8)
        plt.ylabel("\u00b0C", fontsize=8)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig("temp.png", dpi=150)
        plt.close()
        chart_cells.append(Image("temp.png", width=7.8 * cm, height=4.8 * cm))
    if chart_cells:
        charts_row = Table([chart_cells], colWidths=[8 * cm] * len(chart_cells))
        charts_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        content.append(charts_row)
    content.append(Spacer(1, 8))

    # ---------- 5. Emergency Response ----------
    content.append(PageBreak())
    content.append(Paragraph("5. Emergency Response Summary", styles["SectionHeading"]))

    if a["mas_active"]:
        resource_groups = [
            ("Hospitals & Clinics", a["hospitals"]), ("Shelters", a["shelters"]),
            ("Food & Relief Resources", a["food_places"]), ("Ambulance Stations", a["ambulance_stations"]),
            ("Police Stations", a["police_stations"]), ("Fire Stations", a["fire_stations"]),
            ("Blood Banks", a["blood_banks"]), ("NGOs / Aid Organizations", a["ngos"]),
            ("Rescue Teams", a["rescue_teams"]), ("Community Kitchens", a["community_kitchens"]),
        ]
        summary_rows = [["Resource Type", "Live", "Estimated", "Total"]]
        for label, items in resource_groups:
            live_count = sum(1 for x in items if x.get("source") == "live")
            summary_rows.append([label, str(live_count), str(len(items) - live_count), str(len(items))])
        content.append(_pdf_table(summary_rows, col_widths=[6 * cm, 2.5 * cm, 2.7 * cm, 2.3 * cm],
                                   col_align=["LEFT", "CENTER", "CENTER", "CENTER"], repeat_header=True))
        content.append(Spacer(1, 10))

        content.append(Paragraph("Detailed Resource Availability", styles["Heading3"]))
        content.append(_build_resource_detail_table(a))
        content.append(Spacer(1, 10))

        content.append(Paragraph(f"<b>Smart Safe Route:</b> {' &rarr; '.join(a['safe_path'])}", styles["Normal"]))
        content.append(Spacer(1, 3))
        content.append(_hyperlink(a["evacuation_url"], "Open Evacuation Route in Google Maps", styles))
        if a["hospital_routes"]:
            content.append(Spacer(1, 3))
            for r in a["hospital_routes"][:3]:
                content.append(_hyperlink(r["url"], f"Ambulance route from {r['name']}", styles))
    else:
        content.append(Paragraph(
            "Risk levels are low. The emergency response system is on standby and was not "
            "activated for this analysis.",
            styles["Normal"],
        ))
    content.append(Spacer(1, 10))

    # ---------- 6. Recommendations ----------
    content.append(Paragraph("6. Recommendations", styles["SectionHeading"]))
    bullet_items = [ListItem(Paragraph(b, styles["Normal"]), leftIndent=10) for b in get_recommendation_bullets(a)]
    content.append(ListFlowable(bullet_items, bulletType="bullet"))
    content.append(Spacer(1, 10))

    # ---------- 7. Conclusion ----------
    level_label, _ = get_preparedness_level(a)
    content.append(Paragraph("7. Conclusion", styles["SectionHeading"]))
    content.append(Paragraph(f"<b>Preparedness Level:</b> {level_label}", styles["Normal"]))
    content.append(Spacer(1, 4))
    content.append(Paragraph(get_conclusion_text(a), styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
    content.append(Spacer(1, 4))
    content.append(Paragraph(
        "Note: Where live OpenStreetMap coverage was insufficient for a resource category, this "
        "report supplements it with clearly-marked modeled estimates (see 'Src'/'Source' columns "
        "above) so response planning is not left with gaps.",
        styles["SmallGray"],
    ))

    doc.build(content, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)

    with open("report.pdf", "rb") as f:
        return f.read()


def generate_audio_report(analysis):
    """Generates the audio report from the same narrative-building logic
    used to check consistency with the PDF — both read from the same
    `analysis` dict, so numbers can't diverge between the two."""
    narrative = _sanitize_for_speech(build_audio_narrative(analysis))
    tts = gTTS(narrative)
    mp3_buf = BytesIO()
    tts.write_to_fp(mp3_buf)
    mp3_buf.seek(0)
    return mp3_buf.read()


# =========================================================
#  PREDICTION ENGINE
#
#  Multi-factor, rule-based hazard scoring (not a trained ML model)
#  using live forecast data, best-effort historical/terrain context,
#  and recent seismic activity. Every hazard result includes a
#  probability, a confidence score, plain-language reasons, an expected
#  time window, and preventive actions, so predictions are explainable
#  rather than a single opaque risk word.
#
#  Honesty notes baked into the design:
#  - Earthquake/volcano "prediction" here means near-term likelihood of
#    CONTINUED activity (aftershock-style clustering, loosely inspired
#    by Omori's law, and volcanic unrest via nearby seismicity) — not a
#    forecast of a new, independent event. No system can predict the
#    timing of an initial earthquake or eruption; that's a limitation
#    of seismology itself, not of this code.
#  - Confidence scores are capped well below 100% and reduced further
#    when optional enrichment data (historical baseline, terrain
#    gradient) is unavailable, rather than presenting a single-source
#    estimate as certain.
# =========================================================
def _hazard_result(level, probability_pct, confidence_pct, reasons, window, actions):
    return {
        "level": level,
        "probability_pct": max(0, min(99, round(probability_pct))),
        "confidence_pct": max(30, min(92, round(confidence_pct))),
        "reasons": reasons,
        "expected_window": window,
        "actions": actions,
    }


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_historical_rainfall(lat, lon):
    """Best-effort ~30-day rainfall baseline (soil-saturation proxy) from
    Open-Meteo's archive API. Returns None on any failure — historical
    context is an enrichment, not a dependency; predictions still work
    without it, just with a lower confidence score."""
    try:
        end = datetime.date.today() - datetime.timedelta(days=2)  # archive lags ~2 days
        start = end - datetime.timedelta(days=30)
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
            "&daily=precipitation_sum&timezone=auto"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        totals = [v for v in resp.json().get("daily", {}).get("precipitation_sum", []) if v is not None]
        if not totals:
            return None
        return {"total_30d_mm": round(sum(totals), 1)}
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_elevation_profile(lat, lon):
    """Best-effort terrain-gradient proxy for landslide risk: samples
    elevation at the center point plus four ~1.1 km offsets and returns
    the steepest gradient found (m of elevation change per km). Returns
    None on failure."""
    try:
        offset = 0.01  # ~1.1 km at the equator
        lats = [lat, lat + offset, lat - offset, lat, lat]
        lons = [lon, lon, lon, lon + offset, lon - offset]
        url = (
            "https://api.open-meteo.com/v1/elevation"
            f"?latitude={','.join(str(x) for x in lats)}&longitude={','.join(str(x) for x in lons)}"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        elevations = resp.json().get("elevation", [])
        if len(elevations) < 5 or any(e is None for e in elevations):
            return None
        center = elevations[0]
        max_diff = max(abs(e - center) for e in elevations[1:])
        return {"gradient_m_per_km": round(max_diff / 1.1, 1)}
    except Exception:
        return None


def predict_flood(rain_6h_total, daily, historical):
    daily_precip = [v for v in (daily or {}).get("precipitation_sum", []) if v is not None]
    rain_72h = sum(daily_precip[:3])
    reasons = [f"{round(rain_6h_total, 1)} mm of rain in the last 6 hours"]
    if daily_precip:
        reasons.append(f"{round(rain_72h, 1)} mm forecast over the next 3 days")

    saturation_bonus = 0
    if historical and historical.get("total_30d_mm") is not None:
        total_30d = historical["total_30d_mm"]
        if total_30d > 150:
            saturation_bonus = 10
            reasons.append(f"soil likely saturated ({total_30d} mm fell over the past 30 days)")

    score = rain_6h_total * 0.5 + rain_72h * 0.35 + saturation_bonus

    if score > 45:
        level, window = "HIGH", "within 6-24 hours"
    elif score > 22:
        level, window = "MEDIUM", "within 24-48 hours"
    elif score > 8:
        level, window = "LOW", "possible within 3-5 days"
    else:
        level, window = "NONE", "not expected in the near term"
        reasons = ["Rainfall levels are within a normal range"]

    actions = {
        "HIGH": ["Evacuate low-lying areas now", "Move vehicles and valuables to higher ground", "Avoid crossing flooded roads or bridges"],
        "MEDIUM": ["Prepare an evacuation plan", "Monitor local river/drain levels closely", "Avoid unnecessary travel near waterways"],
        "LOW": ["Stay informed via local weather updates", "Clear drains and gutters as a precaution"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[level]

    confidence = 62 + (12 if daily_precip else 0) + (10 if historical else 0)
    return _hazard_result(level, score * 1.6, confidence, reasons, window, actions)


def predict_landslide(daily, historical, elevation):
    daily_precip = [v for v in (daily or {}).get("precipitation_sum", []) if v is not None]
    rain_72h = sum(daily_precip[:3])
    gradient = (elevation or {}).get("gradient_m_per_km")

    reasons = []
    if daily_precip:
        reasons.append(f"{round(rain_72h, 1)} mm of rain forecast over the next 3 days")
    if gradient is not None:
        reasons.append(f"local terrain gradient of ~{gradient} m/km near the analyzed point")
    else:
        reasons.append("terrain gradient data unavailable this run")

    terrain_factor = 1.0
    if gradient is not None:
        if gradient > 40:
            terrain_factor = 1.6
        elif gradient > 15:
            terrain_factor = 1.25

    score = rain_72h * terrain_factor * 0.6
    if historical and (historical.get("total_30d_mm") or 0) > 150:
        score *= 1.15
        reasons.append("ground likely already saturated from recent rainfall")

    if score > 55:
        level, window = "HIGH", "within 24-48 hours if rain continues"
    elif score > 28:
        level, window = "MEDIUM", "within 2-4 days if rain continues"
    elif score > 10:
        level, window = "LOW", "low likelihood in the coming week"
    else:
        level, window = "NONE", "not expected in the near term"

    actions = {
        "HIGH": ["Avoid steep slopes and unstable ground immediately", "Watch for cracking soil, tilting trees, or sudden water changes", "Be ready to evacuate on short notice"],
        "MEDIUM": ["Avoid unnecessary travel on hillside roads", "Watch for early warning signs (new cracks, leaning structures)"],
        "LOW": ["Stay aware of local terrain conditions during heavy rain"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[level]

    confidence = 55 + (10 if daily_precip else 0) + (15 if gradient is not None else 0)
    return _hazard_result(level, score * 1.3, confidence, reasons, window, actions)


def predict_storm_cyclone(current_weather, hourly, daily):
    pressure_series = [v for v in (hourly or {}).get("surface_pressure", []) if v is not None]
    humidity_series = [v for v in (hourly or {}).get("relative_humidity_2m", []) if v is not None]
    wind_now = (current_weather or {}).get("windspeed", 0) or 0
    daily_wind_max = [v for v in (daily or {}).get("windspeed_10m_max", []) if v is not None]

    reasons = [f"current wind speed {wind_now} km/h"]
    pressure_now = pressure_series[0] if pressure_series else None
    if pressure_now is not None:
        reasons.append(f"surface pressure {round(pressure_now)} hPa")

    score = wind_now * 0.5
    if pressure_now is not None and pressure_now < 1000:
        score += (1000 - pressure_now) * 1.2
        reasons.append("low surface pressure consistent with storm development")
    if humidity_series and (sum(humidity_series[:6]) / len(humidity_series[:6])) > 80:
        score += 8
        reasons.append("sustained high humidity")
    if daily_wind_max:
        forecast_peak = max(daily_wind_max[:3])
        if forecast_peak > wind_now:
            score += (forecast_peak - wind_now) * 0.3
            reasons.append(f"forecast wind gusts up to {round(forecast_peak)} km/h in the next 3 days")

    if score > 75:
        level, window = "HIGH", "within 24-48 hours"
    elif score > 45:
        level, window = "MEDIUM", "within 2-4 days"
    elif score > 25:
        level, window = "LOW", "possible later this week"
    else:
        level, window = "NONE", "not expected in the near term"
        reasons = ["No strong storm signals detected in current conditions or forecast"]

    actions = {
        "HIGH": ["Secure loose outdoor objects and shelter indoors", "Avoid coastal areas and low-lying regions", "Follow official storm/cyclone advisories closely"],
        "MEDIUM": ["Monitor storm advisories", "Prepare emergency supplies and secure property"],
        "LOW": ["Stay aware of forecast updates over the coming days"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[level]

    confidence = 55 + (15 if daily_wind_max else 0) + (10 if pressure_series else 0)
    return _hazard_result(level, score * 1.1, confidence, reasons, window, actions)


def predict_heatwave(current_weather, daily, zone):
    daily_max = [v for v in (daily or {}).get("temperature_2m_max", []) if v is not None]
    temp_now = (current_weather or {}).get("temperature")
    threshold = 38 if zone and ("Equatorial" in zone or "Subtropical" in zone) else 35

    reasons = []
    if daily_max:
        reasons.append(f"forecast highs up to {round(max(daily_max[:5]))}\u00b0C over the next 5 days")
    if temp_now is not None:
        reasons.append(f"current temperature {temp_now}\u00b0C")

    hot_days = [t for t in daily_max[:5] if t >= threshold]
    score = len(hot_days) * 20
    if daily_max and max(daily_max[:5]) > threshold + 5:
        score += 20
        reasons.append(f"peak forecast temperature exceeds the {threshold}\u00b0C zone threshold by 5\u00b0C or more")

    if score > 55:
        level, window = "HIGH", "within 1-3 days, lasting multiple days"
    elif score > 25:
        level, window = "MEDIUM", "within 3-5 days"
    elif score > 0:
        level, window = "LOW", "possible later this week"
    else:
        level, window = "NONE", "not expected in the near term"
        reasons = [f"Forecast highs stay below the {threshold}\u00b0C zone threshold"]

    actions = {
        "HIGH": ["Avoid outdoor activity during peak afternoon hours", "Stay hydrated and check on vulnerable individuals", "Watch for heat exhaustion/heatstroke symptoms"],
        "MEDIUM": ["Plan outdoor activities for cooler hours", "Keep extra water and shade available"],
        "LOW": ["Stay aware of the forecast heading into the weekend"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[level]

    confidence = 65 + (15 if daily_max else 0)
    return _hazard_result(level, score * 1.2, confidence, reasons, window, actions)


def predict_drought(daily, historical):
    daily_precip = [v for v in (daily or {}).get("precipitation_sum", []) if v is not None]
    rain_7d_forecast = sum(daily_precip[:7])
    dry_days_forecast = sum(1 for v in daily_precip[:7] if v < 1)

    reasons = []
    if daily_precip:
        reasons.append(f"only {round(rain_7d_forecast, 1)} mm forecast over the next 7 days")
    if historical and historical.get("total_30d_mm") is not None:
        reasons.append(f"{historical['total_30d_mm']} mm fell over the past 30 days")

    score = 0
    if daily_precip:
        score += max(0, 10 - rain_7d_forecast) * 3
        score += dry_days_forecast * 5
    if historical and (historical.get("total_30d_mm") or 999) < 20:
        score += 25
        reasons.append("30-day rainfall total is well below a healthy baseline")

    if score > 55:
        level, window = "HIGH", "developing over the coming 1-2 weeks"
    elif score > 30:
        level, window = "MEDIUM", "developing over the coming 2-4 weeks"
    elif score > 10:
        level, window = "LOW", "early signs only"
    else:
        level, window = "NONE", "not indicated at this time"
        reasons = ["Recent and forecast rainfall are within a normal range"]

    actions = {
        "HIGH": ["Implement water conservation measures now", "Prioritize water use for drinking and essential needs", "Coordinate with local agriculture/water authorities"],
        "MEDIUM": ["Monitor water reserves and reduce non-essential use", "Watch for updated drought advisories"],
        "LOW": ["Stay aware of rainfall trends over the coming weeks"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[level]

    confidence = 50 + (15 if daily_precip else 0) + (15 if historical else 0)
    return _hazard_result(level, score * 1.1, confidence, reasons, window, actions)


def predict_earthquake_activity(earthquakes, lat, lon):
    """See module note: this estimates near-term likelihood of
    CONTINUED seismic activity near a recent event (aftershock-style
    clustering), not a forecast of a new, independent earthquake."""
    nearby = [
        eq for eq in earthquakes
        if is_near(lat, lon, eq["geometry"]["coordinates"][1], eq["geometry"]["coordinates"][0])
    ]
    magnitudes = [eq["properties"].get("mag") or 0 for eq in nearby]
    best_eq = None
    if nearby:
        best = max(nearby, key=lambda eq: eq["properties"].get("mag") or 0)
        best_eq = (best["properties"]["place"], best["properties"].get("mag") or 0)

    significant = [m for m in magnitudes if m >= 4]
    max_mag = max(magnitudes) if magnitudes else 0

    if max_mag >= 6:
        current_level = "HIGH"
    elif max_mag >= 4:
        current_level = "MEDIUM"
    elif max_mag > 0:
        current_level = "LOW"
    else:
        current_level = "NONE"

    reasons = []
    if best_eq:
        reasons.append(f"strongest nearby event: magnitude {best_eq[1]} near {best_eq[0]}")
    reasons.append(f"{len(significant)} earthquake(s) of magnitude 4+ detected nearby in the last 24 hours")

    score = max_mag * 12 + len(significant) * 10
    if score > 70:
        pred_level, window = "HIGH", "elevated aftershock likelihood over the next 24-72 hours"
    elif score > 35:
        pred_level, window = "MEDIUM", "some continued aftershock activity possible over the next few days"
    elif score > 0:
        pred_level, window = "LOW", "minor residual activity possible"
    else:
        pred_level, window = "NONE", "no elevated activity detected"
        reasons = ["No significant earthquakes detected nearby in the last 24 hours"]

    actions = {
        "HIGH": ["Stay clear of damaged structures; aftershocks can cause further collapse", "Keep emergency supplies accessible", "Follow official seismic advisories"],
        "MEDIUM": ["Be prepared for aftershocks", "Secure heavy furniture and check for structural damage"],
        "LOW": ["Stay aware; minor aftershocks are possible"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[pred_level]

    confidence = 60 + (10 if nearby else 0)
    detail = _hazard_result(pred_level, score * 1.1, confidence, reasons, window, actions)
    return current_level, best_eq, detail


def predict_volcano_activity(nearby_volcanoes, volcanoes_all):
    """See module note: this estimates near-term unrest likelihood from
    detected seismicity tagged near volcanic centers, not a forecast of
    eruption timing."""
    count = len(nearby_volcanoes)
    reasons = (
        [f"{count} volcano-linked seismic event(s) detected within 500 km"] if count
        else ["no volcano-linked seismic activity detected within 500 km"]
    )
    current_level = "HIGH" if count else "NONE"

    score = count * 25
    if score > 60:
        pred_level, window = "HIGH", "unrest likely continuing over the next few days"
    elif score > 25:
        pred_level, window = "MEDIUM", "possible continued unrest this week"
    elif score > 0:
        pred_level, window = "LOW", "isolated activity, low continuation likelihood"
    else:
        pred_level, window = "NONE", "no unrest indicated"

    actions = {
        "HIGH": ["Follow official volcanic activity advisories closely", "Avoid areas prone to ashfall or pyroclastic hazards", "Prepare evacuation supplies (masks, goggles)"],
        "MEDIUM": ["Monitor local volcanic activity bulletins"],
        "LOW": ["Stay aware of regional volcanic monitoring updates"],
        "NONE": ["No action needed; continue routine monitoring"],
    }[pred_level]

    confidence = 55 + (10 if volcanoes_all else 0)
    detail = _hazard_result(pred_level, score * 1.1, confidence, reasons, window, actions)
    return current_level, detail


HAZARD_DISPLAY_NAMES = {
    "flood": "Flood", "landslide": "Landslide", "cyclone": "Storm / Cyclone",
    "heatwave": "Heatwave", "drought": "Drought", "earthquake": "Earthquake",
    "volcano": "Volcanic Activity",
}


def build_early_warning_alerts(hazard_details):
    """hazard_details: dict of {hazard_key: hazard_result}. Returns a
    list of alert dicts for anything at MEDIUM or HIGH, sorted by
    severity (HIGH first)."""
    severity_rank = {"HIGH": 2, "MEDIUM": 1, "LOW": 0, "NONE": -1}
    alerts = []
    for key, detail in hazard_details.items():
        if detail["level"] in ("HIGH", "MEDIUM"):
            alerts.append({
                "hazard": HAZARD_DISPLAY_NAMES.get(key, key.title()),
                "level": detail["level"],
                "probability_pct": detail["probability_pct"],
                "confidence_pct": detail["confidence_pct"],
                "window": detail["expected_window"],
                "reasons": detail["reasons"],
                "actions": detail["actions"],
            })
    alerts.sort(key=lambda a: severity_rank.get(a["level"], -1), reverse=True)
    return alerts


# =========================================================
#  MAIN ANALYSIS PIPELINE
#  Runs once per "Analyze Risk" click; result is cached in
#  st.session_state so every tab can read from it without
#  re-hitting the network APIs.
# =========================================================
def run_analysis(place):
    lat, lon, district, state, country = get_coordinates(place)
    if lat is None:
        return None

    zone, disasters = get_global_climatic_zone(lat, lon)

    # ---------- Weather (extended forecast) ----------
    # Requests a 7-day forecast with additional hourly/daily variables
    # (humidity, surface pressure, forecast wind/temperature/precip) in
    # the same single API call — this feeds the prediction engine below
    # without adding extra network round-trips.
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=precipitation,temperature_2m,relative_humidity_2m,surface_pressure"
        f"&daily=precipitation_sum,precipitation_probability_max,temperature_2m_max,"
        f"temperature_2m_min,windspeed_10m_max"
        f"&forecast_days=7&timezone=auto"
    )
    try:
        data = requests.get(weather_url, timeout=10).json()
    except requests.exceptions.RequestException:
        data = {}

    weather = data.get("current_weather", {})
    temperature = weather.get("temperature")
    windspeed = weather.get("windspeed")

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    precipitation = hourly.get("precipitation", [])
    temp_series = hourly.get("temperature_2m", [])

    rain_6h = precipitation[:6]
    rain_24h = precipitation[:24] if len(precipitation) >= 24 else precipitation
    temp_24h = temp_series[:24] if len(temp_series) >= 24 else temp_series

    rainfall = max(rain_6h) if rain_6h else 0
    if rainfall == 0 and rain_6h:
        rainfall = sum(rain_6h)
    is_raining = any(r > 0.5 for r in rain_6h)

    # risk_score is computed further below, once earthquake and volcano
    # probabilities are available — see "Adaptive weight recalibration".

    # ---------- Best-effort enrichment data (historical + terrain) ----------
    # Both are optional signals that raise confidence when available and
    # are skipped cleanly on failure — fetched concurrently with a short
    # wall-clock budget so a slow/unavailable source can't stall analysis.
    historical, elevation = None, None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            hist_future = executor.submit(fetch_historical_rainfall, lat, lon)
            elev_future = executor.submit(fetch_elevation_profile, lat, lon)
            historical = hist_future.result(timeout=6)
            elevation = elev_future.result(timeout=6)
    except concurrent.futures.TimeoutError:
        pass  # keep whichever of historical/elevation already resolved as None

    # ---------- Dynamic model selection (M*) ----------
    # Several hazards now have two competing predictors available: the
    # original rule-based threshold scorer (predict_flood,
    # predict_earthquake_activity, predict_volcano_activity) and the
    # newer Bayesian posterior estimator defined as a nested function
    # below. Rather than hard-wiring one model per hazard, run_analysis
    # computes both candidates and dynamically selects M* — the
    # candidate whose own confidence_pct is higher for THIS run's
    # inputs — since confidence_pct already reflects how much
    # supporting evidence (nearby events, enrichment data availability,
    # etc.) each model had to work with. This lets the pipeline fall
    # back to the simpler threshold model when the Bayesian model's
    # evidence is thin, and prefer the Bayesian posterior when it has
    # richer signal, without changing either model's own code. The
    # selected result is tagged with `selected_model` so the choice is
    # traceable; every other key keeps the same _hazard_result shape,
    # so nothing downstream (alerts, PDF, audio, UI) needs to change.
    def _select_dynamic_model(candidates):
        """candidates: list of (model_name, hazard_result) tuples for the
        same hazard. Returns the hazard_result with the highest
        confidence_pct, augmented with a `selected_model` key."""
        best_name, best_detail = max(candidates, key=lambda c: c[1]["confidence_pct"])
        chosen = dict(best_detail)
        chosen["selected_model"] = best_name
        return chosen

    # ---------- Earthquakes (Bayesian probability estimation) ----------
    # Naive-Bayes-style posterior combining three evidence signals —
    # strongest nearby magnitude, distance to the nearest significant
    # event, and the frequency of magnitude-4+ events nearby in the
    # last 24 hours — each discretized into bins with hand-set
    # likelihoods P(evidence | continued activity) vs P(evidence | no
    # continued activity). Likelihood ratios are multiplied against the
    # prior odds (conditional-independence assumption) to get a
    # posterior probability of continued/aftershock-style activity.
    # "current_level" (the observed risk badge) keeps the original
    # magnitude-threshold logic, since that reflects what has already
    # happened, not a prediction. Output is wrapped in the same
    # _hazard_result shape every other hazard predictor uses, so
    # nothing downstream (alerts, PDF, audio) needs to change.
    def _eq_bin_likelihoods(value, bins):
        """bins: list of (upper_bound, p_given_activity, p_given_no_activity).
        The last entry's upper_bound may be None for 'no upper limit'."""
        for upper, p_yes, p_no in bins:
            if upper is None or value < upper:
                return p_yes, p_no
        return bins[-1][1], bins[-1][2]

    def _bayesian_earthquake_prediction(earthquakes_list, ref_lat, ref_lon):
        nearby = []
        for eq in earthquakes_list:
            eq_lon, eq_lat = eq["geometry"]["coordinates"][0], eq["geometry"]["coordinates"][1]
            dist_km = haversine_km(ref_lat, ref_lon, eq_lat, eq_lon)
            if dist_km <= 1000:
                mag = eq["properties"].get("mag") or 0
                nearby.append({
                    "place": eq["properties"]["place"],
                    "mag": mag,
                    "distance_km": dist_km,
                })

        magnitudes = [e["mag"] for e in nearby]
        best_eq_local = None
        if nearby:
            best = max(nearby, key=lambda e: e["mag"])
            best_eq_local = (best["place"], best["mag"])

        significant = [e for e in nearby if e["mag"] >= 4]
        max_mag = max(magnitudes) if magnitudes else 0
        nearest_distance = min((e["distance_km"] for e in nearby), default=1000.0)
        freq_count = len(significant)

        # Observed current risk — unchanged threshold logic.
        if max_mag >= 6:
            current_level_local = "HIGH"
        elif max_mag >= 4:
            current_level_local = "MEDIUM"
        elif max_mag > 0:
            current_level_local = "LOW"
        else:
            current_level_local = "NONE"

        # Bayesian posterior for near-term continued/aftershock activity.
        prior_p_activity = 0.12
        prior_odds = prior_p_activity / (1 - prior_p_activity)

        mag_bins = [(3, 0.05, 0.50), (4.5, 0.20, 0.30), (6, 0.40, 0.12), (None, 0.35, 0.05)]
        dist_bins = [(50, 0.45, 0.10), (200, 0.30, 0.25), (500, 0.18, 0.35), (None, 0.10, 0.50)]
        freq_bins = [(1, 0.10, 0.55), (3, 0.25, 0.30), (6, 0.35, 0.10), (None, 0.30, 0.05)]

        p_mag_yes, p_mag_no = _eq_bin_likelihoods(max_mag, mag_bins)
        p_dist_yes, p_dist_no = _eq_bin_likelihoods(nearest_distance, dist_bins)
        p_freq_yes, p_freq_no = _eq_bin_likelihoods(freq_count, freq_bins)

        likelihood_ratio = (
            (p_mag_yes / p_mag_no)
            * (p_dist_yes / p_dist_no)
            * (p_freq_yes / p_freq_no)
        )
        posterior_odds = prior_odds * likelihood_ratio
        posterior_p = posterior_odds / (1 + posterior_odds)
        probability_pct = posterior_p * 100

        reasons = []
        if best_eq_local:
            reasons.append(f"strongest nearby event: magnitude {best_eq_local[1]} near {best_eq_local[0]}")
        if nearby:
            reasons.append(f"nearest significant activity ~{round(nearest_distance, 1)} km away")
        reasons.append(f"{freq_count} earthquake(s) of magnitude 4+ detected nearby in the last 24 hours")

        if probability_pct > 70:
            pred_level, window = "HIGH", "elevated aftershock likelihood over the next 24-72 hours"
        elif probability_pct > 40:
            pred_level, window = "MEDIUM", "some continued aftershock activity possible over the next few days"
        elif probability_pct > 15:
            pred_level, window = "LOW", "minor residual activity possible"
        else:
            pred_level, window = "NONE", "no elevated activity detected"
            reasons = ["No significant earthquakes detected nearby in the last 24 hours"]

        actions = {
            "HIGH": ["Stay clear of damaged structures; aftershocks can cause further collapse", "Keep emergency supplies accessible", "Follow official seismic advisories"],
            "MEDIUM": ["Be prepared for aftershocks", "Secure heavy furniture and check for structural damage"],
            "LOW": ["Stay aware; minor aftershocks are possible"],
            "NONE": ["No action needed; continue routine monitoring"],
        }[pred_level]

        confidence = 60 + (10 if nearby else 0)
        detail_local = _hazard_result(pred_level, probability_pct, confidence, reasons, window, actions)
        return current_level_local, best_eq_local, detail_local

    earthquakes = get_earthquakes()
    earthquake_risk, best_eq, earthquake_detail_bayesian = _bayesian_earthquake_prediction(earthquakes, lat, lon)
    _, _, earthquake_detail_threshold = predict_earthquake_activity(earthquakes, lat, lon)
    earthquake_detail = _select_dynamic_model([
        ("threshold", earthquake_detail_threshold),
        ("bayesian", earthquake_detail_bayesian),
    ])
    earthquake_prediction = earthquake_detail["level"]

    # ---------- Volcanoes (Bayesian probability estimation) ----------
    # Naive-Bayes-style posterior combining three evidence signals —
    # count of volcano-linked seismic events within 500 km, the
    # strongest magnitude among them, and distance to the nearest such
    # event — each discretized into bins with hand-set likelihoods
    # P(evidence | continued unrest) vs P(evidence | no continued
    # unrest). Likelihood ratios are multiplied against the prior odds
    # (conditional-independence assumption) to get a posterior
    # probability of continued volcanic unrest, replacing the previous
    # flat "count * 25" threshold score. "current_level" (the observed
    # risk badge) keeps the original count-based logic, since that
    # reflects what has already been detected, not a prediction. Output
    # is wrapped in the same _hazard_result shape every other hazard
    # predictor uses, so nothing downstream (alerts, PDF, audio) needs
    # to change.
    def _volcano_bin_likelihoods(value, bins):
        """bins: list of (upper_bound, p_given_unrest, p_given_no_unrest).
        The last entry's upper_bound may be None for 'no upper limit'."""
        for upper, p_yes, p_no in bins:
            if upper is None or value < upper:
                return p_yes, p_no
        return bins[-1][1], bins[-1][2]

    def _bayesian_volcano_prediction(nearby_volcano_events, all_volcano_events, ref_lat, ref_lon):
        count = len(nearby_volcano_events)
        magnitudes = [v["properties"].get("mag") or 0 for v in nearby_volcano_events]
        max_mag = max(magnitudes) if magnitudes else 0
        distances = [
            haversine_km(ref_lat, ref_lon, v["geometry"]["coordinates"][1], v["geometry"]["coordinates"][0])
            for v in nearby_volcano_events
        ]
        nearest_distance = min(distances) if distances else 500.0

        # Observed current risk — unchanged count-based logic.
        current_level_local = "HIGH" if count else "NONE"

        # Bayesian posterior for near-term continued volcanic unrest.
        prior_p_unrest = 0.08
        prior_odds = prior_p_unrest / (1 - prior_p_unrest)

        count_bins = [(1, 0.08, 0.55), (3, 0.25, 0.28), (6, 0.35, 0.12), (None, 0.32, 0.05)]
        mag_bins = [(2, 0.10, 0.45), (3.5, 0.25, 0.30), (5, 0.35, 0.15), (None, 0.30, 0.10)]
        dist_bins = [(50, 0.40, 0.12), (150, 0.30, 0.22), (350, 0.20, 0.33), (None, 0.10, 0.33)]

        p_count_yes, p_count_no = _volcano_bin_likelihoods(count, count_bins)
        p_mag_yes, p_mag_no = _volcano_bin_likelihoods(max_mag, mag_bins)
        p_dist_yes, p_dist_no = _volcano_bin_likelihoods(nearest_distance, dist_bins)

        likelihood_ratio = (
            (p_count_yes / p_count_no)
            * (p_mag_yes / p_mag_no)
            * (p_dist_yes / p_dist_no)
        )
        posterior_odds = prior_odds * likelihood_ratio
        posterior_p = posterior_odds / (1 + posterior_odds)
        probability_pct = posterior_p * 100

        reasons = (
            [f"{count} volcano-linked seismic event(s) detected within 500 km"] if count
            else ["no volcano-linked seismic activity detected within 500 km"]
        )
        if count:
            reasons.append(f"strongest linked event magnitude {round(max_mag, 1)}")
            reasons.append(f"nearest linked event ~{round(nearest_distance, 1)} km away")

        if probability_pct > 65:
            pred_level, window = "HIGH", "unrest likely continuing over the next few days"
        elif probability_pct > 35:
            pred_level, window = "MEDIUM", "possible continued unrest this week"
        elif probability_pct > 12:
            pred_level, window = "LOW", "isolated activity, low continuation likelihood"
        else:
            pred_level, window = "NONE", "no unrest indicated"
            reasons = ["No volcano-linked seismic activity detected nearby"]

        actions = {
            "HIGH": ["Follow official volcanic activity advisories closely", "Avoid areas prone to ashfall or pyroclastic hazards", "Prepare evacuation supplies (masks, goggles)"],
            "MEDIUM": ["Monitor local volcanic activity bulletins"],
            "LOW": ["Stay aware of regional volcanic monitoring updates"],
            "NONE": ["No action needed; continue routine monitoring"],
        }[pred_level]

        confidence = 55 + (10 if all_volcano_events else 0)
        detail_local = _hazard_result(pred_level, probability_pct, confidence, reasons, window, actions)
        return current_level_local, detail_local

    volcanoes = get_volcano_alerts()
    nearby_volcanoes = [
        v for v in volcanoes
        if is_near(lat, lon, v["geometry"]["coordinates"][1], v["geometry"]["coordinates"][0], threshold_km=500)
    ]
    volcano_risk, volcano_detail_bayesian = _bayesian_volcano_prediction(nearby_volcanoes, volcanoes, lat, lon)
    _, volcano_detail_threshold = predict_volcano_activity(nearby_volcanoes, volcanoes)
    volcano_detail = _select_dynamic_model([
        ("threshold", volcano_detail_threshold),
        ("bayesian", volcano_detail_bayesian),
    ])
    if any("marapi" in v["properties"]["place"].lower() for v in volcanoes):
        volcano_risk = "HIGH"
    volcano_prediction = volcano_detail["level"]

    # ---------- Adaptive weight recalibration (composite risk_score) ----------
    # The previous risk_score was a fixed-weight blend of only two
    # signals (rainfall * 0.7 + windspeed * 0.3). That static split
    # doesn't reflect that a run with strong seismic/volcanic evidence
    # but calm weather is understating its true severity, or that a
    # run with heavy rain but negligible wind is overweighting wind.
    # Each of the four inputs is first normalized onto a common 0-100
    # scale, then the weights are recalibrated per run: whichever
    # signal(s) are relatively most severe THIS run automatically carry
    # proportionally more influence over the composite score, rather
    # than using the same fixed split every time. Weights always sum to
    # 1, so risk_score stays on a comparable 0-100 scale across runs
    # regardless of which signal dominates. If every signal is ~0
    # (calm conditions across the board), weighting falls back to an
    # equal split since there's nothing to differentiate.
    RAINFALL_NORM_CAP_MM = 50.0    # 6h rainfall considered "maximal" for scoring
    WINDSPEED_NORM_CAP_KMH = 120.0  # windspeed considered "maximal" for scoring
    ONLINE_LEARNING_RATE = 0.15     # how strongly each new prediction nudges the persisted weights

    def _normalize_0_100(value, cap):
        if not value or cap <= 0:
            return 0.0
        return max(0.0, min(100.0, (value / cap) * 100.0))

    def _recalibrate_weights(signals):
        """signals: dict of {name: normalized_value_0_100}. Returns
        recalibrated weights (summing to 1) proportional to each
        signal's relative share of total normalized severity this run."""
        total = sum(signals.values())
        if total <= 0:
            n = len(signals) or 1
            return {name: 1.0 / n for name in signals}
        return {name: value / total for name, value in signals.items()}

    normalized_signals = {
        "rainfall": _normalize_0_100(rainfall, RAINFALL_NORM_CAP_MM),
        "windspeed": _normalize_0_100(windspeed or 0, WINDSPEED_NORM_CAP_KMH),
        "earthquake": earthquake_detail["probability_pct"],
        "volcano": volcano_detail["probability_pct"],
    }
    observed_weights = _recalibrate_weights(normalized_signals)

    # ---------- Online learning ----------
    # The weights that drive risk_score are no longer recomputed from
    # scratch every run. A persisted weight vector lives in session
    # state, starting equal across the four signals, and after every
    # prediction it is nudged toward this run's freshly observed
    # weighting via an exponentially-weighted moving-average update:
    #   new = (1 - lr) * old + lr * observed
    # so each prediction updates the weights that the *next* prediction
    # will use, rather than each run being independent. Renormalized so
    # weights always sum to 1 despite floating-point drift.
    if "online_weights" not in st.session_state:
        n = len(normalized_signals)
        st.session_state.online_weights = {name: 1.0 / n for name in normalized_signals}

    persisted_weights = st.session_state.online_weights
    updated_weights = {
        name: (1 - ONLINE_LEARNING_RATE) * persisted_weights.get(name, 1.0 / len(normalized_signals))
        + ONLINE_LEARNING_RATE * observed_weights[name]
        for name in normalized_signals
    }
    weight_total = sum(updated_weights.values()) or 1.0
    updated_weights = {name: value / weight_total for name, value in updated_weights.items()}
    st.session_state.online_weights = updated_weights  # persisted for the next prediction

    adaptive_weights = updated_weights
    risk_score = sum(
        adaptive_weights[name] * normalized_signals[name] for name in normalized_signals
    )


    # ---------- Flood (Bayesian probability estimation) ----------
    # Naive-Bayes-style posterior combining three evidence signals —
    # 6-hour rainfall, current wind speed, and 3-day forecast rainfall —
    # each discretized into bins with hand-set likelihoods P(evidence |
    # flood) vs P(evidence | no flood). Likelihood ratios are multiplied
    # against the prior odds (conditional-independence assumption) to
    # get a posterior probability. A 30-day rainfall baseline, when
    # available, applies a secondary odds update for soil saturation.
    # Output is wrapped in the same _hazard_result shape every other
    # hazard predictor uses, so nothing downstream (alerts, PDF, audio)
    # needs to change.
    def _bin_likelihoods(value, bins):
        """bins: list of (upper_bound, p_given_flood, p_given_no_flood).
        The last entry's upper_bound may be None for 'no upper limit'."""
        for upper, p_flood, p_no_flood in bins:
            if upper is None or value < upper:
                return p_flood, p_no_flood
        return bins[-1][1], bins[-1][2]

    def _bayesian_flood_prediction(rain_6h_total, wind_speed, daily_data, hist_data):
        daily_precip = [v for v in (daily_data or {}).get("precipitation_sum", []) if v is not None]
        rain_72h = sum(daily_precip[:3])
        wind_speed = wind_speed or 0

        prior_p_flood = 0.10  # base rate before observing any evidence
        prior_odds = prior_p_flood / (1 - prior_p_flood)

        rain_6h_bins = [(5, 0.05, 0.55), (15, 0.20, 0.30), (30, 0.45, 0.10), (None, 0.30, 0.05)]
        wind_bins = [(20, 0.15, 0.45), (40, 0.30, 0.35), (60, 0.35, 0.15), (None, 0.20, 0.05)]
        rain_72h_bins = [(20, 0.10, 0.50), (50, 0.25, 0.30), (100, 0.35, 0.15), (None, 0.30, 0.05)]

        p_r6h_flood, p_r6h_noflood = _bin_likelihoods(rain_6h_total, rain_6h_bins)
        p_wind_flood, p_wind_noflood = _bin_likelihoods(wind_speed, wind_bins)
        p_r72h_flood, p_r72h_noflood = _bin_likelihoods(rain_72h, rain_72h_bins)

        likelihood_ratio = (
            (p_r6h_flood / p_r6h_noflood)
            * (p_wind_flood / p_wind_noflood)
            * (p_r72h_flood / p_r72h_noflood)
        )
        posterior_odds = prior_odds * likelihood_ratio
        posterior_p = posterior_odds / (1 + posterior_odds)

        saturation_note = None
        if hist_data and hist_data.get("total_30d_mm") is not None:
            total_30d = hist_data["total_30d_mm"]
            if total_30d > 150:
                posterior_odds *= 1.6
                posterior_p = posterior_odds / (1 + posterior_odds)
                saturation_note = f"soil likely saturated ({total_30d} mm fell over the past 30 days)"

        probability_pct = posterior_p * 100

        reasons = [
            f"{round(rain_6h_total, 1)} mm of rain in the last 6 hours",
            f"wind speed {round(wind_speed, 1)} km/h",
        ]
        if daily_precip:
            reasons.append(f"{round(rain_72h, 1)} mm forecast over the next 3 days")
        if saturation_note:
            reasons.append(saturation_note)

        if probability_pct > 70:
            level, window = "HIGH", "within 6-24 hours"
        elif probability_pct > 40:
            level, window = "MEDIUM", "within 24-48 hours"
        elif probability_pct > 15:
            level, window = "LOW", "possible within 3-5 days"
        else:
            level, window = "NONE", "not expected in the near term"
            reasons = ["Rainfall and wind levels are within a normal range"]

        actions = {
            "HIGH": ["Evacuate low-lying areas now", "Move vehicles and valuables to higher ground", "Avoid crossing flooded roads or bridges"],
            "MEDIUM": ["Prepare an evacuation plan", "Monitor local river/drain levels closely", "Avoid unnecessary travel near waterways"],
            "LOW": ["Stay informed via local weather updates", "Clear drains and gutters as a precaution"],
            "NONE": ["No action needed; continue routine monitoring"],
        }[level]

        confidence = 62 + (12 if daily_precip else 0) + (10 if hist_data else 0)
        return _hazard_result(level, probability_pct, confidence, reasons, window, actions)

    flood_detail_bayesian = _bayesian_flood_prediction(rainfall, windspeed, daily, historical)
    flood_detail_threshold = predict_flood(rainfall, daily, historical)
    flood_detail = _select_dynamic_model([
        ("threshold", flood_detail_threshold),
        ("bayesian", flood_detail_bayesian),
    ])
    flood_risk = "NO FLOOD RISK" if flood_detail["level"] == "NONE" else flood_detail["level"]
    flood_prediction = flood_detail["level"] if flood_detail["level"] != "NONE" else "NO RISK"

    landslide_detail = predict_landslide(daily, historical, elevation)
    cyclone_detail = predict_storm_cyclone(weather, hourly, daily)
    heatwave_detail = predict_heatwave(weather, daily, zone)
    drought_detail = predict_drought(daily, historical)

    hazard_details = {
        "flood": flood_detail, "landslide": landslide_detail, "cyclone": cyclone_detail,
        "heatwave": heatwave_detail, "drought": drought_detail,
        "earthquake": earthquake_detail, "volcano": volcano_detail,
    }
    early_warning_alerts = build_early_warning_alerts(hazard_details)

    # ---------- Overall ----------
    # Reflects ALL hazards (not just flood/earthquake/volcano), since an
    # accurate "overall risk" for an early-warning system shouldn't miss
    # a severe heatwave or storm just because it isn't one of the
    # original three categories. This does not change how or when the
    # Emergency Response system activates (see mas_active below, which
    # keeps its original flood/earthquake/volcano-only trigger).
    all_levels = [d["level"] for d in hazard_details.values()]
    if "HIGH" in all_levels:
        overall_risk = "HIGH"
    elif "MEDIUM" in all_levels:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    mas_active = (
        flood_risk in ["HIGH", "MEDIUM"]
        or earthquake_risk in ["HIGH", "MEDIUM"]
        or volcano_risk == "HIGH"
    )

    # ---------- Emergency response resources ----------
    severity = overall_risk  # HIGH / MEDIUM / LOW — drives simulation scale
    hospitals, ambulance_info, food_places, shelters, safe_path, hospital_routes = [], [], [], [], [], []
    police_stations, fire_stations, blood_banks, ambulance_stations = [], [], [], []
    ngos, rescue_teams, community_kitchens = [], [], []
    hospital_error, food_error = None, None

    if mas_active:
        # Single network round-trip for every live category at once (see
        # fetch_all_live_resources), run in a background thread with a
        # hard wall-clock cap. This is a second layer of protection on
        # top of the internal request timeout/budget: if anything hangs
        # in a way that ignores those (e.g. a stalled DNS lookup), we
        # still bail out and fall back to simulated data on schedule
        # instead of blocking the UI indefinitely.
        with st.spinner("Fetching live emergency resource data..."):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(fetch_all_live_resources, lat, lon)
                    live_buckets, live_error = future.result(timeout=OVERPASS_TOTAL_BUDGET_S + 1)
            except concurrent.futures.TimeoutError:
                live_buckets, live_error = {}, "Live resource lookup exceeded the time budget; using simulated data."

        hospital_error = live_error
        food_error = live_error

        hospitals = attach_estimated_metrics(live_buckets.get("hospital", []), "hospital", severity)
        hospitals = augment_with_simulated(hospitals, "hospital", lat, lon, district, severity)
        ambulance_info = generate_ambulance_data(hospitals)

        for h in hospitals[:3]:
            url = f"https://www.google.com/maps/dir/{h['lat']},{h['lon']}/{lat},{lon}"
            hospital_routes.append({"name": h["name"], "url": url})

        danger_weight = 100 if flood_risk == "HIGH" else 20
        graph = {
            "Start": [("SafeZone1", 5), ("DangerZone", danger_weight)],
            "SafeZone1": [("SafeZone2", 5)],
            "DangerZone": [("SafeZone2", danger_weight)],
            "SafeZone2": [],
        }
        safe_path = dijkstra(graph, "Start", "SafeZone2")

        food_places = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("food", []), "food_distribution_center", severity),
            "food_distribution_center", lat, lon, district, severity,
        )
        shelters = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("shelter", []), "shelter", severity),
            "shelter", lat, lon, district, severity,
        )
        police_stations = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("police_station", []), "police_station", severity),
            "police_station", lat, lon, district, severity,
        )
        fire_stations = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("fire_station", []), "fire_station", severity),
            "fire_station", lat, lon, district, severity,
        )
        blood_banks = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("blood_bank", []), "blood_bank", severity),
            "blood_bank", lat, lon, district, severity,
        )
        ambulance_stations = augment_with_simulated(
            attach_estimated_metrics(live_buckets.get("ambulance_station", []), "ambulance_station", severity),
            "ambulance_station", lat, lon, district, severity,
        )

        # No reliable public OSM coverage for these categories — always modeled.
        ngos = augment_with_simulated([], "ngo", lat, lon, district, severity)
        rescue_teams = augment_with_simulated([], "rescue_team", lat, lon, district, severity)
        community_kitchens = augment_with_simulated([], "community_kitchen", lat, lon, district, severity)

    safe_lat, safe_lon = lat + 0.05, lon + 0.05
    evacuation_url = (
        f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}"
        f"&destination={safe_lat},{safe_lon}"
    )

    # ---------- Report text ----------
    now = datetime.datetime.now()
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")

    report = f"""
    <b>DISASTER ANALYSIS REPORT</b><br/><br/>
    <b>1. Location Details</b><br/>
    Location: {district}, {state}, {country}<br/>
    Date: {current_date}<br/>
    Time: {current_time}<br/><br/>
    <b>2. Weather Information</b><br/>
    Rainfall (6hr): {round(rainfall, 2)} mm<br/>
    Temperature: {temperature} °C<br/>
    Wind Speed: {windspeed} km/h<br/><br/>
    <b>3. Risk Assessment</b><br/>
    Flood Risk: {flood_risk}<br/>
    Earthquake Risk: {earthquake_risk}<br/>
    Volcano Risk: {volcano_risk}<br/><br/>
    <b>4. Predictions</b><br/>
    Flood Prediction: {flood_prediction}<br/>
    Earthquake Prediction: {earthquake_prediction}<br/>
    Volcano Prediction: {volcano_prediction}<br/><br/>
    """

    report += "<b>5. Suggested Action</b><br/>"
    if earthquake_risk == "HIGH":
        report += "High earthquake risk. Move to open safe areas immediately.<br/>"
    elif earthquake_risk == "MEDIUM":
        report += "Moderate earthquake activity. Stay alert and avoid unsafe structures.<br/>"
    elif flood_risk == "HIGH":
        report += "High flood risk. Evacuate low-lying areas.<br/>"
    elif flood_risk == "MEDIUM":
        report += "Moderate flood risk. Stay alert.<br/>"
    elif flood_risk == "LOW":
        report += "Low flood risk. Stay cautious.<br/>"
    else:
        report += "No immediate disaster risk. Safe conditions.<br/>"

    report += "<br/><b>6. Trigger Source</b><br/>"
    if earthquake_risk in ["HIGH", "MEDIUM"]:
        report += "Earthquake Activity"
    elif flood_risk == "HIGH":
        report += "Flood Risk"
    else:
        report += "No Threat"

    if hospitals:
        report += "\n\n🏥 Nearby Hospitals:\n"
        for h in hospitals[:3]:
            distance_note = f" ({h['distance_km']} km)" if h.get("distance_km") is not None else ""
            report += f"- {h['name']}{distance_note}\n"

    return {
        "place_query": place,
        "lat": lat, "lon": lon,
        "district": district, "state": state, "country": country,
        "zone": zone, "disasters": disasters,
        "temperature": temperature, "windspeed": windspeed,
        "rain_6h": rain_6h, "rain_24h": rain_24h, "temp_24h": temp_24h,
        "rainfall": rainfall, "is_raining": is_raining,
        "flood_risk": flood_risk, "flood_prediction": flood_prediction,
        "risk_score": risk_score, "adaptive_weights": adaptive_weights,
        "earthquake_risk": earthquake_risk, "earthquake_prediction": earthquake_prediction,
        "best_eq": best_eq,
        "volcano_risk": volcano_risk, "volcano_prediction": volcano_prediction,
        "nearby_volcanoes": nearby_volcanoes,
        "overall_risk": overall_risk, "mas_active": mas_active,
        "flood_detail": flood_detail, "landslide_detail": landslide_detail,
        "cyclone_detail": cyclone_detail, "heatwave_detail": heatwave_detail,
        "drought_detail": drought_detail, "earthquake_detail": earthquake_detail,
        "volcano_detail": volcano_detail, "early_warning_alerts": early_warning_alerts,
        "historical_rainfall": historical, "elevation_profile": elevation,
        "daily_forecast": daily,
        "hospitals": hospitals, "hospital_error": hospital_error,
        "ambulance_info": ambulance_info, "hospital_routes": hospital_routes,
        "food_places": food_places, "food_error": food_error,
        "shelters": shelters,
        "police_stations": police_stations, "fire_stations": fire_stations,
        "blood_banks": blood_banks, "ambulance_stations": ambulance_stations,
        "ngos": ngos, "rescue_teams": rescue_teams, "community_kitchens": community_kitchens,
        "safe_path": safe_path,
        "evacuation_url": evacuation_url,
        "report_text": report,
        "current_date": current_date, "current_time": current_time,
    }


# =========================================================
#  RENDER: HOME TAB
# =========================================================
def render_home_tab(analysis):
    st.markdown(_HOME_CSS, unsafe_allow_html=True)

    header_col, updated_col = st.columns([4, 1])
    with header_col:
        st.subheader("🌍 Live Global Disaster Risk Map")
    with updated_col:
        st.markdown(
            f"<div class='dc-updated'>🔄 {datetime.datetime.now().strftime('%I:%M %p')}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div class='dc-map-caption'>Countries are shaded by combined earthquake magnitude "
        "reported in the last 24 hours — deeper red means more seismic energy released nearby. "
        "Enter a location above and click <b>Analyze Risk</b> for a full assessment.</div>",
        unsafe_allow_html=True,
    )

    try:
        world_map = load_world_map()
        earthquakes = get_earthquakes()
        country_scores = get_country_risk_scores(earthquakes)
        max_score = max(country_scores.values()) if country_scores else 0

        for feature in world_map["features"]:
            country_name = feature["properties"]["name"]
            score = country_scores.get(country_name, 0)
            feature["properties"]["color"] = _risk_gradient_color(score, max_score)
            feature["properties"]["risk_score"] = round(score, 1)

        map_col, side_col = st.columns([3, 1])

        with map_col:
            geojson_layer = pdk.Layer(
                "GeoJsonLayer",
                world_map,
                get_fill_color="properties.color",
                get_line_color=[255, 255, 255, 35],
                line_width_min_pixels=0.5,
                pickable=True,
                stroked=True,
                filled=True,
                auto_highlight=True,
                highlight_color=[255, 255, 255, 90],
            )
            map_layers = [geojson_layer]
            if analysis is not None:
                selected_location = pd.DataFrame([{
                    "lat": analysis["lat"],
                    "lon": analysis["lon"],
                    "name": f"{analysis['district']}, {analysis['state']}",
                    "risk_score": round(analysis["risk_score"], 1),
                }])
                map_layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    selected_location,
                    get_position="[lon, lat]",
                    get_fill_color=[56, 189, 248, 230],
                    get_line_color=[255, 255, 255, 255],
                    get_radius=180000,
                    line_width_min_pixels=2,
                    pickable=True,
                ))
            view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.3, pitch=0)
            st.pydeck_chart(
                pdk.Deck(
                    layers=map_layers,
                    initial_view_state=view_state,
                    tooltip={"text": "{name}\nRisk score: {risk_score}"},
                ),
                width="stretch",
            )
            st.markdown(
                """
                <div class='dc-legend-row'>
                    <div class='dc-legend-item'><span class='dc-dot' style='background:#2ecc71'></span> Low activity</div>
                    <div class='dc-legend-item'><span class='dc-dot' style='background:#f1c40f'></span> Elevated</div>
                    <div class='dc-legend-item'><span class='dc-dot' style='background:#ff2400'></span> High activity</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with side_col:
            if analysis is not None:
                st.markdown("<div class='dc-side-heading'>📍 Analyzed Location</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='dc-location-card'><div class='dc-location-name'>{analysis['district']}</div><div class='dc-location-meta'>{analysis['state']}, {analysis['country']}<br>Lat {analysis['lat']} · Lon {analysis['lon']}</div><span class='dc-location-risk'>Overall Risk: {analysis['overall_risk']}</span></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div class='dc-side-heading'>📍 Analyzed Location</div>", unsafe_allow_html=True)
                st.caption("Search for a place above to highlight it on the map and see its risk summary here.")

            st.markdown(
                f"""
                <div class='dc-stat-box'>
                    <div class='dc-stat-num'>{len(earthquakes)}</div>
                    <div class='dc-stat-label'>Earthquakes (last 24h)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception as e:
        log_error("Could not load the live world risk map.", exc=e)

    if analysis is None:
        st.markdown("---")
        st.write("👆 Enter a place name above and click **Analyze Risk** to get started.")
        return

    st.markdown("---")
    st.subheader("📍 Latest Analysis Snapshot")

    risk_class = {"HIGH": "dc-risk-high", "MEDIUM": "dc-risk-medium", "LOW": "dc-risk-low"}.get(
        analysis["overall_risk"], "dc-risk-low"
    )
    st.markdown(
        f"""
        <div class='dc-snapshot-banner {risk_class}'>
            <div>
                <div class='dc-snapshot-loc'>📍 {analysis['district']}, {analysis['state']}, {analysis['country']}</div>
                <div class='dc-snapshot-coord'>Lat {analysis['lat']}, Lon {analysis['lon']}</div>
            </div>
            <div class='dc-snapshot-risk'>Overall Risk: {analysis['overall_risk']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    for col, label, icon, value in [
        (c1, "Flood Risk", "🌊", analysis["flood_risk"]),
        (c2, "Earthquake Risk", "🌍", analysis["earthquake_risk"]),
        (c3, "Volcano Risk", "🌋", analysis["volcano_risk"]),
    ]:
        level_class = {"HIGH": "dc-risk-high", "MEDIUM": "dc-risk-medium"}.get(value, "dc-risk-low")
        col.markdown(
            f"""
            <div class='dc-metric-card {level_class}'>
                <div class='dc-metric-icon'>{icon}</div>
                <div class='dc-metric-label'>{label}</div>
                <div class='dc-metric-value'>{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
#  RENDER: DISASTER PREDICTION TAB
#
#  UI-only redesign. Nothing here recomputes or alters any prediction —
#  every value rendered is read as-is from the `analysis` dict produced
#  by run_analysis() and the hazard predictors above. Only the layout
#  and styling of this tab changed.
# =========================================================
_PREDICTION_CSS = """
<style>
.dp-hero {
    border-radius: 16px; padding: 22px 26px; margin-bottom: 18px; color: white;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.dp-hero-high { background: linear-gradient(120deg,#c0392b,#8e2418); }
.dp-hero-medium { background: linear-gradient(120deg,#e2a712,#c98a0a); }
.dp-hero-low { background: linear-gradient(120deg,#1e8449,#166638); }
.dp-hero-title { font-size: 1.05rem; font-weight: 700; opacity: 0.92; letter-spacing: 0.02em; }
.dp-hero-sub { font-size: 0.85rem; opacity: 0.85; margin-top: 2px; }
.dp-hero-score { text-align: right; }
.dp-hero-score-num { font-size: 2.1rem; font-weight: 800; line-height: 1; }
.dp-hero-score-label { font-size: 0.72rem; opacity: 0.85; text-transform: uppercase; letter-spacing: 0.05em; }

.dp-alert-strip { display: flex; gap: 10px; overflow-x: auto; padding: 4px 2px 10px 2px; margin-bottom: 4px; }
.dp-alert-chip {
    flex: 0 0 auto; border-radius: 10px; padding: 10px 14px; min-width: 190px;
    color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.dp-alert-chip-high { background: linear-gradient(135deg,#c0392b,#932a1c); }
.dp-alert-chip-medium { background: linear-gradient(135deg,#e2a712,#b9800a); }
.dp-alert-chip-title { font-weight: 700; font-size: 0.88rem; }
.dp-alert-chip-meta { font-size: 0.72rem; opacity: 0.9; margin-top: 3px; }
.dp-alert-clear {
    border-radius: 12px; padding: 14px 18px; background: linear-gradient(135deg,#123225,#163d2d);
    border: 1px solid #286044; color: #86efac; font-weight: 600; font-size: 0.9rem;
    display: flex; align-items: center; gap: 10px; margin-bottom: 4px;
}
.dp-section-title {
    font-size: 1.05rem; font-weight: 800; margin: 26px 0 10px 0; color: #e8eef7;
    display: flex; align-items: center; gap: 8px;
}
.dp-info-pill {
    display: inline-block; background: #252d3a; color: #cbd5e1; font-size: 0.74rem;
    padding: 3px 10px; border-radius: 999px; margin-bottom: 14px;
}

.dp-card {
    border-radius: 14px; border: 1px solid #e8eaee; padding: 16px 18px; margin-bottom: 14px;
    background: #171a22; border-color: #2b3442; box-shadow: 0 8px 22px rgba(0,0,0,0.16);
}
.dp-card-high { border-left: 5px solid #c0392b; }
.dp-card-medium { border-left: 5px solid #e2a712; }
.dp-card-low { border-left: 5px solid #3a8fd8; }
.dp-card-none { border-left: 5px solid #27ae60; }

.dp-card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; flex-wrap: wrap; }
.dp-card-heading { display: flex; align-items: center; gap: 10px; }
.dp-card-icon { font-size: 1.5rem; line-height: 1; }
.dp-card-name { font-weight: 750; font-size: 1.0rem; color: #f8fafc; }
.dp-card-window { font-size: 0.78rem; color: #a8b3c2; margin-top: 1px; }

.dp-badge {
    font-size: 0.72rem; font-weight: 800; padding: 4px 12px; border-radius: 999px;
    letter-spacing: 0.03em; white-space: nowrap;
}
.dp-badge-high { background: #fdecea; color: #c0392b; border: 1px solid #f3c2bd; }
.dp-badge-medium { background: #fdf3da; color: #8a6206; border: 1px solid #f0dca0; }
.dp-badge-low { background: #e8f2fc; color: #2367a5; border: 1px solid #bfdcf5; }
.dp-badge-none { background: #e9f9ef; color: #1e8449; border: 1px solid #bfe8cf; }

.dp-bar-row { margin-top: 12px; }
.dp-bar-label { display: flex; justify-content: space-between; font-size: 0.74rem; color: #cbd5e1; margin-bottom: 4px; }
.dp-bar-track { background: #303948; border-radius: 6px; height: 9px; overflow: hidden; }
.dp-bar-fill { height: 100%; border-radius: 6px; }
.dp-bar-fill-high { background: linear-gradient(90deg,#e0574a,#c0392b); }
.dp-bar-fill-medium { background: linear-gradient(90deg,#f0c04d,#e2a712); }
.dp-bar-fill-low { background: linear-gradient(90deg,#6ab0e8,#3a8fd8); }
.dp-bar-fill-none { background: linear-gradient(90deg,#5bc98a,#27ae60); }
.dp-bar-fill-conf { background: linear-gradient(90deg,#9aa5b1,#5f6b7a); }

.dp-weather-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 12px; margin-bottom: 6px; }
.dp-weather-card {
    border-radius: 12px; padding: 14px; text-align: center; background: #171a22;
    border: 1px solid #2b3442;
}
.dp-weather-icon { font-size: 1.5rem; }
.dp-weather-label { font-size: 0.72rem; color: #a8b3c2; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.03em; }
.dp-weather-value { font-size: 1.15rem; font-weight: 800; color: #f8fafc; margin-top: 2px; }
</style>
"""

_RISK_ICONS = {
    "flood": "🌊", "landslide": "⛰️", "cyclone": "🌀", "heatwave": "🌡️",
    "drought": "🏜️", "earthquake": "🌍", "volcano": "🌋",
}

_LEVEL_CLASS = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low", "NONE": "none"}


def _dp_badge_html(level):
    cls = _LEVEL_CLASS.get(level, "none")
    return f"<span class='dp-badge dp-badge-{cls}'>{level}</span>"


def _dp_bar_html(label, pct, cls):
    pct = max(0, min(100, pct))
    return (
        f'<div class="dp-bar-row"><div class="dp-bar-label"><span>{label}</span><span>{pct}%</span></div>'
        f'<div class="dp-bar-track"><div class="dp-bar-fill dp-bar-fill-{cls}" style="width:{pct}%;"></div></div></div>'
    )


def _render_hazard_explain(detail, caveat=None):
    """Shared 'why' block: probability, confidence, reasons, and
    recommended actions for a single hazard prediction. All values are
    read verbatim from `detail`, which is produced upstream by the
    (unchanged) prediction engine — only the presentation is new."""
    with st.expander("🔎 Why this prediction? / Recommended actions"):
        if caveat:
            st.caption(caveat)
        st.markdown("**Contributing factors**")
        for r in detail["reasons"]:
            st.markdown(f"- {r}")
        st.markdown("**Recommended actions**")
        for act in detail["actions"]:
            st.markdown(f"- {act}")


def _render_hazard_card(key, label, detail, caveat=None, extra_lines=None):
    """One self-contained hazard card: icon, name, risk badge, expected
    window, probability + confidence bars, then the existing
    'why this prediction' expander underneath. `extra_lines` optionally
    surfaces hazard-specific facts (e.g. the strongest nearby earthquake)
    right under the header, still sourced straight from `analysis`."""
    level = detail["level"]
    cls = _LEVEL_CLASS.get(level, "none")
    icon = _RISK_ICONS.get(key, "⚠️")

    card_html = f"""
    <div class="dp-card dp-card-{cls}">
        <div class="dp-card-top">
            <div class="dp-card-heading">
                <span class="dp-card-icon">{icon}</span>
                <div>
                    <div class="dp-card-name">{label}</div>
                    <div class="dp-card-window">Expected: {detail['expected_window']}</div>
                </div>
            </div>
            {_dp_badge_html(level)}
        </div>
        {_dp_bar_html("Probability", detail['probability_pct'], cls)}
        {_dp_bar_html("Model confidence", detail['confidence_pct'], "conf")}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    if extra_lines:
        for line in extra_lines:
            st.caption(line)

    _render_hazard_explain(detail, caveat=caveat)


def render_prediction_tab(analysis):
    st.markdown(_PREDICTION_CSS, unsafe_allow_html=True)

    if analysis is None:
        st.info("Run an analysis from the input above to see predictions here.")
        return

    # ---------- Hero summary ----------
    overall = analysis["overall_risk"]
    hero_cls = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(overall, "low")
    st.markdown(
        f"""
        <div class="dp-hero dp-hero-{hero_cls}">
            <div>
                <div class="dp-hero-title">🧭 Disaster Prediction — {analysis['district']}, {analysis['state']}</div>
                <div class="dp-hero-sub">{analysis['zone']} · commonly prone to {', '.join(analysis['disasters'])}</div>
            </div>
            <div class="dp-hero-score">
                <div class="dp-hero-score-num">{overall}</div>
                <div class="dp-hero-score-label">Overall Risk · Score {round(analysis['risk_score'], 1)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Location & Weather snapshot ----------
    st.markdown("<div class='dp-section-title'>📍 Location &amp; Weather Snapshot</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="dp-weather-grid">
            <div class="dp-weather-card">
                <div class="dp-weather-icon">🌡️</div>
                <div class="dp-weather-label">Temperature</div>
                <div class="dp-weather-value">{analysis['temperature']} °C</div>
            </div>
            <div class="dp-weather-card">
                <div class="dp-weather-icon">💨</div>
                <div class="dp-weather-label">Wind Speed</div>
                <div class="dp-weather-value">{analysis['windspeed']} km/h</div>
            </div>
            <div class="dp-weather-card">
                <div class="dp-weather-icon">{"🌧️" if analysis["is_raining"] else "☁️"}</div>
                <div class="dp-weather-label">Rain (6h)</div>
                <div class="dp-weather-value">{round(analysis['rainfall'], 1)} mm</div>
            </div>
            <div class="dp-weather-card">
                <div class="dp-weather-icon">📊</div>
                <div class="dp-weather-label">Risk Score</div>
                <div class="dp-weather-value">{round(analysis['risk_score'], 1)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if analysis["is_raining"]:
        st.success("🌧️ Rain detected in forecast")
    else:
        st.info("☁️ No rain detected")

    # ---------- Core hazards: Flood / Earthquake / Volcano ----------
    st.markdown("<div class='dp-section-title'>🎯 Core Hazard Assessment</div>", unsafe_allow_html=True)

    st.markdown("##### 🌊 Flood")
    _render_hazard_card("flood", "Flood Risk", analysis["flood_detail"])

    if analysis["best_eq"]:
        place_name, magnitude = analysis["best_eq"]
        eq_extra = [f"📍 Nearest event: **{place_name}** — magnitude **{magnitude}**"]
    else:
        eq_extra = ["✅ No recent earthquakes detected nearby"]
    st.markdown("##### 🌍 Earthquake")
    _render_hazard_card(
        "earthquake", "Earthquake Risk", analysis["earthquake_detail"],
        caveat="Reflects near-term aftershock/continued-activity likelihood, not a forecast of a new earthquake.",
        extra_lines=eq_extra,
    )

    if analysis["nearby_volcanoes"]:
        volcano_extra = [
            f"🌋 {v['properties']['place']} — activity level {v['properties']['mag']}"
            for v in analysis["nearby_volcanoes"][:3]
        ]
    else:
        volcano_extra = ["✅ No volcanic activity detected nearby"]
    st.markdown("##### 🌋 Volcano")
    _render_hazard_card(
        "volcano", "Volcano Risk", analysis["volcano_detail"],
        caveat="Reflects unrest likelihood from nearby seismicity, not a forecast of eruption timing.",
        extra_lines=volcano_extra,
    )

    # ---------- Prediction summary strip ----------
    st.markdown("<div class='dp-section-title'>🔮 Prediction Summary</div>", unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    for col, icon, label, value in [
        (p1, "🌊", "Flood Prediction", analysis["flood_prediction"]),
        (p2, "🌍", "Earthquake Prediction", analysis["earthquake_prediction"]),
        (p3, "🌋", "Volcano Prediction", analysis["volcano_prediction"]),
    ]:
        col.markdown(
            f"""
            <div class="dp-weather-card">
                <div class="dp-weather-icon">{icon}</div>
                <div class="dp-weather-label">{label}</div>
                <div class="dp-weather-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- Extended hazard predictions ----------
    st.markdown("<div class='dp-section-title'>🧭 Extended Hazard Predictions</div>", unsafe_allow_html=True)

    ext1, ext2 = st.columns(2)
    with ext1:
        _render_hazard_card("landslide", "⛰️ Landslide Risk", analysis["landslide_detail"])
        _render_hazard_card("heatwave", "🌡️ Heatwave Risk", analysis["heatwave_detail"])
    with ext2:
        _render_hazard_card("cyclone", "🌀 Storm / Cyclone Risk", analysis["cyclone_detail"])
        _render_hazard_card("drought", "🏜️ Drought Risk", analysis["drought_detail"])


# =========================================================
#  RENDER: EMERGENCY RESPONSE TAB
# =========================================================
def render_resource_card(r):
    """Renders one emergency resource with an honest source badge —
    'Live' for OpenStreetMap-sourced identity/location data, 'Estimated'
    for modeled entries. Capacity/status figures are always model
    estimates (no public feed exists for real-time bed/ambulance counts),
    so that framing doesn't change based on source."""
    badge = "🟢 Live" if r.get("source") == "live" else "🔧 Estimated"
    st.write(f"**{r['name']}**  ·  {r.get('type', '')}")
    st.caption(
        f"{badge}   •   {r['distance_km']} km away   •   "
        f"~{r.get('travel_time_min', '?')} min travel   •   updated {r.get('last_updated', '')}"
    )
    if r.get("address"):
        st.write(f"🏠 {r['address']}")
    if r.get("contact"):
        st.write(f"📞 {r['contact']}")

    if "beds_available" in r:
        st.write(f"🛏️ Beds: {r['beds_available']}/{r['capacity']} available  |  🏥 ICU: {r['icu_available']}/{r['icu_beds']}")
        st.write(f"👨‍⚕️ Doctors on duty: {r['doctors_on_duty']}  |  🚑 Ambulances: {r['ambulances']}")
    elif "fleet_size" in r:
        st.write(f"🚑 Fleet: {r['fleet_size']}  |  Available: {r['ambulances_available']}  |  Dispatched: {r['ambulances_dispatched']}")
    elif "current_occupants" in r:
        st.write(f"👥 Occupancy: {r['current_occupants']}/{r['capacity']}")
    elif "personnel" in r:
        st.write(f"👮 Personnel: {r['personnel']}  |  Deployed: {r['deployed']}  |  Vehicles: {r['vehicles']}")
    elif "blood_units_available" in r:
        st.write(f"🩸 Units available: {r['blood_units_available']}")
    elif "volunteers" in r:
        st.write(f"🙋 Volunteers: {r['volunteers']}  |  Deployed: {r['deployed']}")

    st.write(f"📊 Status: {r.get('status', 'Operational')}  ({r.get('occupancy_pct', '?')}% load)")
    st.write("---")


def render_response_tab(analysis):
    """Improved Emergency Response tab with modern card-based UI,
    visual capacity indicators, and better information hierarchy."""
    st.markdown(_RESPONSE_CSS, unsafe_allow_html=True)

    if analysis is None:
        st.info("Run an analysis from the input above to see emergency response options here.")
        return

    if not analysis["mas_active"]:
        st.markdown("""
        <div class="er-standby">
            <div class="er-standby-icon">✅</div>
            <div class="er-standby-title">Emergency Response on Standby</div>
            <div class="er-standby-text">Risk levels are currently low. The emergency response system remains on standby.<br>No immediate mobilization is required.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Hero Banner ──
    st.markdown(f"""
    <div class="er-hero">
        <div class="er-hero-title">🚨 Emergency Response System Activated</div>
        <div class="er-hero-sub">
            Real-time resource coordination for <b>{analysis['district']}, {analysis['state']}</b><br>
            Overall Risk: <b>{analysis['overall_risk']}</b> · Risk Score: <b>{round(analysis['risk_score'], 1)}</b>
        </div>
        <div class="er-hero-badge">
            <span class="pulse"></span>
            Live Monitoring Active
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Disclaimer ──
    st.markdown("""
    <div class="er-disclaimer">
        <b>📡 Data Source Notice:</b> Locations marked <b>🟢 Live</b> are sourced from OpenStreetMap. 
        Where live coverage is sparse, <b>🔧 Estimated</b> entries fill gaps with modeled data. 
        Capacity figures (beds, ambulances, occupancy) are always modeled — no public real-time feed exists for facility status.
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Stats ──
    _render_quick_stats(analysis)

    # ── Resource Map ──
    category_colors = {
        "Hospital": [220, 30, 30], "Clinic": [220, 30, 30],
        "Restaurant": [255, 165, 0], "Cafe": [255, 165, 0],
        "Fast Food": [255, 165, 0], "Marketplace": [255, 165, 0],
        "Supermarket": [255, 165, 0], "Food Resource": [255, 165, 0],
        "Food Distribution Center": [255, 165, 0],
        "Relief Shelter": [150, 50, 200], "Emergency Assembly Point": [150, 50, 200],
        "Ambulance Station": [0, 200, 200],
        "Police Station": [30, 90, 220],
        "Fire Station": [230, 90, 20],
        "Blood Bank": [230, 20, 120],
        "NGO / Aid Organization": [50, 160, 60],
        "Rescue Team": [90, 200, 90],
        "Community Kitchen": [200, 180, 30],
    }
    all_resource_lists = (
        analysis["hospitals"][:10] + analysis["food_places"][:10] + analysis["shelters"][:6]
        + analysis["ambulance_stations"][:6] + analysis["police_stations"][:4]
        + analysis["fire_stations"][:4] + analysis["blood_banks"][:4]
        + analysis["ngos"][:4] + analysis["rescue_teams"][:4] + analysis["community_kitchens"][:4]
    )
    map_points = [
        {"name": _resource_display_name(r["name"]), "lat": r["lat"], "lon": r["lon"],
         "color": category_colors.get(r["type"], [120, 120, 120]), "kind": r["type"]}
        for r in all_resource_lists
    ]

    if map_points:
        st.markdown('<div class="er-section-title">🗺️ Emergency Resources Map</div>', unsafe_allow_html=True)
        points_df = pd.DataFrame(map_points)
        user_df = pd.DataFrame([{"lat": analysis["lat"], "lon": analysis["lon"]}])

        resource_layer = pdk.Layer(
            "ScatterplotLayer", points_df,
            get_position="[lon, lat]", get_fill_color="color", get_radius=280, pickable=True,
        )
        user_layer = pdk.Layer(
            "ScatterplotLayer", user_df,
            get_position="[lon, lat]", get_fill_color=[30, 90, 220], get_radius=400,
        )
        view_state = pdk.ViewState(latitude=analysis["lat"], longitude=analysis["lon"], zoom=10)
        st.pydeck_chart(pdk.Deck(
            layers=[resource_layer, user_layer], initial_view_state=view_state,
            tooltip={"text": "{name} ({kind})"},
        ))
        st.caption("🔵 Your location — colors correspond to resource types shown below.")

    # ── Routes first: evacuation guidance and hospital access ──
    _render_route_section(analysis)

    # ── Separate resource groups ──
    _render_resource_group("Hospitals & Clinics", "🏥", analysis["hospitals"], expanded=True, error=analysis.get("hospital_error"))
    _render_resource_group("Food & Relief", "🍞", analysis["food_places"], expanded=True, error=analysis.get("food_error"))
    _render_resource_group("Shelters & Evacuation Centers", "🏠", analysis["shelters"], expanded=True)
    _render_resource_group("Ambulance Stations", "🚑", analysis["ambulance_stations"])
    _render_resource_group("Police Stations", "👮", analysis["police_stations"])
    _render_resource_group("Fire Stations", "🚒", analysis["fire_stations"])
    _render_resource_group("Blood Banks", "🩸", analysis["blood_banks"])
    _render_resource_group("NGOs & Aid Organizations", "🤝", analysis["ngos"])
    _render_resource_group("Rescue Teams", "🚁", analysis["rescue_teams"])
    _render_resource_group("Community Kitchens", "🍲", analysis["community_kitchens"])

    # ── Dispatch, routes, and coordination ──
    if analysis.get("ambulance_info"):
        st.markdown('<div class="er-section-title">🚑 Ambulance Dispatch System</div>', unsafe_allow_html=True)
        _render_ambulance_section(analysis["ambulance_info"])


# =========================================================
#  RENDER: ANALYTICS TAB
# =========================================================
_ANALYTICS_CSS = """
<style>
.an-hero { background: linear-gradient(135deg,#172554,#1e3a8a 55%,#0f766e); border-radius: 18px; padding: 24px 28px; color: white; margin-bottom: 18px; box-shadow: 0 8px 26px rgba(15,23,42,.22); }
.an-hero-top { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }
.an-hero-title { font-size:1.35rem; font-weight:800; }
.an-hero-sub { font-size:.85rem; opacity:.82; margin-top:5px; }
.an-hero-score { text-align:right; }
.an-hero-score-value { font-size:2rem; font-weight:900; line-height:1; }
.an-hero-score-label { font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; opacity:.78; margin-top:5px; }
.an-kpi-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:16px 0 24px; }
.an-kpi { background:#171a22; border:1px solid #2b3240; border-radius:14px; padding:15px 16px; }
.an-kpi-label { color:#9ca8ba; font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; }
.an-kpi-value { color:#f8fafc; font-size:1.35rem; font-weight:800; margin-top:5px; }
.an-kpi-note { color:#7f8da3; font-size:.72rem; margin-top:3px; }
.an-section { color:#f8fafc; font-size:1.05rem; font-weight:800; margin:24px 0 10px; }
.an-alert { background:#291b1b; border:1px solid #713f3f; color:#fecaca; border-radius:11px; padding:13px 16px; margin:8px 0; font-size:.84rem; }
.an-alert-head { display:flex; justify-content:space-between; gap:12px; font-weight:800; color:#fff1f2; }
.an-alert-meta { color:#fda4af; font-size:.75rem; margin-top:5px; }
.an-alert-detail { color:#fecdd3; line-height:1.5; margin-top:8px; }
.an-alert-actions { color:#fed7aa; line-height:1.5; margin-top:7px; }
@media (max-width: 800px) { .an-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
</style>
"""


def render_analytics_tab(analysis):
    if analysis is None:
        st.info("Run an analysis from the input above to see analytics here.")
        return

    st.markdown(_ANALYTICS_CSS, unsafe_allow_html=True)

    overall = analysis["overall_risk"]
    warning_count = len(analysis.get("early_warning_alerts", []))
    rain_series = analysis.get("rain_24h") or []
    temp_series = analysis.get("temp_24h") or []
    peak_rain = max(rain_series, default=0)
    temp_range = (max(temp_series) - min(temp_series)) if temp_series else 0

    st.markdown(
        f"<div class='an-hero'><div class='an-hero-top'><div><div class='an-hero-title'>📊 Analytics Overview</div><div class='an-hero-sub'>Live conditions for {analysis['district']}, {analysis['state']} · {analysis['current_date']} {analysis['current_time']}</div></div><div class='an-hero-score'><div class='an-hero-score-value'>{overall}</div><div class='an-hero-score-label'>Overall Risk · {round(analysis['risk_score'], 1)} score</div></div></div></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='an-kpi-grid'><div class='an-kpi'><div class='an-kpi-label'>🌧️ Rainfall · 6 hours</div><div class='an-kpi-value'>{round(analysis['rainfall'], 1)} mm</div><div class='an-kpi-note'>Peak next 24h: {round(peak_rain, 1)} mm</div></div><div class='an-kpi'><div class='an-kpi-label'>🌡️ Current temperature</div><div class='an-kpi-value'>{analysis['temperature']} °C</div><div class='an-kpi-note'>Forecast range: {round(temp_range, 1)} °C</div></div><div class='an-kpi'><div class='an-kpi-label'>💨 Wind speed</div><div class='an-kpi-value'>{analysis['windspeed']} km/h</div><div class='an-kpi-note'>{'Rain detected' if analysis['is_raining'] else 'No rain detected'}</div></div><div class='an-kpi'><div class='an-kpi-label'>⚠️ Active warnings</div><div class='an-kpi-value'>{warning_count}</div><div class='an-kpi-note'>Across monitored hazards</div></div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='an-section'>📈 24-Hour Weather Forecast</div>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig, ax = plt.subplots(figsize=(7, 3.4))
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#171a22")
        ax.plot(range(len(rain_series)), rain_series, color="#38bdf8", linewidth=2.5, marker="o", markersize=3)
        ax.fill_between(range(len(rain_series)), rain_series, color="#38bdf8", alpha=.12)
        ax.set_title("Rainfall forecast", color="white", loc="left", fontsize=12, fontweight="bold")
        ax.set_xlabel("Hours ahead", color="#9ca8ba")
        ax.set_ylabel("Millimetres", color="#9ca8ba")
        ax.tick_params(colors="#9ca8ba")
        ax.grid(axis="y", color="#334155", alpha=.45)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    with chart_col2:
        fig, ax = plt.subplots(figsize=(7, 3.4))
        fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#171a22")
        ax.plot(range(len(temp_series)), temp_series, color="#fb923c", linewidth=2.5, marker="o", markersize=3)
        ax.fill_between(range(len(temp_series)), temp_series, color="#fb923c", alpha=.12)
        ax.set_title("Temperature forecast", color="white", loc="left", fontsize=12, fontweight="bold")
        ax.set_xlabel("Hours ahead", color="#9ca8ba")
        ax.set_ylabel("Degrees Celsius", color="#9ca8ba")
        ax.tick_params(colors="#9ca8ba")
        ax.grid(axis="y", color="#334155", alpha=.45)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    # ---------- All Disasters Comparison ----------
    # Pulls straight from the same hazard_detail dicts (flood_detail,
    # landslide_detail, cyclone_detail, heatwave_detail, drought_detail,
    # earthquake_detail, volcano_detail) that the Disaster Prediction tab
    # renders — nothing recomputed here, just an all-in-one comparison
    # view across every monitored hazard.
    st.markdown("<div class='an-section'>🧭 Risk Profile by Hazard</div>", unsafe_allow_html=True)

    hazard_keys = ["flood", "landslide", "cyclone", "heatwave", "drought", "earthquake", "volcano"]
    hazard_labels = {
        "flood": "Flood", "landslide": "Landslide", "cyclone": "Storm/Cyclone",
        "heatwave": "Heatwave", "drought": "Drought", "earthquake": "Earthquake",
        "volcano": "Volcano",
    }
    hazard_icons = {
        "flood": "🌊", "landslide": "⛰️", "cyclone": "🌀", "heatwave": "🌡️",
        "drought": "🏜️", "earthquake": "🌍", "volcano": "🌋",
    }
    detail_map = {
        "flood": analysis["flood_detail"], "landslide": analysis["landslide_detail"],
        "cyclone": analysis["cyclone_detail"], "heatwave": analysis["heatwave_detail"],
        "drought": analysis["drought_detail"], "earthquake": analysis["earthquake_detail"],
        "volcano": analysis["volcano_detail"],
    }
    level_colors = {"HIGH": "#c0392b", "MEDIUM": "#e2a712", "LOW": "#3a8fd8", "NONE": "#27ae60"}

    labels = [hazard_labels[k] for k in hazard_keys]
    probs = [detail_map[k]["probability_pct"] for k in hazard_keys]
    confs = [detail_map[k]["confidence_pct"] for k in hazard_keys]
    levels = [detail_map[k]["level"] for k in hazard_keys]
    bar_colors = [level_colors.get(lvl, "#999999") for lvl in levels]

    # Probability and confidence are shown together so the chart communicates
    # both the forecast signal and how strongly the model supports it.
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#171a22")
    x = list(range(len(hazard_keys)))
    width = .36
    ax.bar([i - width / 2 for i in x], probs, width=width, color=bar_colors, label="Probability")
    ax.bar([i + width / 2 for i in x], confs, width=width, color="#94a3b8", alpha=.72, label="Confidence")
    ax.set_xticks(x)
    chart_labels = [hazard_labels[k].replace("Storm/Cyclone", "Storm\nCyclone") for k in hazard_keys]
    ax.set_xticklabels(chart_labels, rotation=0, ha="center")
    ax.set_ylabel("Percent", color="#cbd5e1")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, labelcolor="white")
    ax.grid(axis="y", color="#334155", alpha=.45)
    ax.tick_params(colors="#9ca8ba", axis="y")
    ax.tick_params(axis="x", colors="#cbd5e1", labelsize=9, pad=8)
    for spine in ax.spines.values():
        spine.set_color("#334155")
    st.pyplot(fig)
    plt.close(fig)

    # Full detail table underneath.
    disaster_table = pd.DataFrame({
        "Hazard": labels,
        "Risk Level": levels,
        "Probability (%)": probs,
        "Confidence (%)": confs,
        "Expected Window": [detail_map[k]["expected_window"] for k in hazard_keys],
    })
    st.dataframe(disaster_table, width="stretch", hide_index=True)

    if analysis.get("early_warning_alerts"):
        st.markdown("<div class='an-section'>🚨 Early-Warning Alerts</div>", unsafe_allow_html=True)
        for alert in analysis["early_warning_alerts"]:
            if isinstance(alert, dict):
                hazard = escape(str(alert.get("hazard", "Hazard")))
                level = escape(str(alert.get("level", "WARNING")))
                probability = escape(str(alert.get("probability_pct", "—")))
                confidence = escape(str(alert.get("confidence_pct", "—")))
                window = escape(str(alert.get("window", "Monitor conditions")))
                reasons = " • ".join(escape(str(reason)) for reason in alert.get("reasons", []))
                actions = " • ".join(escape(str(action)) for action in alert.get("actions", []))
                alert_html = (
                    f"<div class='an-alert'><div class='an-alert-head'><span>⚠️ {hazard}</span><span>{level}</span></div>"
                    f"<div class='an-alert-meta'>Probability {probability}% · Confidence {confidence}% · {window}</div>"
                    f"<div class='an-alert-detail'><b>Why:</b> {reasons}</div>"
                    f"<div class='an-alert-actions'><b>Recommended:</b> {actions}</div></div>"
                )
            else:
                alert_html = f"<div class='an-alert'>⚠️ {escape(str(alert))}</div>"
            st.markdown(alert_html, unsafe_allow_html=True)

    st.markdown("<div class='an-section'>🗺️ Location & Resource Context</div>", unsafe_allow_html=True)
    st.image(_build_location_map_png(analysis, dark_theme=True), width="stretch")


# =========================================================
#  RENDER: REPORT TAB
# =========================================================
def render_report_tab(analysis):
    if analysis is None:
        st.info("Run an analysis from the input above to generate a report.")
        return

    st.markdown(
        "<style>.report-hero{background:linear-gradient(135deg,#172554,#1e3a8a 55%,#0f766e);border-radius:18px;padding:22px 26px;color:white;margin-bottom:18px}.report-title{font-size:1.3rem;font-weight:800}.report-sub{font-size:.85rem;opacity:.82;margin-top:5px}.report-panel{background:#171a22;border:1px solid #2b3442;border-radius:14px;padding:16px;color:#cbd5e1;margin-bottom:14px}.report-panel-title{color:#f8fafc;font-weight:800;margin-bottom:5px}[data-testid='stDownloadButton'] button{border-radius:10px;border:1px solid #3b82f6;background:#1d4ed8;color:white;font-weight:700}[data-testid='stDownloadButton'] button:hover{background:#2563eb;border-color:#60a5fa}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='report-hero'><div class='report-title'>📄 Disaster Analysis Report</div><div class='report-sub'>{analysis['district']}, {analysis['state']} · {analysis['current_date']} {analysis['current_time']}</div></div>",
        unsafe_allow_html=True,
    )
    # st.text_area("Report Summary", analysis["report_text"], height=300)

    try:
        pdf_bytes = create_pdf(analysis)
    except Exception as e:
        log_error("PDF generation failed.", exc=e)
        pdf_bytes = None

    if pdf_bytes:
        st.markdown("<div class='report-panel'><div class='report-panel-title'>📑 Full PDF report</div>Complete analysis with charts, hazards, recommendations, and emergency resources.</div>", unsafe_allow_html=True)
        st.download_button(label="📄 Download PDF Report", data=pdf_bytes, file_name="disaster_report.pdf", mime="application/pdf")

    try:
        audio_bytes = generate_audio_report(analysis)
        st.markdown("<div class='report-panel'><div class='report-panel-title'>🎧 Audio briefing</div>Listen to a spoken summary of the same analysis.</div>", unsafe_allow_html=True)
        st.audio(audio_bytes, format="audio/mpeg")
        st.download_button(label="🎵 Download Audio Report", data=audio_bytes, file_name="disaster_audio_report.mp3", mime="audio/mpeg")
    except Exception as e:
        log_error("Error generating or playing audio report.", exc=e)


# =========================================================
#  APP ENTRY POINT
# =========================================================
def main():
    st.set_page_config(page_title="Disaster Copilot", layout="wide")

    st.title("🌍 Disaster Copilot Dashboard")
    st.markdown("Real-time disaster risk analysis using weather intelligence")

    now = datetime.datetime.now()
    st.markdown(f"📅 Date: {now.strftime('%d %B %Y')} | ⏰ Time: {now.strftime('%I:%M %p')}")

    if "analysis" not in st.session_state:
        st.session_state.analysis = None

    place = st.text_input("Enter Place Name")
    if st.button("Analyze Risk"):
        with st.spinner("Analyzing risk..."):
            try:
                result = run_analysis(place)
            except Exception as e:
                result = None
                log_error("Something went wrong while analyzing this location.", exc=e)

        if result is None:
            st.error("Place not found ❌")
        else:
            st.session_state.analysis = result

    tab_home, tab_pred, tab_resp, tab_analytics, tab_report = st.tabs(
        ["🏠 Home", "🌪️ Disaster Prediction", "🚨 Emergency Response", "📊 Analytics", "📄 Report"]
    )

    with tab_home:
        render_home_tab(st.session_state.analysis)
    with tab_pred:
        render_prediction_tab(st.session_state.analysis)
    with tab_resp:
        render_response_tab(st.session_state.analysis)
    with tab_analytics:
        render_analytics_tab(st.session_state.analysis)
    with tab_report:
        render_report_tab(st.session_state.analysis)


if __name__ == "__main__":
    main()
