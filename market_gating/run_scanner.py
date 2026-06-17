#!/usr/bin/env python3
"""Quantitative Stock Scanner – CLI Entry Point
=================================================
Runs the 5-factor scanner against the S&P 500 universe, gated by the
current macro deployment zone.

Usage::

    python run_scanner.py                  # auto-detect zone, top 25
    python run_scanner.py --top 10         # top 10 candidates
    python run_scanner.py --zone REDUCED   # force zone override
    python run_scanner.py --json           # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys

import engine
from scanner.factors import score_universe, FACTOR_NAMES
from signals.composite import SIGNAL_WEIGHTS, get_zone


# ---------------------------------------------------------------------------
# Terminal colour helpers
# ---------------------------------------------------------------------------

def _colour(text: str, code: str) -> str:
    """Wrap *text* in ANSI colour codes for terminal output."""
    codes = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "bold": "\033[1m",
        "reset": "\033[0m",
        "dim": "\033[2m",
        "cyan": "\033[96m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def _score_colour(score: float) -> str:
    """Pick a colour name based on a 0-100 score."""
    if score >= 75:
        return "green"
    elif score >= 50:
        return "yellow"
    return "red"


# ---------------------------------------------------------------------------
# Pretty-print table
# ---------------------------------------------------------------------------

def _print_table(result: dict) -> None:
    """Print a nicely formatted table of scanner candidates."""
    candidates = result.get("candidates", [])
    zone = result.get("zone", "UNKNOWN")

    # Header
    print()
    print(_colour("═" * 100, "dim"))
    print(_colour("  📡  QUANTITATIVE STOCK SCANNER", "bold"))
    print(_colour("═" * 100, "dim"))
    print()

    zone_colours = {"FULL DEPLOY": "green", "REDUCED": "yellow", "DEFENSIVE": "red"}
    zc = zone_colours.get(zone, "dim")
    print(f"  Zone: {_colour(zone, zc)}    "
          f"Universe: {result.get('universe_size', '?')} tickers    "
          f"Showing: top {len(candidates)}")
    if result.get("threshold"):
        print(f"  Filter: composite ≥ {result['threshold']}")
    print()

    if not candidates:
        print(_colour("  No candidates found.", "yellow"))
        print()
        return

    # Column headers
    hdr = (
        f"  {'#':>3s}  {'Ticker':<7s}  {'Comp':>6s}  "
        f"{'MomX':>6s}  {'VolS':>6s}  {'RelS':>6s}  {'HiPx':>6s}  {'MomH':>6s}  "
        f"{'Price':>9s}  {'1m%':>7s}  {'3m%':>7s}"
    )
    print(_colour(hdr, "cyan"))
    print(_colour("  " + "─" * 96, "dim"))

    for i, c in enumerate(candidates, 1):
        factors = c["factors"]
        comp = c["composite"]
        cc = _score_colour(comp)

        ret_1m = f"{c['return_1m']:+.1f}" if c["return_1m"] is not None else "  n/a"
        ret_3m = f"{c['return_3m']:+.1f}" if c["return_3m"] is not None else "  n/a"

        print(
            f"  {i:3d}  {c['ticker']:<7s}  "
            f"{_colour(f'{comp:6.1f}', cc)}  "
            f"{factors['momentum_crossover']:6.1f}  "
            f"{factors['volume_surge']:6.1f}  "
            f"{factors['relative_strength']:6.1f}  "
            f"{factors['high_proximity']:6.1f}  "
            f"{factors['momentum_health']:6.1f}  "
            f"{c['price']:9.2f}  "
            f"{ret_1m:>7s}  "
            f"{ret_3m:>7s}"
        )

    print()
    print(_colour("─" * 100, "dim"))
    print(f"  {_colour('Scan time: ' + result.get('scan_time', '')[:19] + 'Z', 'dim')}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantitative Stock Scanner – score S&P 500 stocks",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of top candidates to show (default: 25).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON.",
    )
    parser.add_argument(
        "--zone",
        type=str,
        default=None,
        choices=["FULL DEPLOY", "REDUCED", "DEFENSIVE"],
        help="Override the deployment zone (default: auto-detect from engine).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Determine zone
    # ------------------------------------------------------------------
    if args.zone:
        zone_label = args.zone
        print(_colour(f"⚙️  Zone override: {zone_label}", "dim"))
    else:
        print(_colour("⏳ Computing macro gate score…", "dim"))
        gate = engine.compute_all(weights=dict(SIGNAL_WEIGHTS))
        zone_info = get_zone(gate["composite_score"])
        zone_label = zone_info["label"]
        print(
            _colour(
                f"  Composite: {gate['composite_score']:.1f}  →  {zone_label}",
                "dim",
            )
        )

    # ------------------------------------------------------------------
    # 2. Run scanner
    # ------------------------------------------------------------------
    print(_colour("⏳ Running quantitative scanner…", "dim"))

    def _progress(current: int, total: int) -> None:
        pct = current / total * 100 if total else 0
        print(f"\r  Scoring: {current}/{total} ({pct:.0f}%)", end="", flush=True)

    result = score_universe(
        zone_label=zone_label,
        top_n=args.top,
        progress_callback=_progress,
    )
    print()  # newline after progress

    # ------------------------------------------------------------------
    # 3. Output
    # ------------------------------------------------------------------
    if result.get("disabled"):
        print()
        print(_colour(f"  🚫 {result['reason']}", "red"))
        print()
        if args.json_output:
            print(json.dumps(result, indent=2))
        return

    if args.json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_table(result)


if __name__ == "__main__":
    main()
