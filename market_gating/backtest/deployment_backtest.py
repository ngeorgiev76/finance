"""
Historical Deployment Backtest Module
======================================

Recomputes the deployment score daily over a 2-year history using
yesterday's score for today's allocation (no look-ahead bias).

Signals & Weights:
    VIX Level          (0.25)  – Percentile-rank vs trailing 1-year
    VIX Term Structure (0.20)  – VIX / VIX3M ratio
    Market Breadth     (0.20)  – RSP/SPY ratio z-score (fallback proxy)
    Credit Spreads     (0.15)  – HYG/TLT ratio z-score
    Put/Call Sentiment (0.10)  – VIX 20-day ROC
    Factor Crowding    (0.10)  – MTUM/VLUE 60-day return correlation

Deployment Zones:
    FULL DEPLOY  : score 70-100, sizing = 100 %
    REDUCED      : score 40-69,  sizing =  60 %
    DEFENSIVE    : score  0-39,  sizing =  25 %
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ── Zone definitions ────────────────────────────────────────────────────────
ZONE_FULL = "FULL DEPLOY"
ZONE_REDUCED = "REDUCED"
ZONE_DEFENSIVE = "DEFENSIVE"

ZONE_COLORS = {
    ZONE_FULL: "#00e676",
    ZONE_REDUCED: "#ffd600",
    ZONE_DEFENSIVE: "#ff1744",
}

ZONE_SIZING = {
    ZONE_FULL: "100%",
    ZONE_REDUCED: "60%",
    ZONE_DEFENSIVE: "25%",
}

# ── Signal weights ──────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "VIX Level": 0.25,
    "VIX Term Structure": 0.20,
    "Market Breadth": 0.20,
    "Credit Spreads": 0.15,
    "Put/Call Sentiment": 0.10,
    "Factor Crowding": 0.10,
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _classify_zone(score: float) -> str:
    """Map a composite score to a deployment zone."""
    if score >= 70:
        return ZONE_FULL
    elif score >= 40:
        return ZONE_REDUCED
    else:
        return ZONE_DEFENSIVE


def _download_ticker(ticker: str, start: str, end: str) -> pd.Series:
    """Download adjusted close for a single ticker and return as a Series."""
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    # yfinance may return MultiIndex columns even for a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df["Close"].squeeze()


# ── Signal computation (vectorised) ────────────────────────────────────────

def _compute_vix_level(vix: pd.Series) -> pd.Series:
    """
    Percentile-rank current VIX within trailing 252 trading days.
    Score = 100 - percentile.  +5 if VIX < 15, -10 if VIX > 30.
    """
    rolling_pct = vix.rolling(252, min_periods=60).apply(
        lambda w: pd.Series(w).rank(pct=True).iloc[-1] * 100, raw=False
    )
    score = 100.0 - rolling_pct
    score = score + np.where(vix < 15, 5, 0)
    score = score + np.where(vix > 30, -10, 0)
    return score.clip(0, 100)


def _compute_vix_term_structure(vix: pd.Series, vix3m: pd.Series) -> pd.Series:
    """
    VIX / VIX3M ratio.  Map 0.85 → 100, 1.15 → 0 (linear interp).
    """
    ratio = vix / vix3m
    score = pd.Series(
        np.interp(ratio.values, [0.85, 1.15], [100, 0]),
        index=ratio.index,
    )
    return score.clip(0, 100)


def _compute_market_breadth(rsp: pd.Series, spy: pd.Series) -> pd.Series:
    """
    RSP/SPY ratio z-score over trailing 252 days.
    breadth_pct = 55 + 12.5 * z
    score = (breadth_pct - 30) / 50 * 100
    """
    ratio = rsp / spy
    rolling_mean = ratio.rolling(252, min_periods=60).mean()
    rolling_std = ratio.rolling(252, min_periods=60).std()
    z = (ratio - rolling_mean) / rolling_std
    breadth_pct = 55 + 12.5 * z
    score = (breadth_pct - 30) / 50 * 100
    return score.clip(0, 100)


def _compute_credit_spreads(hyg: pd.Series, tlt: pd.Series) -> pd.Series:
    """
    HYG/TLT ratio z-score over trailing 252 days.
    Score = (2 - z) / 4 * 100.
    """
    ratio = hyg / tlt
    rolling_mean = ratio.rolling(252, min_periods=60).mean()
    rolling_std = ratio.rolling(252, min_periods=60).std()
    z = (ratio - rolling_mean) / rolling_std
    score = (2 - z) / 4 * 100
    return score.clip(0, 100)


def _compute_putcall_sentiment(vix: pd.Series) -> pd.Series:
    """
    VIX 20-day ROC (%).  Map ROC = -30 → 100, ROC = +50 → 0.
    """
    roc = vix.pct_change(20) * 100  # percentage change over 20 days
    score = pd.Series(
        np.interp(roc.values, [-30, 50], [100, 0]),
        index=roc.index,
    )
    return score.clip(0, 100)


def _compute_factor_crowding(mtum: pd.Series, vlue: pd.Series) -> pd.Series:
    """
    MTUM/VLUE daily-return 60-day rolling correlation.
    Map corr = -0.8 → 0, corr = +0.3 → 100.
    """
    ret_mtum = mtum.pct_change()
    ret_vlue = vlue.pct_change()
    rolling_corr = ret_mtum.rolling(60, min_periods=30).corr(ret_vlue)
    score = pd.Series(
        np.interp(rolling_corr.values, [-0.8, 0.3], [0, 100]),
        index=rolling_corr.index,
    )
    return score.clip(0, 100)


# ── Main backtest function ──────────────────────────────────────────────────

def run_backtest(lookback_years: int = 2) -> dict | None:
    """
    Run a historical deployment-score backtest.

    Parameters
    ----------
    lookback_years : int
        Number of years for the backtest window (default 2).
        An extra year of data is downloaded for trailing-window warm-up.

    Returns
    -------
    dict or None
        A dictionary with backtest results including dates, prices,
        composite scores, zones, zone colours, per-zone performance
        statistics, and per-signal score histories.  Returns ``None``
        on unrecoverable errors.
    """
    try:
        total_years = lookback_years + 1  # extra year for warm-up
        end_date = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=total_years * 365 + 30)).strftime("%Y-%m-%d")

        # ── 1. Download data ────────────────────────────────────────────
        tickers = {
            "VIX": "^VIX",
            "VIX3M": "^VIX3M",
            "SPY": "SPY",
            "RSP": "RSP",
            "HYG": "HYG",
            "TLT": "TLT",
            "MTUM": "MTUM",
            "VLUE": "VLUE",
        }

        data: dict[str, pd.Series] = {}
        for name, ticker in tickers.items():
            print(f"  Downloading {name} ({ticker}) …")
            data[name] = _download_ticker(ticker, start_date, end_date)

        # ── 2. Align on common trading dates ────────────────────────────
        common_idx = data["SPY"].index
        for s in data.values():
            common_idx = common_idx.intersection(s.index)
        common_idx = common_idx.sort_values()

        aligned: dict[str, pd.Series] = {k: v.reindex(common_idx) for k, v in data.items()}

        # ── 3. Compute signal scores (vectorised) ──────────────────────
        print("  Computing signal scores …")
        signals: dict[str, pd.Series] = {
            "VIX Level": _compute_vix_level(aligned["VIX"]),
            "VIX Term Structure": _compute_vix_term_structure(aligned["VIX"], aligned["VIX3M"]),
            "Market Breadth": _compute_market_breadth(aligned["RSP"], aligned["SPY"]),
            "Credit Spreads": _compute_credit_spreads(aligned["HYG"], aligned["TLT"]),
            "Put/Call Sentiment": _compute_putcall_sentiment(aligned["VIX"]),
            "Factor Crowding": _compute_factor_crowding(aligned["MTUM"], aligned["VLUE"]),
        }

        # ── 4. Composite score ──────────────────────────────────────────
        composite = pd.Series(0.0, index=common_idx)
        for sig_name, weight in SIGNAL_WEIGHTS.items():
            composite += signals[sig_name].reindex(common_idx, fill_value=np.nan) * weight
        composite = composite.clip(0, 100)

        # ── 5. Trim to backtest window ──────────────────────────────────
        backtest_start = datetime.today() - timedelta(days=lookback_years * 365 + 5)
        mask = common_idx >= pd.Timestamp(backtest_start)
        bt_dates = common_idx[mask]

        # Also drop any dates where composite is NaN (warm-up period)
        valid_mask = composite.reindex(bt_dates).notna()
        bt_dates = bt_dates[valid_mask.values]

        if len(bt_dates) < 10:
            raise ValueError("Insufficient data after warm-up – fewer than 10 valid backtest days.")

        print(f"  Backtest window: {bt_dates[0].date()} → {bt_dates[-1].date()}  ({len(bt_dates)} days)")

        # ── 6. Apply 1-day lag (yesterday's score → today's zone) ──────
        composite_bt = composite.reindex(bt_dates)
        lagged_score = composite_bt.shift(1)  # NaN on first day

        zones = lagged_score.apply(lambda s: _classify_zone(s) if pd.notna(s) else ZONE_FULL)
        zone_colors_list = zones.map(ZONE_COLORS).tolist()

        # ── 7. SPY daily returns by zone ────────────────────────────────
        spy_bt = aligned["SPY"].reindex(bt_dates)
        spy_ret = spy_bt.pct_change()

        # Drop the first day (no lagged score, no return)
        valid_days = bt_dates[1:]
        spy_ret_valid = spy_ret.reindex(valid_days)
        zones_valid = zones.reindex(valid_days)

        performance: dict[str, dict] = {}
        for zone in [ZONE_FULL, ZONE_REDUCED, ZONE_DEFENSIVE]:
            zone_mask = zones_valid == zone
            zone_returns = spy_ret_valid[zone_mask]
            n_days = int(zone_mask.sum())
            avg_ret = float(zone_returns.mean()) if n_days > 0 else 0.0
            total_ret = float((1 + zone_returns).prod() - 1) if n_days > 0 else 0.0
            performance[zone] = {
                "days": n_days,
                "avg_daily_return": avg_ret,
                "total_return": total_ret,
                "sizing": ZONE_SIZING[zone],
            }

        # ── 8. Build signal history for the backtest window ─────────────
        signal_history: dict[str, list[float]] = {}
        for sig_name, sig_series in signals.items():
            signal_history[sig_name] = sig_series.reindex(bt_dates).tolist()

        # ── 9. Assemble result dict ─────────────────────────────────────
        result = {
            "dates": bt_dates.to_pydatetime().tolist(),
            "spy_prices": spy_bt.tolist(),
            "composite_scores": composite_bt.tolist(),
            "zones": zones.tolist(),
            "zone_colors": zone_colors_list,
            "performance": performance,
            "signal_history": signal_history,
        }

        print("  ── Zone Performance ──")
        for zone, stats in performance.items():
            print(
                f"    {zone:14s}  {stats['days']:>4d} days  "
                f"avg daily {stats['avg_daily_return']:+.4%}  "
                f"total {stats['total_return']:+.2%}  "
                f"sizing {stats['sizing']}"
            )

        print("  Backtest complete ✓")
        return result

    except Exception:
        logger.exception("Deployment backtest failed")
        raise
