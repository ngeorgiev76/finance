"""Analyst – Score Blender
==========================
Blends quantitative scanner scores with LLM fundamental analysis scores
into a unified ranking.

Formula:
    blended = 60% quantitative composite + 40% LLM fundamental score

Rank-change detection: flags candidates where the blended ranking differs
from the quantitative ranking by 3+ positions.

    - Upgraded (green glow): blended rank is 3+ positions better than quant rank
    - Downgraded (red glow): blended rank is 3+ positions worse than quant rank

These flagged rank changes are the key insight: where the quant model and the
AI analyst disagree is where the most interesting information lives.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blend weights
# ---------------------------------------------------------------------------

QUANT_WEIGHT = 0.60
FUNDAMENTAL_WEIGHT = 0.40

# Rank-change threshold for flagging
RANK_CHANGE_THRESHOLD = 3


def blend_scores(
    scanner_candidates: list[dict[str, Any]],
    analysis_results: list[dict[str, Any]],
    quant_weight: float = QUANT_WEIGHT,
    fundamental_weight: float = FUNDAMENTAL_WEIGHT,
    rank_change_threshold: int = RANK_CHANGE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Blend scanner and analysis scores and re-rank candidates.

    Parameters
    ----------
    scanner_candidates : list[dict]
        Output from ``scanner.factors.score_universe()["candidates"]``.
        Each dict must have ``ticker`` and ``composite`` keys.
    analysis_results : list[dict]
        Output from ``analyst.analyzer.analyze_candidates()``.
        Each dict must have ``ticker`` and ``overall_score`` keys.
    quant_weight : float
        Weight for the quantitative composite score (0-1).
    fundamental_weight : float
        Weight for the LLM fundamental score (0-1).
    rank_change_threshold : int
        Minimum rank change to flag a candidate.

    Returns
    -------
    list[dict]
        Blended candidates sorted by blended score descending.
        Each dict contains:
            - ticker: str
            - quant_composite: float (0-100)
            - fundamental_score: float (1-10, scaled to 0-100)
            - blended_score: float (0-100)
            - quant_rank: int (1-based, original scanner rank)
            - blended_rank: int (1-based, after re-ranking)
            - rank_change: int (quant_rank - blended_rank; positive = upgraded)
            - flag: str | None ("upgraded", "downgraded", or None)
            - analysis: dict (full analysis result)
            - scanner: dict (original scanner candidate)
    """
    # Normalise weights
    total_w = quant_weight + fundamental_weight
    if total_w > 0:
        quant_weight /= total_w
        fundamental_weight /= total_w
    else:
        quant_weight = 0.6
        fundamental_weight = 0.4

    # Index analysis results by ticker
    analysis_by_ticker: dict[str, dict] = {}
    for a in analysis_results:
        t = a.get("ticker", "").upper()
        if t:
            analysis_by_ticker[t] = a

    # Build blended records
    records = []
    for quant_rank, candidate in enumerate(scanner_candidates, 1):
        ticker = candidate["ticker"].upper()
        quant_composite = candidate["composite"]  # 0-100

        analysis = analysis_by_ticker.get(ticker, {})
        raw_fundamental = analysis.get("overall_score")

        # Scale LLM score (1-10) to 0-100
        if raw_fundamental is not None:
            fundamental_scaled = float(raw_fundamental) * 10.0
        else:
            # If no analysis available, use quant score as fallback
            fundamental_scaled = quant_composite
            logger.warning(
                "No fundamental analysis for %s – using quant score as fallback",
                ticker,
            )

        blended = round(
            quant_weight * quant_composite + fundamental_weight * fundamental_scaled,
            2,
        )

        records.append({
            "ticker": ticker,
            "quant_composite": quant_composite,
            "fundamental_score_raw": raw_fundamental,
            "fundamental_score": round(fundamental_scaled, 2),
            "blended_score": blended,
            "quant_rank": quant_rank,
            "analysis": analysis,
            "scanner": candidate,
        })

    # Sort by blended score descending and assign blended ranks
    records.sort(key=lambda r: r["blended_score"], reverse=True)
    for blended_rank, record in enumerate(records, 1):
        record["blended_rank"] = blended_rank
        rank_change = record["quant_rank"] - blended_rank  # positive = moved up
        record["rank_change"] = rank_change

        if rank_change >= rank_change_threshold:
            record["flag"] = "upgraded"
        elif rank_change <= -rank_change_threshold:
            record["flag"] = "downgraded"
        else:
            record["flag"] = None

    return records


def get_blend_summary(blended: list[dict]) -> dict[str, Any]:
    """Compute summary statistics for the blended results.

    Returns
    -------
    dict
        - total: int
        - upgraded: int (count of upgraded flags)
        - downgraded: int (count of downgraded flags)
        - avg_blended: float
        - avg_quant: float
        - avg_fundamental: float
        - max_rank_change: int
        - disagreements: list[dict] (top disagreements)
    """
    if not blended:
        return {
            "total": 0,
            "upgraded": 0,
            "downgraded": 0,
            "avg_blended": 0,
            "avg_quant": 0,
            "avg_fundamental": 0,
            "max_rank_change": 0,
            "disagreements": [],
        }

    upgraded = [r for r in blended if r["flag"] == "upgraded"]
    downgraded = [r for r in blended if r["flag"] == "downgraded"]
    disagreements = sorted(
        [r for r in blended if r["flag"] is not None],
        key=lambda r: abs(r["rank_change"]),
        reverse=True,
    )

    return {
        "total": len(blended),
        "upgraded": len(upgraded),
        "downgraded": len(downgraded),
        "avg_blended": round(
            sum(r["blended_score"] for r in blended) / len(blended), 2
        ),
        "avg_quant": round(
            sum(r["quant_composite"] for r in blended) / len(blended), 2
        ),
        "avg_fundamental": round(
            sum(r["fundamental_score"] for r in blended) / len(blended), 2
        ),
        "max_rank_change": max(abs(r["rank_change"]) for r in blended),
        "disagreements": disagreements[:10],
    }
