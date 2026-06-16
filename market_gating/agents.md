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