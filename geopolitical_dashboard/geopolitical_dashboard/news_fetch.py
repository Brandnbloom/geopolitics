"""
news_fetch.py - Live news via NewsAPI.org + improved rule-based insight engine.
Insights require MULTIPLE keyword matches to avoid false positives.
"""

import requests
import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import os
from config import NEWSAPI_KEY

# ─────────────────────────────────────────────────────────────────────────────
# NEWSAPI SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

_NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

_QUERY = (
    "war OR sanctions OR geopolitical OR \"oil price\" OR \"interest rate\" "
    "OR NATO OR Ukraine OR Russia OR China OR Taiwan OR tariff OR \"defense spending\" "
    "OR OPEC OR \"Red Sea\" OR Houthi OR \"artificial intelligence\" OR Fed OR RBI"
)


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVED RULE ENGINE
# Each rule requires:
#   - primary_keywords: ALL must appear (core topic identifiers)
#   - boost_keywords:   additional context words (at least 1 must match)
#   - exclude_keywords: if any of these appear → skip this rule entirely
# ─────────────────────────────────────────────────────────────────────────────

_RULES = [
    {
        "id": "ukraine_war",
        "primary": ["ukraine", "russia"],
        "boost":   ["war", "invasion", "attack", "missile", "troops", "kyiv", "offensive",
                    "drone", "shelling", "ceasefire", "zelenskyy", "putin", "nato", "frontline"],
        "exclude": ["chess", "sport", "tournament", "culture", "film"],
        "min_boost": 1,
        "insight": (
            "Russia-Ukraine war update. Direct market impacts: European energy prices "
            "(Oil and Gas higher on supply fears), safe havens rally (Gold, USD/JPY), "
            "Indian and global defense stocks (HAL, BEL) see procurement demand. "
            "Watch EUR/USD — European growth risk rises with escalation."
        ),
        "sectors":   ["Defense", "Oil & Gas", "Banking"],
        "sentiment": "risk",
    },
    {
        "id": "middle_east_conflict",
        "primary": ["israel", "hamas"],
        "boost":   ["gaza", "war", "attack", "strike", "rocket", "ceasefire", "rafah",
                    "west bank", "idf", "hezbollah", "iran", "hostage"],
        "exclude": ["sport", "football", "election", "economy only"],
        "min_boost": 1,
        "insight": (
            "Middle East conflict escalation. Key market risks: Oil spike if Strait of Hormuz "
            "threatened (+10-15% on Brent), regional tourism collapses, global defense "
            "procurement accelerates. Gold and USD benefit as safe havens."
        ),
        "sectors":   ["Defense", "Oil & Gas", "Tourism"],
        "sentiment": "risk",
    },
    {
        "id": "iran_tensions",
        "primary": ["iran"],
        "boost":   ["nuclear", "sanctions", "strike", "missile", "attack", "israel",
                    "us forces", "hormuz", "proxy", "enrichment", "iaea"],
        "exclude": ["iran economy", "iranian culture", "tourism"],
        "min_boost": 2,
        "insight": (
            "Iran geopolitical risk. Nuclear escalation or Strait of Hormuz tensions "
            "would spike Brent crude sharply. USD strengthens, Oil majors benefit, "
            "Asian importers (India, Japan) face cost pressures."
        ),
        "sectors":   ["Oil & Gas", "Defense"],
        "sentiment": "risk",
    },
    {
        "id": "china_taiwan",
        "primary": ["china", "taiwan"],
        "boost":   ["military", "pla", "strait", "invasion", "tension", "exercises",
                    "semiconductor", "chip", "blockade", "decoupling", "beijing"],
        "exclude": ["trade deal", "tourism", "culture", "business only"],
        "min_boost": 2,
        "insight": (
            "China-Taiwan geopolitical tension. Semiconductor supply chain most at risk — "
            "TSMC produces 90% of advanced chips. Tech stocks volatile. Hang Seng "
            "pressured. Defense procurement globally accelerates on escalation signals."
        ),
        "sectors":   ["Technology", "Defense", "Semiconductors"],
        "sentiment": "risk",
    },
    {
        "id": "houthi_shipping",
        "primary": ["houthi"],
        "boost":   ["red sea", "ship", "attack", "suez", "cargo", "tanker",
                    "missile", "drone", "maritime", "vessel"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "Houthi attacks disrupting Red Sea shipping lanes. Suez Canal rerouting adds "
            "~14 days and 40% cost per voyage. Retail and consumer goods face input cost "
            "inflation. Oil tanker rates spike. Stagflation risk for import-heavy nations."
        ),
        "sectors":   ["Shipping", "Oil & Gas", "Retail"],
        "sentiment": "risk",
    },
    {
        "id": "red_sea_shipping",
        "primary": ["red sea"],
        "boost":   ["shipping", "suez", "cargo", "tanker", "vessel", "attack",
                    "route", "diversion", "freight", "cost"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "Red Sea shipping disruption ongoing. Global freight costs elevated — "
            "impacts supply chains for electronics, retail, and energy. "
            "Companies with lean inventories most vulnerable to delays."
        ),
        "sectors":   ["Shipping", "Manufacturing", "Retail"],
        "sentiment": "risk",
    },
    {
        "id": "fed_policy",
        "primary": ["federal reserve", "fed"],
        "boost":   ["rate", "hike", "cut", "interest", "powell", "fomc",
                    "inflation", "taper", "quantitative", "basis points", "bps"],
        "exclude": ["federal reserve bank robbery", "fed up"],
        "min_boost": 1,
        "insight": (
            "US Federal Reserve policy signal. Rate hikes pressure equities and real estate; "
            "emerging market currencies (INR, JPY) weaken vs USD. "
            "Rate cuts fuel risk-on rallies — watch S&P 500, NIFTY 50, and bond yields closely."
        ),
        "sectors":   ["Banking", "Real Estate", "Currencies"],
        "sentiment": "mixed",
    },
    {
        "id": "rbi_policy",
        "primary": ["reserve bank of india", "rbi"],
        "boost":   ["rate", "repo", "inflation", "rupee", "monetary policy",
                    "das", "governor", "liquidity", "cpi"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "RBI monetary policy development. Direct impact on INR exchange rate, "
            "NIFTY 50 valuations, and Indian banking sector margins. "
            "Rate decisions drive foreign institutional investor flows in/out of India."
        ),
        "sectors":   ["Banking", "Currencies"],
        "sentiment": "mixed",
    },
    {
        "id": "oil_opec",
        "primary": ["opec"],
        "boost":   ["oil", "production", "cut", "quota", "barrel", "output",
                    "crude", "supply", "saudi", "energy"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "OPEC+ production decision directly moves oil prices. Supply cuts support "
            "Brent above target levels — positive for oil majors, negative for aviation, "
            "shipping, and agriculture. India as net oil importer faces currency pressure."
        ),
        "sectors":   ["Oil & Gas", "Aviation", "Shipping"],
        "sentiment": "risk",
    },
    {
        "id": "oil_price_move",
        "primary": ["oil price", "crude oil", "brent crude"],
        "boost":   ["rise", "fall", "spike", "drop", "surge", "slump",
                    "barrel", "wti", "energy market"],
        "exclude": ["cooking oil", "olive oil", "palm oil", "vegetable oil"],
        "min_boost": 1,
        "insight": (
            "Oil price movement with direct macro implications. Rising oil inflates "
            "costs globally — airlines, shipping, and manufacturing margins compress. "
            "Falling oil eases inflation pressure but signals weaker global demand."
        ),
        "sectors":   ["Oil & Gas", "Aviation", "Shipping"],
        "sentiment": "mixed",
    },
    {
        "id": "natural_gas",
        "primary": ["natural gas", "lng"],
        "boost":   ["supply", "price", "europe", "pipeline", "export",
                    "storage", "winter", "shortage", "ttf"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "Natural gas supply/price development. European energy markets most sensitive — "
            "DAX and EUR under pressure when supply is tight. "
            "LNG exporters (US, Qatar, Australia) directly benefit from elevated prices."
        ),
        "sectors":   ["Oil & Gas", "Manufacturing"],
        "sentiment": "mixed",
    },
    {
        "id": "us_tariffs",
        "primary": ["tariff"],
        "boost":   ["trump", "china", "trade war", "import", "duty", "retaliation",
                    "trade policy", "protectionism", "wto", "customs"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "US tariff/trade war escalation. Manufacturing and Agriculture supply chains "
            "most disrupted. USD typically strengthens short-term; affected nation currencies "
            "weaken. Multinational earnings compress on rising input costs and retaliation risk."
        ),
        "sectors":   ["Manufacturing", "Agriculture", "Currencies"],
        "sentiment": "risk",
    },
    {
        "id": "sanctions",
        "primary": ["sanction"],
        "boost":   ["russia", "iran", "china", "north korea", "swift", "ban",
                    "embargo", "export control", "asset freeze", "blacklist"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "New sanctions package announced. Targeted nation's currency and equity "
            "market face immediate pressure. Global banking sector faces compliance cost "
            "increases. Supply chains involving sanctioned entities restructure rapidly."
        ),
        "sectors":   ["Banking", "Oil & Gas", "Technology"],
        "sentiment": "risk",
    },
    {
        "id": "ai_tech",
        "primary": ["artificial intelligence", "ai model", "chatgpt", "openai", "nvidia"],
        "boost":   ["launch", "investment", "chip", "llm", "revenue", "earnings",
                    "data center", "compute", "model", "funding", "valuation"],
        "exclude": ["ai regulation ban", "ai risk warning only"],
        "min_boost": 1,
        "insight": (
            "AI sector development with market implications. Semiconductor and cloud "
            "infrastructure stocks rally on adoption signals. Productivity gains are "
            "broadly positive for equities. Energy demand from data centers supports "
            "natural gas prices long-term."
        ),
        "sectors":   ["Technology", "Semiconductors"],
        "sentiment": "opportunity",
    },
    {
        "id": "india_defense",
        "primary": ["india"],
        "boost":   ["defense", "hal", "bel", "tejas", "brahmos", "drdo",
                    "military", "arms", "weapon", "fighter jet", "missile", "navy"],
        "exclude": [],
        "min_boost": 2,
        "insight": (
            "Indian defense sector development. HAL, BEL, and L&T are direct beneficiaries "
            "of India's defense indigenization push. Multi-year procurement contracts provide "
            "strong earnings visibility. Budget increases are structural, not cyclical."
        ),
        "sectors":   ["Defense", "Manufacturing"],
        "sentiment": "opportunity",
    },
    {
        "id": "nato_defense",
        "primary": ["nato"],
        "boost":   ["defense", "spending", "military", "budget", "article 5",
                    "member", "alliance", "troops", "exercise", "russia"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "NATO defense spending signal. Member nations increasing military budgets "
            "drive multi-year procurement cycles for defense manufacturers. "
            "European defense stocks and Indian defense exporters (HAL, BEL) benefit."
        ),
        "sectors":   ["Defense"],
        "sentiment": "opportunity",
    },
    {
        "id": "banking_crisis",
        "primary": ["bank"],
        "boost":   ["collapse", "crisis", "failure", "contagion", "bailout",
                    "liquidity", "run", "default", "insolvency", "writedown"],
        "exclude": ["central bank rate", "bank earnings beat", "bank opens branch"],
        "min_boost": 1,
        "insight": (
            "Banking sector stress event. Contagion risk elevates market volatility and "
            "safe-haven demand (Gold, USD, Treasuries). Broad equity selloff likely "
            "short-term. Watch interbank lending rates and central bank emergency signals."
        ),
        "sectors":   ["Banking", "Real Estate"],
        "sentiment": "risk",
    },
    {
        "id": "inflation_macro",
        "primary": ["inflation"],
        "boost":   ["cpi", "consumer price", "core inflation", "pce",
                    "rate hike", "central bank", "stagflation", "price pressure"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "Inflation data with direct policy implications. High inflation forces central "
            "banks to maintain restrictive rates longer — negative for equities and real "
            "estate. Commodities and TIPS act as hedges. Emerging market currencies most vulnerable."
        ),
        "sectors":   ["Banking", "Real Estate"],
        "sentiment": "risk",
    },
    {
        "id": "gold_precious",
        "primary": ["gold"],
        "boost":   ["central bank", "price", "record", "rally", "safe haven",
                    "de-dollarization", "reserve", "buying", "silver", "precious metal"],
        "exclude": ["gold medal", "golden globe", "gold mine accident"],
        "min_boost": 1,
        "insight": (
            "Gold/precious metals price catalyst. Central bank reserve diversification "
            "away from USD is a structural multi-year tailwind. Geopolitical uncertainty "
            "drives short-term safe-haven demand. Watch real yields — inverse correlation is strong."
        ),
        "sectors":   ["Commodities", "Currencies"],
        "sentiment": "opportunity",
    },
    {
        "id": "north_korea",
        "primary": ["north korea"],
        "boost":   ["missile", "nuclear", "test", "icbm", "kim", "weapon",
                    "launch", "provocation", "japan", "south korea"],
        "exclude": [],
        "min_boost": 1,
        "insight": (
            "North Korea provocation. JPY and Gold typically rally as safe havens. "
            "Japanese and South Korean defense stocks see increased procurement expectations. "
            "Market impact usually short-lived unless escalation involves direct confrontation."
        ),
        "sectors":   ["Defense"],
        "sentiment": "risk",
    },
]

_FALLBACK_INSIGHT = {
    "insight": (
        "General geopolitical or economic development. "
        "Monitor for downstream impacts on currency, commodity, and equity markets. "
        "No strong sector-specific signal identified from this headline."
    ),
    "sectors":   ["Markets"],
    "sentiment": "mixed",
}


def _score_article(text: str) -> Dict:
    """
    Score an article against all rules.
    Returns the best matching rule's insight, or fallback if no rule qualifies.
    """
    text_lower = text.lower()

    best_rule  = None
    best_score = 0

    for rule in _RULES:
        # All primary keywords must be present
        if not all(kw in text_lower for kw in rule["primary"]):
            continue

        # None of the exclude keywords should be present
        if any(kw in text_lower for kw in rule.get("exclude", [])):
            continue

        # Count how many boost keywords are present
        boost_hits = sum(1 for kw in rule["boost"] if kw in text_lower)

        # Must meet minimum boost threshold
        if boost_hits < rule.get("min_boost", 1):
            continue

        # Score = number of primary matches * 10 + boost hits
        score = len(rule["primary"]) * 10 + boost_hits

        if score > best_score:
            best_score = score
            best_rule  = rule

    if best_rule:
        return {
            "insight":   best_rule["insight"],
            "sectors":   best_rule["sectors"],
            "sentiment": best_rule["sentiment"],
        }

    return _FALLBACK_INSIGHT


def _get_insight(title: str, description: str) -> Dict:
    """Combine title + description for matching, title weighted more."""
    # Title gets repeated 3x to give it more weight in matching
    combined = f"{title} {title} {title} {description or ''}".lower()
    return _score_article(combined)


# ─────────────────────────────────────────────────────────────────────────────
# LIVE FETCH
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def fetch_news(max_articles: int = 30) -> List[Dict]:
    """
    Fetch live geopolitical news from NewsAPI.org.
    Key is read from config.NEWSAPI_KEY or environment variable.
    """
    api_key = os.environ.get("NEWSAPI_KEY", NEWSAPI_KEY)

    if not api_key or api_key == "YOUR_NEWSAPI_KEY_HERE":
        st.error(
            "NewsAPI key not set. "
            "Open config.py and replace YOUR_NEWSAPI_KEY_HERE with your key from newsapi.org. "
            "Free tier: 100 requests/day."
        )
        return []

    from_date = (datetime.now(timezone.utc) - timedelta(days=29)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "q":        _QUERY,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": min(max_articles, 100),
        "from":     from_date,
        "apiKey":   api_key,
    }

    try:
        resp = requests.get(_NEWSAPI_ENDPOINT, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        st.error("Network error — could not reach NewsAPI. Check your internet connection.")
        return []
    except requests.exceptions.Timeout:
        st.error("NewsAPI request timed out. Try again shortly.")
        return []

    if resp.status_code == 401:
        st.error("NewsAPI: Invalid API key. Check config.py NEWSAPI_KEY.")
        return []
    if resp.status_code == 429:
        st.warning("NewsAPI rate limit reached. Free tier allows 100 requests/day. Retrying on next refresh.")
        return []
    if resp.status_code != 200:
        st.error(f"NewsAPI returned HTTP {resp.status_code}: {resp.text[:200]}")
        return []

    data = resp.json()
    if data.get("status") != "ok":
        st.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
        return []

    raw_articles = data.get("articles", [])
    if not raw_articles:
        st.info("NewsAPI returned 0 articles for the current query window.")
        return []

    enriched = []
    for art in raw_articles[:max_articles]:
        title = art.get("title") or ""
        desc  = art.get("description") or ""

        if not title or title == "[Removed]":
            continue

        insight_data = _get_insight(title, desc)

        pub_raw = art.get("publishedAt", "")
        try:
            pub_dt  = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
            pub_str = pub_dt.strftime("%b %d, %Y  %H:%M UTC")
        except Exception:
            pub_str = pub_raw[:16] if pub_raw else "Unknown"

        source = art.get("source", {})
        enriched.append({
            "title":         title,
            "description":   desc,
            "source":        source.get("name", "Unknown") if isinstance(source, dict) else str(source),
            "published":     pub_raw,
            "published_str": pub_str,
            "url":           art.get("url", "#"),
            "image":         art.get("urlToImage", ""),
            "insight":       insight_data["insight"],
            "sectors":       insight_data["sectors"],
            "sentiment":     insight_data["sentiment"],
        })

    enriched.sort(key=lambda x: x["published"], reverse=True)
    return enriched
