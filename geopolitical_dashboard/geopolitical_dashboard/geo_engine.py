"""
geo_engine.py - Rule-based geopolitical risk analysis engine
"""

from typing import Dict, List, Tuple
from config import COUNTRY_RISK, GEO_EVENTS, SECTOR_RULES, SECTORS, SECTOR_ICONS


def get_country_risk_summary() -> List[Dict]:
    """Return enriched country risk data with color coding."""
    enriched = []
    for country in COUNTRY_RISK:
        risk_level = country["risk"]
        color = {
            "high":   [255, 59, 91],    # red
            "medium": [255, 140, 66],   # orange
            "low":    [0, 229, 160],    # green
        }.get(risk_level, [200, 200, 200])

        radius = {
            "high":   country["severity"] * 80000,
            "medium": country["severity"] * 60000,
            "low":    country["severity"] * 40000,
        }.get(risk_level, 300000)

        enriched.append({
            **country,
            "color":       color,
            "radius":      radius,
            "risk_label":  risk_level.upper(),
            "tooltip":     (
                f"{country['country']} | Risk: {risk_level.upper()}\n"
                f"Event: {country['event']}\n"
                f"Why Risky: {country['reason']}\n"
                f"Affected Assets: {country['assets']}"
            ),
        })
    return enriched


def get_global_risk_score() -> Tuple[float, str]:
    """Compute a composite global risk score (0-10)."""
    total = sum(c["severity"] for c in COUNTRY_RISK)
    max_possible = len(COUNTRY_RISK) * 10
    score = (total / max_possible) * 10
    high_count = sum(1 for c in COUNTRY_RISK if c["risk"] == "high")
    label = "CRITICAL" if score > 7 else "HIGH" if score > 5 else "ELEVATED" if score > 3 else "MODERATE"
    return round(score, 1), label


def classify_event(event_label: str) -> str:
    """Classify a geopolitical event into a category."""
    label = event_label.lower()
    if any(k in label for k in ["war", "attack", "invade", "missile", "nuclear", "explosion", "crimea", "houthi"]):
        return "war"
    elif any(k in label for k in ["sanction", "ban", "embargo"]):
        return "sanctions"
    elif any(k in label for k in ["rate", "fed", "hike", "taper"]):
        return "rate_hike"
    elif any(k in label for k in ["oil", "opec", "pipeline", "brent", "energy"]):
        return "oil_spike"
    elif any(k in label for k in ["tariff", "trade"]):
        return "trade_war"
    elif any(k in label for k in ["ai", "chatgpt", "gpt", "nvidia"]):
        return "ai_boom"
    elif any(k in label for k in ["bank", "svb", "collapse", "credit"]):
        return "financial"
    else:
        return "default"


def get_event_sector_impact(event_label: str) -> Dict[str, int]:
    """Return sector impact scores for a given event."""
    category = classify_event(event_label)
    return SECTOR_RULES.get(category, SECTOR_RULES["default"])


def get_all_event_impacts() -> List[Dict]:
    """Return all geo events with their sector impacts."""
    results = []
    for event in GEO_EVENTS:
        impacts = get_event_sector_impact(event["label"])
        category = classify_event(event["label"])
        results.append({
            "date":     event["date"],
            "label":    event["label"],
            "detail":   event["detail"],
            "category": category,
            "impacts":  impacts,
        })
    return results


def generate_market_insight(asset_name: str, day_change: float, war_change: float) -> str:
    """Generate a rule-based market insight for any asset."""
    direction = "📈 up" if day_change > 0 else "📉 down"
    magnitude = "sharply" if abs(day_change) > 2 else "moderately" if abs(day_change) > 0.5 else "slightly"

    if "Oil" in asset_name or "Crude" in asset_name or "Brent" in asset_name or "Gas" in asset_name:
        return f"Energy {direction} {magnitude} ({day_change:+.1f}%). War escalation and OPEC+ supply decisions are primary drivers. Since Feb 2022: {war_change:+.1f}%."
    elif "Gold" in asset_name or "Silver" in asset_name:
        return f"Precious metals {direction} {magnitude} ({day_change:+.1f}%). Safe-haven demand driven by geopolitical uncertainty. Central bank buying accelerating. Since Feb 2022: {war_change:+.1f}%."
    elif "S&P" in asset_name or "Nasdaq" in asset_name or "Dow" in asset_name:
        return f"US market {direction} {magnitude} ({day_change:+.1f}%). Fed policy, AI earnings, and global risk-off/on sentiment key drivers. Since Feb 2022: {war_change:+.1f}%."
    elif "HAL" in asset_name or "BEL" in asset_name or "L&T" in asset_name:
        return f"India defense stock {direction} {magnitude} ({day_change:+.1f}%). Defense budget expansion and 'Make in India' tailwinds. War-driven procurement surge. Since Feb 2022: {war_change:+.1f}%."
    elif "INR" in asset_name or "JPY" in asset_name or "EUR" in asset_name or "GBP" in asset_name:
        return f"Currency {direction} {magnitude} ({day_change:+.1f}%). Central bank divergence, geopolitical risk flows, and commodity prices driving FX. Since Feb 2022: {war_change:+.1f}%."
    elif "Nikkei" in asset_name or "DAX" in asset_name or "FTSE" in asset_name:
        return f"Global index {direction} {magnitude} ({day_change:+.1f}%). Regional geopolitical exposure (Europe: energy crisis; Japan: BOJ policy) key risk. Since Feb 2022: {war_change:+.1f}%."
    elif "NIFTY" in asset_name or "Hang Seng" in asset_name:
        return f"Asian index {direction} {magnitude} ({day_change:+.1f}%). FII flows, China-US tensions, and domestic macro critical. Since Feb 2022: {war_change:+.1f}%."
    else:
        return f"Asset {direction} {magnitude} ({day_change:+.1f}%) today. Monitor geopolitical triggers and macro catalysts for sustained moves. Since Feb 2022: {war_change:+.1f}%."


def get_kpi_metrics(latest_prices_df) -> List[Dict]:
    """Extract top-level KPI metrics for the dashboard header."""
    kpis = []

    try:
        oil = latest_prices_df[latest_prices_df["Asset"] == "Crude Oil (WTI)"].iloc[0]
        kpis.append({"label": "🔥 WTI Crude", "value": f"${oil['Price']:.1f}", "change": oil["Day %"], "unit": "bbl"})
    except Exception:
        kpis.append({"label": "🔥 WTI Crude", "value": "N/A", "change": 0, "unit": "bbl"})

    try:
        gold = latest_prices_df[latest_prices_df["Asset"] == "Gold"].iloc[0]
        kpis.append({"label": "🥇 Gold", "value": f"${gold['Price']:.0f}", "change": gold["Day %"], "unit": "oz"})
    except Exception:
        kpis.append({"label": "🥇 Gold", "value": "N/A", "change": 0, "unit": "oz"})

    try:
        sp = latest_prices_df[latest_prices_df["Asset"] == "S&P 500"].iloc[0]
        kpis.append({"label": "📈 S&P 500", "value": f"{sp['Price']:,.0f}", "change": sp["Day %"], "unit": "pts"})
    except Exception:
        kpis.append({"label": "📈 S&P 500", "value": "N/A", "change": 0, "unit": "pts"})

    try:
        inr = latest_prices_df[latest_prices_df["Asset"] == "USD/INR"].iloc[0]
        kpis.append({"label": "🇮🇳 USD/INR", "value": f"₹{inr['Price']:.2f}", "change": inr["Day %"], "unit": ""})
    except Exception:
        kpis.append({"label": "🇮🇳 USD/INR", "value": "N/A", "change": 0, "unit": ""})

    try:
        hal = latest_prices_df[latest_prices_df["Asset"] == "HAL (India)"].iloc[0]
        kpis.append({"label": "⚔️ HAL India", "value": f"₹{hal['Price']:,.0f}", "change": hal["Day %"], "unit": ""})
    except Exception:
        kpis.append({"label": "⚔️ HAL India", "value": "N/A", "change": 0, "unit": ""})

    risk_score, risk_label = get_global_risk_score()
    kpis.append({"label": "🌍 Global Risk", "value": f"{risk_score}/10", "change": None, "unit": risk_label})

    return kpis
