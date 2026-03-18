"""
geo_map.py - Interactive geopolitical risk world map using pydeck.
Uses open-source map tiles (no Mapbox token required).
Dots are large, clearly colored, with bold country labels.
"""

import pydeck as pdk
import pandas as pd
from geo_engine import get_country_risk_summary


def build_risk_map() -> pdk.Deck:
    """Build a highly visible interactive world risk map."""
    risk_data = get_country_risk_summary()
    df = pd.DataFrame(risk_data)

    # ── Tooltip HTML ──────────────────────────────────────────────────────
    df["tooltip_html"] = df.apply(
        lambda r: (
            f"<div style='font-family:sans-serif;'>"
            f"<div style='font-size:15px;font-weight:700;color:#FFD700;margin-bottom:6px;'>"
            f"  {r['country']}"
            f"</div>"
            f"<div style='color:#FF8C42;font-weight:600;margin-bottom:4px;'>"
            f"  ⚠ Risk Level: {r['risk_label']}"
            f"</div>"
            f"<div style='color:#F0F4FF;margin-bottom:3px;'>"
            f"  <b>Event:</b> {r['event']}"
            f"</div>"
            f"<div style='color:#8B99B5;margin-bottom:3px;font-size:11px;'>"
            f"  <b>Why:</b> {r['reason']}"
            f"</div>"
            f"<div style='color:#00E5A0;margin-top:4px;font-size:11px;'>"
            f"  <b>Affected:</b> {r['assets']}"
            f"</div>"
            f"<div style='margin-top:4px;'>{'🔴' * min(r['severity'], 5)}</div>"
            f"</div>"
        ),
        axis=1,
    )

    # ── Radius: larger so dots are clearly visible ────────────────────────
    # severity 10 → ~900k metres on screen; minimum enforced by radius_min_pixels
    df["dot_radius"] = df["severity"] * 90000

    # ── Outer glow layer (semi-transparent, 2× radius) ───────────────────
    glow_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color=[
            # dynamic color per row handled via get_color column
            "color[0]", "color[1]", "color[2]", 35
        ],
        get_radius="dot_radius",
        radius_scale=2.5,
        radius_min_pixels=20,
        radius_max_pixels=140,
        pickable=False,
        opacity=0.25,
        stroked=False,
    )

    # ── Main dot layer ────────────────────────────────────────────────────
    dot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="dot_radius",
        radius_min_pixels=14,
        radius_max_pixels=80,
        pickable=True,
        opacity=0.90,
        stroked=True,
        get_line_color=[255, 255, 255, 160],
        line_width_min_pixels=2,
    )

    # ── Country name text layer ───────────────────────────────────────────
    text_layer = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["lon", "lat"],
        get_text="country",
        get_size=14,
        get_color=[255, 255, 255, 240],
        get_weight=700,
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 22],
        billboard=True,
    )

    # ── Risk label text (HIGH / MEDIUM / LOW) ────────────────────────────
    risk_label_layer = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["lon", "lat"],
        get_text="risk_label",
        get_size=10,
        get_color="color",
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 38],
        billboard=True,
    )

    # ── View: centred on Europe/Middle East where most events are ─────────
    view_state = pdk.ViewState(
        latitude=25,
        longitude=20,
        zoom=1.8,
        pitch=0,
        bearing=0,
    )

    tooltip = {
        "html": "{tooltip_html}",
        "style": {
            "backgroundColor": "#111827",
            "color": "#F0F4FF",
            "fontSize": "12px",
            "padding": "14px",
            "borderRadius": "10px",
            "border": "1px solid #3B82F6",
            "maxWidth": "340px",
            "boxShadow": "0 4px 24px rgba(0,0,0,0.6)",
        },
    }

    # Use carto-dark (no Mapbox token needed, always renders)
    deck = pdk.Deck(
        layers=[glow_layer, dot_layer, text_layer, risk_label_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    )
    return deck


def get_risk_legend() -> list:
    return [
        {"color": "#FF3B5B", "label": "🔴 HIGH RISK",   "desc": "Active conflict / severe disruption"},
        {"color": "#FF8C42", "label": "🟠 MEDIUM RISK",  "desc": "Elevated tension / significant impact"},
        {"color": "#00E5A0", "label": "🟢 LOW RISK",     "desc": "Monitoring / minor impact"},
    ]