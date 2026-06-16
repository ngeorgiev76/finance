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
    perspective: 800px;
    min-height: 270px;
    margin-bottom: 1rem;
    cursor: pointer;
}
.flip-card-toggle { display: none; }
.flip-card-inner {
    position: relative;
    width: 100%;
    min-height: 270px;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
}
.flip-card-toggle:checked + .flip-card-inner {
    transform: rotateY(180deg);
}
.flip-card-front, .flip-card-back {
    position: absolute;
    top: 0; left: 0; right: 0;
    min-height: 270px;
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
# Sidebar – weight sliders
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
# Main content
# ---------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; font-weight:900; letter-spacing:-1px; margin-bottom:0;'>🛡️ Market Deployment Gate</h1>", unsafe_allow_html=True)
now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
st.markdown(f"<p class='timestamp'>Last refreshed: {now_str}</p>", unsafe_allow_html=True)

# Fetch data
weights_tuple = tuple(sorted(norm_weights.items()))
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
