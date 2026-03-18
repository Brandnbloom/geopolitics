"""
news_fetch.py - Live news via NewsAPI.org + automated rule-based insight engine.
API key is read from config.NEWSAPI_KEY. No mock/fallback data.
"""

import requests
import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from config import NEWSAPI_KEY

# ─────────────────────────────────────────────────────────────────────────────
# NEWSAPI QUERY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

_NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

# Broad geopolitical + market query — covers war, trade, commodities, central banks, AI
_QUERY = (
    "war OR sanctions OR geopolitical OR \"oil price\" OR \"interest rate\" "
    "OR NATO OR Ukraine OR Russia OR China OR Taiwan OR tariff OR \"defense spending\" "
    "OR OPEC OR \"Red Sea\" OR Houthi OR \"artificial intelligence\" OR Fed OR RBI"
)

# High-signal English-language sources
_SOURCES = ",".join([
    "reuters", "bloomberg", "the-wall-street-journal", "financial-times",
    "associated-press", "bbc-news", "cnbc", "the-economist",
])


# ─────────────────────────────────────────────────────────────────────────────
# RULE-BASED INSIGHT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

_INSIGHT_RULES: List[Dict] = [
    {
        "keywords": ["russia", "ukraine", "invasion", "offensive", "kyiv", "kharkiv",
                     "zaporizhzhia", "crimea", "donbas", "zelenskyy", "putin"],
        "insight":   "⚔️ Russia-Ukraine war update. Direct impact: European energy prices (Oil ↑, Gas ↑), "
                     "safe havens (Gold ↑, USD/JPY ↑), Indian/global defense stocks (HAL, BEL). "
                     "Watch EUR/USD for European growth risk.",
        "sectors":   ["Defense", "Oil & Gas", "Banking"],
        "sentiment": "risk",
    },
    {
        "keywords": ["sanction", "swift", "embargo", "export control", "blacklist",
                     "restricted entity", "asset freeze"],
        "insight":   "🚫 Sanctions tightening. Impacts: targeted currency collapses, "
                     "global banking compliance costs rise, supply chains fragment. "
                     "USD strengthens as safe-haven flows accelerate.",
        "sectors":   ["Banking", "Technology", "Oil & Gas"],
        "sentiment": "risk",
    },
    {
        "keywords": ["federal reserve", "fed rate", "interest rate", "rate hike", "rate cut",
                     "powell", "fomc", "quantitative tightening", "taper"],
        "insight":   "🏦 Fed policy signal. Rate hikes pressure equities and real estate; "
                     "emerging market currencies (INR, JPY) weaken vs USD. "
                     "Rate cuts fuel risk-on rallies — watch S&P 500, NIFTY, and bond yields.",
        "sectors":   ["Banking", "Real Estate", "Currencies"],
        "sentiment": "mixed",
    },
    {
        "keywords": ["rbi", "reserve bank of india", "india rate", "repo rate", "shaktikanta"],
        "insight":   "🇮🇳 RBI policy move. Direct impact on INR, NIFTY 50, and Indian banking sector. "
                     "Rate decisions drive FII inflows/outflows and rupee volatility.",
        "sectors":   ["Banking", "INR"],
        "sentiment": "mixed",
    },
    {
        "keywords": ["oil price", "crude", "brent", "opec", "petroleum", "energy price",
                     "barrel", "refinery", "gasoline"],
        "insight":   "🔥 Oil/energy price catalyst. Inflation implications globally. "
                     "Aviation & Shipping margins compress. Oil majors benefit. "
                     "India is a net importer — INR and CAD sensitive.",
        "sectors":   ["Oil & Gas", "Aviation", "Shipping"],
        "sentiment": "risk",
    },
    {
        "keywords": ["natural gas", "lng", "pipeline", "nord stream", "gas supply",
                     "european energy", "ttf"],
        "insight":   "⚡ Natural gas supply event. European energy crisis amplified — "
                     "DAX and EUR under pressure. LNG exporters (US, Qatar) benefit. "
                     "Winter demand seasonality compounds impact.",
        "sectors":   ["Oil & Gas", "Manufacturing"],
        "sentiment": "risk",
    },
    {
        "keywords": ["china", "taiwan", "pla", "strait", "beijing", "xi jinping",
                     "chip ban", "semiconductor", "decoupling"],
        "insight":   "🇨🇳 China/Taiwan geopolitical risk. Semiconductor supply chain most exposed. "
                     "Tech stocks face volatility. Hang Seng pressured on escalation. "
                     "Defense procurement accelerates globally.",
        "sectors":   ["Technology", "Defense", "Semiconductors"],
        "sentiment": "risk",
    },
    {
        "keywords": ["houthi", "red sea", "suez canal", "shipping lane", "cargo ship",
                     "container", "freight rate", "maritime"],
        "insight":   "🚢 Shipping lane disruption. Suez rerouting adds ~14 days and 40% cost. "
                     "Retail and consumer goods face input cost inflation. "
                     "Oil tanker rates spike. Stagflation risk for importing nations.",
        "sectors":   ["Shipping", "Retail", "Manufacturing"],
        "sentiment": "risk",
    },
    {
        "keywords": ["israel", "hamas", "gaza", "iran", "hezbollah", "middle east",
                     "strait of hormuz", "persian gulf"],
        "insight":   "⚔️ Middle East conflict escalation. Hormuz Strait risk would spike Brent +15%. "
                     "Tourism in region collapses. Global defense procurement surges. "
                     "Gold and USD benefit as safe havens.",
        "sectors":   ["Defense", "Oil & Gas", "Tourism"],
        "sentiment": "risk",
    },
    {
        "keywords": ["tariff", "trade war", "protectionism", "import duty", "trade deal",
                     "wto", "customs"],
        "insight":   "📦 Trade war escalation. Manufacturing and Agriculture supply chains disrupted. "
                     "USD typically strengthens; affected currencies weaken. "
                     "Multinational earnings compress on re-shoring costs.",
        "sectors":   ["Manufacturing", "Agriculture", "Currencies"],
        "sentiment": "risk",
    },
    {
        "keywords": ["artificial intelligence", "ai model", "chatgpt", "openai", "nvidia",
                     "llm", "large language model", "generative ai", "machine learning"],
        "insight":   "🤖 AI sector development. Tech and semiconductor stocks rally on adoption signals. "
                     "Productivity gains broadly positive for equities. "
                     "Energy demand from data centers supports natural gas prices.",
        "sectors":   ["Technology", "Semiconductors"],
        "sentiment": "opportunity",
    },
    {
        "keywords": ["nato", "defense spending", "military budget", "arms deal",
                     "hal", "bel", "tejas", "brahmos", "drdo"],
        "insight":   "⚔️ Defense sector catalyst. NATO/bilateral spending increases drive multi-year "
                     "procurement cycles. HAL, BEL, L&T are direct beneficiaries. "
                     "Long-duration contracts provide earnings visibility.",
        "sectors":   ["Defense", "Manufacturing"],
        "sentiment": "opportunity",
    },
    {
        "keywords": ["inflation", "cpi", "consumer price", "stagflation", "recession",
                     "gdp contraction", "economic slowdown"],
        "insight":   "📊 Macro risk signal. High inflation constrains central banks from cutting. "
                     "Recession risk pressures equities, especially rate-sensitive sectors. "
                     "Gold and commodities act as inflation hedges.",
        "sectors":   ["Banking", "Real Estate"],
        "sentiment": "risk",
    },
    {
        "keywords": ["gold", "silver", "safe haven", "precious metal", "central bank buying",
                     "de-dollarization", "reserve currency"],
        "insight":   "🥇 Precious metals catalyst. Central bank diversification away from USD "
                     "is a structural multi-year tailwind for Gold. "
                     "Silver benefits from industrial demand + solar panel growth.",
        "sectors":   ["Oil & Gas", "Currencies"],
        "sentiment": "opportunity",
    },
    {
        "keywords": ["bank collapse", "credit crisis", "svb", "financial contagion",
                     "liquidity crisis", "debt ceiling", "sovereign default"],
        "insight":   "🏦 Financial system stress. Contagion risk elevates VIX and safe-haven demand. "
                     "Broad equity selloff likely short-term. Watch interbank lending rates "
                     "and central bank emergency intervention signals.",
        "sectors":   ["Banking", "Real Estate"],
        "sentiment": "risk",
    },
]


def _get_insight(title: str, description: str) -> Dict:
    """Match article text against rules and return the best insight."""
    text = (title + " " + (description or "")).lower()
    for rule in _INSIGHT_RULES:
        if any(kw in text for kw in rule["keywords"]):
            return {
                "insight":   rule["insight"],
                "sectors":   rule["sectors"],
                "sentiment": rule["sentiment"],
            }
    return {
        "insight":   "📰 Geopolitical/economic development. Monitor for downstream effects on "
                     "currency, commodity, and equity markets. No direct sector match identified.",
        "sectors":   ["Markets"],
        "sentiment": "mixed",
    }


# ─────────────────────────────────────────────────────────────────────────────
# LIVE FETCH
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news(max_articles: int = 30) -> List[Dict]:
    """
    Fetch live geopolitical news from NewsAPI.org.
    Key is read from config.NEWSAPI_KEY.
    Raises a visible Streamlit error if the key is missing or invalid.
    Returns a list of enriched article dicts sorted newest-first.
    """
    if not NEWSAPI_KEY or NEWSAPI_KEY == "YOUR_NEWSAPI_KEY_HERE":
        st.error(
            "❌ **NewsAPI key not set.**  \n"
            "Open `config.py` and replace `YOUR_NEWSAPI_KEY_HERE` with your key from "
            "[newsapi.org](https://newsapi.org). Free tier: 100 requests/day."
        )
        return []

    # NewsAPI free tier only allows articles up to 1 month old
    from_date = (datetime.now(timezone.utc) - timedelta(days=29)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "q":          _QUERY,
        "language":   "en",
        "sortBy":     "publishedAt",
        "pageSize":   min(max_articles, 100),
        "from":       from_date,
        "apiKey":     NEWSAPI_KEY,
    }

    try:
        resp = requests.get(_NEWSAPI_ENDPOINT, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        st.error("❌ Network error — could not reach NewsAPI. Check your internet connection.")
        return []
    except requests.exceptions.Timeout:
        st.error("❌ NewsAPI request timed out. Try again shortly.")
        return []

    if resp.status_code == 401:
        st.error("❌ **NewsAPI: Invalid API key.** Check `config.py → NEWSAPI_KEY`.")
        return []
    if resp.status_code == 429:
        st.warning("⚠️ NewsAPI rate limit reached. Free tier allows 100 requests/day. "
                   "Dashboard will retry on next auto-refresh.")
        return []
    if resp.status_code != 200:
        st.error(f"❌ NewsAPI returned HTTP {resp.status_code}: {resp.text[:200]}")
        return []

    data = resp.json()
    if data.get("status") != "ok":
        st.error(f"❌ NewsAPI error: {data.get('message', 'Unknown error')}")
        return []

    raw_articles = data.get("articles", [])
    if not raw_articles:
        st.info("ℹ️ NewsAPI returned 0 articles for the current query window.")
        return []

    enriched = []
    for art in raw_articles[:max_articles]:
        title = art.get("title") or ""
        desc  = art.get("description") or ""
        if not title or title == "[Removed]":
            continue

        insight_data = _get_insight(title, desc)

        # Parse and normalise published timestamp
        pub_raw = art.get("publishedAt", "")
        try:
            pub_dt  = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
            pub_str = pub_dt.strftime("%b %d, %Y  %H:%M UTC")
        except Exception:
            pub_str = pub_raw[:16] if pub_raw else "Unknown"

        source = art.get("source", {})
        enriched.append({
            "title":       title,
            "description": desc,
            "source":      source.get("name", "Unknown") if isinstance(source, dict) else str(source),
            "published":   pub_raw,
            "published_str": pub_str,
            "url":         art.get("url", "#"),
            "image":       art.get("urlToImage", ""),
            "insight":     insight_data["insight"],
            "sectors":     insight_data["sectors"],
            "sentiment":   insight_data["sentiment"],
        })

    enriched.sort(key=lambda x: x["published"], reverse=True)
    return enriched
