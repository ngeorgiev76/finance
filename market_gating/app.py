"""
Market Deployment Gate – Streamlit Dashboard
=============================================
Premium dark-themed dashboard for the market gating scoring engine.
Launch with:  streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Load environment variables (from .env)
# ---------------------------------------------------------------------------
import os
from pathlib import Path
_env_file = Path(".env")
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip().strip("'\"")

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Deployment Gate",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS – dark premium theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ---- Global overrides ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---- Sidebar Readability ---- */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stCheckbox p {
    color: #f8fafc !important; /* Brighter, crisp white for sidebar text */
    font-weight: 500;
}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
[data-testid="stSidebar"] .stTextInput input {
    background-color: #232736 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* ---- Hero card ---- */
.hero-card {
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,.08);
    box-shadow: 0 8px 32px rgba(0,0,0,.35);
}
.hero-score {
    font-size: 5.5rem;
    font-weight: 900;
    line-height: 1;
    margin: 0.25rem 0;
    letter-spacing: -3px;
    text-shadow: 0 0 40px currentColor;
}
.hero-label {
    font-size: 1rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 4px;
    opacity: 0.7;
    margin-bottom: 0.5rem;
}
.hero-sizing {
    font-size: 1.3rem;
    font-weight: 700;
    margin-top: 0.5rem;
    letter-spacing: 1px;
}

/* ---- Recommendation badge ---- */
.rec-badge {
    display: inline-block;
    padding: 0.6rem 2rem;
    border-radius: 50px;
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.75rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.3);
}

/* ---- Flip-card signal widgets ---- */
.flip-card {
    display: block;
    perspective: 800px;
    min-height: 320px;
    margin-bottom: 1rem;
    cursor: pointer;
}
.flip-card-toggle { display: none; }
.flip-card-inner {
    position: relative;
    width: 100%;
    min-height: 320px;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
}
.flip-card-toggle:checked + .flip-card-inner {
    transform: rotateY(180deg);
}
.flip-card-front, .flip-card-back {
    position: absolute;
    top: 0; left: 0; right: 0;
    min-height: 320px;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid rgba(255,255,255,.06);
    box-shadow: 0 4px 20px rgba(0,0,0,.25);
}
.flip-card-front {
    background: linear-gradient(135deg, rgba(30,30,46,.85), rgba(24,24,37,.95));
    z-index: 2;
}
.flip-card-front:hover {
    box-shadow: 0 8px 30px rgba(0,0,0,.4);
}
.flip-card-back {
    background: linear-gradient(135deg, rgba(24,24,37,.97), rgba(18,18,28,.98));
    transform: rotateY(180deg);
    overflow-y: auto;
}
.signal-name {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #a0a0b8;
    margin-bottom: 0.5rem;
}
.signal-score {
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0.25rem 0;
    letter-spacing: -1px;
}
.signal-detail {
    font-size: 0.8rem;
    color: #8888a0;
    margin-top: 0.5rem;
    line-height: 1.4;
}
.signal-raw {
    font-size: 0.78rem;
    color: #6e6e88;
    font-weight: 500;
}
.flip-hint {
    font-size: 0.7rem;
    color: #5a5a72;
    margin-top: 0.5rem;
    letter-spacing: 0.5px;
}
.back-title {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #a0a0b8;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.back-section {
    margin-bottom: 0.55rem;
}
.back-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #7a7a94;
    margin-bottom: 0.15rem;
}
.back-text {
    font-size: 0.76rem;
    color: #c0c0d4;
    line-height: 1.35;
}
.back-threshold {
    font-size: 0.72rem;
    color: #9a9ab4;
    line-height: 1.4;
    padding-left: 0.5rem;
    border-left: 2px solid rgba(255,255,255,.08);
}
.back-weight {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    background: rgba(255,255,255,.06);
    color: #a0a0b8;
    letter-spacing: 0.5px;
}
.flip-back-hint {
    font-size: 0.68rem;
    color: #5a5a72;
    text-align: center;
    margin-top: 0.5rem;
}

/* ---- Progress bar ---- */
.progress-track {
    width: 100%;
    height: 6px;
    background: rgba(255,255,255,.06);
    border-radius: 3px;
    margin: 0.75rem 0 0.5rem;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
}

/* ---- Guide table ---- */
.guide-row {
    display: flex;
    align-items: center;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.4rem;
    backdrop-filter: blur(6px);
}
.guide-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 12px;
    flex-shrink: 0;
}
.guide-label {
    font-weight: 700;
    font-size: 0.88rem;
    min-width: 120px;
}
.guide-range {
    font-size: 0.82rem;
    color: #8888a0;
    min-width: 80px;
}
.guide-desc {
    font-size: 0.82rem;
    color: #a0a0b8;
}

/* ---- Performance table ---- */
.perf-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 1rem 0;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(20,20,32,0.7);
    border: 1px solid rgba(255,255,255,.06);
}
.perf-table th {
    background: rgba(30,30,46,.9);
    color: #a0a0b8;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,.06);
}
.perf-table td {
    padding: 0.65rem 1rem;
    font-size: 0.85rem;
    color: #e0e0e0;
    border-bottom: 1px solid rgba(255,255,255,.03);
}
.perf-table tr:last-child td {
    border-bottom: none;
}
.perf-table tr:hover td {
    background: rgba(255,255,255,.02);
}
.perf-positive {
    color: #00e676;
    font-weight: 700;
}
.perf-negative {
    color: #ff1744;
    font-weight: 700;
}

/* ---- Sidebar tweaks ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12121c 0%, #0e0e16 100%);
}
section[data-testid="stSidebar"] .stSlider label {
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* ---- Timestamp ---- */
.timestamp {
    text-align: center;
    font-size: 0.78rem;
    color: #6e6e88;
    letter-spacing: 0.5px;
    margin-bottom: 1.5rem;
}

/* ---- Error banner ---- */
.error-banner {
    background: rgba(255,60,60,.1);
    border: 1px solid rgba(255,60,60,.25);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    color: #ff6b6b;
    font-size: 0.85rem;
}

/* ---- Footer ---- */
.footer {
    text-align: center;
    font-size: 0.72rem;
    color: #4a4a5e;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255,255,255,.04);
}

/* ---- Scanner table ---- */
.scanner-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 1rem 0;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(20,20,32,0.7);
    border: 1px solid rgba(255,255,255,.06);
    font-size: 0.82rem;
}
.scanner-table th {
    background: rgba(30,30,46,.9);
    color: #a0a0b8;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.65rem 0.75rem;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,.06);
    white-space: nowrap;
}
.scanner-table th:first-child, .scanner-table th:nth-child(2) {
    text-align: left;
}
.scanner-table td {
    padding: 0.55rem 0.75rem;
    color: #e0e0e0;
    border-bottom: 1px solid rgba(255,255,255,.03);
    text-align: right;
    font-variant-numeric: tabular-nums;
}
.scanner-table td:first-child, .scanner-table td:nth-child(2) {
    text-align: left;
}
.scanner-table tr:hover td {
    background: rgba(255,255,255,.02);
}
.scanner-rank {
    font-weight: 700;
    color: #6e6e88;
}
.scanner-ticker {
    font-weight: 700;
    color: #e0e0e0;
    letter-spacing: 0.5px;
}
.factor-pill {
    display: inline-block;
    padding: 0.15rem 0.45rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 3rem;
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
COLOR_MAP = {
    "green": {"bg": "linear-gradient(135deg, #0d3320 0%, #0a2a1a 100%)", "fg": "#00e676", "badge_bg": "#00e676", "badge_fg": "#0a2a1a"},
    "yellow": {"bg": "linear-gradient(135deg, #33300d 0%, #2a280a 100%)", "fg": "#ffd600", "badge_bg": "#ffd600", "badge_fg": "#2a280a"},
    "red": {"bg": "linear-gradient(135deg, #330d0d 0%, #2a0a0a 100%)", "fg": "#ff1744", "badge_bg": "#ff1744", "badge_fg": "#2a0a0a"},
    "gray": {"bg": "linear-gradient(135deg, #1e1e2e 0%, #181825 100%)", "fg": "#888", "badge_bg": "#888", "badge_fg": "#1e1e2e"},
}

ZONE_COLORS = {
    "FULL DEPLOY": "#00e676",
    "REDUCED": "#ffd600",
    "DEFENSIVE": "#ff1744",
}


def score_color(score: float) -> str:
    """Return a CSS colour for a 0-100 score."""
    if score >= 70:
        return "#00e676"
    if score >= 40:
        return "#ffd600"
    return "#ff1744"


# ---------------------------------------------------------------------------
# Data fetching (cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(weights_tuple):
    """Call the engine with the given weights.  Weights are passed as a tuple
    of (name, value) pairs so Streamlit can hash them for caching."""
    import engine

    weights = dict(weights_tuple) if weights_tuple else None
    return engine.compute_all(weights=weights)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_backtest():
    """Run the 2-year historical backtest (cached for 10 min)."""
    try:
        from backtest.deployment_backtest import run_backtest
        return run_backtest(lookback_years=2)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Backtest failed")
        return None


def get_recommendation(composite_score: float) -> dict:
    """Thin wrapper around engine recommendation logic."""
    import engine

    return engine.get_deployment_recommendation(composite_score)


# ---------------------------------------------------------------------------
# Sidebar – page navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 🧭 Navigation")
selected_page = st.sidebar.radio(
    "Page",
    ["🛡️ Deployment Gate", "📡 Stock Scanner", "🧠 AI Analyst"],
    label_visibility="collapsed",
    key="nav_page",
)

st.sidebar.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar – weight sliders (always visible, used by both pages)
# ---------------------------------------------------------------------------
st.sidebar.markdown("## ⚖️ Signal Weights")
st.sidebar.caption("Adjust weights – they auto-normalise to sum to 1.0")

from signals.composite import SIGNAL_WEIGHTS as _DEFAULT_WEIGHTS

weight_names = list(_DEFAULT_WEIGHTS.keys())

raw_weights: dict[str, float] = {}
for name in weight_names:
    raw_weights[name] = st.sidebar.slider(
        name,
        min_value=0.0,
        max_value=1.0,
        value=_DEFAULT_WEIGHTS[name],
        step=0.05,
        key=f"w_{name}",
    )

total_w = sum(raw_weights.values())
if total_w > 0:
    norm_weights = {k: round(v / total_w, 4) for k, v in raw_weights.items()}
else:
    n = len(raw_weights)
    norm_weights = {k: round(1.0 / n, 4) for k in raw_weights}

st.sidebar.markdown("---")
st.sidebar.markdown("##### Normalised Weights")
for name, w in norm_weights.items():
    st.sidebar.text(f"  {name}: {w:.2%}")

st.sidebar.markdown("---")
st.sidebar.caption("Data refreshes every 5 min. Adjust weights to see instant re-scoring.")

# ---------------------------------------------------------------------------
# Shared data fetch (used by both pages)
# ---------------------------------------------------------------------------
weights_tuple = tuple(sorted(norm_weights.items()))


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1: Deployment Gate
# ═══════════════════════════════════════════════════════════════════════════
def page_gate():
    st.markdown("<h1 style='text-align:center; font-weight:900; letter-spacing:-1px; margin-bottom:0;'>🛡️ Market Deployment Gate</h1>", unsafe_allow_html=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<p class='timestamp'>Last refreshed: {now_str}</p>", unsafe_allow_html=True)

    try:
        with st.spinner("Fetching market signals…"):
            data = fetch_data(weights_tuple)

        composite = data["composite_score"]
        signals = data["signals"]
        rec = get_recommendation(composite)

        # Check for any signal-level errors
        errored = [s for s in signals if s.get("error")]
        if errored:
            err_names = ", ".join(s["name"] for s in errored)
            st.markdown(
                f"<div class='error-banner'>⚠️ Some signals encountered errors and are using fallback scores (50): <strong>{err_names}</strong></div>",
                unsafe_allow_html=True,
            )
    
        # ------------------------------------------------------------------
        # Hero composite score
        # ------------------------------------------------------------------
        colors = COLOR_MAP.get(rec["color"], COLOR_MAP["gray"])
        sizing_pct = f"{rec.get('sizing', 1.0):.0%}"
        st.markdown(
            f"""
            <div class='hero-card' style='background: {colors["bg"]}; border-color: {colors["fg"]}22;'>
                <div class='hero-label'>Composite Deployment Score</div>
                <div class='hero-score' style='color: {colors["fg"]};'>{composite:.0f}</div>
                <div class='rec-badge' style='background: {colors["badge_bg"]}; color: {colors["badge_fg"]};'>
                    {rec["label"]}
                </div>
                <div class='hero-sizing' style='color: {colors["fg"]};'>Position Sizing: {sizing_pct}</div>
                <p style='margin-top:0.75rem; font-size:0.88rem; color:#a0a0b8;'>{rec["description"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
        # ------------------------------------------------------------------
        # Signal flip-card widgets (6 signals, 3 per row)
        # Front: score + progress bar.  Back: methodology & thresholds.
        # ------------------------------------------------------------------
        SIGNAL_INFO = {
            "VIX Level": {
                "icon": "📉",
                "what": "Measures current implied volatility (VIX) relative to its trailing 1-year distribution.",
                "how": "Percentile-ranks the VIX close within its 252-day history. Score = 100 − percentile. Bonus +5 if VIX &lt; 15; penalty −10 if VIX &gt; 30.",
                "why": "The VIX is the market&#39;s fear gauge. Low VIX = calm markets. High VIX = active stress.",
                "thresholds": "VIX &lt; 15 → calm, bonus · 15–20 → normal · 20–30 → elevated · &gt; 30 → fear, penalty",
                "weight": "25%",
            },
            "VIX Term Structure": {
                "icon": "📐",
                "what": "Compares front-month VIX to 3-month VIX (VIX3M) to detect contango vs backwardation.",
                "how": "Ratio = VIX / VIX3M. Linear map: 0.85 → 100 (steep contango), 1.15 → 0 (backwardation).",
                "why": "Backwardation (front &gt; back) signals the market is pricing imminent risk — a strong stress indicator.",
                "thresholds": "&lt; 0.90 → strong contango · 0.90–1.00 → normal · 1.00–1.10 → mild backwardation · &gt; 1.10 → stress",
                "weight": "20%",
            },
            "Market Breadth": {
                "icon": "📊",
                "what": "Tracks % of S&amp;P 500 stocks above their 200-day SMA (RSP/SPY ratio fallback).",
                "how": "Maps breadth %: 80% → score 100, 30% → score 0. Linear interpolation, clamped.",
                "why": "Narrow rallies driven by a few mega-caps are fragile. Broad participation = healthy rally.",
                "thresholds": "&gt; 75% → strong · 50–75% → moderate · 35–50% → weakening · &lt; 35% → poor, narrow market",
                "weight": "20%",
            },
            "Credit Spreads": {
                "icon": "💳",
                "what": "Monitors high-yield credit stress via the HYG/TLT price ratio z-scored over 1 year.",
                "how": "Score = (2 − z) / 4 × 100. Z = −2 (tight) → 100, Z = +2 (wide) → 0.",
                "why": "Credit markets lead equities. Widening spreads = rising default risk = flight to safety.",
                "thresholds": "Z &lt; −1 → very tight, bullish · −1 to 0 → normal · 0 to +1 → mildly wide · &gt; +1 → stress",
                "weight": "15%",
            },
            "Put/Call Sentiment": {
                "icon": "🎭",
                "what": "Uses VIX 20-day rate of change as a proxy for put/call sentiment shifts.",
                "how": "ROC = (VIX − VIX₂₀ᵈ) / VIX₂₀ᵈ × 100. Map: ROC −30% → 100, ROC +50% → 0.",
                "why": "Captures momentum of sentiment. Rising VIX = spiking fear. Falling VIX = complacency.",
                "thresholds": "ROC &lt; −20% → greed · −20% to +10% → neutral · +10% to +30% → fear · &gt; +30% → panic",
                "weight": "10%",
            },
            "Factor Crowding": {
                "icon": "🔄",
                "what": "Tracks 60-day rolling correlation between momentum (MTUM) and value (VLUE) factor returns.",
                "how": "Linear map: corr +0.3 → 100 (normal), corr −0.8 → 0 (extreme crowding).",
                "why": "Extreme negative correlation = crowded momentum = reversal risk (momentum crash precursor).",
                "thresholds": "Corr &gt; +0.2 → normal · 0 to +0.2 → mild · −0.3 to 0 → diverging · &lt; −0.3 → crowded",
                "weight": "10%",
            },
        }
    
        st.markdown("### 📊 Individual Signals")
        st.caption("Click any card to flip it and see methodology, scoring, and interpretation thresholds.")
    
        # Render 3 per row
        cols_per_row = 3
        signal_rows = [signals[i : i + cols_per_row] for i in range(0, len(signals), cols_per_row)]
    
        for row_idx, row in enumerate(signal_rows):
            cols = st.columns(len(row))
            for col_idx, sig in enumerate(zip(cols, row)):
                col, sig_data = sig
                with col:
                    s_color = score_color(sig_data["score"])
                    raw_display = sig_data["raw_value"] if sig_data["raw_value"] is not None else "N/A"
                    if isinstance(raw_display, float):
                        raw_display = f"{raw_display:.4f}"
    
                    pct = max(0, min(100, sig_data["score"]))
                    info = SIGNAL_INFO.get(sig_data["name"], {})
                    card_id = f"flip_{row_idx}_{col_idx}"
                    icon = info.get("icon", "📊")
                    weight = info.get("weight", "")
    
                    # Build threshold lines for the back
                    threshold_html = ""
                    for t in info.get("thresholds", "").split(" · "):
                        if t.strip():
                            threshold_html += f"<div>{t.strip()}</div>"
    
                    st.markdown(
                        f"""
                        <label class='flip-card' for='{card_id}'>
                            <input type='checkbox' class='flip-card-toggle' id='{card_id}' />
                            <div class='flip-card-inner'>
                                <div class='flip-card-front'>
                                    <div class='signal-name'>{icon} {sig_data["name"]}</div>
                                    <div class='signal-score' style='color:{s_color};'>{sig_data["score"]:.1f}</div>
                                    <div class='progress-track'>
                                        <div class='progress-fill' style='width:{pct}%; background:{s_color};'></div>
                                    </div>
                                    <div class='signal-raw'>Raw: {raw_display} &nbsp; <span class='back-weight'>Weight: {weight}</span></div>
                                    <div class='signal-detail'>{sig_data.get("detail", "")}</div>
                                    <div class='flip-hint'>↻ Click to see methodology</div>
                                </div>
                                <div class='flip-card-back'>
                                    <div class='back-title'>{icon} {sig_data["name"]} <span class='back-weight'>{weight}</span></div>
                                    <div class='back-section'>
                                        <div class='back-label'>What it measures</div>
                                        <div class='back-text'>{info.get("what", "")}</div>
                                    </div>
                                    <div class='back-section'>
                                        <div class='back-label'>Scoring method</div>
                                        <div class='back-text'>{info.get("how", "")}</div>
                                    </div>
                                    <div class='back-section'>
                                        <div class='back-label'>Why it matters</div>
                                        <div class='back-text'>{info.get("why", "")}</div>
                                    </div>
                                    <div class='back-section'>
                                        <div class='back-label'>Thresholds</div>
                                        <div class='back-threshold'>{threshold_html}</div>
                                    </div>
                                    <div class='flip-back-hint'>↻ Click to flip back</div>
                                </div>
                            </div>
                        </label>
                        """,
                        unsafe_allow_html=True,
                    )
    
        # ------------------------------------------------------------------
        # Radar / Bar chart
        # ------------------------------------------------------------------
        st.markdown("### 🕸️ Signal Overview")
    
        chart_tab1, chart_tab2 = st.tabs(["Radar Chart", "Bar Chart"])
    
        signal_names = [s["name"] for s in signals]
        signal_scores = [s["score"] for s in signals]
    
        with chart_tab1:
            fig_radar = go.Figure()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=signal_scores + [signal_scores[0]],  # close the polygon
                    theta=signal_names + [signal_names[0]],
                    fill="toself",
                    fillcolor="rgba(0,230,118,0.12)",
                    line=dict(color="#00e676", width=2.5),
                    marker=dict(size=8, color="#00e676"),
                    name="Score",
                )
            )
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=10, color="#6e6e88"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=11, color="#a0a0b8"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                margin=dict(l=80, r=80, t=40, b=40),
                height=420,
                showlegend=False,
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    
        with chart_tab2:
            bar_colors = [score_color(s) for s in signal_scores]
            fig_bar = go.Figure()
            fig_bar.add_trace(
                go.Bar(
                    x=signal_names,
                    y=signal_scores,
                    marker=dict(
                        color=bar_colors,
                        line=dict(width=0),
                        cornerradius=6,
                    ),
                    text=[f"{s:.0f}" for s in signal_scores],
                    textposition="outside",
                    textfont=dict(size=13, color="#e0e0e0", family="Inter"),
                )
            )
            # Add threshold lines
            for threshold, label, color in [
                (70, "Full Deploy", "#00e676"),
                (40, "Reduced", "#ffd600"),
            ]:
                fig_bar.add_hline(
                    y=threshold,
                    line_dash="dot",
                    line_color=color,
                    line_width=1,
                    annotation_text=label,
                    annotation_position="right",
                    annotation_font=dict(size=10, color=color),
                )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                xaxis=dict(
                    tickfont=dict(size=11, color="#a0a0b8"),
                    gridcolor="rgba(255,255,255,0.04)",
                ),
                yaxis=dict(
                    range=[0, 110],
                    tickfont=dict(size=11, color="#6e6e88"),
                    gridcolor="rgba(255,255,255,0.06)",
                ),
                margin=dict(l=40, r=40, t=20, b=60),
                height=400,
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
        # ------------------------------------------------------------------
        # Historical backtest – SPY chart colour-coded by zone
        # ------------------------------------------------------------------
        st.markdown("### 📈 Historical Backtest (2-Year)")
    
        with st.spinner("Running historical backtest…"):
            bt = fetch_backtest()
    
        if bt is not None:
            bt_tab1, bt_tab2, bt_tab3, bt_tab4 = st.tabs(["SPY Chart by Zone", "Composite History", "Signal History", "Performance"])
    
            with bt_tab1:
                fig_spy = go.Figure()
    
                dates = bt["dates"]
                prices = bt["spy_prices"]
                zones = bt["zones"]
    
                # --- Background shading: fill vertical bands for each zone period ---
                zone_alpha = {"FULL DEPLOY": "rgba(0,230,118,0.08)", "REDUCED": "rgba(255,214,0,0.08)", "DEFENSIVE": "rgba(255,23,68,0.12)"}
                i = 0
                while i < len(zones):
                    current_zone = zones[i]
                    j = i
                    while j < len(zones) and zones[j] == current_zone:
                        j += 1
                    # Add a filled rectangle for this contiguous zone block
                    fill_color = zone_alpha.get(current_zone, "rgba(128,128,128,0.05)")
                    fig_spy.add_vrect(
                        x0=dates[i], x1=dates[min(j, len(dates)-1)],
                        fillcolor=fill_color, line_width=0, layer="below",
                    )
                    i = j
    
                # --- Colored line segments: draw SPY price colored by zone ---
                # We draw contiguous same-zone segments as separate traces,
                # overlapping by 1 point at boundaries so there are no gaps.
                legend_added = set()
                i = 0
                while i < len(zones):
                    current_zone = zones[i]
                    j = i
                    while j < len(zones) and zones[j] == current_zone:
                        j += 1
                    # Extend segment by 1 point into the next zone for seamless join
                    end_idx = min(j, len(dates) - 1)
                    seg_dates = dates[i:end_idx + 1]
                    seg_prices = prices[i:end_idx + 1]
                    zc = ZONE_COLORS.get(current_zone, "#888")
                    show_legend = current_zone not in legend_added
                    legend_added.add(current_zone)
                    fig_spy.add_trace(
                        go.Scatter(
                            x=seg_dates,
                            y=seg_prices,
                            mode="lines",
                            line=dict(color=zc, width=2.2),
                            name=current_zone,
                            showlegend=show_legend,
                            legendgroup=current_zone,
                            hovertemplate="%{x|%Y-%m-%d}<br>SPY: $%{y:.2f}<br>" + current_zone + "<extra></extra>",
                        )
                    )
                    i = j
    
                fig_spy.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#e0e0e0"),
                    xaxis=dict(
                        tickfont=dict(size=10, color="#6e6e88"),
                        gridcolor="rgba(255,255,255,0.04)",
                        rangeslider=dict(visible=True, thickness=0.04),
                    ),
                    yaxis=dict(
                        title="SPY Price ($)",
                        tickfont=dict(size=10, color="#6e6e88"),
                        tickprefix="$",
                        gridcolor="rgba(255,255,255,0.06)",
                    ),
                    margin=dict(l=60, r=30, t=30, b=10),
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_spy, use_container_width=True)
    
            with bt_tab2:
                fig_comp = go.Figure()
    
                # Zone background bands
                fig_comp.add_hrect(y0=70, y1=100, fillcolor="rgba(0,230,118,0.06)", line_width=0)
                fig_comp.add_hrect(y0=40, y1=70, fillcolor="rgba(255,214,0,0.06)", line_width=0)
                fig_comp.add_hrect(y0=0, y1=40, fillcolor="rgba(255,23,68,0.06)", line_width=0)
    
                # Composite score line
                fig_comp.add_trace(
                    go.Scatter(
                        x=bt["dates"],
                        y=bt["composite_scores"],
                        mode="lines",
                        line=dict(color="#8b5cf6", width=2),
                        name="Composite Score",
                    )
                )
    
                # Threshold lines
                fig_comp.add_hline(y=70, line_dash="dot", line_color="#00e676", line_width=1)
                fig_comp.add_hline(y=40, line_dash="dot", line_color="#ffd600", line_width=1)
    
                fig_comp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#e0e0e0"),
                    xaxis=dict(
                        tickfont=dict(size=10, color="#6e6e88"),
                        gridcolor="rgba(255,255,255,0.04)",
                    ),
                    yaxis=dict(
                        title="Composite Score",
                        range=[0, 100],
                        tickfont=dict(size=10, color="#6e6e88"),
                        gridcolor="rgba(255,255,255,0.06)",
                    ),
                    margin=dict(l=50, r=30, t=30, b=40),
                    height=400,
                    showlegend=False,
                )
                st.plotly_chart(fig_comp, use_container_width=True)
    
            with bt_tab3:
                st.caption("Individual signal scores over the backtest period. Toggle signals in the legend.")
                sig_hist = bt.get("signal_history", {})
                if sig_hist:
                    fig_sigs = go.Figure()
                    sig_colors = {
                        "VIX Level": "#8b5cf6",
                        "VIX Term Structure": "#06b6d4",
                        "Market Breadth": "#10b981",
                        "Credit Spreads": "#f59e0b",
                        "Put/Call Sentiment": "#ef4444",
                        "Factor Crowding": "#ec4899",
                    }
                    for sig_name, scores in sig_hist.items():
                        fig_sigs.add_trace(
                            go.Scatter(
                                x=bt["dates"],
                                y=scores,
                                mode="lines",
                                line=dict(color=sig_colors.get(sig_name, "#888"), width=1.5),
                                name=sig_name,
                                hovertemplate=f"{sig_name}: " + "%{y:.1f}<extra></extra>",
                            )
                        )
                    # Zone threshold lines
                    fig_sigs.add_hline(y=70, line_dash="dot", line_color="rgba(0,230,118,0.3)", line_width=1)
                    fig_sigs.add_hline(y=40, line_dash="dot", line_color="rgba(255,214,0,0.3)", line_width=1)
                    fig_sigs.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Inter", color="#e0e0e0"),
                        xaxis=dict(
                            tickfont=dict(size=10, color="#6e6e88"),
                            gridcolor="rgba(255,255,255,0.04)",
                        ),
                        yaxis=dict(
                            title="Signal Score",
                            range=[0, 100],
                            tickfont=dict(size=10, color="#6e6e88"),
                            gridcolor="rgba(255,255,255,0.06)",
                        ),
                        margin=dict(l=50, r=30, t=30, b=40),
                        height=450,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=11),
                            bgcolor="rgba(0,0,0,0)",
                        ),
                        hovermode="x unified",
                    )
                    st.plotly_chart(fig_sigs, use_container_width=True)
                else:
                    st.info("No signal history data available from the backtest.")
    
            with bt_tab4:
                perf = bt.get("performance", {})
                if perf:
                    st.markdown("#### 📊 Average SPY Returns by Deployment Zone")
    
                    rows_html = ""
                    for zone_label in ["FULL DEPLOY", "REDUCED", "DEFENSIVE"]:
                        stats = perf.get(zone_label)
                        if not stats:
                            continue
                        zc = ZONE_COLORS.get(zone_label, "#888")
                        avg_ret = stats.get("avg_daily_return", 0) * 100
                        total_ret = stats.get("total_return", 0) * 100
                        days = stats.get("days", 0)
                        sizing = stats.get("sizing", "—")
    
                        avg_cls = "perf-positive" if avg_ret >= 0 else "perf-negative"
                        tot_cls = "perf-positive" if total_ret >= 0 else "perf-negative"
    
                        rows_html += f"""
                        <tr>
                            <td><span style='color:{zc}; font-weight:700;'>●</span> {zone_label}</td>
                            <td>{sizing}</td>
                            <td>{days:,}</td>
                            <td class='{avg_cls}'>{avg_ret:+.4f}%</td>
                            <td class='{tot_cls}'>{total_ret:+.2f}%</td>
                        </tr>
                        """
    
                    st.markdown(
                        f"""
                        <table class='perf-table'>
                            <thead>
                                <tr>
                                    <th>Zone</th>
                                    <th>Sizing</th>
                                    <th>Days</th>
                                    <th>Avg Daily Return</th>
                                    <th>Cumul. Return</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html}
                            </tbody>
                        </table>
                        """,
                        unsafe_allow_html=True,
                    )
    
                    st.caption(
                        "Returns are computed using yesterday's deployment zone for today's allocation "
                        "(no look-ahead bias). Cumulative return is the compounded product of daily returns in each zone."
                    )
                else:
                    st.info("No performance data available from the backtest.")
        else:
            st.warning(
                "Historical backtest could not be computed. This may happen on first run "
                "or if market data is temporarily unavailable. The backtest requires ~3 years "
                "of historical data for 6 different tickers."
            )
    
        # ------------------------------------------------------------------
        # Score interpretation guide
        # ------------------------------------------------------------------
        st.markdown("### 📖 Score Interpretation Guide")
    
        guide_items = [
            ("70 – 100", "FULL DEPLOY", "#00e676", "rgba(0,230,118,0.06)", "Full capital deployment. 100% position sizing. All macro signals favourable."),
            ("40 – 69", "REDUCED", "#ffd600", "rgba(255,214,0,0.06)", "Reduced deployment. 60% sizing, higher bar for new positions. Some headwinds."),
            ("0 – 39", "DEFENSIVE", "#ff1744", "rgba(255,23,68,0.06)", "Defensive mode. 25% sizing, no new longs, scanner disabled. Significant risk."),
        ]
    
        for score_range, label, dot_color, bg_color, desc in guide_items:
            st.markdown(
                f"""
                <div class='guide-row' style='background:{bg_color};'>
                    <div class='guide-dot' style='background:{dot_color};'></div>
                    <span class='guide-label' style='color:{dot_color};'>{label}</span>
                    <span class='guide-range'>{score_range}</span>
                    <span class='guide-desc'>{desc}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
        # ------------------------------------------------------------------
        # Footer
        # ------------------------------------------------------------------
        st.markdown(
            f"""
            <div class='footer'>
                Market Deployment Gate v2.0 &nbsp;·&nbsp; 6 signals · 3 zones
                &nbsp;·&nbsp; Data via yfinance
                &nbsp;·&nbsp; Signals refresh every 5 min &nbsp;·&nbsp; {data["timestamp"][:19]}Z
            </div>
            """,
            unsafe_allow_html=True,
    )

    except Exception as exc:
        st.error(f"Failed to compute market signals: {exc}")
        st.info(
            "This usually means the signal modules in `signals/` are not yet available. "
            "Make sure all 6 signal modules (vix_level, vix_term_structure, breadth, "
            "credit_spreads, put_call, crowding) exist and expose a `compute()` function."
        )
        st.exception(exc)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2: Quantitative Stock Scanner
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def fetch_scanner(zone_label: str, top_n: int = 25):
    """Run the scanner (cached for 10 min)."""
    from scanner.factors import score_universe
    return score_universe(zone_label=zone_label, top_n=top_n)


def _factor_pill(score: float) -> str:
    """Return an HTML pill coloured by factor percentile score."""
    if score >= 80:
        bg, fg = "rgba(0,230,118,0.15)", "#00e676"
    elif score >= 60:
        bg, fg = "rgba(0,230,118,0.08)", "#66ffa6"
    elif score >= 40:
        bg, fg = "rgba(255,214,0,0.10)", "#ffd600"
    elif score >= 20:
        bg, fg = "rgba(255,152,0,0.10)", "#ff9800"
    else:
        bg, fg = "rgba(255,23,68,0.10)", "#ff1744"
    return f"<span class='factor-pill' style='background:{bg}; color:{fg};'>{score:.0f}</span>"


def page_scanner():
    st.markdown("<h1 style='text-align:center; font-weight:900; letter-spacing:-1px; margin-bottom:0;'>📡 Quantitative Stock Scanner</h1>", unsafe_allow_html=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<p class='timestamp'>Last refreshed: {now_str}</p>", unsafe_allow_html=True)

    # First, get the macro gate to determine the zone
    try:
        with st.spinner("Computing macro gate…"):
            data = fetch_data(weights_tuple)
        composite = data["composite_score"]
        rec = get_recommendation(composite)
        zone_label = rec["label"]
        zone_color = rec["color"]
    except Exception as exc:
        st.error(f"Failed to compute macro gate: {exc}")
        return

    # Zone status banner
    colors = COLOR_MAP.get(zone_color, COLOR_MAP["gray"])
    st.markdown(
        f"""
        <div style='background:{colors["bg"]}; border-radius:14px; padding:1rem 1.5rem;
                    border:1px solid rgba(255,255,255,.08); margin-bottom:1.5rem;
                    display:flex; align-items:center; justify-content:space-between;'>
            <div>
                <span style='font-size:0.8rem; color:#a0a0b8; text-transform:uppercase;
                             letter-spacing:2px; font-weight:600;'>Macro Gate</span>
                <div style='font-size:1.8rem; font-weight:800; color:{colors["fg"]};'>
                    {composite:.0f} — {zone_label}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:0.82rem; color:#a0a0b8;'>Scanner Status</div>
                <div style='font-size:1.1rem; font-weight:700; color:{colors["fg"]};'>
                    {"🚫 DISABLED" if zone_label == "DEFENSIVE" else "✅ ACTIVE" + (" (filtered ≥ 75)" if zone_label == "REDUCED" else "")}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if zone_label == "DEFENSIVE":
        st.warning(
            "The scanner is **disabled** in DEFENSIVE mode. "
            "When the macro gate score drops below 40, the system blocks new long entries "
            "to protect capital during high-risk environments."
        )
        st.info("The scanner will automatically re-activate when macro conditions improve.")
        return

    # Scanner controls
    col_a, col_b = st.columns([1, 3])
    with col_a:
        top_n = st.selectbox("Top N candidates", [5, 10, 15, 25, 50, 100, 250, 500], index=3, key="scanner_top_n")

    # Run scanner
    with st.spinner(f"Scanning S&P 500 universe ({zone_label} mode)…"):
        result = fetch_scanner(zone_label, top_n=top_n)

    candidates = result.get("candidates", [])
    universe_size = result.get("universe_size", 0)

    # Stats row
    st1, st2, st3, st4 = st.columns(4)
    st1.metric("Universe Scanned", f"{universe_size}")
    st2.metric("Candidates Found", f"{len(candidates)}")
    st3.metric("Threshold", f"{result.get('threshold', 'None')}")
    st4.metric("Scan Time", result.get("scan_time", "")[:19].replace("T", " "))

    if not candidates:
        st.warning("No candidates met the criteria in this scan.")
        return

    # ------------------------------------------------------------------
    # Results table
    # ------------------------------------------------------------------
    st.markdown("### 🏆 Top Candidates")
    st.caption("Ranked by composite score. Factor scores are universe percentiles (0–100).")

    FACTOR_LABELS = {
        "momentum_crossover": "MomX",
        "volume_surge": "VolS",
        "relative_strength": "RelStr",
        "high_proximity": "Hi%",
        "momentum_health": "MomH",
    }

    header_html = (
        "<th>#</th><th>Ticker</th><th>Composite</th>"
        + "".join(f"<th>{lbl}</th>" for lbl in FACTOR_LABELS.values())
        + "<th>Price</th><th>1M %</th><th>3M %</th>"
    )

    rows_html = ""
    for i, c in enumerate(candidates, 1):
        comp = c["composite"]
        comp_color = score_color(comp)
        factors = c["factors"]

        ret_1m = c.get("return_1m")
        ret_3m = c.get("return_3m")
        ret_1m_str = f"{ret_1m:+.1f}%" if ret_1m is not None else "—"
        ret_3m_str = f"{ret_3m:+.1f}%" if ret_3m is not None else "—"
        ret_1m_cls = "perf-positive" if ret_1m is not None and ret_1m >= 0 else "perf-negative"
        ret_3m_cls = "perf-positive" if ret_3m is not None and ret_3m >= 0 else "perf-negative"

        factor_cells = "".join(
            f"<td>{_factor_pill(factors[k])}</td>" for k in FACTOR_LABELS
        )

        rows_html += f"""
        <tr>
            <td class='scanner-rank'>{i}</td>
            <td class='scanner-ticker'>{c['ticker']}</td>
            <td><span style='color:{comp_color}; font-weight:700;'>{comp:.1f}</span></td>
            {factor_cells}
            <td>${c['price']:.2f}</td>
            <td class='{ret_1m_cls}'>{ret_1m_str}</td>
            <td class='{ret_3m_cls}'>{ret_3m_str}</td>
        </tr>
        """

    st.markdown(
        f"""
        <table class='scanner-table'>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Factor breakdown chart for top 10
    # ------------------------------------------------------------------
    st.markdown("### 📊 Factor Breakdown — Top 10")

    chart_candidates = candidates[:10]
    factor_keys = list(FACTOR_LABELS.keys())
    factor_colors = ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ec4899"]

    fig_factors = go.Figure()
    for fi, fkey in enumerate(factor_keys):
        fig_factors.add_trace(
            go.Bar(
                name=FACTOR_LABELS[fkey],
                x=[c["ticker"] for c in chart_candidates],
                y=[c["factors"][fkey] for c in chart_candidates],
                marker_color=factor_colors[fi],
                opacity=0.85,
            )
        )

    fig_factors.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#e0e0e0"),
        xaxis=dict(tickfont=dict(size=11, color="#a0a0b8")),
        yaxis=dict(
            title="Percentile Score",
            range=[0, 100],
            tickfont=dict(size=10, color="#6e6e88"),
            gridcolor="rgba(255,255,255,0.06)",
        ),
        margin=dict(l=50, r=20, t=30, b=40),
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    st.plotly_chart(fig_factors, use_container_width=True)

    # ------------------------------------------------------------------
    # Factor explanations
    # ------------------------------------------------------------------
    with st.expander("📖 Factor Definitions"):
        st.markdown("""
| Factor | Description |
|--------|-------------|
| **MomX** (Momentum Crossover) | 10-day EMA / 50-day EMA gap + 3-month return. +20 bonus if crossover in last 5 days. |
| **VolS** (Volume Surge) | 5-day avg volume / 20-day avg volume. Expanding volume signals institutional accumulation. |
| **RelStr** (Relative Strength) | 20-day stock return minus 20-day SPY return. Outperformers score higher. |
| **Hi%** (52-Week High Proximity) | Current price / 52-week high. Near highs = momentum (George & Hwang 2004). |
| **MomH** (Momentum Health) | 14-period RSI proxy. Healthy momentum (RSI 50–70) scores highest. |

*All factor scores are percentile-ranked across the S&P 500 universe (0 = lowest, 100 = highest).*
        """)

    # Footer
    st.markdown(
        f"""
        <div class='footer'>
            Quantitative Scanner v1.0 &nbsp;·&nbsp; 5 factors · S&P 500 universe
            &nbsp;·&nbsp; Data via yfinance
            &nbsp;·&nbsp; Gated by macro deployment score
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3: AI Analyst
# ═══════════════════════════════════════════════════════════════════════════

def _dimension_pill(score: float | None) -> str:
    """Return an HTML pill for a 1-10 dimension score."""
    if score is None:
        return "<span class='factor-pill' style='background:rgba(150,150,150,0.1); color:#888;'>—</span>"
    if score >= 8:
        bg, fg = "rgba(0,230,118,0.15)", "#00e676"
    elif score >= 6:
        bg, fg = "rgba(0,230,118,0.08)", "#66ffa6"
    elif score >= 4:
        bg, fg = "rgba(255,214,0,0.10)", "#ffd600"
    elif score >= 3:
        bg, fg = "rgba(255,152,0,0.10)", "#ff9800"
    else:
        bg, fg = "rgba(255,23,68,0.10)", "#ff1744"
    return f"<span class='factor-pill' style='background:{bg}; color:{fg};'>{score:.0f}</span>"


def _rank_delta_html(rank_change: int, flag: str | None) -> str:
    """Return styled HTML for a rank-change delta."""
    if flag == "upgraded":
        icon = "▲"
        color = "#00e676"
        glow = "0 0 8px rgba(0,230,118,0.5)"
    elif flag == "downgraded":
        icon = "▼"
        color = "#ff1744"
        glow = "0 0 8px rgba(255,23,68,0.5)"
    else:
        icon = ""
        color = "#a0a0b8"
        glow = "none"
    sign = "+" if rank_change > 0 else ""
    return (
        f"<span style='color:{color}; font-weight:700; text-shadow:{glow};'>"
        f"{icon} {sign}{rank_change}</span>"
    )


def _fundamental_score_color(score: float | None) -> str:
    """Return a CSS colour for a 1-10 fundamental score."""
    if score is None:
        return "#888"
    if score >= 7:
        return "#00e676"
    if score >= 5:
        return "#ffd600"
    return "#ff1744"


def page_analyst():
    st.markdown("<h1 style='text-align:center; font-weight:900; letter-spacing:-1px; margin-bottom:0;'>🧠 AI Analyst</h1>", unsafe_allow_html=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<p class='timestamp'>Last refreshed: {now_str}</p>", unsafe_allow_html=True)

    # First, get the macro gate to determine the zone
    try:
        with st.spinner("Computing macro gate…"):
            data = fetch_data(weights_tuple)
        composite = data["composite_score"]
        rec = get_recommendation(composite)
        zone_label = rec["label"]
        zone_color = rec["color"]
    except Exception as exc:
        st.error(f"Failed to compute macro gate: {exc}")
        return

    # Zone status banner
    colors = COLOR_MAP.get(zone_color, COLOR_MAP["gray"])
    st.markdown(
        f"""
        <div style='background:{colors["bg"]}; border-radius:14px; padding:1rem 1.5rem;
                    border:1px solid rgba(255,255,255,.08); margin-bottom:1.5rem;
                    display:flex; align-items:center; justify-content:space-between;'>
            <div>
                <span style='font-size:0.8rem; color:#a0a0b8; text-transform:uppercase;
                             letter-spacing:2px; font-weight:600;'>Macro Gate</span>
                <div style='font-size:1.8rem; font-weight:800; color:{colors["fg"]};'>
                    {composite:.0f} — {zone_label}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:0.82rem; color:#a0a0b8;'>Analyst Status</div>
                <div style='font-size:1.1rem; font-weight:700; color:{colors["fg"]};'>
                    {"🚫 DISABLED" if zone_label == "DEFENSIVE" else "✅ ACTIVE"}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if zone_label == "DEFENSIVE":
        st.warning(
            "The AI Analyst is **disabled** in DEFENSIVE mode. "
            "When the macro gate score drops below 40, the system blocks new analysis "
            "to protect capital during high-risk environments."
        )
        st.info("The analyst will automatically re-activate when macro conditions improve.")
        return

    # ------------------------------------------------------------------
    # LLM Provider configuration (sidebar)
    # ------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🤖 LLM Provider")

    provider_options = ["Auto-detect", "Anthropic", "OpenAI", "Gemini", "OpenRouter", "Crof.ai", "Local LLM"]
    provider_choice = st.sidebar.selectbox(
        "Provider",
        provider_options,
        key="analyst_provider",
    )
    provider_map = {
        "Auto-detect": None,
        "Anthropic": "anthropic",
        "OpenAI": "openai",
        "Gemini": "gemini",
        "OpenRouter": "openrouter",
        "Crof.ai": "crofai",
        "Local LLM": "local",
    }

    @st.cache_data(ttl=86400, show_spinner=False)
    def _fetch_gemini_models(explicit_key: str | None = None):
        import requests, os
        api_key = explicit_key or os.getenv("GEMINI_API_KEY")
        defaults = ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-2.5-flash", "gemini-2.5-pro"]
        if not api_key:
            return defaults
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                models = [
                    m["name"].replace("models/", "")
                    for m in resp.json().get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                return models if models else defaults
            return defaults
        except Exception:
            return defaults

    resolved_provider = provider_choice
    if provider_choice == "Auto-detect":
        import os as _os
        for env_key, pname in [
            ("ANTHROPIC_API_KEY", "Anthropic"),
            ("OPENAI_API_KEY", "OpenAI"),
            ("GEMINI_API_KEY", "Gemini"),
            ("GOOGLE_APPLICATION_CREDENTIALS", "Gemini"),
            ("OPENROUTER_API_KEY", "OpenRouter"),
            ("CROFAI_API_KEY", "Crof.ai"),
            ("LOCAL_LLM_URL", "Local LLM"),
        ]:
            # Also check session state for auto-detect!
            if _os.getenv(env_key) or st.session_state.get(f"ui_{env_key}"):
                resolved_provider = pname
                st.sidebar.caption(f"✨ Auto-detected provider: **{pname}**")
                break

    # Determine explicit session key if any
    explicit_key = None
    if resolved_provider and resolved_provider != "Auto-detect":
        env_map = {
            "Anthropic": "ANTHROPIC_API_KEY",
            "OpenAI": "OPENAI_API_KEY",
            "Gemini": "GEMINI_API_KEY",
            "OpenRouter": "OPENROUTER_API_KEY",
            "Crof.ai": "CROFAI_API_KEY",
            "Local LLM": "LOCAL_LLM_URL"
        }
        env_var = env_map.get(resolved_provider)
        if env_var:
            import os as _os
            has_key = bool(_os.getenv(env_var))
            if not has_key:
                try:
                    if env_var in st.secrets:
                        has_key = True
                except Exception:
                    pass
            
            # Use session state key if provided
            if st.session_state.get(f"ui_{env_var}"):
                has_key = True
                explicit_key = st.session_state[f"ui_{env_var}"]
                
            if not has_key:
                ui_key = st.sidebar.text_input(
                    f"🔑 {resolved_provider} API Key", 
                    type="password", 
                    key=f"ui_{env_var}",
                    help="Enter your API key. It is kept completely private to your session."
                )
                if ui_key:
                    explicit_key = ui_key
                    if resolved_provider == "Gemini":
                        _fetch_gemini_models.clear()
                    st.rerun()

    KNOWN_MODELS = {
        "Gemini": _fetch_gemini_models(explicit_key if resolved_provider == "Gemini" else None),
        "OpenAI": ["gpt-4o", "gpt-4o-mini", "o1-mini"],
        "Anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
        "OpenRouter": ["meta-llama/llama-3.1-70b-instruct", "google/gemini-flash-1.5"],
    }

    if resolved_provider in KNOWN_MODELS:
        model_options = KNOWN_MODELS[resolved_provider] + ["Custom..."]
        selected_model = st.sidebar.selectbox("Model", model_options, key="analyst_model_select")
        if selected_model == "Custom...":
            model_override = st.sidebar.text_input("Custom Model ID", key="analyst_model_custom")
        else:
            model_override = selected_model
    else:
        model_override = st.sidebar.text_input(
            "Model override (optional)",
            value="",
            key="analyst_model",
            placeholder="e.g. claude-sonnet-4-20250514",
        )

    # Controls
    col_a, col_b = st.columns([1, 1])
    with col_a:
        top_n = st.selectbox("Scanner Top N Limit", [5, 10, 15, 25, 50, 100, 250, 500], index=1, key="analyst_top_n")
    with col_b:
        st.write("")
        force_refresh = st.checkbox("Force LLM refresh", key="analyst_force")

    # ------------------------------------------------------------------
    # Step 1: Run quantitative scanner
    # ------------------------------------------------------------------
    with st.spinner(f"Scanning S&P 500 universe ({zone_label} mode)…"):
        scan_result = fetch_scanner(zone_label, top_n=top_n)

    all_candidates = scan_result.get("candidates", [])
    if scan_result.get("disabled"):
        st.warning(scan_result.get("reason", "Scanner disabled"))
        return

    if not all_candidates:
        st.warning("No scanner candidates found.")
        return

    # ------------------------------------------------------------------
    # Step 2: User selection
    # ------------------------------------------------------------------
    st.markdown("### 📋 1. Select Candidates for AI Analysis")
    st.caption("Quantitative scores are pre-computed. Select stocks below to run deep fundamental LLM analysis.")
    
    with st.form("candidate_selection"):
        import pandas as pd
        df_data = []
        for c in all_candidates:
            df_data.append({
                "Analyze": False,
                "Ticker": c["ticker"],
                "Quant Rank": c.get("quant_rank", 0),
                "Score": round(c["composite"], 1),
                "Price": f"${c.get('price', 0):.2f}"
            })
        df = pd.DataFrame(df_data)
        
        edited_df = st.data_editor(
            df,
            column_config={"Analyze": st.column_config.CheckboxColumn("Run AI", default=False)},
            disabled=["Ticker", "Quant Rank", "Score", "Price"],
            hide_index=True,
            use_container_width=True
        )
        
        adhoc_ticker = st.text_input("🔍 Or enter Ad-hoc ticker:", placeholder="e.g. AAPL").strip().upper()
        submitted = st.form_submit_button("Run AI Analysis 🚀")
        
    if not submitted:
        return
        
    selected_tickers = edited_df[edited_df["Analyze"]]["Ticker"].tolist()
    if adhoc_ticker and adhoc_ticker not in selected_tickers:
        selected_tickers.append(adhoc_ticker)
        
    if not selected_tickers:
        st.info("Please select at least one candidate or enter an ad-hoc ticker.")
        return
        
    # Build the final candidates list for the LLM
    cand_dict = {c["ticker"]: c for c in all_candidates}
    candidates = []
    for t in selected_tickers:
        if t in cand_dict:
            candidates.append(cand_dict[t])
        else:
            candidates.append({
                "ticker": t,
                "composite": 0.0,
                "factors": {},
                "price": 0.0,
                "return_1m": 0.0,
                "return_3m": 0.0,
                "quant_rank": "-"
            })

    # Step 2: Run LLM analysis
    provider_name = provider_map.get(provider_choice)
    model_name = model_override.strip() or None

    # Check for provider availability
    import os as _os
    provider_available = any([
        _os.getenv("ANTHROPIC_API_KEY"),
        _os.getenv("OPENAI_API_KEY"),
        _os.getenv("GEMINI_API_KEY"),
        _os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        _os.getenv("OPENROUTER_API_KEY"),
        _os.getenv("CROFAI_API_KEY"),
        _os.getenv("LOCAL_LLM_URL"),
        provider_name is not None,
    ])

    if not provider_available:
        st.warning(
            "⚠️ No LLM provider configured. Set one of the following environment variables:\n\n"
            "- `ANTHROPIC_API_KEY` for Claude\n"
            "- `OPENAI_API_KEY` for GPT\n"
            "- `GEMINI_API_KEY` for Gemini\n"
            "- `OPENROUTER_API_KEY` for OpenRouter\n"
            "- `CROFAI_API_KEY` for Crof.ai\n"
            "- `LOCAL_LLM_URL` for local LLM\n\n"
            "The scanner results are shown below without AI analysis."
        )
        # Show scanner-only results
        st.markdown("### 📡 Scanner Results (No AI Analysis)")
        for i, c in enumerate(candidates, 1):
            st.text(f"{i}. {c['ticker']}  —  Quant Score: {c['composite']:.1f}")
        return

    try:
        from analyst.providers import get_provider
        from analyst.analyzer import analyze_candidates
        from analyst.blender import blend_scores, get_blend_summary

        kwargs = {"provider_name": provider_name, "model": model_name}
        if explicit_key:
            if provider_name == "local":
                kwargs["base_url"] = explicit_key
            else:
                kwargs["api_key"] = explicit_key
        provider = get_provider(**kwargs)
        tickers = [c["ticker"] for c in candidates]

        progress_bar = st.progress(0, text="Analyzing candidates…")

        def _analysis_progress(current: int, total: int, ticker: str) -> None:
            progress_bar.progress(
                current / total,
                text=f"Analyzing {ticker} ({current}/{total})…",
            )

        analysis_results = analyze_candidates(
            tickers=tickers,
            provider=provider,
            force_refresh=force_refresh,
            progress_callback=_analysis_progress,
        )
        progress_bar.empty()

        # Step 3: Blend scores
        blended = blend_scores(candidates, analysis_results)
        summary = get_blend_summary(blended)

    except ValueError as exc:
        st.error(f"LLM provider error: {exc}")
        return
    except Exception as exc:
        st.error(f"Analysis pipeline failed: {exc}")
        import traceback
        st.code(traceback.format_exc())
        return

    # ------------------------------------------------------------------
    # Summary metrics & Comparison (Only for Top N Scanner)
    # ------------------------------------------------------------------
    
    DIMENSION_LABELS = {
        "earnings_quality": "EQ",
        "growth_trajectory": "GT",
        "balance_sheet_health": "BS",
        "margin_trends": "MT",
        "red_flags": "RF",
    }
    
    if len(blended) > 1:
        # Calculate cost
        total_prompt_tokens = sum(r.get("analysis", {}).get("usage", {}).get("prompt_tokens", 0) for r in blended)
        total_comp_tokens = sum(r.get("analysis", {}).get("usage", {}).get("completion_tokens", 0) for r in blended)
        PRICING_PER_1M = {
            "gemini-3.6-flash": (0.07, 0.30), "gemini-3.6-pro": (1.25, 5.00),
            "gemini-2.5-flash": (0.07, 0.30), "gemini-2.5-pro": (1.25, 5.00),
            "gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60), "o1-mini": (3.00, 12.00),
            "claude-3-5-sonnet-latest": (3.00, 15.00), "claude-3-5-haiku-latest": (0.25, 1.25),
        }
        prices = PRICING_PER_1M.get(model_name or "gemini-3.6-flash", (0, 0))
        total_cost = (total_prompt_tokens / 1_000_000) * prices[0] + (total_comp_tokens / 1_000_000) * prices[1]

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Candidates", summary["total"])
        m2.metric("Avg Blended", f"{summary['avg_blended']:.1f}")
        m3.metric("Avg Quant", f"{summary['avg_quant']:.1f}")
        m4.metric("Upgraded", f"▲ {summary['upgraded']}", delta=None)
        m5.metric("Downgraded", f"▼ {summary['downgraded']}", delta=None)
        m6.metric("Est. Cost", f"${total_cost:.4f}")
    
        # ------------------------------------------------------------------
        # Blended results table
        # ------------------------------------------------------------------
        st.markdown("### 🏆 Blended Rankings")
        st.caption("60% quantitative composite + 40% AI fundamental score. Rank changes of ±3 or more are flagged.")
    
        DIMENSION_LABELS = {
            "earnings_quality": "EQ",
            "growth_trajectory": "GT",
            "balance_sheet_health": "BS",
            "margin_trends": "MT",
            "red_flags": "RF",
        }
    
        header_html = (
            "<th>#</th><th>Ticker</th><th>Blended</th><th>Quant</th><th>Fund</th>"
            + "".join(f"<th>{lbl}</th>" for lbl in DIMENSION_LABELS.values())
            + "<th>QRank</th><th>Δ</th>"
        )
    
        rows_html = ""
        for r in blended:
            blend_sc = r["blended_score"]
            blend_color = score_color(blend_sc)
            fund_raw = r.get("fundamental_score_raw")
            fund_color = _fundamental_score_color(fund_raw)
    
            analysis = r.get("analysis", {})
            dimensions = analysis.get("dimensions", {})
    
            dim_cells = ""
            for dim_key in DIMENSION_LABELS:
                dim_data = dimensions.get(dim_key, {})
                dim_score = dim_data.get("score") if isinstance(dim_data, dict) else None
                dim_cells += f"<td>{_dimension_pill(dim_score)}</td>"
    
            fund_str = f"{fund_raw:.1f}" if fund_raw is not None else "—"
            delta_html = _rank_delta_html(r["rank_change"], r["flag"])
    
            # Row background glow for flagged candidates
            row_style = ""
            if r["flag"] == "upgraded":
                row_style = "background: rgba(0,230,118,0.04); border-left: 3px solid #00e676;"
            elif r["flag"] == "downgraded":
                row_style = "background: rgba(255,23,68,0.04); border-left: 3px solid #ff1744;"
    
            rows_html += f"""
            <tr style='{row_style}'>
                <td class='scanner-rank'>{r['blended_rank']}</td>
                <td class='scanner-ticker'>{r['ticker']}</td>
                <td><span style='color:{blend_color}; font-weight:700;'>{blend_sc:.1f}</span></td>
                <td>{r['quant_composite']:.1f}</td>
                <td><span style='color:{fund_color}; font-weight:700;'>{fund_str}</span></td>
                {dim_cells}
                <td style='color:#a0a0b8;'>{r['quant_rank']}</td>
                <td>{delta_html}</td>
            </tr>
            """
    
        st.markdown(
            f"""
            <table class='scanner-table'>
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )
    
        # ------------------------------------------------------------------
        # Quant vs AI score comparison chart
        # ------------------------------------------------------------------
        st.markdown("### 📊 Quant vs AI Score Comparison")
    
        chart_data = blended[:15]
        fig_compare = go.Figure()
    
        fig_compare.add_trace(go.Bar(
            name="Quant Score",
            x=[r["ticker"] for r in chart_data],
            y=[r["quant_composite"] for r in chart_data],
            marker_color="#8b5cf6",
            opacity=0.85,
        ))
        fig_compare.add_trace(go.Bar(
            name="Fund Score (×10)",
            x=[r["ticker"] for r in chart_data],
            y=[r["fundamental_score"] for r in chart_data],
            marker_color="#06b6d4",
            opacity=0.85,
        ))
        fig_compare.add_trace(go.Bar(
            name="Blended Score",
            x=[r["ticker"] for r in chart_data],
            y=[r["blended_score"] for r in chart_data],
            marker_color="#10b981",
            opacity=0.85,
        ))
    
        fig_compare.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e0e0e0"),
            xaxis=dict(tickfont=dict(size=11, color="#a0a0b8")),
            yaxis=dict(
                title="Score (0–100)",
                range=[0, 100],
                tickfont=dict(size=10, color="#6e6e88"),
                gridcolor="rgba(255,255,255,0.06)",
            ),
            margin=dict(l=50, r=20, t=30, b=40),
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    
        # ------------------------------------------------------------------
        # Key Disagreements
        # ------------------------------------------------------------------
        disagreements = [r for r in blended if r["flag"] is not None]
        if disagreements:
            st.markdown("### 🔍 Key Disagreements — Quant vs AI")
            st.caption(
                "These are candidates where the quantitative rank and AI-blended rank differ by 3+ positions. "
                "These divergences often surface the most interesting investment insights."
            )
    
            for r in sorted(disagreements, key=lambda x: abs(x["rank_change"]), reverse=True):
                analysis = r.get("analysis", {})
                summary_text = analysis.get("summary", "No analysis available")
                dimensions = analysis.get("dimensions", {})
    
                flag_emoji = "🟢" if r["flag"] == "upgraded" else "🔴"
                flag_label = "UPGRADED" if r["flag"] == "upgraded" else "DOWNGRADED"
                delta = r["rank_change"]
    
                with st.expander(
                    f"{flag_emoji} {r['ticker']} — {flag_label} (Δ{delta:+d})  |  "
                    f"Quant: {r['quant_composite']:.1f}  →  Blended: {r['blended_score']:.1f}"
                ):
                    st.markdown(f"**AI Summary:** {summary_text}")
                    st.markdown("")
    
                    # Dimension details
                    dim_cols = st.columns(5)
                    for idx, (dim_key, dim_label) in enumerate(DIMENSION_LABELS.items()):
                        dim_data = dimensions.get(dim_key, {})
                        dim_score = dim_data.get("score", "—") if isinstance(dim_data, dict) else "—"
                        dim_rationale = dim_data.get("rationale", "N/A") if isinstance(dim_data, dict) else "N/A"
    
                        dim_full_names = {
                            "EQ": "Earnings Quality",
                            "GT": "Growth Trajectory",
                            "BS": "Balance Sheet",
                            "MT": "Margin Trends",
                            "RF": "Red Flags",
                        }
                        with dim_cols[idx]:
                            st.metric(dim_full_names.get(dim_label, dim_label), f"{dim_score}/10")
                            st.caption(dim_rationale)
    
    # ------------------------------------------------------------------
    # Expandable analysis details
    # ------------------------------------------------------------------
    st.markdown("### 📋 Detailed Analysis")
    st.caption("Click any candidate to see the full AI analysis.")

    for r in blended:
        analysis = r.get("analysis", {})
        summary_text = analysis.get("summary", "No analysis available")
        dimensions = analysis.get("dimensions", {})
        fundamentals = analysis.get("fundamentals", {})

        fund_raw = r.get("fundamental_score_raw")
        fund_str = f"{fund_raw:.1f}/10" if fund_raw is not None else "N/A"
        cached = "📦 cached" if analysis.get("cached") else "🔄 fresh"

        with st.expander(
            f"{r['blended_rank']}. {r['ticker']}  —  Fund: {fund_str}  "
            f"Blended: {r['blended_score']:.1f}  ({cached})"
        ):
            usage = analysis.get("usage", {})
            if usage:
                st.caption(f"Tokens used: {usage.get('prompt_tokens', 0):,} prompt / {usage.get('completion_tokens', 0):,} completion")
            
            if analysis.get("error"):
                st.error(f"Analysis error: {analysis['error']}")
                continue

            st.markdown(f"**Summary:** {summary_text}")
            st.markdown("")

            # Scores in columns
            dim_cols = st.columns(5)
            dim_full_names = {
                "earnings_quality": "Earnings Quality",
                "growth_trajectory": "Growth Trajectory",
                "balance_sheet_health": "Balance Sheet",
                "margin_trends": "Margin Trends",
                "red_flags": "Red Flags",
            }
            for idx, (dim_key, dim_name) in enumerate(dim_full_names.items()):
                dim_data = dimensions.get(dim_key, {})
                dim_score = dim_data.get("score", "—") if isinstance(dim_data, dict) else "—"
                dim_rationale = dim_data.get("rationale", "N/A") if isinstance(dim_data, dict) else "N/A"
                with dim_cols[idx]:
                    st.metric(dim_name, f"{dim_score}/10")
                    st.caption(dim_rationale)

            # Fundamental data
            quarters = fundamentals.get("quarters", [])
            if quarters:
                st.markdown("**Quarterly Fundamentals:**")
                q_data = []
                for q in quarters:
                    q_row = {
                        "Quarter": q.get("quarter_end", ""),
                        "Revenue": f"${q['revenue']:,.0f}" if q.get("revenue") else "—",
                        "Net Income": f"${q['net_income']:,.0f}" if q.get("net_income") else "—",
                        "Gross Margin": f"{q['gross_margin']:.1f}%" if q.get("gross_margin") is not None else "—",
                        "Op Margin": f"{q['operating_margin']:.1f}%" if q.get("operating_margin") is not None else "—",
                        "D/E": f"{q['debt_equity']:.2f}" if q.get("debt_equity") is not None else "—",
                        "ROE": f"{q['roe']:.1f}%" if q.get("roe") is not None else "—",
                    }
                    q_data.append(q_row)
                import pandas as _pd
                st.dataframe(
                    _pd.DataFrame(q_data),
                    use_container_width=True,
                    hide_index=True,
                )

    # ------------------------------------------------------------------
    # Scoring methodology
    # ------------------------------------------------------------------
    with st.expander("📖 Methodology"):
        st.markdown("""
| Component | Description |
|-----------|-------------|
| **Blended Score** | 60% quantitative composite (from scanner) + 40% AI fundamental score (scaled 1–10 → 0–100) |
| **Earnings Quality** | Is net income backed by real cash flow? CFO/NI ratio > 1.0 is healthy. |
| **Growth Trajectory** | Revenue and net income QoQ growth trends. Acceleration vs deceleration. |
| **Balance Sheet Health** | Debt/equity ratio relative to sector norms. Over-leverage risk. |
| **Margin Trends** | Gross and operating margin trajectory across quarters. |
| **Red Flags** | Signs of earnings manipulation, AR anomalies, declining cash flow quality. 10 = clean, 1 = severe. |
| **Rank Change** | Quant rank minus blended rank. Positive = AI upgraded (green), Negative = AI downgraded (red). |
| **Flag Threshold** | Rank changes of ±3 or more are flagged. These disagreements often surface the most interesting information. |

*AI analysis is cached by (ticker, quarter_end). Same quarter data = free from cache.*
        """)

    # Footer
    st.markdown(
        f"""
        <div class='footer'>
            AI Analyst v1.0 &nbsp;·&nbsp; 5 dimensions · LLM-powered
            &nbsp;·&nbsp; 60/40 quant-fundamental blend
            &nbsp;·&nbsp; Gated by macro deployment score
        </div>
        """,
        unsafe_allow_html=True,
    )



# ═══════════════════════════════════════════════════════════════════════════
if selected_page == "🛡️ Deployment Gate":
    page_gate()
elif selected_page == "📡 Stock Scanner":
    page_scanner()
elif selected_page == "🧠 AI Analyst":
    page_analyst()
