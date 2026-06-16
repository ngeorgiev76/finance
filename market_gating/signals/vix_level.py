"""VIX Level signal module.

Fetches ^VIX data for the trailing one year, percentile-ranks the current
close against that history, and produces a deployment-gating score.

Scoring logic
-------------
* Base score: linear map from percentile rank to score.
  - percentile  0  → score 100  (very low VIX = green light)
  - percentile 100 → score   0  (very high VIX = red light)
* Bonus:  +5 when VIX < 15  (unusually calm markets).
* Penalty: −10 when VIX > 30 (elevated fear).
* Final score is clamped to [0, 100].
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, Any

import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

_TICKER = "^VIX"
_LOOKBACK_DAYS = 365
_LOW_VIX_THRESHOLD = 15.0
_HIGH_VIX_THRESHOLD = 30.0
_LOW_VIX_BONUS = 5
_HIGH_VIX_PENALTY = -10


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def compute() -> Dict[str, Any]:
    """Compute the VIX Level signal.

    Returns
    -------
    dict
        score      – int in [0, 100].
        raw_value  – current VIX close (float).
        detail     – human-readable explanation (str).
        name       – 'VIX Level'.
    """
    name = "VIX Level"

    try:
        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=_LOOKBACK_DAYS)

        ticker = yf.Ticker(_TICKER)
        hist = ticker.history(start=str(start_date), end=str(end_date))

        if hist.empty or len(hist) < 2:
            raise ValueError(f"Insufficient data returned for {_TICKER}")

        closes = hist["Close"].dropna().values
        current_vix = float(closes[-1])

        # Percentile rank of current VIX within the trailing window.
        percentile = float(np.sum(closes < current_vix) / len(closes) * 100.0)

        # Linear map: percentile 0 → 100, percentile 100 → 0.
        base_score = 100.0 - percentile

        # Bonus / penalty adjustments.
        adjustment = 0
        adjustment_details: list[str] = []

        if current_vix < _LOW_VIX_THRESHOLD:
            adjustment += _LOW_VIX_BONUS
            adjustment_details.append(
                f"+{_LOW_VIX_BONUS} bonus (VIX < {_LOW_VIX_THRESHOLD})"
            )

        if current_vix > _HIGH_VIX_THRESHOLD:
            adjustment += _HIGH_VIX_PENALTY
            adjustment_details.append(
                f"{_HIGH_VIX_PENALTY} penalty (VIX > {_HIGH_VIX_THRESHOLD})"
            )

        final_score = int(round(_clamp(base_score + adjustment)))

        detail_parts = [
            f"VIX={current_vix:.2f}",
            f"percentile={percentile:.1f}%",
            f"base_score={base_score:.1f}",
        ]
        if adjustment_details:
            detail_parts.extend(adjustment_details)
        detail_parts.append(f"final_score={final_score}")

        detail = " | ".join(detail_parts)

        return {
            "score": final_score,
            "raw_value": current_vix,
            "detail": detail,
            "name": name,
        }

    except Exception:
        logger.exception("Failed to compute %s signal", name)
        return {
            "score": 50,
            "raw_value": None,
            "detail": "Error computing VIX Level signal; returning neutral score.",
            "name": name,
        }
