"""Analyst – Candidate Analyzer
================================
For each scanner candidate, gathers fundamental data from yfinance and
sends it to an LLM for qualitative scoring on 5 dimensions:

    1. Earnings Quality
    2. Growth Trajectory
    3. Balance Sheet Health
    4. Margin Trends
    5. Red Flags

Results are cached in a local SQLite database keyed by (ticker, quarter_end)
so that the same quarter is never re-analyzed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from analyst.providers import LLMProvider, get_provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQLite cache
# ---------------------------------------------------------------------------

_DB_PATH = Path(__file__).parent / "analysis_cache.db"


def _get_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open (and optionally create) the analysis cache database."""
    path = str(db_path or _DB_PATH)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_cache (
            ticker       TEXT    NOT NULL,
            quarter_end  TEXT    NOT NULL,
            analysis     TEXT    NOT NULL,
            created_at   TEXT    NOT NULL,
            PRIMARY KEY (ticker, quarter_end)
        )
    """)
    conn.commit()
    return conn


def _cache_get(conn: sqlite3.Connection, ticker: str, quarter_end: str) -> dict | None:
    """Retrieve a cached analysis, or None if not cached."""
    row = conn.execute(
        "SELECT analysis FROM analysis_cache WHERE ticker = ? AND quarter_end = ?",
        (ticker.upper(), quarter_end),
    ).fetchone()
    if row:
        return json.loads(row[0])
    return None


def _cache_put(conn: sqlite3.Connection, ticker: str, quarter_end: str,
               analysis: dict) -> None:
    """Store an analysis result in the cache."""
    conn.execute(
        """INSERT OR REPLACE INTO analysis_cache
           (ticker, quarter_end, analysis, created_at)
           VALUES (?, ?, ?, ?)""",
        (
            ticker.upper(),
            quarter_end,
            json.dumps(analysis),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Fundamental data gathering
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> float | None:
    """Convert a value to float, returning None if it's missing or NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def gather_fundamentals(ticker: str) -> dict[str, Any]:
    """Gather last 4 quarters of fundamental data from yfinance.

    Returns a dict with:
        - ticker: str
        - quarter_end: str (latest quarter end date)
        - quarters: list of quarterly data dicts
        - cfo_ni_ratio: float | None
        - ar_growth_vs_revenue_growth: float | None
    """
    stock = yf.Ticker(ticker)

    # Quarterly financials
    try:
        income_q = stock.quarterly_income_stmt
    except Exception:
        income_q = pd.DataFrame()

    try:
        cashflow_q = stock.quarterly_cashflow
    except Exception:
        cashflow_q = pd.DataFrame()

    try:
        balance_q = stock.quarterly_balance_sheet
    except Exception:
        balance_q = pd.DataFrame()

    if income_q.empty:
        return {
            "ticker": ticker,
            "quarter_end": "unknown",
            "quarters": [],
            "cfo_ni_ratio": None,
            "ar_growth_vs_revenue_growth": None,
            "error": "No income statement data available",
        }

    # Determine quarter end dates (columns are dates, newest first)
    quarter_dates = list(income_q.columns[:4])
    latest_quarter = str(quarter_dates[0].date()) if quarter_dates else "unknown"

    quarters = []
    for qdate in quarter_dates:
        q: dict[str, Any] = {"quarter_end": str(qdate.date())}

        # Income statement items
        def _get_income(label: str) -> float | None:
            for name in [label]:
                if name in income_q.index and qdate in income_q.columns:
                    return _safe_float(income_q.loc[name, qdate])
            return None

        q["revenue"] = _get_income("Total Revenue")
        q["net_income"] = _get_income("Net Income")
        q["gross_profit"] = _get_income("Gross Profit")
        q["operating_income"] = _get_income("Operating Income")

        # Margins
        if q["revenue"] and q["revenue"] != 0:
            q["gross_margin"] = round(
                (q["gross_profit"] / q["revenue"] * 100) if q["gross_profit"] else 0, 2
            )
            q["operating_margin"] = round(
                (q["operating_income"] / q["revenue"] * 100) if q["operating_income"] else 0, 2
            )
        else:
            q["gross_margin"] = None
            q["operating_margin"] = None

        # Cash flow items
        def _get_cashflow(label: str) -> float | None:
            if cashflow_q.empty:
                return None
            if label in cashflow_q.index and qdate in cashflow_q.columns:
                return _safe_float(cashflow_q.loc[label, qdate])
            return None

        q["operating_cash_flow"] = _get_cashflow("Operating Cash Flow")
        q["free_cash_flow"] = _get_cashflow("Free Cash Flow")

        # Balance sheet items
        def _get_balance(label: str) -> float | None:
            if balance_q.empty:
                return None
            if label in balance_q.index and qdate in balance_q.columns:
                return _safe_float(balance_q.loc[label, qdate])
            return None

        total_debt = _get_balance("Total Debt")
        total_equity = _get_balance("Stockholders Equity")
        q["total_debt"] = total_debt
        q["stockholders_equity"] = total_equity

        if total_debt is not None and total_equity and total_equity != 0:
            q["debt_equity"] = round(total_debt / total_equity, 3)
        else:
            q["debt_equity"] = None

        # ROE
        if q["net_income"] is not None and total_equity and total_equity != 0:
            q["roe"] = round(q["net_income"] / total_equity * 100, 2)
        else:
            q["roe"] = None

        # Accounts receivable (for AR growth check)
        q["accounts_receivable"] = _get_balance("Net Receivables")

        quarters.append(q)

    # CFO / Net Income ratio (latest quarter)
    cfo_ni_ratio = None
    if quarters:
        cfo = quarters[0].get("operating_cash_flow")
        ni = quarters[0].get("net_income")
        if cfo is not None and ni and ni != 0:
            cfo_ni_ratio = round(cfo / ni, 3)

    # AR growth vs Revenue growth (latest vs previous quarter)
    ar_vs_rev = None
    if len(quarters) >= 2:
        ar_curr = quarters[0].get("accounts_receivable")
        ar_prev = quarters[1].get("accounts_receivable")
        rev_curr = quarters[0].get("revenue")
        rev_prev = quarters[1].get("revenue")

        if all(v is not None and v != 0 for v in [ar_prev, rev_prev]):
            ar_growth = (ar_curr - ar_prev) / abs(ar_prev) if ar_curr is not None else None
            rev_growth = (rev_curr - rev_prev) / abs(rev_prev) if rev_curr is not None else None
            if ar_growth is not None and rev_growth is not None:
                ar_vs_rev = round(ar_growth - rev_growth, 4)

    return {
        "ticker": ticker,
        "quarter_end": latest_quarter,
        "quarters": quarters,
        "cfo_ni_ratio": cfo_ni_ratio,
        "ar_growth_vs_revenue_growth": ar_vs_rev,
    }


# ---------------------------------------------------------------------------
# LLM analysis prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior equity research analyst. You will be given quarterly \
fundamental financial data for a stock. Score the company 1-10 on each of these 5 dimensions:

1. **Earnings Quality** – Is net income backed by real cash flow? Is the CFO/NI ratio healthy \
(>1.0 is ideal)? Is AR growing faster than revenue (a red flag)?
2. **Growth Trajectory** – Is revenue and net income growing quarter-over-quarter? Is the \
growth accelerating or decelerating?
3. **Balance Sheet Health** – Is debt/equity reasonable for the sector? Is the company \
over-leveraged?
4. **Margin Trends** – Are gross and operating margins expanding, stable, or contracting \
across the quarters shown?
5. **Red Flags** – Any signs of earnings manipulation, unusual AR growth, declining cash \
flow quality, or deteriorating fundamentals? Score 10 = no red flags, 1 = severe concerns.

Respond ONLY with a JSON object in exactly this format (no markdown fences, no commentary):
{
    "earnings_quality": {"score": <1-10>, "rationale": "<1-2 sentences>"},
    "growth_trajectory": {"score": <1-10>, "rationale": "<1-2 sentences>"},
    "balance_sheet_health": {"score": <1-10>, "rationale": "<1-2 sentences>"},
    "margin_trends": {"score": <1-10>, "rationale": "<1-2 sentences>"},
    "red_flags": {"score": <1-10>, "rationale": "<1-2 sentences>"},
    "overall_score": <float, weighted average>,
    "summary": "<2-3 sentence overall assessment>"
}"""


def _build_user_prompt(fundamentals: dict) -> str:
    """Build the user prompt with formatted fundamental data."""
    ticker = fundamentals["ticker"]
    quarters = fundamentals.get("quarters", [])

    lines = [f"Analyze {ticker}:\n"]

    for q in quarters:
        lines.append(f"Quarter ending {q['quarter_end']}:")
        lines.append(f"  Revenue:            ${q.get('revenue', 'N/A'):>15,}" if q.get('revenue') else "  Revenue:            N/A")
        lines.append(f"  Net Income:         ${q.get('net_income', 'N/A'):>15,}" if q.get('net_income') else "  Net Income:         N/A")
        lines.append(f"  Operating Cash Flow:${q.get('operating_cash_flow', 'N/A'):>15,}" if q.get('operating_cash_flow') else "  Operating Cash Flow:N/A")
        lines.append(f"  Free Cash Flow:     ${q.get('free_cash_flow', 'N/A'):>15,}" if q.get('free_cash_flow') else "  Free Cash Flow:     N/A")
        lines.append(f"  Gross Margin:       {q.get('gross_margin', 'N/A')}%")
        lines.append(f"  Operating Margin:   {q.get('operating_margin', 'N/A')}%")
        lines.append(f"  Debt/Equity:        {q.get('debt_equity', 'N/A')}")
        lines.append(f"  ROE:                {q.get('roe', 'N/A')}%")
        lines.append("")

    cfo_ni = fundamentals.get("cfo_ni_ratio")
    ar_vs_rev = fundamentals.get("ar_growth_vs_revenue_growth")
    lines.append(f"CFO/NI Ratio (latest): {cfo_ni if cfo_ni is not None else 'N/A'}")
    lines.append(f"AR Growth vs Revenue Growth (latest): {ar_vs_rev if ar_vs_rev is not None else 'N/A'}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Score dimensions and weights
# ---------------------------------------------------------------------------

SCORE_DIMENSIONS = [
    "earnings_quality",
    "growth_trajectory",
    "balance_sheet_health",
    "margin_trends",
    "red_flags",
]


def _compute_overall(analysis: dict) -> float:
    """Compute the overall score as an equal-weighted average of the 5 dimensions."""
    scores = []
    for dim in SCORE_DIMENSIONS:
        entry = analysis.get(dim, {})
        score = entry.get("score")
        if score is not None:
            scores.append(float(score))
    return round(sum(scores) / len(scores), 2) if scores else 5.0


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_candidate(
    ticker: str,
    provider: LLMProvider | None = None,
    db_path: str | Path | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Analyze a single candidate on fundamental quality.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.
    provider : LLMProvider | None
        LLM provider to use. If None, auto-detects from environment.
    db_path : str | Path | None
        SQLite cache path override.
    force_refresh : bool
        If True, bypasses the cache.

    Returns
    -------
    dict
        Analysis result with scores, rationales, and metadata.
    """
    ticker = ticker.upper()

    # 1. Gather fundamentals
    fundamentals = gather_fundamentals(ticker)

    if not fundamentals.get("quarters"):
        return {
            "ticker": ticker,
            "error": fundamentals.get("error", "No fundamental data available"),
            "overall_score": None,
            "fundamentals": fundamentals,
        }

    quarter_end = fundamentals["quarter_end"]

    # 2. Check cache
    conn = _get_db(db_path)
    if not force_refresh:
        cached = _cache_get(conn, ticker, quarter_end)
        if cached:
            logger.info("Cache hit for %s (quarter %s)", ticker, quarter_end)
            cached["cached"] = True
            conn.close()
            return cached

    # 3. Call LLM
    if provider is None:
        provider = get_provider()

    user_prompt = _build_user_prompt(fundamentals)

    try:
        analysis = provider.complete_json(SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        logger.error("LLM analysis failed for %s: %s", ticker, exc)
        conn.close()
        return {
            "ticker": ticker,
            "error": f"LLM analysis failed: {exc}",
            "overall_score": None,
            "fundamentals": fundamentals,
        }

    # Ensure overall_score is computed
    if "overall_score" not in analysis or analysis["overall_score"] is None:
        analysis["overall_score"] = _compute_overall(analysis)

    # Estimate usage (1 token ≈ 4 characters)
    est_prompt_tokens = (len(SYSTEM_PROMPT) + len(user_prompt)) // 4
    est_completion_tokens = len(str(analysis)) // 4

    result = {
        "ticker": ticker,
        "quarter_end": quarter_end,
        "overall_score": analysis["overall_score"],
        "usage": {
            "prompt_tokens": est_prompt_tokens,
            "completion_tokens": est_completion_tokens,
        },
        "dimensions": {
            dim: analysis.get(dim, {"score": None, "rationale": "N/A"})
            for dim in SCORE_DIMENSIONS
        },
        "summary": analysis.get("summary", ""),
        "fundamentals": fundamentals,
        "cached": False,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    # 4. Cache the result
    _cache_put(conn, ticker, quarter_end, result)
    conn.close()

    return result


def analyze_candidates(
    tickers: list[str],
    provider: LLMProvider | None = None,
    db_path: str | Path | None = None,
    force_refresh: bool = False,
    progress_callback: Any | None = None,
) -> list[dict[str, Any]]:
    """Analyze multiple candidates.

    Parameters
    ----------
    tickers : list[str]
        List of ticker symbols to analyze.
    provider : LLMProvider | None
        Shared LLM provider instance.
    db_path : str | Path | None
        SQLite cache path override.
    force_refresh : bool
        If True, bypasses the cache for all tickers.
    progress_callback : callable | None
        Called with (current_index, total, ticker) for progress tracking.

    Returns
    -------
    list[dict]
        List of analysis results.
    """
    if provider is None:
        provider = get_provider()

    results = []
    total = len(tickers)

    for idx, ticker in enumerate(tickers):
        if progress_callback is not None:
            progress_callback(idx + 1, total, ticker)

        try:
            result = analyze_candidate(
                ticker,
                provider=provider,
                db_path=db_path,
                force_refresh=force_refresh,
            )
            results.append(result)
        except Exception as exc:
            logger.error("Failed to analyze %s: %s", ticker, exc)
            results.append({
                "ticker": ticker.upper(),
                "error": str(exc),
                "overall_score": None,
            })

    return results
