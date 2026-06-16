"""
Market Breadth Signal
=====================
Measures the percentage of S&P 500 stocks trading above their 200-day
simple moving average. Healthy bull markets feature broad participation;
narrow rallies driven by a handful of mega-caps score poorly.

Primary data source:
    ^MMTH — CBOE S&P 500 stocks above 200-day SMA index (values ~0-100).

Fallback (if ^MMTH is unavailable):
    Compute the RSP / SPY price ratio and z-score it over 1 year.
    When RSP outperforms SPY, breadth is expanding.  The z-score is
    mapped to a synthetic breadth percentage:
        z = +2  → ~80 % breadth  (strong)
        z = -2  → ~30 % breadth  (weak)
    Then the standard breadth-to-score mapping is applied.

Score mapping (breadth percentage → 0-100 score):
    80 % breadth → 100
    30 % breadth →   0
    Linear interpolation, clamped to [0, 100].
"""

import numpy as np
import pandas as pd
import yfinance as yf


def _breadth_pct_to_score(breadth_pct: float) -> float:
    """Map breadth percentage [30, 80] → score [0, 100], clamped."""
    score = (breadth_pct - 30.0) / (80.0 - 30.0) * 100.0
    return float(np.clip(score, 0.0, 100.0))


def _try_mmth() -> float | None:
    """
    Attempt to fetch the latest value of ^MMTH (S&P 500 stocks above
    200-day SMA percentage) via yfinance.

    Returns the breadth percentage (0-100) or None on failure.
    """
    try:
        ticker = yf.Ticker("^MMTH")
        hist = ticker.history(period="5d")
        if hist.empty:
            return None
        last_close = float(hist["Close"].dropna().iloc[-1])
        # ^MMTH values are already expressed as a percentage (0-100)
        if 0.0 <= last_close <= 100.0:
            return last_close
        return None
    except Exception:
        return None


def _fallback_rsp_spy() -> tuple[float, float]:
    """
    Fallback breadth estimator using the RSP / SPY price ratio.

    RSP (Invesco S&P 500 Equal Weight ETF) gives equal weight to all
    constituents.  SPY is cap-weighted.  When breadth is healthy the
    average stock keeps up with the mega-caps, so RSP/SPY rises.

    Returns
    -------
    breadth_pct : float
        Synthetic breadth percentage derived from the ratio z-score.
    z_score : float
        The z-score of the current RSP/SPY ratio vs its 1-year history.
    """
    end = pd.Timestamp.now(tz="America/New_York")
    start = end - pd.DateOffset(years=1, weeks=2)  # extra buffer for 252 trading days

    rsp = yf.download("RSP", start=start.strftime("%Y-%m-%d"),
                       end=end.strftime("%Y-%m-%d"), progress=False)
    spy = yf.download("SPY", start=start.strftime("%Y-%m-%d"),
                       end=end.strftime("%Y-%m-%d"), progress=False)

    if rsp.empty or spy.empty:
        raise ValueError("Could not download RSP or SPY data")

    # Flatten MultiIndex columns if present (yfinance >= 0.2.31)
    if isinstance(rsp.columns, pd.MultiIndex):
        rsp.columns = rsp.columns.get_level_values(0)
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)

    # Align on common dates
    common_idx = rsp.index.intersection(spy.index)
    if len(common_idx) < 60:
        raise ValueError(f"Insufficient overlapping data: {len(common_idx)} days")

    ratio = rsp.loc[common_idx, "Close"] / spy.loc[common_idx, "Close"]
    ratio = ratio.dropna()

    current_ratio = float(ratio.iloc[-1])
    mean = float(ratio.mean())
    std = float(ratio.std())

    if std < 1e-9:
        raise ValueError("RSP/SPY ratio has near-zero standard deviation")

    z = (current_ratio - mean) / std

    # Map z-score to synthetic breadth percentage
    # z = +2  → 80 %   (strong breadth)
    # z = -2  → 30 %   (weak breadth)
    # Linear: breadth = 55 + 12.5 * z  (midpoint 55 at z=0)
    breadth_pct = 55.0 + 12.5 * z
    breadth_pct = float(np.clip(breadth_pct, 5.0, 95.0))  # soft clamp before scoring

    return breadth_pct, z


def compute() -> dict:
    """
    Compute the Market Breadth signal.

    Returns
    -------
    dict
        score : float       0-100 deployment score
        raw_value : float   breadth percentage (0-100)
        detail : str        human-readable explanation
        name : str          'Market Breadth'
    """
    try:
        # --- Primary: ^MMTH ---
        breadth_pct = _try_mmth()

        if breadth_pct is not None:
            score = _breadth_pct_to_score(breadth_pct)
            detail = (
                f"{breadth_pct:.1f}% of S&P 500 stocks above 200-day SMA "
                f"(source: ^MMTH). Score {score:.0f}/100."
            )
            return {
                "score": round(score, 2),
                "raw_value": round(breadth_pct, 2),
                "detail": detail,
                "name": "Market Breadth",
            }

        # --- Fallback: RSP / SPY ratio z-score ---
        breadth_pct, z = _fallback_rsp_spy()
        score = _breadth_pct_to_score(breadth_pct)
        detail = (
            f"RSP/SPY ratio z-score {z:+.2f} → synthetic breadth {breadth_pct:.1f}%. "
            f"Score {score:.0f}/100 (fallback method; ^MMTH unavailable)."
        )
        return {
            "score": round(score, 2),
            "raw_value": round(breadth_pct, 2),
            "detail": detail,
            "name": "Market Breadth",
        }

    except Exception as exc:
        return {
            "score": 50,
            "raw_value": None,
            "detail": f"Market Breadth computation failed: {exc}",
            "name": "Market Breadth",
        }
