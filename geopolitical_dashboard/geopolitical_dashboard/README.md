# 🌐 GeoSignal — Geopolitical Market Intelligence Dashboard

A fully automated, real-time geopolitical market intelligence platform built with Python and Streamlit.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the dashboard
```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`

---

## 📁 Project Structure

```
geopolitical_dashboard/
├── app.py            # Main Streamlit app (UI, tabs, layout)
├── config.py         # All constants: tickers, events, colors, rules
├── data_fetch.py     # yfinance market data + caching
├── news_fetch.py     # News API + rule-based insight engine
├── geo_engine.py     # Geopolitical risk analysis + metrics
├── geo_map.py        # Pydeck interactive world map
├── geo_impact.py     # Heatmaps, correlation, cumulative returns
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## 🗝️ Optional: Live News API

To get real headlines instead of curated mock data, add your NewsAPI key:

1. Get a free key at https://newsapi.org
2. In `app.py`, find `fetch_news(api_key="", ...)` and replace with your key:
   ```python
   fetch_news(api_key="YOUR_KEY_HERE", max_articles=20)
   ```

Without a key, the dashboard uses a curated set of realistic mock headlines with full automated insights.

---

## 🗺️ Map Features

The interactive world map uses **Pydeck** (no Mapbox token required for default tiles).

For higher-quality satellite/dark map tiles, add a Mapbox token to `.streamlit/secrets.toml`:
```toml
mapbox_token = "pk.YOUR_MAPBOX_TOKEN"
```

---

## 📊 Features

| Tab | Features |
|-----|----------|
| **Markets** | Price charts from Feb 2022, event annotations, hover tooltips, day/war % change |
| **News** | Real-time headlines, rule-based automated insights, sector impact tagging |
| **Maps & Sector** | Interactive risk map, country risk table, sector impact heatmap |
| **Analytics** | Cumulative returns, correlation matrix, commodity heatmap, league table |

---

## ⚙️ Configuration

All key settings are in `config.py`:
- `WAR_START_DATE` — start of data range
- `GEO_EVENTS` — annotated events on charts
- `COUNTRY_RISK` — map data and risk levels
- `SECTOR_RULES` — rule engine for sector impacts
- `REFRESH_INTERVAL` — auto-refresh in seconds (default: 120)

---

## ⚠️ Disclaimer

This dashboard is for **informational purposes only**. Not financial advice. Market data via Yahoo Finance. Always do your own research.
