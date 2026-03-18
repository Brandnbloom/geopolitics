"""
data_fetch.py - Live market data via yfinance. No mock/synthetic data.
Day % always sourced from fast_info (live prev_close) to avoid lag on Indian stocks.
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
# PRICE HISTORY  (for charts and since-war % only)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def fetch_price_history(ticker_symbol: str,
                        start: str = WAR_START_DATE,
                        end: str = TODAY) -> pd.DataFrame:
    """
    Fetch real daily Close prices from Yahoo Finance.
    Returns an empty DataFrame on any failure.
    NOTE: Do NOT use the last two rows for Day % — use fetch_live_quote instead,
          which reads fast_info.previous_close for accuracy (especially .NS stocks).
    """
    try:
        raw = yf.download(
            ticker_symbol,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=30,
        )
    except Exception as exc:
        st.warning(f"yfinance download error for {ticker_symbol}: {exc}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        st.warning(f"No data returned for {ticker_symbol}. Yahoo Finance may be temporarily unavailable.")
        return pd.DataFrame()

    raw = _flatten_columns(raw)

    if "Close" not in raw.columns:
        st.warning(f"Close column missing for {ticker_symbol}.")
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
        st.warning("Could not fetch data for: " + ", ".join(failed))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# LIVE INTRADAY QUOTE
# This is the AUTHORITATIVE source for Day % — uses fast_info.previous_close
# which Yahoo Finance updates correctly for all markets including NSE (.NS)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_quote(symbol: str) -> dict:
    """
    Pull the live quote via yfinance Ticker.fast_info.
    fast_info.previous_close is the official prior session close —
    this is correct for Indian stocks unlike computing from daily history rows.

    Returns dict with: price, change, change_pct, prev_close, high, low, source
    Returns {} on complete failure.
    """
    try:
        ticker     = yf.Ticker(symbol)
        info       = ticker.fast_info
        price      = getattr(info, "last_price",     None)
        prev_close = getattr(info, "previous_close", None)
        high       = getattr(info, "day_high",       None)
        low        = getattr(info, "day_low",        None)
        open_      = getattr(info, "open",           None)

        # Validate — must have both price and prev_close, and they must be positive
        if (price and prev_close and
                float(price) > 0 and float(prev_close) > 0):
            chg     = float(price) - float(prev_close)
            chg_pct = chg / float(prev_close) * 100
            return {
                "price":      round(float(price),      4),
                "prev_close": round(float(prev_close), 4),
                "change":     round(chg,               4),
                "change_pct": round(chg_pct,           2),
                "high":       round(float(high),  4) if high  else None,
                "low":        round(float(low),   4) if low   else None,
                "open":       round(float(open_), 4) if open_ else None,
                "source":     "live",
            }
    except Exception:
        pass

    # Fallback: try history-based EOD calculation
    # This can be off by 1 day for some markets — used only when fast_info fails
    try:
        df = fetch_price_history(symbol)
        if not df.empty and len(df) >= 2:
            p  = float(df["price"].iloc[-1])
            pc = float(df["price"].iloc[-2])
            if p > 0 and pc > 0:
                return {
                    "price":      round(p,        4),
                    "prev_close": round(pc,       4),
                    "change":     round(p - pc,   4),
                    "change_pct": round((p - pc) / pc * 100, 2),
                    "high":       None,
                    "low":        None,
                    "open":       None,
                    "source":     "eod",  # flag as EOD so UI can show caveat
                }
    except Exception:
        pass

    return {}


@st.cache_data(ttl=60, show_spinner=False)
def get_live_quotes_all() -> dict:
    """Live quotes for every asset. Returns asset_name -> quote dict."""
    return {
        name: fetch_live_quote(symbol)
        for name, symbol in ALL_TICKERS.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY TABLE
# Day % comes from fast_info (live) — NOT from history rows
# Since Feb 22 % comes from history (correct for long-term)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_latest_prices() -> pd.DataFrame:
    """
    Summary table for all assets.
    - Price and Day %    → from fetch_live_quote (fast_info, accurate prev_close)
    - Since Feb 22 %     → from fetch_price_history (long-term accuracy)
    """
    rows = []
    for name, symbol in ALL_TICKERS.items():

        # ── Live quote for price + Day % ──────────────────────────────────
        quote = fetch_live_quote(symbol)
        if not quote:
            continue

        price   = quote["price"]
        day_pct = quote["change_pct"]
        source  = quote["source"]

        # ── History for since-war return ──────────────────────────────────
        df = fetch_price_history(symbol)
        if not df.empty and len(df) >= 2:
            war_start = float(df["price"].iloc[0])
            war_pct   = round((price - war_start) / war_start * 100, 2)
            last_date = str(df.index[-1].date())
        else:
            war_pct   = None
            last_date = "N/A"

        rows.append({
            "Asset":        name,
            "Category":     next((c for c, ns in ASSET_CATEGORIES.items() if name in ns), "Other"),
            "Price":        round(price, 4),
            "Prev Close":   quote.get("prev_close"),
            "Day %":        round(day_pct, 2),
            "Since Feb 22": war_pct,
            "Symbol":       symbol,
            "Last Date":    last_date,
            "Source":       source,
        })

    if not rows:
        st.error("No real market data could be loaded. Check your internet connection.")
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

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
    """Sector x month impact heatmap from rule-based geo-event engine."""
    from config import SECTORS, SECTOR_RULES, GEO_EVENTS
    import pandas as pd

    months = pd.date_range(start=WAR_START_DATE, end=TODAY, freq="MS")
    data   = {s: {} for s in SECTORS}

    event_map = [
        (["war", "invade", "attack", "missile", "nuclear", "explosion", "crimea", "houthi"], "war"),
        (["sanction", "swift"], "sanctions"),
        (["hike", "fed"], "rate_hike"),
        (["oil", "opec", "pipeline"], "oil_spike"),
        (["tariff", "trade"], "trade_war"),
        (["ai", "chatgpt"], "ai_boom"),
    ]

    for event in GEO_EVENTS:
        ll       = event["label"].lower()
        rule_key = next((k for kws, k in event_map if any(w in ll for w in kws)), "default")
        rule     = SECTOR_RULES[rule_key]
        mk       = pd.Timestamp(event["date"]).strftime("%b %Y")
        for sector, impact in rule.items():
            if sector in data:
                data[sector][mk] = data[sector].get(mk, 0) + impact

    month_labels = [m.strftime("%b %Y") for m in months]
    return pd.DataFrame(
        {s: [data[s].get(m, 0) for m in month_labels] for s in SECTORS},
        index=month_labels,
    ).T
