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

/* ---- Signal cards ---- */
.signal-card {
    background: linear-gradient(135deg, rgba(30,30,46,.85), rgba(24,24,37,.95));
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.signal-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,.4);
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
    min-width: 110px;
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
    "orange": {"bg": "linear-gradient(135deg, #331a0d 0%, #2a150a 100%)", "fg": "#ff9100", "badge_bg": "#ff9100", "badge_fg": "#2a150a"},
    "red": {"bg": "linear-gradient(135deg, #330d0d 0%, #2a0a0a 100%)", "fg": "#ff1744", "badge_bg": "#ff1744", "badge_fg": "#2a0a0a"},
    "gray": {"bg": "linear-gradient(135deg, #1e1e2e 0%, #181825 100%)", "fg": "#888", "badge_bg": "#888", "badge_fg": "#1e1e2e"},
}


def score_color(score: float) -> str:
    """Return a CSS colour for a 0-100 score."""
    if score >= 75:
        return "#00e676"
    if score >= 55:
        return "#ffd600"
    if score >= 35:
        return "#ff9100"
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


def get_recommendation(composite_score: float) -> dict:
    """Thin wrapper around engine recommendation logic."""
    import engine

    return engine.get_deployment_recommendation(composite_score)


# ---------------------------------------------------------------------------
# Sidebar – weight sliders
# ---------------------------------------------------------------------------
st.sidebar.markdown("## ⚖️ Signal Weights")
st.sidebar.caption("Adjust weights – they auto-normalise to sum to 1.0")

weight_names = [
    "VIX Level",
    "VIX Term Structure",
    "Market Breadth",
    "Credit Spreads",
    "Put/Call Sentiment",
]

raw_weights: dict[str, float] = {}
for name in weight_names:
    raw_weights[name] = st.sidebar.slider(
        name,
        min_value=0.0,
        max_value=1.0,
        value=0.20,
        step=0.05,
        key=f"w_{name}",
    )

total_w = sum(raw_weights.values())
if total_w > 0:
    norm_weights = {k: round(v / total_w, 4) for k, v in raw_weights.items()}
else:
    norm_weights = {k: 0.20 for k in raw_weights}

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
    st.markdown(
        f"""
        <div class='hero-card' style='background: {colors["bg"]}; border-color: {colors["fg"]}22;'>
            <div class='hero-label'>Composite Deployment Score</div>
            <div class='hero-score' style='color: {colors["fg"]};'>{composite:.0f}</div>
            <div class='rec-badge' style='background: {colors["badge_bg"]}; color: {colors["badge_fg"]};'>
                {rec["label"]}
            </div>
            <p style='margin-top:0.75rem; font-size:0.88rem; color:#a0a0b8;'>{rec["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Signal detail cards
    # ------------------------------------------------------------------
    st.markdown("### 📊 Individual Signals")

    # Create columns – up to 3 per row for a clean grid
    cols_per_row = 3
    rows = [signals[i : i + cols_per_row] for i in range(0, len(signals), cols_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for col, sig in zip(cols, row):
            with col:
                s_color = score_color(sig["score"])
                raw_display = sig["raw_value"] if sig["raw_value"] is not None else "N/A"
                if isinstance(raw_display, float):
                    raw_display = f"{raw_display:.4f}"

                pct = max(0, min(100, sig["score"]))
                st.markdown(
                    f"""
                    <div class='signal-card'>
                        <div class='signal-name'>{sig["name"]}</div>
                        <div class='signal-score' style='color:{s_color};'>{sig["score"]:.1f}</div>
                        <div class='progress-track'>
                            <div class='progress-fill' style='width:{pct}%; background:{s_color};'></div>
                        </div>
                        <div class='signal-raw'>Raw: {raw_display}</div>
                        <div class='signal-detail'>{sig.get("detail", "")}</div>
                    </div>
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
        st.plotly_chart(fig_radar, width="stretch")

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
            (75, "Aggressive", "#00e676"),
            (55, "Moderate", "#ffd600"),
            (35, "Cautious", "#ff9100"),
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
        st.plotly_chart(fig_bar, width="stretch")

    # ------------------------------------------------------------------
    # Score interpretation guide
    # ------------------------------------------------------------------
    st.markdown("### 📖 Score Interpretation Guide")

    guide_items = [
        ("75 – 100", "AGGRESSIVE", "#00e676", "rgba(0,230,118,0.06)", "Full capital deployment. All macro signals are favourable – lean into positions."),
        ("55 – 74", "MODERATE", "#ffd600", "rgba(255,214,0,0.06)", "Normal deployment. Conditions are acceptable – standard position sizing."),
        ("35 – 54", "CAUTIOUS", "#ff9100", "rgba(255,145,0,0.06)", "Reduced deployment. Headwinds detected – tighten stops, smaller positions."),
        ("0 – 34", "DEFENSIVE", "#ff1744", "rgba(255,23,68,0.06)", "Minimal deployment. Significant macro stress – preserve capital."),
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
            Market Deployment Gate v1.0 &nbsp;·&nbsp; Data via yfinance
            &nbsp;·&nbsp; Signals refresh every 5 min &nbsp;·&nbsp; {data["timestamp"][:19]}Z
        </div>
        """,
        unsafe_allow_html=True,
    )

except Exception as exc:
    st.error(f"Failed to compute market signals: {exc}")
    st.info(
        "This usually means the signal modules in `signals/` are not yet available. "
        "Make sure all 5 signal modules (vix_level, vix_term_structure, breadth, "
        "credit_spreads, put_call) exist and expose a `compute()` function."
    )
    st.exception(exc)
