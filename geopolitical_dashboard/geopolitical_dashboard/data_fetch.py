"""
data_fetch.py - Live market data via yfinance. No mock/synthetic data.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from config import ALL_TICKERS, WAR_START_DATE, TODAY, ASSET_CATEGORIES, COMMODITIES


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns that yfinance >= 0.2.x produces."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PRICE HISTORY
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def fetch_price_history(ticker_symbol: str,
                        start: str = WAR_START_DATE,
                        end: str = TODAY) -> pd.DataFrame:
    """
    Fetch real daily Close prices from Yahoo Finance.
    Returns an empty DataFrame on any failure — callers must handle that case.
    """
    try:
        raw = yf.download(
            ticker_symbol,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        st.warning(f"⚠️ yfinance download error for **{ticker_symbol}**: {exc}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        st.warning(f"⚠️ No data returned for **{ticker_symbol}**. "
                   "Yahoo Finance may be temporarily unavailable.")
        return pd.DataFrame()

    raw = _flatten_columns(raw)

    if "Close" not in raw.columns:
        st.warning(f"⚠️ 'Close' column missing for **{ticker_symbol}**.")
        return pd.DataFrame()

    out = raw[["Close"]].rename(columns={"Close": "price"})
    out.index = pd.to_datetime(out.index)
    out.index.name = "date"
    out = out.dropna()
    return out


@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_prices() -> dict:
    """Fetch real price history for all configured tickers."""
    result = {}
    failed = []
    for name, symbol in ALL_TICKERS.items():
        df = fetch_price_history(symbol)
        result[name] = df
        if df.empty:
            failed.append(f"{name} ({symbol})")

    if failed:
        st.warning(
            "⚠️ Could not fetch live data for: " + ", ".join(failed) +
            ". Check your internet connection or Yahoo Finance status."
        )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# LIVE INTRADAY QUOTE (fastest path — uses fast_info)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_quote(symbol: str) -> dict:
    """
    Pull the latest intraday quote via yfinance Ticker.fast_info.
    Falls back to last two rows of daily history if fast_info is unavailable.
    Returns {} on complete failure.
    """
    try:
        info = yf.Ticker(symbol).fast_info
        price      = getattr(info, "last_price",     None)
        prev_close = getattr(info, "previous_close", None)
        high       = getattr(info, "day_high",       None)
        low        = getattr(info, "day_low",        None)

        if price and prev_close:
            chg     = price - prev_close
            chg_pct = chg / prev_close * 100
            return {
                "price":      round(float(price),   4),
                "change":     round(float(chg),     4),
                "change_pct": round(float(chg_pct), 2),
                "high":       round(float(high), 4) if high else None,
                "low":        round(float(low),  4) if low  else None,
                "source":     "live",
            }
    except Exception:
        pass

    # Fallback: derive from daily history (still real data, just end-of-day)
    df = fetch_price_history(symbol)
    if not df.empty and len(df) >= 2:
        p  = float(df["price"].iloc[-1])
        pc = float(df["price"].iloc[-2])
        return {
            "price":      round(p,  4),
            "change":     round(p - pc, 4),
            "change_pct": round((p - pc) / pc * 100, 2),
            "high":       None,
            "low":        None,
            "source":     "eod",
        }
    return {}


@st.cache_data(ttl=60, show_spinner=False)
def get_live_quotes_all() -> dict:
    """Live/EOD quotes for every asset. Returns asset_name → quote dict."""
    return {
        name: fetch_live_quote(symbol)
        for name, symbol in ALL_TICKERS.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# DERIVED ANALYTICS (all built on real price data)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_latest_prices() -> pd.DataFrame:
    """Summary table: latest price, day %, and since-war % for all assets."""
    rows = []
    for name, symbol in ALL_TICKERS.items():
        df = fetch_price_history(symbol)
        if df.empty or len(df) < 2:
            continue

        latest    = float(df["price"].iloc[-1])
        prev      = float(df["price"].iloc[-2])
        war_start = float(df["price"].iloc[0])

        rows.append({
            "Asset":        name,
            "Category":     next((c for c, ns in ASSET_CATEGORIES.items() if name in ns), "Other"),
            "Price":        round(latest, 4),
            "Day %":        round((latest - prev)    / prev    * 100, 2),
            "Since Feb 22": round((latest - war_start) / war_start * 100, 2),
            "Symbol":       symbol,
            "Last Date":    str(df.index[-1].date()),
        })

    if not rows:
        st.error("❌ No real market data could be loaded. "
                 "Check your internet connection and Yahoo Finance availability.")
    return pd.DataFrame(rows)


@st.cache_data(ttl=120, show_spinner=False)
def get_cumulative_returns() -> pd.DataFrame:
    """All assets indexed to 100 at war start date."""
    frames = []
    for name, df in fetch_all_prices().items():
        if df.empty or len(df) < 2:
            continue
        s = (df["price"] / df["price"].iloc[0]) * 100
        s.name = name
        frames.append(s)
    return pd.concat(frames, axis=1).ffill() if frames else pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def get_correlation_matrix() -> pd.DataFrame:
    """Pairwise return correlation across all available assets."""
    prices = {
        n: df["price"]
        for n, df in fetch_all_prices().items()
        if not df.empty and len(df) > 10
    }
    if len(prices) < 2:
        return pd.DataFrame()
    return pd.DataFrame(prices).ffill().dropna().pct_change().dropna().corr().round(2)


@st.cache_data(ttl=120, show_spinner=False)
def get_commodity_daily_changes() -> pd.DataFrame:
    """Daily % change for commodities — last 30 trading days."""
    rows = {}
    for name, symbol in COMMODITIES.items():
        df = fetch_price_history(symbol)
        if df.empty or len(df) < 2:
            continue
        rows[name] = (df["price"].pct_change() * 100).tail(30)
    return pd.DataFrame(rows).tail(30) if rows else pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def get_sector_heatmap_data() -> pd.DataFrame:
    """
    Sector × month impact heatmap derived from the rule-based geo-event engine.
    Purely rule-driven — no price data needed.
    """
    from config import SECTORS, SECTOR_RULES, GEO_EVENTS
    import pandas as pd

    months = pd.date_range(start=WAR_START_DATE, end=TODAY, freq="MS")
    data = {s: {} for s in SECTORS}

    event_map = [
        (["war", "invade", "attack", "missile", "nuclear", "explosion", "crimea", "houthi"], "war"),
        (["sanction", "swift"], "sanctions"),
        (["hike", "fed"], "rate_hike"),
        (["oil", "opec", "pipeline"], "oil_spike"),
        (["tariff", "trade"], "trade_war"),
        (["ai", "chatgpt"], "ai_boom"),
    ]

    for event in GEO_EVENTS:
        ll = event["label"].lower()
        rule_key = next((k for kws, k in event_map if any(w in ll for w in kws)), "default")
        rule = SECTOR_RULES[rule_key]
        month_key = pd.Timestamp(event["date"]).strftime("%b %Y")
        for sector, impact in rule.items():
            if sector in data:
                data[sector][month_key] = data[sector].get(month_key, 0) + impact

    month_labels = [m.strftime("%b %Y") for m in months]
    return pd.DataFrame(
        {s: [data[s].get(m, 0) for m in month_labels] for s in SECTORS},
        index=month_labels,
    ).T
