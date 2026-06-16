"""Factor Crowding signal module.

Measures the degree of factor crowding by tracking the rolling correlation
between momentum and value factor returns.  When these two factors become
highly negatively correlated it indicates that momentum trades are crowded
and vulnerable to sharp reversals (the "momentum crash" phenomenon).

Methodology
-----------
1. Download ~1 year of daily prices for factor-proxy ETFs:
   - MTUM  (iShares MSCI USA Momentum Factor ETF)
   - VLUE  (iShares MSCI USA Value Factor ETF)
2. Compute daily returns for each ETF.
3. Calculate the 60-day rolling Pearson correlation between the two return
   series.
4. Take the most recent correlation value and map it to a 0-100 score via
   linear interpolation:
       corr = +0.3  →  score 100  (normal regime, factors independent)
       corr = -0.8  →  score   0  (extreme crowding / reversal risk)
5. Score is clamped to [0, 100].

A highly negative correlation implies that when momentum rallies, value
sells off (and vice-versa), which is the hallmark of crowded factor
positioning and precedes momentum crashes.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, Any

import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

_MOMENTUM_ETF = "MTUM"
_VALUE_ETF = "VLUE"
_LOOKBACK_DAYS = 365
_ROLLING_WINDOW = 60

# Correlation anchors for the linear score mapping.
_CORR_NORMAL = 0.3    # corr at which score = 100
_CORR_CROWDED = -0.8   # corr at which score = 0


def compute() -> Dict[str, Any]:
    """Compute the Factor Crowding signal.

    Returns
    -------
    dict
        score      – int in [0, 100].
        raw_value  – latest 60-day rolling correlation (float).
        detail     – human-readable explanation (str).
        name       – 'Factor Crowding'.
    """
    name = "Factor Crowding"

    try:
        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=_LOOKBACK_DAYS)

        data = yf.download(
            [_MOMENTUM_ETF, _VALUE_ETF],
            start=str(start_date),
            end=str(end_date),
            progress=False,
        )

        if data.empty:
            raise ValueError(
                f"No data returned for {_MOMENTUM_ETF} / {_VALUE_ETF}"
            )

        # yfinance may return MultiIndex columns (metric, ticker).
        # Flatten to just the ticker level under "Close".
        import pandas as pd
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"]
            if isinstance(close, pd.DataFrame):
                close.columns = close.columns.get_level_values(0)
        else:
            close = data[["Close"]]

        if _MOMENTUM_ETF not in close.columns or _VALUE_ETF not in close.columns:
            raise ValueError(
                f"Missing expected columns; got {list(close.columns)}"
            )

        mtum_ret = close[_MOMENTUM_ETF].pct_change().dropna()
        vlue_ret = close[_VALUE_ETF].pct_change().dropna()

        # Align the two return series.
        combined = mtum_ret.to_frame("mtum").join(
            vlue_ret.to_frame("vlue"), how="inner"
        )

        if len(combined) < _ROLLING_WINDOW:
            raise ValueError(
                f"Only {len(combined)} overlapping return days; "
                f"need at least {_ROLLING_WINDOW}"
            )

        rolling_corr = combined["mtum"].rolling(_ROLLING_WINDOW).corr(
            combined["vlue"]
        )
        rolling_corr = rolling_corr.dropna()

        if rolling_corr.empty:
            raise ValueError("Rolling correlation series is empty")

        current_corr = float(rolling_corr.iloc[-1])

        # Linear interpolation: _CORR_CROWDED → 0, _CORR_NORMAL → 100.
        score = float(
            np.interp(current_corr, [_CORR_CROWDED, _CORR_NORMAL], [0, 100])
        )
        final_score = int(round(np.clip(score, 0, 100)))

        detail = (
            f"60d corr(MTUM, VLUE)={current_corr:.3f} | "
            f"score={final_score} "
            f"(0 at corr≤{_CORR_CROWDED}, 100 at corr≥{_CORR_NORMAL})"
        )

        return {
            "score": final_score,
            "raw_value": current_corr,
            "detail": detail,
            "name": name,
        }

    except Exception:
        logger.exception("Failed to compute %s signal", name)
        return {
            "score": 50,
            "raw_value": None,
            "detail": "Error computing Factor Crowding signal; returning neutral score.",
            "name": name,
        }
