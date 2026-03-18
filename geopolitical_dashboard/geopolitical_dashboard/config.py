"""
config.py - Central configuration for Geopolitical Market Intelligence Dashboard
"""

from datetime import date

# ─────────────────────────────────────────────
# ★ YOUR API KEYS — fill these in
# ─────────────────────────────────────────────
NEWSAPI_KEY = "e1379ea1ef3e44b6b2ad4774e1dfed57"   # https://newsapi.org — free tier: 100 req/day

# ─────────────────────────────────────────────
# DATE RANGE
# ─────────────────────────────────────────────
WAR_START_DATE = "2022-02-24"
TODAY = date.today().strftime("%Y-%m-%d")

# ─────────────────────────────────────────────
# ASSETS
# ─────────────────────────────────────────────
INDICES = {
    "S&P 500":    "^GSPC",
    "Dow Jones":  "^DJI",
    "Nasdaq":     "^IXIC",
    "FTSE 100":   "^FTSE",
    "DAX":        "^GDAXI",
    "Nikkei 225": "^N225",
    "Hang Seng":  "^HSI",
    "NIFTY 50":   "^NSEI",
}

COMMODITIES = {
    "Crude Oil (WTI)": "CL=F",
    "Brent Crude":     "BZ=F",
    "Gold":            "GC=F",
    "Silver":          "SI=F",
    "Natural Gas":     "NG=F",
}

CURRENCIES = {
    "USD/INR":  "INR=X",
    "EUR/USD":  "EURUSD=X",
    "USD/JPY":  "JPY=X",
    "GBP/USD":  "GBPUSD=X",
}

DEFENSE_STOCKS = {
    "HAL (India)": "HAL.NS",
    "BEL (India)": "BEL.NS",
    "L&T (India)": "LT.NS",
}

ALL_TICKERS = {**INDICES, **COMMODITIES, **CURRENCIES, **DEFENSE_STOCKS}

ASSET_CATEGORIES = {
    "Indices":        list(INDICES.keys()),
    "Commodities":    list(COMMODITIES.keys()),
    "Currencies":     list(CURRENCIES.keys()),
    "Defense Stocks": list(DEFENSE_STOCKS.keys()),
}

# ─────────────────────────────────────────────
# GEOPOLITICAL EVENT ANNOTATIONS
# ─────────────────────────────────────────────
GEO_EVENTS = [
    {"date": "2022-02-24", "label": "🔴 Russia invades Ukraine",            "detail": "Commodity surge, risk-off selloff"},
    {"date": "2022-03-04", "label": "🔥 Zaporizhzhia nuclear plant attack", "detail": "Energy fears spike, safe havens rally"},
    {"date": "2022-03-16", "label": "📉 Fed hikes rates 25bps",             "detail": "Risk assets under pressure"},
    {"date": "2022-06-15", "label": "📈 Fed hikes 75bps",                   "detail": "Largest hike since 1994"},
    {"date": "2022-09-30", "label": "💥 Nord Stream sabotage",              "detail": "European energy crisis deepens"},
    {"date": "2022-10-08", "label": "🌉 Crimea bridge explosion",           "detail": "War escalation, defense stocks rally"},
    {"date": "2023-01-11", "label": "🤖 ChatGPT 100M users",               "detail": "AI/Tech sector mega rally begins"},
    {"date": "2023-03-10", "label": "🏦 SVB Bank collapse",                 "detail": "Banking panic, global contagion fears"},
    {"date": "2023-10-07", "label": "⚔️ Hamas attacks Israel",              "detail": "Oil spike, defense rally, tourism crash"},
    {"date": "2023-11-15", "label": "🇨🇳 US-China summit",                  "detail": "Trade tensions ease briefly"},
    {"date": "2024-01-15", "label": "🚢 Houthi Red Sea attacks",            "detail": "Shipping costs surge, supply chain fears"},
    {"date": "2024-04-01", "label": "🇮🇷 Iran strikes Israel",              "detail": "Middle East escalation, oil spikes"},
    {"date": "2024-11-05", "label": "🗳️ Trump wins US election",           "detail": "Dollar surge, tariff fears, volatility"},
    {"date": "2025-01-20", "label": "🏛️ Trump inauguration",               "detail": "Trade war rhetoric intensifies"},
    {"date": "2025-03-01", "label": "📦 US tariffs on Canada/Mexico",       "detail": "Trade war escalation, global selloff"},
]

# ─────────────────────────────────────────────
# COUNTRY RISK DATA (map)
# ─────────────────────────────────────────────
COUNTRY_RISK = [
    {"country": "Russia",        "lat": 61.5,  "lon": 105.3, "risk": "high",   "event": "War / Sanctions",          "severity": 10, "assets": "Oil, Gas, Wheat, Defense",  "reason": "Ongoing Ukraine war, sweeping Western sanctions on SWIFT, oil, technology"},
    {"country": "Ukraine",       "lat": 48.4,  "lon": 31.2,  "risk": "high",   "event": "Active War Zone",          "severity": 10, "assets": "Wheat, Corn, Defense",      "reason": "Active military conflict, infrastructure destruction, grain export disruption"},
    {"country": "Israel",        "lat": 31.0,  "lon": 35.2,  "risk": "high",   "event": "Gaza War / Iran Strikes",  "severity": 9,  "assets": "Oil, Defense, Tourism",     "reason": "Gaza conflict, Iran missile attacks, regional escalation risk"},
    {"country": "Iran",          "lat": 32.4,  "lon": 53.7,  "risk": "high",   "event": "Proxy War / Sanctions",    "severity": 8,  "assets": "Oil, Gas, USD",             "reason": "Proxy attacks on Israel, nuclear program, oil sanctions"},
    {"country": "China",         "lat": 35.9,  "lon": 104.2, "risk": "medium", "event": "Taiwan Tensions / Trade",  "severity": 7,  "assets": "Tech, Supply Chain",        "reason": "Taiwan military exercises, US chip bans, trade war escalation"},
    {"country": "North Korea",   "lat": 40.3,  "lon": 127.5, "risk": "high",   "event": "Nuclear / Missiles",       "severity": 8,  "assets": "Defense, JPY, Gold",        "reason": "Ballistic missile tests near Japan, nuclear weapons advancement"},
    {"country": "Yemen",         "lat": 15.6,  "lon": 48.5,  "risk": "high",   "event": "Houthi Red Sea Attacks",   "severity": 8,  "assets": "Shipping, Oil, Retail",     "reason": "Houthi attacks on commercial vessels, Suez Canal rerouting costs"},
    {"country": "Taiwan",        "lat": 23.7,  "lon": 121.0, "risk": "medium", "event": "China Military Pressure",  "severity": 7,  "assets": "Semiconductors, Tech",      "reason": "PLA military exercises, chip supply chain risk, US-China flashpoint"},
    {"country": "United States", "lat": 37.1,  "lon": -95.7, "risk": "medium", "event": "Tariffs / Fed Policy",     "severity": 6,  "assets": "All markets, USD",          "reason": "Aggressive tariff policy, Fed rate decisions affecting global capital flows"},
    {"country": "Saudi Arabia",  "lat": 23.9,  "lon": 45.1,  "risk": "medium", "event": "OPEC+ Oil Cuts",           "severity": 6,  "assets": "Oil, Gas, Energy",          "reason": "OPEC+ production cuts driving oil price volatility and inflation globally"},
    {"country": "Pakistan",      "lat": 30.4,  "lon": 69.3,  "risk": "medium", "event": "India-Pakistan Tensions",  "severity": 5,  "assets": "INR, Defense, India mkts",  "reason": "Cross-border tensions, nuclear-armed neighbors, impacts Indian defense"},
    {"country": "Germany",       "lat": 51.2,  "lon": 10.4,  "risk": "medium", "event": "Energy Crisis / Recession","severity": 5,  "assets": "EUR, DAX, Gas",             "reason": "Post-Nord Stream energy crisis, industrial recession, ECB policy pressure"},
    {"country": "India",         "lat": 20.6,  "lon": 79.0,  "risk": "low",    "event": "Geopolitical Beneficiary", "severity": 3,  "assets": "NIFTY, Defense, INR",       "reason": "Defense manufacturing boom, China+1 strategy, neutral stance benefiting trade"},
    {"country": "Japan",         "lat": 36.2,  "lon": 138.3, "risk": "low",    "event": "Defense Buildup / BOJ",    "severity": 4,  "assets": "JPY, Nikkei, Defense",      "reason": "Historic defense spending increase, BOJ rate policy, yen carry trade risk"},
]

# ─────────────────────────────────────────────
# SECTOR RULES (rule-based engine)
# ─────────────────────────────────────────────
SECTOR_RULES = {
    "war":       {"Defense": +3, "Oil & Gas": +2, "Banking": -1, "Tourism": -3, "Agriculture": -2},
    "sanctions": {"Banking": -2, "Oil & Gas": -1, "Defense": +1, "Technology": -1},
    "rate_hike": {"Banking": +1, "Real Estate": -3, "Technology": -2, "Utilities": -1},
    "oil_spike": {"Oil & Gas": +3, "Aviation": -3, "Shipping": -2, "Agriculture": -1, "Defense": +1},
    "trade_war": {"Technology": -2, "Manufacturing": -2, "Agriculture": -2, "Defense": +1},
    "ai_boom":   {"Technology": +4, "Semiconductors": +3, "Banking": +1, "Manufacturing": +1},
    "default":   {"Defense": 0, "Oil & Gas": 0, "Banking": 0, "Tourism": 0, "Technology": 0},
}

SECTORS = ["Defense", "Oil & Gas", "Banking", "Tourism", "Technology", "Agriculture", "Shipping", "Manufacturing"]

SECTOR_ICONS = {
    "Defense":       "⚔️",
    "Oil & Gas":     "🔥",
    "Banking":       "🏦",
    "Tourism":       "✈️",
    "Technology":    "💻",
    "Agriculture":   "🌾",
    "Shipping":      "🚢",
    "Manufacturing": "🏭",
}

# ─────────────────────────────────────────────
# UI / REFRESH
# ─────────────────────────────────────────────
REFRESH_INTERVAL = 120   # seconds

COLORS = {
    "bg_dark":       "#0A0E1A",
    "bg_card":       "#111827",
    "bg_card2":      "#1A2236",
    "accent_red":    "#FF3B5B",
    "accent_green":  "#00E5A0",
    "accent_yellow": "#FFD700",
    "accent_blue":   "#3B82F6",
    "accent_orange": "#FF8C42",
    "text_primary":  "#F0F4FF",
    "text_secondary":"#8B99B5",
    "border":        "#1E2D45",
}
