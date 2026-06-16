"""VIX Term Structure signal module.

Compares the front-month VIX (^VIX) to the 3-month VIX (^VIX3M) to gauge
whether the volatility term structure is in contango (normal) or backwardation
(stressed).

Scoring logic
-------------
* Ratio = ^VIX / ^VIX3M
* Linear interpolation between two anchor points, then clamped to [0, 100]:
  - ratio 0.85 → score 100  (steep contango, calm markets)
  - ratio 1.15 → score   0  (backwardation, fear/stress)
"""

from __future__ import annotations

import logging
from typing import Dict, Any

import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

_FRONT_TICKER = "^VIX"
_BACK_TICKER = "^VIX3M"
_RATIO_LOW = 0.85   # maps to score 100
_RATIO_HIGH = 1.15  # maps to score   0


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def compute() -> Dict[str, Any]:
    """Compute the VIX Term Structure signal.

    Returns
    -------
    dict
        score      – int in [0, 100].
        raw_value  – VIX / VIX3M ratio (float).
        detail     – human-readable explanation (str).
        name       – 'VIX Term Structure'.
    """
    name = "VIX Term Structure"

    try:
        front = yf.Ticker(_FRONT_TICKER)
        back = yf.Ticker(_BACK_TICKER)

        front_hist = front.history(period="5d")
        back_hist = back.history(period="5d")

        if front_hist.empty:
            raise ValueError(f"No data returned for {_FRONT_TICKER}")
        if back_hist.empty:
            raise ValueError(f"No data returned for {_BACK_TICKER}")

        front_close = float(front_hist["Close"].dropna().iloc[-1])
        back_close = float(back_hist["Close"].dropna().iloc[-1])

        if back_close == 0.0:
            raise ValueError(f"{_BACK_TICKER} close is zero; cannot compute ratio")

        ratio = front_close / back_close

        # Linear interpolation: ratio_low → 100, ratio_high → 0
        score_raw = float(
            np.interp(ratio, [_RATIO_LOW, _RATIO_HIGH], [100.0, 0.0])
        )
        final_score = int(round(_clamp(score_raw)))

        structure_label = "contango" if ratio < 1.0 else "backwardation"

        detail = (
            f"VIX={front_close:.2f} | VIX3M={back_close:.2f} | "
            f"ratio={ratio:.4f} ({structure_label}) | score={final_score}"
        )

        return {
            "score": final_score,
            "raw_value": ratio,
            "detail": detail,
            "name": name,
        }

    except Exception:
        logger.exception("Failed to compute %s signal", name)
        return {
            "score": 50,
            "raw_value": None,
            "detail": "Error computing VIX Term Structure signal; returning neutral score.",
            "name": name,
        }
