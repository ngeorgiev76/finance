Build a market deployment gating system in Python with a Streamlit dashboard.
This system answers: "Should I be deploying capital right now, and how aggressively?"
It pulls 6 macro signals, scores each 0-100, and blends into a deployment score.

1. VIX Level (signals/vix_level.py):
Percentile-rank current VIX against trailing 1 year. Low VIX = high score.
Bonus +5 if VIX < 15. Penalty -10 if VIX > 30.

2. VIX Term Structure (signals/vix_term_structure.py):
Ratio = front-month VIX / VIX3M. Below 1.0 = contango = calm = high score.
Above 1.0 = backwardation = stress = low score. Map: 0.85 -> 100, 1.15 -> 0.

3. Market Breadth (signals/breadth.py):
% of S&P 500 stocks above 200-day SMA. 80% -> 100, 30% -> 0.
Catches narrow rallies driven by a few mega-caps while everything else declines.

4. Credit Spreads (signals/credit_spreads.py):
HYG vs TLT spread proxy, z-score against 1-year history.
Tight spreads (z = -2) -> 100. Wide spreads (z = +2) -> 0.

5. Put/Call Sentiment (signals/put_call.py):
VIX 20-day rate of change as proxy. Rapidly rising VIX = fear = low score.
ROC -30% -> 100, ROC +50% -> 0.

6. Factor Crowding (signals/crowding.py):
Build momentum and value long/short baskets from top/bottom 50 stocks.
60-day rolling correlation between factor returns.
Corr +0.3 -> 100 (normal). Corr -0.8 -> 0 (extreme crowding).
Highly negative correlation = momentum crowded = reversal risk.

Composite (signals/composite.py):
Weighted blend: VIX Level 0.25, Term Structure 0.20, Breadth 0.20,
Credit 0.15, Put/Call 0.10, Crowding 0.10.
Score 70-100: FULL DEPLOY (100% sizing)
Score 40-69: REDUCED (60% sizing, higher bar for new positions)
Score 0-39: DEFENSIVE (25% sizing, no new longs, scanner disabled)

Historical Backtest (backtest/deployment_backtest.py):
Recompute score daily over 2-year history using yesterdays score for todays
allocation (no look-ahead). Overlay zones on SPY chart. Calculate avg SPY return
in FULL DEPLOY vs REDUCED vs DEFENSIVE days.

Streamlit Dashboard: dark theme (#0b0e17), deployment score as huge number,
6 signal gauges, SPY chart color-coded by zone, performance comparison table.

Entry: run_macro_gate.py (refresh data + recalculate scores)