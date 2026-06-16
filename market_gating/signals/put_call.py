"""
Put/Call Sentiment Signal Module

Uses the 20-day rate of change (ROC) of the CBOE Volatility Index (^VIX) as a
sentiment proxy, since direct put/call ratio data is not freely available via
standard market-data APIs.

Interpretation:
    - A sharply falling VIX (large negative ROC) indicates rising complacency
      and greed → high score (bullish gate signal).
    - A sharply rising VIX (large positive ROC) indicates spiking fear →
      low score (bearish gate signal).

Score mapping (linear interpolation, clamped to [0, 100]):
    ROC = -30 %  →  score 100
    ROC = +50 %  →  score   0
"""

import numpy as np
import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
_VIX_TICKER = "^VIX"
_LOOKBACK_CALENDAR_DAYS = 120      # fetch enough calendar days to guarantee ≥60 trading days
_ROC_PERIOD = 20                   # 20 trading-day rate of change window

# Linear score-mapping anchors
_ROC_BULL = -30.0   # ROC value that maps to score 100
_ROC_BEAR = 50.0    # ROC value that maps to score 0


def compute() -> dict:
    """Compute the Put/Call Sentiment signal based on VIX 20-day ROC.

    Returns
    -------
    dict
        score      : int in [0, 100] — overall signal strength.
        raw_value  : float — 20-day VIX rate of change in percent.
        detail     : str — human-readable explanation of the result.
        name       : str — 'Put/Call Sentiment'.
    """
    name = "Put/Call Sentiment"

    try:
        # ------------------------------------------------------------------
        # 1. Fetch VIX closing prices
        # ------------------------------------------------------------------
        ticker = yf.Ticker(_VIX_TICKER)
        hist = ticker.history(period=f"{_LOOKBACK_CALENDAR_DAYS}d")

        if hist.empty:
            raise ValueError("yfinance returned no data for ^VIX")

        close = hist["Close"].dropna()

        if len(close) < _ROC_PERIOD + 1:
            raise ValueError(
                f"Insufficient VIX data: got {len(close)} trading days, "
                f"need at least {_ROC_PERIOD + 1}"
            )

        # ------------------------------------------------------------------
        # 2. Compute 20-day rate of change
        # ------------------------------------------------------------------
        current_vix = float(close.iloc[-1])
        vix_20d_ago = float(close.iloc[-(_ROC_PERIOD + 1)])
        roc = (current_vix - vix_20d_ago) / vix_20d_ago * 100.0

        # ------------------------------------------------------------------
        # 3. Map ROC to score via linear interpolation, clamped [0, 100]
        #    ROC = _ROC_BULL (-30) → 100
        #    ROC = _ROC_BEAR (+50) →   0
        #    slope = (0 - 100) / (_ROC_BEAR - _ROC_BULL)
        # ------------------------------------------------------------------
        score_raw = np.interp(roc, [_ROC_BULL, _ROC_BEAR], [100.0, 0.0])
        score = int(np.clip(np.round(score_raw), 0, 100))

        # ------------------------------------------------------------------
        # 4. Build human-readable detail string
        # ------------------------------------------------------------------
        if score >= 70:
            sentiment = "complacency / greed (VIX falling)"
        elif score <= 30:
            sentiment = "fear (VIX spiking)"
        else:
            sentiment = "neutral sentiment"

        detail = (
            f"VIX 20-day ROC: {roc:+.1f}% "
            f"(current VIX {current_vix:.2f}, 20d ago {vix_20d_ago:.2f}). "
            f"Indicates {sentiment}."
        )

        return {
            "score": score,
            "raw_value": round(roc, 2),
            "detail": detail,
            "name": name,
        }

    except Exception as exc:
        return {
            "score": 50,
            "raw_value": None,
            "detail": f"Error computing {name}: {exc}",
            "name": name,
        }
