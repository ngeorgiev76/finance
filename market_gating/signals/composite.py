"""
Composite Scoring Configuration
================================
Defines the official signal weights and deployment zone tiers for the
Market Deployment Gate system.

Weighted blend:
    VIX Level       0.25
    Term Structure  0.20
    Breadth         0.20
    Credit          0.15
    Put/Call        0.10
    Crowding        0.10

Deployment zones (applied to the composite score):
    70-100  FULL DEPLOY   → 100 % sizing
    40-69   REDUCED       → 60 % sizing, higher bar for new positions
     0-39   DEFENSIVE     → 25 % sizing, no new longs, scanner disabled
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Official signal weights (must sum to 1.0)
# ---------------------------------------------------------------------------
SIGNAL_WEIGHTS: dict[str, float] = {
    "VIX Level":          0.25,
    "VIX Term Structure": 0.20,
    "Market Breadth":     0.20,
    "Credit Spreads":     0.15,
    "Put/Call Sentiment":  0.10,
    "Factor Crowding":    0.10,
}

# ---------------------------------------------------------------------------
# Deployment zone tiers (evaluated top-down; first match wins)
# ---------------------------------------------------------------------------
DEPLOYMENT_ZONES: list[dict] = [
    {
        "min": 70,
        "label": "FULL DEPLOY",
        "color": "green",
        "sizing": 1.00,
        "description": "Full capital deployment – all macro signals favourable. 100% position sizing.",
    },
    {
        "min": 40,
        "label": "REDUCED",
        "color": "yellow",
        "sizing": 0.60,
        "description": "Reduced deployment – higher bar for new positions. 60% position sizing.",
    },
    {
        "min": 0,
        "label": "DEFENSIVE",
        "color": "red",
        "sizing": 0.25,
        "description": "Defensive mode – no new longs, scanner disabled. 25% position sizing.",
    },
]


def get_zone(composite_score: float) -> dict:
    """Return the deployment zone dict for the given composite score.

    Parameters
    ----------
    composite_score : float
        The blended score (0-100).

    Returns
    -------
    dict
        Contains 'label', 'color', 'sizing', 'description', and the
        input 'score'.
    """
    for zone in DEPLOYMENT_ZONES:
        if composite_score >= zone["min"]:
            return {**zone, "score": composite_score}
    # Fallback
    return {
        "label": "UNKNOWN",
        "color": "gray",
        "sizing": 0.0,
        "description": "Unable to determine deployment zone.",
        "score": composite_score,
    }
