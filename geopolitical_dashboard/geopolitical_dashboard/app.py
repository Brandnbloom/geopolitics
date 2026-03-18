"""
app.py - GeoSignal: Geopolitical Market Intelligence Dashboard
Real-time data: yfinance (market) + NewsAPI (news). Zero mock data.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time

st.set_page_config(
    page_title="GeoSignal — Market Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from config import (
    GEO_EVENTS, ASSET_CATEGORIES, ALL_TICKERS, COLORS,
    SECTOR_ICONS, SECTORS, WAR_START_DATE, REFRESH_INTERVAL,
)
from data_fetch import (
    fetch_all_prices, get_latest_prices, get_cumulative_returns,
    get_correlation_matrix, get_commodity_daily_changes,
    get_sector_heatmap_data, get_live_quotes_all,
)
from news_fetch import fetch_news
from geo_engine import (
    get_country_risk_summary, get_global_risk_score,
    generate_market_insight, get_kpi_metrics,
)
from geo_map import build_risk_map, get_risk_legend
from geo_impact import (
    build_sector_heatmap, build_commodity_heatmap,
    build_correlation_matrix, build_cumulative_returns_chart,
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0A0E1A;
    color: #F0F4FF;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 0.5rem; max-width: 100%; }

.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #111827; border-radius: 12px;
    padding: 6px; border: 1px solid #1E2D45;
}
.stTabs [data-baseweb="tab"] {
    height: 40px; padding: 0 20px; background: transparent;
    border-radius: 8px; color: #8B99B5; font-weight: 600;
    font-size: 13px; letter-spacing: 0.5px; border: none;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1E3A5F, #1A2D4A) !important;
    color: #F0F4FF !important; border: 1px solid #3B82F6 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1A2236 100%);
    border: 1px solid #1E2D45; border-radius: 14px;
    padding: 16px 18px; position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px; background: linear-gradient(90deg, #3B82F6, #00E5A0);
}
.kpi-label  { font-size: 11px; font-weight: 600; color: #8B99B5; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value  { font-size: 22px; font-weight: 700; color: #F0F4FF; font-family: 'JetBrains Mono', monospace; line-height: 1.2; }
.kpi-pos    { color: #00E5A0; font-size: 12px; font-weight: 600; margin-top: 4px; }
.kpi-neg    { color: #FF3B5B; font-size: 12px; font-weight: 600; margin-top: 4px; }
.kpi-neu    { color: #FFD700; font-size: 12px; font-weight: 600; margin-top: 4px; }

.ticker-strip {
    background: #0D1120; border: 1px solid #1E2D45; border-radius: 8px;
    padding: 8px 14px; display: flex; gap: 28px; overflow-x: auto;
    white-space: nowrap; margin-bottom: 14px; align-items: center;
}
.ticker-item { display: inline-flex; flex-direction: column; align-items: flex-start; }
.ticker-name { font-size: 10px; color: #8B99B5; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
.ticker-price { font-size: 14px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #F0F4FF; }
.ticker-chg-pos { font-size: 11px; color: #00E5A0; font-weight: 600; }
.ticker-chg-neg { font-size: 11px; color: #FF3B5B; font-weight: 600; }

.news-card {
    background: #111827; border: 1px solid #1E2D45;
    border-left: 3px solid #3B82F6; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px;
}
.news-card.risk        { border-left-color: #FF3B5B; }
.news-card.opportunity { border-left-color: #00E5A0; }
.news-card.mixed       { border-left-color: #FFD700; }
.news-title   { font-size: 14px; font-weight: 600; color: #F0F4FF; margin-bottom: 6px; line-height: 1.4; }
.news-meta    { font-size: 11px; color: #8B99B5; margin-bottom: 8px; }
.news-desc    { font-size: 12px; color: #8B99B5; margin-bottom: 8px; line-height: 1.5; }
.news-insight { font-size: 12px; color: #F0F4FF; background: #1A2236; border-radius: 6px; padding: 8px 10px; margin-top: 6px; line-height: 1.5; }
.sector-badge { display: inline-block; background: #1E2D45; color: #8B99B5; border-radius: 4px; padding: 2px 7px; font-size: 10px; font-weight: 600; margin-right: 4px; margin-top: 4px; }

.section-header { font-size: 13px; font-weight: 700; color: #8B99B5; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 0; border-bottom: 1px solid #1E2D45; margin-bottom: 14px; }
.info-box { background: #0D1E35; border: 1px solid #1E3A5F; border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #8B99B5; margin-bottom: 10px; }

.live-badge { display: inline-flex; align-items: center; gap: 5px; background: #0D4A2A; border: 1px solid #00E5A0; border-radius: 20px; padding: 4px 10px; font-size: 11px; font-weight: 700; color: #00E5A0; }
.live-dot   { width: 7px; height: 7px; background: #00E5A0; border-radius: 50%; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

.data-source-badge { display: inline-flex; align-items: center; gap: 4px; background: #0D1E35; border: 1px solid #1E3A5F; border-radius: 6px; padding: 3px 8px; font-size: 10px; color: #8B99B5; font-weight: 600; }
.data-source-badge.live { border-color: #00E5A0; color: #00E5A0; background: #0D4A2A22; }

[data-testid="stDataFrame"] { border: 1px solid #1E2D45; border-radius: 10px; overflow: hidden; }
.stMultiSelect [data-baseweb="select"] { background: #111827; border-color: #1E2D45; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _color_num(v):
    """Cell styler for numeric change columns."""
    if isinstance(v, (int, float)):
        return f"color:{'#00E5A0' if v > 0 else '#FF3B5B' if v < 0 else '#FFD700'}"
    return ""

def _color_perf(v):
    """Cell styler for performance league table."""
    if not isinstance(v, (int, float)):
        return ""
    if v > 20:  return "color:#00E5A0;font-weight:700"
    if v > 0:   return "color:#34D399"
    if v > -20: return "color:#FF8C42"
    return "color:#FF3B5B;font-weight:700"

def _color_risk(v):
    """Cell styler for risk level column."""
    return ("color:#FF3B5B;font-weight:700" if v == "HIGH" else
            "color:#FF8C42;font-weight:700" if v == "MEDIUM" else
            "color:#00E5A0;font-weight:700" if v == "LOW" else "")


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def render_header(last_updated: str, risk_score: float, risk_label: str, data_ok: bool):
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown("""
        <div>
          <div style="font-size:24px;font-weight:700;background:linear-gradient(90deg,#3B82F6,#00E5A0);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-0.5px;">
            🌐 GeoSignal Intelligence
          </div>
          <div style="font-size:12px;color:#8B99B5;letter-spacing:1px;margin-top:2px;">
            REAL-TIME GEOPOLITICAL MARKET INTELLIGENCE PLATFORM
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        rc = "#FF3B5B" if risk_label in ("CRITICAL", "HIGH") else "#FF8C42" if risk_label == "ELEVATED" else "#FFD700"
        st.markdown(f"""
        <div style="text-align:right;padding-top:4px;">
          <div style="font-size:11px;color:#8B99B5;text-transform:uppercase;letter-spacing:1px;">Global Risk Index</div>
          <div style="font-size:20px;font-weight:700;color:{rc};font-family:'JetBrains Mono',monospace;">
            {risk_score}/10 <span style="font-size:13px;">{risk_label}</span>
          </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        data_badge = '<span class="data-source-badge live">✓ LIVE DATA</span>' if data_ok \
                     else '<span class="data-source-badge" style="color:#FF3B5B;border-color:#FF3B5B;">⚠ DATA ERROR</span>'
        st.markdown(f"""
        <div style="text-align:right;padding-top:6px;">
          <div class="live-badge"><div class="live-dot"></div>LIVE</div>
          <div style="margin-top:5px;">{data_badge}</div>
          <div style="font-size:10px;color:#8B99B5;margin-top:4px;">
            Yahoo Finance · NewsAPI · {last_updated}
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #1E2D45;margin:10px 0 16px;'>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LIVE TICKER STRIP
# ─────────────────────────────────────────────────────────────────────────────
_TICKER_ASSETS = [
    "S&P 500", "Nasdaq", "NIFTY 50", "Hang Seng",
    "Crude Oil (WTI)", "Brent Crude", "Gold", "Natural Gas",
    "USD/INR", "EUR/USD", "USD/JPY",
    "HAL (India)", "BEL (India)",
]

def render_ticker_strip(live_quotes: dict):
    items_html = ""
    for name in _TICKER_ASSETS:
        q = live_quotes.get(name)
        if not q:
            continue
        price = q["price"]
        chg   = q["change_pct"]
        arrow = "▲" if chg >= 0 else "▼"
        cls   = "ticker-chg-pos" if chg >= 0 else "ticker-chg-neg"
        fmt   = f"{price:,.4f}" if price < 10 else f"{price:,.2f}" if price < 10000 else f"{price:,.0f}"
        items_html += f"""
        <div class="ticker-item">
          <span class="ticker-name">{name}</span>
          <span class="ticker-price">{fmt}</span>
          <span class="{cls}">{arrow} {abs(chg):.2f}%</span>
        </div>"""
    st.markdown(f'<div class="ticker-strip">{items_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI BAR
# ─────────────────────────────────────────────────────────────────────────────
def render_kpi_bar(kpis: list):
    cols = st.columns(len(kpis))
    for i, kpi in enumerate(kpis):
        with cols[i]:
            ch = kpi.get("change")
            if ch is None:
                chg_html = f'<div class="kpi-neu">{kpi["unit"]}</div>'
            elif ch > 0:
                chg_html = f'<div class="kpi-pos">▲ {ch:+.2f}% today</div>'
            elif ch < 0:
                chg_html = f'<div class="kpi-neg">▼ {ch:.2f}% today</div>'
            else:
                chg_html = '<div class="kpi-neu">— flat today</div>'
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{kpi['label']}</div>
              <div class="kpi-value">{kpi['value']}</div>
              {chg_html}
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PRICE CHART
# ─────────────────────────────────────────────────────────────────────────────
def build_price_chart(asset_name: str, price_df: pd.DataFrame,
                      day_chg: float, war_chg: float) -> go.Figure:
    if price_df.empty:
        fig = go.Figure()
        fig.update_layout(
            plot_bgcolor="#0A0E1A", paper_bgcolor="#0A0E1A",
            annotations=[dict(text="No data available", xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(color="#8B99B5", size=14))]
        )
        return fig

    lc  = "#00E5A0" if war_chg >= 0 else "#FF3B5B"
    rgb = "0,229,160" if war_chg >= 0 else "255,59,91"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=price_df.index, y=price_df["price"],
        fill="tozeroy",
        fillcolor=f"rgba({rgb}, 0.07)",
        line=dict(color=lc, width=1.8),
        name=asset_name,
        hovertemplate=(
            f"<b>{asset_name}</b><br>"
            "Date: %{x|%b %d, %Y}<br>"
            "Price: %{y:,.4f}<br>"
            "<extra></extra>"
        ),
    ))

    for event in GEO_EVENTS:
        edate = pd.Timestamp(event["date"])
        if edate < price_df.index[0] or edate > price_df.index[-1]:
            continue
        idx = price_df.index.searchsorted(edate)
        if idx >= len(price_df):
            continue
        snap_price = float(price_df["price"].iloc[idx])
        fig.add_vline(x=price_df.index[idx], line_dash="dot",
                      line_color="#1E2D45", line_width=1)
        fig.add_annotation(
            x=price_df.index[idx], y=snap_price,
            text=event["label"].split(" ")[0],
            showarrow=True, arrowhead=2, arrowsize=0.8,
            arrowcolor="#3B82F6", font=dict(size=12, color="#3B82F6"),
            bgcolor="#0D1E35", bordercolor="#3B82F6",
            borderwidth=1, borderpad=3,
            hovertext=f"{event['label']}<br>{event['detail']}",
        )

    fig.update_layout(
        title=dict(
            text=f"{asset_name}  |  Today: {'▲' if day_chg >= 0 else '▼'} {day_chg:+.2f}%"
                 f"  |  Since Feb 2022: {war_chg:+.1f}%",
            font=dict(color="#F0F4FF", size=14),
        ),
        plot_bgcolor="#0A0E1A", paper_bgcolor="#0A0E1A",
        font=dict(color="#8B99B5"),
        xaxis=dict(showgrid=True, gridcolor="#111827", gridwidth=0.5,
                   tickfont=dict(color="#8B99B5", size=10)),
        yaxis=dict(showgrid=True, gridcolor="#111827", gridwidth=0.5,
                   tickfont=dict(color="#8B99B5", size=10)),
        margin=dict(l=10, r=10, t=50, b=20),
        height=320, hovermode="x unified", showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MARKETS TAB
# ─────────────────────────────────────────────────────────────────────────────
def render_markets_tab(latest_df: pd.DataFrame, all_prices: dict, live_quotes: dict):
    st.markdown('<div class="section-header">Asset Price Monitor — Feb 24, 2022 to Today (Yahoo Finance)</div>',
                unsafe_allow_html=True)

    if latest_df.empty:
        st.error("Market data unavailable. Ensure you have internet access and yfinance is installed.")
        return

    cat_tabs = st.tabs(["Indices", "Commodities", "Currencies", "Defense Stocks"])
    for cat_tab, cat_key in zip(cat_tabs, ["Indices", "Commodities", "Currencies", "Defense Stocks"]):
        with cat_tab:
            assets = ASSET_CATEGORIES[cat_key]
            cat_df = latest_df[latest_df["Category"] == cat_key][
                ["Asset", "Price", "Day %", "Since Feb 22", "Last Date"]].copy()

            if not cat_df.empty:
                styled = (cat_df.style
                          .map(_color_num, subset=["Day %", "Since Feb 22"])
                          .format({"Price": "{:.4f}", "Day %": "{:+.2f}%", "Since Feb 22": "{:+.1f}%"}))
                st.dataframe(styled, use_container_width=True,
                             height=min(200, len(cat_df) * 40 + 40))

            # Live quote callout
            live_row = []
            for name in assets:
                q = live_quotes.get(name)
                if q:
                    arrow = "▲" if q["change_pct"] >= 0 else "▼"
                    col   = "#00E5A0" if q["change_pct"] >= 0 else "#FF3B5B"
                    src   = "live" if q.get("source") == "live" else "EOD"
                    live_row.append(
                        f"<b style='color:#F0F4FF'>{name}</b> "
                        f"<span style='font-family:monospace'>{q['price']:,.4f}</span> "
                        f"<span style='color:{col}'>{arrow}{abs(q['change_pct']):.2f}%</span> "
                        f"<span style='color:#8B99B5;font-size:10px'>({src})</span>"
                    )
            if live_row:
                st.markdown(
                    '<div class="info-box" style="margin-bottom:12px;"><b>Live Quotes:</b> &nbsp;&nbsp;'
                    + " &nbsp;|&nbsp; ".join(live_row) + "</div>",
                    unsafe_allow_html=True
                )

            # Charts 2-per-row
            for i in range(0, len(assets), 2):
                cols = st.columns(2)
                for j, asset in enumerate(assets[i:i + 2]):
                    with cols[j]:
                        df  = all_prices.get(asset, pd.DataFrame())
                        row = latest_df[latest_df["Asset"] == asset]
                        dc  = float(row["Day %"].values[0])       if not row.empty else 0.0
                        wc  = float(row["Since Feb 22"].values[0]) if not row.empty else 0.0
                        st.plotly_chart(build_price_chart(asset, df, dc, wc),
                                        use_container_width=True,
                                        config={"displayModeBar": False})
                        st.markdown(
                            f'<div class="info-box">💡 {generate_market_insight(asset, dc, wc)}</div>',
                            unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# NEWS TAB
# ─────────────────────────────────────────────────────────────────────────────
def render_news_tab(articles: list):
    st.markdown('<div class="section-header">Live Geopolitical News — NewsAPI · Rule-Based Insights</div>',
                unsafe_allow_html=True)

    if not articles:
        st.warning("No news articles loaded. Check your NEWSAPI_KEY in config.py.")
        return

    c1, c2 = st.columns([3, 1])
    with c1:
        filters = st.multiselect("Filter by sentiment", ["risk", "opportunity", "mixed"],
                                 default=["risk", "opportunity", "mixed"], key="news_filter")
    with c2:
        st.markdown(f"<div style='padding-top:28px;font-size:11px;color:#8B99B5;'>"
                    f"{len(articles)} live articles · auto-refresh every 2 min</div>",
                    unsafe_allow_html=True)

    shown = [a for a in articles if a["sentiment"] in filters]
    if not shown:
        st.info("No articles match the selected filters.")
        return

    for art in shown:
        sent = art["sentiment"]
        icon = "🔴" if sent == "risk" else "🟢" if sent == "opportunity" else "🟡"
        sectors_html = "".join(
            f'<span class="sector-badge">{s}</span>'
            for s in art["sectors"]
        )
        desc       = art.get("description", "")
        desc_short = (desc[:180] + "…") if len(desc) > 180 else desc

        st.markdown(f"""
        <div class="news-card {sent}">
          <div class="news-title">
            <a href="{art['url']}" target="_blank" style="color:#F0F4FF;text-decoration:none;">
              {art['title']}
            </a>
          </div>
          <div class="news-meta">
            <b>{art['source']}</b> · {art['published_str']} · {icon} {sent.upper()}
          </div>
          <div class="news-desc">{desc_short}</div>
          <div class="news-insight">{art['insight']}</div>
          <div style="margin-top:8px;">{sectors_html}</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAPS & SECTOR TAB
# ─────────────────────────────────────────────────────────────────────────────
def render_maps_tab(sector_df: pd.DataFrame):
    st.markdown('<div class="section-header">Global Geopolitical Risk Map</div>',
                unsafe_allow_html=True)

    for lc, leg in zip(st.columns(3), get_risk_legend()):
        with lc:
            st.markdown(f"""
            <div style="display:flex;align-items:center;background:#111827;border:1px solid #1E2D45;
                 border-radius:8px;padding:8px 12px;">
              <div style="width:12px;height:12px;border-radius:50%;background:{leg['color']};margin-right:8px;"></div>
              <div>
                <div style="font-size:12px;font-weight:700;color:#F0F4FF;">{leg['label']}</div>
                <div style="font-size:10px;color:#8B99B5;">{leg['desc']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    try:
        st.pydeck_chart(build_risk_map(), use_container_width=True)
    except Exception as e:
        st.error(f"Map error: {e}")

    st.markdown('<div class="section-header" style="margin-top:20px;">Country Risk Tracker</div>',
                unsafe_allow_html=True)

    rows = [{
        "Country":         r["country"],
        "Risk Level":      r["risk_label"],
        "Event":           r["event"],
        "Severity":        "H" * min(r["severity"], 5),
        "Affected Assets": r["assets"],
    } for r in get_country_risk_summary()]

    st.dataframe(
        pd.DataFrame(rows).style.map(_color_risk, subset=["Risk Level"]),
        use_container_width=True, height=380
    )

    st.markdown('<div class="section-header" style="margin-top:20px;">Sector Impact Heatmap</div>',
                unsafe_allow_html=True)
    if not sector_df.empty:
        st.plotly_chart(build_sector_heatmap(sector_df),
                        use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS TAB
# ─────────────────────────────────────────────────────────────────────────────
def render_analytics_tab(latest_df: pd.DataFrame):
    st.markdown('<div class="section-header">Cumulative Returns — All Assets Since Feb 2022</div>',
                unsafe_allow_html=True)

    all_assets = list(ALL_TICKERS.keys())
    selected   = st.multiselect(
        "Select assets to compare", all_assets,
        default=["S&P 500", "Gold", "Crude Oil (WTI)", "HAL (India)", "NIFTY 50", "USD/INR"],
        key="cum_ret",
    )
    cum = get_cumulative_returns()
    if not cum.empty and selected:
        st.plotly_chart(build_cumulative_returns_chart(cum, selected),
                        use_container_width=True, config={"displayModeBar": True})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">Commodity Daily % Change</div>',
                    unsafe_allow_html=True)
        cd = get_commodity_daily_changes()
        if not cd.empty:
            st.plotly_chart(build_commodity_heatmap(cd),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("Commodity data unavailable.")

    with c2:
        st.markdown('<div class="section-header">Asset Correlation Matrix</div>',
                    unsafe_allow_html=True)
        corr_sel = st.multiselect(
            "Assets for correlation", all_assets,
            default=["S&P 500", "Gold", "Crude Oil (WTI)", "NIFTY 50", "USD/INR", "HAL (India)"],
            key="corr",
        )
        full_corr = get_correlation_matrix()
        if not full_corr.empty and corr_sel:
            avail = [a for a in corr_sel if a in full_corr.columns]
            if avail:
                st.plotly_chart(build_correlation_matrix(full_corr.loc[avail, avail]),
                                use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-header" style="margin-top:10px;">Performance League Table</div>',
                unsafe_allow_html=True)
    if not latest_df.empty:
        perf = (latest_df[["Asset", "Category", "Price", "Day %", "Since Feb 22"]]
                .sort_values("Since Feb 22", ascending=False)
                .reset_index(drop=True))
        st.dataframe(
            perf.style
                .map(_color_perf, subset=["Day %", "Since Feb 22"])
                .format({"Price": "{:.4f}", "Day %": "{:+.2f}%", "Since Feb 22": "{:+.1f}%"}),
            use_container_width=True, height=500,
        )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
        st.cache_data.clear()
        st.session_state.last_refresh = time.time()
        st.rerun()

    with st.spinner("Fetching live market data from Yahoo Finance..."):
        all_prices  = fetch_all_prices()
        latest_df   = get_latest_prices()
        live_quotes = get_live_quotes_all()
        sector_df   = get_sector_heatmap_data()

    with st.spinner("Fetching live news from NewsAPI..."):
        news_articles = fetch_news(max_articles=30)

    risk_score, risk_label = get_global_risk_score()
    kpis     = get_kpi_metrics(latest_df)
    last_upd = datetime.utcnow().strftime("%H:%M UTC")
    data_ok  = not latest_df.empty

    render_header(last_upd, risk_score, risk_label, data_ok)
    render_ticker_strip(live_quotes)
    render_kpi_bar(kpis)
    st.markdown("<br>", unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([
        "Markets",
        "News & Insights",
        "Maps & Sector",
        "Analytics",
    ])
    with t1: render_markets_tab(latest_df, all_prices, live_quotes)
    with t2: render_news_tab(news_articles)
    with t3: render_maps_tab(sector_df)
    with t4: render_analytics_tab(latest_df)

    refresh_in = max(0, int(REFRESH_INTERVAL - (time.time() - st.session_state.last_refresh)))
    st.markdown(f"""
    <div style="position:fixed;bottom:10px;right:16px;background:#111827;border:1px solid #1E2D45;
         border-radius:8px;padding:6px 12px;font-size:10px;color:#8B99B5;">
      Next refresh in ~{refresh_in}s | Yahoo Finance + NewsAPI
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:30px;padding:12px;border-top:1px solid #1E2D45;text-align:center;">
      <span style="font-size:11px;color:#8B99B5;">
        GeoSignal Intelligence · Market data: Yahoo Finance ·
        News: NewsAPI.org · Insights: rule-based engine · Not financial advice.
      </span>
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
