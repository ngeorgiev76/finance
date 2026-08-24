#!/usr/bin/env python3
"""AI Analyst – CLI Entry Point
=================================
Runs the full scan-and-analyze pipeline: quantitative scanner → LLM
fundamental analysis → blended re-ranking.

Usage::

    python run_analysis.py                          # full end-to-end
    python run_analysis.py --scan-and-analyze       # explicit flag (same as default)
    python run_analysis.py --top 10                 # top 10 candidates
    python run_analysis.py --provider anthropic     # explicit provider
    python run_analysis.py --model claude-sonnet-4-20250514  # explicit model
    python run_analysis.py --json                   # JSON output
    python run_analysis.py --zone "FULL DEPLOY"     # override zone
    python run_analysis.py --force-refresh          # bypass LLM cache
    python run_analysis.py --dashboard              # launch Streamlit after
"""

from __future__ import annotations

import argparse
import json
import os
import sys


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
        "magenta": "\033[95m",
        "white": "\033[97m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def _score_colour(score: float) -> str:
    """Pick a colour name based on a score."""
    if score >= 75:
        return "green"
    elif score >= 50:
        return "yellow"
    return "red"


def _flag_icon(flag: str | None) -> str:
    """Return a visual indicator for rank change flags."""
    if flag == "upgraded":
        return _colour("▲", "green")
    elif flag == "downgraded":
        return _colour("▼", "red")
    return " "


# ---------------------------------------------------------------------------
# Pretty-print results
# ---------------------------------------------------------------------------

def _print_results(blended: list[dict], summary: dict, zone: str) -> None:
    """Print a nicely formatted table of blended analysis results."""
    print()
    print(_colour("═" * 110, "dim"))
    print(_colour("  🧠  AI ANALYST – BLENDED RANKING", "bold"))
    print(_colour("═" * 110, "dim"))
    print()

    zone_colours = {"FULL DEPLOY": "green", "REDUCED": "yellow", "DEFENSIVE": "red"}
    zc = zone_colours.get(zone, "dim")
    print(f"  Zone: {_colour(zone, zc)}    "
          f"Candidates: {summary['total']}    "
          f"Upgraded: {_colour(str(summary['upgraded']), 'green')}    "
          f"Downgraded: {_colour(str(summary['downgraded']), 'red')}")
    print(f"  Avg Blended: {summary['avg_blended']:.1f}    "
          f"Avg Quant: {summary['avg_quant']:.1f}    "
          f"Avg Fundamental: {summary['avg_fundamental']:.1f}")
    print()

    if not blended:
        print(_colour("  No candidates to display.", "yellow"))
        print()
        return

    # Column headers
    hdr = (
        f"  {'#':>3s}  {'Ticker':<7s}  {'Blend':>7s}  {'Quant':>7s}  "
        f"{'Fund':>6s}  {'QRank':>5s}  {'Δ':>4s}  {'':>1s}  {'Summary':<50s}"
    )
    print(_colour(hdr, "cyan"))
    print(_colour("  " + "─" * 106, "dim"))

    for r in blended:
        blend_score = r["blended_score"]
        bc = _score_colour(blend_score)
        rank_delta = r["rank_change"]
        delta_str = f"{rank_delta:+d}" if rank_delta != 0 else " 0"

        # Truncate summary
        analysis = r.get("analysis", {})
        summary_text = analysis.get("summary", "")
        if len(summary_text) > 50:
            summary_text = summary_text[:47] + "…"

        # Fundamental display
        fund_raw = r.get("fundamental_score_raw")
        fund_str = f"{fund_raw:.1f}" if fund_raw is not None else " n/a"

        print(
            f"  {r['blended_rank']:3d}  {r['ticker']:<7s}  "
            f"{_colour(f'{blend_score:7.1f}', bc)}  "
            f"{r['quant_composite']:7.1f}  "
            f"{fund_str:>6s}  "
            f"{r['quant_rank']:5d}  "
            f"{delta_str:>4s}  "
            f"{_flag_icon(r['flag'])}  "
            f"{summary_text:<50s}"
        )

    print()

    # Show disagreements
    disagreements = [r for r in blended if r["flag"] is not None]
    if disagreements:
        print(_colour("  ── Key Disagreements (Quant vs AI) ──", "magenta"))
        print()
        for r in sorted(disagreements, key=lambda x: abs(x["rank_change"]), reverse=True):
            icon = _flag_icon(r["flag"])
            delta = r["rank_change"]
            analysis = r.get("analysis", {})
            summary_text = analysis.get("summary", "No analysis available")

            print(f"  {icon} {_colour(r['ticker'], 'bold')} "
                  f"(Δ{delta:+d}): {summary_text}")
            print()

    print(_colour("─" * 110, "dim"))
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Analyst – scan, analyze, and blend scores",
    )
    parser.add_argument(
        "--scan-and-analyze",
        action="store_true",
        default=True,
        help="Run full end-to-end pipeline (default).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of top candidates to analyze (default: 25).",
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
        help="Override the deployment zone (default: auto-detect).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM provider (anthropic, openai, gemini, openrouter, crofai, local).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name override.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass the analysis cache.",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the Streamlit dashboard after analysis.",
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
        import engine
        from signals.composite import SIGNAL_WEIGHTS
        gate = engine.compute_all(weights=dict(SIGNAL_WEIGHTS))
        zone_info = engine.get_deployment_recommendation(gate["composite_score"])
        zone_label = zone_info["label"]
        print(
            _colour(
                f"  Composite: {gate['composite_score']:.1f}  →  {zone_label}",
                "dim",
            )
        )

    # ------------------------------------------------------------------
    # 2. Run quantitative scanner
    # ------------------------------------------------------------------
    print(_colour("⏳ Running quantitative scanner…", "dim"))
    from scanner.factors import score_universe

    def _scan_progress(current: int, total: int) -> None:
        pct = current / total * 100 if total else 0
        print(f"\r  Scanning: {current}/{total} ({pct:.0f}%)", end="", flush=True)

    scan_result = score_universe(
        zone_label=zone_label,
        top_n=args.top,
        progress_callback=_scan_progress,
    )
    print()  # newline after progress

    if scan_result.get("disabled"):
        print()
        print(_colour(f"  🚫 {scan_result['reason']}", "red"))
        print()
        if args.json_output:
            print(json.dumps(scan_result, indent=2))
        return

    candidates = scan_result.get("candidates", [])
    if not candidates:
        print(_colour("  No scanner candidates found.", "yellow"))
        if args.json_output:
            print(json.dumps(scan_result, indent=2))
        return

    print(_colour(f"  Found {len(candidates)} candidates", "dim"))

    # ------------------------------------------------------------------
    # 3. Run AI fundamental analysis
    # ------------------------------------------------------------------
    print(_colour("⏳ Running AI fundamental analysis…", "dim"))
    from analyst.analyzer import analyze_candidates
    from analyst.providers import get_provider

    try:
        provider = get_provider(provider_name=args.provider, model=args.model)
    except ValueError as exc:
        print(_colour(f"  ❌ {exc}", "red"))
        print()
        print(_colour("  Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY,", "dim"))
        print(_colour("  OPENROUTER_API_KEY, CROFAI_API_KEY, or LOCAL_LLM_URL", "dim"))
        print()
        sys.exit(1)

    tickers = [c["ticker"] for c in candidates]

    def _analysis_progress(current: int, total: int, ticker: str) -> None:
        cached_str = ""
        print(f"\r  Analyzing: {current}/{total} – {ticker} {cached_str}   ",
              end="", flush=True)

    analysis_results = analyze_candidates(
        tickers=tickers,
        provider=provider,
        force_refresh=args.force_refresh,
        progress_callback=_analysis_progress,
    )
    print()  # newline after progress

    # ------------------------------------------------------------------
    # 4. Blend scores
    # ------------------------------------------------------------------
    print(_colour("⏳ Blending scores…", "dim"))
    from analyst.blender import blend_scores, get_blend_summary

    blended = blend_scores(candidates, analysis_results)
    summary = get_blend_summary(blended)

    # ------------------------------------------------------------------
    # 5. Output
    # ------------------------------------------------------------------
    if args.json_output:
        output = {
            "zone": zone_label,
            "scan_result": scan_result,
            "blended": blended,
            "summary": summary,
        }
        # Remove non-serialisable items
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_results(blended, summary, zone_label)

    # ------------------------------------------------------------------
    # 6. Optionally launch dashboard
    # ------------------------------------------------------------------
    if args.dashboard:
        print(_colour("🚀 Launching Streamlit dashboard…", "dim"))
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
