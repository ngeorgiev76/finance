#!/usr/bin/env python3
"""
Market Deployment Gate – Entry Point
=====================================
Refresh data, recalculate all signal scores, and print the deployment
recommendation.  Optionally launch the Streamlit dashboard.

Usage:
    python run_macro_gate.py              # compute & print
    python run_macro_gate.py --dashboard  # compute, print, then launch dashboard
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import engine
from signals.composite import SIGNAL_WEIGHTS, get_zone


def _colour(text: str, code: str) -> str:
    """Wrap *text* in ANSI colour codes for terminal output."""
    codes = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "bold": "\033[1m",
        "reset": "\033[0m",
        "dim": "\033[2m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Market Deployment Gate – refresh data & score",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the Streamlit dashboard after computing scores.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for scripting / piping).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Compute all signals
    # ------------------------------------------------------------------
    print(_colour("⏳ Fetching market data and computing signals…", "dim"))
    data = engine.compute_all(weights=dict(SIGNAL_WEIGHTS))
    composite = data["composite_score"]
    zone = get_zone(composite)

    # ------------------------------------------------------------------
    # 2. JSON mode
    # ------------------------------------------------------------------
    if args.json:
        output = {
            "composite_score": composite,
            "zone": zone["label"],
            "sizing": f"{zone['sizing']:.0%}",
            "signals": [
                {"name": s["name"], "score": s["score"], "raw_value": s["raw_value"]}
                for s in data["signals"]
            ],
            "timestamp": data["timestamp"],
        }
        print(json.dumps(output, indent=2))
        return

    # ------------------------------------------------------------------
    # 3. Pretty-print results
    # ------------------------------------------------------------------
    zone_colour = zone["color"]

    print()
    print(_colour("═" * 60, "dim"))
    print(_colour("  🛡️  MARKET DEPLOYMENT GATE", "bold"))
    print(_colour("═" * 60, "dim"))
    print()

    # Individual signals
    for sig in data["signals"]:
        score = sig["score"]
        bar_len = int(score / 100 * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)

        if score >= 70:
            sc = _colour(f"{score:5.1f}", "green")
        elif score >= 40:
            sc = _colour(f"{score:5.1f}", "yellow")
        else:
            sc = _colour(f"{score:5.1f}", "red")

        print(f"  {sig['name']:<22s}  {sc}  {bar}")

    print()
    print(_colour("─" * 60, "dim"))

    # Composite
    composite_str = f"{composite:.0f}"
    print(
        f"  {'Composite Score':<22s}  "
        f"{_colour(composite_str, zone_colour)}  "
        f"{_colour(zone['label'], zone_colour)}"
    )
    print(f"  {'Position Sizing':<22s}  {zone['sizing']:.0%}")
    print(f"  {_colour(zone['description'], 'dim')}")
    print()
    print(_colour("─" * 60, "dim"))
    print(f"  {_colour('Timestamp: ' + data['timestamp'][:19] + 'Z', 'dim')}")
    print()

    # ------------------------------------------------------------------
    # 4. Optionally launch dashboard
    # ------------------------------------------------------------------
    if args.dashboard:
        print(_colour("🚀 Launching Streamlit dashboard…", "bold"))
        app_path = Path(__file__).parent / "app.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    main()
