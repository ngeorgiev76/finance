"""Quantitative Scanner – Factor Scoring
=========================================
Computes 5 alpha-oriented factors for each ticker in the universe, then
percentile-ranks and blends them into a single composite score.

Factors
-------
1. **Momentum Crossover** – 10/50 EMA gap + 3-month return, with crossover bonus.
2. **Volume Surge** – 5-day vs 20-day average volume ratio.
3. **Relative Strength** – 20-day stock return minus 20-day SPY return.
4. **52-Week High Proximity** – current price / 252-day rolling max.
5. **Momentum Health (RSI proxy)** – 14-period RSI mapped to a score.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

import numpy as np
import pandas as pd
import yfinance as yf

from scanner.universe import get_sp500_tickers

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def _linear_map(
    value: float,
    in_lo: float,
    in_hi: float,
    out_lo: float = 0.0,
    out_hi: float = 100.0,
) -> float:
    """Linearly map *value* from [in_lo, in_hi] → [out_lo, out_hi], then clamp."""
    if in_hi == in_lo:
        return (out_lo + out_hi) / 2.0
    scaled = out_lo + (value - in_lo) / (in_hi - in_lo) * (out_hi - out_lo)
    return _clamp(scaled, min(out_lo, out_hi), max(out_lo, out_hi))


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute the standard RSI with exponential (Wilder) smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta.clip(upper=0.0))

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


# ---------------------------------------------------------------------------
# Individual factor functions
# ---------------------------------------------------------------------------

def momentum_crossover(df: pd.DataFrame) -> float:
    """Factor 1: Momentum Crossover (10/50 EMA)."""
    close = df["Close"]
    if len(close) < 63:
        return 0.0

    ema10 = close.ewm(span=10, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()

    current_price = float(close.iloc[-1])
    if current_price == 0:
        return 0.0

    gap_pct = float((ema10.iloc[-1] - ema50.iloc[-1]) / current_price)
    return_3m = float((close.iloc[-1] / close.iloc[-63] - 1.0)) if len(close) >= 63 else 0.0

    # Check for a golden crossover in the last 5 trading days.
    crossover = False
    lookback = min(5, len(ema10) - 1)
    for i in range(1, lookback + 1):
        idx = -i
        prev_idx = idx - 1
        if abs(prev_idx) <= len(ema10):
            if ema10.iloc[prev_idx] <= ema50.iloc[prev_idx] and ema10.iloc[idx] > ema50.iloc[idx]:
                crossover = True
                break

    raw_score = gap_pct * 100.0 + return_3m * 50.0
    raw_score = _clamp(raw_score)

    if crossover:
        raw_score = _clamp(raw_score + 20.0)

    return round(raw_score, 2)


def volume_surge(df: pd.DataFrame) -> float:
    """Factor 2: Volume Surge (5d avg / 20d avg)."""
    vol = df["Volume"]
    if len(vol) < 20:
        return 0.0

    avg_5d = float(vol.iloc[-5:].mean())
    avg_20d = float(vol.iloc[-20:].mean())

    if avg_20d == 0:
        return 0.0

    ratio = avg_5d / avg_20d
    return round(_linear_map(ratio, 0.7, 2.0), 2)


def relative_strength(df: pd.DataFrame, spy_df: pd.DataFrame) -> float:
    """Factor 3: Relative Strength vs SPY (20-day return spread).

    Returns the raw spread (not percentile-ranked); percentile ranking
    happens in ``score_universe`` across the full universe.
    """
    if len(df) < 21 or len(spy_df) < 21:
        return 0.0

    stock_close = df["Close"]
    spy_close = spy_df["Close"]

    stock_ret = float(stock_close.iloc[-1] / stock_close.iloc[-21] - 1.0)
    spy_ret = float(spy_close.iloc[-1] / spy_close.iloc[-21] - 1.0)

    return round(stock_ret - spy_ret, 6)


def high_proximity(df: pd.DataFrame) -> float:
    """Factor 4: 52-Week High Proximity."""
    close = df["Close"]
    if len(close) < 10:
        return 0.0

    lookback = min(252, len(close))
    rolling_high = float(close.iloc[-lookback:].max())

    if rolling_high == 0:
        return 0.0

    ratio = float(close.iloc[-1]) / rolling_high
    return round(_linear_map(ratio, 0.70, 1.0), 2)


def momentum_health(df: pd.DataFrame) -> float:
    """Factor 5: Momentum Health (RSI proxy for short interest decline)."""
    close = df["Close"]
    if len(close) < 20:
        return 0.0

    rsi_series = _compute_rsi(close, period=14)
    rsi = float(rsi_series.iloc[-1])

    if np.isnan(rsi):
        return 50.0

    if rsi > 70:
        return 80.0
    elif rsi >= 50:
        # Linear 50 → 80 as RSI goes 50 → 70
        return round(_linear_map(rsi, 50.0, 70.0, 50.0, 80.0), 2)
    elif rsi >= 30:
        # Linear 20 → 50 as RSI goes 30 → 50
        return round(_linear_map(rsi, 30.0, 50.0, 20.0, 50.0), 2)
    else:
        return 40.0


# ---------------------------------------------------------------------------
# Factor names (stable order used everywhere)
# ---------------------------------------------------------------------------
FACTOR_NAMES = [
    "momentum_crossover",
    "volume_surge",
    "relative_strength",
    "high_proximity",
    "momentum_health",
]

FACTOR_FUNCTIONS: dict[str, Callable] = {
    "momentum_crossover": momentum_crossover,
    "volume_surge": volume_surge,
    # relative_strength handled specially (needs SPY)
    "high_proximity": high_proximity,
    "momentum_health": momentum_health,
}


# ---------------------------------------------------------------------------
# Extract single-ticker DataFrame from a multi-ticker yfinance download
# ---------------------------------------------------------------------------

def _extract_ticker_df(
    all_data: pd.DataFrame,
    ticker: str,
    tickers: list[str],
) -> pd.DataFrame | None:
    """Pull a single ticker's OHLCV DataFrame from a multi-ticker download.

    Returns *None* if data is missing or too sparse to be useful.
    """
    try:
        if len(tickers) == 1:
            # Single-ticker download – columns are just OHLCV
            df = all_data.copy()
        else:
            # Multi-ticker download (group_by='ticker') – multi-level columns
            if isinstance(all_data.columns, pd.MultiIndex):
                # yfinance >= 0.2.31 may return (Ticker, Price) or (Price, Ticker)
                if ticker in all_data.columns.get_level_values(0):
                    df = all_data[ticker].copy()
                elif ticker in all_data.columns.get_level_values(1):
                    df = all_data.xs(ticker, level=1, axis=1).copy()
                else:
                    return None
            else:
                return None

        # Drop rows where Close is NaN
        if "Close" not in df.columns:
            return None
        df = df.dropna(subset=["Close"])
        if len(df) < 20:
            return None
        return df
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def score_universe(
    zone_label: str,
    tickers: list[str] | None = None,
    top_n: int = 25,
    progress_callback: Callable[[int, int], Any] | None = None,
) -> dict:
    """Score every ticker in the universe and return the top candidates.

    Parameters
    ----------
    zone_label : str
        Current deployment zone (``"FULL DEPLOY"``, ``"REDUCED"``,
        ``"DEFENSIVE"``).
    tickers : list[str] | None
        Override the default S&P 500 universe.
    top_n : int
        Number of candidates to return.
    progress_callback : callable | None
        Called with ``(current_count, total_count)`` as tickers are scored.

    Returns
    -------
    dict
        Scanner results; see module docstring for schema.
    """
    # DEFENSIVE mode – scanner is disabled.
    if zone_label == "DEFENSIVE":
        return {
            "disabled": True,
            "reason": "Scanner disabled in DEFENSIVE mode",
            "candidates": [],
        }

    if tickers is None:
        tickers = get_sp500_tickers()

    # ------------------------------------------------------------------
    # 1. Batch-download 1 year of daily data (single network call)
    # ------------------------------------------------------------------
    download_tickers = list(set(tickers) | {"SPY"})
    logger.info(
        "Downloading 1-year daily data for %d tickers…",
        len(download_tickers),
    )

    all_data = yf.download(
        download_tickers,
        period="1y",
        group_by="ticker",
        threads=True,
        progress=False,
    )

    if all_data.empty:
        logger.error("yfinance returned an empty DataFrame – aborting scan")
        return {
            "zone": zone_label,
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "universe_size": 0,
            "candidates": [],
            "threshold": None,
        }

    # SPY reference data
    spy_df = _extract_ticker_df(all_data, "SPY", download_tickers)
    if spy_df is None:
        logger.warning("SPY data unavailable – relative strength will be zero")

    # ------------------------------------------------------------------
    # 2. Compute raw factor scores for every ticker
    # ------------------------------------------------------------------
    records: list[dict] = []
    total = len(tickers)

    for idx, ticker in enumerate(tickers):
        if progress_callback is not None:
            progress_callback(idx + 1, total)

        df = _extract_ticker_df(all_data, ticker, download_tickers)
        if df is None:
            continue

        close = df["Close"]
        current_price = float(close.iloc[-1])

        # 21-day return
        return_1m = (
            float(close.iloc[-1] / close.iloc[-21] - 1.0)
            if len(close) >= 21
            else np.nan
        )
        # 63-day return
        return_3m = (
            float(close.iloc[-1] / close.iloc[-63] - 1.0)
            if len(close) >= 63
            else np.nan
        )

        # Raw factor values
        try:
            f_mc = momentum_crossover(df)
            f_vs = volume_surge(df)
            f_rs = relative_strength(df, spy_df) if spy_df is not None else 0.0
            f_hp = high_proximity(df)
            f_mh = momentum_health(df)
        except Exception:
            logger.debug("Factor computation failed for %s – skipping", ticker)
            continue

        records.append(
            {
                "ticker": ticker,
                "price": round(current_price, 2),
                "return_1m": round(return_1m * 100, 2) if not np.isnan(return_1m) else None,
                "return_3m": round(return_3m * 100, 2) if not np.isnan(return_3m) else None,
                "momentum_crossover": f_mc,
                "volume_surge": f_vs,
                "relative_strength": f_rs,
                "high_proximity": f_hp,
                "momentum_health": f_mh,
            }
        )

    if not records:
        return {
            "zone": zone_label,
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "universe_size": 0,
            "candidates": [],
            "threshold": None,
        }

    # ------------------------------------------------------------------
    # 3. Percentile-rank each factor across the universe
    # ------------------------------------------------------------------
    scores_df = pd.DataFrame(records)
    n_stocks = len(scores_df)

    for factor in FACTOR_NAMES:
        col = scores_df[factor]
        # rank → 0-100 percentile
        scores_df[f"{factor}_pctile"] = col.rank(pct=True) * 100.0

    # Composite = equal weight (20 % each) of percentile-ranked factors
    pctile_cols = [f"{f}_pctile" for f in FACTOR_NAMES]
    scores_df["composite"] = scores_df[pctile_cols].mean(axis=1).round(2)

    # ------------------------------------------------------------------
    # 4. Apply zone filter and sort
    # ------------------------------------------------------------------
    threshold: float | None = None

    if zone_label == "REDUCED":
        threshold = 75.0
        scores_df = scores_df[scores_df["composite"] >= threshold]

    scores_df = scores_df.sort_values("composite", ascending=False).head(top_n)

    # ------------------------------------------------------------------
    # 5. Build output
    # ------------------------------------------------------------------
    candidates: list[dict] = []
    for _, row in scores_df.iterrows():
        candidates.append(
            {
                "ticker": row["ticker"],
                "composite": round(float(row["composite"]), 2),
                "factors": {
                    "momentum_crossover": round(float(row["momentum_crossover_pctile"]), 2),
                    "volume_surge": round(float(row["volume_surge_pctile"]), 2),
                    "relative_strength": round(float(row["relative_strength_pctile"]), 2),
                    "high_proximity": round(float(row["high_proximity_pctile"]), 2),
                    "momentum_health": round(float(row["momentum_health_pctile"]), 2),
                },
                "price": row["price"],
                "return_1m": row["return_1m"],
                "return_3m": row["return_3m"],
            }
        )

    return {
        "zone": zone_label,
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "universe_size": n_stocks,
        "candidates": candidates,
        "threshold": threshold,
    }
