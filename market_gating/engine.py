"""
Market Deployment Gating Engine
===============================
Aggregates 6 macro signals into a single composite deployment score (0-100).
Each signal module exposes a compute() function returning a dict with:
    - name: str
    - score: float (0-100)
    - raw_value: float
    - detail: str
"""

from datetime import datetime, timezone
from typing import Optional

from signals import vix_level, vix_term_structure, breadth, credit_spreads, put_call, crowding
from signals.composite import SIGNAL_WEIGHTS as _COMPOSITE_WEIGHTS, DEPLOYMENT_ZONES, get_zone

# ---------------------------------------------------------------------------
# Signal registry – order matters only for display
# ---------------------------------------------------------------------------
SIGNAL_MODULES = [
    vix_level,
    vix_term_structure,
    breadth,
    credit_spreads,
    put_call,
    crowding,
]

# ---------------------------------------------------------------------------
# Default weights – see signals/composite.py for official weights (6 signals)
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS = dict(_COMPOSITE_WEIGHTS)


def compute_all(weights: Optional[dict] = None) -> dict:
    """Compute all signals and return the composite deployment score.

    Parameters
    ----------
    weights : dict, optional
        Mapping of signal name → weight (0-1). Values are automatically
        normalised so they sum to 1.0.  If *None*, ``DEFAULT_WEIGHTS`` is used.

    Returns
    -------
    dict
        {
            "composite_score": float,
            "signals": [{"name", "score", "raw_value", "detail"}, ...],
            "weights": {name: normalised_weight, ...},
            "timestamp": str (ISO-8601),
        }
    """
    if weights is None:
        weights = dict(DEFAULT_WEIGHTS)

    # ------------------------------------------------------------------
    # 1. Collect individual signal results
    # ------------------------------------------------------------------
    results: list[dict] = []
    errors: list[dict] = []

    for module in SIGNAL_MODULES:
        try:
            result = module.compute()
            results.append(result)
        except Exception as exc:
            # Record the error but don't let one broken signal kill the whole engine
            error_entry = {
                "name": getattr(module, "__name__", str(module)).rsplit(".", 1)[-1],
                "score": 50.0,   # neutral fallback
                "raw_value": None,
                "detail": f"Error: {exc}",
                "error": True,
            }
            results.append(error_entry)
            errors.append(error_entry)

    # ------------------------------------------------------------------
    # 2. Normalise weights so they sum to 1.0
    # ------------------------------------------------------------------
    normalised: dict[str, float] = {}
    total_weight = 0.0
    for r in results:
        name = r["name"]
        w = weights.get(name, 0.20)
        normalised[name] = w
        total_weight += w

    if total_weight > 0:
        normalised = {k: v / total_weight for k, v in normalised.items()}
    else:
        # Fallback to equal weight if all weights are zero
        equal = 1.0 / len(results) if results else 0.0
        normalised = {r["name"]: equal for r in results}

    # ------------------------------------------------------------------
    # 3. Compute weighted composite score
    # ------------------------------------------------------------------
    composite = sum(
        r["score"] * normalised.get(r["name"], 0.0) for r in results
    )
    composite = round(max(0.0, min(100.0, composite)), 2)

    return {
        "composite_score": composite,
        "signals": results,
        "weights": normalised,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Deployment recommendation logic
# ---------------------------------------------------------------------------
# Re-export DEPLOYMENT_ZONES for backward compatibility
DEPLOYMENT_TIERS = DEPLOYMENT_ZONES


def get_deployment_recommendation(composite_score: float) -> dict:
    """Map a composite score to a deployment recommendation.

    Parameters
    ----------
    composite_score : float
        The blended score (0-100).

    Returns
    -------
    dict
        {
            "label": str,       # e.g. "FULL DEPLOY"
            "color": str,       # CSS-friendly colour name
            "description": str, # human-readable explanation
            "sizing": float,    # position sizing multiplier
            "score": float,     # echo of the input score
        }
    """
    return get_zone(composite_score)
