# Market Deployment Gate – System Specification
## Overview
A market deployment gating system in Python with a Streamlit dashboard.
This system answers: **"Should I be deploying capital right now, and how aggressively?"**

It pulls 6 macro signals, scores each 0-100, and blends them into a composite
deployment score that determines position sizing and new-position criteria.

---

## Signals

### 1. VIX Level (`signals/vix_level.py`)
- **Weight:** 25%
- **Data:** ^VIX via yfinance (trailing 1 year)
- **Method:** Percentile-rank current VIX against trailing 252 trading days.
  Score = 100 − percentile. Low VIX = high score.
- **Adjustments:** Bonus +5 if VIX < 15. Penalty −10 if VIX > 30.
- **Thresholds:** VIX < 15 → calm · 15–20 → normal · 20–30 → elevated · > 30 → fear

### 2. VIX Term Structure (`signals/vix_term_structure.py`)
- **Weight:** 20%
- **Data:** ^VIX and ^VIX3M via yfinance
- **Method:** Ratio = front-month VIX / VIX3M.
  Below 1.0 = contango = calm = high score.
  Above 1.0 = backwardation = stress = low score.
  Linear map: 0.85 → 100, 1.15 → 0.
- **Labels:** < 0.98 → contango · 0.98–1.02 → flat · > 1.02 → backwardation
- **Thresholds:** < 0.90 → strong contango · 0.90–1.00 → normal · 1.00–1.10 → mild backwardation · > 1.10 → severe stress

### 3. Market Breadth (`signals/breadth.py`)
- **Weight:** 20%
- **Data (primary):** ^MMTH (CBOE S&P 500 stocks above 200-day SMA index)
- **Data (fallback):** RSP/SPY price ratio z-scored over 1 year
- **Method:** % of S&P 500 stocks above 200-day SMA. 80% → 100, 30% → 0.
  Catches narrow rallies driven by a few mega-caps while everything else declines.
- **Thresholds:** > 75% → strong breadth · 50–75% → moderate · 35–50% → weakening · < 35% → poor, narrow market

### 4. Credit Spreads (`signals/credit_spreads.py`)
- **Weight:** 15%
- **Data:** HYG and TLT via yfinance (trailing 1 year)
- **Method:** HYG/TLT price ratio z-scored against 1-year history.
  Score = (2 − z) / 4 × 100.
  Tight spreads (z = −2) → 100. Wide spreads (z = +2) → 0.
- **Thresholds:** Z < −1 → very tight, bullish · −1 to 0 → normal · 0 to +1 → mildly wide · > +1 → stress

### 5. Put/Call Sentiment (`signals/put_call.py`)
- **Weight:** 10%
- **Data:** ^VIX via yfinance
- **Method:** VIX 20-day rate of change as sentiment proxy.
  Rapidly rising VIX = fear = low score.
  ROC −30% → 100, ROC +50% → 0.
- **Thresholds:** ROC < −20% → greed · −20% to +10% → neutral · +10% to +30% → rising fear · > +30% → panic spike

### 6. Factor Crowding (`signals/crowding.py`)
- **Weight:** 10%
- **Data:** MTUM and VLUE ETFs via yfinance (trailing 1 year)
- **Method:** 60-day rolling correlation between momentum and value factor returns.
  Corr +0.3 → 100 (normal). Corr −0.8 → 0 (extreme crowding).
  Highly negative correlation = momentum crowded = reversal risk.
- **Thresholds:** Corr > +0.2 → normal · 0 to +0.2 → mild · −0.3 to 0 → diverging · < −0.3 → crowded, reversal risk

---

## Composite Scoring (`signals/composite.py`)

Weighted blend of all 6 signals:

| Signal             | Weight |
|--------------------|--------|
| VIX Level          | 0.25   |
| VIX Term Structure | 0.20   |
| Market Breadth     | 0.20   |
| Credit Spreads     | 0.15   |
| Put/Call Sentiment | 0.10   |
| Factor Crowding    | 0.10   |

### Deployment Zones

| Zone         | Score  | Sizing | Action                                      |
|--------------|--------|--------|---------------------------------------------|
| FULL DEPLOY  | 70–100 | 100%   | Full capital deployment, all signals green   |
| REDUCED      | 40–69  | 60%    | Higher bar for new positions                 |
| DEFENSIVE    | 0–39   | 25%    | No new longs, scanner disabled               |

---

## Engine (`engine.py`)

Orchestrates all 6 signal modules:
- Calls each signal's `compute()` function
- Handles per-signal errors gracefully (fallback score = 50)
- Normalises custom weights to sum to 1.0
- Returns composite score, all signal results, normalised weights, and UTC timestamp

---

## Historical Backtest (`backtest/deployment_backtest.py`)

- Downloads 3 years of data (2 backtest + 1 warm-up) for 8 tickers:
  ^VIX, ^VIX3M, SPY, RSP, HYG, TLT, MTUM, VLUE
- Recomputes all 6 signal scores daily using vectorised pandas operations
- Uses **yesterday's composite score** for today's allocation (no look-ahead bias)
- Assigns deployment zones and computes per-zone SPY performance stats
- Returns: dates, SPY prices, composite scores, zones, per-zone performance,
  and per-signal score histories

---

## Streamlit Dashboard (`app.py`)

### Theme
Dark premium theme with Inter font, glassmorphism effects, gradient backgrounds.

### Page 1: Deployment Gate
1. **Hero Card** — Composite deployment score as oversized number, zone badge,
   position sizing percentage, recommendation description
2. **Flip-Card Signal Widgets** — 6 interactive cards in a 3×2 grid:
   - **Front:** Signal name, score, progress bar, raw value, weight badge
   - **Back (click to reveal):** Methodology, scoring formula, interpretation,
     threshold ranges — no separate section needed
3. **Signal Overview** — Tabbed radar chart and bar chart with zone threshold lines
4. **Historical Backtest** — 4 tabs:
   - **SPY Chart by Zone** — SPY price as colored line segments (green/yellow/red)
     with semi-transparent background shading per zone period, range slider,
     unified hover tooltips
   - **Composite History** — Score time series with zone background bands
   - **Signal History** — Individual signal score evolution over 2 years,
     per-signal color coding, legend toggle
   - **Performance** — Per-zone average daily return, compounded cumulative return,
     day count, sizing
5. **Score Interpretation Guide** — Visual reference for the 3 deployment zones

### Page 2: Quantitative Stock Scanner
1. **Macro Gate Banner** — Shows current composite score and scanner active/disabled status
2. **Scanner Results Table** — Ranked candidates with composite score, 5 factor percentiles
   (displayed as color-coded pills), price, 1M/3M returns
3. **Factor Breakdown Chart** — Grouped bar chart comparing top 10 candidates across all factors
4. **Factor Definitions** — Expandable reference for each factor's methodology

### Sidebar
- Page navigation (Deployment Gate / Stock Scanner)
- Adjustable signal weight sliders with auto-normalisation

---

## Quantitative Scanner (`scanner/`)

### Overview
A 5-factor stock scanner that scans the S&P 500 universe and ranks stocks by
a composite multi-factor score. The scanner is **gated by the macro deployment
system** — it is disabled in DEFENSIVE mode and applies a ≥75 threshold in
REDUCED mode.

### Universe (`scanner/universe.py`)
S&P 500 constituents scraped from Wikipedia. Cached for 24 hours.
Tickers normalised (dots → hyphens) for yfinance compatibility.

### Factors (`scanner/factors.py`)

| # | Factor | Method | Score Range |
|---|--------|--------|-------------|
| 1 | **Momentum Crossover** | 10/50 EMA gap + 3-month return. +20 bonus if crossover in last 5 days. | 0–100 |
| 2 | **Volume Surge** | 5-day avg volume / 20-day avg volume. Map 0.7→0, 2.0→100. | 0–100 |
| 3 | **Relative Strength** | 20-day stock return − 20-day SPY return. Percentile-ranked. | 0–100 |
| 4 | **52-Week High Proximity** | Current price / 252-day high. Map 0.70→0, 1.0→100. | 0–100 |
| 5 | **Momentum Health** | 14-period RSI proxy (substitutes for short interest data). | 0–100 |

### Composite Scoring
- All 5 factors are **percentile-ranked** across the universe (0–100)
- Composite = equal weight (20% each) of the 5 percentile-ranked factor scores
- Results sorted by composite descending, top N returned

### Zone Gating
- **FULL DEPLOY**: All candidates surfaced (no threshold)
- **REDUCED**: Only candidates with composite ≥ 75
- **DEFENSIVE**: Scanner disabled, returns empty list

---

## Entry Points

- **`run_macro_gate.py`** — CLI: refresh data, recalculate scores, optionally
  launch the Streamlit dashboard with `--dashboard`
- **`run_scanner.py`** — CLI: run the 5-factor scanner against S&P 500.
  Args: `--top N`, `--json`, `--zone [FULL DEPLOY|REDUCED|DEFENSIVE]`
- **`streamlit run app.py`** — Launch the interactive dashboard directly