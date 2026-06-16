"""
Credit Spreads Signal
=====================
Uses the HYG / TLT price ratio as a proxy for high-yield credit spreads.

    HYG — iShares iBoxx $ High Yield Corporate Bond ETF
    TLT — iShares 20+ Year Treasury Bond ETF

When high-yield bonds outperform treasuries (ratio rises), credit spreads
are tightening — the market is pricing in low default risk.  When the
ratio falls, spreads are widening and stress is rising.

Method:
    1. Download 1 year of daily close prices for HYG and TLT.
    2. Compute the HYG / TLT price ratio time series.
    3. Z-score the latest ratio against its trailing 1-year distribution.

Score mapping (z-score → 0-100):
    z = −2  (tight spreads, bullish)  → 100
    z = +2  (wide spreads, bearish)   →   0
    Linear interpolation, clamped to [0, 100].

    score = (2 − z) / 4 × 100
"""

import numpy as np
import pandas as pd
import yfinance as yf


def _zscore_to_score(z: float) -> float:
    """Map z-score from [-2, +2] → score [100, 0], clamped to [0, 100]."""
    score = (2.0 - z) / 4.0 * 100.0
    return float(np.clip(score, 0.0, 100.0))


def compute() -> dict:
    """
    Compute the Credit Spreads signal.

    Returns
    -------
    dict
        score : float       0-100 deployment score
        raw_value : float   z-score of HYG/TLT ratio (negative = tight = bullish)
        detail : str        human-readable explanation
        name : str          'Credit Spreads'
    """
    try:
        end = pd.Timestamp.now(tz="America/New_York")
        start = end - pd.DateOffset(years=1, weeks=2)  # extra buffer

        hyg = yf.download("HYG", start=start.strftime("%Y-%m-%d"),
                           end=end.strftime("%Y-%m-%d"), progress=False)
        tlt = yf.download("TLT", start=start.strftime("%Y-%m-%d"),
                           end=end.strftime("%Y-%m-%d"), progress=False)

        if hyg.empty or tlt.empty:
            raise ValueError("Could not download HYG or TLT data")

        # Flatten MultiIndex columns if present (yfinance >= 0.2.31)
        if isinstance(hyg.columns, pd.MultiIndex):
            hyg.columns = hyg.columns.get_level_values(0)
        if isinstance(tlt.columns, pd.MultiIndex):
            tlt.columns = tlt.columns.get_level_values(0)

        # Align on common trading dates
        common_idx = hyg.index.intersection(tlt.index)
        if len(common_idx) < 60:
            raise ValueError(
                f"Insufficient overlapping data: {len(common_idx)} days"
            )

        ratio = hyg.loc[common_idx, "Close"] / tlt.loc[common_idx, "Close"]
        ratio = ratio.dropna()

        if len(ratio) < 60:
            raise ValueError(
                f"Insufficient ratio data after dropna: {len(ratio)} days"
            )

        current_ratio = float(ratio.iloc[-1])
        mean = float(ratio.mean())
        std = float(ratio.std())

        if std < 1e-9:
            raise ValueError("HYG/TLT ratio has near-zero standard deviation")

        z = (current_ratio - mean) / std
        score = _zscore_to_score(z)

        # Determine qualitative label
        if z <= -1.0:
            condition = "very tight (bullish)"
        elif z <= -0.3:
            condition = "tight (mildly bullish)"
        elif z <= 0.3:
            condition = "near average"
        elif z <= 1.0:
            condition = "wide (mildly bearish)"
        else:
            condition = "very wide (bearish)"

        detail = (
            f"HYG/TLT ratio {current_ratio:.4f} "
            f"(1y mean {mean:.4f}, std {std:.4f}). "
            f"Z-score {z:+.2f} → spreads {condition}. "
            f"Score {score:.0f}/100."
        )

        return {
            "score": round(score, 2),
            "raw_value": round(z, 4),
            "detail": detail,
            "name": "Credit Spreads",
        }

    except Exception as exc:
        return {
            "score": 50,
            "raw_value": None,
            "detail": f"Credit Spreads computation failed: {exc}",
            "name": "Credit Spreads",
        }
