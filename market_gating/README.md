# 🛡️ Market Deployment Gate

> **"Should I be deploying capital right now, and how aggressively?"**

A Python-based market deployment gating system that aggregates 6 macro signals into a single composite score (0–100), mapping to three deployment zones that determine position sizing and new-position criteria. Includes a premium dark-themed Streamlit dashboard and a 2-year historical backtest engine.

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-dashboard-FF4B4B.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

---

## Quick Start

```bash
# 1. Clone and enter the directory
cd market_gating

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the CLI scorer
python run_macro_gate.py

# 4. Launch the interactive dashboard
streamlit run app.py
```

---

## How It Works

The system fetches real-time market data via [yfinance](https://github.com/ranaroussi/yfinance), scores 6 independent macro signals from 0–100, and blends them into a **composite deployment score** using configurable weights.

### Deployment Zones

| Zone | Score Range | Position Sizing | Action |
|------|------------|----------------|--------|
| 🟢 **FULL DEPLOY** | 70 – 100 | 100% | All macro signals favourable. Full capital deployment. |
| 🟡 **REDUCED** | 40 – 69 | 60% | Some headwinds. Higher bar for new positions. |
| 🔴 **DEFENSIVE** | 0 – 39 | 25% | Significant risk. No new longs, scanner disabled. |

---

## Signals

| # | Signal | Weight | Data Source | What It Measures |
|---|--------|--------|-------------|-----------------|
| 1 | **VIX Level** | 25% | ^VIX | Current implied volatility percentile vs trailing 1-year |
| 2 | **VIX Term Structure** | 20% | ^VIX, ^VIX3M | Contango/backwardation of the VIX curve |
| 3 | **Market Breadth** | 20% | ^MMTH or RSP/SPY | % of S&P 500 stocks above 200-day SMA |
| 4 | **Credit Spreads** | 15% | HYG, TLT | High-yield credit stress (HYG/TLT ratio z-score) |
| 5 | **Put/Call Sentiment** | 10% | ^VIX | VIX 20-day rate of change (sentiment momentum) |
| 6 | **Factor Crowding** | 10% | MTUM, VLUE | Momentum/value factor correlation (crowding risk) |

Each signal module follows a consistent interface:

```python
def compute() -> dict:
    return {
        "name": str,        # Signal name
        "score": float,     # 0-100 deployment score
        "raw_value": float, # Underlying data value
        "detail": str,      # Human-readable explanation
    }
```

All signals have graceful error handling — if a data source is unavailable, the signal returns a neutral score of 50 without crashing the system.

---

## Project Structure

```
market_gating/
├── app.py                          # Streamlit dashboard (3 pages)
├── engine.py                       # Signal orchestrator & composite scorer
├── run_macro_gate.py               # CLI: macro gate scorer
├── run_scanner.py                  # CLI: quantitative stock scanner
├── run_analysis.py                 # CLI: scan + AI analysis + blended ranking
├── requirements.txt                # Python dependencies
├── market_gating.md                # System specification
├── analyst.md                      # Analyst module specification
├── signals/
│   ├── __init__.py
│   ├── vix_level.py                # Signal 1: VIX percentile rank
│   ├── vix_term_structure.py       # Signal 2: VIX/VIX3M ratio
│   ├── breadth.py                  # Signal 3: Market breadth
│   ├── credit_spreads.py           # Signal 4: HYG/TLT spread proxy
│   ├── put_call.py                 # Signal 5: VIX ROC sentiment
│   ├── crowding.py                 # Signal 6: Factor crowding
│   └── composite.py                # Weights & zone definitions
├── scanner/
│   ├── __init__.py
│   ├── universe.py                 # S&P 500 constituent loader (Wikipedia)
│   └── factors.py                  # 5-factor scoring & universe orchestrator
├── analyst/
│   ├── __init__.py
│   ├── providers.py                # Multi-provider LLM abstraction layer
│   ├── analyzer.py                 # Fundamental data gathering + LLM scoring
│   ├── blender.py                  # 60/40 quant-fundamental score blender
│   └── analysis_cache.db           # SQLite cache (auto-created)
└── backtest/
    ├── __init__.py
    └── deployment_backtest.py      # 2-year historical backtest engine
```


---

## Dashboard

The Streamlit dashboard features a dark premium theme with two pages:

### Page 1: Deployment Gate

#### Hero Section
Large composite score display with zone badge and position sizing recommendation.

### Interactive Flip-Card Signals
Six signal widgets in a 3×2 grid. **Click any card to flip it** and reveal:
- What the signal measures
- How the score is calculated
- Why it matters for deployment
- Interpretation threshold ranges

### Signal Overview
Tabbed radar chart and bar chart showing all signal scores at a glance, with deployment zone threshold lines.

### Historical Backtest (2-Year)
Four tabs of historical analysis:

- **SPY Chart by Zone** — SPY price rendered as colored line segments (green/yellow/red) with semi-transparent background zone shading and a range slider for navigation
- **Composite History** — Daily composite score with zone background bands
- **Signal History** — Individual signal evolution over time, with toggleable legend per signal
- **Performance** — Per-zone average daily return, compounded cumulative return, trading days, and sizing

### Page 2: Quantitative Stock Scanner

The scanner page activates only when the macro gate gives the green light:

- **Macro Gate Banner** — Real-time composite score with scanner active/disabled indicator
- **Results Table** — Top N candidates ranked by composite score, with color-coded factor percentile pills, price, and 1M/3M returns
- **Factor Breakdown Chart** — Grouped bar chart comparing the top 10 candidates across all 5 factors
- **Factor Definitions** — Expandable reference explaining each factor's methodology

**High-Performance Caching:** The scanner uses a custom **Stale-While-Revalidate Pickle Cache**. It instantly loads 500 stocks from the local disk if the data is less than 1 hour old. If the cache is stale, it serves the UI instantly while spawning a silent background daemon thread to refresh the 1-year price history. This ensures you never wait 60+ seconds for a network pull.

### Page 3: AI Analyst

The analyst page completely decouples the quant scan from the LLM execution to save tokens:

- **Two-Step Pipeline** — First, view the quantitative scanner results. Then, select specific stocks via checkboxes to pass to the LLM.
- **Ad-Hoc Ticker** — Input any ticker (even outside the Top N scanner list) to instantly run an AI fundamental analysis on it.
- **Dynamic Model Selection** — The provider dropdown (including the "Auto-detect" mode) intelligently scans your `.env` keys, visually confirms the detected provider, and queries the respective API (like Google's API) to list the absolutely newest available models. 
- **Cost & Token Tracking** — Estimates exact prompt/completion tokens based on model pricing, displaying the **Est. Cost** for the batch run and tracking per-stock token usage.
- **Blended Rankings Table** — Candidates re-ranked by blended score (60% quant + 40% AI), with 5 dimension score pills (EQ, GT, BS, MT, RF).
- **Key Disagreements** — Expandable cards highlighting candidates where rank changed by 3+ positions (green glow = upgraded, red glow = downgraded).
- **Detailed Analysis** — Expandable per-candidate view with AI summary, 5-dimension rationales, quarterly fundamental data table, and exact token usage.

### Sidebar Controls
- Page navigation radio buttons (3 pages)
- Adjustable weight sliders for each signal with automatic normalisation to 1.0
- LLM provider and dynamic model selection (visible on AI Analyst page)


---

## CLI Usage

```bash
# Macro gate — standard output
python run_macro_gate.py

# Macro gate — JSON output
python run_macro_gate.py --json

# Macro gate — then launch dashboard
python run_macro_gate.py --dashboard

# Stock scanner — auto-detect zone, top 25
python run_scanner.py

# Stock scanner — top 10
python run_scanner.py --top 10

# Stock scanner — override zone
python run_scanner.py --zone "FULL DEPLOY"

# Stock scanner — JSON output
python run_scanner.py --json

# AI Analyst — full end-to-end scan + analyze
python run_analysis.py

# AI Analyst — top 10, explicit provider
python run_analysis.py --top 10 --provider anthropic

# AI Analyst — with model override
python run_analysis.py --provider openai --model gpt-4o

# AI Analyst — bypass analysis cache
python run_analysis.py --force-refresh

# AI Analyst — JSON output
python run_analysis.py --json

# AI Analyst — then launch dashboard
python run_analysis.py --dashboard
```

### Example Output

```
═══════════════════════════════════════════════════════════
  🛡️  MARKET DEPLOYMENT GATE
═══════════════════════════════════════════════════════════

  VIX Level               72.0  ████████████████████████░░░░░░
  VIX Term Structure      85.0  ██████████████████████████░░░░
  Market Breadth          61.0  ███████████████████░░░░░░░░░░░
  Credit Spreads          54.0  █████████████████░░░░░░░░░░░░░
  Put/Call Sentiment      68.0  █████████████████████░░░░░░░░░
  Factor Crowding         77.0  ████████████████████████░░░░░░

──────────────────────────────────────────────────────────
  Composite Score          70   FULL DEPLOY
  Position Sizing          100%
```

---

## Backtest Methodology

The historical backtest engine (`backtest/deployment_backtest.py`):

1. **Downloads** 3 years of data for 8 tickers (SPY, ^VIX, ^VIX3M, RSP, HYG, TLT, MTUM, VLUE)
2. **Computes** all 6 signal scores daily using vectorised pandas operations
3. **Applies 1-day lag** — yesterday's composite score determines today's zone (no look-ahead bias)
4. **Assigns zones** and calculates per-zone SPY performance statistics
5. **Returns** comprehensive results including per-signal score histories

---

## Requirements & Installation

- Python 3.9+
- Dependencies: `yfinance`, `streamlit`, `pandas`, `numpy`, `plotly`, `requests`

```bash
# 1. Clone the repository
git clone https://github.com/ngeorgiev76/finance.git
cd finance/market_gating

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running & Deployment

You can run the full interactive dashboard locally using Streamlit. The dashboard uses port `8501` by default.

```bash
# Launch the Streamlit dashboard
streamlit run app.py
```

*Note: The first time you launch the scanner, it will take ~60 seconds to download the S&P 500 history. Subsequent runs will be instantaneous due to the stale-while-revalidate local cache.*

---

## Configuring LLMs & API Keys

To use the **AI Analyst** feature (Page 3), you must configure at least one Large Language Model (LLM) provider. 

The application automatically loads API keys from a `.env` file in the root directory. Create a file named `.env` and add your preferred provider keys:

```ini
# .env file

# Google Gemini (Supports AI Studio Developer Keys & Google Cloud Vertex API Keys)
GEMINI_API_KEY="your_gemini_api_key_here"

# Anthropic (Claude 3.5 Sonnet, Haiku, etc.)
ANTHROPIC_API_KEY="your_anthropic_api_key_here"

# OpenAI (GPT-4o, o1-mini, etc.)
OPENAI_API_KEY="your_openai_api_key_here"

# OpenRouter (Llama 3, DeepSeek, etc.)
OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

**How it works in the UI:**
1. Once your `.env` file is saved, start or refresh the dashboard (`streamlit run app.py`).
2. Navigate to the **🧠 AI Analyst** tab.
3. In the left sidebar, use the **Provider** dropdown to select your configured LLM (e.g., Gemini, Anthropic).
4. The **Model** dropdown will dynamically fetch and list the latest available models for that provider (e.g., pulling the live model list directly from the Gemini API).

---

## Advanced Configuration

### Signal Weights

Default weights are defined in `signals/composite.py` and can be adjusted via:
- The sidebar sliders in the Streamlit dashboard (live re-scoring)
- Passing a custom `weights` dict to `engine.compute_all()`

### Adding New Signals

1. Create a new module in `signals/` with a `compute()` function returning `{name, score, raw_value, detail}`
2. Add it to `SIGNAL_MODULES` in `engine.py`
3. Add its weight to `SIGNAL_WEIGHTS` in `signals/composite.py`
4. Add its backtest-compatible computation to `backtest/deployment_backtest.py`

---

## License

MIT
